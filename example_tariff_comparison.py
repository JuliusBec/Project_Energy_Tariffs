#!/usr/bin/env python3
"""
Beispiel: Tarifvergleich mit dynamischen Preisen aus Scrapers
Zeigt, wie man verschiedene Anbieter vergleicht mit regionalspezifischen Preisen
"""

from datetime import datetime
from src.backend.EnergyTariff import DynamicTariff
from src.Webscraping.scraper_tibber import TibberScraper
from src.Webscraping.scraper_enbw import EnbwScraper

print("=" * 80)
print("📊 TARIFVERGLEICH MIT SCRAPER-INTEGRATION")
print("=" * 80)
print()

# Konfiguration
ZIP_CODE = "71065"  # Stuttgart
ANNUAL_CONSUMPTION = 2500  # kWh
START_DATE = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

print(f"🏠 Standort: PLZ {ZIP_CODE}")
print(f"⚡ Jahresverbrauch: {ANNUAL_CONSUMPTION} kWh")
print()

# Liste für Tarife
tariffs = []

# ============================================================================
# 1. TIBBER
# ============================================================================
print("=" * 80)
print("1️⃣  TIBBER")
print("=" * 80)
print()

try:
    scraper = TibberScraper(debug_mode=False)
    tibber_data = scraper.scrape_tariff(
        zip_code=ZIP_CODE,
        annual_consumption=ANNUAL_CONSUMPTION
    )
    
    print(f"✓ Grundpreis: {tibber_data['total_base_monthly']:.2f} €/Monat")
    print(f"✓ Netzentgelte + Steuern: {tibber_data['additional_price_ct']:.2f} ct/kWh")
    print(f"✓ Datenquelle: {tibber_data['data_source']}")
    
    tibber_tariff = DynamicTariff(
        name="Tibber Dynamic",
        provider="Tibber",
        base_price=tibber_data['total_base_monthly'],
        start_date=START_DATE,
        network_fee=0,
        postal_code=ZIP_CODE,
        additional_price_ct_kwh=tibber_data['additional_price_ct']
    )
    
    tariffs.append(("Tibber", tibber_tariff))
    print("✅ Tarif konfiguriert\n")
    
except Exception as e:
    print(f"❌ Fehler: {e}\n")

# ============================================================================
# 2. EnBW (optional, wenn Scraper verfügbar)
# ============================================================================
print("=" * 80)
print("2️⃣  EnBW")
print("=" * 80)
print()

try:
    # EnBW nutzt unterschiedliche Markup-Struktur
    # Für Demo verwenden wir manuelle Werte (Scraper benötigt Browser)
    
    print("ℹ️  Verwende Demo-Werte (EnBW-Scraper benötigt Browser)")
    
    enbw_tariff = DynamicTariff(
        name="EnBW mobility+ dynamic",
        provider="EnBW",
        base_price=14.90,  # €/Monat
        start_date=START_DATE,
        network_fee=18.00,  # Einmalige Netznutzungsgebühr
        postal_code=ZIP_CODE,
        additional_price_ct_kwh=19.5  # EnBW hat oft etwas höhere Netzentgelte
    )
    
    tariffs.append(("EnBW", enbw_tariff))
    print("✅ Tarif konfiguriert (Demo-Werte)\n")
    
except Exception as e:
    print(f"❌ Fehler: {e}\n")

# ============================================================================
# 3. VERGLEICHSBERECHNUNG
# ============================================================================
print("=" * 80)
print("💰 KOSTENVERGLEICH (30 Tage)")
print("=" * 80)
print()

results = []

for name, tariff in tariffs:
    try:
        result = tariff.calculate_cost_with_breakdown(ANNUAL_CONSUMPTION)
        
        results.append({
            'name': name,
            'total_cost': result['total_cost'],
            'avg_kwh_price': result['avg_kwh_price'],
            'base_price': tariff.base_price,
            'additional_ct': tariff.additional_price_ct_kwh if hasattr(tariff, 'additional_price_ct_kwh') else 18.4
        })
        
    except Exception as e:
        print(f"❌ {name}: Fehler bei Berechnung - {e}")

# Sortiere nach Gesamtkosten
results.sort(key=lambda x: x['total_cost'])

# Ausgabe
print(f"{'Anbieter':<20} {'Grundpreis':>12} {'Zusatz-Komp.':>14} {'Ø kWh-Preis':>12} {'Gesamtkosten':>14}")
print("-" * 80)

for r in results:
    print(f"{r['name']:<20} {r['base_price']:>10.2f} € {r['additional_ct']:>10.2f} ct {r['avg_kwh_price']*100:>10.2f} ct {r['total_cost']:>12.2f} €")

if len(results) > 1:
    print()
    print("=" * 80)
    print("🏆 EMPFEHLUNG")
    print("=" * 80)
    print()
    
    winner = results[0]
    savings = results[-1]['total_cost'] - winner['total_cost']
    
    print(f"Günstigster Anbieter: {winner['name']}")
    print(f"Kosten (30 Tage): {winner['total_cost']:.2f} €")
    print(f"Durchschnittlicher kWh-Preis: {winner['avg_kwh_price']*100:.2f} ct/kWh")
    
    if savings > 1:
        print(f"\n💡 Ersparnis gegenüber teuerstem Anbieter: {savings:.2f} € (30 Tage)")
        print(f"   Hochgerechnet auf Jahr: {savings * 12:.2f} €")

print()
print("=" * 80)
print("📌 HINWEISE:")
print("=" * 80)
print()
print("• Alle Preise inkl. Netzentgelte, Steuern und Umlagen")
print("• Börsenstrompreise basieren auf Prophet-Forecast (2 Jahre Training)")
print("• Zusätzliche Komponenten (Netzentgelte etc.) von Anbietern gescrapt")
print("• Preise können sich stündlich ändern (dynamische Tarife)")
print("• Grundpreise sind monatlich fällig")
print()
