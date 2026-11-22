# rpi-os-trends

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23269998.svg)](https://doi.org/10.5281/zenodo.23269998)

**English** · [Deutsch](#deutsch)

Collects the download statistics of the Raspberry Pi Imager from
<https://rpi-imager-stats.raspberrypi.com/> and keeps them as a time series
going back to October 2021. Charts and method:
<https://raspberry.tips/en/raspberry-pi-os-statistics> (German:
<https://raspberry.tips/raspberry-pi-os-statistik-trends>).

The percentages are **shares of downloads through the Raspberry Pi Imager**, not
of the installed base. Anyone who writes their image with `dd`, a vendor flasher
or straight from a distribution's repository does not show up here.

### Files

| Path | Content |
|------|---------|
| `data/rpi_os_stats.json` | Latest snapshot. `top_10` is kept for backwards compatibility, `snapshot` holds every dimension and time window. |
| `data/history.json` | Time series, one point per day, rolling 30-day window. |
| `data/history.csv` | The same series as a flat table: `date, dimension, label, percent` (dimensions `os`, `host_arch`, `locale`). |
| `scripts/export_csv.py` | Builds `history.csv` from `history.json`; runs as part of the fetch script. |
| `scripts/rpi_stats_parser.py` | Shared parser for live fetches and the backfill. |
| `scripts/fetch_rpi_os_stats.py` | Weekly fetch, writes both data files. |
| `scripts/backfill_from_wayback.py` | One-off backfill from the Internet Archive. |
| `scripts/test_parser.py` | Regression test; runs offline inside the GitHub Action. |

`host_arch` is the CPU architecture of the computer **running the Imager**
(mostly x86_64), not the bitness of the image that was written.

### The source has a trap

The tables on the source page write their header row as bare `<th>` cells
**without an enclosing `<tr>`**:

```html
<thead>
  <th scope="col">Operating System</th>
  <th scope="col">Percentage</th>
</thead>
```

lxml does not add the missing `<tr>`, so `table.find_all('tr')[0]` is already
the first **data** row, not the header. The first version of this script skipped
one row too many with `rows[1:]`. From May to August 2026 it published ranks 2
to 11 as the "top 10", leaving out the leader, *Raspberry Pi OS (64-bit)* at
about 37 %. The published distribution added up to roughly 52 % instead of 90 %.

The parser therefore only keeps rows that actually contain a `<td>`. That works
whether or not an HTML parser inserts the missing `<tr>`. `scripts/test_parser.py`
checks both cases and runs before every fetch.

On top of that, `fetch_rpi_os_stats.py` aborts if the OS shares add up to less
than 80 %. No new data is better than silently wrong data.

### Today, week or month?

The source reports every dimension in three windows. The time series only uses
the **monthly window**. The `today` table is a one-day snapshot and swings a lot
depending on when it is fetched. In our own collection from May to August 2026,
"Raspberry Pi OS (32-bit)" jumped between 4.39 % and 11.61 % and Ubuntu between
4.83 % and 9.43 %. That is noise from the fetch time, not a trend.

### Break in the series (late 2023)

At the end of 2023 the source started listing 64-bit Raspberry Pi OS separately.
The kink in the series at that point reflects a change in how downloads are
counted, not a change in what people use. Raspberry Pi OS as a whole is the
robust figure: about 60 % in 2021, about 70 % in 2026.

### Backfill

Our own collection starts in May 2026. The Internet Archive, however, has been
capturing the source page since October 2021, monthly tables included:

```bash
curl -sL "http://web.archive.org/cdx/search/cdx?url=rpi-imager-stats.raspberrypi.com&output=text&fl=timestamp,statuscode,digest&collapse=digest" -o cdx.txt
bash scripts/fetch_all_wayback.sh          # downloads into wb/
python scripts/backfill_from_wayback.py wb/ data/history.json
```

Dimensions available in the archive: `os` from October 2021, `locale` and
`arch` from February 2022.

### Use in WordPress

`wordpress/rpi-os-trends-sync.php` pulls both JSON files into WordPress options
and renders them **server-side** through the shortcodes `[rpi_os_stats]` and
`[rpi_os_history]`. There are two reasons for that:

- The Content Security Policy of raspberry.tips only allows `connect-src 'self'`,
  so a browser fetch from `raw.githubusercontent.com` would be blocked.
- Up to v1 the numbers only lived inside a `<script>` block. A page whose whole
  point is the statistics did not contain a single number in its delivered HTML,
  which is bad for every crawler that does not run JavaScript.

Also, v2 no longer touches the page content. v1 rewrote the post daily via
`wp_update_post`, which bumped `post_modified` and with it the sitemap `lastmod`
for no actual change.

### License and citation

Data (`data/`) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
code under MIT, see `LICENSE`. The underlying percentages are published by
Raspberry Pi Ltd. CC BY covers the compilation and time series in this
repository.

Suggested citation (metadata in `CITATION.cff`, GitHub offers "Cite this repository"):

> Schweizer, P. (2026). *Raspberry Pi Imager download statistics: time series
> 2021–2026 (rpi-os-trends)* [Data set]. raspberry.tips.
> https://doi.org/10.5281/zenodo.23269998

The DOI above is the concept DOI and always resolves to the latest version.
Each version also has its own DOI (first version: 10.5281/zenodo.23269999).

---

## Deutsch

Sammelt die Download-Statistiken des Raspberry Pi Imager von
<https://rpi-imager-stats.raspberrypi.com/> und schreibt sie als Zeitreihe fort.
Datenbasis für <https://raspberry.tips/raspberry-pi-os-statistik-trends>.

Die Prozentwerte sind **Anteile an den Downloads über den Raspberry Pi Imager** —
nicht an der installierten Basis. Wer sein Image per `dd`, dem Hersteller-Flasher
oder aus dem Distributions-Repo schreibt, taucht hier nicht auf.

### Dateien

| Pfad | Inhalt |
|------|--------|
| `data/rpi_os_stats.json` | Aktueller Stand. `top_10` bleibt aus Kompatibilitätsgründen erhalten, `snapshot` enthält alle Dimensionen und Zeiträume. |
| `data/history.json` | Zeitreihe, ein Punkt je Tag, rollierendes 30-Tage-Fenster. |
| `data/history.csv` | Dieselbe Zeitreihe flach: `date, dimension, label, percent` (Dimensionen `os`, `host_arch`, `locale`). |
| `scripts/export_csv.py` | Erzeugt `history.csv` aus `history.json`, läuft im Fetch-Script mit. |
| `scripts/rpi_stats_parser.py` | Gemeinsamer Parser für Live-Abruf und Backfill. |
| `scripts/fetch_rpi_os_stats.py` | Wöchentlicher Abruf, schreibt beide Datendateien. |
| `scripts/backfill_from_wayback.py` | Einmaliger Backfill aus dem Internet Archive. |
| `scripts/test_parser.py` | Regressionstest, läuft ohne Netz in der Action. |

### Die Quelle hat eine Falle

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

### Zeitraum: heute, Woche oder Monat?

Die Quelle liefert jede Dimension in drei Fenstern. Für die Zeitreihe zählt nur
das **Monatsfenster**. Die `today`-Tabelle ist ein Tages-Schnappschuss und
schwankt je nach Abrufzeitpunkt erheblich: in der eigenen Sammlung von Mai bis
August 2026 sprang „Raspberry Pi OS (32-bit)" zwischen 4,39 % und 11,61 %,
Ubuntu zwischen 4,83 % und 9,43 %. Das ist Abrufzeitpunkt-Rauschen, kein Trend.

### Backfill

Die eigene Sammlung beginnt im Mai 2026. Das Internet Archive hat die Quellseite
dagegen seit Oktober 2021 gespiegelt, samt Monatstabellen. Ablauf:

```bash
curl -sL "http://web.archive.org/cdx/search/cdx?url=rpi-imager-stats.raspberrypi.com&output=text&fl=timestamp,statuscode,digest&collapse=digest" -o cdx.txt
bash scripts/fetch_all_wayback.sh          # lädt nach wb/
python scripts/backfill_from_wayback.py wb/ data/history.json
```

Verfügbarkeit der Dimensionen im Archiv: `os` ab Oktober 2021, `locale` und
`arch` ab Februar 2022.

### Weiterverwendung in WordPress

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

### Lizenz und Zitieren

Daten (`data/`) unter [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
Code unter MIT — Details in `LICENSE`. Die zugrunde liegenden Prozentwerte
veröffentlicht Raspberry Pi Ltd; CC BY bezieht sich auf die Zusammenstellung
und Zeitreihe in diesem Repository.

Zitiervorschlag (Metadaten in `CITATION.cff`, GitHub zeigt dazu „Cite this repository"):

> Schweizer, P. (2026). *Raspberry Pi Imager download statistics: time series
> 2021–2026 (rpi-os-trends)* [Data set]. raspberry.tips.
> https://doi.org/10.5281/zenodo.23269998

Die DOI oben ist die Concept-DOI und zeigt immer auf die neueste Version.
Jede Version hat zusätzlich eine eigene DOI (erste Version: 10.5281/zenodo.23269999).
