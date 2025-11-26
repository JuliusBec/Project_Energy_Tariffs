Forecasting & Predictions
=========================

The forecasting module provides powerful prediction models for energy prices and energy consumption.
It combines Prophet and Chronos for accurate short-term and long-term forecasts.

Overview
--------

The module contains two main components:

* **Energy Price Forecast** - Prediction of day-ahead electricity prices
* **Energy Usage Forecast** - Prediction of household consumption

Both modules use machine learning algorithms and historical data for accurate predictions.

Energy Price Forecast
---------------------

.. automodule:: backend.forecasting.energy_price_forecast
   :members:
   :undoc-members:
   :show-inheritance:

Description
^^^^^^^^^^^^

The Energy Price Forecaster uses Facebook Prophet to predict day-ahead electricity prices
based on SMARD data (Federal Network Agency).

Features
^^^^^^^^

* Prophet-based time series forecasting
* SMARD API integration
* Automatic seasonality detection
* Confidence intervals
* Up to 720 hours forecast

Usage
^^^^^

Basic Usage
"""""""""""""""""""""""

.. code-block:: python

   from src.backend.forecasting.energy_price_forecast import (
       load_and_prepare_data,
       create_prophet_model,
       forecast_prices
   )
   import pandas as pd

   # Load data
   df = load_and_prepare_data('app_data/germany_dayahead_prices.csv')
   
   # Create model
   model = create_prophet_model(
       changepoint_prior_scale=0.15,
       seasonality_prior_scale=10.0
   )
   
   # Training
   model.fit(df)
   
   # Forecast for 7 days
   forecast = forecast_prices(model, periods=168)  # 168 hours = 7 days
   
   print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail())

Advanced Configuration
""""""""""""""""""""""

.. code-block:: python

   # Custom model with user-defined parameters
   from prophet import Prophet
   
   model = Prophet(
       daily_seasonality=True,
       weekly_seasonality=True,
       yearly_seasonality=True,
       changepoint_prior_scale=0.15,      # Flexibility for trend changes
       seasonality_prior_scale=10.0,      # Strength of seasonality
       interval_width=0.95,               # 95% confidence interval
       growth='linear',                   # Linear growth
       seasonality_mode='additive'        # Additive seasonality
   )
   
   # Add additional regressors
   model.add_regressor('temperature')
   model.add_regressor('wind_speed')
   
   # Custom seasonality
   model.add_seasonality(
       name='monthly',
       period=30.5,
       fourier_order=5
   )

SMARD API Integration
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from src.backend.forecasting.energy_price_forecast import fetch_smard_data
   from datetime import datetime, timedelta
   
   # Define time period
   end_date = datetime.now()
   start_date = end_date - timedelta(days=365)
   
   # Fetch data from SMARD API
   df = fetch_smard_data(
       start_timestamp=int(start_date.timestamp() * 1000),
       end_timestamp=int(end_date.timestamp() * 1000)
   )
   
   # Save data
   df.to_csv('app_data/latest_prices.csv', index=False)

Visualization
^^^^^^^^^^^^^

.. code-block:: python

   import matplotlib.pyplot as plt
   from prophet.plot import plot_plotly, plot_components_plotly
   
   # Plot forecast
   fig1 = model.plot(forecast)
   plt.title('Day-Ahead Electricity Price Forecast')
   plt.ylabel('Price (€/MWh)')
   plt.xlabel('Date')
   plt.savefig('forecast_plot.png')
   
   # Component analysis
   fig2 = model.plot_components(forecast)
   plt.savefig('components_plot.png')
   
   # Interactive Plotly charts
   fig3 = plot_plotly(model, forecast)
   fig3.write_html('interactive_forecast.html')

Energy Usage Forecast
---------------------

.. automodule:: backend.forecasting.energy_usage_forecast
   :members:
   :undoc-members:
   :show-inheritance:

Description
^^^^^^^^^^^^

