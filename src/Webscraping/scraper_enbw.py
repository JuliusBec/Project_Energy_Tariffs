#!/usr/bin/env python3
"""
EnBW Dynamischer Stromtarif Scraper (Playwright Async)
=======================================================
Scraper für https://www.enbw.com/strom/dynamischer-stromtarif

Extrahiert:
- Grundpreis (€/Monat)
- Arbeitspreis / Markup (ct/kWh)
- Durchschnittlicher Börsenpreis (ct/kWh)
- Gesamtpreis (ct/kWh)

Input: PLZ, Jahresverbrauch (kWh)
Output: Dict mit Tarifinformationen
"""

import logging
import re
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnbwScraper:
    """Scraper für EnBW dynamischen Stromtarif mit Playwright"""
    
    BASE_URL = "https://www.enbw.com/strom/dynamischer-stromtarif"
    
    # Fallback-Daten basierend auf realistischen EnBW-Tarifen nach PLZ
    BASE_PRICE_BY_REGION = {
        '68': 18.21,  # Mannheim
        '69': 18.21,  # Heidelberg
        '70': 18.21,  # Stuttgart
        '71': 18.21,  # Ludwigsburg
        '72': 18.21,  # Tübingen
        '73': 18.21,  # Esslingen
        '74': 18.21,  # Heilbronn
        '75': 18.21,  # Karlsruhe
        '76': 18.21,  # Pforzheim
        '77': 18.21,  # Offenburg
        '78': 18.21,  # Freiburg
        '79': 18.21,  # Freiburg
    }
    
    MARKUP_BY_REGION = {
        '68': 15.36,  # Mannheim
        '69': 15.36,  # Heidelberg
        '70': 15.36,  # Stuttgart
        '71': 15.36,  # Ludwigsburg
        '72': 15.36,  # Tübingen
        '73': 15.36,  # Esslingen
        '74': 15.36,  # Heilbronn
        '75': 15.36,  # Karlsruhe
        '76': 15.36,  # Pforzheim
        '77': 15.36,  # Offenburg
        '78': 15.36,  # Freiburg
        '79': 15.36,  # Freiburg
    }
    
    async def _scrape_with_playwright(self, zip_code: str, annual_consumption: int) -> Optional[Dict]:
        """
        Scrape EnBW prices using Playwright with JavaScript execution (Async)
        
        Args:
            zip_code: German postal code (PLZ)
            annual_consumption: Annual energy consumption in kWh
            
        Returns:
            Dictionary with pricing information, or None if failed
        """
        try:
            logger.info(f"🔧 Starting Playwright scraping for PLZ {zip_code}")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Round consumption to nearest available option
                available_options = [1450, 2450, 3050, 4150, 4850]
                closest_consumption = min(available_options, key=lambda x: abs(x - annual_consumption))
                
                # Build direct URL with parameters (this loads the tariff results page directly)
                tariff_url = f"{self.BASE_URL}?Postleitzahl={zip_code}&Verbrauch={closest_consumption}&Typ=Strom&context=shared.offer-context.electricity.dynamic.pk#tarife"
                
                logger.info(f"📍 Loading tariff page with PLZ {zip_code} and {closest_consumption} kWh...")
                await page.goto(tariff_url, wait_until='networkidle')
                await asyncio.sleep(3)
                
                # Accept cookies
                logger.info("🍪 Accepting cookies...")
                try:
                    cookie_button = page.locator('button:has-text("Alle akzeptieren")').first
                    await cookie_button.click(timeout=5000, force=True)
                    logger.info("✅ Cookies accepted")
                    await asyncio.sleep(2)
                except:
                    logger.info("⚠️ No cookie banner or already accepted")
                
                # Click "Weitere Tarifdetails" to open modal with detailed pricing
                logger.info("🔍 Opening detail modal...")
                try:
                    detail_btn = page.locator('text=Weitere Tarifdetails').first
                    await detail_btn.click(timeout=5000, force=True)
                    await asyncio.sleep(2)  # Wait for modal to open
                    logger.info("✅ Detail modal opened")
                except Exception as e:
                    logger.warning(f"⚠️ Could not click detail button: {e}")
                
                # Try to get content from modal first, fallback to body
                modal_text = ""
                try:
                    modal = page.locator('.modal').first
                    if await modal.is_visible(timeout=2000):
                        modal_text = await modal.inner_text()
                        logger.info("✅ Found modal content")
                except:
                    pass
                
                # Get body text as fallback
                body_text = await page.locator('body').inner_text()
                search_text = modal_text if modal_text else body_text
                
                await browser.close()
                
                # Extract prices using regex from modal or body
                # Grundpreis Pattern: "Grundpreis pro Monat 18,21 €"
                grundpreis_match = re.search(r'Grundpreis[^\d]*?(\d+[,.]?\d*)\s*€', search_text, re.IGNORECASE)
                
                # Arbeitspreis Pattern: "Arbeitspreis pro kWh 15,36 Cent" (from modal)
                arbeitspreis_match = re.search(r'Arbeitspreis[^\d]*?(\d+[,.]?\d*)\s*(ct|Cent)', search_text, re.IGNORECASE)
                
                # Börsenpreis Pattern
                boerse_match = re.search(r'Börsenpreis[^\d]*?(\d+[,.]?\d*)\s*(ct|Cent)', search_text, re.IGNORECASE)
                
                if grundpreis_match:
                    base_price = float(grundpreis_match.group(1).replace(',', '.'))
                    logger.info(f"✅ Found Grundpreis: {base_price} €/Monat")
                    
                    markup = None
                    exchange_price = None
                    
                    if arbeitspreis_match:
                        markup = float(arbeitspreis_match.group(1).replace(',', '.'))
                        logger.info(f"✅ Found Arbeitspreis: {markup} ct/kWh")
                    
                    if boerse_match:
                        exchange_price = float(boerse_match.group(1).replace(',', '.'))
                        logger.info(f"✅ Found Börsenpreis: {exchange_price} ct/kWh")
                    
                    return {
                        'provider': 'EnBW',
                        'tariff_name': 'EnBW Dynamisch',
                        'base_price_monthly': base_price,
                        'markup_ct_kwh': markup,
                        'exchange_price_ct_kwh': exchange_price,
                        'total_kwh_price_ct': (markup + exchange_price) if (markup and exchange_price) else None,
                        'zip_code': zip_code,
                        'annual_consumption_kwh': annual_consumption,
                        'data_source': 'playwright_scraping',
                        'scraped_at': datetime.now().isoformat(),
                        'url': self.BASE_URL
                    }
                
                logger.warning("⚠️ Playwright loaded page but couldn't extract prices")
                return None
                
        except Exception as e:
            logger.error(f"❌ Playwright scraping failed: {e}")
            return None
    
    def _get_fallback_prices(self, zip_code: str, annual_consumption: int) -> Dict:
        """
        Get fallback prices based on postal code region
        
        Args:
            zip_code: German postal code (PLZ)
            annual_consumption: Annual consumption in kWh
            
        Returns:
            Dictionary with pricing information
        """
        region = zip_code[:2]
        
        base_price = self.BASE_PRICE_BY_REGION.get(region, 18.21)
        markup = self.MARKUP_BY_REGION.get(region, 15.36)
        
        logger.info(f"📊 Using fallback prices for region {region}")
        logger.info(f"   Grundpreis: {base_price} €/Monat")
        logger.info(f"   Arbeitspreis: {markup} ct/kWh")
        
        return {
            'provider': 'EnBW',
            'tariff_name': 'EnBW Dynamisch',
            'base_price_monthly': base_price,
            'markup_ct_kwh': markup,
            'exchange_price_ct_kwh': None,  # Not available in fallback
            'total_kwh_price_ct': None,
            'zip_code': zip_code,
            'annual_consumption_kwh': annual_consumption,
            'data_source': 'fallback_regional_data',
            'scraped_at': datetime.now().isoformat(),
            'url': self.BASE_URL
        }
    
    async def scrape_tariff(self, zip_code: str, annual_consumption: int = 3000) -> Dict:
        """
        Scrape EnBW tariff information (Async)
        
        Args:
            zip_code: German postal code (PLZ)
            annual_consumption: Annual energy consumption in kWh (default: 3000)
            
        Returns:
            Dictionary with pricing information
        """
        logger.info(f"🔍 Starting EnBW price lookup for PLZ {zip_code}")
        
        # Try Playwright scraping
        result = await self._scrape_with_playwright(zip_code, annual_consumption)
        
        # Fall back to regional data if scraping failed
        if not result:
            logger.info("⚠️ Playwright scraping failed, using fallback data")
            result = self._get_fallback_prices(zip_code, annual_consumption)
        
        return result


