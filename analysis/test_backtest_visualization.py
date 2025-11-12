"""
Test script for backtest visualization with local plotting capabilities.
This module provides two different views for analyzing backtest results:
1. Daily aggregated view (mobile-friendly)
2. Detailed hourly view with confidence intervals

For production API, use the create_backtest function with return_data=True
in energy_usage_forecast.py
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.backend.forecasting.energy_usage_forecast import forecast_prophet


def plot_backtest_daily_view(backtest_df, forecast_only):
    """
    Create daily aggregated view (mobile-friendly).
    
    Parameters:
    - backtest_df: DataFrame with actual energy usage data
    - forecast_only: DataFrame with forecast data from Prophet
    """
    # Aggregate to daily totals for cleaner visualization
    forecast_daily = forecast_only.copy()
    forecast_daily = forecast_daily.set_index('ds').resample('D').sum().reset_index()
    
    backtest_daily = backtest_df.copy()
    backtest_daily = backtest_daily.set_index('datetime').resample('D').sum().reset_index()
    
    # Create mobile-friendly plot
    plt.figure(figsize=(12, 7))
    
    # Plot with better styling
    plt.plot(forecast_daily['ds'], forecast_daily['yhat'], 
            label='Forecast', color='#2E86AB', linewidth=2.5, marker='o', markersize=5)
    plt.plot(backtest_daily['datetime'], backtest_daily['value'], 
            label='Actual', color='#F24236', linewidth=2.5, marker='s', markersize=5)
    
    plt.title('Daily Energy Usage: Actual vs Forecast\n(30-Day Backtest)', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Date', fontsize=13)
    plt.ylabel('Daily Energy Usage (kWh)', fontsize=13)
    
    # Set y-axis to start at 0 and go up to 150% of maximum value
    max_actual = backtest_daily['value'].max()
    max_forecast = forecast_daily['yhat'].max()
    y_max = max(max_actual, max_forecast) * 1.5
    plt.ylim(bottom=0, top=y_max)
    
    # Improve legend and grid
    plt.legend(loc='best', frameon=True, fancybox=True, shadow=True, fontsize=11)
    plt.grid(True, alpha=0.3, linestyle='--')
    
    # Better date formatting for mobile
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    plt.show()


def plot_backtest_hourly_view(backtest_df, forecast_only):
    """
    Create detailed hourly view with confidence intervals.
    
    Parameters:
    - backtest_df: DataFrame with actual energy usage data
    - forecast_only: DataFrame with forecast data from Prophet
    """
    plt.figure(figsize=(16, 9))
    
    # Plot forecast with confidence intervals
    plt.plot(forecast_only['ds'], forecast_only['yhat'], 
            label='Forecast', color='#2E86AB', alpha=0.9, linewidth=2)
    plt.fill_between(forecast_only['ds'], 
                    forecast_only['yhat_lower'], 
                    forecast_only['yhat_upper'], 
                    color='#2E86AB', alpha=0.2, label='90% Confidence Interval')
    
    # Plot actual values
    plt.plot(backtest_df['datetime'], backtest_df['value'], 
            label='Actual', color='#F24236', alpha=0.9, linewidth=2)
    
    plt.title('Hourly Energy Usage: Actual vs Forecast (30-Day Backtest)', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Date', fontsize=13)
    plt.ylabel('Hourly Energy Usage (kWh)', fontsize=13)
    
    # Set y-axis to start at 0
    plt.ylim(bottom=0)
    
    plt.legend(loc='best', fontsize=11, frameon=True, fancybox=True, shadow=True)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    plt.show()


def run_backtest_analysis(usage_df, show_daily=True, show_hourly=True):
    """
    Run complete backtest analysis with local plotting.
    
    Parameters:
    - usage_df: DataFrame with energy usage data (must have 'datetime' and 'value' columns)
    - show_daily: Show daily aggregated view
    - show_hourly: Show detailed hourly view
    
    Returns:
    - Dictionary with backtest metrics and data
    """
    print("=" * 80)
    print("BACKTEST ANALYSIS")
    print("=" * 80)
    
    # Prepare data
    usage_df = usage_df.copy()
    usage_df['datetime'] = pd.to_datetime(usage_df['datetime'])
    
    # Resample to hourly frequency for consistent comparison
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
        print(f"⚠️  Removing incomplete last day ({last_day}) with only {hours_in_last_day} hours")
        backtest_df = backtest_df[backtest_df['datetime'].dt.date != last_day]
        complete_days = len(backtest_df) // 24
        print(f"✓  Using {complete_days} complete days ({len(backtest_df)} hours) for backtest")
    
    # Train on everything before the backtest period
    train_end_datetime = backtest_df['datetime'].min() - pd.Timedelta(hours=1)
    train_df = usage_df[usage_df['datetime'] <= train_end_datetime]
    
    print(f"\n📊 Training Period: {train_df['datetime'].min()} to {train_df['datetime'].max()}")
    print(f"📊 Backtest Period: {backtest_df['datetime'].min()} to {backtest_df['datetime'].max()}")
    print(f"📊 Training samples: {len(train_df)} hours")
    print(f"📊 Backtest samples: {len(backtest_df)} hours")
    
    # Generate forecast
    print("\n🔮 Generating forecast...")
    backtest_forecast = forecast_prophet(train_df, days=30)
    
    # Extract only the forecast period that exactly matches backtest_df
    forecast_start_time = backtest_df['datetime'].min()
    forecast_end_time = backtest_df['datetime'].max()
    forecast_only = backtest_forecast[
        (backtest_forecast['ds'] >= forecast_start_time) & 
        (backtest_forecast['ds'] <= forecast_end_time)
    ].copy()
    
    # Ensure we have exactly the same number of data points
    if len(forecast_only) != len(backtest_df):
        print(f"⚠️  Warning: Forecast has {len(forecast_only)} hours, backtest has {len(backtest_df)} hours")
        if len(forecast_only) < len(backtest_df):
            needed_hours = len(backtest_df) - len(forecast_only)
            additional_forecast = backtest_forecast[
                backtest_forecast['ds'] > forecast_end_time
            ].head(needed_hours)
            forecast_only = pd.concat([forecast_only, additional_forecast], ignore_index=True)
            print(f"✓  Extended forecast to {len(forecast_only)} hours to match backtest period")
    
    # Clip negative values to 0
    forecast_only['yhat'] = forecast_only['yhat'].clip(lower=0)
    forecast_only['yhat_lower'] = forecast_only['yhat_lower'].clip(lower=0)
    forecast_only['yhat_upper'] = forecast_only['yhat_upper'].clip(lower=0)
    
    # Calculate metrics
    total_forecast_usage = forecast_only['yhat'].sum()
    total_actual_usage = backtest_df['value'].sum()
    absolute_error = abs(total_forecast_usage - total_actual_usage)
    percentage_error = (absolute_error / total_actual_usage) * 100
    
    merged_df = pd.merge(forecast_only[['ds', 'yhat']], backtest_df[['datetime', 'value']], 
                        left_on='ds', right_on='datetime', how='inner')
    mae = np.mean(np.abs(merged_df['yhat'] - merged_df['value']))
    mse = np.mean((merged_df['yhat'] - merged_df['value'])**2)
    rmse = np.sqrt(mse)
    
    # Calculate confidence interval metrics
    confidence_interval_width = forecast_only['yhat_upper'] - forecast_only['yhat_lower']
    avg_confidence_interval_width = confidence_interval_width.mean()
    relative_confidence_interval_width = (avg_confidence_interval_width / forecast_only['yhat'].mean()) * 100
    
    # Print metrics
    print("\n" + "=" * 80)
    print("BACKTEST METRICS")
    print("=" * 80)
    print(f"Total Forecasted Usage:  {total_forecast_usage:>10.2f} kWh")
    print(f"Total Actual Usage:      {total_actual_usage:>10.2f} kWh")
    print(f"Absolute Error:          {absolute_error:>10.2f} kWh")
    print(f"Percentage Error:        {percentage_error:>10.2f} %")
    print(f"Mean Absolute Error:     {mae:>10.4f} kWh")
    print(f"Mean Squared Error:      {mse:>10.4f} kWh²")
    print(f"Root Mean Squared Error: {rmse:>10.4f} kWh")
    print(f"Forecast Accuracy:       {100 - percentage_error:>10.2f} %")
    print("-" * 80)
    print(f"Avg CI Width:            {avg_confidence_interval_width:>10.4f} kWh")
    print(f"Relative CI Width:       {relative_confidence_interval_width:>10.2f} % of mean")
    print("=" * 80)
    
    # Show plots
    if show_daily:
        print("\n📈 Showing daily aggregated view...")
        plot_backtest_daily_view(backtest_df, forecast_only)
    
    if show_hourly:
        print("\n📈 Showing hourly detailed view...")
        plot_backtest_hourly_view(backtest_df, forecast_only)
    
    # Return metrics
    return {
        'total_forecast_usage': total_forecast_usage,
        'total_actual_usage': total_actual_usage,
        'absolute_error': absolute_error,
        'percentage_error': percentage_error,
        'mae': mae,
        'mse': mse,
        'rmse': rmse,
        'accuracy': 100 - percentage_error,
        'forecast_period_days': len(backtest_df) // 24,
        'avg_confidence_interval_width': avg_confidence_interval_width,
        'relative_confidence_interval_width': relative_confidence_interval_width
    }


def main():
    """
    Main function to run backtest analysis.
    Modify this to load your own data file.
    """
    # Example: Load user data
    # Replace with your actual data file path
    data_file = "../data/user_data/user_data_14781.csv"
    
    # Check if file exists
    if not os.path.exists(data_file):
        print(f"❌ Error: Data file not found: {data_file}")
        print("\n💡 Available test files in data/user_data/:")
        user_data_dir = "../data/user_data"
        if os.path.exists(user_data_dir):
            files = [f for f in os.listdir(user_data_dir) if f.endswith('.csv')]
            for f in files[:5]:  # Show first 5 files
                print(f"   - {f}")
        return
    
    print(f"📁 Loading data from: {data_file}")
    df = pd.read_csv(data_file)
    
    # Validate columns
    if 'datetime' not in df.columns or 'value' not in df.columns:
        print("❌ Error: CSV must have 'datetime' and 'value' columns")
        print(f"Found columns: {df.columns.tolist()}")
        return
    
    print(f"✓  Loaded {len(df)} rows of data")
    print(f"✓  Date range: {df['datetime'].min()} to {df['datetime'].max()}")
    
    # Run backtest analysis
    metrics = run_backtest_analysis(
        df, 
        show_daily=True,   # Show daily view
        show_hourly=True   # Show hourly view
    )
    
    print("\n✅ Backtest analysis complete!")
    
    return metrics


if __name__ == "__main__":
    main()
