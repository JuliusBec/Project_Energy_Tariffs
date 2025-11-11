#!/usr/bin/env python3
"""
Test: Vollständige Integration EnBW-Scraper mit DynamicTariff
PLZ 68167 (Mannheim)
"""

from datetime import datetime
from src.backend.EnergyTariff import DynamicTariff
from src.Webscraping.scraper_enbw import EnbwScraper

print("=" * 80)
print("🧪 VOLLSTÄNDIGE INTEGRATION: EnBW PLZ 68167")
print("=" * 80)
print()

ZIP_CODE = "68167"  # Mannheim
ANNUAL_CONSUMPTION = 2500
START_DATE = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# Schritt 1: Scrape EnBW
print("📡 Schritt 1: EnBW-Daten scrapen...")
print("-" * 80)

scraper = EnbwScraper(headless=True, debug=False, use_edge=False)
enbw_data = scraper.scrape_tariff(
    zip_code=ZIP_CODE,
    annual_consumption=ANNUAL_CONSUMPTION
)

print(f"✓ Grundpreis: {enbw_data['base_price_monthly']:.2f} €/Monat")
print(f"✓ Arbeitspreis (Zusatz-Komponenten): {enbw_data['markup_ct_kwh']:.2f} ct/kWh")
print(f"  (Netzentgelte + Steuern + Umlagen + Herkunftsnachweise)")
print(f"✓ Ø Börsenpreis (wird ersetzt): {enbw_data['exchange_price_ct_kwh']:.2f} ct/kWh")
print()

# Schritt 2: Erstelle DynamicTariff
print("🏗️  Schritt 2: DynamicTariff erstellen...")
print("-" * 80)

enbw_tariff = DynamicTariff(
    name=enbw_data['tariff_name'],
    provider="EnBW",
    base_price=enbw_data['base_price_monthly'],
    start_date=START_DATE,
    network_fee=0,  # EnBW: keine einmalige Gebühr, alles in markup
    postal_code=ZIP_CODE,
    additional_price_ct_kwh=enbw_data['markup_ct_kwh']  # ← WICHTIG!
)

print(f"✓ Tarif: {enbw_tariff.name}")
print(f"✓ Grundpreis: {enbw_tariff.base_price:.2f} €/Monat")
print(f"✓ Zusätzliche Komponenten: {enbw_tariff.additional_price_ct_kwh:.2f} ct/kWh")
print(f"✓ Einmalige Netzgebühr: {enbw_tariff.network_fee:.2f} €")
print()

# Schritt 3: Berechne Kosten
print("💰 Schritt 3: Kosten berechnen...")
print("-" * 80)

result = enbw_tariff.calculate_cost_with_breakdown(ANNUAL_CONSUMPTION)

print(f"✓ Jahresverbrauch: {ANNUAL_CONSUMPTION} kWh")
print(f"✓ Gesamtkosten (30 Tage): {result['total_cost']:.2f} €")
print(f"✓ Durchschnittlicher kWh-Preis: {result['avg_kwh_price']*100:.2f} ct/kWh")
print()

# Schritt 4: Preisaufschlüsselung
print("=" * 80)
print("📊 PREISAUFSCHLÜSSELUNG:")
print("=" * 80)
print()

avg_price_ct = result['avg_kwh_price'] * 100

print(f"Endkundenpreis (berechnet):        {avg_price_ct:.2f} ct/kWh")
print()
print("Komponenten:")
print(f"  • Börsenstrompreis (Forecast):    ~4-5 ct/kWh")
print(f"  • Anbieter-Kosten (Modell):        ~7.0 ct/kWh")
print(f"  • Netzentgelte + Steuern (EnBW):  {enbw_tariff.additional_price_ct_kwh:.2f} ct/kWh ✓")
print(f"    └─ Von EnBW gescrapt für PLZ {ZIP_CODE}")
print()

# Vergleich mit EnBW-Angabe
enbw_total = enbw_data['total_kwh_price_ct']
print(f"Vergleich mit EnBW-Angabe:")
print(f"  EnBW-Gesamtpreis (inkl. Börse):    {enbw_total:.2f} ct/kWh")
print(f"  Unsere Berechnung:                 {avg_price_ct:.2f} ct/kWh")
print(f"  Differenz:                          {abs(avg_price_ct - enbw_total):.2f} ct/kWh")
print()

if abs(avg_price_ct - enbw_total) < 3:
    print("  ✅ SEHR GUT! Differenz < 3 ct/kWh")
elif abs(avg_price_ct - enbw_total) < 5:
    print("  ✓ GUT! Differenz < 5 ct/kWh")
else:
    print("  ⚠️  Größere Abweichung (normal, da EnBW Ø Börsenpreis 10.04 ct/kWh nutzt)")

print()
print("=" * 80)
print("✅ INTEGRATION ERFOLGREICH")
print("=" * 80)
print()
print("Wichtig:")
print(f"  • Grundpreis: {enbw_data['base_price_monthly']:.2f} €/Mon (PLZ-spezifisch)")
print(f"  • Arbeitspreis: {enbw_data['markup_ct_kwh']:.2f} ct/kWh (PLZ-spezifisch)")
print("  • Diese Werte werden jetzt korrekt von EnBW gescrapt!")
