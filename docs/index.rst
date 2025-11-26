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
   webscraping
   forecasting

Features
--------

* Real-time energy price tracking
* Advanced forecasting models (Prophet & Chronos)
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

API Documentation
^^^^^^^^^^^^^^^^^

Complete API reference for the backend energy tariff system.

:doc:`api`
   Core tariff calculation, risk analysis, and backend services.

Web Scraping
^^^^^^^^^^^^

Automated data collection from German energy providers.

:doc:`webscraping`
   Scraper modules for Tibber, EnBW, Tado and other providers.
   Includes PLZ-based pricing and async support.

Forecasting & Predictions
^^^^^^^^^^^^^^^^^^^^^^^^^^

Machine learning models for price and usage predictions.

:doc:`forecasting`
   Prophet and Chronos models for energy price and consumption forecasting.
   Includes SMARD integration and time series analysis.

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

Forecasting
"""""""""""

.. code-block:: python

   from src.backend.forecasting.energy_usage_forecast import forecast_prophet
   import pandas as pd

   df = pd.read_csv('app_data/example_smart_meter.csv')
   forecast = forecast_prophet(df, days=30)
   print(forecast[['datetime', 'yhat']].head())

Project Structure
-----------------

.. code-block:: text

   Project_Energy_Tariffs/
   ├── src/
   │   ├── backend/
   │   │   ├── energy_tariff.py
   │   │   ├── risk_analysis.py
   │   │   └── forecasting/
   │   │       ├── energy_price_forecast.py
   │   │       └── energy_usage_forecast.py
   │   ├── frontend/
   │   │   └── src/
   │   └── webscraping/
   │       ├── scraper_tibber.py
   │       ├── scraper_enbw.py
   │       └── scraper_tado.py
   ├── app_data/
   ├── docs/
   ├── app.py
   └── requirements.txt

Contributing
------------

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Update documentation
5. Submit a pull request

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

