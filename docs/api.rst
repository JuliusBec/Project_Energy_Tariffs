REST API
========

FastAPI backend providing HTTP endpoints for tariff comparison, consumption forecasting, risk analysis, and web scraping integration.

Overview
--------

The DYNERGY API (``backend.app``) exposes RESTful endpoints for:

* Tariff cost calculations (fixed and dynamic)
* Consumption data upload and forecasting
* Risk analysis for dynamic tariff suitability
* Web scraping integration for live tariff data
* Day-ahead price forecasts

**Base URL:** ``http://localhost:8000``

**CORS:** Enabled for ``localhost:3000``, ``localhost:5173`` (Vite)

Core Endpoints
--------------

GET /api/tariffs
^^^^^^^^^^^^^^^^

List available energy tariffs.

**Response:**

.. code-block:: json

   {
     "tariffs": [
       {
         "id": "enbw-komfort",
         "name": "EnBW Komfort",
         "provider": "EnBW",
         "base_price": 15.90,
         "kwh_rate": 0.3599,
         "is_dynamic": false,
         "features": ["green", "fixed"]
       }
     ]
   }

POST /api/compare-tariffs-with-csv
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Compare tariffs using uploaded smart meter CSV data.

**Request:**

- Content-Type: ``multipart/form-data``
- Body:
  - ``file``: CSV file with columns [datetime, value, status]
  - ``zip_code``: German postal code (optional)

**Example:**

.. code-block:: bash

   curl -X POST http://localhost:8000/api/compare-tariffs-with-csv \
     -F "file=@smart_meter.csv" \
     -F "zip_code=70173"

**Response:**

.. code-block:: json

   {
     "results": [
       {
         "tariff_name": "Tibber",
         "monthly_cost": 89.45,
         "annual_cost": 1073.40,
         "tariff_type": "dynamic",
         "avg_kwh_price": 0.2634
       },
       {
         "tariff_name": "EnBW Komfort",
         "monthly_cost": 95.00,
         "annual_cost": 1140.00,
         "tariff_type": "fixed",
         "avg_kwh_price": 0.3599
       }
     ]
   }

POST /api/calculate-yearly-usage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extract annual consumption from uploaded CSV.

**Request:**

- Content-Type: ``multipart/form-data``
- Body: ``file``: CSV file

**Response:**

.. code-block:: json

   {
     "annual_kwh": 3456.78,
     "data_period_days": 365,
     "avg_daily_kwh": 9.47
   }

POST /api/risk-analysis
^^^^^^^^^^^^^^^^^^^^^^^

Analyze consumption patterns vs market prices.

**Request:**

- Content-Type: ``multipart/form-data``
- Body:
  - ``file``: CSV file
  - ``days``: Analysis period (default: 30)

**Response:**

.. code-block:: json

   {
     "market_avg_price": 0.0850,
     "user_weighted_price": 0.0790,
     "price_differential_pct": -7.06,
     "risk_exposure": "favorable",
     "risk_message": "User consumed more during low-price periods",
     "total_consumption": 245.67,
     "price_volatility": 0.0234
   }

POST /api/risk-score
^^^^^^^^^^^^^^^^^^^^

Calculate aggregated risk score for dynamic tariffs.

**Request:**

.. code-block:: json

   {
     "file": "<multipart/form-data>",
     "days": 30,
     "is_dynamic": true
   }

**Response:**

.. code-block:: json

   {
     "risk_level": "low",
     "risk_score": 28,
     "risk_message": "Low risk: Your consumption profile suits dynamic tariffs",
     "risk_factors": [
       {
         "factor": "Historischer Verbrauch",
         "impact": "positive",
         "detail": "7.1% unter Marktdurchschnitt"
       },
       {
         "factor": "Verbrauchstiming",
         "impact": "positive",
         "detail": "Vermeidet teure Stunden"
       }
     ]
   }

POST /api/backtest-data
^^^^^^^^^^^^^^^^^^^^^^^

Validate Prophet forecast accuracy using hold-out test period.

**Request:**

- Content-Type: ``multipart/form-data``
- Body: ``file``: CSV file with consumption history

**Response:**

