import pandas as pd
from datetime import datetime, time, timedelta
import os
import glob
import numpy as np


def _get_most_recent_price_file(app_data_dir: str) -> str:
    """
    Find the most recent price data file in the app_data directory.
    
    Parameters:
    app_data_dir (str): Path to the app_data directory
    
    Returns:
    str: Path to the most recent price file
    
    Raises:
    FileNotFoundError: If no price files are found
    """
    # Pattern for price files: germany_dayahead_prices_raw_YYYYMMDD_HHMMSS.csv
    pattern = os.path.join(app_data_dir, "germany_dayahead_prices_raw_*.csv")
    price_files = glob.glob(pattern)
    
    if not price_files:
        raise FileNotFoundError(f"No price data files found in {app_data_dir}")
    
    # Sort by filename (which includes timestamp) to get the most recent
    most_recent_file = sorted(price_files)[-1]
    return most_recent_file


def _get_price_forecast_file(app_data_dir: str) -> str:
    """
    Find the price forecast file in the app_data directory.
    
    Parameters:
    app_data_dir (str): Path to the app_data directory
    
    Returns:
    str: Path to the price forecast file
    
    Raises:
    FileNotFoundError: If no forecast file is found
    """
    # Look for the forecast file (static name for now)
    forecast_file = os.path.join(app_data_dir, "germany_price_forecast_720h.csv")
    
    if not os.path.exists(forecast_file):
        raise FileNotFoundError(f"Price forecast file not found: {forecast_file}")
    
    return forecast_file


def _load_historic_prices(price_file_path: str, days: int, end_date: datetime = None) -> pd.DataFrame:
    """
    Load historic price data for the last n days.
    
    Parameters:
    price_file_path (str): Path to the price data file
    days (int): Number of days to look back
    end_date (datetime): End date for the analysis period. If None, uses the most recent date in the file.
    
    Returns:
    pd.DataFrame: DataFrame with columns ['ds', 'price_eur_per_mwh', 'price_eur_per_kwh']
    """
    df = pd.read_csv(price_file_path)
    df['ds'] = pd.to_datetime(df['ds'])
    
    # Use specified end date or the latest date in the file
    if end_date is None:
        end_date = df['ds'].max()
    else:
        # Ensure end_date doesn't exceed available data
        end_date = min(end_date, df['ds'].max())
    
    # Filter to last n days from end_date
    start_date = end_date - timedelta(days=days)
    df = df[(df['ds'] >= start_date) & (df['ds'] <= end_date)].copy()
    
    # Convert price from €/MWh to €/kWh
    df['price_eur_per_kwh'] = df['price_eur_per_mwh'] / 1000
    
    return df


def _calculate_weighted_average_price(prices: pd.DataFrame, consumption: pd.DataFrame) -> dict:
    """
    Calculate the weighted average price based on consumption profile.
    
    Parameters:
    prices (pd.DataFrame): Price data with columns ['ds', 'price_eur_per_kwh']
    consumption (pd.DataFrame): Consumption data with columns ['datetime', 'value']
    
    Returns:
    dict: Contains weighted_avg_price, total_consumption, total_cost
    """
    # Ensure datetime columns are properly formatted
    prices = prices.copy()
    consumption = consumption.copy()
    
    if 'ds' in prices.columns:
        prices['datetime'] = pd.to_datetime(prices['ds'])
    
    consumption['datetime'] = pd.to_datetime(consumption['datetime'])
    
    # Resample consumption to hourly if it's not already
    time_diff = consumption['datetime'].diff().mode()[0] if len(consumption) > 1 else pd.Timedelta(hours=1)
    
    if time_diff == pd.Timedelta(minutes=15):
        # Convert 15-minute kW readings to kWh (multiply by 0.25 hours)
        consumption['value'] = consumption['value'] * 0.25
        consumption = consumption.set_index('datetime').resample('h').sum().reset_index()
    
    # Merge consumption with prices on datetime
    merged = consumption.merge(prices[['datetime', 'price_eur_per_kwh']], on='datetime', how='inner')
    
    if len(merged) == 0:
        raise ValueError("No matching timestamps between consumption and price data")
    
    # Calculate weighted average price
    merged['cost'] = merged['value'] * merged['price_eur_per_kwh']
    total_cost = merged['cost'].sum()
    total_consumption = merged['value'].sum()
    
    weighted_avg_price = total_cost / total_consumption if total_consumption > 0 else 0
    
    return {
        'weighted_avg_price': float(weighted_avg_price),
        'total_consumption': float(total_consumption),
        'total_cost': float(total_cost),
        'num_hours': int(len(merged))
    }


