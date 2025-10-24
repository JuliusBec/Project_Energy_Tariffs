from abc import ABC, abstractmethod
from datetime import datetime, time, timedelta
from typing import Optional
import pandas as pd
from .forecasting.usage_forecasting.UsageForecaster import forecast_prophet
from calendar import monthrange
import os

class EnergyTariff(ABC):
    """
    Abstract base class for electricity contracts.
    """

    def __init__(self, name: str, base_price: float, is_dynamic: bool, start_date: datetime, kwh_rate: Optional[float] = None, 
                 provider: Optional[str] = None, min_duration: Optional[int] = None, features: Optional[list] = None):
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
        self.features = features if features else []

    def calculate_billing_period_days(self) -> int:
        """
        Calculate actual billing period in days based on German monthly billing practices.
        Handles month-end adjustments and varying month lengths.
        
        Returns:
            int: Number of days in the billing period
        """

        start_day = self.start_date.day
        start_month = self.start_date.month
        start_year = self.start_date.year
        
        # Determine next billing date following German energy contract standards
        if start_month == 12:
            next_month = 1
            next_year = start_year + 1
        else:
            next_month = start_month + 1
            next_year = start_year
            
        # Handle month-end billing adjustments
        days_in_start_month = monthrange(start_year, start_month)[1]
        days_in_next_month = monthrange(next_year, next_month)[1]
        
        if start_day == days_in_start_month:  # Started on last day of month
            # Bill on last day of next month (German end-of-month rule)
            next_billing_day = days_in_next_month
        else:
            # Bill on same day next month, adjust if day doesn't exist
            next_billing_day = min(start_day, days_in_next_month)
            
        # Calculate actual billing period days
        next_billing_date = datetime(next_year, next_month, next_billing_day)
        return (next_billing_date - self.start_date).days
    
    @abstractmethod
    def calculate_cost_split(self, total_consumption_kwh: float) -> dict:
        """
        Calculate the total cost breakdown for given consumption.
        
        Args:
            total_consumption_kwh: Total energy consumption in kWh (from forecast or historical data)
            
        Returns:
            dict: Breakdown of costs including base_price, variable_cost, total_cost, etc.
        """
        pass

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

    def calculate_cost_split(self, total_consumption_kwh: float) -> dict:
        """
        Calculate cost breakdown for fixed tariff.
        Returns base price, variable cost, and total cost breakdown.
        
        Args:
            total_consumption_kwh: Total energy consumption in kWh (from forecast or historical data)
            
        Returns:
            dict: Breakdown of costs including base_price, variable_cost, total_cost, etc.
        """
        # Calculate actual billing period based on German monthly billing practices
        billing_period_days = self.calculate_billing_period_days()
        
        # Calculate costs
        variable_cost = total_consumption_kwh * self.kwh_rate
        total_cost = variable_cost + self.base_price
        
        return {
            "base_price": self.base_price,
            "variable_cost": variable_cost,
            "total_cost": total_cost,
            "total_consumption_kwh": total_consumption_kwh,
            "fixed_kwh_rate": self.kwh_rate,
            "billing_period_days": billing_period_days
        }

    def calculate_cost(self, data) -> float:
        """
        Calculate the total cost for a given consumption in kWh.
        """
        import os
        
        # Calculate actual billing period based on German monthly billing practices
        billing_period_days = self.calculate_billing_period_days()
        
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # load consumption data if provided, else use default synthetic data
        if isinstance(data, pd.DataFrame):
            # Process uploaded consumption data
            consumption_data = data.copy()
            consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
            consumption_data = consumption_data.resample('H', on='datetime').sum().reset_index()
            future_consumption = forecast_prophet(consumption_data)
        elif isinstance(data, (int, float)):
            # load standard load profile data
            yearly_usage = data
            standard_profile_path = os.path.join(project_root, "app_data", "standard_profile", "Standard_Load_Profile_2025_2026.csv")
            consumption_data = pd.read_csv(standard_profile_path)
            consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
            current_yearly_usage = consumption_data['value'].sum()
            adjustment_factor = yearly_usage / current_yearly_usage if current_yearly_usage > 0 else 1
            consumption_data['value'] = consumption_data['value'] * adjustment_factor
            
            future_consumption = slice_seasonal_data(consumption_data, self.start_date, days=billing_period_days)
        else:
            raise ValueError("Input data must be a pandas DataFrame or a numeric yearly usage value.")
            
        # For fixed tariffs, we use 'value' column (from slice_seasonal_data) or 'yhat' column (from Prophet forecast)
        if 'yhat' in future_consumption.columns:
            total_consumption = future_consumption['yhat'].sum()
        elif 'value' in future_consumption.columns:
            total_consumption = future_consumption['value'].sum()
        else:
            raise ValueError("Expected 'yhat' or 'value' column in consumption data")
            
        total_cost = (total_consumption * self.kwh_rate) + self.base_price
        
        return total_cost



