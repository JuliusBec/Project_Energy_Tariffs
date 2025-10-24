import torch
import numpy as np 
import pandas as pd
from chronos import ChronosPipeline
from datetime import datetime, timedelta

def forecast_chronos(df, pipeline=None, context_length=512, forecast_steps=168, 
                         rolling_window_size=62, num_samples=20, use_single_shot=False):
    """
    Perform weekly energy usage forecasting using Chronos with rolling window or single-shot approach.

    Parameters:
    - df: DataFrame with time series data (must contain 'value' column and datetime index/column)
    - pipeline: ChronosPipeline model (if None, will load default)
    - context_length: Number of historical points to use as context (default: 512)
    - forecast_steps: Number of steps to predict (default: 168 = 7 days)
    - rolling_window_size: Hours to predict in each iteration (default: 24 = 1 day)
    - num_samples: Number of forecast samples for uncertainty quantification
    - use_single_shot: If True, bypass rolling window and predict all steps at once

    Returns:
    - forecast_df: DataFrame with forecasted values and confidence intervals
    """
    df = df.copy()
    
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Load model if not provided
    if pipeline is None:
        print("Loading Chronos model for energy usage forecasting...")
        pipeline = ChronosPipeline.from_pretrained(
            "amazon/chronos-t5-base",
            device_map="cpu",
            torch_dtype=torch.float16
        )

    # Resample to hourly frequency (sum for energy consumption)
    if 'status' in df.columns:
        df.drop(columns=["status"], inplace=True)
    df = df.set_index("datetime").resample("H").sum().reset_index()
    
    # Extract time series values and last datetime
    usage_data = df["value"].values
    last_datetime = pd.to_datetime(df['datetime']).iloc[-1]
    
    if use_single_shot:
        print("Using SINGLE-SHOT forecasting approach (no rolling window)")
        
        # Get context window (last context_length points)
        context_start = max(0, len(usage_data) - context_length)
        context_data = usage_data[context_start:]
        
        # Convert to tensor for Chronos
        context_tensor = torch.tensor(context_data, dtype=torch.float32).unsqueeze(0)
        
        print(f"Single-shot: Forecasting {forecast_steps} hours at once")
        print(f"  Input data stats: mean={np.mean(context_data):.4f}, std={np.std(context_data):.4f}")
        print(f"  Input data range: [{np.min(context_data):.4f}, {np.max(context_data):.4f}]")

        # Generate single forecast for all steps
        try:
            print(f"  Requesting prediction_length: {forecast_steps}")
            forecast = pipeline.predict(
                context=context_tensor,
                prediction_length=forecast_steps,
                num_samples=num_samples,
            )
            print(f"  Actual forecast shape: {forecast.shape}")
            
            # Process forecast results
            forecast_np = forecast.detach().numpy().squeeze(0)  # Shape: (num_samples, forecast_steps)
            
            # Calculate statistics
            forecast_mean = np.mean(forecast_np, axis=0)
            forecast_lower = np.percentile(forecast_np, 2.5, axis=0)  # 95% CI lower
            forecast_upper = np.percentile(forecast_np, 97.5, axis=0)  # 95% CI upper
            
            print(f"  Forecast stats: mean={np.mean(forecast_mean):.4f}, std={np.std(forecast_mean):.4f}")
            print(f"  Forecast range: [{np.min(forecast_mean):.4f}, {np.max(forecast_mean):.4f}]")
            
            # Generate timestamps
            forecast_timestamps = [
                last_datetime + timedelta(hours=i + 1) 
                for i in range(forecast_steps)
            ]
            
            # Create final forecast DataFrame
            forecast_df = pd.DataFrame({
                'datetime': forecast_timestamps,
                'usage_forecast_mean': forecast_mean,
                'usage_lower_95': forecast_lower,
                'usage_upper_95': forecast_upper
            })

            # forecast_df.to_csv('data/usage_forecasting/user_data_' + str(user_id) + '_forecast_chronos.csv', index=False)
            print(f"\nSingle-shot forecast completed!")
            return forecast_df
            
        except Exception as e:
            print(f"Single-shot failed: {e}")
            print("Falling back to rolling window approach...")
    else:
    # Rolling window approach (original logic)
        print("Using ROLLING WINDOW forecasting approach")
            
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
                f"(progress: {hours_forecasted + current_window}/{forecast_steps})")
            
            # Debug: Check input data variation
            if iteration == 1:
                print(f"  Input data stats: mean={np.mean(context_data):.4f}, std={np.std(context_data):.4f}")
                print(f"  Input data range: [{np.min(context_data):.4f}, {np.max(context_data):.4f}]")

            # Generate forecast
            print(f"  Requesting prediction_length: {current_window}")
            forecast = pipeline.predict(
                context=context_tensor,
                prediction_length=current_window,
                num_samples=num_samples,
            )
            print(f"  Actual forecast shape: {forecast.shape}")
            
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
            
            # Sample randomly from the forecast distribution to preserve uncertainty
            random_sample_idx = np.random.randint(0, num_samples)
            sampled_forecast = forecast_np[random_sample_idx]  # Use actual sample, not mean

            # Ensure non-negative values
            sampled_forecast = np.maximum(sampled_forecast, 0)

            extended_series = np.concatenate([extended_series, sampled_forecast])
            
            # Update counter
            hours_forecasted += current_window
                
        # Create final forecast DataFrame
        forecast_df = pd.DataFrame({
            'datetime': forecast_timestamps,
            'usage_forecast_mean': all_forecasts_mean,
            'usage_lower_95': all_forecasts_lower,
            'usage_upper_95': all_forecasts_upper
        })

        # forecast_df.to_csv('data/usage_forecasting/user_data_' + str(user_id) + '_forecast_chronos.csv', index=False)
        print(f"\nRolling window forecast completed!")

    return forecast_df