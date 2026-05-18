import requests
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup

# Konfiguration
SOURCE_URL = "https://rpi-imager-stats.raspberrypi.com/"
OUTPUT_FILE = "data/rpi_os_stats.json"

def fetch_stats():
    print(f"Abrufen der Statistiken von {SOURCE_URL}...")
    try:
        response = requests.get(SOURCE_URL, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Wir suchen die erste Tabelle auf der Seite (Downloads today)
        table = soup.find('table')
        if not table:
            print("❌ Keine Tabelle in der HTML-Antwort gefunden.")
            return
            
        rows = table.find_all('tr')
        stats_list = []
        
        for row in rows[1:]: # Überspringe den Header
            cols = row.find_all(['th', 'td'])
            if len(cols) == 2:
                os_name = cols[0].get_text(strip=True)
                percentage = cols[1].get_text(strip=True)
                
                # Bereinige Prozentwert (z.B. "38.58%" -> 38.58)
                numeric_value = float(percentage.replace('%', ''))
                
                stats_list.append({
                    "name": os_name,
                    "value": numeric_value,
                    "label": percentage
                })
        
        # Datenstruktur für das Dashboard
        data = {
            "last_updated": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "source": SOURCE_URL,
            "top_10": stats_list[:10]
        }
        
        # Speichern als JSON
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Statistiken erfolgreich gespeichert: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"❌ Fehler beim Abrufen der Statistiken: {e}")

if __name__ == "__main__":
    fetch_stats()
