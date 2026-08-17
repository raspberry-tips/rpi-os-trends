# rpi-os-trends

Sammelt die Download-Statistiken des Raspberry Pi Imager von
<https://rpi-imager-stats.raspberrypi.com/> und schreibt sie als Zeitreihe fort.
Datenbasis für <https://raspberry.tips/raspberry-pi-os-statistik-trends>.

Die Prozentwerte sind **Anteile an den Downloads über den Raspberry Pi Imager** —
nicht an der installierten Basis. Wer sein Image per `dd`, dem Hersteller-Flasher
oder aus dem Distributions-Repo schreibt, taucht hier nicht auf.

## Dateien

| Pfad | Inhalt |
|------|--------|
| `data/rpi_os_stats.json` | Aktueller Stand. `top_10` bleibt aus Kompatibilitätsgründen erhalten, `snapshot` enthält alle Dimensionen und Zeiträume. |
| `data/history.json` | Zeitreihe, ein Punkt je Tag, rollierendes 30-Tage-Fenster. |
| `scripts/rpi_stats_parser.py` | Gemeinsamer Parser für Live-Abruf und Backfill. |
| `scripts/fetch_rpi_os_stats.py` | Wöchentlicher Abruf, schreibt beide Datendateien. |
| `scripts/backfill_from_wayback.py` | Einmaliger Backfill aus dem Internet Archive. |
| `scripts/test_parser.py` | Regressionstest, läuft ohne Netz in der Action. |

## Die Quelle hat eine Falle

Die Tabellen der Quellseite schreiben ihre Kopfzeile als blanke `<th>` **ohne
umschliessendes `<tr>`**:

```html
<thead>
  <th scope="col">Operating System</th>
  <th scope="col">Percentage</th>
</thead>
```

lxml ergänzt dafür kein `<tr>`. `table.find_all('tr')[0]` ist damit bereits die
erste **Daten**zeile, nicht die Kopfzeile. Die erste Fassung dieses Scripts
übersprang mit `rows[1:]` eine Zeile zu viel und veröffentlichte von Mai bis
August 2026 die Plätze 2 bis 11 als „Top 10" — ohne den Spitzenreiter
*Raspberry Pi OS (64-bit)* mit rund 37 %. Die publizierte Verteilung summierte
sich auf etwa 52 % statt auf 90 %.

Der Parser filtert deshalb auf Zeilen, die tatsächlich ein `<td>` enthalten. Das
ist unabhängig davon, ob ein HTML-Parser das fehlende `<tr>` ergänzt oder nicht.
`scripts/test_parser.py` prüft beide Varianten und läuft vor jedem Abruf.

Zusätzlich bricht `fetch_rpi_os_stats.py` ab, wenn die OS-Verteilung sich auf
unter 80 % summiert — lieber keine neuen Daten als stillschweigend falsche.

## Zeitraum: heute, Woche oder Monat?

Die Quelle liefert jede Dimension in drei Fenstern. Für die Zeitreihe zählt nur
das **Monatsfenster**. Die `today`-Tabelle ist ein Tages-Schnappschuss und
schwankt je nach Abrufzeitpunkt erheblich: in der eigenen Sammlung von Mai bis
August 2026 sprang „Raspberry Pi OS (32-bit)" zwischen 4,39 % und 11,61 %,
Ubuntu zwischen 4,83 % und 9,43 %. Das ist Abrufzeitpunkt-Rauschen, kein Trend.

## Backfill

Die eigene Sammlung beginnt im Mai 2026. Das Internet Archive hat die Quellseite
dagegen seit Oktober 2021 gespiegelt, samt Monatstabellen. Ablauf:

```bash
curl -sL "http://web.archive.org/cdx/search/cdx?url=rpi-imager-stats.raspberrypi.com&output=text&fl=timestamp,statuscode,digest&collapse=digest" -o cdx.txt
bash scripts/fetch_all_wayback.sh          # lädt nach wb/
python scripts/backfill_from_wayback.py wb/ data/history.json
```

Verfügbarkeit der Dimensionen im Archiv: `os` ab Oktober 2021, `locale` und
`arch` ab Februar 2022.

## Weiterverwendung in WordPress

`wordpress/rpi-os-trends-sync.php` zieht beide JSON-Dateien in WordPress-Optionen
und rendert sie über die Shortcodes `[rpi_os_stats]` und `[rpi_os_history]`
**serverseitig**. Wichtig aus zwei Gründen:

- Die Content-Security-Policy von raspberry.tips erlaubt `connect-src` nur
  `'self'` — ein Fetch auf `raw.githubusercontent.com` aus dem Browser wäre
  blockiert.
- Bis v1 standen die Zahlen ausschliesslich in einem `<script>`-Block. Im
  ausgelieferten HTML einer Seite, deren gesamter Wert die Statistik ist, kam
  keine einzige Zahl vor — schlecht für alle Crawler, die kein JavaScript
  ausführen.

Ausserdem fasst v2 den Seiteninhalt nicht mehr an. v1 schrieb den Post per
`wp_update_post` täglich neu, was `post_modified` und damit `lastmod` in der
Sitemap ohne inhaltlichen Grund hochzählte.
