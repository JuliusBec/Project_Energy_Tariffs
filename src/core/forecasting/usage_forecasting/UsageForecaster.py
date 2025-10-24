from chronos import ChronosPipeline

import numpy as np 
import pandas as pd
from datetime import datetime, timedelta
from prophet import Prophet
import matplotlib.pyplot as plt



def calculate_total_weekly_usage(forecast_df):
    # Resample to hourly frequency
    forecast_df = forecast_df.resample("H", on="datetime").sum().reset_index()
    # Sum the usage for each week
    weekly_usage = forecast_df.set_index("datetime").resample("W").sum()
    return weekly_usage

def forecast_prophet(df, days=30):
    # Explicitly create a copy to avoid SettingWithCopyWarning
    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"], format='%m/%d/%y %H:%M')

    # Resample to hourly frequency for consistent modeling (sum for energy consumption)
    # Only drop status column if it exists
    if 'status' in df.columns:
        df.drop(columns=['status'], inplace=True)
    df = df.set_index("datetime").resample("H").sum().reset_index()

    prophet_df = df.copy()
    prophet_df.rename(columns={'datetime': 'ds', 'value': 'y'}, inplace=True)
    
    prophet_model = Prophet(
        daily_seasonality=True,
        yearly_seasonality=False,
        weekly_seasonality=True,
        changepoint_prior_scale=0.25,
        seasonality_prior_scale=2.0,
        interval_width=0.9,
        growth="linear",
        seasonality_mode='additive'    # Additive seasonality (typical for energy consumption)
    )

    prophet_model.fit(prophet_df)

    future = prophet_model.make_future_dataframe(periods=24*days, freq='h')

    forecast = prophet_model.predict(future)

    return forecast

