from typing import Optional
import pandas as pd
import EnergyTariff
import datetime
import forecasting.usage_forecasting.UsageForecaster as UsageForecaster
from datetime import datetime


def calculate_tariff_costs(tariff: EnergyTariff, usage_data: Optional[pd.DataFrame], household_size: Optional[int] = None) -> float:
    # function to calculate costs based on usage data and tariff
    
    if tariff.is_dynamic:
        
        if usage_data is None:
            raise ValueError("Usage data must be provided for dynamic tariffs.")
        
        # Dynamic tariff cost calculation logic
        start_date = tariff.start_date
        
        # Assuming price_data is available for dynamic tariffs
        price_data = pd.read_csv("data/price_data/dynamic_price_data.csv")
        price_data['datetime'] = pd.to_datetime(price_data['datetime'])
        
        future_usage = UsageForecaster.forecast_prophet(usage_data)

        future_usage = future_usage.merge(price_data, on='datetime', how='left')

        future_usage["hourly_price"] = future_usage["price_per_kwh"] * future_usage["yhat"]

        costs = future_usage["hourly_price"].sum() + tariff.base_price
        
        return costs

    else:
        # Fixed tariff cost calculation logic
        if household_size is None:
            raise ValueError("Household size must be provided for fixed tariffs.")
        
        match household_size:
            case 1:
                consumption_data = pd.read_csv("data/household_data/synthetic_1_person_household.csv")
            case 2:
                consumption_data = pd.read_csv("data/household_data/synthetic_2_person_household.csv")
            case 3:
                consumption_data = pd.read_csv("data/household_data/synthetic_3_person_household.csv")

        start_date = tariff.start_date
        
        # Get 30 days of consumption data using seasonal pattern
        sliced_data = slice_seasonal_data(consumption_data, start_date, days=30)
        
        # Calculate total costs
        total_consumption = sliced_data['value'].sum()
        costs = tariff.base_price + (total_consumption * tariff.kwh_rate)
        
    return costs

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