"""
Tado Energy Scraper - Playwright Async Version
Extrahiert dynamische Stromtarif-Daten von Tado Energy (energy.tado.com)
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, Optional
from playwright.async_api import async_playwright, Page, Browser

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TadoScraper:
    """Async Playwright-based scraper for Tado Energy tariffs"""
    
    BASE_URL = "https://energy.tado.com/price"
    
    async def _scrape_with_playwright(self, zip_code: str, annual_consumption: int) -> Optional[Dict]:
        """
        Scrape Tado tariff using Playwright async
        
        Args:
            zip_code: German postal code (PLZ)
            annual_consumption: Annual consumption in kWh
            
        Returns:
            Dict with tariff data or None if scraping failed
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Build URL with parameters for direct tariff display
                tariff_url = f"{self.BASE_URL}?yearlyConsumption={annual_consumption}&zipcode={zip_code}&includeHourlyTariffSavings=true&hasSmartMeter=true"
                
                logger.info(f"📍 Loading Tado price page for PLZ {zip_code}, {annual_consumption} kWh...")
                await page.goto(tariff_url, wait_until='networkidle')
                await asyncio.sleep(8)  # Wait for SPA (Angular/Vue) to load fully
                
                # Accept cookies if present
                logger.info("🍪 Accepting cookies...")
                try:
                    cookie_button = page.locator('button:has-text("Accept")').first
                    await cookie_button.click(timeout=3000, force=True)
                    logger.info("✅ Cookies accepted")
                    await asyncio.sleep(2)
                except:
                    logger.info("⚠️ No cookie banner or already accepted")
                
                # Click "Mehr Details" button to expand price breakdown
                logger.info("🔍 Expanding price details...")
                try:
                    # Click first "Mehr Details" button (for Arbeitspreis)
                    detail_buttons = page.locator('text=Mehr Details')
                    await detail_buttons.first.click(force=True, timeout=5000)
                    await asyncio.sleep(3)
                    logger.info("✅ Price details expanded")
                except Exception as e:
                    logger.warning(f"⚠️ Could not expand details: {e}")
                
                # Get page content
                body_text = await page.locator('body').inner_text()
                await browser.close()
                
                # Extract prices using regex
                # Grundpreis: "Grundpreis 16,01 €"
                grundpreis_match = re.search(r'Grundpreis[^\d]*?(\d+[,.]?\d*)\s*€', body_text, re.IGNORECASE)
                
                # Arbeitspreis pro kWh (dynamisch): "Arbeitspreis pro kWh (dynamisch) 26,96 ct/kWh"
                # This appears after clicking "Mehr Details"
                arbeitspreis_kwh_match = re.search(r'Arbeitspreis pro kWh[^\d]*?(\d+[,.]?\d*)\s*(ct|Cent)', body_text, re.IGNORECASE)
                
                # Alternative: Monthly tariff price
                # "monatlich dynamischem Verbrauchspreis (November : 30,87 ct/kWh)"
                monthly_tariff_match = re.search(r'Verbrauchspreis[^\d]*?(\d+[,.]?\d*)\s*ct/kWh', body_text, re.IGNORECASE)
                
                # Total monthly Arbeitspreis: "Arbeitspreis 93,27 €"
                arbeitspreis_total_match = re.search(r'Arbeitspreis\s*(\d+[,.]?\d*)\s*€', body_text, re.IGNORECASE)
                
                # WICHTIG: Netznutzung, Umlagen, Steuern und weitere Beschaffungskosten
                # z.B. "Netznutzung, Umlagen, Steuern und weitere Beschaffungskosten 64,67 €"
                network_fees_match = re.search(r'Netznutzung[^€]*?(\d+[,.]?\d*)\s*€', body_text, re.IGNORECASE)
                
                base_price = None
                kwh_price_ct = None
                monthly_arbeitspreis = None
                network_fees_euro = None
                
                if grundpreis_match:
                    base_price = float(grundpreis_match.group(1).replace(',', '.'))
                    logger.info(f"✅ Found Grundpreis: {base_price} €/Monat")
                
                if arbeitspreis_kwh_match:
                    kwh_price_ct = float(arbeitspreis_kwh_match.group(1).replace(',', '.'))
                    logger.info(f"✅ Found Arbeitspreis pro kWh: {kwh_price_ct} ct/kWh")
                elif monthly_tariff_match:
                    # Fallback to monthly tariff price
                    kwh_price_ct = float(monthly_tariff_match.group(1).replace(',', '.'))
                    logger.info(f"✅ Found Monthly tariff price: {kwh_price_ct} ct/kWh")
                
                if arbeitspreis_total_match:
                    monthly_arbeitspreis = float(arbeitspreis_total_match.group(1).replace(',', '.'))
                    logger.info(f"✅ Found monthly Arbeitspreis: {monthly_arbeitspreis} €")
                
                if network_fees_match:
                    network_fees_euro = float(network_fees_match.group(1).replace(',', '.'))
                    logger.info(f"✅ Found Netznutzung/Umlagen/Steuern: {network_fees_euro} €")
                
                if base_price is not None and kwh_price_ct is not None:
                    # Berechnung des Markup (Netznutzung, Steuern, Umlagen):
                    # Die 64,67 € (network_fees_euro) müssen durch monatliche kWh geteilt werden
                    monthly_kwh = annual_consumption / 12
                    
                    if network_fees_euro is not None and monthly_kwh > 0:
                        # Markup ct/kWh = (Netznutzung € / monatliche kWh) * 100
                        markup_ct_kwh = (network_fees_euro / monthly_kwh) * 100
                        logger.info(f"📊 Markup berechnet: {network_fees_euro}€ / {monthly_kwh:.2f} kWh = {markup_ct_kwh:.2f} ct/kWh")
                    else:
                        # Fallback: assume ~18 ct/kWh is markup (typical for Tado)
                        markup_ct_kwh = 18.0
                        logger.warning(f"⚠️ Network fees not found, using fallback markup: {markup_ct_kwh} ct/kWh")
                    
                    monthly_cost = base_price + (monthly_kwh * (kwh_price_ct / 100))
                    
                    return {
                        'provider': 'Tado Energy',
                        'tariff_name': 'Tado Hourly',
                        'base_price_monthly': base_price,
                        'kwh_price_ct': kwh_price_ct,  # Total price (including current exchange)
                        'markup_ct_kwh': markup_ct_kwh,  # Only the markup portion (Netz + Steuern + Umlagen)
                        'network_fees_euro': network_fees_euro,  # Raw network fees in €
                        'monthly_arbeitspreis': monthly_arbeitspreis,  # From website calculation
                        'monthly_cost_estimated': round(monthly_cost, 2),
                        'annual_cost_estimated': round(monthly_cost * 12, 2),
                        'zip_code': zip_code,
                        'annual_consumption_kwh': annual_consumption,
                        'data_source': 'playwright_scraping',
                        'scraped_at': datetime.now().isoformat(),
                        'url': tariff_url
                    }
                
                logger.warning("⚠️ Playwright loaded page but couldn't extract complete prices")
                return None
                
        except Exception as e:
            logger.error(f"❌ Playwright scraping failed: {e}")
            return None
    
    def _get_fallback_prices(self, zip_code: str, annual_consumption: int) -> Dict:
        """
        Get fallback prices based on typical Tado pricing
        
        Args:
            zip_code: German postal code (PLZ)
            annual_consumption: Annual consumption in kWh
            
        Returns:
            Dict with estimated tariff data
        """
        # Tado typically has consistent pricing across Germany
        # Based on observed data from Nov 2024
        base_price = 16.01  # €/Monat
        kwh_price_ct = 28.0  # ct/kWh (estimated average)
        
        monthly_kwh_cost = (annual_consumption / 12) * (kwh_price_ct / 100)
        monthly_cost = base_price + monthly_kwh_cost
        
        logger.info("📊 Using fallback Tado pricing estimates")
        logger.info(f"   Grundpreis: {base_price} €/Monat")
        logger.info(f"   Arbeitspreis: {kwh_price_ct} ct/kWh (estimated)")
        
        return {
            'provider': 'Tado Energy',
            'tariff_name': 'Tado Hourly',
            'base_price_monthly': base_price,
            'kwh_price_ct': kwh_price_ct,
            'monthly_cost_estimated': round(monthly_cost, 2),
            'annual_cost_estimated': round(monthly_cost * 12, 2),
            'zip_code': zip_code,
            'annual_consumption_kwh': annual_consumption,
            'data_source': 'fallback_estimate',
            'scraped_at': datetime.now().isoformat(),
            'url': self.BASE_URL
        }
    
    async def scrape_tariff(self, zip_code: str, annual_consumption: int) -> Dict:
        """
        Main scraping method with fallback
        
        Args:
            zip_code: German postal code (5 digits)
            annual_consumption: Annual consumption in kWh
            
        Returns:
            Dict with tariff data (either scraped or fallback)
        """
        logger.info(f"🔍 Starting Tado price lookup for PLZ {zip_code}")
        
        # Try Playwright scraping first
        logger.info("🔧 Starting Playwright scraping")
        result = await self._scrape_with_playwright(zip_code, annual_consumption)
        
        if result:
            return result
        
        # Fallback to estimates
        logger.info("⚠️ Playwright scraping failed, using fallback data")
        return self._get_fallback_prices(zip_code, annual_consumption)


