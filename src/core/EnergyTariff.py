from abc import ABC, abstractmethod
from datetime import datetime, time  
from typing import Optional
import pandas as pd
import forecasting.usage_forecasting.UsageForecaster as UsageForecaster

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

    def calculate_cost(self, consumption_data: Optional[pd.DataFrame]) -> float:
        """
        Calculate the total cost for a given consumption in kWh.
        """
        
        # load consumption data if provided, else use default synthetic data
        if consumption_data is not None:
            consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
            consumption_data = consumption_data.resample('H', on='datetime').sum().reset_index()
            future_consumption = UsageForecaster.forecast_prophet(consumption_data)
        else:
            consumption_data = pd.read_csv("data/household_data/synthetic_1_person_household.csv")
            consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
            future_consumption = slice_seasonal_data(consumption_data, self.start_date, days=30)

        total_cost = future_consumption['yhat'].sum() * self.kwh_rate + self.base_price
        
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

    def calculate_cost(self, consumption_data: Optional[pd.DataFrame]) -> float:
        """
        Calculate the total cost for a given consumption in kWh.
        """
        # load consumption data if provided, else use default synthetic data
        if consumption_data is not None:
            consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
            consumption_data = consumption_data.resample('H', on='datetime').sum().reset_index()
            future_consumption = UsageForecaster.forecast_prophet(consumption_data)
        else:
            consumption_data = pd.read_csv("data/household_data/synthetic_1_person_household.csv")
            consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
            future_consumption = slice_seasonal_data(consumption_data, self.start_date, days=30)

        # load price data
        future_prices = pd.read_csv("data/forecast_90days.csv")
        future_prices['datetime'] = pd.to_datetime(future_prices['datetime'])
        
        # merge consumption and price data
        future_data = future_consumption.merge(future_prices, on='datetime', how='left')
        
        # calculate total cost
        total_cost = future_data.apply(lambda row: row['yhat'] * row['price_per_kwh'], axis=1).sum() + self.base_price
        
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
        current_date += datetime.timedelta(days=1)
    
    if result_data:
        return pd.concat(result_data, ignore_index=True)
    else:
        return pd.DataFrame(columns=['datetime', 'value'])