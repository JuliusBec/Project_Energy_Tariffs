#!/usr/bin/env python3
"""
EnBW Dynamischer Stromtarif Scraper
====================================
Scraper für https://www.enbw.com/strom/dynamischer-stromtarif

Extrahiert:
- Grundpreis (€/Monat)
- Arbeitspreis / Markup (ct/kWh)
- Durchschnittlicher Gesamtpreis (ct/kWh)
- Tarifname

Input: PLZ, Jahresverbrauch (kWh)
Output: Dict mit Tarifinformationen
"""

import time
import re
import platform
from datetime import datetime
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException
)


class EnbwScraper:
    """Scraper für EnBW dynamischen Stromtarif"""
    
    BASE_URL = "https://www.enbw.com/strom/dynamischer-stromtarif"
    
    def __init__(self, headless: bool = True, debug: bool = False, use_edge: bool = True):
        """
        Initialize EnBW scraper
        
        Args:
            headless: Run browser in headless mode
            debug: Enable debug output and save screenshots
            use_edge: Use Edge browser (default True for Windows compatibility)
        """
        self.headless = headless
        self.debug = debug
        self.use_edge = use_edge
        self.driver = None
        
    def _setup_driver(self):
        """Setup WebDriver - Edge (bevorzugt) oder Chrome"""
        
        # Versuche Edge zu verwenden (auf Windows immer verfügbar)
        if self.use_edge and platform.system() == 'Windows':
            try:
                edge_options = EdgeOptions()
                
                if self.headless:
                    edge_options.add_argument('--headless=new')
                
                # Standard Edge Optionen
                edge_options.add_argument('--no-sandbox')
                edge_options.add_argument('--disable-dev-shm-usage')
                edge_options.add_argument('--disable-gpu')
                edge_options.add_argument('--window-size=1920,1080')
                edge_options.add_argument('--disable-blink-features=AutomationControlled')
                edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                edge_options.add_experimental_option('useAutomationExtension', False)
                
                # User Agent
                edge_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0')
                
                driver = webdriver.Edge(options=edge_options)
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                if self.debug:
                    print("✅ Edge Browser gestartet")
                
                return driver
                
            except Exception as e:
                if self.debug:
                    print(f"⚠️  Edge nicht verfügbar: {e}")
                    print("   Versuche Chrome...")
        
        # Versuche Chrome/Chromium
        chrome_options = ChromeOptions()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # Standard Chrome Optionen für Selenium
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User Agent
        chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Versuche Chromium binary explizit zu setzen (für Container)
        import shutil
        chromium_path = shutil.which('chromium-browser') or shutil.which('chromium')
        if chromium_path:
            chrome_options.binary_location = chromium_path
            if self.debug:
                print(f"   Verwende Chromium: {chromium_path}")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            if self.debug:
                print("✅ Chrome/Chromium Browser gestartet")
            
            return driver
        except Exception as e:
            if self.debug:
                print(f"❌ Chrome/Chromium Fehler: {e}")
            raise
    
    def _extract_price(self, text: str, pattern: str) -> Optional[float]:
        """
        Extrahiert Preis aus Text mit deutschen Zahlenformaten
        
        Args:
            text: Text zum Durchsuchen
            pattern: Regex Pattern
            
        Returns:
            Preis als float oder None
        """
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(',', '.')
            try:
                return float(price_str)
            except ValueError:
                if self.debug:
                    print(f"⚠️  Konnte Preis nicht parsen: {match.group(1)}")
        return None
    
    def _wait_and_find_element(self, by: By, value: str, timeout: int = 10) -> Optional[Any]:
        """
        Wartet auf Element und gibt es zurück
        
        Args:
            by: Selenium By locator
            value: Locator value
            timeout: Timeout in Sekunden
            
        Returns:
            WebElement oder None
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            if self.debug:
                print(f"⏱️  Timeout beim Warten auf Element: {by}={value}")
            return None
    
    def _accept_cookies(self):
        """Akzeptiert Cookie-Banner falls vorhanden"""
        try:
            # Verschiedene mögliche Cookie-Button Selektoren
            cookie_selectors = [
                "button[data-track-id*='cookie']",
                "button[id*='cookie']",
                "button[class*='cookie']",
                ".uc-accept-all-button",
                "#uc-btn-accept-banner",
                "button:has-text('Alle akzeptieren')",
                "button:has-text('Akzeptieren')"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    cookie_btn.click()
                    if self.debug:
                        print("✅ Cookie-Banner akzeptiert")
                    time.sleep(0.5)
                    return
                except:
                    continue
                    
        except Exception as e:
            if self.debug:
                print(f"ℹ️  Kein Cookie-Banner gefunden oder bereits akzeptiert")
    
    def scrape_tariff(
        self,
        zip_code: str,
        annual_consumption: int = 3000,
        max_retries: int = 2
    ) -> Optional[Dict[str, Any]]:
        """
        Scrape EnBW Tarifrechner
        
        Args:
            zip_code: PLZ (z.B. "71065")
            annual_consumption: Jahresverbrauch in kWh (default: 3000)
            max_retries: Maximale Anzahl Wiederholungsversuche
            
        Returns:
            Dict mit Tarifdaten oder None bei Fehler
        """
        for attempt in range(max_retries):
            try:
                if self.debug:
                    print(f"\n{'='*60}")
                    print(f"🔍 EnBW Scraper - Versuch {attempt + 1}/{max_retries}")
                    print(f"   PLZ: {zip_code}, Verbrauch: {annual_consumption} kWh")
                    print(f"{'='*60}\n")
                
                # Setup Driver
                self.driver = self._setup_driver()
                
                # Lade Seite
                if self.debug:
                    print(f"📄 Lade {self.BASE_URL}")
                self.driver.get(self.BASE_URL)
                time.sleep(2)
                
                # Accept Cookies
                self._accept_cookies()
                
                # Screenshot vor Interaktion
                if self.debug:
                    self.driver.save_screenshot('enbw_01_initial.png')
                    print("📸 Screenshot gespeichert: enbw_01_initial.png")
                
                # Finde PLZ-Eingabefeld
                # EnBW nutzt wahrscheinlich ein Formular - suche nach verschiedenen Selektoren
                plz_selectors = [
                    "input[name*='zip']",
                    "input[name*='plz']",
                    "input[name*='postal']",
                    "input[placeholder*='Postleitzahl']",
                    "input[id*='zip']",
                    "input[id*='plz']",
                    "input[type='text']",
                    "input[type='tel']"
                ]
                
                plz_input = None
                for selector in plz_selectors:
                    plz_input = self._wait_and_find_element(By.CSS_SELECTOR, selector, timeout=5)
                    if plz_input:
                        if self.debug:
                            print(f"✅ PLZ-Feld gefunden: {selector}")
                        break
                
                if not plz_input:
                    raise Exception("PLZ-Eingabefeld nicht gefunden")
                
                # PLZ eingeben
                plz_input.clear()
                plz_input.send_keys(zip_code)
                if self.debug:
                    print(f"✏️  PLZ eingegeben: {zip_code}")
                
                # Warte auf Ort-Feld (Vue.js braucht Zeit)
                time.sleep(2)
                
                # Prüfe ob Ort erkannt wurde
                try:
                    ort_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='Ort']")
                    if ort_input.get_attribute('value'):
                        if self.debug:
                            print(f"✅ Ort erkannt: {ort_input.get_attribute('value')}")
                except:
                    pass
                
                time.sleep(0.5)
                
                # Finde Verbrauchs-Eingabefeld oder Dropdown
                consumption_selectors = [
                    "select[name*='consumption']",
                    "select[name*='verbrauch']",
                    "select[name*='kwh']",
                    "select[id*='consumption']",
                    "select[id*='verbrauch']",
                    "input[name*='consumption']",
                    "input[name*='verbrauch']",
                    "input[name*='kwh']",
                    "input[placeholder*='Verbrauch']",
                    "input[placeholder*='kWh']",
                    "input[id*='consumption']",
                    "input[id*='verbrauch']",
                    "input[type='number']"
                ]
                
                consumption_input = None
                is_dropdown = False
                
                for selector in consumption_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in elements:
                            if elem != plz_input and elem.is_displayed():
                                consumption_input = elem
                                is_dropdown = elem.tag_name == 'select'
                                if self.debug:
                                    print(f"✅ Verbrauchs-{'Dropdown' if is_dropdown else 'Feld'} gefunden: {selector}")
                                break
                        if consumption_input:
                            break
                    except:
                        continue
                
                if consumption_input:
                    if is_dropdown:
                        # Dropdown: Finde Option die am nächsten zu annual_consumption liegt
                        from selenium.webdriver.support.select import Select
                        select = Select(consumption_input)
                        
                        # Alle Optionen holen
                        options = select.options
                        best_option = None
                        best_option_value = None
                        min_difference = float('inf')
                        
                        if self.debug:
                            print(f"\n🔍 Dropdown-Analyse für Zielwert {annual_consumption} kWh:")
                            print("   Verfügbare Optionen:")
                        
                        for idx, option in enumerate(options):
                            # Extrahiere Zahl aus Option-Text
                            option_text = option.text.strip()
                            option_value_attr = option.get_attribute('value')
                            
                            # Versuche Zahl aus verschiedenen Quellen zu extrahieren
                            numbers = re.findall(r'\d+', option_text)
                            
                            # Wenn kein Text, versuche value-Attribut
                            if not numbers and option_value_attr:
                                numbers = re.findall(r'\d+', option_value_attr)
                            
                            if numbers:
                                option_value = int(numbers[0])
                                difference = abs(option_value - annual_consumption)
                                
                                if self.debug:
                                    print(f"   [{idx}] {option_text} = {option_value} kWh (Δ {difference} kWh)")
                                
                                # Überspringe Placeholder-Optionen (z.B. "Bitte wählen")
                                if option_value_attr and (option_value_attr == "" or "bitte" in option_text.lower()):
                                    continue
                                
                                if difference < min_difference:
                                    min_difference = difference
                                    best_option = option
                                    best_option_value = option_value
                        
                        if best_option:
                            # Wähle die beste Option mit JavaScript (robuster für Vue.js)
                            try:
                                # Versuche mit JavaScript zu setzen
                                best_value = best_option.get_attribute('value')
                                
                                # 1. Setze Select-Element
                                self.driver.execute_script(
                                    f"arguments[0].value = '{best_value}'; "
                                    "arguments[0].dispatchEvent(new Event('change', { bubbles: true })); "
                                    "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
                                    consumption_input
                                )
                                
                                # 2. Aktualisiere das hidden input "Verbrauch" (wichtig für EnBW!)
                                try:
                                    hidden_input = self.driver.find_element(By.CSS_SELECTOR, 'input[type="hidden"][name="Verbrauch"]')
                                    self.driver.execute_script(
                                        f"arguments[0].value = '{best_value}';",
                                        hidden_input
                                    )
                                    if self.debug:
                                        print(f"   ✅ Hidden Input 'Verbrauch' aktualisiert: {best_value} kWh")
                                except Exception as e:
                                    if self.debug:
                                        print(f"   ⚠️  Hidden Input nicht gefunden: {e}")
                                
                                if self.debug:
                                    print(f"\n✅ Dropdown-Option gewählt (JavaScript):")
                                    print(f"   Text: {best_option.text}")
                                    print(f"   Wert: {best_option_value} kWh")
                                    print(f"   Differenz zur Eingabe ({annual_consumption} kWh): {min_difference} kWh")
                                
                                # Aktualisiere annual_consumption auf den tatsächlich gewählten Wert
                                annual_consumption = best_option_value
                                
                                # Warte auf Vue.js Reaktion
                                time.sleep(1)
                            except Exception as e:
                                if self.debug:
                                    print(f"⚠️  JavaScript-Selektion fehlgeschlagen: {e}")
                                # Fallback: Normale Selektion
                                select.select_by_value(best_option.get_attribute('value'))
                                if self.debug:
                                    print(f"✅ Dropdown per Select gewählt")
                        else:
                            # Falls keine passende Option gefunden, nimm die erste nach dem Placeholder
                            if len(options) > 1:
                                select.select_by_index(1)
                                if self.debug:
                                    print(f"⚠️  Keine passende Option gefunden - Standard-Option gewählt (Index 1)")
                    else:
                        # Normales Input-Feld
                        consumption_input.clear()
                        consumption_input.send_keys(str(annual_consumption))
                        if self.debug:
                            print(f"✏️  Verbrauch eingegeben: {annual_consumption} kWh (direktes Eingabefeld)")
                    time.sleep(1)
                
                # Screenshot nach Eingabe
                if self.debug:
                    self.driver.save_screenshot('enbw_02_form_filled.png')
                    print("📸 Screenshot gespeichert: enbw_02_form_filled.png")
                
                # Finde und klicke Submit-Button mit mehreren Strategien
                button_clicked = False
                
                # Strategie 1: Suche nach data-testid="submit"
                try:
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[data-testid='submit']")
                    if submit_btn.is_displayed() and submit_btn.is_enabled():
                        # Scrolle zum Button
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                        time.sleep(0.5)
                        # Klicke mit JavaScript (robuster für Vue.js)
                        self.driver.execute_script("arguments[0].click();", submit_btn)
                        if self.debug:
                            print(f"✅ Submit-Button geklickt (data-testid, JavaScript)")
                        button_clicked = True
                        time.sleep(3)  # Warte auf Navigation
                except Exception as e:
                    if self.debug:
                        print(f"⚠️  Strategie 1 (data-testid) fehlgeschlagen: {e}")
                
                # Strategie 2: Suche nach Button-Text
                if not button_clicked:
                    button_selectors = [
                        "button[type='submit']",
                        "button[class*='submit']",
                        "button[class*='button--primary']",
                        "button"
                    ]
                    
                    for selector in button_selectors:
                        try:
                            buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for btn in buttons:
                                if btn.is_displayed() and btn.is_enabled():
                                    btn_text = btn.text.lower()
                                    if any(word in btn_text for word in ['tarife finden', 'berechnen', 'weiter', 'jetzt']):
                                        # Scrolle zum Button
                                        self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                                        time.sleep(0.5)
                                        # Klicke mit JavaScript
                                        self.driver.execute_script("arguments[0].click();", btn)
                                        if self.debug:
                                            print(f"✅ Button geklickt: {btn.text} (JavaScript)")
                                        button_clicked = True
                                        time.sleep(3)
                                        break
                            if button_clicked:
                                break
                        except Exception as e:
                            continue
                
                # Strategie 3: Formular direkt per JavaScript absenden
                if not button_clicked:
                    try:
                        form = self.driver.find_element(By.CSS_SELECTOR, "form[data-testid='tariff-finder-form']")
                        self.driver.execute_script("arguments[0].submit();", form)
                        if self.debug:
                            print(f"✅ Formular abgeschickt (JavaScript submit)")
                        button_clicked = True
                        time.sleep(3)
                    except Exception as e:
                        if self.debug:
                            print(f"⚠️  Strategie 3 (form submit) fehlgeschlagen: {e}")
                
                if not button_clicked:
                    if self.debug:
                        print("⚠️  Kein Submit-Button gefunden - Seite lädt möglicherweise dynamisch")
                    time.sleep(3)
                
                # Warte explizit auf die #tarife Ergebnis-Sektion (Vue.js SPA)
                if self.debug:
                    print("⏳ Warte auf Ergebnis-Sektion #tarife...")
                
                try:
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    
                    # Warte bis zu 10 Sekunden auf das tarife-Element
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'section#tarife[data-testid="tariff-overview-wrapper"]'))
                    )
                    
                    # Zusätzliche Wartezeit für vollständiges Rendering der Preisdaten
                    time.sleep(2)
                    
                    if self.debug:
                        print("✅ Ergebnis-Sektion #tarife geladen")
                except Exception as e:
                    if self.debug:
                        print(f"⚠️  Timeout bei #tarife, versuche trotzdem zu extrahieren... ({e})")
                    time.sleep(2)
                
                # Screenshot nach Ergebnisladen
                if self.debug:
                    self.driver.save_screenshot('enbw_03_results.png')
                    print("📸 Screenshot gespeichert: enbw_03_results.png")
                
                # Extrahiere Tarifinformationen
                page_source = self.driver.page_source
                
                if self.debug:
                    with open('enbw_page_source.html', 'w', encoding='utf-8') as f:
                        f.write(page_source)
                    print("💾 Seitenquellcode gespeichert: enbw_page_source.html")
                
                # Suche nach Preisangaben in verschiedenen Formaten
                # EnBW zeigt:
                # - Beispielhafte Monatskosten (z.B. 91 €)
                # - ⌀ Börsenpreis pro kWh (variabel, z.B. 9,94 Cent)
                # - Arbeitspreis pro kWh (z.B. 18,75 Cent)
                # - Arbeitspreis pro kWh gesamt (z.B. 28,69 Cent)
                # - Grundpreis pro Monat (z.B. 17,61 €)
                
                if self.debug:
                    print("\n🔍 Suche nach EnBW-Preiskomponenten:")
                
                # STRATEGIE 1: Direkte Extraktion aus data-testid="contract-data-value" (bevorzugt)
                # EnBW verwendet: <span class="product-contract-data__value" data-testid="contract-data-value">18,21&nbsp;€</span>
                
                base_price = None
                exchange_price = None
                markup_price = None
                total_price = None
                monthly_cost = None
                
                # Suche alle contract-data-value Elemente mit Kontext
                import re
                
                # Grundpreis pro Monat
                grundpreis_match = re.search(
                    r'<span[^>]*>Grundpreis\s+pro\s+Monat</span>.*?data-testid="contract-data-value">(\d+[,.]?\d*)&nbsp;€',
                    page_source, re.DOTALL
                )
                if grundpreis_match:
                    base_price = float(grundpreis_match.group(1).replace(',', '.'))
                    if self.debug:
                        print(f"   ✅ Grundpreis pro Monat: {base_price} €/Monat")
                
                # Börsenpreis pro kWh (variabel)
                boerse_match = re.search(
                    r'<span[^>]*>⌀\s+Börsenpreis\s+pro\s+kWh\s+\(variabel\)</span>.*?data-testid="contract-data-value">(\d+[,.]?\d*)&nbsp;Cent',
                    page_source, re.DOTALL
                )
                if boerse_match:
                    exchange_price = float(boerse_match.group(1).replace(',', '.'))
                    if self.debug:
                        print(f"   ✅ ⌀ Börsenpreis: {exchange_price} ct/kWh (variabel)")
                
                # Arbeitspreis pro kWh (Markup)
                arbeitspreis_match = re.search(
                    r'<span[^>]*>\+\s+Arbeitspreis\s+pro\s+kWh</span>.*?data-testid="contract-data-value">(\d+[,.]?\d*)&nbsp;Cent',
                    page_source, re.DOTALL
                )
                if arbeitspreis_match:
                    markup_price = float(arbeitspreis_match.group(1).replace(',', '.'))
                    if self.debug:
                        print(f"   ✅ + Arbeitspreis (Markup): {markup_price} ct/kWh")
                
                # Arbeitspreis pro kWh gesamt (variabel)
                gesamt_match = re.search(
                    r'<span[^>]*>Arbeitspreis\s+pro\s+kWh\s+gesamt\s+\(variabel\)</span>.*?data-testid="contract-data-value">(\d+[,.]?\d*)&nbsp;Cent',
                    page_source, re.DOTALL
                )
                if gesamt_match:
                    total_price = float(gesamt_match.group(1).replace(',', '.'))
                    if self.debug:
                        print(f"   ✅ Arbeitspreis gesamt: {total_price} ct/kWh (variabel)")
                
                # Beispielhafte Monatskosten
                monatskosten_match = re.search(
                    r'<div[^>]*class="product-info-price-bonus__price[^"]*">(\d+)<span[^>]*>&nbsp;€</span>.*?<span>Beispielhafte\s+Monatskosten</span>',
                    page_source, re.DOTALL
                )
                if monatskosten_match:
                    monthly_cost = float(monatskosten_match.group(1))
                    if self.debug:
                        print(f"   ✅ Beispielhafte Monatskosten: {monthly_cost} €/Monat")
                
                # STRATEGIE 2: Fallback mit alten Patterns (für Kompatibilität)
                if not base_price:
                    # Pattern für Grundpreis pro Monat (€/Monat)
                    base_patterns = [
                        r'Grundpreis\s+pro\s+Monat[:\s]+(\d+[,.]?\d*)\s*€',
                        r'Grundpreis[:\s]+(\d+[,.]?\d*)\s*€[/\s]*Monat',
                        r'Grundgebühr[:\s]+(\d+[,.]?\d*)\s*€[/\s]*Monat',
                        r'Monatlicher\s+Grundpreis[:\s]+(\d+[,.]?\d*)\s*€'
                    ]
                    
                    for pattern in base_patterns:
                        base_price = self._extract_price(page_source, pattern)
                        if base_price:
                            if self.debug:
                                print(f"   ✅ Grundpreis pro Monat (Fallback): {base_price} €/Monat")
                            break
                
                if not exchange_price:
                    # Pattern für durchschnittlichen Börsenpreis (ct/kWh)
                    exchange_patterns = [
                        r'⌀\s+Börsenpreis\s+pro\s+kWh[:\s\(]*variabel\)?[:\s]+(\d+[,.]?\d*)\s*Cent',
                        r'Börsenpreis[:\s]+(\d+[,.]?\d*)\s*Cent',
                        r'Börsenpreis[:\s]+(\d+[,.]?\d*)\s*ct'
                    ]
                    
                    for pattern in exchange_patterns:
                        exchange_price = self._extract_price(page_source, pattern)
                        if exchange_price:
                            if self.debug:
                                print(f"   ✅ ⌀ Börsenpreis (Fallback): {exchange_price} ct/kWh (variabel)")
                            break
                
                if not markup_price:
                    # Pattern für Arbeitspreis/Markup
                    markup_patterns = [
                        r'\+\s+Arbeitspreis\s+pro\s+kWh[:\s]+(\d+[,.]?\d*)\s*Cent',
                        r'Arbeitspreis\s+pro\s+kWh[:\s]+(\d+[,.]?\d*)\s*Cent',
                        r'Verbrauchspreis[:\s]+(\d+[,.]?\d*)\s*ct[/\s]*kWh'
                    ]
                    
                    for pattern in markup_patterns:
                        markup_price = self._extract_price(page_source, pattern)
                        if markup_price:
                            if self.debug:
                                print(f"   ✅ + Arbeitspreis (Fallback): {markup_price} ct/kWh")
                            break
                
                if not total_price:
                    # Pattern für Gesamt-Arbeitspreis
                    total_patterns = [
                        r'Arbeitspreis\s+pro\s+kWh\s+gesamt[:\s\(]*variabel\)?[:\s]+(\d+[,.]?\d*)\s*Cent',
                        r'Gesamtpreis[:\s]+(\d+[,.]?\d*)\s*Cent[/\s]*kWh'
                    ]
                    
                    for pattern in total_patterns:
                        total_price = self._extract_price(page_source, pattern)
                        if total_price:
                            if self.debug:
                                print(f"   ✅ Arbeitspreis gesamt (Fallback): {total_price} ct/kWh")
                            break
                
                if not monthly_cost:
                    # Pattern für Monatskosten
                    monthly_patterns = [
                        r'Beispielhafte\s+Monatskosten[:\s]+(\d+[,.]?\d*)\s*€',
                        r'Monatliche\s+Kosten[:\s]+(\d+[,.]?\d*)\s*€'
                    ]
                    
                    for pattern in monthly_patterns:
                        monthly_cost = self._extract_price(page_source, pattern)
                        if monthly_cost:
                            if self.debug:
                                print(f"   ✅ Beispielhafte Monatskosten (Fallback): {monthly_cost} €/Monat")
                            break
                
                # Validierung - mindestens Grundpreis sollte gefunden werden
                if not base_price:
                    raise Exception("Keine Preisdaten gefunden - möglicherweise Seitenstruktur geändert")
                
                # Erstelle Rückgabe-Dict
                result = {
                    'provider': 'EnBW',
                    'tariff_name': 'EnBW Dynamisch',
                    'base_price_monthly': base_price,                    # Grundpreis (fix)
                    'markup_ct_kwh': markup_price,                       # Arbeitspreis ohne Börse (fix)
                    'exchange_price_ct_kwh': exchange_price,             # Durchschnittlicher Börsenpreis (variabel)
                    'total_kwh_price_ct': total_price,                   # Gesamtpreis pro kWh (Arbeit + Börse)
                    'monthly_cost_example': monthly_cost,                # Beispiel Monatskosten
                    'zip_code': zip_code,
                    'annual_consumption_kwh': annual_consumption,
                    'data_source': 'scraped',
                    'scraped_at': datetime.now().isoformat(),
                    'url': self.BASE_URL
                }
                
                if self.debug:
                    print(f"\n✅ Erfolgreich gescraped:")
                    print(f"   Provider: {result['provider']}")
                    print(f"   Tarif: {result['tariff_name']}")
                    print(f"   Grundpreis: {result['base_price_monthly']} €/Monat")
                    if result['markup_ct_kwh']:
                        print(f"   + Arbeitspreis: {result['markup_ct_kwh']} ct/kWh")
                    if result['exchange_price_ct_kwh']:
                        print(f"   + ⌀ Börsenpreis: {result['exchange_price_ct_kwh']} ct/kWh (variabel)")
                    if result['total_kwh_price_ct']:
                        print(f"   = Gesamt kWh-Preis: {result['total_kwh_price_ct']} ct/kWh")
                    if result['monthly_cost_example']:
                        print(f"   Beispiel Monatskosten: {result['monthly_cost_example']} €")
                
                return result
                
            except Exception as e:
                if self.debug:
                    print(f"\n❌ Fehler bei Versuch {attempt + 1}: {str(e)}")
                    if self.driver:
                        self.driver.save_screenshot(f'enbw_error_{attempt + 1}.png')
                        print(f"📸 Error Screenshot: enbw_error_{attempt + 1}.png")
                
                if attempt < max_retries - 1:
                    if self.debug:
                        print(f"🔄 Wiederhole in 2 Sekunden...")
                    time.sleep(2)
                else:
                    if self.debug:
                        print(f"\n❌ Scraping fehlgeschlagen nach {max_retries} Versuchen")
                    return None
                    
            finally:
                if self.driver:
                    self.driver.quit()
                    self.driver = None
        
        return None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.driver:
            self.driver.quit()


def test_dropdown_logic():
    """Testet die Dropdown-Logik ohne Browser"""
    print("\n" + "="*60)
    print("EnBW Dropdown-Logik Test (ohne Browser)")
    print("="*60 + "\n")
    
    # EnBW Dropdown-Optionen (von der echten Webseite)
    enbw_options = {
        1450: "1450 (1 Person)",
        2450: "2450 (2 Personen)",
        3050: "3050 (3 Personen)",
        4150: "4150 (4 Personen)",
        4850: "4850 (5 Personen)"
    }
    
    # Test-Szenario basierend auf echten Daten
    test_cases = [
        {"zip": "72760", "consumption": 3050},  # Echtes Beispiel vom User
        {"zip": "68161", "consumption": 3250},
        {"zip": "71065", "consumption": 2500},
    ]
    
    print("📊 EnBW extrahiert folgende Daten:")
    print("─" * 60)
    print("1. Grundpreis pro Monat (€/Monat) - z.B. 17,61 €")
    print("2. + Arbeitspreis pro kWh (ct/kWh) - z.B. 18,75 ct")
    print("3. + ⌀ Börsenpreis pro kWh (ct/kWh, variabel) - z.B. 9,94 ct")
    print("4. = Arbeitspreis gesamt (ct/kWh) - z.B. 28,69 ct")
    print("5. Beispielhafte Monatskosten - z.B. 91 €")
    print("─" * 60)
    
    print("\n📋 Beispiel für PLZ 72760, 3050 kWh/Jahr:")
    print("   Grundpreis pro Monat: 17,61 €")
    print("   + Arbeitspreis: 18,75 ct/kWh")
    print("   + ⌀ Börsenpreis: 9,94 ct/kWh (variabel)")
    print("   = Gesamt: 28,69 ct/kWh")
    print("   Beispiel Monatskosten: 91 €")
    
    for test in test_cases:
        consumption = test['consumption']
        
        print(f"\n{'─'*60}")
        print(f"Dropdown-Test: PLZ {test['zip']}, Eingabe: {consumption} kWh")
        print(f"{'─'*60}\n")
        
        # Simuliere die Dropdown-Logik aus dem Scraper
        best_option = None
        best_value = None
        min_difference = float('inf')
        
        print("Verfügbare Dropdown-Optionen:")
        print(f"{'Index':<8} {'Option':<30} {'Wert':>10} {'Differenz':>12}")
        print("─" * 60)
        
        for idx, (value, text) in enumerate(enbw_options.items()):
            difference = abs(value - consumption)
            marker = ""
            
            if difference < min_difference:
                min_difference = difference
                best_value = value
                best_option = text
                marker = " ← WIRD GEWÄHLT"
            
            print(f"{idx:<8} {text:<30} {value:>10} {difference:>10} kWh{marker}")
        
        print("─" * 60)
        print(f"✅ Gewählt: {best_option} (Δ {min_difference} kWh)")


def main():
    """Test-Funktion für den EnBW Scraper"""
    print("\n" + "="*60)
    print("EnBW Dynamischer Stromtarif Scraper - ECHTER TEST")
    print("="*60 + "\n")
    
    print("🔍 Teste mit PLZ 71065 und 2250 kWh")
    print("─" * 60 + "\n")
    
    try:
        # Versuche echten Browser-Test
        with EnbwScraper(headless=True, debug=True, use_edge=False) as scraper:
            result = scraper.scrape_tariff(
                zip_code="71065",
                annual_consumption=2250
            )
            
            if result:
                print("\n" + "="*60)
                print("✅ ERFOLG - Echte Daten von EnBW extrahiert!")
                print("="*60)
                print(f"\n📍 PLZ: {result['zip_code']}")
                print(f"⚡ Gewählter Verbrauch: {result['annual_consumption_kwh']} kWh/Jahr")
                print(f"\n� Preiskomponenten:")
                print(f"   Grundpreis: {result['base_price_monthly']:.2f} €/Monat")
                
                if result['markup_ct_kwh']:
                    print(f"   + Arbeitspreis: {result['markup_ct_kwh']:.2f} ct/kWh")
                
                if result['exchange_price_ct_kwh']:
                    print(f"   + ⌀ Börsenpreis: {result['exchange_price_ct_kwh']:.2f} ct/kWh (variabel)")
                
                if result['total_kwh_price_ct']:
                    print(f"   = Gesamt pro kWh: {result['total_kwh_price_ct']:.2f} ct/kWh")
                
                if result['monthly_cost_example']:
                    print(f"\n📊 Beispielhafte Monatskosten: {result['monthly_cost_example']:.0f} €")
                
                print(f"\n🕐 Zeitstempel: {result['scraped_at']}")
                print(f"🌐 Quelle: {result['url']}")
            else:
                print("\n❌ Scraping fehlgeschlagen")
                
    except Exception as e:
        print(f"\n❌ Fehler beim Browser-Test: {str(e)}")
        print("\n💡 Fallback: Zeige Dropdown-Logik")
        print("─" * 60)
        
        # Fallback zu Dropdown-Test
        enbw_options = {
            1450: "1450 (1 Person)",
            2450: "2450 (2 Personen)",
            3050: "3050 (3 Personen)",
            4150: "4150 (4 Personen)",
            4850: "4850 (5 Personen)"
        }
        
        target = 2250
        best_value = min(enbw_options.keys(), key=lambda x: abs(x - target))
        
        print(f"\n✅ Für Eingabe {target} kWh würde gewählt werden:")
        print(f"   {enbw_options[best_value]} (Differenz: {abs(best_value - target)} kWh)")
        print(f"\n   Der Scraper würde dann die ECHTEN Preise")
        print(f"   von der EnBW-Seite extrahieren (nicht hardcodiert!)")


if __name__ == "__main__":
    main()
