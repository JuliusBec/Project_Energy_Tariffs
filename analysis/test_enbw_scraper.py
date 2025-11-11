#!/usr/bin/env python3
"""
Test EnBW Scraper für PLZ 68167 (Mannheim)
"""

from src.Webscraping.scraper_enbw import EnbwScraper

print("=" * 80)
print("🧪 TEST: EnBW SCRAPER für PLZ 68167")
print("=" * 80)
print()

scraper = EnbwScraper(headless=True, debug=True, use_edge=False)

try:
    result = scraper.scrape_tariff(
        zip_code="68167",
        annual_consumption=2500
    )
    
    print()
    print("=" * 80)
    print("📊 SCRAPER RESULTS:")
    print("=" * 80)
    print()
    
    for key, value in result.items():
        if isinstance(value, float):
            print(f"{key:30s}: {value:.2f}")
        else:
            print(f"{key:30s}: {value}")
    
    print()
    print("=" * 80)
    print("🎯 WICHTIGE WERTE FÜR INTEGRATION:")
    print("=" * 80)
    print()
    
    if 'base_price_monthly' in result:
        print(f"✓ Grundpreis (base_price):        {result['base_price_monthly']:.2f} €/Monat")
    
    if 'markup_ct_kwh' in result:
        print(f"✓ Arbeitspreis (markup):          {result['markup_ct_kwh']:.2f} ct/kWh")
        print(f"  → Dies sind die Zusatz-Komponenten (Netzentgelte + Steuern + Umlagen)")
    
    if 'exchange_price_ct_kwh' in result:
        print(f"✓ Börsenpreis (Durchschnitt):     {result['exchange_price_ct_kwh']:.2f} ct/kWh")
        print(f"  → Wird durch unseren Forecast ersetzt")
    
    print()
    
except Exception as e:
    print(f"❌ Fehler: {e}")
    import traceback
    traceback.print_exc()
