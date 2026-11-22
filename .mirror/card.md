# Raspberry Pi Imager OS Download Shares (2021–2026)

Which operating systems do people write to SD cards and SSDs with the official **Raspberry Pi Imager**? The public statistics page [rpi-imager-stats.raspberrypi.com](https://rpi-imager-stats.raspberrypi.com/) only shows the current 30-day window. This dataset turns it into a time series that goes back to **October 2021**.

- **Interactive charts and method:** [raspberry.tips – Raspberry Pi OS statistics](https://raspberry.tips/en/raspberry-pi-os-statistics) (German: [raspberry.tips/raspberry-pi-os-statistik-trends](https://raspberry.tips/raspberry-pi-os-statistik-trends))
- **Source repository (scraper, parser tests, weekly updates):** [github.com/raspberry-tips/rpi-os-trends](https://github.com/raspberry-tips/rpi-os-trends)
- **Citable, versioned archive:** [doi.org/10.5281/zenodo.23269998](https://doi.org/10.5281/zenodo.23269998)

This is a mirror. The GitHub repository is the canonical source and updates first.

## Files

| File | Content |
|---|---|
| `history.csv` | Flat time series: `date, dimension, label, percent` |
| `history.json` | The same series as JSON, one entry per date |
| `rpi_os_stats.json` | Latest snapshot with all dimensions and all three time windows of the source |

Dimensions:
- `os`: operating system or image family
- `host_arch`: CPU architecture of the computer **running the Imager** (mostly x86_64). This is not the bitness of the image.
- `locale`: Imager UI language

## How the data was built

- **History 2021–2026:** reconstructed from 104 Internet Archive captures of the statistics page. Each point uses the source's rolling 30-day window.
- **Since 2026:** a weekly scraper adds new points. It aborts when the OS shares sum to less than 80 %, because no data is better than silently wrong data.
- **Pitfall in the source:** the table header consists of bare header cells (th) without an enclosing table row (tr). An earlier parser therefore skipped the first real data row and dropped the top OS (Raspberry Pi OS 64-bit, ~37 %). The current parser only counts rows that contain data cells (td) and is covered by a regression test.

## Caveats

- Values are **shares of Imager downloads**, not of installed systems. Images written with `dd`, vendor flashers or other tools are not counted.
- In **late 2023** the source started reporting 64-bit Raspberry Pi OS separately. The resulting break in the series reflects a change in counting, not in user behaviour.
- The `today` and `week` windows of the source fluctuate heavily depending on when they are fetched. The time series uses the monthly window only.

## Citation

Philipp Schweizer, *Raspberry Pi Imager OS statistics (rpi-os-trends)*, raspberry.tips. DOI: [10.5281/zenodo.23269998](https://doi.org/10.5281/zenodo.23269998)

## License

Data: CC BY 4.0. Please credit "raspberry.tips" and link to the source. Code in the source repository: MIT.
