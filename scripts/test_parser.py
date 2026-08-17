"""Selbsttest des Parsers — läuft ohne Netz in der GitHub Action.

Der wichtigste Fall ist der erste: Die Quellseite schreibt ihre Kopfzeile als
blanke <th> OHNE umschliessendes <tr>. lxml ergänzt kein <tr>, deshalb war
find_all('tr')[0] bereits die erste Datenzeile — ein `rows[1:]` verschluckte
den Spitzenreiter. Genau so lief das von Mai bis August 2026 unbemerkt live:
veröffentlicht wurden die Plätze 2 bis 11, in Summe rund 52 statt 90 Prozent.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rpi_stats_parser import parse_stats_page, sanity_check

FIXTURE = """
<html><body>
<table class="table mt-4">
  <caption>Downloads by operating system today</caption>
  <thead>
    <th scope="col">Operating System</th>
    <th scope="col">Percentage</th>
  </thead>
  <tbody>
    <tr><th scope="row">Raspberry Pi OS (64-bit)</th><td>37.14%</td></tr>
    <tr><th scope="row">Raspberry Pi OS (other)</th><td>25.27%</td></tr>
    <tr><th scope="row">Home Assistant</th><td>7.14%</td></tr>
    <tr><th scope="row">Ubuntu</th><td>6.22%</td></tr>
    <tr><th scope="row">Raspberry Pi OS (32-bit)</th><td>24.23%</td></tr>
  </tbody>
</table>
<table class="table mt-4">
  <caption>Downloads by operating system from the past month</caption>
  <thead>
    <th scope="col">Operating System</th><th scope="col">Percentage</th>
  </thead>
  <tbody>
    <tr><th scope="row">Raspberry Pi OS (64-bit)</th><td>36.34%</td></tr>
    <tr><th scope="row">Raspberry Pi OS (other)</th><td>63.66%</td></tr>
  </tbody>
</table>
<table class="table mt-4">
  <caption>Downloads by Raspberry Pi Imager OS architecture from the past month</caption>
  <thead><tr><th scope="col">Architecture</th><th scope="col">Percentage</th></tr></thead>
  <tbody>
    <tr><th scope="row">arm64</th><td>70.00%</td></tr>
    <tr><th scope="row">armhf</th><td>30.00%</td></tr>
  </tbody>
</table>
<table class="table mt-4">
  <caption>Downloads by Raspberry Pi Imager locale from the past month</caption>
  <thead><th scope="col">Locale</th><th scope="col">Percentage</th></thead>
  <tbody>
    <tr><th scope="row">en</th><td>60.00%</td></tr>
    <tr><th scope="row">de</th><td>40.00%</td></tr>
  </tbody>
</table>
</body></html>
"""

failures = []


def check(label, cond, detail=""):
    if cond:
        print("  ok    %s" % label)
    else:
        print("  FEHLT %s %s" % (label, detail))
        failures.append(label)


def main():
    print("Parser-Selbsttest")
    parsed = parse_stats_page(FIXTURE)

    os_today = parsed.get("os", {}).get("today", [])
    check("OS/today gefunden", len(os_today) == 5, "(%d Zeilen)" % len(os_today))
    check(
        "Spitzenreiter nicht abgeschnitten",
        bool(os_today) and os_today[0]["name"] == "Raspberry Pi OS (64-bit)",
        "(erster Eintrag: %s)" % (os_today[0]["name"] if os_today else "-"),
    )
    check(
        "Kopfzeile nicht als Datenzeile",
        all(r["name"] != "Operating System" for r in os_today),
    )
    check("Wert korrekt geparst", bool(os_today) and abs(os_today[0]["value"] - 37.14) < 1e-9)

    # thead MIT <tr> muss genauso funktionieren wie ohne — der Parser darf nicht
    # davon abhängen, was der jeweilige HTML-Parser ergänzt.
    arch = parsed.get("host_arch", {}).get("month", [])
    check("host_arch/month gefunden (thead mit <tr>)", len(arch) == 2, "(%d Zeilen)" % len(arch))
    check("host_arch ohne Kopfzeile", all(r["name"] != "Architecture" for r in arch))

    locale = parsed.get("locale", {}).get("month", [])
    check("locale/month gefunden", len(locale) == 2, "(%d Zeilen)" % len(locale))

    os_month = parsed.get("os", {}).get("month", [])
    check("OS/month getrennt von OS/today", len(os_month) == 2, "(%d Zeilen)" % len(os_month))

    check("sanity_check meldet nichts bei 100%%", sanity_check(parsed) == [])

    # Regression: eine um den Spitzenreiter gekürzte Verteilung muss auffallen.
    truncated = {"os": {"month": os_month[1:]}}
    check("sanity_check erkennt fehlende Zeilen", len(sanity_check(truncated)) > 0)

    print()
    if failures:
        print("FEHLGESCHLAGEN: %d Prüfung(en) — %s" % (len(failures), ", ".join(failures)))
        return 1
    print("Alle Prüfungen bestanden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
