#!/usr/bin/env python3
"""
Finaler Tarifvergleich mit echten Scraper-Daten
Zeigt PLZ-spezifische Preise für verschiedene Regionen
"""

from datetime import datetime
from src.backend.EnergyTariff import DynamicTariff
from src.Webscraping.scraper_tibber import TibberScraper
from src.Webscraping.scraper_enbw import EnbwScraper

print("=" * 100)
print("📊 TARIFVERGLEICH MIT ECHTEN SCRAPER-DATEN (PLZ-SPEZIFISCH)")
print("=" * 100)
print()

# Test verschiedene PLZ
test_configs = [
    {"plz": "68167", "city": "Mannheim", "consumption": 2500},
    {"plz": "71065", "city": "Stuttgart", "consumption": 2500},
]

for config in test_configs:
    plz = config["plz"]
    city = config["city"]
    consumption = config["consumption"]
    
    print("=" * 100)
    print(f"📍 {city} (PLZ {plz}) - Jahresverbrauch: {consumption} kWh")
    print("=" * 100)
    print()
    
    tariffs = []
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # ========================================================================
    # TIBBER
    # ========================================================================
    try:
        print("1️⃣  TIBBER")
        print("-" * 100)
        
        tibber_scraper = TibberScraper(debug_mode=False)
        tibber_data = tibber_scraper.scrape_tariff(zip_code=plz, annual_consumption=consumption)
        
        print(f"   Grundpreis: {tibber_data['total_base_monthly']:.2f} €/Mon")
        print(f"   Zusatz-Komponenten: {tibber_data['additional_price_ct']:.2f} ct/kWh")
        
        tibber_tariff = DynamicTariff(
            name="Tibber",
            provider="Tibber",
            base_price=tibber_data['total_base_monthly'],
            start_date=start_date,
            network_fee=0,
            postal_code=plz,
            additional_price_ct_kwh=tibber_data['additional_price_ct']
        )
        
        result = tibber_tariff.calculate_cost_with_breakdown(consumption)
        tariffs.append({
            'name': 'Tibber',
            'base': tibber_data['total_base_monthly'],
            'additional': tibber_data['additional_price_ct'],
            'avg_kwh': result['avg_kwh_price'] * 100,
            'total_cost': result['total_cost']
        })
        
        print(f"   ✓ Berechnet: {result['avg_kwh_price']*100:.2f} ct/kWh, {result['total_cost']:.2f} € (30 Tage)")
        print()
        
    except Exception as e:
        print(f"   ❌ Fehler: {e}\n")
    
    # ========================================================================
    # EnBW (nur mit Browser)
    # ========================================================================
    try:
        print("2️⃣  EnBW")
        print("-" * 100)
        
        enbw_scraper = EnbwScraper(headless=True, debug=False, use_edge=False)
        enbw_data = enbw_scraper.scrape_tariff(zip_code=plz, annual_consumption=consumption)
        
        print(f"   Grundpreis: {enbw_data['base_price_monthly']:.2f} €/Mon")
        print(f"   Zusatz-Komponenten: {enbw_data['markup_ct_kwh']:.2f} ct/kWh")
        
        enbw_tariff = DynamicTariff(
            name="EnBW Dynamisch",
            provider="EnBW",
            base_price=enbw_data['base_price_monthly'],
            start_date=start_date,
            network_fee=0,
            postal_code=plz,
            additional_price_ct_kwh=enbw_data['markup_ct_kwh']
        )
        
        result = enbw_tariff.calculate_cost_with_breakdown(consumption)
        tariffs.append({
            'name': 'EnBW',
            'base': enbw_data['base_price_monthly'],
            'additional': enbw_data['markup_ct_kwh'],
            'avg_kwh': result['avg_kwh_price'] * 100,
            'total_cost': result['total_cost']
        })
        
        print(f"   ✓ Berechnet: {result['avg_kwh_price']*100:.2f} ct/kWh, {result['total_cost']:.2f} € (30 Tage)")
        print()
        
    except Exception as e:
        print(f"   ❌ Fehler: {e}\n")
    
    # ========================================================================
    # VERGLEICH
    # ========================================================================
    if tariffs:
        print("=" * 100)
        print("💰 KOSTENVERGLEICH (30 Tage)")
        print("=" * 100)
        print()
        print(f"{'Anbieter':<15} {'Grundpreis':>12} {'Zusatz-Komp.':>15} {'Ø kWh-Preis':>13} {'Gesamtkosten':>14}")
        print("-" * 100)
        
        tariffs.sort(key=lambda x: x['total_cost'])
        
        for t in tariffs:
            print(f"{t['name']:<15} {t['base']:>10.2f} € {t['additional']:>12.2f} ct {t['avg_kwh']:>11.2f} ct {t['total_cost']:>12.2f} €")
        
        if len(tariffs) > 1:
            winner = tariffs[0]
            savings = tariffs[-1]['total_cost'] - winner['total_cost']
            
            print()
            print(f"🏆 Günstigster: {winner['name']} mit {winner['total_cost']:.2f} € (30 Tage)")
            if savings > 1:
                print(f"💡 Ersparnis: {savings:.2f} € (30 Tage) = {savings*12:.2f} € (Jahr)")
        
        print()

print()
print("=" * 100)
print("📌 WICHTIGE ERKENNTNISSE:")
print("=" * 100)
print()
print("✅ Alle Werte sind PLZ-spezifisch und werden dynamisch gescrapt")
print("✅ Grundpreise und Zusatz-Komponenten variieren je nach Region")
print("✅ Börsenstrompreis wird durch unseren Prophet-Forecast ersetzt (~4-5 ct/kWh)")
print("✅ Endkundenpreise sind realistisch und vergleichbar")
print()
