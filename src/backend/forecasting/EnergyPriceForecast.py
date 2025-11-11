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
import subprocess
import sys
from datetime import datetime, timedelta

def check_and_install_requirements():
    """Check and install required packages if they're missing"""
    required_packages = {
        'pandas': '2.1.3',
        'matplotlib': '3.9.2',
        'numpy': '1.26.4',
        'prophet': '1.1.4',
        'requests': '2.32.5',
        'seaborn': '0.13.2'
    }
    
    missing_packages = []
    
    for package, version in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(f"{package}=={version}")
    
    if missing_packages:
        print("Installing missing packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
        print("Required packages installed successfully!")
        print("Please restart the script for the changes to take effect.")
        sys.exit(0)

# Check and install requirements before importing
check_and_install_requirements()

# Now import the required packages
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
    Raises:
        SMARDAPIError: If API request fails or no data received
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
    Raises:
        SMARDAPIError: If API request fails or data is invalid
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

def to_eur_per_kwh(df: pd.DataFrame) -> pd.DataFrame:
    """Convert prices from EUR/MWh to EUR/kWh"""
    out = df.copy()
    out["price_eur_per_kwh"] = out["price_eur_per_mwh"] / 1000.0
    return out

def apply_retail_pricing(forecast: pd.DataFrame, 
                        profile_costs: float = 10.0,
                        risk_premium: float = 5.0,
                        margin: float = 55.0,
                        floor_eur_per_mwh: float = 0.0,
                        use_probabilistic: bool = True) -> pd.DataFrame:
    """
    Apply retail pricing logic to wholesale price forecasts with proper zero-censoring
    
    Two-stage approach:
    1. Market Forecast: Day-ahead prices as-is (can be negative)
    2. Tariff Mapping: Convert to retail prices with business logic
    
    Retail price components per kWh:
        - Zero-censored wholesale price (E[max(0, Y_t)])
        - Profile/management costs (Profilkosten/Bewirtschaftungskosten)
        - Risk premium (Risikoprämie)
        - Supplier margin (Marge)
    
    Args:
        forecast: DataFrame with 'yhat', 'yhat_lower', 'yhat_upper' columns
        profile_costs: Profile/management costs in EUR/MWh (default: 10 = 1 ct/kWh)
        risk_premium: Risk premium in EUR/MWh (default: 5 = 0.5 ct/kWh)
        margin: Supplier margin in EUR/MWh (default: 55 = 5.5 ct/kWh)
        floor_eur_per_mwh: Minimum price floor for wholesale component (default: 0)
        use_probabilistic: Use probabilistic expectation E[max(0,Y)] instead of max(0, E[Y])
    
    Returns:
        DataFrame with retail prices:
        - yhat_energy: Zero-censored wholesale component
        - yhat_retail: Full retail price (energy + costs + premium + margin)
        - yhat_retail_lower/upper: Confidence intervals
    
    Mathematical approach:
        If use_probabilistic=True and we have prediction intervals:
            Assume Y_t ~ N(μ_t, σ_t²) where:
            μ_t = yhat
            σ_t ≈ (yhat_upper - yhat_lower) / (2 * 1.96)  # 95% CI
            
            Then: E[max(0, Y_t)] = μ_t * Φ(μ_t/σ_t) + σ_t * φ(μ_t/σ_t)
            where Φ is standard normal CDF, φ is standard normal PDF
        
        Otherwise: Simple clipping max(0, μ_t)
    
    Note:
        - Wholesale prices can be negative (wind/solar surplus)
        - Suppliers apply floor at 0 for energy component
        - Costs/premium/margin always >= 0
        - Total: 70 EUR/MWh ≈ 7 ct/kWh markup (typical for dynamic tariffs)
    """
    from scipy import stats
    
    retail = forecast.copy()
    
    if use_probabilistic and 'yhat_lower' in retail.columns and 'yhat_upper' in retail.columns:
        # Probabilistic approach: E[max(0, Y)] with Normal approximation
        mu = retail['yhat'].values
        # Estimate sigma from 95% confidence interval
        sigma = (retail['yhat_upper'].values - retail['yhat_lower'].values) / (2 * 1.96)
        sigma = np.maximum(sigma, 1e-6)  # Avoid division by zero
        
        # Standardized value
        z = mu / sigma
        
        # E[max(0, Y)] = μ * Φ(z) + σ * φ(z)
        # Where Φ is CDF and φ is PDF of standard normal
        phi_z = stats.norm.cdf(z)  # CDF
        pdf_z = stats.norm.pdf(z)  # PDF
        
        expected_positive = mu * phi_z + sigma * pdf_z
        retail['yhat_energy'] = np.maximum(expected_positive, floor_eur_per_mwh)
        
        # For confidence intervals, use simpler clipping approach
        retail['yhat_energy_lower'] = np.maximum(retail['yhat_lower'] + profile_costs + risk_premium + margin, 
                                                  floor_eur_per_mwh + profile_costs + risk_premium + margin)
        retail['yhat_energy_upper'] = np.maximum(retail['yhat_upper'] + profile_costs + risk_premium + margin,
                                                  floor_eur_per_mwh + profile_costs + risk_premium + margin)
    else:
        # Simple approach: max(0, point estimate)
        retail['yhat_energy'] = np.maximum(retail['yhat'], floor_eur_per_mwh)
        
        if 'yhat_lower' in retail.columns:
            retail['yhat_energy_lower'] = np.maximum(retail['yhat_lower'], floor_eur_per_mwh)
        if 'yhat_upper' in retail.columns:
            retail['yhat_energy_upper'] = np.maximum(retail['yhat_upper'], floor_eur_per_mwh)
    
    # Add fixed components (always >= 0)
    total_markup = profile_costs + risk_premium + margin
    
    retail['yhat_retail'] = retail['yhat_energy'] + total_markup
    
    if 'yhat_energy_lower' in retail.columns:
        retail['yhat_retail_lower'] = retail['yhat_energy_lower'] + total_markup
    if 'yhat_energy_upper' in retail.columns:
        retail['yhat_retail_upper'] = retail['yhat_energy_upper'] + total_markup
    
    return retail

def train_prophet(df_hourly: pd.DataFrame, 
                 seasonality_mode: str = "multiplicative",
                 changepoint_prior_scale: float = 0.05,  # Reduced for more stable long-term trends
                 changepoint_range: float = 0.95,  # Allow changepoints throughout most of the training data
                 season_weekly: bool = True,
                 season_daily: bool = True) -> Prophet:
    """
    Train a Prophet model on hourly price data optimized for long-term forecasting
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
        # Create and configure Prophet model optimized for long-term forecasting
        model = Prophet(
            growth='flat',  # No trend - only seasonal patterns
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

def make_future_and_predict(model: Prophet, 
                          horizon_hours: int, 
                          tz: str = "Europe/Berlin",
                          return_components: bool = False) -> pd.DataFrame:
    """
    Generate and make predictions for future dates
    Args:
        model: Trained Prophet model
        horizon_hours: Number of hours to forecast
        tz: Timezone for the predictions
        return_components: Whether to return trend and seasonality components
    Returns:
        pd.DataFrame: Forecast results
    """
    try:
        logging.info(f"Generating {horizon_hours}h forecast...")
        
        # Create future dates
        future = model.make_future_dataframe(
            periods=horizon_hours,
            freq="H",
            include_history=True
        )
        
        # Make predictions (Prophet doesn't support timezones)
        forecast = model.predict(future)
        
        if return_components:
            # Add trend and seasonality components
            components = ['trend', 'weekly', 'daily', 'hourly']
            forecast = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper'] + 
                             [c for c in components if c in forecast.columns]]
        else:
            forecast = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
        
        logging.info("Forecast generated successfully")
        return forecast
        
    except Exception as e:
        logging.error(f"Error generating forecast: {str(e)}")
        raise

def plot_forecast_analysis(model: Prophet, forecast: pd.DataFrame, actual_data: pd.DataFrame):
    """Create detailed forecast analysis plots with long-term trend analysis"""
    try:
        logging.info("Creating forecast analysis plots...")
        plt.style.use('default')  # Using default style instead of seaborn
        
        # Create figures directory if it doesn't exist
        figures_dir = 'figures'
        os.makedirs(figures_dir, exist_ok=True)
        
        # Create figure with multiple subplots
        fig = plt.figure(figsize=(20, 16))  # Larger figure for more detail
    
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
        # Get overlapping dates and create a merged dataframe
        merged_df = pd.merge(
            forecast[['ds', 'yhat']], 
            actual_data[['ds', 'price_eur_per_mwh']], 
            on='ds', 
            how='inner'
        )
        
        # Calculate errors
        errors = merged_df['price_eur_per_mwh'].values - merged_df['yhat'].values
        
        ax3 = plt.subplot(3, 1, 3)
        ax3.hist(errors, bins=50, edgecolor='black')
        ax3.set_title('Forecast Error Distribution')
        ax3.set_xlabel('Error (EUR/MWh)')
        ax3.set_ylabel('Frequency')
        
        plt.tight_layout()
        save_path = os.path.join(figures_dir, 'forecast_analysis.png')
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logging.info(f"Forecast analysis plots saved to {save_path}")
        
    except Exception as e:
        logging.error(f"Error creating forecast analysis plots: {str(e)}")
        raise

def calculate_required_chunks(target_days):
    """
    Calculate how many chunks are needed for a target number of days
    Assuming each chunk contains about 1 week of data
    """
    days_per_chunk = 7
    return int(target_days / days_per_chunk) + 1  # Add 1 for safety

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
        parser.add_argument(
            "--save-eur-kwh",
            action="store_true",
            help="Also save prices in EUR/kWh"
        )
        args = parser.parse_args()

        # Use app_data directory for output
        output_dir = 'app_data'
        os.makedirs(output_dir, exist_ok=True)

        # Calculate required chunks for 2 years of data
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
        
        # Verify we have enough data
        if date_range.days < args.training_days * 0.9:  # Allow for 10% missing data
            logging.warning(f"Warning: Only got {date_range.days} days of data, "
                          f"less than the requested {args.training_days} days")
        
        # Save raw data with descriptive filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        raw_data_path = os.path.join(output_dir, f'germany_dayahead_prices_raw_{timestamp}.csv')
        df.to_csv(raw_data_path, index=False)
        logging.info(f"\nRaw data saved to {raw_data_path}")

        # Calculate EUR/kWh if requested
        if args.save_eur_kwh:
            kwh_df = to_eur_per_kwh(df)
            kwh_path = os.path.join(output_dir, f'germany_dayahead_prices_kwh_{timestamp}.csv')
            kwh_df.to_csv(kwh_path, index=False)
            logging.info(f"EUR/kWh prices saved to {kwh_path}")

        # Train Prophet model
        logging.info("Training Prophet model...")
        model = train_prophet(
            df_hourly=df,
            seasonality_mode='multiplicative',
            changepoint_prior_scale=0.2
        )

        # Generate forecast
        logging.info(f"Generating {args.horizon_hours}h forecast...")
        forecast = make_future_and_predict(
            model,
            args.horizon_hours,
            return_components=True
        )

        # Apply retail pricing (converts wholesale to realistic end-customer prices)
        logging.info("Applying retail pricing logic (probabilistic zero-censoring + markup)...")
        forecast_retail = apply_retail_pricing(
            forecast,
            profile_costs=10.0,    # 1.0 ct/kWh profile/management costs
            risk_premium=5.0,      # 0.5 ct/kWh risk premium
            margin=55.0,           # 5.5 ct/kWh supplier margin
            floor_eur_per_mwh=0.0, # No negative prices to customers
            use_probabilistic=True # Use E[max(0,Y)] instead of max(0,E[Y])
        )

        # Save wholesale forecast results with descriptive filename
        forecast_path = os.path.join(output_dir, f'germany_price_forecast_{args.horizon_hours}h.csv')
        forecast_retail.to_csv(forecast_path, index=False)
        logging.info(f"Forecast saved to {forecast_path}")

        # Create visualization
        logging.info("Generating forecast analysis plots...")
        plot_forecast_analysis(model, forecast, df)
        logging.info("Analysis plots saved to forecast_analysis.png")

        # Print forecast statistics for BOTH wholesale and retail
        future_forecast = forecast[forecast['ds'] > df['ds'].max()]
        future_retail = forecast_retail[forecast_retail['ds'] > df['ds'].max()]
        
        logging.info("\n" + "="*70)
        logging.info("WHOLESALE FORECAST (Day-Ahead Market - uncensored):")
        logging.info("="*70)
        logging.info(f"Average Price: {future_forecast['yhat'].mean():7.2f} EUR/MWh ({future_forecast['yhat'].mean()/10:5.2f} ct/kWh)")
        logging.info(f"Max Price:     {future_forecast['yhat'].max():7.2f} EUR/MWh")
        logging.info(f"Min Price:     {future_forecast['yhat'].min():7.2f} EUR/MWh")
        negative_wholesale = (future_forecast['yhat'] < 0).sum()
        logging.info(f"Negative:      {negative_wholesale:3d} hours ({negative_wholesale/len(future_forecast)*100:.1f}%)")
        
        logging.info("\n" + "="*70)
        logging.info("RETAIL FORECAST (End Customer - with business logic):")
        logging.info("="*70)
        logging.info(f"Average Energy: {future_retail['yhat_energy'].mean():7.2f} EUR/MWh ({future_retail['yhat_energy'].mean()/10:5.2f} ct/kWh)")
        logging.info(f"Average Retail: {future_retail['yhat_retail'].mean():7.2f} EUR/MWh ({future_retail['yhat_retail'].mean()/10:5.2f} ct/kWh)")
        logging.info(f"Max Price:      {future_retail['yhat_retail'].max():7.2f} EUR/MWh ({future_retail['yhat_retail'].max()/10:5.2f} ct/kWh)")
        logging.info(f"Min Price:      {future_retail['yhat_retail'].min():7.2f} EUR/MWh ({future_retail['yhat_retail'].min()/10:5.2f} ct/kWh)")
        
        zero_price = (future_retail['yhat_energy'] == 0).sum()
        if zero_price > 0:
            logging.info(f"\nFree energy hours (negative wholesale → 0): {zero_price} hours ({zero_price/len(future_retail)*100:.1f}%)")
            logging.info(f"Customer price in those hours: {70:.2f} EUR/MWh (7.0 ct/kWh) - markup only")
        
        logging.info("\n" + "="*70)
        logging.info("Note: This uses probabilistic E[max(0,Y)] calculation")
        logging.info("      instead of naive max(0, E[Y]) for unbiased estimates.")
        
        logging.info("Forecasting completed successfully!")

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        raise

def create_chart_data(historical_file=None, 
                        forecast_file='germany_price_forecast_720h.csv',
                        app_data_dir='app_data'):
    """
    Create chart data for visualization on the frontend using Chart.js.
    Reads historical and forecast data from app_data folder and resamples to daily averages.
    
    Args:
        historical_file: Name of the historical price data CSV file (if None, uses most recent)
        forecast_file: Name of the forecast data CSV file
        app_data_dir: Directory containing the data files
    
    Returns:
        dict: Dictionary with structure suitable for Chart.js containing:
            - historical_data: {timestamps, prices} daily averages of historical data
            - forecast_data: {timestamps, prices, lower_bound, upper_bound} daily averages
            - metrics: {avg_historical_price, avg_forecast_price, etc.}
            - combined_data: Full timeline combining historical and forecast
    """
    try:
        import glob
        
        # If no historical file specified, find the most recent one
        if historical_file is None:
            pattern = os.path.join(app_data_dir, 'germany_dayahead_prices_raw_*.csv')
            historical_files = glob.glob(pattern)
            if not historical_files:
                raise FileNotFoundError(f"No historical price files found matching pattern: {pattern}")
            # Sort by filename (which includes timestamp) and get the most recent
            historical_file = os.path.basename(sorted(historical_files)[-1])
            logging.info(f"Auto-selected most recent historical file: {historical_file}")
        
        # Construct file paths
        historical_path = os.path.join(app_data_dir, historical_file)
        forecast_path = os.path.join(app_data_dir, forecast_file)
        
        # Read historical data
        logging.info(f"Reading historical price data from {historical_path}")
        historical_df = pd.read_csv(historical_path)
        historical_df['ds'] = pd.to_datetime(historical_df['ds'])
        
        # Read forecast data
        logging.info(f"Reading forecast data from {forecast_path}")
        forecast_df = pd.read_csv(forecast_path)
        forecast_df['ds'] = pd.to_datetime(forecast_df['ds'])
        
        # Resample historical data to daily averages for better readability
        logging.info("Resampling data to daily averages...")
        historical_daily = historical_df.set_index('ds').resample('D').agg({
            'price_eur_per_mwh': 'mean'
        }).reset_index()
        
        # Remove any NaN values from historical data
        historical_daily = historical_daily.dropna()
        
        # Resample forecast data to daily averages
        forecast_daily = forecast_df.set_index('ds').resample('D').agg({
            'yhat': 'mean',
            'yhat_lower': 'mean',
            'yhat_upper': 'mean'
        }).reset_index()
        
        # Remove any NaN values from forecast data
        forecast_daily = forecast_daily.dropna()
        
        # Separate historical and future forecast (no overlap)
        last_historical_date = historical_daily['ds'].max()
        forecast_future_only = forecast_daily[forecast_daily['ds'] > last_historical_date].copy()
        
        # Limit forecast to exactly 30 days from the last historical date
        forecast_end_date = last_historical_date + pd.Timedelta(days=30)
        forecast_future_only = forecast_future_only[forecast_future_only['ds'] <= forecast_end_date].copy()
        
        logging.info(f"Forecast limited to 30 days: {len(forecast_future_only)} days from {forecast_future_only['ds'].min()} to {forecast_future_only['ds'].max()}")
        
        # Replace any remaining NaN/Inf values with None for JSON compatibility
        def clean_for_json(series):
            """Convert NaN and Inf values to None for JSON serialization"""
            return series.replace([np.inf, -np.inf], np.nan).where(pd.notna(series), None).tolist()
        
        # Prepare historical data for Chart.js
        historical_data = {
            'timestamps': historical_daily['ds'].dt.strftime('%Y-%m-%d').tolist(),
            'prices': [round(float(x), 2) if x is not None and not np.isnan(x) and not np.isinf(x) else None 
                        for x in historical_daily['price_eur_per_mwh']]
        }
        
        # Prepare forecast data for Chart.js
        forecast_data = {
            'timestamps': forecast_future_only['ds'].dt.strftime('%Y-%m-%d').tolist(),
            'prices': [round(float(x), 2) if x is not None and not np.isnan(x) and not np.isinf(x) else None 
                        for x in forecast_future_only['yhat']],
            'lower_bound': [round(float(x), 2) if x is not None and not np.isnan(x) and not np.isinf(x) else None 
                            for x in forecast_future_only['yhat_lower']],
            'upper_bound': [round(float(x), 2) if x is not None and not np.isnan(x) and not np.isinf(x) else None 
                            for x in forecast_future_only['yhat_upper']]
        }
        
        # Calculate metrics
        avg_historical_price = historical_daily['price_eur_per_mwh'].mean()
        avg_forecast_price = forecast_future_only['yhat'].mean()
        max_historical_price = historical_daily['price_eur_per_mwh'].max()
        max_forecast_price = forecast_future_only['yhat'].max()
        min_historical_price = historical_daily['price_eur_per_mwh'].min()
        min_forecast_price = forecast_future_only['yhat'].min()
        
        metrics = {
            'historical_period_days': len(historical_daily),
            'forecast_period_days': len(forecast_future_only),
            'avg_historical_price': float(round(avg_historical_price, 2)),
            'avg_forecast_price': float(round(avg_forecast_price, 2)),
            'max_historical_price': float(round(max_historical_price, 2)),
            'max_forecast_price': float(round(max_forecast_price, 2)),
            'min_historical_price': float(round(min_historical_price, 2)),
            'min_forecast_price': float(round(min_forecast_price, 2)),
            'price_change_percentage': float(round(
                ((avg_forecast_price - avg_historical_price) / avg_historical_price) * 100, 2
            )),
            'historical_start_date': historical_daily['ds'].min().strftime('%Y-%m-%d'),
            'historical_end_date': historical_daily['ds'].max().strftime('%Y-%m-%d'),
            'forecast_start_date': forecast_future_only['ds'].min().strftime('%Y-%m-%d'),
            'forecast_end_date': forecast_future_only['ds'].max().strftime('%Y-%m-%d')
        }
        
        # Create combined timeline for a complete view
        combined_timestamps = historical_data['timestamps'] + forecast_data['timestamps']
        combined_historical = historical_data['prices'] + [None] * len(forecast_data['timestamps'])
        combined_forecast = [None] * len(historical_data['timestamps']) + forecast_data['prices']
        
        combined_data = {
            'timestamps': combined_timestamps,
            'historical_prices': combined_historical,
            'forecast_prices': combined_forecast,
            'forecast_lower': [None] * len(historical_data['timestamps']) + forecast_data['lower_bound'],
            'forecast_upper': [None] * len(historical_data['timestamps']) + forecast_data['upper_bound']
        }
        
        logging.info(f"Chart data prepared successfully:")
        logging.info(f"  Historical: {len(historical_daily)} days ({metrics['historical_start_date']} to {metrics['historical_end_date']})")
        logging.info(f"  Forecast: {len(forecast_future_only)} days ({metrics['forecast_start_date']} to {metrics['forecast_end_date']})")
        logging.info(f"  Avg Historical Price: {avg_historical_price:.2f} EUR/MWh")
        logging.info(f"  Avg Forecast Price: {avg_forecast_price:.2f} EUR/MWh")
        logging.info(f"  Price Change: {metrics['price_change_percentage']}%")
        
        return {
            'historical_data': historical_data,
            'forecast_data': forecast_data,
            'combined_data': combined_data,
            'metrics': metrics
        }
        
    except FileNotFoundError as e:
        logging.error(f"Data file not found: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error creating chart data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def get_price_breakdown(avg_price_eur_per_mwh=None, app_data_dir='app_data'):
    """
    Calculate the breakdown of energy price components for doughnut chart.
    
    This function calculates the breakdown of electricity price components based on
    typical German electricity price structure. The percentages are based on data
    from Bundesnetzagentur.
    
    Typical German electricity price structure (approximate):
    - Generation/Wholesale: ~40% (market price from SMARD)
    - Network fees: ~25%
    - Taxes & levies: ~20% (EEG levy, electricity tax, etc.)
    - VAT: ~16%
    - Profit margin & other: ~5-10%
    
    Args:
        avg_price_eur_per_mwh: Average wholesale market price in EUR/MWh. 
                               If None, uses the average from the latest forecast file.
        app_data_dir: Directory containing the forecast data files.
    
    Returns:
        dict: Price breakdown suitable for Chart.js doughnut chart with structure:
            {
                'labels': List of component names,
                'values': List of percentage values,
                'colors': List of color codes for each component,
                'prices_eur_per_kwh': List of absolute prices in EUR/kWh,
                'total_price_eur_per_kwh': Total end-user price,
                'wholesale_price_eur_per_mwh': Wholesale market price used,
                'note': 'Explanation that percentages are from Bundesnetzagentur'
            }
    """
    try:
        # If no price provided, get average from last 24h of historical data
        if avg_price_eur_per_mwh is None:
            import glob
            from datetime import datetime, timedelta
            
            # Look for historical price data files
            historical_pattern = os.path.join(app_data_dir, 'germany_dayahead_prices_raw_*.csv')
            historical_files = glob.glob(historical_pattern)
            
            if historical_files:
                # Get the most recent historical file
                latest_historical = sorted(historical_files)[-1]
                logging.info(f"Loading historical data from {latest_historical}")
                historical_df = pd.read_csv(latest_historical)
                
                # Parse datetime column
                historical_df['ds'] = pd.to_datetime(historical_df['ds'])
                
                # Filter to last 24 hours
                now = datetime.now()
                last_24h_start = now - timedelta(hours=24)
                
                # Get data from last 24 hours
                recent_data = historical_df[historical_df['ds'] >= last_24h_start]
                
                if len(recent_data) > 0:
                    avg_price_eur_per_mwh = recent_data['price_eur_per_mwh'].mean()
                    logging.info(f"Using average price from last 24h: {avg_price_eur_per_mwh:.2f} EUR/MWh ({len(recent_data)} data points)")
                else:
                    # If no data in last 24h, use most recent available data
                    logging.warning("No data found in last 24h, using most recent 24 data points")
                    recent_data = historical_df.tail(24)
                    avg_price_eur_per_mwh = recent_data['price_eur_per_mwh'].mean()
                    logging.info(f"Using average of last 24 data points: {avg_price_eur_per_mwh:.2f} EUR/MWh")
            else:
                # Fallback to a reasonable default
                avg_price_eur_per_mwh = 100.0
                logging.warning("No historical price files found, using default price of 100 EUR/MWh")
        
        # Convert wholesale price from EUR/MWh to EUR/kWh
        wholesale_price_eur_per_kwh = avg_price_eur_per_mwh / 1000
        

        # percentages taken from bundesnetzagentur
        components = {
            'Beschaffung, Vertrieb und Marge': {
                'percentage': 43.5,
                'color': '#059669',  # Green
                'description': 'Wholesale electricity market price'
            },
            'Netzentgelte': {
                'percentage': 31.8,
                'color': '#f59e0b',  # Orange
                'description': 'Grid infrastructure and transmission costs'
            },
            'Steuern, Abgaben und weitere Umlagen': {
                'percentage': 24.7,
                'color': '#ef4444',  # Red
                'description': 'EEG levy, electricity tax, and other levies'
            }
        }
        
        # Calculate total end-user price
        # The wholesale price represents the "Beschaffung, Vertrieb und Marge" component
        # We can estimate the total price by scaling up
        wholesale_percentage = components['Beschaffung, Vertrieb und Marge']['percentage']
        estimated_total_price_eur_per_kwh = wholesale_price_eur_per_kwh * (100 / wholesale_percentage)
        
        # Calculate absolute prices for each component
        labels = []
        percentages = []
        colors = []
        prices_eur_per_kwh = []
        descriptions = []
        
        for component_name, component_data in components.items():
            labels.append(component_name)
            percentages.append(component_data['percentage'])
            colors.append(component_data['color'])
            descriptions.append(component_data['description'])
            
            # Calculate absolute price for this component
            component_price = estimated_total_price_eur_per_kwh * (component_data['percentage'] / 100)
            prices_eur_per_kwh.append(round(component_price, 4))
        
        result = {
            'labels': labels,
            'values': percentages,
            'colors': colors,
            'prices_eur_per_kwh': prices_eur_per_kwh,
            'descriptions': descriptions,
            'total_price_eur_per_kwh': round(estimated_total_price_eur_per_kwh, 4),
            'wholesale_price_eur_per_mwh': round(avg_price_eur_per_mwh, 2),
            'wholesale_price_eur_per_kwh': round(wholesale_price_eur_per_kwh, 4),
            'note': 'Component percentages are based on data from Bundesnetzagentur',
            'data_source': 'Bundesnetzagentur',
            'last_updated': None  # Can be updated when using official data
        }
        
        logging.info("Price breakdown calculated successfully:")
        logging.info(f"  Wholesale price: {avg_price_eur_per_mwh:.2f} EUR/MWh ({wholesale_price_eur_per_kwh:.4f} EUR/kWh)")
        logging.info(f"  Estimated total end-user price: {estimated_total_price_eur_per_kwh:.4f} EUR/kWh")
        logging.info(f"  Components: {len(labels)}")
        
        return result
        
    except Exception as e:
        logging.error(f"Error calculating price breakdown: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
