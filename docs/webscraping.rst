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

Performance Optimization
------------------------

1. **Browser Reuse**: Reuse browser instances
2. **Parallel Scraping**: Use asyncio.gather for multiple postal codes
3. **Selective Scraping**: Scrape only required fields
4. **Headless Mode**: Enable headless for better performance

.. code-block:: python

   # Browser reuse
   async with async_playwright() as p:
       browser = await p.chromium.launch(headless=True)
       
       # Multiple pages in parallel
       tasks = [scrape_page(browser, plz) for plz in postal_codes]
       results = await asyncio.gather(*tasks)
       
       await browser.close()