def create_historic_risk_analysis(consumption_data: pd.DataFrame, days: int = 30, app_data_dir: str = None) -> dict:
    """
    Perform historic risk analysis by comparing market average prices with user's weighted average price.
    
    This function analyzes how much exposure the user had to price fluctuations by comparing:
    - The simple market average price over the period
    - The weighted average price the user actually faced based on their consumption pattern
    
    Parameters:
    consumption_data (pd.DataFrame): DataFrame with user consumption data, must have 'datetime' and 'value' columns
    days (int): Number of days to analyze (default: 30)
    app_data_dir (str): Path to app_data directory. If None, uses default path
    
    Returns:
    dict: A dictionary containing:
        - market_avg_price: Simple average of all hourly prices (€/kWh)
        - user_weighted_price: Weighted average price based on consumption (€/kWh)
        - price_differential: Difference between user's price and market average (€/kWh)
        - price_differential_pct: Percentage difference
        - risk_exposure: 'favorable' if user paid less than average, 'unfavorable' if more
        - total_consumption: Total consumption over the period (kWh)
        - total_cost: Total cost over the period (€)
        - price_volatility: Standard deviation of prices over the period
        - days_analyzed: Actual number of days in the analysis
        - num_hours: Number of hours with matching price and consumption data
        - price_file_used: Name of the price data file used
    """
    # Determine app_data directory
    if app_data_dir is None:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        app_data_dir = os.path.join(project_root, "app_data")
    
    # Find and load the most recent price file
    try:
        price_file = _get_most_recent_price_file(app_data_dir)
        price_file_name = os.path.basename(price_file)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Cannot perform risk analysis: {str(e)}")
    
    # Prepare consumption data
    consumption_data = consumption_data.copy()
    consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
    
    # Determine the analysis period based on consumption data availability
    # Use the most recent data available in the consumption dataset
    consumption_end = consumption_data['datetime'].max()
    
    # Load historic prices matching the consumption timeframe
    prices = _load_historic_prices(price_file, days, end_date=consumption_end)
    
    # Filter consumption data to match the price data timeframe
    price_start = prices['ds'].min()
    price_end = prices['ds'].max()
    consumption_filtered = consumption_data[
        (consumption_data['datetime'] >= price_start) & 
        (consumption_data['datetime'] <= price_end)
    ].copy()
    
    if len(consumption_filtered) == 0:
        raise ValueError(
            f"No consumption data overlaps with price data period "
            f"({price_start.date()} to {price_end.date()}). "
            f"Consumption data range: {consumption_data['datetime'].min().date()} to {consumption_data['datetime'].max().date()}"
        )
    
    # Calculate market average price
    market_avg_price = prices['price_eur_per_kwh'].mean()
    price_volatility = prices['price_eur_per_kwh'].std()
    
    # Calculate user's weighted average price
    weighted_results = _calculate_weighted_average_price(prices, consumption_filtered)
    user_weighted_price = weighted_results['weighted_avg_price']
    
    # Calculate differential
    price_differential = user_weighted_price - market_avg_price
    price_differential_pct = (price_differential / market_avg_price * 100) if market_avg_price > 0 else 0
    
    # Determine risk exposure
    if price_differential < 0:
        risk_exposure = 'favorable'
        risk_message = f"User consumed more during low-price periods, saving {abs(price_differential_pct):.2f}%"
    else:
        risk_exposure = 'unfavorable'
        risk_message = f"User consumed more during high-price periods, paying {price_differential_pct:.2f}% more"
    
    # Calculate actual days analyzed
    days_analyzed = (price_end - price_start).days
    
    return {
        'market_avg_price': round(float(market_avg_price), 4),
        'user_weighted_price': round(float(user_weighted_price), 4),
        'price_differential': round(float(price_differential), 4),
        'price_differential_pct': round(float(price_differential_pct), 2),
        'risk_exposure': risk_exposure,
        'risk_message': risk_message,
        'total_consumption': round(float(weighted_results['total_consumption']), 2),
        'total_cost': round(float(weighted_results['total_cost']), 2),
        'price_volatility': round(float(price_volatility), 4),
        'days_analyzed': int(days_analyzed),
        'num_hours': int(weighted_results['num_hours']),
        'price_file_used': price_file_name,
        'analysis_period': {
            'start': price_start.strftime('%Y-%m-%d'),
            'end': price_end.strftime('%Y-%m-%d')
        }
    }