.. code-block:: json

   {
     "metrics": {
       "mae": 0.14,
       "mse": 0.03,
       "forecast_error_percentage": 8.5,
       "total_forecast_usage": 245.6,
       "total_actual_usage": 266.3
     },
     "daily_data": {
       "timestamps": ["2024-12-01", "2024-12-02", ...],
       "forecast": [8.2, 7.9, ...],
       "actual": [8.5, 8.1, ...]
     }
   }

GET /api/price-chart-data
^^^^^^^^^^^^^^^^^^^^^^^^^

Retrieve day-ahead price forecasts for visualization.

**Response:**

.. code-block:: json

   {
     "historical_data": {
       "timestamps": ["2024-11-01", ...],
       "prices": [85.32, 78.45, ...]
     },
     "forecast_data": {
       "timestamps": ["2024-12-01", ...],
       "prices": [90.15, ...],
       "lower_bound": [75.20, ...],
       "upper_bound": [105.10, ...]
     },
     "metrics": {
       "avg_forecast_price": 89.45,
       "price_change_percentage": 5.2
     }
   }

Scraper Endpoints
-----------------

POST /api/scrape/tibber
^^^^^^^^^^^^^^^^^^^^^^^

Fetch current Tibber pricing.

**Request:**

.. code-block:: json

   {
     "postal_code": "70173"
   }

**Response:**

.. code-block:: json

   {
     "base_price_monthly": 14.99,
     "kwh_price_additional": 15.50,
     "provider": "Tibber",
     "is_dynamic": true
   }

POST /api/scrape/enbw
^^^^^^^^^^^^^^^^^^^^^

Fetch EnBW dynamic tariff data.

**Request:**

.. code-block:: json

   {
     "postal_code": "76131",
     "annual_consumption": 3500
   }

**Response:**

.. code-block:: json

   {
     "base_price_monthly": 18.21,
     "markup_ct_kwh": 15.36,
     "total_price_ct_kwh": 26.84,
     "provider": "EnBW",
     "is_dynamic": true
   }

POST /api/scrape/tado
^^^^^^^^^^^^^^^^^^^^^

Fetch Tado tariff information.

**Request:**

.. code-block:: json

   {
     "postal_code": "10115"
   }

Health Check
------------

GET /health
^^^^^^^^^^^

Health check endpoint for monitoring.

**Response:**

.. code-block:: json

   {
     "status": "healthy",
     "service": "DYNERGY API",
     "timestamp": "2024-12-01T10:30:00"
   }

Error Handling
--------------

All endpoints return standard HTTP status codes:

- ``200``: Success
- ``400``: Bad Request (invalid input)
- ``404``: Not Found
- ``500``: Internal Server Error

**Error Response Format:**

.. code-block:: json

   {
     "detail": "Error message description"
   }

Data Models
-----------

TariffRequest
^^^^^^^^^^^^^

.. code-block:: python

   class TariffRequest(BaseModel):
       annualConsumption: Optional[float]
       hasSmartMeter: Optional[bool]
       zipCode: Optional[str] = "70173"

TariffCalculationResponse
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   class TariffCalculationResponse(BaseModel):
       tariff_name: str
       monthly_cost: float
       annual_cost: float
       tariff_type: str  # "fixed" or "dynamic"
       avg_kwh_price: float
       annual_kwh: Optional[float]

Running the API
---------------

Development
^^^^^^^^^^^

.. code-block:: bash

   # Start FastAPI server
   cd src/backend
   uvicorn app:app --reload --port 8000
   
   # Access interactive docs
   open http://localhost:8000/docs

Production
^^^^^^^^^^

.. code-block:: bash

   # With gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.backend.app:app
   
   # With Docker
   docker-compose up backend

API Documentation
-----------------

Interactive API documentation is available at:

- **Swagger UI**: ``http://localhost:8000/docs``
- **ReDoc**: ``http://localhost:8000/redoc``

See Also
--------

- :doc:`tariff_models` - Tariff calculation classes
- :doc:`risk_analysis` - Risk assessment functions
- :doc:`usage_forecasting` - Consumption prediction
- :doc:`price_forecasting` - Price prediction
- :doc:`webscraping` - Scraper modules
