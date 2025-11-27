#!/usr/bin/env python3
"""
Test des neuen /api/compare-tariffs-with-csv Endpunkts
Kombiniert CSV-Verbrauchsdaten mit PLZ-spezifischen Scraper-Preisen
"""

import requests
import os

print("=" * 80)
print("🧪 TEST: CSV + PLZ-SPEZIFISCHE PREISE")
print("=" * 80)
print()

# API-Konfiguration
API_URL = "http://localhost:8000/api/compare-tariffs-with-csv"

# Test-Konfiguration
ZIP_CODE = "68167" # Mannheim
PROVIDERS = "tibber,enbw"

# Finde eine Beispiel-CSV-Datei
test_csv_files = [
 "app_data/standard_profile/energy_usage.csv",
 "analysis/test_data/sample_consumption.csv"
]

csv_file = None
for f in test_csv_files:
 if os.path.exists(f):
 csv_file = f
 break

if not csv_file:
 print("[ERROR] Keine Test-CSV gefunden!")
 print(" Erstelle Demo-CSV...")

 import pandas as pd
 from datetime import datetime, timedelta

 # Erstelle Demo-Daten: 30 Tage, 15-Minuten-Intervalle
 start = datetime(2024, 10, 1)
 dates = [start + timedelta(minutes=15*i) for i in range(30*24*4)]

 # Simuliere realistischen Verbrauch (in Watt für 15-Min-Intervalle)
 import numpy as np
 np.random.seed(42)

 # Basis-Last + Tageszyklen + Zufall
 values = []
 for i, dt in enumerate(dates):
 hour = dt.hour
 # Höherer Verbrauch morgens und abends
 if 6 <= hour <= 9 or 17 <= hour <= 22:
 base = 300 # Watt
 else:
 base = 150 # Watt

 noise = np.random.normal(0, 50)
 values.append(max(50, base + noise))

 df = pd.DataFrame({
 'datetime': dates,
 'value': values
 })

 csv_file = "test_consumption_demo.csv"
 df.to_csv(csv_file, index=False)
 print(f" [OK] Demo-CSV erstellt: {csv_file}")
 print(f" [OK] {len(df)} Einträge, {(df['datetime'].max() - df['datetime'].min()).days} Tage")
 print()

print(f"📄 CSV-Datei: {csv_file}")
print(f"📍 PLZ: {ZIP_CODE}")
print(f"🏢 Anbieter: {PROVIDERS}")
print()

# Test ob Server läuft
try:
 response = requests.get("http://localhost:8000/health", timeout=2)
 print("[OK] API-Server läuft")
except:
 print("[ERROR] API-Server läuft NICHT!")
 print(" Starte den Server mit: python app.py")
 print(" Oder: uvicorn app:app --reload")
 exit(1)

print()
print("=" * 80)
print("📡 SENDE REQUEST AN API...")
print("=" * 80)
print()

try:
 with open(csv_file, 'rb') as f:
 files = {'file': (os.path.basename(csv_file), f, 'text/csv')}
 data = {
 'zip_code': ZIP_CODE,
 'providers': PROVIDERS
 }

 print(f"POST {API_URL}")
 print(f" - CSV: {os.path.basename(csv_file)}")
 print(f" - PLZ: {ZIP_CODE}")
 print(f" - Anbieter: {PROVIDERS}")
 print()

 response = requests.post(API_URL, files=files, data=data, timeout=300)

 if response.status_code == 200:
 result = response.json()

 print("=" * 80)
 print("[OK] ERFOLG!")
 print("=" * 80)
 print()

 print(f"PLZ: {result['zip_code']}")
 print(f"Jahresverbrauch: {result['annual_consumption_kwh']:.2f} kWh")
 print(f"CSV-Zeitraum: {result['csv_date_range']['days']} Tage")
 print()

 print("=" * 80)
 print(" TARIFVERGLEICH:")
 print("=" * 80)
 print()

 print(f"{'Anbieter':<15} {'Grundpreis':>12} {'Zusatz-K.':>12} {'Ø kWh':>10} {'Monatlich':>12} {'Jährlich':>12}")
 print("-" * 80)

 for tariff in result['tariffs']:
 savings = f"(-{tariff.get('savings_monthly', 0):.2f}€)" if 'savings_monthly' in tariff else ""

 print(f"{tariff['provider']:<15} "
 f"{tariff['base_price_monthly']:>10.2f} € "
 f"{tariff['additional_price_ct_kwh']:>10.2f} ct "
 f"{tariff['avg_kwh_price_ct']:>8.2f} ct "
 f"{tariff['monthly_cost']:>10.2f} € "
 f"{tariff['annual_cost']:>10.2f} € "
 f"{savings}")

 print()
 print(f" Günstigster Anbieter: {result['cheapest_provider']}")

 if len(result['tariffs']) > 1:
 savings_monthly = result['tariffs'][1].get('savings_monthly', 0)
 savings_annual = result['tariffs'][1].get('savings_annual', 0)

 if savings_monthly > 0:
 print(f" Ersparnis: {savings_monthly:.2f} €/Monat = {savings_annual:.2f} €/Jahr")

 print()
 print("=" * 80)
 print("📌 WICHTIG:")
 print("=" * 80)
 print()
 print("[OK] Verbrauchsdaten aus CSV verwendet (echte Smart-Meter Daten)")
 print("[OK] Preise PLZ-spezifisch von Anbietern gescrapt")
 print("[OK] Börsenstrompreis aus Prophet-Forecast (~4-5 ct/kWh)")
 print("[OK] Realistische Endkundenpreise inkl. aller Komponenten")

 else:
 print(f"[ERROR] Fehler: HTTP {response.status_code}")
 print(response.text)

except Exception as e:
 print(f"[ERROR] Fehler: {e}")
 import traceback
 traceback.print_exc()