def calculate_coincidence_factor(consumption_data: pd.DataFrame, days: int = 30, 
                                expensive_hours_pct: float = 20.0, app_data_dir: str = None) -> dict:
    """
    Calculate the coincidence factor by analyzing how much energy usage occurred during 
    the most expensive hours in the last n days.
    
    This function identifies the most expensive X% of hours and calculates what percentage 
    of the user's total consumption occurred during those expensive periods. A high coincidence
    factor indicates that the user consumes more energy when prices are high (unfavorable),
    while a low factor suggests better consumption timing.
    
    Parameters:
    consumption_data (pd.DataFrame): DataFrame with user consumption data, must have 'datetime' and 'value' columns
    days (int): Number of days to analyze (default: 30)
    expensive_hours_pct (float): Percentage of most expensive hours to analyze (default: 20.0, range: 0-100)
    app_data_dir (str): Path to app_data directory. If None, uses default path
    
    Returns:
    dict: A dictionary containing:
        - expensive_hours_pct: Percentage threshold used for expensive hours
        - num_expensive_hours: Number of hours classified as expensive
        - total_hours: Total number of hours analyzed
        - consumption_during_expensive_hours: kWh consumed during expensive hours
        - total_consumption: Total kWh consumed
        - consumption_coincidence_pct: % of total consumption during expensive hours
        - cost_during_expensive_hours: Cost incurred during expensive hours (€)
        - total_cost: Total cost (€)
        - cost_coincidence_pct: % of total cost during expensive hours
        - avg_price_expensive_hours: Average price during expensive hours (€/kWh)
        - avg_price_cheap_hours: Average price during cheap hours (€/kWh)
        - price_threshold: Price threshold for expensive hours (€/kWh)
        - correlation: Correlation coefficient between consumption and prices
        - coincidence_rating: 'high', 'medium', or 'low' based on consumption_coincidence_pct
    """
    # Validate percentage
    if not 0 < expensive_hours_pct <= 100:
        raise ValueError(f"expensive_hours_pct must be between 0 and 100, got {expensive_hours_pct}")
    
    # Determine app_data directory
    if app_data_dir is None:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        app_data_dir = os.path.join(project_root, "app_data")
    
    # Find and load the most recent price file
    try:
        price_file = _get_most_recent_price_file(app_data_dir)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Cannot perform coincidence analysis: {str(e)}")
    
    # Prepare consumption data
    consumption_data = consumption_data.copy()
    consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
    
    # Determine the analysis period based on consumption data availability
    consumption_end = consumption_data['datetime'].max()
    
    # Load historic prices matching the consumption timeframe
    prices = _load_historic_prices(price_file, days, end_date=consumption_end)
    
    # Prepare price data
    prices = prices.copy()
    prices['datetime'] = pd.to_datetime(prices['ds'])
    
    # Filter consumption data to match the price data timeframe
    price_start = prices['datetime'].min()
    price_end = prices['datetime'].max()
    consumption_filtered = consumption_data[
        (consumption_data['datetime'] >= price_start) & 
        (consumption_data['datetime'] <= price_end)
    ].copy()
    
    if len(consumption_filtered) == 0:
        raise ValueError(
            f"No consumption data overlaps with price data period "
            f"({price_start.date()} to {price_end.date()})"
        )
    
    # Resample consumption to hourly if it's not already
    time_diff = consumption_filtered['datetime'].diff().mode()[0] if len(consumption_filtered) > 1 else pd.Timedelta(hours=1)
    
    if time_diff == pd.Timedelta(minutes=15):
        # Convert 15-minute kW readings to kWh (multiply by 0.25 hours)
        consumption_filtered['value'] = consumption_filtered['value'] * 0.25
        consumption_filtered = consumption_filtered.set_index('datetime').resample('h').sum().reset_index()
    
    # Merge consumption with prices on datetime
    merged = consumption_filtered.merge(prices[['datetime', 'price_eur_per_kwh']], on='datetime', how='inner')
    
    if len(merged) == 0:
        raise ValueError("No matching timestamps between consumption and price data")
    
    # Calculate the price threshold for expensive hours
    price_threshold = merged['price_eur_per_kwh'].quantile(1 - (expensive_hours_pct / 100))
    
    # Identify expensive hours
    merged['is_expensive'] = merged['price_eur_per_kwh'] >= price_threshold
    
    # Calculate metrics
    total_hours = len(merged)
    num_expensive_hours = merged['is_expensive'].sum()
    
    # Consumption metrics
    total_consumption = merged['value'].sum()
    consumption_expensive = merged[merged['is_expensive']]['value'].sum()
    consumption_cheap = merged[~merged['is_expensive']]['value'].sum()
    consumption_coincidence_pct = (consumption_expensive / total_consumption * 100) if total_consumption > 0 else 0
    
    # Cost metrics
    merged['cost'] = merged['value'] * merged['price_eur_per_kwh']
    total_cost = merged['cost'].sum()
    cost_expensive = merged[merged['is_expensive']]['cost'].sum()
    cost_cheap = merged[~merged['is_expensive']]['cost'].sum()
    cost_coincidence_pct = (cost_expensive / total_cost * 100) if total_cost > 0 else 0
    
    # Price metrics
    avg_price_expensive = merged[merged['is_expensive']]['price_eur_per_kwh'].mean()
    avg_price_cheap = merged[~merged['is_expensive']]['price_eur_per_kwh'].mean()
    
    # Handle NaN values (can occur if all hours are in one category)
    if pd.isna(avg_price_expensive):
        avg_price_expensive = 0.0
    if pd.isna(avg_price_cheap):
        avg_price_cheap = 0.0
    
    # Calculate correlation coefficient
    correlation = merged['value'].corr(merged['price_eur_per_kwh'])
    # Handle NaN correlation (can occur with insufficient variance)
    if pd.isna(correlation):
        correlation = 0.0
    
    # Determine coincidence rating
    if consumption_coincidence_pct > expensive_hours_pct + 10:
        coincidence_rating = 'high'
        rating_message = f"High coincidence: {consumption_coincidence_pct:.1f}% of consumption during {expensive_hours_pct:.0f}% most expensive hours (unfavorable)"
    elif consumption_coincidence_pct > expensive_hours_pct - 5:
        coincidence_rating = 'medium'
        rating_message = f"Medium coincidence: {consumption_coincidence_pct:.1f}% of consumption during {expensive_hours_pct:.0f}% most expensive hours (neutral)"
    else:
        coincidence_rating = 'low'
        rating_message = f"Low coincidence: {consumption_coincidence_pct:.1f}% of consumption during {expensive_hours_pct:.0f}% most expensive hours (favorable)"
    
    return {
        'expensive_hours_pct': float(expensive_hours_pct),
        'num_expensive_hours': int(num_expensive_hours),
        'total_hours': int(total_hours),
        'consumption_during_expensive_hours': round(float(consumption_expensive), 2),
        'consumption_during_cheap_hours': round(float(consumption_cheap), 2),
        'total_consumption': round(float(total_consumption), 2),
        'consumption_coincidence_pct': round(float(consumption_coincidence_pct), 2),
        'cost_during_expensive_hours': round(float(cost_expensive), 2),
        'cost_during_cheap_hours': round(float(cost_cheap), 2),
        'total_cost': round(float(total_cost), 2),
        'cost_coincidence_pct': round(float(cost_coincidence_pct), 2),
        'avg_price_expensive_hours': round(float(avg_price_expensive), 4),
        'avg_price_cheap_hours': round(float(avg_price_cheap), 4),
        'price_threshold': round(float(price_threshold), 4),
        'correlation': round(float(correlation), 4),
        'coincidence_rating': coincidence_rating,
        'rating_message': rating_message,
        'days_analyzed': int(days),
        'analysis_period': {
            'start': price_start.strftime('%Y-%m-%d'),
            'end': price_end.strftime('%Y-%m-%d')
        }
    }

