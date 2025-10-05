from abc import ABC, abstractmethod
from datetime import datetime, time, timedelta
from typing import Optional
import pandas as pd
from .forecasting.usage_forecasting.UsageForecaster import forecast_prophet

class EnergyTariff(ABC):
    """
    Abstract base class for electricity contracts.
    """

    def __init__(self, name: str, base_price: float, is_dynamic: bool, start_date: datetime, kwh_rate: Optional[float] = None, 
                 provider: Optional[str] = None, min_duration: Optional[int] = None, features: Optional[dict] = None):
        """
        Initialize the energy tariff.
        """
        self.name = name
        self.provider = provider
        self.min_duration = min_duration
        self.base_price = base_price
        self.kwh_rate = kwh_rate
        self.start_date = start_date
        self.is_dynamic = is_dynamic
        self.features = features if features else {}

class FixedTariff(EnergyTariff):
    """
    Represents a fixed energy tariff.
    """

    def __init__(self, name: str, base_price: float, kwh_rate: float, start_date: datetime, provider: Optional[str] = None, 
                 min_duration: Optional[int] = None, is_dynamic: bool = False):
        """
        Initialize the fixed tariff with base price and kWh rate.
        """
        super().__init__(name=name, base_price=base_price, is_dynamic=False, start_date=start_date,
                         kwh_rate=kwh_rate, provider=provider, min_duration=min_duration)

    def calculate_cost(self, data) -> float:
        """
        Calculate the total cost for a given consumption in kWh.
        """
        
        # load consumption data if provided, else use default synthetic data
        if isinstance(data, pd.DataFrame):
            # Process uploaded consumption data
            consumption_data = data.copy()
            consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
            consumption_data = consumption_data.resample('H', on='datetime').sum().reset_index()
            future_consumption = forecast_prophet(consumption_data)
        elif isinstance(data, (int, float)):
            # load synthetic data
            yearly_usage = data
            consumption_data = pd.read_csv("data/household_data/synthetic_household.csv")
            consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
            current_yearly_usage = consumption_data['value'].sum()
            adjustment_factor = yearly_usage / current_yearly_usage if current_yearly_usage > 0 else 1
            consumption_data['value'] = consumption_data['value'] * adjustment_factor
            
            future_consumption = slice_seasonal_data(consumption_data, self.start_date, days=30)
        else:
            raise ValueError("Input data must be a pandas DataFrame or a numeric yearly usage value.")
            
        # For fixed tariffs, we use 'value' column (from slice_seasonal_data) or 'yhat' column (from Prophet forecast)
        if 'yhat' in future_consumption.columns:
            total_consumption = future_consumption['yhat'].sum()
        elif 'value' in future_consumption.columns:
            total_consumption = future_consumption['value'].sum()
        else:
            raise ValueError("Expected 'yhat' or 'value' column in consumption data")
            
        total_cost = total_consumption * self.kwh_rate + self.base_price
        
        return total_cost

class DynamicTariff(EnergyTariff):
    """
    Represents a dynamic energy tariff.
    """

    def __init__(self, name: str, base_price: float, start_date: datetime, provider: Optional[str] = None, is_dynamic: bool = True):
        """
        Initialize the dynamic tariff with base price and kWh rate.
        """
        super().__init__(name, base_price=base_price, start_date=start_date, provider=provider, is_dynamic=True)

    def calculate_cost(self, data) -> float:
        """
        Calculate the total cost for a given consumption in kWh.
        """
        # load consumption data if provided, else use default synthetic data
        if isinstance(data, pd.DataFrame):
            # Process uploaded consumption data
            consumption_data = data.copy()
            consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
            consumption_data = consumption_data.resample('H', on='datetime').sum().reset_index()
            future_consumption = forecast_prophet(consumption_data)
        elif isinstance(data, (int, float)):
            # load synthetic data
            yearly_usage = data
            consumption_data = pd.read_csv("data/household_data/synthetic_household.csv")
            consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
            current_yearly_usage = consumption_data['value'].sum()
            adjustment_factor = yearly_usage / current_yearly_usage if current_yearly_usage > 0 else 1
            consumption_data['value'] = consumption_data['value'] * adjustment_factor
            
            future_consumption = slice_seasonal_data(consumption_data, self.start_date, days=30)
        else:
            raise ValueError("Input data must be a pandas DataFrame or a numeric yearly usage value.")
        
        # load price data
        future_prices = pd.read_csv("data/forecast_90days.csv")
        future_prices['datetime'] = pd.to_datetime(future_prices['datetime'])
        
        # merge consumption and price data
        future_data = future_consumption.merge(future_prices, on='datetime', how='left')
        
        # calculate total cost - handle both 'yhat' and 'value' columns
        if 'yhat' in future_data.columns:
            consumption_column = 'yhat'
        elif 'value' in future_data.columns:
            consumption_column = 'value'
        else:
            raise ValueError("Expected 'yhat' or 'value' column in consumption data")
            
        total_cost = future_data.apply(lambda row: row[consumption_column] * row['predicted_mean'], axis=1).sum() + self.base_price
        
        return total_cost

def slice_seasonal_data(df: pd.DataFrame, start_date: datetime, days: int = 30) -> pd.DataFrame:
    """
    Slice data based on day/month only (ignoring year) for seasonal patterns.
    Cycles through the year if needed.
    """
    df_copy = df.copy()
    df_copy['datetime'] = pd.to_datetime(df_copy['datetime'])
    
    # Add day/month columns for matching
    df_copy['month'] = df_copy['datetime'].dt.month
    df_copy['day'] = df_copy['datetime'].dt.day
    df_copy['hour'] = df_copy['datetime'].dt.hour
    
    result_data = []
    current_date = start_date
    
    for i in range(days):
        # Find matching day/month in the dataframe
        mask = (df_copy['month'] == current_date.month) & (df_copy['day'] == current_date.day)
        day_data = df_copy[mask].copy()
        
        if not day_data.empty:
            # Update datetime to match the target date while keeping hourly pattern
            day_data['datetime'] = day_data.apply(
                lambda row: current_date.replace(hour=row['hour']), axis=1
            )
            result_data.append(day_data[['datetime', 'value']])
        
        # Move to next day
        current_date += timedelta(days=1)
    
    if result_data:
        return pd.concat(result_data, ignore_index=True)
    else:
        return pd.DataFrame(columns=['datetime', 'value'])