#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Energy Price Forecasting using Prophet
Predicts day-ahead electricity prices for Germany using SMARD data
"""

import argparse
import json
import logging
import os
from datetime import datetime, timedelta
import pandas as pd
import requests
import numpy as np
from zoneinfo import ZoneInfo
import matplotlib.pyplot as plt
from prophet import Prophet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configure matplotlib for non-interactive backend
plt.switch_backend('Agg')

# API Configuration
SMARD_BASE = "https://www.smard.de/app/chart_data"
FILTER_ID = "4169"  # Day-Ahead Wholesale Price (€/MWh)
REGION = "DE"      # Germany
RESOLUTION = "hour" # Hourly resolution

class SMARDAPIError(Exception):
    """Custom exception for SMARD API errors"""
    pass

def fetch_available_timestamps():
    """
    Fetch available timestamps from SMARD API
    Returns:
        list: Sorted list of timestamps in milliseconds
    """
    try:
        url = f"{SMARD_BASE}/{FILTER_ID}/{REGION}/index_{RESOLUTION}.json"
        logging.info(f"Fetching timestamps from {url}")
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        timestamps = sorted(data.get("timestamps", []))
        if not timestamps:
            raise SMARDAPIError("No timestamps received from SMARD API")
        
        logging.info(f"Found {len(timestamps)} available timestamps")
        return timestamps
        
    except requests.exceptions.RequestException as e:
        raise SMARDAPIError(f"Failed to fetch timestamps: {str(e)}")
    except json.JSONDecodeError as e:
        raise SMARDAPIError(f"Failed to parse API response: {str(e)}")

def fetch_timeseries_for_timestamp(ts_ms: int) -> pd.DataFrame:
    """
    Fetch timeseries data for a specific timestamp
    Args:
        ts_ms: Timestamp in milliseconds
    Returns:
        pd.DataFrame: DataFrame with columns [utc_ms, price_eur_per_mwh]
    """
    try:
        path = f"{FILTER_ID}_{REGION}_{RESOLUTION}_{ts_ms}.json"
        url = f"{SMARD_BASE}/{FILTER_ID}/{REGION}/{path}"
        logging.debug(f"Fetching data from {url}")
        
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        payload = response.json()
        
        series = payload.get("series", [])
        if not series:
            raise SMARDAPIError(f"No data received for timestamp {ts_ms}")
        
        df = pd.DataFrame(series, columns=["utc_ms", "price_eur_per_mwh"])
        return df
        
    except requests.exceptions.RequestException as e:
        raise SMARDAPIError(f"Failed to fetch data: {str(e)}")
    except (json.JSONDecodeError, KeyError) as e:
        raise SMARDAPIError(f"Failed to parse data: {str(e)}")

def load_smard_dayahead(limit_chunks: int | None = None) -> pd.DataFrame:
    """
    Load all available (or last N chunks) hourly day-ahead prices for Germany
    Args:
        limit_chunks: Optional limit on number of chunks to load
    Returns:
        pd.DataFrame: Clean DataFrame with datetime index and prices
    """
    try:
        # Fetch available timestamps
        timestamps = fetch_available_timestamps()
        if limit_chunks:
            timestamps = timestamps[-limit_chunks:]
            logging.info(f"Using last {limit_chunks} chunks")

        # Fetch data chunks
        frames = []
        for i, ts in enumerate(timestamps, 1):
            try:
                df = fetch_timeseries_for_timestamp(ts)
                frames.append(df)
                logging.info(f"Loaded chunk {i}/{len(timestamps)} ({ts})")
            except SMARDAPIError as e:
                logging.warning(f"Failed to load chunk {ts}: {str(e)}")

        if not frames:
            raise SMARDAPIError("No data could be loaded")

        # Combine and process data
        data = pd.concat(frames, ignore_index=True).drop_duplicates("utc_ms")
        logging.info(f"Combined {len(frames)} chunks, got {len(data)} records")

        # Convert timestamps to Berlin timezone then remove timezone info (Prophet requirement)
        data["ds"] = (pd.to_datetime(data["utc_ms"], unit="ms", utc=True)
                     .dt.tz_convert("Europe/Berlin")
                     .dt.tz_localize(None))  # Remove timezone info
        data = data.sort_values("ds").reset_index(drop=True)

        # Clean data
        original_len = len(data)
        data = data[pd.notna(data["price_eur_per_mwh"])]
        data = data[~(data["price_eur_per_mwh"].astype(float).abs() > 1e6)]
        cleaned_len = len(data)
        
        if original_len != cleaned_len:
            logging.warning(f"Removed {original_len - cleaned_len} invalid records")
        
        logging.info(f"Final dataset: {len(data)} records from {data['ds'].min()} to {data['ds'].max()}")
        return data[["ds", "price_eur_per_mwh"]]
        
    except Exception as e:
        raise SMARDAPIError(f"Failed to load day-ahead prices: {str(e)}")

def train_prophet(df_hourly: pd.DataFrame, 
                 seasonality_mode: str = "multiplicative",
                 changepoint_prior_scale: float = 0.05,
                 changepoint_range: float = 0.95,
                 season_weekly: bool = True,
                 season_daily: bool = True) -> Prophet:
    """
    Train a Prophet model optimized for long-term forecasting
    Args:
        df_hourly: DataFrame with ds (datetime) and price_eur_per_mwh columns
        seasonality_mode: 'additive' or 'multiplicative'
        changepoint_prior_scale: Flexibility of the trend (0.01-0.5)
        changepoint_range: Proportion of history in which trend changepoints will be estimated
        season_weekly: Whether to model weekly seasonality
        season_daily: Whether to model daily seasonality
    Returns:
        Prophet: Trained Prophet model
    """
    try:
        # Create and configure Prophet model
        model = Prophet(
            yearly_seasonality=20,  # Increased Fourier terms for better yearly pattern modeling
            weekly_seasonality=10,  # Increased Fourier terms for weekly patterns
            daily_seasonality=season_daily,
            changepoint_prior_scale=changepoint_prior_scale,
            seasonality_mode=seasonality_mode,
            interval_width=0.95,  # 95% prediction intervals
            changepoint_range=changepoint_range,  # Allow changepoints throughout the data
            n_changepoints=100,  # Increased number of changepoints for long-term data
        )
        
        # Add custom seasonalities
        model.add_seasonality(
            name='hourly',
            period=24,
            fourier_order=12
        )
        
        # Prepare training data
        train = df_hourly.rename(columns={"ds": "ds", "price_eur_per_mwh": "y"})[["ds", "y"]]
        train["y"] = train["y"].astype(float)
        
        # Fit the model
        logging.info("Training Prophet model...")
        model.fit(train)
        logging.info("Model training completed")
        
        return model
        
    except Exception as e:
        logging.error(f"Error training Prophet model: {str(e)}")
        raise

def plot_forecast_analysis(model: Prophet, forecast: pd.DataFrame, actual_data: pd.DataFrame):
    """Create detailed forecast analysis plots with long-term trend analysis"""
    try:
        logging.info("Creating forecast analysis plots...")
        
        # Force Agg backend
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.style.use('seaborn')
        
        # Save to Desktop for visibility
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        output_path = os.path.join(desktop, 'forecast_analysis.png')
        
        # Create figure with multiple subplots
        fig = plt.figure(figsize=(20, 16))
        
        # Plot 1: Actual vs Predicted with confidence intervals
        ax1 = plt.subplot(3, 1, 1)
        ax1.plot(actual_data['ds'], actual_data['price_eur_per_mwh'], 
                label='Actual', color='blue', alpha=0.5)
        ax1.plot(forecast['ds'], forecast['yhat'], 
                label='Forecast', color='red', linestyle='--')
        ax1.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'],
                        color='red', alpha=0.1, label='95% Confidence Interval')
        ax1.set_title('Energy Price Forecast with Confidence Intervals')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Price (EUR/MWh)')
        ax1.legend()
        
        # Plot 2: Components
        if 'trend' in forecast.columns:
            ax2 = plt.subplot(3, 1, 2)
            ax2.plot(forecast['ds'], forecast['trend'], label='Trend')
            if 'weekly' in forecast.columns:
                ax2.plot(forecast['ds'], forecast['weekly'], label='Weekly Pattern')
            if 'daily' in forecast.columns:
                ax2.plot(forecast['ds'], forecast['daily'], label='Daily Pattern')
            ax2.set_title('Forecast Components')
            ax2.set_xlabel('Date')
            ax2.set_ylabel('Effect on Price')
            ax2.legend()
        
        # Plot 3: Error Analysis (for historical data only)
        historical_forecast = forecast[forecast['ds'].isin(actual_data['ds'])]
        historical_actual = actual_data[actual_data['ds'].isin(historical_forecast['ds'])]
        errors = historical_actual['price_eur_per_mwh'].values - historical_forecast['yhat'].values
        
        ax3 = plt.subplot(3, 1, 3)
        ax3.hist(errors, bins=50, edgecolor='black')
        ax3.set_title('Forecast Error Distribution')
        ax3.set_xlabel('Error (EUR/MWh)')
        ax3.set_ylabel('Frequency')
        
        # Add statistical information
        rmse = np.sqrt(np.mean(errors**2))
        mae = np.mean(np.abs(errors))
        stats_text = f'RMSE: {rmse:.2f} EUR/MWh\nMAE: {mae:.2f} EUR/MWh'
        ax3.text(0.95, 0.95, stats_text,
                transform=ax3.transAxes,
                verticalalignment='top',
                horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        # Save with explicit flushing and closing
        try:
            fig.savefig(output_path, dpi=300, bbox_inches='tight', format='png')
            fig.clf()
            plt.close(fig)
            plt.close('all')
            
            if os.path.exists(output_path):
                logging.info(f"Plot saved successfully to: {output_path}")
                logging.info(f"File size: {os.path.getsize(output_path)} bytes")
            else:
                raise Exception("File was not created successfully")
                
        except Exception as e:
            logging.error(f"Error saving plot: {str(e)}")
            plt.close('all')
            raise
        
    except Exception as e:
        logging.error(f"Error creating plots: {str(e)}")
        plt.close('all')  # Clean up any open figures
        raise

def calculate_required_chunks(target_days):
    """Calculate how many chunks needed for target days of data"""
    days_per_chunk = 7
    return int(target_days / days_per_chunk) + 1

def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(
            description="SMARD Day-Ahead Price Forecasting using Prophet"
        )
        parser.add_argument(
            "--horizon-hours",
            type=int,
            default=720,  # 30 days
            help="Forecast horizon in hours (default: 720=30 days)"
        )
        parser.add_argument(
            "--training-days",
            type=int,
            default=730,  # 2 years
            help="Number of days of training data to use (default: 730=2 years)"
        )

        args = parser.parse_args()

        # Create output directory
        os.makedirs('output', exist_ok=True)

        # Calculate required chunks for training data
        required_chunks = calculate_required_chunks(args.training_days)
        logging.info(f"Requesting {required_chunks} chunks to cover {args.training_days} days of training data")
        
        # Load data
        logging.info("Loading SMARD Day-Ahead prices (Germany, hourly)...")
        df = load_smard_dayahead(limit_chunks=required_chunks)
        
        # Calculate and log the training data range
        date_range = df['ds'].max() - df['ds'].min()
        logging.info(f"\nTraining Data Range:")
        logging.info(f"Start date: {df['ds'].min().strftime('%Y-%m-%d %H:%M')}")
        logging.info(f"End date: {df['ds'].max().strftime('%Y-%m-%d %H:%M')}")
        logging.info(f"Total period: {date_range.days} days and {date_range.seconds//3600} hours")
        logging.info(f"Total data points: {len(df)} hourly prices")
        
        # Save raw data
        raw_data_path = os.path.join('output', 'smard_dayahead_de.csv')
        df.to_csv(raw_data_path, index=False)
        logging.info(f"\nRaw data saved to {raw_data_path}")

        # Train model
        logging.info("Training Prophet model...")
        model = train_prophet(
            df_hourly=df,
            seasonality_mode='multiplicative',
            changepoint_prior_scale=0.05,
            changepoint_range=0.95
        )

        # Generate forecast
        logging.info(f"Generating {args.horizon_hours}h forecast...")
        future = model.make_future_dataframe(
            periods=args.horizon_hours,
            freq='H',
            include_history=True
        )
        forecast = model.predict(future)

        # Save forecast results
        forecast_path = os.path.join('output', 'forecast.csv')
        forecast.to_csv(forecast_path, index=False)
        logging.info(f"Forecast saved to {forecast_path}")

        # Create visualization
        logging.info("Generating forecast analysis plots...")
        plot_forecast_analysis(model, forecast, df)

        # Print forecast statistics
        future_forecast = forecast[forecast['ds'] > df['ds'].max()]
        logging.info("\nForecast Statistics (next period):")
        logging.info(f"Average Price: {future_forecast['yhat'].mean():.2f} EUR/MWh")
        logging.info(f"Max Price: {future_forecast['yhat'].max():.2f} EUR/MWh")
        logging.info(f"Min Price: {future_forecast['yhat'].min():.2f} EUR/MWh")
        
        logging.info("Forecasting completed successfully!")

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