def get_user_load_profile(consumption_data: pd.DataFrame, days: int = 30, app_data_dir: str = None) -> dict:
    """
    Analyze the user's load profile by calculating average consumption and price patterns per hour of day.
    
    This function calculates the average energy usage for each hour of the day (0-23) over the past n days,
    along with the corresponding average energy prices at those hours. This allows visualization of how
    the user's consumption pattern correlates with price patterns throughout the day.
    
    Parameters:
    consumption_data (pd.DataFrame): DataFrame with user consumption data, must have 'datetime' and 'value' columns
    days (int): Number of days to analyze (default: 30)
    app_data_dir (str): Path to app_data directory. If None, uses default path
    
    Returns:
    dict: A dictionary containing:
        - hourly_data: List of 24 objects (one per hour), each containing:
            - hour: Hour of day (0-23)
            - avg_consumption_kwh: Average consumption during this hour (kWh)
            - avg_price_eur_per_kwh: Average price during this hour (€/kWh)
            - num_data_points: Number of data points used for this hour
        - summary: Dictionary with overall statistics:
            - total_days_analyzed: Actual number of days in the analysis
            - peak_consumption_hour: Hour with highest average consumption
            - lowest_consumption_hour: Hour with lowest average consumption
            - peak_price_hour: Hour with highest average price
            - lowest_price_hour: Hour with lowest average price
            - correlation: Correlation coefficient between hourly consumption and prices
    """
    # Determine app_data directory
    if app_data_dir is None:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        app_data_dir = os.path.join(project_root, "app_data")
    
    # Find and load the most recent price file
    try:
        price_file = _get_most_recent_price_file(app_data_dir)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Cannot analyze load profile: {str(e)}")
    
    # Prepare consumption data
    consumption_data = consumption_data.copy()
    consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
    
    # Determine the analysis period based on consumption data availability
    consumption_end = consumption_data['datetime'].max()
    consumption_start = consumption_end - timedelta(days=days)
    
    # Filter consumption data to the last n days
    consumption_filtered = consumption_data[
        consumption_data['datetime'] >= consumption_start
    ].copy()
    
    if len(consumption_filtered) == 0:
        raise ValueError(f"No consumption data available for the last {days} days")
    
    # Load historic prices matching the consumption timeframe
    prices = _load_historic_prices(price_file, days, end_date=consumption_end)
    
    # Prepare price data
    prices = prices.copy()
    prices['datetime'] = pd.to_datetime(prices['ds'])
    
    # Resample consumption to hourly if needed
    time_diff = consumption_filtered['datetime'].diff().mode()[0] if len(consumption_filtered) > 1 else pd.Timedelta(hours=1)
    
    if time_diff == pd.Timedelta(minutes=15):
        # Convert 15-minute kW readings to kWh (multiply by 0.25 hours)
        consumption_filtered['value'] = consumption_filtered['value'] * 0.25
        consumption_filtered = consumption_filtered.set_index('datetime').resample('h').sum().reset_index()
    
    # Extract hour of day for consumption data
    consumption_filtered['hour'] = consumption_filtered['datetime'].dt.hour
    
    # Extract hour of day for price data
    prices['hour'] = prices['datetime'].dt.hour
    
    # Calculate average consumption by hour of day
    avg_consumption_by_hour = consumption_filtered.groupby('hour').agg({
        'value': ['mean', 'count']
    }).reset_index()
    avg_consumption_by_hour.columns = ['hour', 'avg_consumption', 'count']
    
    # Calculate average price by hour of day
    avg_price_by_hour = prices.groupby('hour')['price_eur_per_kwh'].mean().reset_index()
    avg_price_by_hour.columns = ['hour', 'avg_price']
    
    # Merge consumption and price data
    hourly_combined = avg_consumption_by_hour.merge(avg_price_by_hour, on='hour', how='outer')
    
    # Fill missing hours with 0 for consumption (prices should be complete)
    hourly_combined = hourly_combined.set_index('hour').reindex(range(24), fill_value=0).reset_index()
    hourly_combined['avg_consumption'] = hourly_combined['avg_consumption'].fillna(0)
    hourly_combined['avg_price'] = hourly_combined['avg_price'].fillna(0)
    hourly_combined['count'] = hourly_combined['count'].fillna(0).astype(int)
    
    # Build hourly data list for response
    hourly_data = []
    for _, row in hourly_combined.iterrows():
        hourly_data.append({
            'hour': int(row['hour']),
            'avg_consumption_kwh': round(float(row['avg_consumption']), 3),
            'avg_price_eur_per_kwh': round(float(row['avg_price']), 4),
            'num_data_points': int(row['count'])
        })
    
    # Calculate summary statistics
    # Find peak and lowest consumption hours
    max_consumption_idx = hourly_combined['avg_consumption'].idxmax()
    min_consumption_idx = hourly_combined['avg_consumption'].idxmin()
    peak_consumption_hour = int(hourly_combined.loc[max_consumption_idx, 'hour'])
    lowest_consumption_hour = int(hourly_combined.loc[min_consumption_idx, 'hour'])
    
    # Find peak and lowest price hours
    max_price_idx = hourly_combined['avg_price'].idxmax()
    min_price_idx = hourly_combined['avg_price'].idxmin()
    peak_price_hour = int(hourly_combined.loc[max_price_idx, 'hour'])
    lowest_price_hour = int(hourly_combined.loc[min_price_idx, 'hour'])
    
    # Calculate correlation between hourly consumption and prices
    # Filter out hours with no consumption data
    hourly_with_data = hourly_combined[hourly_combined['avg_consumption'] > 0].copy()
    if len(hourly_with_data) > 1:
        correlation = hourly_with_data['avg_consumption'].corr(hourly_with_data['avg_price'])
        # Handle NaN correlation (can occur with insufficient variance)
        if pd.isna(correlation):
            correlation = 0.0
    else:
        correlation = 0.0
    
    # Calculate actual days analyzed
    actual_days = (consumption_filtered['datetime'].max() - consumption_filtered['datetime'].min()).days
    
    return {
        'hourly_data': hourly_data,
        'summary': {
            'total_days_analyzed': int(actual_days),
            'peak_consumption_hour': int(peak_consumption_hour),
            'lowest_consumption_hour': int(lowest_consumption_hour),
            'peak_price_hour': int(peak_price_hour),
            'lowest_price_hour': int(lowest_price_hour),
            'correlation': round(float(correlation), 4),
            'analysis_period': {
                'start': consumption_filtered['datetime'].min().strftime('%Y-%m-%d'),
                'end': consumption_filtered['datetime'].max().strftime('%Y-%m-%d')
            }
        }
    }

