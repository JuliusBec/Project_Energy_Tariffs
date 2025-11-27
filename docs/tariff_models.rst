Tariff Models
==============

Energy tariff model classes for comparing fixed and dynamic electricity contracts in the German market.

Overview
--------

The tariff models module (``backend.energy_tariff``) provides abstract and concrete implementations for calculating electricity costs under different pricing structures.

Module: ``backend.energy_tariff``

Classes
-------

EnergyTariff
^^^^^^^^^^^^

Abstract base class for all energy tariff types. Provides common functionality for billing periods, contract management, and cost calculations.

**Key Methods:**

- ``calculate_billing_period_days()``: Calculate German market-standard billing period length
- ``calculate_cost_split()``: Abstract method for itemized cost breakdown
- ``calculate_cost()``: Calculate total cost for the billing period

FixedTariff
^^^^^^^^^^^

Traditional fixed-rate electricity tariff with constant per-kWh pricing.

.. code-block:: python

   from src.backend.energy_tariff import FixedTariff
   from datetime import datetime
   
   # Create fixed tariff
   tariff = FixedTariff(
       name="EnBW Komfort",
       provider="EnBW",
       base_price=15.90,        # €/month
       kwh_rate=0.3599,         # €/kWh
       start_date=datetime.now(),
       min_duration=12,         # months
       features=["green", "fixed"]
   )
   
   # Calculate cost for 250 kWh monthly consumption
   cost_breakdown = tariff.calculate_cost_split(250)
   print(f"Total: {cost_breakdown['total_cost']}€")
   print(f"Base: {cost_breakdown['base_price']}€")
   print(f"Energy: {cost_breakdown['variable_cost']}€")

**Cost Calculation:**

Total Cost = Base Price + (Consumption × kWh Rate)

DynamicTariff
^^^^^^^^^^^^^

Spot-market-based electricity tariff with hourly price variations following EPEX SPOT day-ahead market.

.. code-block:: python

   from src.backend.energy_tariff import DynamicTariff
   from datetime import datetime
   import pandas as pd
   
   # Create dynamic tariff
   tariff = DynamicTariff(
       name="Tibber",
       provider="Tibber",
       base_price=14.99,                    # €/month
       start_date=datetime.now(),
       network_fee=0.0,                     # One-time fee
       additional_price_ct_kwh=15.5,        # Fixed markup (ct/kWh)
       features=["dynamic", "green", "smart_meter"]
   )
   
   # Load smart meter data
   consumption_df = pd.read_csv('smart_meter_data.csv')
   
   # Calculate cost with time-dependent pricing
   result = tariff.calculate_cost_with_breakdown(consumption_df)
   print(f"Total: {result['total_cost']}€")
   print(f"Avg price: {result['avg_kwh_price']}€/kWh")

**Price Components:**

- Wholesale price (day-ahead market, zero-censored)
- Network fees (~7-8 ct/kWh)
- Electricity tax (2.05 ct/kWh)
- Concession fees (~1.5 ct/kWh)
- VAT (19%)
- Supplier costs (~7 ct/kWh)

Data Formats
------------

Smart Meter CSV Format
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

   datetime,value,status
   01/15/24 00:00,0.45,
   01/15/24 01:00,0.38,
   ...

- ``datetime``: MM/DD/YY HH:MM format
- ``value``: Consumption in kWh (or kW for automatic conversion)
- ``status``: Optional status column (ignored)

Consumption Patterns
--------------------

Standard Load Profile
^^^^^^^^^^^^^^^^^^^^^

For annual consumption input without smart meter data, the system uses German H0 standard load profile scaled to match the provided yearly consumption.

.. code-block:: python

   # Calculate cost with annual consumption only
   annual_kwh = 3500
   cost = tariff.calculate_cost(annual_kwh)

Forecasting Integration
^^^^^^^^^^^^^^^^^^^^^^^

For uploaded smart meter data, consumption is forecasted using Prophet for the billing period:

.. code-block:: python

   import pandas as pd
   
   # Load historical data
   df = pd.read_csv('consumption_history.csv')
   
   # Prophet automatically forecasts next billing period
   cost = tariff.calculate_cost(df)

Helper Functions
----------------

slice_seasonal_data
^^^^^^^^^^^^^^^^^^^

Extract seasonal consumption pattern from historical data by matching day-of-year and hour.

.. code-block:: python

   from src.backend.energy_tariff import slice_seasonal_data
   from datetime import datetime
   
   # Extract March consumption pattern
   march_data = slice_seasonal_data(
       df=yearly_consumption_df,
       start_date=datetime(2025, 3, 1),
       days=30
   )

API Reference
-------------

.. automodule:: backend.energy_tariff
   :members:
   :undoc-members:
   :show-inheritance:

Billing Period Calculation
---------------------------

German energy contracts follow market-standard billing practices:

- Contracts starting on month-end bill on the last day of subsequent months
- Contracts starting mid-month bill on the same day each month
- Handles varying month lengths (28-31 days)

Integration
-----------

Tariff models integrate with forecasting and risk analysis:

.. code-block:: python

   from src.backend.energy_tariff import DynamicTariff, FixedTariff
   from src.backend.risk_analysis import create_historic_risk_analysis
   
   # Create tariffs
   dynamic = DynamicTariff(name="Tibber", base_price=14.99, ...)
   fixed = FixedTariff(name="EnBW", base_price=15.90, kwh_rate=0.36, ...)
   
   # Calculate costs
   dynamic_cost = dynamic.calculate_cost_with_breakdown(consumption_df)
   fixed_cost = fixed.calculate_cost(consumption_df)
   
   # Analyze risk
   risk = create_historic_risk_analysis(consumption_df, days=30)

See Also
--------

- :doc:`risk_analysis` - Risk assessment for dynamic tariffs
- :doc:`usage_forecasting` - Consumption prediction
- :doc:`price_forecasting` - Price prediction
- :doc:`api` - REST API endpoints