The Energy Usage Forecaster predicts household electricity consumption.
Prophet is used for traditional time series analysis and Chronos for deep learning-based predictions.

Features
^^^^^^^^

* Prophet & Chronos models
* Hourly consumption forecast
* Weekly aggregation
* Seasonality detection (daily, weekly)
* Flexible forecast periods

Usage
^^^^^

Prophet-based Forecast
"""""""""""""""""""""""""""

.. code-block:: python

   from src.backend.forecasting.energy_usage_forecast import forecast_prophet
   import pandas as pd
   
   # Load historical consumption data
   df = pd.read_csv('app_data/example_smart_meter.csv')
   
   # Format: datetime, value
   # datetime: Timestamp
   # value: Consumption in kWh
   
   # 30-day forecast
   forecast_df = forecast_prophet(df, days=30)
   
   print(forecast_df[['datetime', 'yhat', 'yhat_lower', 'yhat_upper']].head())
   
   # Calculate weekly totals
   from src.backend.forecasting.energy_usage_forecast import (
       calculate_total_weekly_usage
   )
   weekly_usage = calculate_total_weekly_usage(forecast_df)
   print(f"Weekly consumption:\n{weekly_usage}")

Chronos Deep Learning Modell
""""""""""""""""""""""""""""

.. code-block:: python

   from chronos import ChronosPipeline
   import torch
   import numpy as np
   
   # Chronos Pipeline laden
   pipeline = ChronosPipeline.from_pretrained(
       "amazon/chronos-t5-small",
       device_map="cpu",  # Oder "cuda" für GPU
       torch_dtype=torch.bfloat16,
   )
   
   # Prepare historical data
   context = torch.tensor(df['value'].values[-168:])  # Last 7 days
   
   # Forecast for 24 hours
   forecast = pipeline.predict(
       context=context,
       prediction_length=24,
       num_samples=20
   )
   
   # Median forecast
   median_forecast = np.median(forecast[0].numpy(), axis=0)

Data Format
^^^^^^^^^^^

Input data must have the following format:

.. code-block:: python

   # CSV structure
   datetime,value,status
   01/15/24 00:00,0.45,
   01/15/24 01:00,0.38,
   01/15/24 02:00,0.32,
   ...

   # Or as DataFrame
   import pandas as pd
   
   df = pd.DataFrame({
       'datetime': pd.date_range('2024-01-01', periods=8760, freq='h'),
       'value': np.random.uniform(0.2, 2.5, 8760)  # kWh per hour
   })

Model Parameters
----------------

Prophet Parameters
^^^^^^^^^^^^^^^^^^

Important parameters for model optimization:

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - Parameter
     - Description
     - Recommended Value
   * - ``daily_seasonality``
     - Daily patterns (day/night)
     - ``True``
   * - ``weekly_seasonality``
     - Weekly patterns (weekday/weekend)
     - ``True``
   * - ``yearly_seasonality``
     - Annual patterns (seasons)
     - ``False`` (for consumption)
   * - ``changepoint_prior_scale``
     - Flexibility for trend changes
     - ``0.15-0.25``
   * - ``seasonality_prior_scale``
     - Strength of seasonality
     - ``2.0-10.0``
   * - ``interval_width``
     - Confidence interval
     - ``0.90-0.95``
   * - ``seasonality_mode``
     - Type of seasonality
     - ``'additive'``