def get_price_forecast_volatility(app_data_dir: str = None) -> dict:
    """
    Analyze price forecast volatility by reading the most recent forecast data.
    
    This function loads the most recent price forecast file from the app_data directory
    and calculates two key volatility metrics.
    
    Parameters:
    app_data_dir (str): Path to app_data directory. If None, uses default path
    
    Returns:
    dict: Contains:
        - forecast_std_dev: Standard deviation of forecasted prices (€/kWh)
        - avg_confidence_interval_width: Average width of confidence intervals if available (€/kWh), None otherwise
    
    Raises:
    FileNotFoundError: If no forecast files are found
    """
    # Determine app_data directory
    if app_data_dir is None:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        app_data_dir = os.path.join(project_root, "app_data")
    
    # Find the price forecast file
    try:
        forecast_file = _get_price_forecast_file(app_data_dir)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Cannot analyze price forecast volatility: {str(e)}")
    
    # Load the forecast data
    df = pd.read_csv(forecast_file)
    
    # Check for required columns
    if 'ds' not in df.columns:
        raise ValueError(f"Forecast file must have 'ds' (datetime) column. Found columns: {df.columns.tolist()}")
    
    # Convert datetime
    df['ds'] = pd.to_datetime(df['ds'])
    
    # Determine price column (could be different names)
    price_col = None
    for col in ['price_eur_per_mwh', 'yhat', 'forecast', 'price']:
        if col in df.columns:
            price_col = col
            break
    
    if price_col is None:
        raise ValueError(f"No price column found in forecast file. Available columns: {df.columns.tolist()}")
    
    # Convert price to €/kWh if it's in €/MWh
    # Check both column name and value range to determine if conversion is needed
    # Prices in €/MWh are typically > 10, while €/kWh are typically < 1
    mean_price = df[price_col].mean()
    if 'mwh' in price_col.lower() or mean_price > 10:
        # Prices are in €/MWh, convert to €/kWh
        df['price_eur_per_kwh'] = df[price_col] / 1000
    else:
        # Already in €/kWh
        df['price_eur_per_kwh'] = df[price_col]
    
    # Calculate standard deviation
    forecast_std = df['price_eur_per_kwh'].std()
    
    # Check for confidence interval columns
    avg_ci_width = None
    lower_col = None
    upper_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'lower' in col_lower or 'yhat_lower' in col_lower:
            lower_col = col
        if 'upper' in col_lower or 'yhat_upper' in col_lower:
            upper_col = col
    
    if lower_col and upper_col:
        # Convert confidence intervals from €/MWh to €/kWh
        df['lower_kwh'] = df[lower_col] / 1000
        df['upper_kwh'] = df[upper_col] / 1000
        
        # Calculate average confidence interval width
        df['ci_width'] = df['upper_kwh'] - df['lower_kwh']
        avg_ci_width = df['ci_width'].mean()
    
    return {
        'forecast_std_dev': round(float(forecast_std), 4),
        'avg_confidence_interval_width': round(float(avg_ci_width), 4) if avg_ci_width is not None else None
    }

    


