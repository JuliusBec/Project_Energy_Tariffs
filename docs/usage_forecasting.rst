Usage Forecasting
==================

Household electricity consumption forecasting using Facebook Prophet.

Overview
--------

The usage forecasting module predicts household electricity consumption based on historical smart meter data. It uses Prophet time series models with daily and weekly seasonality to generate hourly consumption forecasts.

Module: ``backend.forecasting.energy_usage_forecast``

Key Functions
-------------

forecast_prophet
^^^^^^^^^^^^^^^^

Generate future consumption forecasts using Prophet.

.. code-block:: python

   from src.backend.forecasting.energy_usage_forecast import forecast_prophet
   import pandas as pd
   
   # Load smart meter data
   df = pd.read_csv('app_data/example_smart_meter.csv')
   # Required columns: datetime, value (kWh)
   
   # Forecast next 30 days
   forecast = forecast_prophet(df, days=30)
   
   print(f"Total predicted consumption: {forecast['yhat'].sum():.2f} kWh")

**Parameters:**

- ``df``: DataFrame with columns ['datetime', 'value'] containing historical hourly consumption
- ``days``: Number of days to forecast (default: 30)

**Returns:**

DataFrame with Prophet forecast columns:

- ``ds``: DateTime of prediction
- ``yhat``: Predicted consumption (kWh)
- ``yhat_lower``: Lower confidence bound
- ``yhat_upper``: Upper confidence bound

**Model Configuration:**

- Daily and weekly seasonality enabled
- Linear growth trend
- 90% confidence intervals
- Additive seasonality mode

create_backtest
^^^^^^^^^^^^^^^

Validate forecast accuracy using a hold-out test period.

.. code-block:: python

   from src.backend.forecasting.energy_usage_forecast import create_backtest
   
   # Validate model on last 30 days
   backtest_results = create_backtest(usage_df)
   
   # Access metrics
   metrics = backtest_results['metrics']
   print(f"MAE: {metrics['mae']:.2f} kWh")
   print(f"Forecast error: {metrics['forecast_error_percentage']:.1f}%")

**Returns:**

Dictionary containing:

- ``hourly_data``: Hourly predictions vs actual values
- ``daily_data``: Daily aggregated forecast vs actual
- ``metrics``: MAE, MSE, total error, confidence intervals

calculate_total_weekly_usage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Aggregate hourly forecasts to weekly totals.

.. code-block:: python

   from src.backend.forecasting.energy_usage_forecast import (
       calculate_total_weekly_usage
   )
   
   weekly_totals = calculate_total_weekly_usage(forecast)
   print(weekly_totals)

Data Format
-----------

Input CSV Format
^^^^^^^^^^^^^^^^

Smart meter data must follow this structure:

.. code-block:: text

   datetime,value,status
   01/15/24 00:00,0.45,
   01/15/24 01:00,0.38,
   01/15/24 02:00,0.32,
   ...

- ``datetime``: Timestamp in format MM/DD/YY HH:MM
- ``value``: Consumption in kWh
- ``status``: Optional status column (ignored)

Example Usage
-------------

Complete Forecasting Pipeline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import pandas as pd
   from src.backend.forecasting.energy_usage_forecast import (
       forecast_prophet, 
       calculate_total_weekly_usage,
       create_backtest
   )
   
   # Load data
   df = pd.read_csv('app_data/example_smart_meter.csv')
   
   # Validate model performance
   backtest = create_backtest(df)
   print(f"Model MAE: {backtest['metrics']['mae']:.2f} kWh")
   
   # Generate forecast
   forecast = forecast_prophet(df, days=30)
   
   # Analyze weekly patterns
   weekly = calculate_total_weekly_usage(forecast)
   print(f"Weekly consumption:\n{weekly['yhat']}")
   
   # Calculate total consumption
   total_30_days = forecast['yhat'].sum()
   avg_daily = total_30_days / 30
   print(f"\nTotal 30-day consumption: {total_30_days:.2f} kWh")
   print(f"Average daily: {avg_daily:.2f} kWh")

API Reference
-------------

.. automodule:: backend.forecasting.energy_usage_forecast
   :members:
   :undoc-members:
   :show-inheritance:

Model Parameters
----------------

The Prophet model is configured with:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Parameter
     - Value
   * - ``daily_seasonality``
     - True (captures day/night patterns)
   * - ``weekly_seasonality``
     - True (captures weekday/weekend patterns)
   * - ``yearly_seasonality``
     - False (not relevant for short-term forecasts)
   * - ``changepoint_prior_scale``
     - 0.25 (moderate trend flexibility)
   * - ``seasonality_prior_scale``
     - 2.0 (moderate seasonality strength)
   * - ``interval_width``
     - 0.9 (90% confidence intervals)
   * - ``seasonality_mode``
     - 'additive'

Evaluation Metrics
------------------

The ``create_backtest`` function provides:

**Error Metrics:**

- **MAE** (Mean Absolute Error): Average absolute difference between forecast and actual
- **MSE** (Mean Squared Error): Squared errors for outlier sensitivity
- **Forecast Error Percentage**: Total prediction error as percentage

**Confidence Metrics:**

- **Average Confidence Interval Width**: Average range of uncertainty
- **Relative Confidence Interval Width**: Uncertainty relative to mean forecast

Integration
-----------

Usage forecasts integrate with the tariff comparison system to calculate expected energy costs:

.. code-block:: python

   # Combine usage and price forecasts
   usage_forecast = forecast_prophet(usage_df, days=30)
   # price_forecast from energy_price_forecast module
   
   merged = pd.merge(
       usage_forecast[['ds', 'yhat']],
       price_forecast[['ds', 'yhat']],
       on='ds',
       suffixes=('_usage', '_price')
   )
   
   # Calculate costs (price in €/MWh -> €/kWh)
   merged['cost'] = merged['yhat_usage'] * merged['yhat_price'] / 1000
   
   total_cost = merged['cost'].sum()
   print(f"Predicted 30-day cost: {total_cost:.2f}€")

See Also
--------

- :doc:`price_forecasting` - Energy price prediction
- :doc:`backend` - Backend API reference
- :doc:`concept` - System architecture
