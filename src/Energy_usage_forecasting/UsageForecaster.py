from chronos import ChronosPipeline
import torch
import numpy as np 
import pandas as pd
from datetime import datetime, timedelta
from prophet import Prophet

def forecast_chronos(df, pipeline=None, context_length=512, forecast_steps=168, 
                         rolling_window_size=62, num_samples=20):
    """
    Perform weekly energy usage forecasting using Chronos with rolling window approach.

    Parameters:
    - df: DataFrame with time series data (must contain 'value' column and datetime index/column)
    - pipeline: ChronosPipeline model (if None, will load default)
    - context_length: Number of historical points to use as context (default: 512)
    - forecast_steps: Number of steps to predict (default: 168 = 7 days)
    - rolling_window_size: Hours to predict in each iteration (default: 24 = 1 day)
    - num_samples: Number of forecast samples for uncertainty quantification

    Returns:
    - forecast_df: DataFrame with forecasted values and confidence intervals
    """
    df = df.copy()
    
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Load model if not provided
    if pipeline is None:
        print("Loading Chronos model for energy usage forecasting...")
        pipeline = ChronosPipeline.from_pretrained(
            "amazon/chronos-t5-small",
            device_map="cpu",
            torch_dtype=torch.float16
        )

    # Resample to hourly frequency
    df.drop(columns=["status"], inplace=True)
    df = df.set_index("datetime").resample("H").mean().reset_index()
    
    # Extract time series values and last datetime
    usage_data = df["value"].values
    last_datetime = pd.to_datetime(df['datetime']).iloc[-1]
        
    # Initialize results storage
    all_forecasts_mean = []
    all_forecasts_lower = []
    all_forecasts_upper = []
    forecast_timestamps = []
    
    # Create extended series for rolling context
    extended_series = usage_data.copy()
    
    # Rolling window forecasting loop
    hours_forecasted = 0
    iteration = 0
    
    while hours_forecasted < forecast_steps:
        iteration += 1
        
        # Determine forecast window size for this iteration
        remaining_hours = forecast_steps - hours_forecasted
        current_window = min(rolling_window_size, remaining_hours)
        
        # Get context window (last context_length points)
        context_start = max(0, len(extended_series) - context_length)
        context_data = extended_series[context_start:]
        
        # Convert to tensor for Chronos
        context_tensor = torch.tensor(context_data, dtype=torch.float32).unsqueeze(0)
        
        print(f"Iteration {iteration}: Forecasting {current_window} hours "
              f"(progress: {hours_forecasted + rolling_window_size}/{forecast_steps})")
        
        # Debug: Check input data variation
        if iteration == 1:
            print(f"  Input data stats: mean={np.mean(context_data):.4f}, std={np.std(context_data):.4f}")
            print(f"  Input data range: [{np.min(context_data):.4f}, {np.max(context_data):.4f}]")

        # Generate forecast
        forecast = pipeline.predict(
            context=context_tensor,
            prediction_length=current_window,
            num_samples=num_samples,
        )
        
        # Process forecast results
        forecast_np = forecast.detach().numpy().squeeze(0)  # Shape: (num_samples, window_size)
        
        # Calculate statistics
        forecast_mean = np.mean(forecast_np, axis=0)
        forecast_lower = np.percentile(forecast_np, 2.5, axis=0)  # 95% CI lower
        forecast_upper = np.percentile(forecast_np, 97.5, axis=0)  # 95% CI upper
        
        # Debug: Check forecast variation
        print(f"  Forecast stats: mean={np.mean(forecast_mean):.4f}, std={np.std(forecast_mean):.4f}")
        print(f"  Forecast range: [{np.min(forecast_mean):.4f}, {np.max(forecast_mean):.4f}]")
        
        # Store results
        all_forecasts_mean.extend(forecast_mean)
        all_forecasts_lower.extend(forecast_lower)
        all_forecasts_upper.extend(forecast_upper)
        
        # Generate timestamps for this forecast window
        window_timestamps = [
            last_datetime + timedelta(hours=hours_forecasted + i + 1) 
            for i in range(current_window)
        ]
        forecast_timestamps.extend(window_timestamps)
        
        # Use mean forecast with small noise to preserve uncertainty
        forecast_mean = np.mean(forecast_np, axis=0)
        forecast_std = np.std(forecast_np, axis=0)
        
        # Add controlled noise (10% of std) to prevent over-smoothing
        noise = np.random.normal(0, forecast_std * 0.1)
        noisy_forecast = forecast_mean + noise
        
        # Ensure non-negative values
        noisy_forecast = np.maximum(noisy_forecast, 0)
        
        extended_series = np.concatenate([extended_series, noisy_forecast])
        
        # Update counter
        hours_forecasted += current_window
            
    # Create final forecast DataFrame
    forecast_df = pd.DataFrame({
        'datetime': forecast_timestamps,
        'usage_forecast_mean': all_forecasts_mean,
        'usage_lower_95': all_forecasts_lower,
        'usage_upper_95': all_forecasts_upper
    })
    
    
    print(f"\nWeekly forecast completed!")
    
    return forecast_df

def calculate_total_weekly_usage(forecast_df):
    # Resample to hourly frequency
    forecast_df = forecast_df.resample("H", on="datetime").sum().reset_index()
    # Sum the usage for each week
    weekly_usage = forecast_df.set_index("datetime").resample("W").sum()
    return weekly_usage

def forecast_prophet(df):
    df["datetime"] = pd.to_datetime(df["datetime"], format='%m/%d/%y %H:%M')

    prophet_df = df.copy()
    prophet_df.rename(columns={'datetime': 'ds', 'value': 'y'}, inplace=True)
    prophet_df.drop(columns=['status'], inplace=True)

    print(prophet_df.head())

    prophet_model = Prophet(
        daily_seasonality=True,
        yearly_seasonality=False,
        weekly_seasonality=True,
        changepoint_prior_scale=0.01,
        seasonality_prior_scale=10,
        interval_width=0.9
    )

    prophet_model.fit(prophet_df)

    future = prophet_model.make_future_dataframe(periods=4*24*30, freq='15min')

    forecast = prophet_model.predict(future)

    # Clip negative values to zero (energy usage cannot be negative)
    print(f"Negative values before clipping: yhat={sum(forecast['yhat'] < 0)}, yhat_lower={sum(forecast['yhat_lower'] < 0)}, yhat_upper={sum(forecast['yhat_upper'] < 0)}")
    forecast['yhat'] = forecast['yhat'].clip(lower=0)
    forecast['yhat_lower'] = forecast['yhat_lower'].clip(lower=0)
    forecast['yhat_upper'] = forecast['yhat_upper'].clip(lower=0)
    print(f"Negative values after clipping: yhat={sum(forecast['yhat'] < 0)}, yhat_lower={sum(forecast['yhat_lower'] < 0)}, yhat_upper={sum(forecast['yhat_upper'] < 0)}")

    forecast.to_csv('data/usage_forecasting/user_data_14781_forecast_prophet.csv', index=False)



df = pd.read_csv('data/usage_forecasting/user_data_14781_training.csv')

forecast_df = forecast_chronos(df, context_length=512, forecast_steps=168, rolling_window_size=62, num_samples=20)
forecast_df.to_csv('data/usage_forecasting/user_data_14781_forecast_chronos.csv', index=False)