def get_simplified_risk_score_for_yearly_usage(forecast_price_volatility: dict, is_dynamic: bool, 
                                                historic_price_volatility: float = None) -> dict:
    """
    Calculate a simplified risk score when only yearly usage is provided (no CSV uploaded).
    
    Since we don't have actual consumption patterns, we can only assess risk based on:
    - Price volatility (both historic and forecasted) for dynamic tariffs
    - Fixed tariff advantage (inherently lower risk)
    
    Parameters:
    forecast_price_volatility (dict): Output from price volatility analysis
    is_dynamic (bool): Whether the tariff is dynamic
    historic_price_volatility (float): Optional historic price volatility from market data
    
    Returns:
    dict: Contains risk_level, risk_score, risk_message, risk_factors, simplified flag
    """
    score = 40  # Start with moderate baseline
    factors = []
    
    if is_dynamic:
        # For dynamic tariffs without consumption data, risk is primarily about price uncertainty
        price_std_dev = forecast_price_volatility.get('forecast_std_dev', None)
        
        if price_std_dev is not None:
            # Assess based on forecasted price volatility
            if price_std_dev > 0.05:
                score += 15
                factors.append({
                    'factor': 'Preisvolatilität (Prognose)', 
                    'impact': 'negative', 
                    'detail': f'Sehr hohe erwartete Preisschwankungen (σ: {price_std_dev:.4f} €/kWh)'
                })
            elif price_std_dev > 0.035:
                score += 8
                factors.append({
                    'factor': 'Preisvolatilität (Prognose)', 
                    'impact': 'negative', 
                    'detail': f'Hohe erwartete Preisschwankungen (σ: {price_std_dev:.4f} €/kWh)'
                })
            elif price_std_dev > 0.025:
                score += 3
                factors.append({
                    'factor': 'Preisvolatilität (Prognose)', 
                    'impact': 'neutral', 
                    'detail': f'Moderate erwartete Preisschwankungen (σ: {price_std_dev:.4f} €/kWh)'
                })
            else:
                score -= 5
                factors.append({
                    'factor': 'Preisvolatilität (Prognose)', 
                    'impact': 'positive', 
                    'detail': f'Niedrige erwartete Preisschwankungen (σ: {price_std_dev:.4f} €/kWh)'
                })
        
        # Add historic price volatility if available
        if historic_price_volatility is not None:
            if historic_price_volatility > 0.06:
                score += 10
                factors.append({
                    'factor': 'Historische Preisvolatilität', 
                    'impact': 'negative', 
                    'detail': f'Sehr hohe historische Preisschwankungen (σ: {historic_price_volatility:.4f} €/kWh)'
                })
            elif historic_price_volatility > 0.045:
                score += 6
                factors.append({
                    'factor': 'Historische Preisvolatilität', 
                    'impact': 'negative', 
                    'detail': f'Hohe historische Preisschwankungen (σ: {historic_price_volatility:.4f} €/kWh)'
                })
            elif historic_price_volatility > 0.03:
                score += 2
                factors.append({
                    'factor': 'Historische Preisvolatilität', 
                    'impact': 'neutral', 
                    'detail': f'Moderate historische Preisschwankungen (σ: {historic_price_volatility:.4f} €/kWh)'
                })
            else:
                score -= 4
                factors.append({
                    'factor': 'Historische Preisvolatilität', 
                    'impact': 'positive', 
                    'detail': f'Niedrige historische Preisschwankungen (σ: {historic_price_volatility:.4f} €/kWh)'
                })
        
        factors.append({
            'factor': 'Verbrauchsdaten', 
            'impact': 'neutral', 
            'detail': 'Keine individuellen Verbrauchsdaten - Bewertung basiert auf Standardlastprofil'
        })
    else:
        # Fixed tariffs are inherently lower risk
        score -= 20
        factors.append({
            'factor': 'Tariftyp', 
            'impact': 'positive', 
            'detail': 'Fester Tarif - Keine Preisschwankungen'
        })
    
    # Ensure score is within bounds
    overall_risk_score = max(0, min(100, score))
    
    # Determine risk level and message
    if overall_risk_score <= 30:
        risk_level = 'low'
        if is_dynamic:
            risk_message = 'Niedriges Risiko: Geringe erwartete Preisvolatilität macht dynamische Tarife attraktiv'
        else:
            risk_message = 'Niedriges Risiko: Fester Tarif bietet volle Preissicherheit'
    elif overall_risk_score <= 50:
        risk_level = 'moderate'
        if is_dynamic:
            risk_message = 'Moderates Risiko: Moderate Preisschwankungen erwartet. Empfehlung: Verbrauchsdaten für genauere Analyse hochladen'
        else:
            risk_message = 'Moderates Risiko: Fester Tarif bietet Preissicherheit'
    else:
        risk_level = 'high'
        if is_dynamic:
            risk_message = 'Höheres Risiko: Hohe Preisvolatilität erwartet. Bitte Verbrauchsdaten hochladen für detaillierte Analyse'
        else:
            risk_message = 'Moderates Risiko: Fester Tarif bietet stabile Preise'
    
    return {
        'risk_level': risk_level,
        'risk_score': int(overall_risk_score),
        'risk_message': risk_message,
        'risk_factors': factors,
        'forecast_quality_included': False,
        'simplified': True,
        'note': 'Vereinfachte Risikobewertung basierend auf Standardlastprofil. Für genauere Analyse bitte Verbrauchsdaten hochladen.'
    }
    
    
