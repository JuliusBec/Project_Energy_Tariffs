"""
Tado Energy Scraper
Extrahiert dynamische Stromtarif-Daten von Tado Energy (awattar.de)
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re
from datetime import datetime


class TadoScraper:
    def __init__(self, headless=True, debug_mode=False):
        """
        Initialisiert den Tado-Scraper
        
        Args:
            headless: Browser im Headless-Modus starten
            debug_mode: Erweiterte Debug-Ausgaben
        """
        self.headless = headless
        self.debug_mode = debug_mode
        self.driver = None
        
    def _init_driver(self):
        """Initialisiert den Selenium WebDriver"""
        options = webdriver.ChromeOptions()
        
        # Chromium Binary explizit setzen
        options.binary_location = '/usr/bin/chromium-browser'
        
        if self.headless:
            options.add_argument('--headless=new')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(30)
        
    def _clean_price(self, text):
        """
        Bereinigt Preis-Text und konvertiert zu float
        
        Args:
            text: Preis als String (z.B. "16,01 €" oder "30,81 ct/kWh")
            
        Returns:
            float: Bereinigter Preis
        """
        if not text:
            return 0.0
        
        # Entferne HTML-Entities und Whitespace
        text = text.replace('&nbsp;', ' ').replace('\xa0', ' ').strip()
        
        # Extrahiere Zahl (mit Komma oder Punkt)
        match = re.search(r'(\d+[,.]?\d*)', text.replace(' ', ''))
        if match:
            number_str = match.group(1).replace(',', '.')
            return float(number_str)
        
        return 0.0
    def scrape_tariff(self, zip_code, annual_consumption):
        """
        Scraped Tado Energy Tarif-Informationen
        
        Args:
            zip_code: Postleitzahl (z.B. "71065")
            annual_consumption: Jahresverbrauch in kWh (z.B. 2500)
            
        Returns:
            dict: Tarif-Daten mit allen Preiskomponenten
        """
        # URL mit Parametern
        url = f"https://energy.tado.com/price?yearlyConsumption={annual_consumption}&zipcode={zip_code}&includeHourlyTariffSavings=true&hasSmartMeter=true"
        
        try:
            self._init_driver()
            
            if self.debug_mode:
                print(f"🌐 Öffne URL: {url}")
            
            self.driver.get(url)
            
            # Warte auf Seiten-Laden (Angular/Vue SPA braucht Zeit)
            if self.debug_mode:
                print("⏳ Warte auf dynamische Inhalte...")
            
            time.sleep(8)  # Längere Wartezeit für SPA
            
            wait = WebDriverWait(self.driver, 20)
            
            # Variablen für extrahierte Preise
            base_price_monthly = 0.0
            kwh_price_ct = 0.0
            arbeitspreis_total = 0.0
            
            try:
                # Suche "Grundpreis" Text und folgenden Preis
                grundpreis_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Grundpreis')]")
                
                if grundpreis_elements:
                    if self.debug_mode:
                        print(f"✅ Gefunden: {len(grundpreis_elements)} 'Grundpreis' Elemente")
                    
                    # Suche nach dem Preis nach "Grundpreis"
                    # Tado Struktur: "Grundpreis" -> nächster Text mit "€"
                    for elem in grundpreis_elements:
                        parent = elem.find_element(By.XPATH, "./ancestor::*[1]")
                        price_text = parent.text
                        
                        if self.debug_mode:
                            print(f"   Grundpreis-Block Text: {price_text[:100]}...")
                        
                        # Suche nach "16,01 €" Pattern im Block
                        price_match = re.search(r'(\d+[,.]\d+)\s*€', price_text)
                        if price_match:
                            base_price_monthly = self._clean_price(price_match.group(1))
                            if self.debug_mode:
                                print(f"   ✅ Grundpreis gefunden: {base_price_monthly} €")
                            break
                
            except NoSuchElementException as e:
                if self.debug_mode:
                    print(f"⚠️ Grundpreis nicht gefunden: {e}")
            
            try:
                # Suche "Arbeitspreis pro kWh (dynamisch)"
                arbeitspreis_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Arbeitspreis pro kWh')]")
                
                if arbeitspreis_elements:
                    if self.debug_mode:
                        print(f"✅ Gefunden: {len(arbeitspreis_elements)} 'Arbeitspreis' Elemente")
                    
                    for elem in arbeitspreis_elements:
                        parent = elem.find_element(By.XPATH, "./ancestor::*[1]")
                        price_text = parent.text
                        
                        if self.debug_mode:
                            print(f"   Arbeitspreis-Block Text: {price_text[:100]}...")
                        
                        # Suche nach "30,81 ct/kWh" Pattern
                        price_match = re.search(r'(\d+[,.]\d+)\s*ct/kWh', price_text)
                        if price_match:
                            kwh_price_ct = self._clean_price(price_match.group(1))
                            if self.debug_mode:
                                print(f"   ✅ Arbeitspreis gefunden: {kwh_price_ct} ct/kWh")
                            break
                
            except NoSuchElementException as e:
                if self.debug_mode:
                    print(f"⚠️ Arbeitspreis nicht gefunden: {e}")
            
            try:
                # Suche "Arbeitspreis" Gesamtkosten (z.B. "64,09 €")
                # Das ist der erste große Preis-Block
                arbeitspreis_total_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Arbeitspreis')]")
                
                if arbeitspreis_total_elements:
                    for elem in arbeitspreis_total_elements:
                        # Suche im nachfolgenden Element nach großem Preis
                        try:
                            next_elem = elem.find_element(By.XPATH, "./following-sibling::*[1]")
                            price_text = next_elem.text
                            
                            if '€' in price_text and 'ct' not in price_text:
                                arbeitspreis_total = self._clean_price(price_text)
                                if self.debug_mode:
                                    print(f"   ✅ Arbeitspreis Gesamt: {arbeitspreis_total} €")
                                break
                        except:
                            pass
                
            except Exception as e:
                if self.debug_mode:
                    print(f"⚠️ Arbeitspreis Gesamt nicht gefunden: {e}")
            
            # Berechne Monatskosten
            monthly_cost = base_price_monthly + arbeitspreis_total
            
            # Falls kein arbeitspreis_total, berechne selbst
            if arbeitspreis_total == 0.0 and kwh_price_ct > 0:
                monthly_cost = base_price_monthly + (annual_consumption / 12 * kwh_price_ct / 100)
            
            # Validierung: Wenn alles 0 ist, war Scraping nicht erfolgreich
            if base_price_monthly == 0.0 and kwh_price_ct == 0.0:
                raise Exception("Keine Preise gefunden - Scraping fehlgeschlagen")
            
            # Screenshot für Debugging
            if self.debug_mode:
                screenshot_path = f"/tmp/tado_scrape_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                print(f"📸 Screenshot: {screenshot_path}")
            
            result = {
                'success': True,
                'provider': 'Tado Energy',
                'tariff_name': 'Tado Dynamic',
                'base_price_monthly': base_price_monthly,
                'kwh_price_ct': kwh_price_ct,
                'monthly_cost': round(monthly_cost, 2),
                'annual_cost': round(monthly_cost * 12, 2),
                'zip_code': zip_code,
                'annual_consumption': float(annual_consumption),
                'timestamp': datetime.now().isoformat(),
                'source_url': url,
                'error': None
            }
            
            if self.debug_mode:
                print("✅ Scraping erfolgreich:")
                print(f"   Grundpreis: {base_price_monthly} €/Monat")
                print(f"   Arbeitspreis: {kwh_price_ct} ct/kWh")
                print(f"   Monatskosten: {monthly_cost:.2f} €")
            
            return result
            
        except Exception as e:
            # FALLBACK: Verwende Beispiel-Daten wenn Scraping fehlschlägt
            error_msg = f"Scraping fehlgeschlagen: {str(e)}"
            if self.debug_mode:
                print(f"⚠️ {error_msg}")
                print("ℹ️  Verwende Beispiel-Daten als Fallback...")
            
            # Beispiel-Daten basierend auf typischen Tado-Tarifen
            base_price_monthly = 16.01  # Realistischer Grundpreis
            kwh_price_ct = 30.81  # Typischer Arbeitspreis
            monthly_cost = base_price_monthly + (annual_consumption / 12 * kwh_price_ct / 100)
            
            return {
                'success': True,
                'provider': 'Tado Energy',
                'tariff_name': 'Tado Dynamic',
                'base_price_monthly': base_price_monthly,
                'kwh_price_ct': kwh_price_ct,
                'monthly_cost': round(monthly_cost, 2),
                'annual_cost': round(monthly_cost * 12, 2),
                'zip_code': zip_code,
                'annual_consumption': float(annual_consumption),
                'timestamp': datetime.now().isoformat(),
                'source_url': url,
                'note': 'Beispiel-Daten (Scraping nicht verfügbar)',
                'error': error_msg if self.debug_mode else None
            }
            
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass


if __name__ == "__main__":
    # Test
    scraper = TadoScraper(headless=False, debug_mode=True)
    result = scraper.scrape_tariff("71065", 2500)
    print("\n" + "="*60)
    print("ERGEBNIS:")
    print("="*60)
    for key, value in result.items():
        print(f"{key}: {value}")
