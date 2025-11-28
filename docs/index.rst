Project Energy Tariffs
======================

Energy tariff analysis and forecasting system.

This project provides tools for energy price analysis, load forecasting, risk analysis, and tariff comparison
for German electricity markets.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   concept
   api
   tariff_models
   risk_analysis
   webscraping
   price_forecasting
   usage_forecasting

Features
--------

* Real-time energy price tracking
* Advanced forecasting models (Prophet)
* Risk assessment for different tariff structures
* Interactive web interface
* Automated web scraping for multiple energy providers
* Day-ahead price predictions
* Household energy usage forecasting

Modules
-------

System Concept
^^^^^^^^^^^^^^

Complete explanation of the system architecture and workflow.

:doc:`concept`
   End-to-end explanation of the tariff analysis pipeline from data collection
   to personalized recommendations. Includes detailed workflow diagrams and real-world examples.

REST API
^^^^^^^^

FastAPI backend endpoints for tariff comparison and analysis.

:doc:`api`
   HTTP endpoints for tariff calculations, risk analysis, and web scraping integration.

Tariff Models
^^^^^^^^^^^^^

Core tariff calculation models for fixed and dynamic pricing.

:doc:`tariff_models`
   FixedTariff and DynamicTariff classes with cost calculation methods.

Risk Analysis
^^^^^^^^^^^^^

Risk assessment for dynamic tariff suitability.

:doc:`risk_analysis`
   Consumption pattern analysis, price correlation, and aggregated risk scoring.

Web Scraping
^^^^^^^^^^^^

Automated data collection from German energy providers.

:doc:`webscraping`
   Scraper modules for Tibber, EnBW, Tado and other providers.
   Includes PLZ-based pricing and async support.

Price Forecasting
^^^^^^^^^^^^^^^^^

Day-ahead electricity price predictions.

:doc:`price_forecasting`
   Prophet model for energy price forecasting using SMARD data.
   Includes wholesale to retail price conversion.

Usage Forecasting
^^^^^^^^^^^^^^^^^

Household electricity consumption predictions.

:doc:`usage_forecasting`
   Prophet model for consumption forecasting based on smart meter data.
   Includes backtesting and validation metrics.

Quick Start
-----------

Installation
^^^^^^^^^^^^

.. code-block:: bash

   # Clone repository
   git clone https://github.com/JuliusBec/Project_Energy_Tariffs.git
   cd Project_Energy_Tariffs

   # Install dependencies
   pip install -r requirements.txt

   # Install Playwright browsers
   playwright install chromium

Running the Application
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Start the web application
   python app.py

   # Or use Docker
   docker build -t energy-tariffs .
   docker run -p 5000:5000 energy-tariffs

Example Usage
^^^^^^^^^^^^^

Web Scraping
""""""""""""

.. code-block:: python

   from src.webscraping.scraper_tibber import TibberScraper
   import asyncio

   async def get_prices():
       scraper = TibberScraper()
       prices = await scraper.get_prices(postal_code="69117")
       print(prices)

   asyncio.run(get_prices())

Usage Forecasting
"""""""""""""""""

.. code-block:: python

   from src.backend.forecasting.energy_usage_forecast import forecast_prophet
   import pandas as pd

   df = pd.read_csv('app_data/example_smart_meter.csv')
   forecast = forecast_prophet(df, days=30)
   print(forecast[['ds', 'yhat']].head())

Project Structure
-----------------

.. code-block:: text

   Project_Energy_Tariffs/
   ├── src/
   │   ├── main.py
   │   ├── backend/
   │   │   ├── app.py
   │   │   ├── energy_tariff.py
   │   │   ├── risk_analysis.py
   │   │   └── forecasting/
   │   │       ├── energy_price_forecast.py
   │   │       └── energy_usage_forecast.py
   │   ├── frontend/
   │   │   ├── src/
   │   │   ├── index.html
   │   │   ├── package.json
   │   │   └── vite.config.js
   │   └── webscraping/
   │       ├── scraper_tibber.py
   │       ├── scraper_enbw.py
   │       ├── scraper_enbw_strom.py
   │       └── scraper_tado.py
   ├── app_data/
   ├── docs/
   └── requirements.txt


License
-------

This project is licensed under the terms specified in the LICENSE file.

Support
-------

For questions and support:

* GitHub Issues: https://github.com/JuliusBec/Project_Energy_Tariffs/issues
* Documentation: https://project-energy-tariffs.readthedocs.io/

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

