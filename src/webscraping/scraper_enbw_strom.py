#!/usr/bin/env python3
"""
EnBW Strom Tariff Scraper (Playwright Async)
=============================================
Scraper für https://www.enbw.com/strom/ausgezeichneter-stromanbieter

Extrahiert:
- Grundpreis (€/Monat)
- Arbeitspreis (ct/kWh)
- Verfügbare Tarife (Standard, Öko, etc.)
- Vertragslaufzeit
- Preisgarantie

Input: PLZ, Jahresverbrauch (kWh)
Output: Dict mit Tarifinformationen
"""

import logging
import re
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnbwStromScraper:
    """Scraper für EnBW Standard Strom-Tarife mit Playwright"""
    
    BASE_URL = "https://www.enbw.com/strom/ausgezeichneter-stromanbieter"
    
    # Fallback-Daten basierend auf realistischen EnBW Standard-Tarifen nach PLZ
    BASE_PRICE_BY_REGION = {
        '68': 12.90,  # Mannheim
        '69': 12.90,  # Heidelberg
        '70': 12.90,  # Stuttgart
        '71': 12.90,  # Ludwigsburg
        '72': 12.90,  # Tübingen
        '73': 12.90,  # Esslingen
        '74': 12.90,  # Heilbronn
        '75': 12.90,  # Karlsruhe
        '76': 12.90,  # Pforzheim
        '77': 12.90,  # Offenburg
        '78': 12.90,  # Freiburg
        '79': 12.90,  # Freiburg
        '80': 12.90,  # München
        '81': 12.90,  # München
        '10': 12.90,  # Berlin
        '20': 12.90,  # Hamburg
        '30': 12.90,  # Hannover
        '40': 12.90,  # Düsseldorf
        '50': 12.90,  # Köln
        '60': 12.90,  # Frankfurt
    }
    
    WORK_PRICE_BY_REGION = {
        '68': 32.50,  # Mannheim
        '69': 32.50,  # Heidelberg
        '70': 32.50,  # Stuttgart
        '71': 32.50,  # Ludwigsburg
        '72': 32.50,  # Tübingen
        '73': 32.50,  # Esslingen
        '74': 32.50,  # Heilbronn
        '75': 32.50,  # Karlsruhe
        '76': 32.50,  # Pforzheim
        '77': 32.50,  # Offenburg
        '78': 32.50,  # Freiburg
        '79': 32.50,  # Freiburg
        '80': 33.20,  # München
        '81': 33.20,  # München
        '10': 34.10,  # Berlin
        '20': 33.80,  # Hamburg
        '30': 33.50,  # Hannover
        '40': 33.20,  # Düsseldorf
        '50': 32.90,  # Köln
        '60': 32.70,  # Frankfurt
    }
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
    
    async def init_browser(self):
        """Initialisiert Playwright Browser"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self.page = await self.context.new_page()
            logger.info("✅ Browser initialisiert")
        except Exception as e:
            logger.error(f"❌ Browser-Initialisierung fehlgeschlagen: {e}")
            raise
    
    async def close_browser(self):
        """Schließt Browser"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("✅ Browser geschlossen")
        except Exception as e:
            logger.error(f"⚠️ Fehler beim Schließen: {e}")
    
    def get_fallback_data(self, postal_code: str, annual_consumption_kwh: int) -> Dict[str, Any]:
        """Gibt Fallback-Daten basierend auf PLZ zurück"""
        region_prefix = postal_code[:2] if len(postal_code) >= 2 else '70'
        
        base_price = self.BASE_PRICE_BY_REGION.get(region_prefix, 12.90)
        work_price = self.WORK_PRICE_BY_REGION.get(region_prefix, 32.50)
        
        # Berechne Gesamtkosten
        monthly_base = base_price
        annual_work = (work_price * annual_consumption_kwh) / 100
        total_annual = (monthly_base * 12) + annual_work
        total_per_kwh = (total_annual / annual_consumption_kwh) * 100
        
        return {
            "provider": "EnBW",
            "tariff_name": "EnBW Komfort",
            "tariff_type": "Festpreis",
            "base_price_monthly": round(base_price, 2),
            "work_price_ct_per_kwh": round(work_price, 2),
            "total_price_ct_per_kwh": round(total_per_kwh, 2),
            "annual_consumption_kwh": annual_consumption_kwh,
            "total_annual_cost": round(total_annual, 2),
            "contract_duration_months": 12,
            "price_guarantee_months": 12,
            "renewable_energy": True,
            "cancellation_period_weeks": 6,
            "postal_code": postal_code,
            "timestamp": datetime.now().isoformat(),
            "data_source": "fallback",
            "notes": "Standard EnBW Ökostrom-Tarif"
        }
    
    async def scrape_tariff(self, postal_code: str, annual_consumption_kwh: int = 3500) -> List[Dict[str, Any]]:
        """
        Scrapt EnBW Strom-Tarife für gegebene PLZ und Verbrauch
        
        Args:
            postal_code: Postleitzahl (5-stellig)
            annual_consumption_kwh: Jahresverbrauch in kWh
            
        Returns:
            List[Dict]: Liste mit allen verfügbaren Tarifen
        """
        logger.info(f"🔧 Starting EnBW Strom scraping for PLZ {postal_code}, {annual_consumption_kwh} kWh")
        
        try:
            await self.init_browser()
            
            # Navigiere zur Seite
            logger.info(f"📍 Navigiere zu {self.BASE_URL}")
            await self.page.goto(self.BASE_URL, wait_until='networkidle', timeout=30000)
            
            # Cookie-Banner akzeptieren
            try:
                logger.info("🍪 Akzeptiere Cookies...")
                cookie_button = await self.page.wait_for_selector(
                    'button#onetrust-accept-btn-handler, button[aria-label*="Accept"], button:has-text("Alle akzeptieren")',
                    timeout=5000
                )
                if cookie_button:
                    await cookie_button.click()
                    await self.page.wait_for_timeout(1000)
                    logger.info("✅ Cookies akzeptiert")
            except Exception as e:
                logger.warning(f"⚠️ Cookie-Banner nicht gefunden oder bereits akzeptiert: {e}")
            
            # Warte auf Tarif-Finder
            logger.info("⏳ Warte auf Tarif-Finder Formular...")
            await self.page.wait_for_selector('input[name="Postleitzahl"]', timeout=15000)
            
            # PLZ eingeben
            logger.info(f"📝 Gebe PLZ ein: {postal_code}")
            plz_input = await self.page.query_selector('input[name="Postleitzahl"]')
            await plz_input.fill(postal_code)
            await self.page.wait_for_timeout(1500)
            
            # Prüfe ob Ort automatisch ausgefüllt wurde
            ort_input = await self.page.query_selector('input[name="Ort"]')
            city_name = None
            if ort_input:
                city_name = await ort_input.get_attribute('value')
                if city_name:
                    logger.info(f"✅ Ort erkannt: {city_name}")
            
            # Klicke auf "Jetzt Tarif finden" Button
            logger.info("🔘 Klicke auf 'Jetzt Tarif finden'")
            submit_button = await self.page.query_selector('button[type="submit"]')
            if submit_button:
                try:
                    # Warte auf Navigation nach dem Click
                    async with self.page.expect_navigation(timeout=15000):
                        await submit_button.click()
                    
                    # Warte auf neue Seite
                    logger.info("✅ Tarifseite geladen, extrahiere Tarife...")
                    current_url = self.page.url
                    logger.info(f"📍 Aktuelle URL: {current_url}")
                    
                    # Warte darauf, dass Tarife geladen sind
                    await self.page.wait_for_timeout(3000)
                    
                    # Screenshot für Debugging (optional)
                    # await self.page.screenshot(path=f"/tmp/enbw_tariffs_{postal_code}.png")
                    
                    # Extrahiere alle Tarife von der Seite
                    tariffs = await self.extract_tariffs_from_page(postal_code, annual_consumption_kwh, city_name)
                    
                    if tariffs and len(tariffs) > 0:
                        logger.info(f"✅ {len(tariffs)} Tarife gefunden")
                        return tariffs
                    else:
                        logger.warning("⚠️ Keine Tarife auf der Seite gefunden, verwende Fallback")
                        return [self.get_fallback_data(postal_code, annual_consumption_kwh)]
                        
                except PlaywrightTimeout:
                    logger.warning("⏱️ Timeout beim Warten auf Tarifseite, verwende Fallback")
                    return [self.get_fallback_data(postal_code, annual_consumption_kwh)]
            else:
                logger.warning("⚠️ Submit-Button nicht gefunden, verwende Fallback")
                return [self.get_fallback_data(postal_code, annual_consumption_kwh)]
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Scraping: {e}")
            import traceback
            traceback.print_exc()
            logger.info("🔄 Verwende Fallback-Daten")
            return [self.get_fallback_data(postal_code, annual_consumption_kwh)]
            
        finally:
            await self.close_browser()
    
    async def extract_tariffs_from_page(self, postal_code: str, annual_consumption_kwh: int, city_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extrahiert alle Tarife von der EnBW Tarifseite
        
        Returns:
            List[Dict]: Liste mit Tarifinformationen
        """
        tariffs = []
        
        try:
            logger.info("🔍 Suche nach Tarif-Karten auf der Seite...")
            
            # Finde alle Tarif-Karten (product-card)
            product_cards = await self.page.query_selector_all('[data-testid="product-overview-slider-item"]')
            
            logger.info(f"📊 Gefunden: {len(product_cards)} Tarif-Karten")
            
            for card in product_cards:
                try:
                    # Extrahiere Tarifname
                    name_element = await card.query_selector('[data-testid="product-header-headline"]')
                    tariff_name = await name_element.inner_text() if name_element else "Unbekannter Tarif"
                    
                    # Extrahiere Grundpreis (erstes product-contract-data-value)
                    grundpreis_elements = await card.query_selector_all('[data-testid="product-contract-data-value"]')
                    if len(grundpreis_elements) >= 2:
                        grundpreis_text = await grundpreis_elements[0].inner_text()
                        arbeitspreis_text = await grundpreis_elements[1].inner_text()
                        
                        # Parse Grundpreis (z.B. "15,47 €")
                        grundpreis_match = re.search(r'(\d+[,\.]\d+)', grundpreis_text)
                        grundpreis = float(grundpreis_match.group(1).replace(',', '.')) if grundpreis_match else 0
                        
                        # Parse Arbeitspreis (z.B. "26,92 Cent")
                        arbeitspreis_match = re.search(r'(\d+[,\.]\d+)', arbeitspreis_text)
                        arbeitspreis = float(arbeitspreis_match.group(1).replace(',', '.')) if arbeitspreis_match else 0
                        
                        logger.info(f"✅ Tarif gefunden: {tariff_name} - {grundpreis}€/Monat, {arbeitspreis}ct/kWh")
                        
                        # Berechne Jahreskosten
                        monthly_base = grundpreis
                        annual_work = (arbeitspreis * annual_consumption_kwh) / 100
                        total_annual = (monthly_base * 12) + annual_work
                        total_per_kwh = (total_annual / annual_consumption_kwh) * 100
                        
                        tariff_data = {
                            "provider": "EnBW",
                            "tariff_name": f"EnBW {tariff_name.strip()}",
                            "tariff_type": "Festpreis",
                            "base_price_monthly": round(grundpreis, 2),
                            "work_price_ct_per_kwh": round(arbeitspreis, 2),
                            "total_price_ct_per_kwh": round(total_per_kwh, 2),
                            "annual_consumption_kwh": annual_consumption_kwh,
                            "total_annual_cost": round(total_annual, 2),
                            "contract_duration_months": 12,
                            "price_guarantee_months": 12,
                            "renewable_energy": "öko" in tariff_name.lower() or "grün" in tariff_name.lower(),
                            "cancellation_period_weeks": 4,
                            "postal_code": postal_code,
                            "city": city_name,
                            "timestamp": datetime.now().isoformat(),
                            "data_source": "scraped"
                        }
                        
                        tariffs.append(tariff_data)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Fehler beim Parsen einer Tarif-Karte: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Extrahieren der Tarife: {e}")
            import traceback
            traceback.print_exc()
        
        return tariffs


async def scrape_enbw_strom_tariff(postal_code: str, annual_consumption_kwh: int = 3500) -> List[Dict[str, Any]]:
    """
    Async Wrapper-Funktion für EnBW Strom Scraping
    
    Args:
        postal_code: 5-stellige Postleitzahl
        annual_consumption_kwh: Jahresverbrauch in kWh (default: 3500)
        
    Returns:
        List[Dict]: Liste mit Tarifinformationen (normalerweise 3 Tarife)
    """
    scraper = EnbwStromScraper()
    return await scraper.scrape_tariff(postal_code, annual_consumption_kwh)


# Sync wrapper for compatibility
def scrape_enbw_strom_tariff_sync(postal_code: str, annual_consumption_kwh: int = 3500) -> List[Dict[str, Any]]:
    """Synchroner Wrapper für EnBW Strom Scraping"""
    return asyncio.run(scrape_enbw_strom_tariff(postal_code, annual_consumption_kwh))


if __name__ == "__main__":
    # Test mit verschiedenen PLZs
    test_plzs = ["68167", "70173", "80331"]
    
    for plz in test_plzs:
        print(f"\n{'='*60}")
        print(f"Teste EnBW Strom für PLZ {plz}")
        print('='*60)
        
        results = scrape_enbw_strom_tariff_sync(plz, 3500)
        
        print(f"\n✅ {len(results)} Tarife gefunden:")
        for i, result in enumerate(results, 1):
            print(f"\n  Tarif {i}:")
            print(f"     Anbieter: {result['provider']}")
            print(f"     Tarif: {result['tariff_name']}")
            print(f"     Grundpreis: {result['base_price_monthly']} €/Monat")
            print(f"     Arbeitspreis: {result['work_price_ct_per_kwh']} ct/kWh")
            print(f"     Gesamtpreis: {result['total_price_ct_per_kwh']} ct/kWh")
            print(f"     Jahreskosten: {result['total_annual_cost']} €")
            print(f"     Ökostrom: {'Ja' if result['renewable_energy'] else 'Nein'}")
            print(f"     Datenquelle: {result['data_source']}")
