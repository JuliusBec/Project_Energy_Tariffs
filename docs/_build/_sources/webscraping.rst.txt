Web Scraping Module
===================

The web scraping module contains specialized scrapers for various German energy providers.
All scrapers use Playwright for JavaScript rendering and support postal code-based tariff queries.

Overview
--------

The module provides automated scrapers for:

* **Tibber** - Dynamic electricity tariff
* **EnBW** - Dynamic electricity tariff
* **EnBW Strom** - Additional EnBW tariffs
* **Tado** - Smart home energy management

All scrapers deliver structured tariff data including:

- Base price (€/month)
- Energy price (ct/kWh)
- Regional price differences (postal code-based)
- Additional tariff features
- Provider-specific information
- Contract details and minimum duration
- Green energy status

Architecture
------------

The scrapers follow a consistent architecture:

1. **Input Validation**: Postal code and consumption validation
2. **Browser Automation**: Playwright-based navigation and JavaScript execution
3. **Data Extraction**: CSS selectors and XPath queries
4. **Fallback Strategy**: Regional averages when live scraping fails
5. **Data Normalization**: Consistent output format across all scrapers

.. code-block:: text

   ┌─────────────┐
   │   Input     │ → Postal Code, Consumption
   └──────┬──────┘
          ↓
   ┌─────────────┐
   │ Validation  │ → Check format and ranges
   └──────┬──────┘
          ↓
   ┌─────────────┐
   │  Playwright │ → Launch browser, navigate
   └──────┬──────┘
          ↓
   ┌─────────────┐
   │  Scraping   │ → Extract price data
   └──────┬──────┘
          ↓
   ┌─────────────┐
   │  Fallback?  │ → Use regional data if needed
   └──────┬──────┘
          ↓
   ┌─────────────┐
   │   Output    │ → Normalized tariff dict
   └─────────────┘

Tibber Scraper
--------------

.. automodule:: webscraping.scraper_tibber
   :members:
   :undoc-members:
   :show-inheritance:

Example Usage
^^^^^^^^^^^^^

.. code-block:: python

   from src.webscraping.scraper_tibber import TibberScraper
   import asyncio

   async def get_tibber_prices():
       scraper = TibberScraper()
       prices = await scraper.get_prices(postal_code="69117")
       print(f"Base price: {prices['base_price_monthly']}€")
       print(f"Energy price: {prices['kwh_price_additional']}ct/kWh")

   asyncio.run(get_tibber_prices())

Features
^^^^^^^^

* Automatic postal code validation
* Fallback to regional average prices
* Async/Await support
* Playwright browser automation

EnBW Scraper
------------

.. automodule:: webscraping.scraper_enbw
   :members:
   :undoc-members:
   :show-inheritance:

Example Usage
^^^^^^^^^^^^^

.. code-block:: python

   from src.webscraping.scraper_enbw import EnbwScraper
   import asyncio

   async def get_enbw_prices():
       scraper = EnbwScraper()
       prices = await scraper.get_prices(
           postal_code="76131",
           annual_consumption=3500
       )
       print(f"Markup: {prices['markup_ct_kwh']}ct/kWh")
       print(f"Total price: {prices['total_price_ct_kwh']}ct/kWh")

   asyncio.run(get_enbw_prices())

Features
^^^^^^^^

* Dynamic exchange prices
* Markup calculation
* Consumption-dependent prices
* Headless browser mode

EnBW Strom Scraper
------------------

.. automodule:: webscraping.scraper_enbw_strom
   :members:
   :undoc-members:
   :show-inheritance:

Tado Scraper
------------

.. automodule:: webscraping.scraper_tado
   :members:
   :undoc-members:
   :show-inheritance:

Installation
------------

Prerequisites
^^^^^^^^^^^^^

.. code-block:: bash

   # Install Playwright
   pip install playwright
   
   # Install browser binaries
   playwright install chromium

Dependencies
^^^^^^^^^^^^

* Python 3.9+
* Playwright >= 1.40.0
* asyncio
* logging

Configuration
-------------

Scraper settings can be controlled via environment variables:

.. code-block:: bash

   # Timeout for browser operations (seconds)
   export SCRAPER_TIMEOUT=30000
   
   # Enable headless mode
   export HEADLESS=true
   
   # Set log level
   export LOG_LEVEL=INFO

Best Practices
--------------

