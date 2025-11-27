Price Forecasting
=========================

The forecasting module provides prediction models for energy prices.
It uses Facebook Prophet for time series forecasting with automatic seasonality detection.

Overview
--------

The module focuses on:

* **Energy Price Forecast** - Prediction of day-ahead electricity prices using SMARD data

Energy Price Forecast
---------------------

.. automodule:: backend.forecasting.energy_price_forecast
   :members:
   :undoc-members:
   :show-inheritance:

Description
^^^^^^^^^^^^

Predicts day-ahead electricity prices using Facebook Prophet and SMARD data from the German Federal Network Agency.

Features
^^^^^^^^

* Prophet time series forecasting
* SMARD API integration
* Seasonality detection
* Confidence intervals
* Forecasts up to 720 hours

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
     - ``True``
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



Best Practices
--------------

1. **Data Quality**
   
   - Use at least 1 year of historical data
   - Remove outliers and faulty measurements
   - Fill missing values appropriately

2. **Model Selection**
   
   - Prophet for interpretable and accurate results
   - Tune hyperparameters for your specific use case
   - Use ensemble methods with different configurations

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

.. autofunction:: backend.forecasting.energy_price_forecast.create_chart_data

   Generates Chart.js-compatible visualization data combining historical and forecast prices.
   Resamples hourly data to daily averages for frontend charts.

.. autofunction:: backend.forecasting.energy_price_forecast.get_price_breakdown

   Calculates electricity price component breakdown based on Bundesnetzagentur data.
   Returns wholesale, network fees, and tax components for visualization.

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



Feature Engineering
-------------------

External Regressors
^^^^^^^^^^^^^^^^^^^

Add weather and calendar features:

.. code-block:: python

   import pandas as pd
   from prophet import Prophet
   
   def add_weather_features(df):
       """Add weather data as regressors"""
       # Load weather data
       weather = pd.read_csv('app_data/combined_market_temperature_data.csv')
       weather['datetime'] = pd.to_datetime(weather['datetime'])
       
       # Merge with energy data
       df = df.merge(weather[['datetime', 'temperature', 'wind_speed']], 
                     on='datetime', how='left')
       
       # Fill missing values
       df['temperature'].fillna(df['temperature'].mean(), inplace=True)
       df['wind_speed'].fillna(df['wind_speed'].mean(), inplace=True)
       
       return df
   
   def forecast_with_regressors(df, days=30):
       # Add features
       df = add_weather_features(df)
       
       # Prepare for Prophet
       prophet_df = df.rename(columns={'datetime': 'ds', 'value': 'y'})
       
       # Create model with regressors
       model = Prophet(
           daily_seasonality=True,
           weekly_seasonality=True
       )
       
       model.add_regressor('temperature')
       model.add_regressor('wind_speed')
       
       # Add custom seasonalities
       model.add_seasonality(
           name='monthly',
           period=30.5,
           fourier_order=5
       )
       
       model.fit(prophet_df)
       
       # Future dataframe with predicted weather
       future = model.make_future_dataframe(periods=24*days, freq='h')
       # Note: You need weather forecasts for future period
       # For now, use historical averages
       future['temperature'] = prophet_df['temperature'].mean()
       future['wind_speed'] = prophet_df['wind_speed'].mean()
       
       forecast = model.predict(future)
       return forecast

Holiday Effects
^^^^^^^^^^^^^^^

.. code-block:: python

   import pandas as pd
   from prophet import Prophet
   
   # Define German holidays
   german_holidays = pd.DataFrame([
       {'holiday': 'New Year', 'ds': '2024-01-01', 'lower_window': 0, 'upper_window': 1},
       {'holiday': 'Easter', 'ds': '2024-03-31', 'lower_window': -1, 'upper_window': 1},
       {'holiday': 'Labour Day', 'ds': '2024-05-01', 'lower_window': 0, 'upper_window': 1},
       {'holiday': 'Christmas', 'ds': '2024-12-25', 'lower_window': -1, 'upper_window': 2},
       {'holiday': 'Christmas', 'ds': '2024-12-26', 'lower_window': 0, 'upper_window': 1},
       # Add more holidays
   ])
   
   # Create model with holidays
   model = Prophet(
       holidays=german_holidays,
       holidays_prior_scale=10.0  # Adjust strength
   )

Model Persistence & Deployment
------------------------------

Saving and Loading Models
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import pickle
   import json
   from datetime import datetime
   
   def save_model_with_metadata(model, forecast, filepath='models/'):
       """Save model with metadata for versioning"""
       timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
       
       # Save model
       model_path = f"{filepath}prophet_model_{timestamp}.pkl"
       with open(model_path, 'wb') as f:
           pickle.dump(model, f)
       
       # Save metadata
       metadata = {
           'timestamp': timestamp,
           'model_params': model.__dict__,
           'forecast_period': len(forecast),
           'mae': None,  # Add if you have test data
           'rmse': None
       }
       
       metadata_path = f"{filepath}metadata_{timestamp}.json"
       with open(metadata_path, 'w') as f:
           json.dump(metadata, f, indent=2, default=str)
       
       return model_path, metadata_path
   
   def load_latest_model(filepath='models/'):
       """Load most recent model"""
       import glob
       import os
       
       models = glob.glob(f"{filepath}prophet_model_*.pkl")
       if not models:
           raise FileNotFoundError("No models found")
       
       latest = max(models, key=os.path.getctime)
       
       with open(latest, 'rb') as f:
           model = pickle.load(f)
       
       return model

Scheduled Retraining
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from apscheduler.schedulers.asyncio import AsyncIOScheduler
   import asyncio
   
   async def retrain_models():
       """Scheduled model retraining"""
       logger.info("Starting model retraining...")
       
       # Fetch latest data
       df = load_and_prepare_data('app_data/germany_dayahead_prices.csv')
       
       # Train new model
       model = create_prophet_model()
       model.fit(df)
       
       # Evaluate on holdout set
       # ... evaluation code ...
       
       # Save if better than current model
       save_model_with_metadata(model, forecast)
       
       logger.info("Model retraining completed")
   
   # Schedule retraining every week
   scheduler = AsyncIOScheduler()
   scheduler.add_job(retrain_models, 'cron', day_of_week='mon', hour=2)
   scheduler.start()

Production API
^^^^^^^^^^^^^^

.. code-block:: python

   from fastapi import FastAPI, HTTPException
   from pydantic import BaseModel
   import pandas as pd
   
   app = FastAPI()
   
   # Load model at startup
   price_model = load_latest_model('models/price/')
   
   class ForecastRequest(BaseModel):
       days: int = 7
       postal_code: str = None
   
   @app.post("/api/forecast/price")
   async def forecast_price(request: ForecastRequest):
       try:
           future = price_model.make_future_dataframe(
               periods=24*request.days, 
               freq='h'
           )
           forecast = price_model.predict(future)
           
           return {
               'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_dict('records'),
               'avg_price': forecast['yhat'].mean(),
               'min_price': forecast['yhat'].min(),
               'max_price': forecast['yhat'].max()
           }
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))

Resources
---------

* `Prophet Documentation <https://facebook.github.io/prophet/>`_
* `SMARD API <https://www.smard.de/home/downloadcenter/download-marktdaten/>`_
* `Time Series Forecasting Best Practices <https://otexts.com/fpp3/>`_
