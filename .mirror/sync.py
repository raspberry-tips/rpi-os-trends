#!/usr/bin/env python3
"""Mirror this dataset repository to Hugging Face and Kaggle.

The GitHub repository is the canonical source. This script reads the data files
from ./data, the dataset card, cover image and metadata from ./.mirror, and
creates or updates the mirrors.

    python .mirror/sync.py            # dry run: build and validate only
    python .mirror/sync.py --check    # exit 1 if a mirror is older than the last data/ commit
    python .mirror/sync.py --live     # upload to both platforms
    python .mirror/sync.py --live --if-stale    # upload only if a mirror is behind (used by the scheduled Action)
    python .mirror/sync.py --live --only hf

Environment: HF_TOKEN (write), KAGGLE_API_TOKEN (KGAT_...).
Requires: pip install huggingface_hub kaggle
The same file lives in raspberry-tips/rpi-os-trends and raspberry-tips/rpi-prices-lifecycle;
keep both copies identical.
"""
import argparse
import csv
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MIRROR = REPO / ".mirror"
# resolve() expands Windows 8.3 short names (PHILIP~1), which break the Kaggle CLI upload cache.
STAGING = Path(tempfile.gettempdir()).resolve() / ("mirror-" + REPO.name)
MIN_BYTES = 1000
# 'create' wants the SPDX-style id, 'metadata --update' only accepts Kaggle's display name.
KAGGLE_LICENSE_DISPLAY = {"CC-BY-4.0": "Attribution 4.0 International (CC BY 4.0)"}


def load_config():
    return json.loads((MIRROR / "config.json").read_text(encoding="utf-8"))


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def stage(cfg):
    """Copy and validate data files, write platform cards into STAGING/{hf,kaggle}."""
    if STAGING.exists():
        shutil.rmtree(STAGING)
    for target in ("hf", "kaggle"):
        (STAGING / target).mkdir(parents=True)
    counts = {}
    for rel in cfg["files"]:
        src = REPO / rel
        data = src.read_bytes()
        if len(data) < MIN_BYTES:
            sys.exit(f"ABORT: {rel} only {len(data)} bytes")
        if src.suffix == ".csv":
            rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
            if not rows:
                sys.exit(f"ABORT: {rel} has no rows")
            counts[src.name] = len(rows)
        elif src.suffix == ".json":
            json.loads(data)
        for target in ("hf", "kaggle"):
            (STAGING / target / src.name).write_bytes(data)
    card = (MIRROR / "card.md").read_text(encoding="utf-8")
    (STAGING / "hf" / "README.md").write_text(hf_front_matter(cfg) + card, encoding="utf-8")
    return card, counts


def hf_front_matter(cfg):
    lines = ["---", "license: cc-by-4.0", f'pretty_name: "{cfg["title"]}"', "language:", "- en",
             "size_categories:", f"- {cfg['size_category']}", "tags:"]
    lines += [f"- {t}" for t in cfg["keywords"]]
    lines.append("configs:")
    for c in cfg["hf_configs"]:
        lines += [f"- config_name: {c['config_name']}", f"  data_files: {c['data_files']}"]
        if c.get("default"):
            lines.append("  default: true")
    return "\n".join(lines + ["---", "", ""])


def kaggle_metadata(cfg, card):
    body = card.split("\n", 1)[1].lstrip() if card.startswith("# ") else card  # H1 duplicates the title
    return {
        "title": cfg["title"],
        "subtitle": cfg["subtitle"],
        "id": cfg["kaggle_id"],
        "licenses": [{"name": "CC-BY-4.0"}],
        "keywords": cfg["kaggle_keywords"],
        "description": body,
        "isPrivate": False,
        "resources": cfg.get("resources", []),
        "userSpecifiedSources": cfg.get("sources", ""),
        "expectedUpdateFrequency": cfg.get("update_frequency", "not specified"),
    }


def kaggle(args, quiet=False):
    r = subprocess.run(["kaggle", *args], capture_output=True, text=True)
    out = " | ".join(l for l in (r.stdout + r.stderr).splitlines() if "%|" not in l and l.strip())
    if not quiet:
        print("  kaggle " + args[1] + ": " + out)
    return r.returncode, r.stdout


def last_data_commit():
    out = subprocess.run(["git", "-C", str(REPO), "log", "-1", "--format=%cI", "--", "data"],
                         capture_output=True, text=True).stdout.strip()
    if not out:
        sys.exit("ABORT: no git history for data/ (shallow clone? use fetch-depth: 0)")
    return ts(out)