async def scrape_tado_tariff(zip_code: str, annual_consumption: int) -> Dict:
    """
    Convenience function to scrape Tado tariff
    
    Args:
        zip_code: German postal code (5 digits, e.g., "68167")
        annual_consumption: Annual consumption in kWh (e.g., 4150)
        
    Returns:
        Dict with tariff data
        
    Example:
        >>> result = await scrape_tado_tariff("68167", 4150)
        >>> print(f"{result['base_price_monthly']} €/Mon, {result['kwh_price_ct']} ct/kWh")
    """
    scraper = TadoScraper()
    return await scraper.scrape_tariff(zip_code, annual_consumption)


if __name__ == "__main__":
    # Test the scraper
    async def test():
        result = await scrape_tado_tariff("68167", 4150)
        print("\n✅ Tado Scraping Result:")
        print(f"   Grundpreis: {result.get('base_price_monthly')} €/Monat")
        print(f"   Arbeitspreis: {result.get('kwh_price_ct')} ct/kWh")
        print(f"   Monthly Arbeitspreis (Website): {result.get('monthly_arbeitspreis')} €")
        print(f"   Estimated monthly cost: {result.get('monthly_cost_estimated')} €")
        print(f"   Quelle: {result.get('data_source')}")
    
    asyncio.run(test())
