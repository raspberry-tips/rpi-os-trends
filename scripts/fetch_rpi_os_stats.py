"""Holt die Raspberry-Pi-Imager-Download-Statistiken und schreibt sie fort.

Erzeugt zwei Dateien:

  data/rpi_os_stats.json  — aktueller Stand. Behält die bisherige Struktur
                            (last_updated / source / top_10) bei, damit das
                            bereits ausgerollte WordPress-Plugin weiterläuft,
                            und ergänzt sie um `snapshot` mit allen Dimensionen.

  data/history.json       — Zeitreihe. Ein Eintrag je Kalendertag, Dedupe über
                            das Datum (die WP-Cron läuft täglich, die Action
                            wöchentlich — ohne Dedupe entstünden Duplikate).

Die Prozentwerte sind Anteile an den Downloads über den Raspberry Pi Imager,
nicht an der installierten Basis.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rpi_stats_parser import parse_stats_page, sanity_check

SOURCE_URL = "https://rpi-imager-stats.raspberrypi.com/"
DATA_DIR = "data"
CURRENT_FILE = os.path.join(DATA_DIR, "rpi_os_stats.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

# Nur diese Dimensionen wandern in die Zeitreihe. `image` und `version` sind
# extrem kleinteilig (jede Point-Release eigene Zeile) und würden history.json
# aufblähen, ohne inhaltlich etwas zu tragen.
HISTORY_DIMENSIONS = ("os", "host_arch", "locale")

# Zeitraum für die Zeitreihe: das rollierende Monatsfenster ist die einzige
# Reihe, die man sinnvoll als Trend zeichnen kann. `today` ist ein Tages-
# Schnappschuss und schwankt je nach Abrufzeitpunkt um mehrere Prozentpunkte.
HISTORY_PERIOD = "month"


def fetch_html(url):
    # Import erst hier: mit --from-file läuft das Script ohne requests.
    import requests

    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "rpi-os-trends/2.0 (+https://raspberry.tips)"},
    )
    response.raise_for_status()
    return response.text


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {"source": SOURCE_URL, "period": HISTORY_PERIOD, "points": []}
    with open(HISTORY_FILE, encoding="utf-8") as f:
        return json.load(f)


def build_point(date_iso, parsed):
    point = {"date": date_iso}
    for dim in HISTORY_DIMENSIONS:
        rows = parsed.get(dim, {}).get(HISTORY_PERIOD)
        if not rows:
            continue
        # Auf zwei Nachkommastellen runden — die Quelle liefert nicht mehr,
        # und Float-Rauschen wie 28.219999999999998 hat in der Ausgabe nichts
        # verloren (stand so im ausgelieferten Chart).
        point[dim] = {r["name"]: round(r["value"], 2) for r in rows}
    return point


def main(argv=None):
    ap = argparse.ArgumentParser(description="Raspberry-Pi-Imager-Statistiken abrufen und fortschreiben.")
    ap.add_argument(
        "--from-file",
        metavar="HTML",
        help="Statt der Quellseite eine lokal gespeicherte Kopie parsen (Test ohne Netz).",
    )
    ap.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="Datum für den Zeitreihen-Punkt überschreiben (nur mit --from-file sinnvoll).",
    )
    args = ap.parse_args(argv)

    if args.from_file:
        print("Lese lokale Kopie: %s" % args.from_file)
        try:
            with open(args.from_file, encoding="utf-8", errors="replace") as f:
                html = f.read()
        except OSError as exc:
            print("FEHLER beim Lesen: %s" % exc)
            return 1
    else:
        print("Abrufen der Statistiken von %s ..." % SOURCE_URL)
        try:
            html = fetch_html(SOURCE_URL)
        except Exception as exc:
            print("FEHLER beim Abruf: %s" % exc)
            return 1

    parsed = parse_stats_page(html)
    if not parsed.get("os"):
        print("FEHLER: Keine OS-Tabelle gefunden — Struktur der Quelle geändert?")
        return 1

    warnings = sanity_check(parsed)
    for w in warnings:
        print("WARNUNG: %s" % w)
    if warnings:
        # Lieber gar nicht schreiben als kaputte Zahlen veröffentlichen.
        print("Abbruch: Plausibilitätsprüfung fehlgeschlagen, Daten bleiben unverändert.")
        return 1

    now = datetime.now(timezone.utc)
    date_iso = args.date or now.strftime("%Y-%m-%d")

    os.makedirs(DATA_DIR, exist_ok=True)

    # --- aktueller Stand ---
    os_today = parsed["os"].get("today", [])
    current = {
        "last_updated": now.strftime("%d.%m.%Y %H:%M"),
        "last_updated_iso": now.isoformat(timespec="seconds"),
        "source": SOURCE_URL,
        # Rückwärtskompatibel: das ausgerollte WP-Plugin liest genau diesen Key.
        "top_10": [
            {"name": r["name"], "value": round(r["value"], 2), "label": r["label"]}
            for r in os_today[:10]
        ],
        "snapshot": {
            dim: {per: [
                {"name": r["name"], "value": round(r["value"], 2), "label": r["label"]}
                for r in rows
            ] for per, rows in periods.items()}
            for dim, periods in parsed.items()
        },
    }
    with open(CURRENT_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=4, ensure_ascii=False)
        f.write("\n")
    print("Geschrieben: %s (Top 1: %s %.2f%%)" % (
        CURRENT_FILE, os_today[0]["name"], os_today[0]["value"]))

    # --- Zeitreihe fortschreiben ---
    history = load_history()
    point = build_point(date_iso, parsed)
    points = [p for p in history.get("points", []) if p.get("date") != date_iso]
    points.append(point)
    points.sort(key=lambda p: p["date"])
    history["points"] = points
    history["source"] = SOURCE_URL
    history["period"] = HISTORY_PERIOD
    history["generated"] = now.isoformat(timespec="seconds")

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("Geschrieben: %s (%d Datenpunkte, %s .. %s)" % (
        HISTORY_FILE, len(points), points[0]["date"], points[-1]["date"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