async def scrape_enbw_tariff(zip_code: str, annual_consumption: int = 3000) -> Dict:
    """
    Main async function to scrape EnBW electricity tariff
    
    Args:
        zip_code: German postal code (PLZ)
        annual_consumption: Annual energy consumption in kWh
        
    Returns:
        Dictionary with pricing information
    """
    scraper = EnbwScraper()
    return await scraper.scrape_tariff(zip_code, annual_consumption)


if __name__ == "__main__":
    # Test the scraper
    test_plz = "68167"
    test_consumption = 3500
    
    print(f"\n{'='*60}")
    print(f"Testing EnBW Scraper with Playwright (Async)")
    print(f"{'='*60}")
    print(f"PLZ: {test_plz}")
    print(f"Jahresverbrauch: {test_consumption} kWh")
    print(f"{'='*60}\n")
    
    # Run async function
    result = asyncio.run(scrape_enbw_tariff(test_plz, test_consumption))
    
    print(f"\n{'='*60}")
    print(f"Results:")
    print(f"{'='*60}")
    print(f"Provider: {result['provider']}")
    print(f"Tarif: {result['tariff_name']}")
    print(f"Grundpreis: {result['base_price_monthly']} €/Monat")
    print(f"Arbeitspreis: {result['markup_ct_kwh']} ct/kWh")
    if result.get('exchange_price_ct_kwh'):
        print(f"Börsenpreis: {result['exchange_price_ct_kwh']} ct/kWh")
    print(f"Quelle: {result['data_source']}")
    print(f"{'='*60}\n")
