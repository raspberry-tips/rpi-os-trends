# Raspberry Pi OS Popularity Tracker 📊

This tool automatically tracks the popularity of different operating systems within the Raspberry Pi ecosystem. It utilizes official telemetry data from the Raspberry Pi Imager to provide up-to-date trends and usage statistics.

## 🚀 Features

- **Automated Data Fetching:** A Python-based scraper retrieves the latest stats from the official [Raspberry Pi Imager Statistics dashboard](https://rpi-imager-stats.raspberrypi.com/).
- **GitHub Actions Integration:** The data is updated automatically every Monday via a built-in CI/CD workflow.
- **Clean Data Format:** Results are saved in a structured `data/rpi_os_stats.json` file, perfect for integration into web dashboards, WordPress sites, or research projects.

## 🛠️ Components

- `scripts/fetch_rpi_os_stats.py`: The core scraping logic using `BeautifulSoup4`.
- `.github/workflows/update_os_stats.yml`: The automation engine that keeps the data fresh.
- `data/rpi_os_stats.json`: The latest captured dataset.

## 📦 Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/raspberry-tips/rpi-os-trends.git
   cd rpi-os-trends
   ```

2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run manually:**
   ```bash
   python scripts/fetch_rpi_os_stats.py
   ```

## 📈 Integration

You can easily visualize this data using libraries like **Chart.js**. Simply fetch the `data/rpi_os_stats.json` file and map the `top_10` array to your chart axes.

---
*Maintained by [raspberry.tips](https://raspberry.tips)*