1. **Rate Limiting**: Implement delays between requests
2. **Error Handling**: Use built-in fallback mechanisms
3. **Async Operations**: Use async/await for parallel scraping tasks
4. **Postal Code Validation**: Verify postal code formats before scraping

Error Handling
--------------

All scrapers use structured logging and fallback strategies:

.. code-block:: python

   import logging
   
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)
   
   try:
       prices = await scraper.get_prices(postal_code="12345")
   except Exception as e:
       logger.error(f"Scraping failed: {e}")
       # Fallback to stored prices

Regional Price Differences
--------------------------

All scrapers support postal code-based price queries for all of Germany.
The first two digits of the postal code determine the region:

* 01-09: East Germany
* 10-19: Berlin/Brandenburg
* 20-29: North Germany
* 30-39: Lower Saxony
* 40-59: North Rhine-Westphalia
* 60-69: Hesse/Rhineland-Palatinate
* 70-79: Baden-Württemberg
* 80-89: Bavaria
* 90-99: Bavaria/Thuringia

API Reference
-------------

TibberScraper
^^^^^^^^^^^^^

.. autoclass:: webscraping.scraper_tibber.TibberScraper
   :members:
   :special-members: __init__

EnbwScraper
^^^^^^^^^^^

.. autoclass:: webscraping.scraper_enbw.EnbwScraper
   :members:
   :special-members: __init__

Advanced Usage
--------------

Batch Processing
^^^^^^^^^^^^^^^^

.. code-block:: python

   import asyncio
   from src.webscraping.scraper_tibber import TibberScraper
   from src.webscraping.scraper_enbw import EnbwScraper

   async def compare_providers(postal_code: str):
       tibber = TibberScraper()
       enbw = EnbwScraper()
       
       # Parallel scraping
       results = await asyncio.gather(
           tibber.get_prices(postal_code=postal_code),
           enbw.get_prices(postal_code=postal_code, annual_consumption=3500)
       )
       
       return {
           'tibber': results[0],
           'enbw': results[1]
       }

   prices = asyncio.run(compare_providers("69117"))

Caching
^^^^^^^

Implement caching for frequent queries:

.. code-block:: python

   from functools import lru_cache
   from datetime import datetime, timedelta

   class CachedScraper:
       def __init__(self):
           self.cache = {}
           self.cache_duration = timedelta(hours=1)
       
       async def get_prices_cached(self, postal_code):
           cache_key = f"{postal_code}_{datetime.now().hour}"
           
           if cache_key in self.cache:
               return self.cache[cache_key]
           
           scraper = TibberScraper()
           prices = await scraper.get_prices(postal_code=postal_code)
           self.cache[cache_key] = prices
           
           return prices

Troubleshooting
---------------

Common Issues
^^^^^^^^^^^^^

**Problem: "Playwright not installed"**

.. code-block:: bash

   playwright install chromium

**Problem: Timeout errors**

Increase the timeout in scraper settings:

.. code-block:: python

   scraper = TibberScraper()
   scraper.timeout = 60000  # 60 seconds

**Problem: No prices found**

Check postal code validation and use fallback data:

.. code-block:: python

   if not prices:
       logger.warning("No live prices, using fallback")
       prices = scraper.get_fallback_prices(postal_code)

**Problem: Website structure changed**

Websites change frequently. Update selectors:

.. code-block:: python

   # Check current selectors
   await page.screenshot(path='debug.png')
   html = await page.content()
   with open('debug.html', 'w') as f:
       f.write(html)
   
   # Find new selectors using browser DevTools

**Problem: Rate limiting / IP blocked**

Implement delays and rotate user agents:

.. code-block:: python

   import random
   import asyncio
   
   user_agents = [
       'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
       'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...'
   ]
   
   async def scrape_with_delay(postal_codes):
       for plz in postal_codes:
           await asyncio.sleep(random.uniform(2, 5))  # Random delay
           scraper = TibberScraper()
           scraper.user_agent = random.choice(user_agents)
           prices = await scraper.get_prices(postal_code=plz)

**Problem: Memory leaks with long-running scrapers**

.. code-block:: python

   # Properly close browser contexts
   async def scrape_batch(postal_codes):
       async with async_playwright() as p:
           browser = await p.chromium.launch()
           
           for plz in postal_codes:
               context = await browser.new_context()
               page = await context.new_page()
               
               try:
                   # Scraping logic
                   pass
               finally:
                   await context.close()  # Important!
           
           await browser.close()

Performance Optimization
------------------------

