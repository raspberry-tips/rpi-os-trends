"""Einmaliger Backfill der Zeitreihe aus dem Internet Archive.

Die eigene Sammlung reicht nur bis Mai 2026 zurück und besteht aus Tages-
Schnappschüssen. Das Internet Archive hat die Quellseite dagegen seit Oktober
2021 regelmässig gespiegelt — inklusive der rollierenden Monatstabellen. Daraus
lässt sich eine belastbare Zeitreihe rekonstruieren.

Ablauf (Download getrennt, damit Netzzugriff und Auswertung unabhängig sind):

  1. CDX-Liste holen:
     curl -sL "http://web.archive.org/cdx/search/cdx?url=rpi-imager-stats.raspberrypi.com&output=text&fl=timestamp,statuscode,digest&collapse=digest" -o cdx.txt
  2. Snapshots herunterladen: bash fetch_all_wayback.sh
  3. python backfill_from_wayback.py wb/ data/history.json

Bewusst kein `requests` hier: der Download läuft über curl (Projektregel für
die lokale Windows-Umgebung), dieses Script liest nur noch von der Platte.
"""

import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rpi_stats_parser import parse_stats_page, sanity_check

HISTORY_DIMENSIONS = ("os", "host_arch", "locale")
PERIOD = "month"
SOURCE_URL = "https://rpi-imager-stats.raspberrypi.com/"


def date_from_timestamp(ts):
    # Wayback-Timestamp: YYYYMMDDhhmmss
    return "%s-%s-%s" % (ts[0:4], ts[4:6], ts[6:8])


def main(indir, outfile):
    files = sorted(f for f in os.listdir(indir) if f.endswith(".html"))
    if not files:
        print("Keine HTML-Dateien in %s" % indir)
        return 1

    by_date = {}
    skipped = defaultdict(int)

    for fn in files:
        ts = fn[:-5]
        date_iso = date_from_timestamp(ts)
        path = os.path.join(indir, fn)
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                html = f.read()
        except OSError as exc:
            skipped["lesefehler"] += 1
            continue

        parsed = parse_stats_page(html)
        rows = parsed.get("os", {}).get(PERIOD)
        if not rows:
            # 2021er-Snapshots haben nur 6 Tabellen; Monatsfenster fehlt teils.
            skipped["kein_monatsfenster"] += 1
            continue

        warn = sanity_check({"os": {"month": rows}})
        if warn:
            skipped["unplausibel"] += 1
            print("  uebersprungen %s: %s" % (date_iso, warn[0]))
            continue

        point = {"date": date_iso}
        for dim in HISTORY_DIMENSIONS:
            drows = parsed.get(dim, {}).get(PERIOD)
            if drows:
                point[dim] = {r["name"]: round(r["value"], 2) for r in drows}

        # Mehrere Snapshots am selben Tag: der spätere gewinnt.
        by_date[date_iso] = point

    points = [by_date[d] for d in sorted(by_date)]

    history = {
        "source": SOURCE_URL,
        "period": PERIOD,
        "note": (
            "Anteile an den Downloads ueber den Raspberry Pi Imager, rollierendes "
            "30-Tage-Fenster. Punkte bis einschliesslich des Backfill-Datums stammen "
            "aus Spiegelungen im Internet Archive."
        ),
        "points": points,
    }

    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=1, ensure_ascii=False)
        f.write("\n")

    print("\n%d Datenpunkte geschrieben nach %s" % (len(points), outfile))
    if points:
        print("Zeitraum: %s bis %s" % (points[0]["date"], points[-1]["date"]))
    for reason, n in sorted(skipped.items()):
        print("uebersprungen (%s): %d" % (reason, n))
    return 0


if __name__ == "__main__":
    indir = sys.argv[1] if len(sys.argv) > 1 else "wb"
    outfile = sys.argv[2] if len(sys.argv) > 2 else "data/history.json"
    sys.exit(main(indir, outfile))