def get_aggregated_risk_score(historic_risk_analysis: dict, coincidence_factor: dict, forecast_price_volatility: dict,
                              is_dynamic: bool, usage_forecast_quality: dict = None) -> dict:
    """
    Aggregate the risk analysis results into a simple risk assessment.
    
    This function combines the outputs from historic risk analysis, coincidence factor
    calculations, and forecast quality metrics to provide an overall risk assessment for the user.
    
    Parameters:
    historic_risk_analysis (dict): Output from create_historic_risk_analysis function
    coincidence_factor (dict): Output from calculate_coincidence_factor function
    forecast_price_volatility (dict): Output from price volatility analysis
    is_dynamic (bool): Whether the tariff is dynamic
    usage_forecast_quality (dict): Optional. Quality metrics from backtest (includes avg_confidence_interval_width, 
                                    relative_confidence_interval_width, mae, forecast_error_percentage)
    
    Returns:
    dict: Contains:
        - risk_level: 'low', 'moderate', or 'high'
        - risk_score: numeric score (0-100, lower is better)
        - risk_message: human-readable explanation
        - risk_factors: breakdown of contributing factors
        - forecast_quality_included: boolean indicating if forecast quality was factored in
    """
    # Initialize score (lower is better/less risky)
    # Start with a lower baseline to allow for more differentiation
    score = 35  # Start at lower baseline for better differentiation
    factors = []
    
    # For fixed tariffs, skip consumption-pattern-based risk factors
    # since prices don't vary with market conditions
    if is_dynamic:
        # Adjust score based on historic risk analysis
        # Using more granular thresholds to better differentiate user patterns
        price_diff_pct = historic_risk_analysis.get('price_differential_pct', 0)
        if price_diff_pct < -10:
            score -= 12  # Very favorable - excellent consumption timing
            factors.append({'factor': 'Historischer Verbrauch', 'impact': 'positive', 'detail': f'{abs(price_diff_pct):.1f}% unter Marktdurchschnitt'})
        elif price_diff_pct < -5:
            score -= 8  # Favorable - good consumption timing
            factors.append({'factor': 'Historischer Verbrauch', 'impact': 'positive', 'detail': f'{abs(price_diff_pct):.1f}% unter Marktdurchschnitt'})
        elif -5 <= price_diff_pct <= 5:
            score += 0  # Neutral - no adjustment
            factors.append({'factor': 'Historischer Verbrauch', 'impact': 'neutral', 'detail': 'Im Marktdurchschnitt'})
        elif price_diff_pct <= 10:
            score += 8  # Slightly unfavorable
            factors.append({'factor': 'Historischer Verbrauch', 'impact': 'negative', 'detail': f'{price_diff_pct:.1f}% über Marktdurchschnitt'})
        else:
            score += 12  # Very unfavorable - poor consumption timing
            factors.append({'factor': 'Historischer Verbrauch', 'impact': 'negative', 'detail': f'{price_diff_pct:.1f}% über Marktdurchschnitt'})
        
        # Adjust score based on coincidence factor
        # More nuanced thresholds to capture different consumption patterns
        consumption_coincidence = coincidence_factor.get('consumption_coincidence_pct', 0)
        expensive_hours_pct = coincidence_factor.get('expensive_hours_pct', 20.0)
        
        # Calculate how much the user deviates from the expensive hours percentage
        coincidence_deviation = consumption_coincidence - expensive_hours_pct
        
        if coincidence_deviation < -10:
            score -= 12  # Excellent - significantly avoids expensive hours
            factors.append({'factor': 'Verbrauchstiming', 'impact': 'positive', 'detail': 'Vermeidet teure Stunden deutlich'})
        elif coincidence_deviation < -5:
            score -= 8  # Good - avoids expensive hours
            factors.append({'factor': 'Verbrauchstiming', 'impact': 'positive', 'detail': 'Vermeidet teure Stunden'})
        elif -5 <= coincidence_deviation <= 5:
            score += 0  # Neutral - typical pattern, no adjustment
            factors.append({'factor': 'Verbrauchstiming', 'impact': 'neutral', 'detail': 'Typisches Verbrauchsmuster'})
        elif coincidence_deviation <= 15:
            score += 8  # Slightly unfavorable
            factors.append({'factor': 'Verbrauchstiming', 'impact': 'negative', 'detail': 'Erhöhter Verbrauch zu teuren Zeiten'})
        else:
            score += 12  # Very unfavorable - high consumption during expensive hours
            factors.append({'factor': 'Verbrauchstiming', 'impact': 'negative', 'detail': 'Hoher Verbrauch zu teuren Zeiten'})
        
        # Check price volatility with adjusted thresholds
        volatility = historic_risk_analysis.get('price_volatility', 0)
        if volatility > 0.06:  # Very high volatility (>6 ct/kWh std dev)
            score += 8
            factors.append({'factor': 'Preisvolatilität', 'impact': 'negative', 'detail': 'Sehr hohe Preisschwankungen'})
        elif volatility > 0.045:  # High volatility
            score += 5
            factors.append({'factor': 'Preisvolatilität', 'impact': 'negative', 'detail': 'Hohe Preisschwankungen'})
        elif volatility > 0.03:  # Medium volatility
            score += 2
            factors.append({'factor': 'Preisvolatilität', 'impact': 'neutral', 'detail': 'Moderate Preisschwankungen'})
        else:
            score -= 3  # Low volatility is favorable
            factors.append({'factor': 'Preisvolatilität', 'impact': 'positive', 'detail': 'Niedrige Preisschwankungen'})
    
    # Adjust score based on forecast quality (if provided)
    forecast_quality_included = False
    if usage_forecast_quality:
        forecast_quality_included = True
        
        # Prioritize forecast_error_percentage as it's more reliable than relative CI width
        # (relative CI width can be misleading for low-consumption households)
        forecast_error_pct = usage_forecast_quality.get('forecast_error_percentage', None)
        relative_ci_width = usage_forecast_quality.get('relative_confidence_interval_width', None)
        
        if forecast_error_pct is not None:
            # Use forecast error percentage as primary metric (most reliable)
            # Lower error = better predictions = lower risk
            
            if forecast_error_pct < 10:
                # Excellent forecast quality - significantly reduces risk
                score -= 8
                factors.append({
                    'factor': 'Prognosequalität', 
                    'impact': 'positive', 
                    'detail': f'Sehr hohe Vorhersagegenauigkeit (Fehler: {forecast_error_pct:.1f}%)'
                })
            elif forecast_error_pct < 20:
                # Good forecast quality - reduces risk
                score -= 4
                factors.append({
                    'factor': 'Prognosequalität', 
                    'impact': 'positive', 
                    'detail': f'Gute Vorhersagegenauigkeit (Fehler: {forecast_error_pct:.1f}%)'
                })
            elif forecast_error_pct < 30:
                # Fair forecast quality - slight risk increase
                score += 3
                factors.append({
                    'factor': 'Prognosequalität', 
                    'impact': 'neutral', 
                    'detail': f'Moderate Vorhersageunsicherheit (Fehler: {forecast_error_pct:.1f}%)'
                })
            else:
                # Poor forecast quality - increases risk
                score += 10
                factors.append({
                    'factor': 'Prognosequalität', 
                    'impact': 'negative', 
                    'detail': f'Hohe Vorhersageunsicherheit (Fehler: {forecast_error_pct:.1f}%)'
                })
        
        elif relative_ci_width is not None:
            # Fallback to relative confidence interval width if forecast error not available
            # Note: This can be misleading for low-consumption households
            # Adjusted ranges to be more lenient
            
            if relative_ci_width < 40:
                # Excellent forecast quality - reduces risk for dynamic tariffs
                score -= 8
                factors.append({
                    'factor': 'Prognosequalität', 
                    'impact': 'positive', 
                    'detail': f'Sehr hohe Vorhersagegenauigkeit (CI: {relative_ci_width:.1f}%)'
                })
            elif relative_ci_width < 80:
                # Good forecast quality - slight risk reduction
                score -= 4
                factors.append({
                    'factor': 'Prognosequalität', 
                    'impact': 'positive', 
                    'detail': f'Gute Vorhersagegenauigkeit (CI: {relative_ci_width:.1f}%)'
                })
            elif relative_ci_width < 120:
                # Fair forecast quality - neutral to slight risk increase
                score += 3
                factors.append({
                    'factor': 'Prognosequalität', 
                    'impact': 'neutral', 
                    'detail': f'Moderate Vorhersageunsicherheit (CI: {relative_ci_width:.1f}%)'
                })
            else:
                # Poor forecast quality - increases risk
                score += 10
                factors.append({
                    'factor': 'Prognosequalität', 
                    'impact': 'negative', 
                    'detail': f'Hohe Vorhersageunsicherheit (CI: {relative_ci_width:.1f}%)'
                })
    
    # Adjust score based on price forecast volatility (ONLY for dynamic tariffs)
    # Price volatility doesn't matter for fixed tariffs since they have fixed rates
    if is_dynamic and forecast_price_volatility:
        price_std_dev = forecast_price_volatility.get('forecast_std_dev', None)
        price_ci_width = forecast_price_volatility.get('avg_confidence_interval_width', None)
        
        if price_std_dev is not None:
            # Standard deviation thresholds (in €/kWh)
            # Adjusted thresholds: Low: <0.025, Medium: 0.025-0.045, High: >0.045
            
            if price_std_dev > 0.05:
                # Very high price volatility increases risk significantly
                score += 8
                factors.append({
                    'factor': 'Preisvolatilität (Prognose)', 
                    'impact': 'negative', 
                    'detail': f'Sehr hohe erwartete Preisschwankungen (σ: {price_std_dev:.4f} €/kWh)'
                })
            elif price_std_dev > 0.035:
                # High price volatility
                score += 5
                factors.append({
                    'factor': 'Preisvolatilität (Prognose)', 
                    'impact': 'negative', 
                    'detail': f'Hohe erwartete Preisschwankungen (σ: {price_std_dev:.4f} €/kWh)'
                })
            elif price_std_dev > 0.025:
                # Medium price volatility
                score += 2
                factors.append({
                    'factor': 'Preisvolatilität (Prognose)', 
                    'impact': 'neutral', 
                    'detail': f'Moderate erwartete Preisschwankungen (σ: {price_std_dev:.4f} €/kWh)'
                })
            else:
                # Low price volatility reduces risk
                score -= 3
                factors.append({
                    'factor': 'Preisvolatilität (Prognose)', 
                    'impact': 'positive', 
                    'detail': f'Niedrige erwartete Preisschwankungen (σ: {price_std_dev:.4f} €/kWh)'
                })
        
        # Additional check for confidence interval width if available
        # CI width reflects forecast uncertainty (±half the width from the mean)
        # E.g., 0.15 €/kWh (150 €/MWh) means ±75 €/MWh uncertainty
        if price_ci_width is not None:
            if price_ci_width > 0.20:
                # Very wide confidence intervals (>200 €/MWh) indicate very high uncertainty
                score += 10
                factors.append({
                    'factor': 'Preisprognose-Unsicherheit', 
                    'impact': 'negative', 
                    'detail': f'Sehr hohe Unsicherheit in Preisprognose (Breite Konfidenzintervall: {price_ci_width:.4f} €/kWh)'
                })
            elif price_ci_width > 0.12:
                # Wide confidence intervals (>120 €/MWh) indicate high uncertainty
                # This includes typical values around 150-180 €/MWh
                score += 6
                factors.append({
                    'factor': 'Preisprognose-Unsicherheit', 
                    'impact': 'negative', 
                    'detail': f'Hohe Prognoseunsicherheit (Breite Konfidenzintervall: {price_ci_width:.4f} €/kWh)'
                })
            elif price_ci_width > 0.08:
                # Medium confidence intervals (80-120 €/MWh) - moderate uncertainty
                score += 3
                factors.append({
                    'factor': 'Preisprognose-Unsicherheit', 
                    'impact': 'neutral', 
                    'detail': f'Moderate Prognoseunsicherheit (Breite Konfidenzintervall: {price_ci_width:.4f} €/kWh)'
                })
            else:
                # Narrow confidence intervals (<80 €/MWh) indicate good forecast quality
                score -= 3
                factors.append({
                    'factor': 'Preisprognose-Qualität', 
                    'impact': 'positive', 
                    'detail': f'Gute Prognosequalität (Breite Konfidenzintervall: {price_ci_width:.4f} €/kWh)'
                })
            
    # Adjust score for fixed tariffs
    if not is_dynamic:
        score -= 20  # Fixed tariffs are less risky (reduced from 25)
        factors.append({'factor': 'Tariftyp', 'impact': 'positive', 'detail': 'Fester Tarif'})
    
    # Ensure score is within bounds (0-100, lower is better)
    overall_risk_score = max(0, min(100, score))
    
    # Determine risk level and message with adjusted thresholds
    # Lower thresholds to account for lower starting baseline
    if overall_risk_score <= 30:
        risk_level = 'low'
        if forecast_quality_included:
            risk_message = 'Niedriges Risiko: Ihr Verbrauchsprofil und zuverlässige Prognosen eignen sich gut für dynamische Tarife'
        else:
            risk_message = 'Niedriges Risiko: Ihr Verbrauchsprofil eignet sich gut für dynamische Tarife'
    elif overall_risk_score <= 50:
        risk_level = 'moderate'
        if forecast_quality_included:
            risk_message = 'Moderates Risiko: Dynamische Tarife können vorteilhaft sein. Berücksichtigen Sie die Prognosequalität'
        else:
            risk_message = 'Moderates Risiko: Dynamische Tarife können für Sie vorteilhaft sein, aber Optimierung empfohlen'
    else:
        risk_level = 'high'
        if forecast_quality_included:
            risk_message = 'Höheres Risiko: Unsichere Prognosen und ungünstiges Verbrauchsmuster erhöhen das Risiko'
        else:
            risk_message = 'Höheres Risiko: Überprüfen Sie, ob Sie Ihren Verbrauch zu günstigeren Zeiten verschieben können'
    
    return {
        'risk_level': risk_level,
        'risk_score': int(overall_risk_score),
        'risk_message': risk_message,
        'risk_factors': factors,
        'forecast_quality_included': forecast_quality_included
    }