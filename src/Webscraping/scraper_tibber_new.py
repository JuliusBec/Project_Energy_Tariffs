"""
Tibber Scraper - Vereinfachte Version mit requests-html
"""

import logging
import time
from typing import Dict, Optional
import re
from requests_html import HTMLSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TibberScraper:
    """Scraper for Tibber electricity prices using requests-html"""
    
    def __init__(self):
        self.session = None
    
    def scrape_tariff(self, plz: str, kwh_year: int) -> Dict:
        """
        Scrape Tibber tariff for given postal code and consumption
        
        Args:
            plz: Postal code
            kwh_year: Annual consumption in kWh
            
        Returns:
            Dictionary with price data
        """
        logger.info(f"Scraping Tibber for PLZ {plz}, {kwh_year} kWh/Jahr")
        
        # Try scraping with requests-html
        result = self._scrape_with_requests_html(plz, kwh_year)
        
        if result:
            return {
                'success': True,
                'data_source': 'requests_html_scraping',
                'total_base_monthly': result['base_price'],
                'additional_price_ct': result['work_price'],
                'markup_ct_kwh': result['work_price'],
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        
        # Fallback to regional estimation
        logger.warning(f"Scraping failed for PLZ {plz}, using regional fallback")
        return self._get_fallback_prices(plz, kwh_year)
    
    def _scrape_with_requests_html(self, plz: str, kwh_year: int) -> Optional[Dict]:
        """
        Scrape using requests-html (renders JavaScript without full browser)
        
        Returns:
            Dict with 'base_price' and 'work_price' or None
        """
        try:
            logger.info("Starting requests-html scraping...")
            
            self.session = HTMLSession()
            url = f'https://tibber.com/de/preisrechner?postalCode={plz}&averageConsumption={kwh_year}'
            
            # Fetch page
            logger.info(f"Fetching {url}")
            r = self.session.get(url, timeout=15)
            
            # Render JavaScript (downloads Chromium on first run)
            logger.info("Rendering JavaScript...")
            r.html.render(timeout=25, sleep=5)
            
            # Extract text from rendered page
            page_text = r.html.text
            logger.info(f"Got {len(page_text)} characters of rendered text")
            
            # Search for prices using regex patterns
            base_price_patterns = [
                r'Grundpreis.*?(\d{1,3}[,.]?\d{0,2})\s*€',
                r'(\d{1,3}[,.]?\d{0,2})\s*€\s*/?\s*Monat',
                r'monatlich.*?(\d{1,3}[,.]?\d{0,2})\s*€',
            ]
            
            work_price_patterns = [
                r'(\d{1,2}[,.]?\d{0,2})\s*ct\s*/\s*kWh',
                r'Arbeitspreis.*?(\d{1,2}[,.]?\d{0,2})',
                r'(\d{1,2}[,.]?\d{0,2})\s*Cent\s*/\s*kWh',
            ]
            
            base_price = None
            work_price = None
            
            # Try to find base price
            for pattern in base_price_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    base_price = float(match.group(1).replace(',', '.'))
                    logger.info(f"Found Grundpreis: {base_price} €/Monat")
                    break
            
            # Try to find work price
            for pattern in work_price_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    work_price = float(match.group(1).replace(',', '.'))
                    logger.info(f"Found Arbeitspreis: {work_price} ct/kWh")
                    break
            
            # Validate prices are realistic
            if base_price and work_price:
                if 5 <= base_price <= 50 and 5 <= work_price <= 30:
                    logger.info(f"✅ Scraping successful: {base_price}€/Mon + {work_price}ct/kWh")
                    return {
                        'base_price': base_price,
                        'work_price': work_price
                    }
                else:
                    logger.warning(f"Prices seem unrealistic: {base_price}€, {work_price}ct/kWh")
            else:
                logger.warning("Could not find both prices in rendered page")
            
            return None
            
        except Exception as e:
            logger.error(f"requests-html scraping failed: {str(e)}")
            return None
        finally:
            if self.session:
                try:
                    self.session.close()
                    self.session = None
                except:
                    pass
    
    def _get_fallback_prices(self, plz: str, kwh_year: int) -> Dict:
        """
        Fallback: Return regional average prices based on PLZ
        """
        plz_prefix = plz[:2]
        
        # Regional prices based on Tibber's typical pricing structure
        # Grundpreis (€/Monat) + Arbeitspreis (ct/kWh)
        regional_data = {
            '01': (12.50, 16.50),  # Dresden, Sachsen
            '04': (12.50, 16.50),  # Leipzig, Sachsen
            '06': (12.50, 16.50),  # Halle, Sachsen-Anhalt
            '10': (15.50, 17.00),  # Berlin
            '12': (15.50, 17.00),  # Berlin
            '13': (15.50, 17.00),  # Berlin
            '14': (15.50, 17.00),  # Potsdam, Brandenburg
            '20': (14.50, 16.50),  # Hamburg
            '22': (14.50, 16.50),  # Hamburg
            '28': (14.00, 16.00),  # Bremen
            '30': (14.50, 16.50),  # Hannover, Niedersachsen
            '40': (14.50, 16.50),  # Düsseldorf, NRW
            '44': (14.50, 16.50),  # Dortmund, NRW
            '50': (14.50, 16.50),  # Köln, NRW
            '60': (15.00, 16.80),  # Frankfurt, Hessen
            '68': (16.09, 15.25),  # Mannheim, Baden-Württemberg
            '69': (15.50, 15.80),  # Heidelberg, Baden-Württemberg
            '70': (15.50, 15.80),  # Stuttgart, Baden-Württemberg
            '80': (15.80, 16.20),  # München, Bayern
            '90': (15.00, 15.80),  # Nürnberg, Bayern
        }
        
        base_price, work_price = regional_data.get(plz_prefix, (14.50, 16.00))
        
        logger.info(f"Using fallback for PLZ {plz}: {base_price}€/Mon + {work_price}ct/kWh")
        
        return {
            'success': True,
            'data_source': 'regional_fallback',
            'total_base_monthly': base_price,
            'additional_price_ct': work_price,
            'markup_ct_kwh': work_price,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        }


if __name__ == "__main__":
    # Test scraper
    scraper = TibberScraper()
    
    test_cases = [
        ('68167', 3500),  # Mannheim
        ('10115', 3500),  # Berlin
        ('80331', 3500),  # München
    ]
    
    for plz, kwh in test_cases:
        print(f"\n=== Testing PLZ {plz}, {kwh} kWh/Jahr ===")
        result = scraper.scrape_tariff(plz, kwh)
        print(f"Result: {result}")
