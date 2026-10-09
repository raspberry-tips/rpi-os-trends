"""Writes data/history.json as a flat CSV (long format) for reuse outside Python.

Columns: date, dimension, label, percent
  date       ISO date of the snapshot (YYYY-MM-DD)
  dimension  os | host_arch | locale
  label      category as shown on the source page
  percent    share of Raspberry Pi Imager downloads in the rolling 30-day window

Usage: python scripts/export_csv.py [data/history.json] [data/history.csv]
"""

import csv
import json
import os
import sys

DIMENSIONS = ("os", "host_arch", "locale")


def write_history_csv(history, path):
    rows = 0
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["date", "dimension", "label", "percent"])
        for point in sorted(history.get("points", []), key=lambda p: p["date"]):
            for dim in DIMENSIONS:
                values = point.get(dim) or {}
                for label, value in sorted(values.items(), key=lambda kv: -kv[1]):
                    writer.writerow([point["date"], dim, label, "%.2f" % value])
                    rows += 1
    return rows


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    src = argv[0] if len(argv) > 0 else os.path.join("data", "history.json")
    dst = argv[1] if len(argv) > 1 else os.path.join("data", "history.csv")
    with open(src, encoding="utf-8") as f:
        history = json.load(f)
    rows = write_history_csv(history, dst)
    print("Geschrieben: %s (%d Zeilen)" % (dst, rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
