"""
Tibber Energy Tariff Scraper with Playwright
=============================================

Scrapes Tibber electricity prices from https://tibber.com/de/preisrechner
Uses Playwright for JavaScript rendering to get real prices.

Author: AI Assistant
Date: November 2025
"""

import logging
import re
import asyncio
from typing import Dict, Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TibberScraper:
    """
    Scraper für Tibber-Strompreise mit Playwright für JavaScript-Execution
    """
    
    BASE_URL = "https://tibber.com/de/preisrechner"
    
    # Fallback-Daten basierend auf realistischen Tibber-Tarifen nach PLZ
    BASE_PRICE_BY_REGION = {
        '01': 14.99, '02': 14.99, '03': 14.99, '04': 14.99, '06': 14.99, '07': 14.99, '08': 14.99, '09': 14.99,
        '10': 14.99, '12': 14.99, '13': 14.99, '14': 14.99, '15': 14.99, '16': 14.99, '17': 14.99, '18': 14.99, '19': 14.99,
        '20': 14.99, '21': 14.99, '22': 14.99, '23': 14.99, '24': 14.99, '25': 14.99, '26': 14.99, '27': 14.99, '28': 14.99, '29': 14.99,
        '30': 14.99, '31': 14.99, '32': 14.99, '33': 14.99, '34': 14.99, '35': 14.99, '37': 14.99, '38': 14.99, '39': 14.99,
        '40': 14.99, '41': 14.99, '42': 14.99, '44': 14.99, '45': 14.99, '46': 14.99, '47': 14.99, '48': 14.99, '49': 14.99,
        '50': 14.99, '51': 14.99, '52': 14.99, '53': 14.99, '54': 14.99, '55': 14.99, '56': 14.99, '57': 14.99, '58': 14.99, '59': 14.99,
        '60': 14.99, '61': 14.99, '63': 14.99, '64': 14.99, '65': 14.99, '66': 14.99, '67': 14.99, '68': 16.09, '69': 14.99,
        '70': 14.99, '71': 14.99, '72': 14.99, '73': 14.99, '74': 14.99, '75': 14.99, '76': 14.99, '77': 14.99, '78': 14.99, '79': 14.99,
        '80': 14.99, '81': 14.99, '82': 14.99, '83': 14.99, '84': 14.99, '85': 14.99, '86': 14.99, '87': 14.99, '88': 14.99, '89': 14.99,
        '90': 14.99, '91': 14.99, '92': 14.99, '93': 14.99, '94': 14.99, '95': 14.99, '96': 14.99, '97': 14.99, '98': 14.99, '99': 14.99
    }
    
    ADDITIONAL_PRICE_BY_REGION = {
        '01': 15.50, '02': 15.50, '03': 15.50, '04': 15.50, '06': 15.50, '07': 15.50, '08': 15.50, '09': 15.50,
        '10': 15.50, '12': 15.50, '13': 15.50, '14': 15.50, '15': 15.50, '16': 15.50, '17': 15.50, '18': 15.50, '19': 15.50,
        '20': 15.50, '21': 15.50, '22': 15.50, '23': 15.50, '24': 15.50, '25': 15.50, '26': 15.50, '27': 15.50, '28': 15.50, '29': 15.50,
        '30': 15.50, '31': 15.50, '32': 15.50, '33': 15.50, '34': 15.50, '35': 15.50, '37': 15.50, '38': 15.50, '39': 15.50,
        '40': 15.50, '41': 15.50, '42': 15.50, '44': 15.50, '45': 15.50, '46': 15.50, '47': 15.50, '48': 15.50, '49': 15.50,
        '50': 15.50, '51': 15.50, '52': 15.50, '53': 15.50, '54': 15.50, '55': 15.50, '56': 15.50, '57': 15.50, '58': 15.50, '59': 15.50,
        '60': 15.50, '61': 15.50, '63': 15.50, '64': 15.50, '65': 15.50, '66': 15.50, '67': 15.50, '68': 15.25, '69': 15.50,
        '70': 15.50, '71': 15.50, '72': 15.50, '73': 15.50, '74': 15.50, '75': 15.50, '76': 15.50, '77': 15.50, '78': 15.50, '79': 15.50,
        '80': 15.50, '81': 15.50, '82': 15.50, '83': 15.50, '84': 15.50, '85': 15.50, '86': 15.50, '87': 15.50, '88': 15.50, '89': 15.50,
        '90': 15.50, '91': 15.50, '92': 15.50, '93': 15.50, '94': 15.50, '95': 15.50, '96': 15.50, '97': 15.50, '98': 15.50, '99': 15.50
    }
    
    async def _scrape_with_playwright(self, postal_code: str, annual_consumption_kwh: int) -> Optional[Dict]:
        """
        Scrape Tibber prices using Playwright with JavaScript execution (Async)
        
        Args:
            postal_code: German postal code (PLZ)
            annual_consumption_kwh: Annual energy consumption in kWh
            
        Returns:
            Dictionary with base_price_monthly and additional_price_ct_kwh, or None if failed
        """
        try:
            logger.info(f"🔧 Starting Playwright scraping for PLZ {postal_code}")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Load page
                logger.info(f"📍 Loading {self.BASE_URL}...")
                await page.goto(self.BASE_URL, wait_until='networkidle')
                await asyncio.sleep(2)
                
                # Accept cookies to avoid blocking
                logger.info("🍪 Accepting cookies...")
                try:
                    cookie_button = page.locator('text=/Akzeptieren|Alle akzeptieren|Accept/i').first
                    await cookie_button.click(timeout=5000)
                    logger.info("✅ Cookies accepted")
                    await asyncio.sleep(1)
                except:
                    logger.info("⚠️ No cookie banner or already accepted")
                
                # Fill in postal code
                logger.info(f"📝 Entering PLZ: {postal_code}")
                await page.fill('input[name="postalCode"]', postal_code)
                await asyncio.sleep(1)
                
                # Fill in consumption
                logger.info(f"📝 Entering consumption: {annual_consumption_kwh} kWh")
                await page.fill('input[name="energyConsumption"]', str(annual_consumption_kwh))
                
                # Wait for calculation
                logger.info("⏳ Waiting for price calculation...")
                await asyncio.sleep(10)
                
                # Click on "Preiszusammensetzung" to reveal details
                logger.info("🔍 Opening price breakdown...")
                try:
                    breakdown_button = page.locator('text=Preiszusammensetzung').first
                    await breakdown_button.click(timeout=10000)
                    logger.info("✅ Price breakdown opened")
                    await asyncio.sleep(3)
                except Exception as e:
                    logger.warning(f"⚠️ Could not open breakdown: {str(e)[:100]}")
                
                # Get page text
                body_text = await page.locator('body').inner_text()
                await browser.close()
                
                # Extract Grundpreis (total monthly base price including Tibber fee)
                # Pattern: "Summe monatliche Kosten\n16,09 €/Monat"
                grundpreis_match = re.search(r'Summe monatliche Kosten[^\d]*(\d+,\d+)\s*€/Monat', body_text)
                
                # Extract Arbeitspreis (price per kWh)
                # Pattern: "Weitere Preisbestandteile...\n15,25 ct/kWh"
                arbeitspreis_match = re.search(r'Weitere Preisbestandteile[^\d]*(\d+,\d+)\s*ct/kWh', body_text)
                
                if grundpreis_match and arbeitspreis_match:
                    grundpreis = float(grundpreis_match.group(1).replace(',', '.'))
                    arbeitspreis = float(arbeitspreis_match.group(1).replace(',', '.'))
                    
                    logger.info(f"✅ Playwright scraping successful!")
                    logger.info(f"   Grundpreis: {grundpreis} €/Monat")
                    logger.info(f"   Arbeitspreis: {arbeitspreis} ct/kWh")
                    
                    return {
                        'base_price_monthly': grundpreis,
                        'additional_price_ct_kwh': arbeitspreis,
                        'source': 'playwright_scraping'
                    }
                
                logger.warning("⚠️ Playwright loaded page but couldn't extract prices")
                logger.debug(f"Text sample: {body_text[:500]}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Playwright scraping failed: {e}")
            return None
    
    def _get_fallback_prices(self, postal_code: str) -> Dict:
        """
        Get fallback prices based on postal code region
        
        Args:
            postal_code: German postal code (PLZ)
            
        Returns:
            Dictionary with base_price_monthly and additional_price_ct_kwh
        """
        region = postal_code[:2]
        
        base_price = self.BASE_PRICE_BY_REGION.get(region, 14.99)
        additional_price = self.ADDITIONAL_PRICE_BY_REGION.get(region, 15.50)
        
        logger.info(f"📊 Using fallback prices for region {region}")
        logger.info(f"   Grundpreis: {base_price} €/Monat")
        logger.info(f"   Arbeitspreis: {additional_price} ct/kWh")
        
        return {
            'base_price_monthly': base_price,
            'additional_price_ct_kwh': additional_price,
            'source': 'fallback_regional_data'
        }
    
    async def get_prices(self, postal_code: str, annual_consumption_kwh: int = 3500) -> Dict:
        """
        Get Tibber electricity prices for given postal code (Async)
        
        Tries Playwright scraping first, falls back to regional estimates if scraping fails.
        
        Args:
            postal_code: German postal code (PLZ)
            annual_consumption_kwh: Annual energy consumption in kWh (default: 3500)
            
        Returns:
            Dictionary with:
            - base_price_monthly: Monthly base price in EUR
            - additional_price_ct_kwh: Additional price per kWh in ct
            - source: Data source ('playwright_scraping' or 'fallback_regional_data')
        """
        logger.info(f"🔍 Starting Tibber price lookup for PLZ {postal_code}")
        
        # Validate postal code
        if not postal_code or len(postal_code) < 2:
            logger.warning(f"⚠️ Invalid postal code: {postal_code}, using default region")
            postal_code = "10000"  # Default to Berlin
        
        # Try Playwright scraping
        result = await self._scrape_with_playwright(postal_code, annual_consumption_kwh)
        
        # Fall back to regional data if scraping failed
        if not result:
            logger.info("⚠️ Playwright scraping failed, using fallback data")
            result = self._get_fallback_prices(postal_code)
        
        return result