Example: Parameter Tuning
"""""""""""""""""""""""""""

.. code-block:: python

   from prophet import Prophet
   from sklearn.metrics import mean_absolute_error
   
   # Parameter grid
   params = {
       'changepoint_prior_scale': [0.15, 0.20, 0.25],
       'seasonality_prior_scale': [2.0, 5.0, 10.0]
   }
   
   best_params = {}
   best_mae = float('inf')
   
   for cp_scale in params['changepoint_prior_scale']:
       for s_scale in params['seasonality_prior_scale']:
           model = Prophet(
               changepoint_prior_scale=cp_scale,
               seasonality_prior_scale=s_scale,
               daily_seasonality=True,
               weekly_seasonality=True
           )
           
           model.fit(train_df)
           forecast = model.predict(test_df)
           
           mae = mean_absolute_error(test_df['y'], forecast['yhat'])
           
           if mae < best_mae:
               best_mae = mae
               best_params = {
                   'changepoint_prior_scale': cp_scale,
                   'seasonality_prior_scale': s_scale
               }
   
   print(f"Best parameters: {best_params}")
   print(f"MAE: {best_mae:.4f} kWh")

Evaluation & Metrics
--------------------

Model Evaluation
^^^^^^^^^^^^^^^^

.. code-block:: python

   from sklearn.metrics import (
       mean_absolute_error,
       mean_squared_error,
       r2_score
   )
   import numpy as np
   
   def evaluate_forecast(actual, predicted):
       """Calculate evaluation metrics"""
       mae = mean_absolute_error(actual, predicted)
       rmse = np.sqrt(mean_squared_error(actual, predicted))
       mape = np.mean(np.abs((actual - predicted) / actual)) * 100
       r2 = r2_score(actual, predicted)
       
       return {
           'MAE': mae,
           'RMSE': rmse,
           'MAPE': mape,
           'R²': r2
       }
   
   # Application
   metrics = evaluate_forecast(
       actual=test_data['value'],
       predicted=forecast_df['yhat']
   )
   
   print(f"MAE: {metrics['MAE']:.2f} kWh")
   print(f"RMSE: {metrics['RMSE']:.2f} kWh")
   print(f"MAPE: {metrics['MAPE']:.2f}%")
   print(f"R²: {metrics['R²']:.4f}")

Cross-Validation
^^^^^^^^^^^^^^^^

.. code-block:: python

   from prophet.diagnostics import cross_validation, performance_metrics
   
   # Time Series Cross-Validation
   df_cv = cross_validation(
       model,
       initial='730 days',    # Initial training
       period='180 days',     # Distance between cutoffs
       horizon='30 days'      # Forecast horizon
   )
   
   # Performance metrics
   df_p = performance_metrics(df_cv)
   print(df_p[['horizon', 'mape', 'rmse']])

Practical Examples
------------------

Complete Pipeline: Price Forecast
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from src.backend.forecasting.energy_price_forecast import (
       load_and_prepare_data,
       create_prophet_model,
       forecast_prices,
       save_forecast
   )
   import pandas as pd
   
   # 1. Load data
   df = load_and_prepare_data('app_data/germany_dayahead_prices.csv')
   
   # 2. Create and train model
   model = create_prophet_model()
   model.fit(df)
   
   # 3. Forecast for 30 days
   forecast = forecast_prices(model, periods=720)  # 30 days * 24 hours
   
   # 4. Save
   save_forecast(forecast, 'app_data/germany_price_forecast_720h.csv')
   
   # 5. Statistics
   print(f"Average price: {forecast['yhat'].mean():.2f} €/MWh")
   print(f"Min: {forecast['yhat'].min():.2f} €/MWh")
   print(f"Max: {forecast['yhat'].max():.2f} €/MWh")

Complete Pipeline: Usage Forecast
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from src.backend.forecasting.energy_usage_forecast import (
       forecast_prophet,
       calculate_total_weekly_usage
   )
   import pandas as pd
   
   # 1. Load smart meter data
   df = pd.read_csv('app_data/example_smart_meter.csv')
   
   # 2. 30-day forecast
   forecast = forecast_prophet(df, days=30)
   
   # 3. Weekly aggregation
   weekly = calculate_total_weekly_usage(forecast)
   
   # 4. Output
   print("Weekly consumption (kWh):")
   print(weekly['yhat'])
   
   # 5. Total consumption
   total_month = forecast['yhat'].sum()
   print(f"\nTotal consumption (30 days): {total_month:.2f} kWh")

Integration in Tariff Comparison
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from src.backend.forecasting.energy_usage_forecast import forecast_prophet
   from src.backend.forecasting.energy_price_forecast import forecast_prices
   import pandas as pd
   
   # Predict consumption
   usage_df = pd.read_csv('app_data/smart_meter.csv')
   usage_forecast = forecast_prophet(usage_df, days=30)
   
   # Predict prices
   price_model = create_prophet_model()
   price_forecast = forecast_prices(price_model, periods=720)
   
   # Combine for cost calculation
   merged = pd.merge(
       usage_forecast[['datetime', 'yhat']],
       price_forecast[['ds', 'yhat']],
       left_on='datetime',
       right_on='ds',
       suffixes=('_usage', '_price')
   )
   
   # Calculate costs (price in €/MWh -> €/kWh)
   merged['cost'] = (merged['yhat_usage'] * 
                     merged['yhat_price'] / 1000)
   
   total_cost = merged['cost'].sum()
   print(f"Estimated costs (30 days): {total_cost:.2f}€")

Best Practices
--------------

1. **Data Quality**
   
   - Use at least 1 year of historical data
   - Remove outliers and faulty measurements
   - Fill missing values appropriately

2. **Model Selection**
   
   - Prophet for interpretable results
   - Chronos for highest accuracy
   - Combine models for ensemble predictions

3. **Validation**
   
   - Use time series cross-validation
   - Test on unseen data
   - Monitor metrics continuously

4. **Performance**
   
   - Cache trained models
   - Use incremental training
   - Parallelize batch predictions

Troubleshooting
---------------

Common Issues
^^^^^^^^^^^^^

**Problem: "Unable to fit model" error**

.. code-block:: python

   # Solution: Check data format
   df['ds'] = pd.to_datetime(df['ds'])
   df = df.dropna()
   df = df.sort_values('ds')

**Problem: Unrealistic predictions**

.. code-block:: python

   # Solution: Set cap values
   model = Prophet(
       growth='logistic'  # Instead of 'linear'
   )
   
   df['cap'] = 300  # Maximum price in €/MWh
   df['floor'] = -50  # Minimum price

**Problem: Slow predictions**

.. code-block:: python

   # Solution: Serialize model
   import pickle
   
   # Save model
   with open('model.pkl', 'wb') as f:
       pickle.dump(model, f)
   
   # Load model
   with open('model.pkl', 'rb') as f:
       model = pickle.load(f)

API Reference
-------------

Functions
^^^^^^^^^

.. autofunction:: backend.forecasting.energy_price_forecast.load_and_prepare_data

.. autofunction:: backend.forecasting.energy_price_forecast.create_prophet_model

.. autofunction:: backend.forecasting.energy_price_forecast.forecast_prices

.. autofunction:: backend.forecasting.energy_usage_forecast.forecast_prophet

.. autofunction:: backend.forecasting.energy_usage_forecast.calculate_total_weekly_usage

Advanced Features
-----------------

Uncertainty Quantification
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Analyze confidence intervals
   forecast['uncertainty'] = (
       forecast['yhat_upper'] - forecast['yhat_lower']
   )
   
   # Identify high uncertainty
   high_uncertainty = forecast[
       forecast['uncertainty'] > forecast['uncertainty'].quantile(0.9)
   ]
   
   print(f"Periods with high uncertainty: {len(high_uncertainty)}")

Anomaly Detection
^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Forecast vs. actual values
   df['anomaly'] = abs(df['y'] - df['yhat']) > (2 * df['yhat_upper'])
   
   anomalies = df[df['anomaly'] == True]
   print(f"Detected anomalies: {len(anomalies)}")

Resources
---------

* `Prophet Documentation <https://facebook.github.io/prophet/>`_
* `Chronos Paper <https://arxiv.org/abs/2403.07815>`_
* `SMARD API <https://www.smard.de/home/downloadcenter/download-marktdaten/>`_
* `Time Series Forecasting Best Practices <https://otexts.com/fpp3/>`_
