"""Parser für rpi-imager-stats.raspberrypi.com.

Die Quellseite liefert 15 Tabellen: 5 Dimensionen (OS, Image, Imager-Version,
Locale, OS-Architektur) mal 3 Zeiträume (today, past week, past month).

WICHTIG: Der <thead> der Tabellen enthält blanke <th>-Elemente OHNE <tr>-Wrapper.
lxml erzeugt dafür keine Zeile, deshalb ist find_all('tr')[0] bereits die erste
Datenzeile. Ein `rows[1:]` verschluckt damit den Spitzenreiter. Wir filtern
stattdessen auf Zeilen, die tatsächlich ein <td> enthalten — das ist unabhängig
davon, ob der Parser ein <tr> ergänzt oder nicht.
"""

import re

from bs4 import BeautifulSoup

DIMENSIONS = [
    (re.compile(r"\boperating system\b", re.I), "os"),
    (re.compile(r"\bimager (version|OS architecture|locale)\b", re.I), None),  # siehe unten
    (re.compile(r"\bimage\b", re.I), "image"),
]

PERIODS = [
    (re.compile(r"from the past month", re.I), "month"),
    (re.compile(r"from the past week", re.I), "week"),
    (re.compile(r"\btoday\b", re.I), "today"),
]


def _dimension(caption):
    c = caption.lower()
    if "os architecture" in c:
        # ACHTUNG: Das ist die Architektur des RECHNERS, auf dem der Imager
        # läuft (aktuell rund 82 % x86_64), NICHT die Bitbreite des geschriebenen
        # Images. Die 32/64-Bit-Verteilung der Systeme steckt in den Zeilen
        # "Raspberry Pi OS (64-bit)" bzw. "(32-bit)" der os-/image-Tabellen.
        return "host_arch"
    if "locale" in c:
        return "locale"
    if "imager version" in c or "raspberry pi imager version" in c:
        return "version"
    if "operating system" in c:
        return "os"
    if "by image" in c:
        return "image"
    return None


def _period(caption):
    for rx, name in PERIODS:
        if rx.search(caption):
            return name
    return None


def parse_stats_page(html):
    """Gibt {"os": {"today": [...], "week": [...], "month": [...]}, ...} zurück.

    Jeder Eintrag ist {"name": str, "value": float, "label": str}, absteigend
    sortiert wie in der Quelle.
    """
    soup = BeautifulSoup(html, "lxml")
    out = {}

    for table in soup.find_all("table"):
        cap_el = table.find("caption")
        if not cap_el:
            continue
        caption = cap_el.get_text(strip=True)
        dim = _dimension(caption)
        per = _period(caption)
        if not dim or not per:
            continue

        rows = []
        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            # Nur echte Datenzeilen: genau zwei Zellen UND mindestens ein <td>.
            # Die Kopfzeile besteht ausschliesslich aus <th> und fliegt so raus,
            # egal ob sie in einem <tr> steckt oder nicht.
            if len(cells) != 2 or tr.find("td") is None:
                continue
            name = cells[0].get_text(strip=True)
            label = cells[1].get_text(strip=True)
            try:
                value = float(label.replace("%", "").replace(",", ".").strip())
            except ValueError:
                continue
            if not name:
                continue
            rows.append({"name": name, "value": value, "label": label})

        if rows:
            out.setdefault(dim, {})[per] = rows

    return out


def sanity_check(parsed):
    """Plausibilitätsprüfung. Gibt eine Liste von Warnungen zurück (leer = ok)."""
    warnings = []
    os_month = parsed.get("os", {}).get("month") or parsed.get("os", {}).get("today")
    if not os_month:
        warnings.append("Keine OS-Tabelle gefunden")
        return warnings

    total = sum(r["value"] for r in os_month)
    if total < 80:
        warnings.append(
            "OS-Verteilung summiert nur %.2f%% — vermutlich fehlen Zeilen "
            "(Regressionsverdacht: abgeschnittener Spitzenreiter)" % total
        )
    if total > 101:
        warnings.append("OS-Verteilung summiert %.2f%% — Doppelzählung?" % total)

    names = [r["name"] for r in os_month]
    if not any("Raspberry Pi OS" in n for n in names[:3]):
        warnings.append(
            "Kein 'Raspberry Pi OS' unter den Top 3 (%s) — Struktur geändert?" % names[:3]
        )
    return warnings