def mirror_times(cfg):
    from huggingface_hub import HfApi

    try:
        hf_time = HfApi(token=os.environ.get("HF_TOKEN") or None).dataset_info(cfg["hf_repo"]).last_modified
    except Exception:
        hf_time = None
    rc, out = kaggle(["datasets", "list", "--mine", "--csv"], quiet=True)
    kg_raw = {r["ref"]: r["lastUpdated"] for r in csv.DictReader(io.StringIO(out))}.get(cfg["kaggle_id"]) if rc == 0 else None
    kg_time = ts(kg_raw.replace(" ", "T") + ("" if "+" in kg_raw else "+00:00")) if kg_raw else None
    return {"hf": hf_time, "kaggle": kg_time}


def stale_targets(cfg):
    data_time = last_data_commit()
    times = mirror_times(cfg)
    print(f"GitHub data/ last commit: {data_time:%Y-%m-%d %H:%M} UTC")
    stale = []
    for name, t in times.items():
        ok = t is not None and t >= data_time
        print(f"  {name:7} {t:%Y-%m-%d %H:%M}  {'ok' if ok else 'STALE'}" if t else f"  {name:7} not found  STALE")
        if not ok:
            stale.append(name)
    return stale


def push_hf(cfg):
    from huggingface_hub import HfApi

    api = HfApi(token=os.environ["HF_TOKEN"])
    api.create_repo(cfg["hf_repo"], repo_type="dataset", exist_ok=True, private=False)
    api.upload_folder(repo_id=cfg["hf_repo"], repo_type="dataset", folder_path=str(STAGING / "hf"),
                      commit_message="Sync from " + cfg["github"])
    print(f"  HF ok: https://huggingface.co/datasets/{cfg['hf_repo']}")


def push_kaggle(cfg, card):
    folder = STAGING / "kaggle"
    meta = kaggle_metadata(cfg, card)
    (folder / "dataset-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    if (MIRROR / "cover.png").exists():
        # Kaggle crops 560x280 from the top-left; cover.png has exactly that size.
        shutil.copyfile(MIRROR / "cover.png", folder / "dataset-cover-image.png")
    exists = kaggle(["datasets", "status", cfg["kaggle_id"]], quiet=True)[0] == 0
    if exists:
        rc, _ = kaggle(["datasets", "version", "-p", str(folder), "-m", "Sync from " + cfg["github"]])
    else:
        rc, _ = kaggle(["datasets", "create", "-p", str(folder), "--public"])
    if rc != 0:
        sys.exit("ABORT: kaggle upload failed")
    # create/version ignore column descriptions, sources and cover image; push them separately.
    meta["licenses"] = [{"name": KAGGLE_LICENSE_DISPLAY.get(l["name"], l["name"])} for l in meta["licenses"]]
    (folder / "dataset-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    if kaggle(["datasets", "metadata", "-p", str(folder), "--update", cfg["kaggle_id"]])[0] != 0:
        sys.exit("ABORT: kaggle metadata update failed")
    print(f"  Kaggle ok: https://www.kaggle.com/datasets/{cfg['kaggle_id']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--if-stale", action="store_true", help="with --live: only upload mirrors that are behind")
    ap.add_argument("--only", choices=["hf", "kaggle"])
    args = ap.parse_args()
    cfg = load_config()
    print(f"[{cfg['github']}]")

    if args.check:
        sys.exit(1 if stale_targets(cfg) else 0)

    targets = [args.only] if args.only else ["hf", "kaggle"]
    if args.live:
        need = {"hf": "HF_TOKEN", "kaggle": "KAGGLE_API_TOKEN"}
        missing = [need[t] for t in targets if not os.environ.get(need[t])]
        if missing:
            sys.exit("ABORT: missing environment variables: " + ", ".join(missing))
        if args.if_stale:
            stale = stale_targets(cfg)
            targets = [t for t in targets if t in stale]
            if not targets:
                print("All mirrors up to date, nothing to do.")
                return

    card, counts = stage(cfg)
    print(f"  staged: {counts}")
    if not args.live:
        print(f"Dry run, staging in {STAGING}. Use --live to upload.")
        return
    if "hf" in targets:
        push_hf(cfg)
    if "kaggle" in targets:
        push_kaggle(cfg, card)


if __name__ == "__main__":
    main()