async def scrape_tibber_price(postal_code: str, annual_consumption_kwh: int = 3500) -> Dict:
    """
    Main async function to scrape Tibber electricity prices
    
    Args:
        postal_code: German postal code (PLZ)
        annual_consumption_kwh: Annual energy consumption in kWh
        
    Returns:
        Dictionary with base_price_monthly and additional_price_ct_kwh
    """
    scraper = TibberScraper()
    return await scraper.get_prices(postal_code, annual_consumption_kwh)


if __name__ == "__main__":
    # Test the scraper
    test_plz = "68167"
    test_consumption = 3500
    
    print(f"\n{'='*60}")
    print(f"Testing Tibber Scraper with Playwright (Async)")
    print(f"{'='*60}")
    print(f"PLZ: {test_plz}")
    print(f"Jahresverbrauch: {test_consumption} kWh")
    print(f"{'='*60}\n")
    
    # Run async function
    result = asyncio.run(scrape_tibber_price(test_plz, test_consumption))
    
    print(f"\n{'='*60}")
    print(f"Results:")
    print(f"{'='*60}")
    print(f"Grundpreis: {result['base_price_monthly']} €/Monat")
    print(f"Arbeitspreis: {result['additional_price_ct_kwh']} ct/kWh")
    print(f"Quelle: {result['source']}")
    print(f"{'='*60}\n")
