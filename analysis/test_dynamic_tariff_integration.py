#!/usr/bin/env python3
"""
Test der DynamicTariff-Integration mit Scraper-Daten
Zeigt, wie die additional_price_ct_kwh von Tibber verwendet wird
"""

from datetime import datetime
from src.backend.energy_tariff import DynamicTariff
from src.webscraping.scraper_tibber import TibberScraper

print("=" * 80)
print("🧪 TEST: DYNAMIC TARIFF MIT SCRAPER-INTEGRATION")
print("=" * 80)
print()

# 1. Scrape Tibber-Daten
print("📡 Schritt 1: Tibber-Daten scrapen...")
print("-" * 80)

scraper = TibberScraper(debug_mode=False)
scraper_result = scraper.scrape_tariff(
 zip_code="71065", # Stuttgart
 annual_consumption=2500
)

print(f"[OK] Datenquelle: {scraper_result['data_source']}")
print(f"[OK] Börsenstrompreis: {scraper_result['exchange_price_ct']:.2f} ct/kWh")
print(f"[OK] Zusätzliche Komponenten: {scraper_result['additional_price_ct']:.2f} ct/kWh")
print(f" (Netzentgelte, Steuern, Umlagen, Herkunftsnachweise)")
print(f"[OK] Grundpreis: {scraper_result['total_base_monthly']:.2f} €/Monat")
print()

# 2. Erstelle DynamicTariff mit additional_price_ct_kwh
print("🏗️ Schritt 2: DynamicTariff-Objekt erstellen...")
print("-" * 80)

start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

tibber_tariff = DynamicTariff(
 name="Tibber Dynamic",
 provider="Tibber",
 base_price=scraper_result['total_base_monthly'], # 15.89 €/Monat
 start_date=start_date,
 network_fee=0, # Bei Tibber in base_price enthalten
 features=["dynamic", "green", "smart-meter"],
 postal_code="71065",
 additional_price_ct_kwh=scraper_result['additional_price_ct'] # 18.4 ct/kWh ← WICHTIG!
)

print(f"[OK] Tarif erstellt: {tibber_tariff.name}")
print(f"[OK] Anbieter: {tibber_tariff.provider}")
print(f"[OK] Grundpreis: {tibber_tariff.base_price:.2f} €/Monat")
print(f"[OK] Zusätzliche Preiskomponenten: {tibber_tariff.additional_price_ct_kwh:.2f} ct/kWh")
print()

# 3. Berechne Kosten (mit Jahresverbrauch)
print(" Schritt 3: Kosten berechnen...")
print("-" * 80)

try:
 yearly_usage = 2500 # kWh
 result = tibber_tariff.calculate_cost_with_breakdown(yearly_usage)

 print(f"[OK] Jahresverbrauch: {yearly_usage} kWh")
 print(f"[OK] Gesamtkosten (30 Tage): {result['total_cost']:.2f} €")
 print(f"[OK] Durchschnittlicher kWh-Preis: {result['avg_kwh_price']:.4f} €/kWh")
 print(f" = {result['avg_kwh_price']*100:.2f} ct/kWh")
 print()

 # 4. Preisaufschlüsselung
 print("=" * 80)
 print(" PREISAUFSCHLÜSSELUNG:")
 print("=" * 80)
 print()

 avg_price_ct = result['avg_kwh_price'] * 100

 # Schätzung der Komponenten
 print(f"Endkundenpreis: {avg_price_ct:6.2f} ct/kWh")
 print()
 print("Aufschlüsselung:")
 print(f" • Börsenstrompreis (Forecast): ~4-5 ct/kWh")
 print(f" • Anbieter-Kosten (Modell): ~7.0 ct/kWh")
 print(f" • Netzentgelte + Steuern (Tibber): {tibber_tariff.additional_price_ct_kwh:6.2f} ct/kWh")
 print(f" └─ Von Tibber gescrapt [OK]")
 print()

 # Vergleich mit Tibber-Referenz
 tibber_reference = 29.32
 difference = abs(avg_price_ct - tibber_reference)

 print(f"Vergleich mit Tibber-Durchschnitt (12 Monate):")
 print(f" Unsere Berechnung: {avg_price_ct:5.2f} ct/kWh")
 print(f" Tibber-Referenz: {tibber_reference:5.2f} ct/kWh")
 print(f" Differenz: {difference:5.2f} ct/kWh")
 print()

 if difference < 2:
 print(" [OK] SEHR GUT! Differenz < 2 ct/kWh")
 elif difference < 5:
 print(" [OK] GUT! Differenz < 5 ct/kWh")
 else:
 print(" [WARNING] Größere Abweichung")

except Exception as e:
 print(f"[ERROR] Fehler bei der Berechnung: {e}")
 import traceback
 traceback.print_exc()

print()
print("=" * 80)
print("[OK] TEST ABGESCHLOSSEN")
print("=" * 80)