1. **Browser Reuse**: Reuse browser instances
2. **Parallel Scraping**: Use asyncio.gather for multiple postal codes
3. **Selective Scraping**: Scrape only required fields
4. **Headless Mode**: Enable headless for better performance
5. **Connection Pooling**: Reuse network connections
6. **Resource Blocking**: Block unnecessary resources (images, fonts)

.. code-block:: python

   # Browser reuse with resource blocking
   async with async_playwright() as p:
       browser = await p.chromium.launch(
           headless=True,
           args=['--disable-gpu', '--no-sandbox']
       )
       
       context = await browser.new_context(
           user_agent='Mozilla/5.0...',
           viewport={'width': 1920, 'height': 1080}
       )
       
       # Block images and fonts for faster loading
       await context.route('**/*.{png,jpg,jpeg,gif,svg,woff,woff2}', 
                          lambda route: route.abort())
       
       # Multiple pages in parallel
       tasks = [scrape_page(context, plz) for plz in postal_codes]
       results = await asyncio.gather(*tasks)
       
       await browser.close()

Testing & Monitoring
--------------------

Unit Tests
^^^^^^^^^^

.. code-block:: python

   import pytest
   from src.webscraping.scraper_tibber import TibberScraper
   
   @pytest.mark.asyncio
   async def test_tibber_scraper():
       scraper = TibberScraper()
       prices = await scraper.get_prices(postal_code="69117")
       
       assert prices is not None
       assert 'base_price_monthly' in prices
       assert prices['base_price_monthly'] > 0
       assert prices['kwh_price_additional'] > 0
   
   @pytest.mark.asyncio
   async def test_invalid_postal_code():
       scraper = TibberScraper()
       with pytest.raises(ValueError):
           await scraper.get_prices(postal_code="99999")

Integration Tests
^^^^^^^^^^^^^^^^^

.. code-block:: python

   @pytest.mark.asyncio
   @pytest.mark.integration
   async def test_all_scrapers():
       postal_code = "69117"
       
       tibber = TibberScraper()
       enbw = EnbwScraper()
       
       results = await asyncio.gather(
           tibber.get_prices(postal_code=postal_code),
           enbw.get_prices(postal_code=postal_code, annual_consumption=3500),
           return_exceptions=True
       )
       
       # At least one scraper should succeed
       successful = [r for r in results if not isinstance(r, Exception)]
       assert len(successful) > 0

Monitoring
^^^^^^^^^^

.. code-block:: python

   import time
   from datetime import datetime
   
   class MonitoredScraper:
       def __init__(self):
           self.metrics = {
               'requests': 0,
               'successes': 0,
               'failures': 0,
               'avg_duration': 0
           }
       
       async def scrape_with_monitoring(self, postal_code):
           start = time.time()
           self.metrics['requests'] += 1
           
           try:
               scraper = TibberScraper()
               prices = await scraper.get_prices(postal_code=postal_code)
               self.metrics['successes'] += 1
               return prices
           except Exception as e:
               self.metrics['failures'] += 1
               logger.error(f"Scraping failed: {e}")
               raise
           finally:
               duration = time.time() - start
               self.metrics['avg_duration'] = (
                   (self.metrics['avg_duration'] * (self.metrics['requests'] - 1) + duration) 
                   / self.metrics['requests']
               )
               
               logger.info(f"Scraping metrics: {self.metrics}")

Data Validation
---------------

Validate Scraped Data
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from typing import Dict, Any
   
   def validate_tariff_data(data: Dict[str, Any]) -> bool:
       """Validate scraped tariff data for consistency"""
       required_fields = [
           'base_price_monthly',
           'kwh_price_additional',
           'provider',
           'postal_code'
       ]
       
       # Check required fields
       if not all(field in data for field in required_fields):
           return False
       
       # Validate price ranges (reasonable bounds)
       if not (0 < data['base_price_monthly'] < 50):
           logger.warning(f"Unusual base price: {data['base_price_monthly']}")
           return False
       
       if not (5 < data['kwh_price_additional'] < 50):
           logger.warning(f"Unusual kWh price: {data['kwh_price_additional']}")
           return False
       
       # Validate postal code format
       if not (isinstance(data['postal_code'], str) and len(data['postal_code']) == 5):
           return False
       
       return True
   
   # Usage
   prices = await scraper.get_prices(postal_code="69117")
   if validate_tariff_data(prices):
       # Process valid data
       pass
   else:
       # Use fallback or retry
       logger.error("Invalid tariff data received")
