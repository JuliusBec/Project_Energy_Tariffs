"""
Tibber Energy Tariff Scraper
============================

Scrapes Tibber electricity prices from https://tibber.com/de/preisrechner

IMPORTANT: Tibber loads prices dynamically via JavaScript. We use two approaches:
1. requests + JSON parsing from __NEXT_DATA__ (fast, no browser needed)
2. Fallback with PLZ-based estimations

Author: AI Assistant
Date: November 2025
"""

import re
import time
import logging
from typing import Dict, Any, Optional
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TibberScraper:
    """
    Scraper für Tibber Stromtarife
    
    Uses requests library to fetch and parse Tibber pricing data.
    Falls back to regional price estimations if scraping fails.
    """
    
    BASE_URL = "https://tibber.com/de/preisrechner"
    
    # PLZ-abhängige Grundpreise (€/Monat) - ohne Tibber-Gebühr
    # Diese Werte sind die reinen Netznutzungsgebühren
    BASE_PRICE_BY_REGION = {
        '71': 9.90,   # Stuttgart
        '70': 9.90,   # Stuttgart-Region
        '68': 10.10,  # Mannheim (Grundpreis 16,09 - Tibber-Gebühr 5,99 = 10,10)
        '67': 10.10,  # Ludwigshafen/Speyer
        '66': 10.05,  # Saarbrücken
        '10': 8.50,   # Berlin
        '80': 10.20,  # München
        '60': 9.30,   # Frankfurt
        '40': 8.90,   # Essen/Duisburg
        '50': 9.10,   # Köln
        '20': 9.50,   # Hamburg
        '30': 9.15,   # Hannover
        '01': 9.85,   # Dresden
        '04': 9.75,   # Leipzig
        '99': 10.30,  # Thüringen
        '06': 9.95,   # Sachsen-Anhalt
        '39': 10.00,  # Magdeburg
        '18': 9.80,   # Rostock
        '24': 9.70,   # Kiel
        'default': 9.85
    }
    
    # PLZ-abhängiger Arbeitspreis: Weitere Preisbestandteile (ct/kWh)
    # (Herkunftsnachweise, Umlagen, Abgaben, Steuern)
    ADDITIONAL_PRICE_BY_REGION = {
        '71': 18.40,  # Stuttgart
        '70': 18.40,
        '68': 15.25,  # Mannheim (laut aktuellem Scraping)
        '67': 16.00,  # Ludwigshafen
        '66': 17.00,
        '10': 17.50,  # Berlin
        '80': 19.10,  # München
        '60': 17.00,  # Frankfurt
        '40': 16.50,  # Essen
        '50': 17.20,  # Köln
        'default': 18.40
    }
    
    def __init__(self, debug_mode: bool = False):
        """
        Initialisiert den Scraper
        
        Args:
            debug_mode: Aktiviert ausführliches Logging
        """
        self.debug_mode = debug_mode
        if debug_mode:
            logger.setLevel(logging.DEBUG)
    
    def _get_base_price(self, zip_code: str) -> float:
        """Gibt PLZ-abhängigen Grundpreis (ohne Tibber-Gebühr) zurück"""
        prefix = zip_code[:2] if len(zip_code) >= 2 else 'default'
        return self.BASE_PRICE_BY_REGION.get(prefix, self.BASE_PRICE_BY_REGION['default'])
    
    def _get_additional_price(self, zip_code: str) -> float:
        """Gibt PLZ-abhängigen Arbeitspreis (Herkunftsnachweise, Umlagen, etc.) zurück"""
        prefix = zip_code[:2] if len(zip_code) >= 2 else 'default'
        return self.ADDITIONAL_PRICE_BY_REGION.get(prefix, self.ADDITIONAL_PRICE_BY_REGION['default'])
    
    def _scrape_with_selenium(self, zip_code: str, annual_consumption: int) -> Optional[Dict[str, Any]]:
        """
        Scrapt Tibber-Preise mit Selenium (rendert JavaScript)
        
        Gibt None zurück, wenn Scraping fehlschlägt → Fallback wird verwendet.
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.common.exceptions import TimeoutException
            from webdriver_manager.chrome import ChromeDriverManager
            
            url = f"{self.BASE_URL}?postalCode={zip_code}&averageConsumption={annual_consumption}"
            logger.info(f"🌐 Starte Selenium-Scraping für: {url}")
            
            # Chrome Optionen
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            chrome_options.binary_location = '/usr/bin/chromium-browser'
            
            # Service mit WebDriver Manager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            try:
                driver.get(url)
                logger.info("� Seite geladen, warte auf Preisanzeige...")
                
                # Warte auf Preis-Elemente (max 15 Sekunden)
                wait = WebDriverWait(driver, 15)
                
                # Suche nach verschiedenen möglichen Selektoren
                possible_selectors = [
                    (By.XPATH, "//*[contains(text(), '€') and contains(text(), 'Monat')]"),
                    (By.XPATH, "//*[contains(text(), 'ct/kWh') or contains(text(), 'Cent/kWh')]"),
                    (By.CSS_SELECTOR, "[data-testid*='price']"),
                    (By.CSS_SELECTOR, "[class*='price']"),
                ]
                
                found_prices = False
                for selector_type, selector in possible_selectors:
                    try:
                        element = wait.until(EC.presence_of_element_located((selector_type, selector)))
                        logger.info(f"✅ Preis-Element gefunden: {element.text[:100]}")
                        found_prices = True
                        break
                    except TimeoutException:
                        continue
                
                if not found_prices:
                    logger.warning("⚠️ Keine Preis-Elemente gefunden")
                # Parse die Preise aus dem HTML
                page_source = driver.page_source
                
                # Suche nach Grundpreis-Mustern
                base_price_patterns = [
                    r'Grundpreis[:\s]*([0-9,]+)\s*€',
                    r'([0-9,]+)\s*€\s*/\s*Monat',
                    r'monatlich[:\s]*([0-9,]+)\s*€',
                ]
                
                base_price = None
                for pattern in base_price_patterns:
                    match = re.search(pattern, page_source, re.IGNORECASE)
                    if match:
                        base_price = float(match.group(1).replace(',', '.'))
                        logger.info(f"📊 Grundpreis gefunden: {base_price} €/Monat")
                        break
                
                # Suche nach Arbeitspreis-Mustern
                work_price_patterns = [
                    r'([0-9,]+)\s*ct/kWh',
                    r'([0-9,]+)\s*Cent/kWh',
                    r'Arbeitspreis[:\s]*([0-9,]+)',
                ]
                
                work_price = None
                for pattern in work_price_patterns:
                    match = re.search(pattern, page_source, re.IGNORECASE)
                    if match:
                        work_price = float(match.group(1).replace(',', '.'))
                        logger.info(f"📊 Arbeitspreis gefunden: {work_price} ct/kWh")
                        break
                
                if base_price and work_price:
                    logger.info(f"✅ Scraping erfolgreich: {base_price}€/Mon + {work_price}ct/kWh")
                    return {
                        'success': True,
                        'data_source': 'selenium_scraping',
                        'total_base_monthly': round(base_price, 2),
                        'additional_price_ct': work_price,
                        'markup_ct_kwh': work_price,
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                else:
                    logger.warning(f"⚠️ Nicht alle Preise gefunden (Grund: {base_price}, Arbeit: {work_price})")
                    return None
                    
            finally:
                driver.quit()
                
        except Exception as e:
            logger.error(f"❌ Selenium-Scraping fehlgeschlagen: {e}")
            return None
    
    def _scrape_with_nextdata(self, zip_code: str, annual_consumption: int) -> Optional[Dict[str, Any]]:
        """
        Versucht, die Next.js prerender JSON (/_next/data/...) auszulesen und daraus Preise zu parsen.
        Liefert None, wenn kein geeigneter Wert extrahiert werden kann.
        """
        try:
            import requests
            # Lade die Seite und extrahiere buildId aus __NEXT_DATA__
            url = f"{self.BASE_URL}?postalCode={zip_code}&averageConsumption={annual_consumption}"
            headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
            r = requests.get(url, headers=headers, timeout=20)
            r.raise_for_status()

            m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text, re.DOTALL)
            if not m:
                logger.debug("_scrape_with_nextdata: __NEXT_DATA__ nicht gefunden")
                return None
            nd = json.loads(m.group(1))
            buildId = nd.get('buildId')
            if not buildId:
                logger.debug("_scrape_with_nextdata: buildId nicht gefunden")
                return None

            next_url = f'https://tibber.com/_next/data/{buildId}/de/preisrechner.json?postalCode={zip_code}&averageConsumption={annual_consumption}'
            logger.info(f"🔗 Lade Next-data: {next_url}")
            r2 = requests.get(next_url, headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'}, timeout=20)
            r2.raise_for_status()
            data = r2.json()

            page_data = data.get('pageProps', {}).get('data')
            if not page_data:
                logger.debug("_scrape_with_nextdata: pageProps.data fehlt")
                return None

            # page_data ist oft ein großer String; suche nach Base/Price-Feldern
            text = page_data if isinstance(page_data, str) else json.dumps(page_data)

            # 1) Suche JSON-like fields
            patterns = [
                r'"basePrice"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
                r'"basePriceMonthly"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
                r'"energyPricePerKwh"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
                r'"taxPricePerKwh"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
                r'"totalPricePerKwh"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
            ]

            base_price = None
            kwh_price = None
            for pat in patterns:
                for m in re.finditer(pat, text):
                    val = float(m.group(1))
                    # heuristik: base price in EUR (>=1 and <=200)
                    if 'basePrice' in pat and 1 <= val <= 200:
                        base_price = round(val, 2)
                    else:
                        # kWh-Werte oft in EUR or ct; store as candidate
                        if 0 < val < 100:
                            kwh_price = val

            # 2) Falls nicht gefunden, suche nach deutsch ausgeschriebenen Strings
            if base_price is None:
                m2 = re.search(r'Grundpreis[^0-9\n\r]{0,20}([0-9]{1,3},[0-9]{1,2})\s*€', text, re.IGNORECASE)
                if m2:
                    base_price = float(m2.group(1).replace(',', '.'))

            if kwh_price is None:
                m3 = re.search(r'([0-9]{1,2},[0-9]{1,2})\s*ct/kWh', text, re.IGNORECASE)
                if m3:
                    kwh_price = float(m3.group(1).replace(',', '.'))

            # Wenn wir einen kWh-Preis in ct gefunden haben, benutze ihn
            if kwh_price is not None and kwh_price > 1:  # ct
                additional_price_ct = float(kwh_price)
            elif kwh_price is not None and kwh_price <= 1:
                # falls in EUR/kWh, konvertiere in ct
                additional_price_ct = round(kwh_price * 100, 2)
            else:
                additional_price_ct = None

            if base_price is not None or additional_price_ct is not None:
                result = {
                    'success': True,
                    'data_source': 'next_data_parsing',
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                }
                if base_price is not None:
                    result['base_price_monthly'] = round(base_price, 2)
                if additional_price_ct is not None:
                    result['additional_price_ct'] = additional_price_ct
                    result['markup_ct_kwh'] = additional_price_ct
                logger.info(f"_scrape_with_nextdata -> {result}")
                return result

            logger.debug("_scrape_with_nextdata: Keine passenden Preisfelder extrahiert")
            return None

        except Exception as e:
            logger.error(f"_scrape_with_nextdata Fehler: {e}")
            return None
    
    def _get_fallback_data(self, zip_code: str, annual_consumption: int) -> Dict[str, Any]:
        """
        Generiert PLZ-basierte Schätzungen
        
        Verwendet realistische Werte basierend auf Tibber-Website-Daten
        und regionalen Unterschieden.
        """
        logger.info(f"📊 Generiere PLZ-basierte Schätzungen für {zip_code}")
        
        monthly_consumption = annual_consumption / 12
        
        # PLZ-abhängige Werte
        base_price = self._get_base_price(zip_code)
        additional_price_ct = self._get_additional_price(zip_code)
        
        # Tibber-Gebühr (fest)
        tibber_fee = 5.99
        
        # Gesamter Grundpreis
        total_base_monthly = base_price + tibber_fee
        
        logger.info(f"   PLZ-Präfix: {zip_code[:2]}")
        logger.info(f"   Grundpreis (Netz): {base_price} €/Mon")
        logger.info(f"   Tibber-Gebühr: {tibber_fee} €/Mon")
        logger.info(f"   Grundpreis gesamt: {total_base_monthly} €/Mon")
        logger.info(f"   Arbeitspreis: {additional_price_ct} ct/kWh")
        
        return {
            'success': True,
            'data_source': 'plz_estimation',
            'base_price_monthly': round(base_price, 2),
            'tibber_fee_monthly': tibber_fee,
            'total_base_monthly': round(total_base_monthly, 2),
            'additional_price_ct': additional_price_ct,
            'markup_ct_kwh': additional_price_ct,  # Alias für Backend-Kompatibilität
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'note': f'PLZ-basierte Schätzung - Grundpreis {round(total_base_monthly, 2)} €/Mon, Arbeitspreis {additional_price_ct} ct/kWh'
        }
    
    def scrape_tariff(
        self,
        zip_code: str,
        annual_consumption: int
    ) -> Dict[str, Any]:
        """
        Hauptfunktion zum Scrapen der Tibber-Tarife
        
        Args:
            zip_code: Deutsche Postleitzahl
            annual_consumption: Jahresverbrauch in kWh
            
        Returns:
            Dict mit Preisinformationen
        """
        try:
            logger.info(f"🔍 Starte Tibber-Scraping für PLZ {zip_code}, {annual_consumption} kWh/Jahr")
            
            # Versuch 1: Scraping über Next.js prerender JSON (schnell, kein Browser)
            scraped_data = self._scrape_with_nextdata(zip_code, annual_consumption)
            if scraped_data:
                logger.info("✅ Scraping via Next-data erfolgreich")
                return scraped_data

            # Versuch 2: Scraping mit Selenium (rendert JavaScript)
            scraped_data = self._scrape_with_selenium(zip_code, annual_consumption)
            if scraped_data:
                logger.info("✅ Scraping mit Selenium erfolgreich")
                return scraped_data

            # Versuch 3: PLZ-basierte Schätzungen (Fallback)
            logger.warning("⚠️ Real-Scraping nicht möglich, verwende PLZ-Schätzungen")
            return self._get_fallback_data(zip_code, annual_consumption)
            
        except Exception as e:
            logger.error(f"❌ Unerwarteter Fehler: {e}")
            # Last resort: Fallback
            return self._get_fallback_data(zip_code, annual_consumption)


def main():
    """Testfunktion"""
    scraper = TibberScraper(debug_mode=True)
    
    print("\n" + "="*60)
    print("TEST 1: PLZ 71065 (Stuttgart), 2500 kWh/Jahr")
    print("="*60)
    
    result1 = scraper.scrape_tariff(
        zip_code="71065",
        annual_consumption=2500
    )
    
    print("\nErgebnis:")
    for key, value in result1.items():
        print(f"  {key:30s}: {value}")
    
    print("\n" + "="*60)
    print("TEST 2: PLZ 67165 (Ludwigshafen), 3500 kWh/Jahr")
    print("="*60)
    
    result2 = scraper.scrape_tariff(
        zip_code="67165",
        annual_consumption=3500
    )
    
    print("\nErgebnis:")
    for key, value in result2.items():
        print(f"  {key:30s}: {value}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