def create_backtest(usage_df, return_data=False, show_daily_view=False, show_hourly_view=True):
    """
    Create backtest visualization comparing actual vs forecasted energy usage.
    
    Parameters:
    - usage_df: DataFrame with energy usage data
    - return_data: If True, return structured data instead of displaying plots
    - show_daily_view: Show daily aggregated view (mobile-friendly)
    - show_hourly_view: Show detailed hourly view
    
    Returns:
    - If return_data=True: Dictionary with hourly_data, daily_data, and metrics
    - If return_data=False: None (displays plots)
    """
    
    usage_df = usage_df.copy()
    usage_df['datetime'] = pd.to_datetime(usage_df['datetime'])
    
    # Resample to hourly frequency for consistent comparison (sum for energy consumption)
    if 'status' in usage_df.columns:
        usage_df.drop(columns=["status"], inplace=True)
    usage_df = usage_df.set_index("datetime").resample("H").sum().reset_index()
    
    # Split the usage_df into train and test sets
    # Get exactly the last 720 hours (30 days × 24 hours) for backtest
    backtest_df = usage_df.tail(24 * 30).copy()
    
    # Check if the last day is incomplete (less than 24 hours)
    last_day = backtest_df['datetime'].dt.date.iloc[-1]
    hours_in_last_day = len(backtest_df[backtest_df['datetime'].dt.date == last_day])
    
    if hours_in_last_day < 24:
        print(f"Removing incomplete last day ({last_day}) with only {hours_in_last_day} hours")
        # Remove the incomplete day to get exactly 29 complete days
        backtest_df = backtest_df[backtest_df['datetime'].dt.date != last_day]
        complete_days = len(backtest_df) // 24
        print(f"Using {complete_days} complete days ({len(backtest_df)} hours) for backtest")
    
    # Train on everything before the backtest period
    train_end_datetime = backtest_df['datetime'].min() - pd.Timedelta(hours=1)
    train_df = usage_df[usage_df['datetime'] <= train_end_datetime]

    # Calculate forecast hours to exactly match backtest period
    forecast_hours = len(backtest_df)
    backtest_forecast = forecast_prophet(train_df, days=30)  # Generate more than needed
    
    # Extract only the forecast period that exactly matches backtest_df
    forecast_start_time = backtest_df['datetime'].min()
    forecast_end_time = backtest_df['datetime'].max()
    forecast_only = backtest_forecast[
        (backtest_forecast['ds'] >= forecast_start_time) & 
        (backtest_forecast['ds'] <= forecast_end_time)
    ].copy()
    
    # Ensure we have exactly the same number of data points
    if len(forecast_only) != len(backtest_df):
        print(f"Warning: Forecast has {len(forecast_only)} hours, backtest has {len(backtest_df)} hours")
        # If forecast is shorter, extend it by taking more from the full forecast
        if len(forecast_only) < len(backtest_df):
            needed_hours = len(backtest_df) - len(forecast_only)
            # Get additional hours from the end of the full forecast
            additional_forecast = backtest_forecast[
                backtest_forecast['ds'] > forecast_end_time
            ].head(needed_hours)
            forecast_only = pd.concat([forecast_only, additional_forecast], ignore_index=True)
            print(f"Extended forecast to {len(forecast_only)} hours to match backtest period")
    
    # Clip negative values to 0
    forecast_only['yhat'] = forecast_only['yhat'].clip(lower=0)
    forecast_only['yhat_lower'] = forecast_only['yhat_lower'].clip(lower=0)
    forecast_only['yhat_upper'] = forecast_only['yhat_upper'].clip(lower=0)
    
    # Calculate and print the total usage in the backtest period
    total_forecast_usage = forecast_only['yhat'].sum()
    total_actual_usage = backtest_df['value'].sum()
    print(f"Total forecasted usage over backtest period: {total_forecast_usage:.2f}")
    print(f"Total actual usage over backtest period: {total_actual_usage:.2f}")
    print(f"Forecast error (absolute): {abs(total_forecast_usage - total_actual_usage):.2f}")
    print(f"Forecast error (percentage): {abs(total_forecast_usage - total_actual_usage) / total_actual_usage * 100:.2f}%")
    
    # Calculate and print the MAE and MSE between the forecast and the backtest data
    merged_df = pd.merge(forecast_only[['ds', 'yhat']], backtest_df[['datetime', 'value']], 
                        left_on='ds', right_on='datetime', how='inner')
    mae = np.mean(np.abs(merged_df['yhat'] - merged_df['value']))
    mse = np.mean((merged_df['yhat'] - merged_df['value'])**2)
    print(f"Backtest MAE: {mae:.4f}")
    print(f"Backtest MSE: {mse:.4f}")

    # Prepare data for return if requested
    if return_data:
        # Aggregate to daily totals
        forecast_daily = forecast_only.copy()
        forecast_daily = forecast_daily.set_index('ds').resample('D').sum().reset_index()
        
        backtest_daily = backtest_df.copy()
        backtest_daily = backtest_daily.set_index('datetime').resample('D').sum().reset_index()
        
        # Prepare hourly data
        hourly_data = {
            'timestamps': forecast_only['ds'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
            'forecast': forecast_only['yhat'].tolist(),
            'forecast_lower': forecast_only['yhat_lower'].tolist(),
            'forecast_upper': forecast_only['yhat_upper'].tolist(),
            'actual': backtest_df['value'].tolist()
        }
        
        # Prepare daily data
        daily_data = {
            'timestamps': forecast_daily['ds'].dt.strftime('%Y-%m-%d').tolist(),
            'forecast': forecast_daily['yhat'].tolist(),
            'actual': backtest_daily['value'].tolist()
        }
        
        # Metrics
        metrics = {
            'total_forecast_usage': float(total_forecast_usage),
            'total_actual_usage': float(total_actual_usage),
            'forecast_error_absolute': float(abs(total_forecast_usage - total_actual_usage)),
            'forecast_error_percentage': float(abs(total_forecast_usage - total_actual_usage) / total_actual_usage * 100),
            'mae': float(mae),
            'mse': float(mse),
            'forecast_period_days': len(forecast_daily)
        }
        
        return {
            'hourly_data': hourly_data,
            'daily_data': daily_data,
            'metrics': metrics
        }
    
    # Show daily aggregated view (mobile-friendly)
    if show_daily_view:
        # Aggregate to daily totals for cleaner visualization
        forecast_daily = forecast_only.copy()
        forecast_daily = forecast_daily.set_index('ds').resample('D').sum().reset_index()
        
        backtest_daily = backtest_df.copy()
        backtest_daily = backtest_daily.set_index('datetime').resample('D').sum().reset_index()
        
        # Create mobile-friendly plot
        plt.figure(figsize=(10, 6))
        
        # Plot with better styling
        plt.plot(forecast_daily['ds'], forecast_daily['yhat'], 
                label='Forecast', color='#2E86AB', linewidth=2, marker='o', markersize=4)
        plt.plot(backtest_daily['datetime'], backtest_daily['value'], 
                label='Actual', color='#F24236', linewidth=2, marker='s', markersize=4)
        
        plt.title('Daily Energy Usage: Actual vs Forecast\n(30-Day Backtest)', fontsize=14, fontweight='bold', pad=20)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Daily Energy Usage (kWh)', fontsize=12)
        
        # Set y-axis to start at 0 and go up to 150% of maximum value
        max_actual = backtest_daily['value'].max()
        max_forecast = forecast_daily['yhat'].max()
        y_max = max(max_actual, max_forecast) * 1.5
        plt.ylim(bottom=0, top=y_max)
        
        # Improve legend and grid
        plt.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        plt.grid(True, alpha=0.3, linestyle='--')
        
        # Better date formatting for mobile
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        plt.show()
    
    # Show detailed hourly view if requested
    if show_hourly_view:
        plt.figure(figsize=(15, 8))
        plt.plot(forecast_only['ds'], forecast_only['yhat'], label='Forecast', color='blue', alpha=0.8)
        plt.fill_between(forecast_only['ds'], forecast_only['yhat_lower'], forecast_only['yhat_upper'], 
                        color='blue', alpha=0.2, label='90% Confidence Interval')
        plt.plot(backtest_df['datetime'], backtest_df['value'], label='Actual', color='orange', alpha=0.8)
        
        plt.title('Hourly Energy Usage: Actual vs Forecast (30-Day Backtest)', fontsize=14, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Hourly Energy Usage (kWh)', fontsize=12)
        
        # Set y-axis to start at 0
        plt.ylim(bottom=0)
        
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    
# execute create_backtest with user data for testing

user_data = pd.read_csv('data/household_data/user_data_12401.csv')
create_backtest(user_data, show_daily_view=True, show_hourly_view=True)