class DynamicTariff(EnergyTariff):
    """
    Represents a dynamic energy tariff.
    """

    def __init__(self, name: str, base_price: float, start_date: datetime, provider: Optional[str] = None, is_dynamic: bool = True, markup: float = 0.20):
        """
        Initialize the dynamic tariff with base price and markup.
        
        Args:
            name: Name of the tariff
            base_price: Monthly base price in €
            start_date: Start date for the tariff
            provider: Energy provider name
            is_dynamic: Whether this is a dynamic tariff (always True for this class)
            markup: Markup added to wholesale prices in €/kWh (default 0.20 for grid fees, taxes, etc.)
        """
        super().__init__(name, base_price=base_price, start_date=start_date, provider=provider, is_dynamic=True)
        self.markup = markup  # €/kWh markup added to wholesale prices

    def _get_average_forecast_price(self) -> float:
        """
        Get average price from the latest forecast data.
        Returns a default value if forecast data is not available.
        """
        import os
        try:
            # Get the project root directory
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            app_data_path = os.path.join(project_root, "app_data")
            
            # Find the most recent price forecast file
            forecast_files = [f for f in os.listdir(app_data_path) if f.startswith('germany_price_forecast_') and f.endswith('.csv')]
            if not forecast_files:
                return 0.25  # Default fallback price in €/kWh
            
            # Sort by filename to get the most recent
            latest_forecast_file = sorted(forecast_files)[-1]
            price_data_path = os.path.join(app_data_path, latest_forecast_file)
            
            forecast_data = pd.read_csv(price_data_path)
            
            if 'yhat' in forecast_data.columns:
                # Convert €/MWh to €/kWh and add markup, then return average
                return (forecast_data['yhat'].mean() / 1000) + self.markup
            else:
                return 0.25  # Default fallback price in €/kWh
                
        except Exception:
            return 0.25  # Default fallback price in €/kWh

    def calculate_cost_split(self, total_consumption_kwh: float) -> dict:
        """
        Calculate cost breakdown for dynamic tariff.
        For dynamic tariffs, this is a simplified version that doesn't include 
        time-dependent pricing details since those require the actual consumption timeline.
        
        Args:
            total_consumption_kwh: Total energy consumption in kWh
            
        Returns:
            dict: Basic breakdown with estimated average price
        """
        # For dynamic tariffs, we can only provide a basic breakdown without timing data
        # The actual cost calculation with time-dependent pricing is handled in calculate_cost
        billing_period_days = self.calculate_billing_period_days()
        
        # Get average price from latest forecast data
        estimated_avg_kwh_price = self._get_average_forecast_price()
        
        variable_cost = total_consumption_kwh * estimated_avg_kwh_price
        total_cost = variable_cost + self.base_price
        
        return {
            "base_price": self.base_price,
            "variable_cost": variable_cost,
            "total_cost": total_cost,
            "total_consumption_kwh": total_consumption_kwh,
            "estimated_avg_kwh_price": estimated_avg_kwh_price,
            "billing_period_days": billing_period_days,
            "note": "Dynamic tariff cost breakdown requires actual consumption timeline for accurate pricing"
        }

    def calculate_cost(self, data) -> float:
        """
        Calculate the total cost for a given consumption in kWh.
        """
        print(f"DynamicTariff.calculate_cost() called with data: {type(data)}")
        
        # Calculate actual billing period based on German monthly billing practices
        billing_period_days = self.calculate_billing_period_days()
        
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        print(f"Project root directory: {project_root}")
        
        # load consumption data if provided, else use default synthetic data
        if isinstance(data, pd.DataFrame):
            # Process uploaded consumption data
            consumption_data = data.copy()
            consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
            
            # Use only the most recent 3 months for faster Prophet processing
            # while still capturing seasonal patterns
            consumption_data = consumption_data.sort_values('datetime')
            cutoff_date = consumption_data['datetime'].max() - pd.Timedelta(days=90)
            consumption_data = consumption_data[consumption_data['datetime'] >= cutoff_date]
            print(f"Using recent 3 months of data: {len(consumption_data)} rows, from {consumption_data['datetime'].min()} to {consumption_data['datetime'].max()}")
            
            consumption_data = consumption_data.resample('H', on='datetime').sum().reset_index()
            print(f"After hourly resampling: {len(consumption_data)} rows")
            future_consumption = forecast_prophet(consumption_data)
            
            # Prophet returns columns 'ds' and 'yhat', but we need 'datetime' and 'value'
            future_consumption = future_consumption.rename(columns={'ds': 'datetime', 'yhat': 'value'})
            print(f"Prophet forecast columns after rename: {list(future_consumption.columns)}")
        elif isinstance(data, (int, float)):
            # load standard load profile
            yearly_usage = data
            print(f"Loading standard load profile for yearly usage: {yearly_usage}")
            
            try:
                standard_profile_path = os.path.join(project_root, "app_data", "standard_profile", "Standard_Load_Profile_2025_2026.csv")
                consumption_data = pd.read_csv(standard_profile_path)
                print(f"Successfully loaded standard load profile from {standard_profile_path}, shape: {consumption_data.shape}")
            except Exception as e:
                print(f"Error loading standard load profile: {e}")
                # Return just base price if data loading fails
                return self.base_price
                
            consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
            current_yearly_usage = consumption_data['value'].sum()
            adjustment_factor = yearly_usage / current_yearly_usage if current_yearly_usage > 0 else 1
            consumption_data['value'] = consumption_data['value'] * adjustment_factor
            
            future_consumption = slice_seasonal_data(consumption_data, self.start_date, days=billing_period_days)
            print(f"Future consumption data shape: {future_consumption.shape}")
        else:
            raise ValueError("Input data must be a pandas DataFrame or a numeric yearly usage value.")
        
        # load price forecast data from app_data
        try:
            app_data_path = os.path.join(project_root, "app_data")
            
            # Find the most recent price forecast file
            forecast_files = [f for f in os.listdir(app_data_path) if f.startswith('germany_price_forecast_') and f.endswith('.csv')]
            if not forecast_files:
                raise FileNotFoundError("No price forecast files found in app_data")
            
            # Sort by filename to get the most recent (assumes timestamp in filename)
            latest_forecast_file = sorted(forecast_files)[-1]
            price_data_path = os.path.join(app_data_path, latest_forecast_file)
            
            future_prices = pd.read_csv(price_data_path)
            print(f"Successfully loaded price forecast data from {price_data_path}, shape: {future_prices.shape}")
            
            # Use 'yhat' column from Prophet forecast and convert from €/MWh to €/kWh
            if 'yhat' not in future_prices.columns:
                raise ValueError(f"Expected 'yhat' column in forecast data, found columns: {list(future_prices.columns)}")
            
            future_prices['predicted_mean'] = (future_prices['yhat'] / 1000) + self.markup  # Convert €/MWh to €/kWh and add markup
            future_prices = future_prices.rename(columns={'ds': 'datetime'})  # Prophet uses 'ds' for datetime
            print(f"Using Prophet forecast with yhat column, converted prices from €/MWh to €/kWh and added markup of {self.markup}")
            print(f"Sample converted prices: {future_prices['predicted_mean'].head().tolist()}")
        except Exception as e:
            print(f"Error loading price forecast data: {e}")
            # Return just base price if price data loading fails
            return self.base_price
            
        future_prices['datetime'] = pd.to_datetime(future_prices['datetime'])
        
        # merge consumption and price data
        future_data = future_consumption.merge(future_prices, on='datetime', how='left')
        print(f"Merged data shape: {future_data.shape}")
        print(f"Merged data columns: {list(future_data.columns)}")
        print(f"Number of non-null price values: {future_data['predicted_mean'].notna().sum()}")
        print(f"Number of null price values: {future_data['predicted_mean'].isna().sum()}")
        print(f"Price data date range: {future_prices['datetime'].min()} to {future_prices['datetime'].max()}")
        print(f"Consumption data date range: {future_consumption['datetime'].min()} to {future_consumption['datetime'].max()}")
        
        # calculate total cost - handle both 'yhat' and 'value' columns
        if 'yhat' in future_data.columns:
            consumption_column = 'yhat'
        elif 'value' in future_data.columns:
            consumption_column = 'value'
        else:
            raise ValueError("Expected 'yhat' or 'value' column in consumption data")
            
        # Calculate consumption costs
        consumption_costs = future_data.apply(lambda row: row[consumption_column] * row['predicted_mean'], axis=1)
        total_consumption_cost = consumption_costs.sum()
        total_cost = total_consumption_cost + self.base_price
        
        print(f"Consumption column used: {consumption_column}")
        print(f"Sample consumption values: {future_data[consumption_column].head().tolist()}")
        print(f"Sample price values: {future_data['predicted_mean'].head().tolist()}")
        print(f"Sample consumption costs: {consumption_costs.head().tolist()}")
        print(f"Total consumption cost: {total_consumption_cost}")
        print(f"Base price: {self.base_price}")
        print(f"Total cost: {total_cost}")
        
        return total_cost
    
    def calculate_cost_with_breakdown(self, data):
        """
        Calculate the total cost and return both cost and average kWh price.
        Returns: dict with 'total_cost' and 'avg_kwh_price'
        """
        import os
        
        # Calculate actual billing period based on German monthly billing practices
        billing_period_days = self.calculate_billing_period_days()
        
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # load consumption data if provided, else use default synthetic data
        if isinstance(data, pd.DataFrame):
            # Process uploaded consumption data
            consumption_data = data.copy()
            consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
            
            # Use only the most recent 3 months for faster Prophet processing
            consumption_data = consumption_data.sort_values('datetime')
            cutoff_date = consumption_data['datetime'].max() - pd.Timedelta(days=90)
            consumption_data = consumption_data[consumption_data['datetime'] >= cutoff_date]
            
            consumption_data = consumption_data.resample('H', on='datetime').sum().reset_index()
            future_consumption = forecast_prophet(consumption_data)
            
            # Prophet returns columns 'ds' and 'yhat', but we need 'datetime' and 'value'
            future_consumption = future_consumption.rename(columns={'ds': 'datetime', 'yhat': 'value'})
        elif isinstance(data, (int, float)):
            # load standard load profile
            yearly_usage = data
            
            try:
                standard_profile_path = os.path.join(project_root, "app_data", "standard_profile", "Standard_Load_Profile_2025_2026.csv")
                consumption_data = pd.read_csv(standard_profile_path)
            except Exception as e:
                # Return just base price if data loading fails
                return {'total_cost': self.base_price, 'avg_kwh_price': 0.0}
                
            consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
            current_yearly_usage = consumption_data['value'].sum()
            adjustment_factor = yearly_usage / current_yearly_usage if current_yearly_usage > 0 else 1
            consumption_data['value'] = consumption_data['value'] * adjustment_factor
            
            future_consumption = slice_seasonal_data(consumption_data, self.start_date, days=billing_period_days)
        else:
            raise ValueError("Input data must be a pandas DataFrame or a numeric yearly usage value.")
        
        # load price forecast data from app_data
        try:
            app_data_path = os.path.join(project_root, "app_data")
            
            # Find the most recent price forecast file
            forecast_files = [f for f in os.listdir(app_data_path) if f.startswith('germany_price_forecast_') and f.endswith('.csv')]
            if not forecast_files:
                raise FileNotFoundError("No price forecast files found in app_data")
            
            # Sort by filename to get the most recent (assumes timestamp in filename)
            latest_forecast_file = sorted(forecast_files)[-1]
            price_data_path = os.path.join(app_data_path, latest_forecast_file)
            
            future_prices = pd.read_csv(price_data_path)
            
            # Use 'yhat' column from Prophet forecast and convert from €/MWh to €/kWh
            if 'yhat' not in future_prices.columns:
                raise ValueError(f"Expected 'yhat' column in forecast data, found columns: {list(future_prices.columns)}")
            
            future_prices['predicted_mean'] = (future_prices['yhat'] / 1000) + self.markup  # Convert €/MWh to €/kWh and add markup
            future_prices = future_prices.rename(columns={'ds': 'datetime'})  # Prophet uses 'ds' for datetime
        except Exception as e:
            # Return just base price if price data loading fails
            return {'total_cost': self.base_price, 'avg_kwh_price': 0.0}
            
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
            
        # Calculate consumption costs
        consumption_costs = future_data.apply(lambda row: row[consumption_column] * row['predicted_mean'], axis=1)
        total_consumption_cost = consumption_costs.sum()
        total_cost = total_consumption_cost + self.base_price
        
        # Calculate average kWh price
        total_consumption = future_data[consumption_column].sum()
        avg_kwh_price = future_data['predicted_mean'].mean() if len(future_data) > 0 else 0.0
        
        print(f"Total consumption: {total_consumption} kWh")
        print(f"Total consumption cost: {total_consumption_cost}€")
        print(f"Average kWh price: {avg_kwh_price:.4f}€/kWh")
        print(f"Base price: {self.base_price}€")
        print(f"Total cost: {total_cost}€")
        
        return {
            'total_cost': total_cost,
            'avg_kwh_price': avg_kwh_price
        }

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
        final_df = pd.concat(result_data, ignore_index=True)
        return final_df
    else:
        return pd.DataFrame(columns=['datetime', 'value'])