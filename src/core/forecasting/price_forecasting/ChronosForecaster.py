import pandas as pd
from chronos import ChronosPipeline
import torch
import matplotlib.pyplot as plt
import numpy as np 
from datetime import datetime, timedelta

def rolling_window_forecast(df, pipeline, context_length=512, forecast_steps=48, num_samples=10):
    """
    Perform rolling window forecasting for a full year using Chronos.
    
    Parameters:
    - df: DataFrame with time series data
    - pipeline: ChronosPipeline model
    - context_length: Number of historical points to use as context (default: 512)
    - forecast_steps: Number of steps to predict in each iteration (default: 48 = 2 days)
    - num_samples: Number of forecast samples for uncertainty quantification
    
    Returns:
    - forecast_df: DataFrame with forecasted values and confidence intervals
    """
    
    # Extract time series values
    time_series = df["market_price"].values
    
    # Calculate total steps for one year (365 days * 24 hours)
    total_forecast_hours = 365 * 24  # 8760 hours
    
    # Initialize lists to store results
    all_forecasts_mean = []
    all_forecasts_lower = []
    all_forecasts_upper = []
    forecast_timestamps = []
    
    # Starting point for forecasting (after the training data)
    current_position = len(time_series)
    
    # Create extended time series that will include both historical and forecasted values
    extended_series = time_series.copy()
    
    # Get the last datetime from the original data
    last_datetime = pd.to_datetime(df['datetime'].iloc[-1])
    
    print(f"Starting rolling window forecast for {total_forecast_hours} hours ({total_forecast_hours//24} days)")
    print(f"Using context length: {context_length}, forecast steps per iteration: {forecast_steps}")
    print(f"Last training datetime: {last_datetime}")
    
    # Rolling window forecasting loop
    steps_forecasted = 0
    iteration = 0
    
    while steps_forecasted < total_forecast_hours:
        iteration += 1
        
        # Determine how many steps to forecast in this iteration
        remaining_steps = total_forecast_hours - steps_forecasted
        current_forecast_steps = min(forecast_steps, remaining_steps)
        
        # Get context window (last context_length points from extended series)
        context_start = max(0, len(extended_series) - context_length)
        context_data = extended_series[context_start:]
        
        # Convert to tensor
        context_tensor = torch.tensor(context_data, dtype=torch.float32).unsqueeze(0)
        
        print(f"Iteration {iteration}: Forecasting {current_forecast_steps} steps (total progress: {steps_forecasted}/{total_forecast_hours})")
        
        # Generate forecast
        forecast = pipeline.predict(
            context=context_tensor,
            prediction_length=current_forecast_steps,
            num_samples=num_samples,
        )
        
        # Process forecast results
        forecast_np = forecast.detach().numpy().squeeze(0)  # Shape: (num_samples, forecast_steps)
        
        # Calculate statistics
        forecast_mean = np.mean(forecast_np, axis=0)
        forecast_lower = np.percentile(forecast_np, 2.5, axis=0)
        forecast_upper = np.percentile(forecast_np, 97.5, axis=0)
        
        # Store results
        all_forecasts_mean.extend(forecast_mean)
        all_forecasts_lower.extend(forecast_lower)
        all_forecasts_upper.extend(forecast_upper)
        
        # Generate timestamps for this forecast batch
        for i in range(current_forecast_steps):
            forecast_time = last_datetime + timedelta(hours=steps_forecasted + i + 1)
            forecast_timestamps.append(forecast_time)
        
        # Update extended series with mean forecast for next iteration's context
        extended_series = np.concatenate([extended_series, forecast_mean])
        
        # Update counters
        steps_forecasted += current_forecast_steps
        
        # Progress update
        if iteration % 10 == 0:
            progress = (steps_forecasted / total_forecast_hours) * 100
            print(f"Progress: {progress:.1f}% ({steps_forecasted}/{total_forecast_hours} hours)")
    
    # Create final forecast DataFrame
    forecast_df = pd.DataFrame({
        'datetime': forecast_timestamps,
        'mean': all_forecasts_mean,
        'lower_95': all_forecasts_lower,
        'upper_95': all_forecasts_upper
    })
    
    return forecast_df

# Initialize Chronos pipeline
print("Loading Chronos model...")
pipeline = ChronosPipeline.from_pretrained(
    "amazon/chronos-t5-small",
    device_map="cpu",
    torch_dtype=torch.float16
)

# Load training data
print("Loading training data...")
df = pd.read_csv("data/training_dataset_weather.csv")
print(f"Training data shape: {df.shape}")
print(f"Training data date range: {df['datetime'].iloc[0]} to {df['datetime'].iloc[-1]}")

# Perform rolling window forecast
print("\nStarting rolling window forecast...")
forecast_df = rolling_window_forecast(
    df=df, 
    pipeline=pipeline, 
    context_length=512,  # Use 512 hours (~21 days) as context
    forecast_steps=48,   # Predict 48 hours (2 days) at a time
    num_samples=10       # Generate 10 samples for uncertainty quantification
)

print(f"\nForecast completed!")
print(f"Forecast shape: {forecast_df.shape}")
print(f"Forecast date range: {forecast_df['datetime'].iloc[0]} to {forecast_df['datetime'].iloc[-1]}")

# Save to CSV
output_file = "data/chronos_yearly_forecast.csv"
forecast_df.to_csv(output_file, index=False)
print(f"Yearly forecast results saved to {output_file}")

# Display summary statistics
print(f"\nForecast Summary Statistics:")
print(f"Mean forecast value: {forecast_df['mean'].mean():.2f}")
print(f"Forecast std deviation: {forecast_df['mean'].std():.2f}")
print(f"Min forecast value: {forecast_df['mean'].min():.2f}")
print(f"Max forecast value: {forecast_df['mean'].max():.2f}")

# Create visualization
print("\nGenerating forecast visualization...")
plt.figure(figsize=(15, 8))

# Plot a subset for better visibility (first 30 days)
subset_days = 30
subset_hours = subset_days * 24
forecast_subset = forecast_df.head(subset_hours).copy()
forecast_subset['hour'] = range(len(forecast_subset))

plt.subplot(2, 1, 1)
plt.plot(forecast_subset['hour'], forecast_subset['mean'], label='Mean Forecast', color='blue', linewidth=1)
plt.fill_between(forecast_subset['hour'], forecast_subset['lower_95'], forecast_subset['upper_95'], 
                color='lightblue', alpha=0.3, label='95% CI')
plt.title(f'Rolling Window Forecast - First {subset_days} Days (Hourly Resolution)')
plt.xlabel('Hours from forecast start')
plt.ylabel('Energy Price')
plt.legend()
plt.grid(True, alpha=0.3)

# Plot full year (daily averages for overview)
plt.subplot(2, 1, 2)
forecast_df['date'] = pd.to_datetime(forecast_df['datetime']).dt.date
daily_avg = forecast_df.groupby('date').agg({
    'mean': 'mean',
    'lower_95': 'mean', 
    'upper_95': 'mean'
}).reset_index()

plt.plot(range(len(daily_avg)), daily_avg['mean'], label='Daily Average Forecast', color='red', linewidth=1)
plt.fill_between(range(len(daily_avg)), daily_avg['lower_95'], daily_avg['upper_95'], 
                color='lightcoral', alpha=0.3, label='95% CI (Daily Avg)')
plt.title('Full Year Forecast - Daily Averages')
plt.xlabel('Days from forecast start')
plt.ylabel('Energy Price (Daily Average)')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('figures/yearly_rolling_forecast.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"\nForecast visualization saved to figures/yearly_rolling_forecast.png")
print("Rolling window forecast completed successfully!")