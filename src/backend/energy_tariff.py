from abc import ABC, abstractmethod
from datetime import datetime, time, timedelta
from typing import Optional
import pandas as pd
from .forecasting.energy_usage_forecast import forecast_prophet
from calendar import monthrange
import os

class EnergyTariff(ABC):
    """
    Abstract base class for electricity contracts.
    """

    def __init__(self, name: str, base_price: float, is_dynamic: bool, start_date: datetime, kwh_rate: Optional[float] = None, 
                 provider: Optional[str] = None, min_duration: Optional[int] = None, features: Optional[list] = None,
                 postal_code: Optional[str] = None):
        """
        Initialize the energy tariff.
        
        Args:
            name: Name of the tariff
            base_price: Monthly base price in €
            is_dynamic: Whether this is a dynamic tariff
            start_date: Start date for the tariff
            kwh_rate: Fixed price per kWh in € (for fixed tariffs)
            provider: Energy provider name
            min_duration: Minimum contract duration in months
            features: List of tariff features (e.g., ["green", "fixed"])
            postal_code: German postal code (Postleitzahl) for location-specific pricing or availability
        """
        self.name = name
        self.provider = provider
        self.min_duration = min_duration
        self.base_price = base_price
        self.kwh_rate = kwh_rate
        self.start_date = start_date
        self.is_dynamic = is_dynamic
        self.features = features if features else []
        self.postal_code = postal_code

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
                 min_duration: Optional[int] = None, is_dynamic: bool = False, features: Optional[list] = None,
                 postal_code: Optional[str] = None):
        """
        Initialize the fixed tariff with base price and kWh rate.
        
        Args:
            name: Name of the tariff
            base_price: Monthly base price in €
            kwh_rate: Fixed price per kWh in €
            start_date: Start date for the tariff
            provider: Energy provider name
            min_duration: Minimum contract duration in months
            is_dynamic: Whether this is a dynamic tariff (always False for this class)
            features: List of tariff features (e.g., ["fixed", "green"])
            postal_code: German postal code (Postleitzahl) for location-specific pricing or availability
        """
        super().__init__(name=name, base_price=base_price, is_dynamic=False, start_date=start_date,
                         kwh_rate=kwh_rate, provider=provider, min_duration=min_duration, features=features,
                         postal_code=postal_code)

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
        
        Args:
            data: pandas DataFrame with 'datetime' and 'value' columns (hourly kWh consumption)
                  or a numeric value representing annual consumption in kWh.
        """
        print(f"\n{'='*80}")
        print(f"FixedTariff.calculate_cost() called for tariff: {self.name}")
        print(f"Data type: {type(data)}")
        
        if isinstance(data, pd.DataFrame):
            if 'value' in data.columns:
                print(f"Total consumption in uploaded data: {data['value'].sum():.2f} kWh")
        else:
            print(f"Numeric value (annual consumption): {data}")
        print(f"{'='*80}\n")
        
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
            
            # Convert from power (kW) to energy (kWh) based on time intervals
            time_diff = consumption_data['datetime'].diff().mode()[0]
            if time_diff == pd.Timedelta(minutes=15):
                # 15-minute intervals: multiply by 0.25 hours to convert kW to kWh
                consumption_data['value'] = consumption_data['value'] * 0.25
                print(f"Converted 15-minute kW readings to kWh (multiplied by 0.25)")
            elif time_diff == pd.Timedelta(hours=1):
                # Hourly data: multiply by 1 hour to convert kW to kWh
                consumption_data['value'] = consumption_data['value'] * 1.0
                print(f"Converted hourly kW readings to kWh (multiplied by 1.0)")
            # If already in kWh or other intervals, use as-is
            
            consumption_data = consumption_data.resample('h', on='datetime').sum().reset_index()
            print(f"After resampling to hourly: {len(consumption_data)} rows, total: {consumption_data['value'].sum():.2f} kWh")
            future_consumption = forecast_prophet(consumption_data)
            
            # Prophet returns columns 'ds' and 'yhat', rename to match expected format
            future_consumption = future_consumption.rename(columns={'ds': 'datetime', 'yhat': 'value'})
        elif isinstance(data, (int, float)):
            # load standard load profile data
            yearly_usage = data
            standard_profile_path = os.path.join(project_root, "app_data", "standard_profile", "Standard_Load_Profile_2025_2026.csv")
            consumption_data = pd.read_csv(standard_profile_path)
            consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
            
            # Convert from 15-minute Watt values to hourly kWh BEFORE scaling
            time_diff = consumption_data['datetime'].diff().mode()[0]
            if time_diff == pd.Timedelta(minutes=15):
                # Values are in W for 15-minute intervals
                # Convert to kWh: multiply by 0.25 hours and divide by 1000
                consumption_data['value'] = consumption_data['value'] * 0.25 / 1000
                consumption_data = consumption_data.set_index('datetime').resample('h').sum().reset_index()
            
            # NOW calculate the adjustment factor with properly converted kWh values
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

    def __init__(self, name: str, base_price: float, start_date: datetime, provider: Optional[str] = None, 
                 is_dynamic: bool = True, network_fee: float = 0.0, features: Optional[list] = None,
                 postal_code: Optional[str] = None, additional_price_ct_kwh: Optional[float] = None):
        """
        Initialize the dynamic tariff with base price and one-time network fee.
        
        Args:
            name: Name of the tariff
            base_price: Monthly base price in €
            start_date: Start date for the tariff
            provider: Energy provider name
            is_dynamic: Whether this is a dynamic tariff (always True for this class)
            network_fee: One-time network usage fee (einmalige Zahlung für Netznutzung) in €
            features: List of tariff features (e.g., ["dynamic", "green"])
            postal_code: German postal code (Postleitzahl) for location-specific pricing or availability
            additional_price_ct_kwh: Fixed price components in ct/kWh (network fees, taxes, levies)
                                     from scraped provider data (e.g., Tibber's 18.4 ct/kWh)
        """
        super().__init__(name, base_price=base_price, start_date=start_date, provider=provider, is_dynamic=True, 
                         features=features, postal_code=postal_code)
        self.network_fee = network_fee  # One-time fee for network usage
        self.additional_price_ct_kwh = additional_price_ct_kwh  # Fixed components from scraper (ct/kWh)

    def _get_average_forecast_price(self) -> float:
        """
        Get average retail price from the latest forecast data.
        Returns a default value if forecast data is not available.
        
        Note: Uses yhat_retail column which includes:
        - Zero-censored wholesale price E[max(0, Y)]
        - Profile costs (10 EUR/MWh)
        - Risk premium (5 EUR/MWh)  
        - Supplier margin (55 EUR/MWh)
        Total markup: 70 EUR/MWh (7 ct/kWh)
        
        Network fee is handled separately as one-time charge.
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
            
            # Use retail price (includes business logic: zero-censoring + markup)
            if 'yhat_retail' in forecast_data.columns:
                # Convert €/MWh to €/kWh
                return forecast_data['yhat_retail'].mean() / 1000
            elif 'yhat' in forecast_data.columns:
                # Fallback to old format (wholesale + simple markup)
                # Add 70 EUR/MWh markup for compatibility
                return (forecast_data['yhat'].mean() + 70) / 1000
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
        
        # Get average price from latest forecast data (without markup)
        estimated_avg_kwh_price = self._get_average_forecast_price()
        
        variable_cost = total_consumption_kwh * estimated_avg_kwh_price
        total_cost = variable_cost + self.base_price + self.network_fee
        
        return {
            "base_price": self.base_price,
            "variable_cost": variable_cost,
            "network_fee": self.network_fee,
            "total_cost": total_cost,
            "total_consumption_kwh": total_consumption_kwh,
            "estimated_avg_kwh_price": estimated_avg_kwh_price,
            "billing_period_days": billing_period_days,
            "note": "Dynamic tariff cost breakdown requires actual consumption timeline for accurate pricing"
        }
    
    def calculate_cost_with_breakdown(self, data):
        """
        Calculate the total cost and return both cost and average kWh price.
        
        Args:
            data: pandas DataFrame with 'datetime' and 'value' columns (hourly kWh consumption)
                  or a numeric value representing annual consumption in kWh.
                  
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
            
            # Convert from power (kW) to energy (kWh) based on time intervals
            time_diff = consumption_data['datetime'].diff().mode()[0]
            if time_diff == pd.Timedelta(minutes=15):
                # 15-minute intervals: multiply by 0.25 hours to convert kW to kWh
                consumption_data['value'] = consumption_data['value'] * 0.25
            elif time_diff == pd.Timedelta(hours=1):
                # Hourly data: multiply by 1 hour to convert kW to kWh
                consumption_data['value'] = consumption_data['value'] * 1.0
            # If already in kWh or other intervals, use as-is
            
            # Use only the most recent 3 months for faster Prophet processing
            consumption_data = consumption_data.sort_values('datetime')
            cutoff_date = consumption_data['datetime'].max() - pd.Timedelta(days=90)
            consumption_data = consumption_data[consumption_data['datetime'] >= cutoff_date]
            
            consumption_data = consumption_data.resample('h', on='datetime').sum().reset_index()
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
                # Return just base price and network fee if data loading fails
                return {'total_cost': self.base_price + self.network_fee, 'avg_kwh_price': 0.0}
                
            consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
            
            # Convert from 15-minute Watt values to hourly kWh BEFORE scaling
            time_diff = consumption_data['datetime'].diff().mode()[0]
            if time_diff == pd.Timedelta(minutes=15):
                # Values are in W for 15-minute intervals
                # Convert to kWh: multiply by 0.25 hours and divide by 1000
                consumption_data['value'] = consumption_data['value'] * 0.25 / 1000
                consumption_data = consumption_data.set_index('datetime').resample('h').sum().reset_index()
            
            # NOW calculate the adjustment factor with properly converted kWh values
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
            
            # Use 'yhat_energy' column (zero-censored wholesale) + add fixed components
            # This gives us: Börsenpreis + Arbeitspreis (vom Scraper)
            if 'yhat_energy' in future_prices.columns:
                # New format: Start with zero-censored energy price (in EUR/MWh)
                # yhat_energy already contains E[max(0,Y)] - the probabilistic zero-censored wholesale price
                
                # Convert to ct/kWh for easier understanding
                wholesale_ct_kwh = future_prices['yhat_energy'] / 10  # EUR/MWh → ct/kWh
                
                # Add Arbeitspreis (work price) from scraper
                # This already includes ALL fixed components:
                #    - Anbieterkosten (supplier costs): ~7 ct/kWh
                #    - Netzentgelte (network fees): ~7-8 ct/kWh
                #    - Stromsteuer (electricity tax): 2.05 ct/kWh
                #    - Konzessionsabgabe (concession fee): ~1.5 ct/kWh
                #    - MwSt (VAT 19%): ~4-5 ct/kWh
                #    - Herkunftsnachweise (certificates): ~0.1-0.5 ct/kWh
                if hasattr(self, 'additional_price_ct_kwh') and self.additional_price_ct_kwh is not None:
                    # Use scraped Arbeitspreis (already contains ALL markups)
                    arbeitspreis_ct = self.additional_price_ct_kwh
                else:
                    # Default fallback for non-dynamic tariffs: ~25.4 ct/kWh
                    #    - Supplier costs: 7.0 ct/kWh
                    #    - Network/taxes/levies: 18.4 ct/kWh
                    arbeitspreis_ct = 25.4
                
                # Total price = wholesale (Börsenpreis) + Arbeitspreis (all other components)
                # For dynamic tariffs: ~11 ct (wholesale) + ~15 ct (markup) = ~26 ct/kWh
                total_price_ct = wholesale_ct_kwh + arbeitspreis_ct
                future_prices['predicted_mean'] = total_price_ct / 100  # ct/kWh → €/kWh
                
            elif 'yhat_retail' in future_prices.columns:
                # Fallback: Use retail price (already has supplier markup included)
                # yhat_retail = yhat_energy + 7.0 ct/kWh (supplier costs)
                # We still need to add the Arbeitspreis from scraper (taxes/network fees)
                retail_ct_kwh = future_prices['yhat_retail'] / 10  # EUR/MWh → ct/kWh
                
                if hasattr(self, 'additional_price_ct_kwh') and self.additional_price_ct_kwh is not None:
                    # Arbeitspreis from scraper
                    arbeitspreis_ct = self.additional_price_ct_kwh
                else:
                    # Default: Only add taxes/network (no supplier costs, already in yhat_retail)
                    arbeitspreis_ct = 18.4
                    
                future_prices['predicted_mean'] = (retail_ct_kwh + arbeitspreis_ct) / 100  # → €/kWh
                
            elif 'yhat' in future_prices.columns:
                # Old format: Raw wholesale (can be negative) + add all markups
                wholesale_eur_mwh = future_prices['yhat'].clip(lower=0)  # Simple zero-floor
                wholesale_ct_kwh = wholesale_eur_mwh / 10
                
                if hasattr(self, 'additional_price_ct_kwh') and self.additional_price_ct_kwh is not None:
                    # Use scraped Arbeitspreis (contains all markups)
                    arbeitspreis_ct = self.additional_price_ct_kwh
                else:
                    # Default: supplier + taxes/network
                    arbeitspreis_ct = 25.4
                    
                future_prices['predicted_mean'] = (wholesale_ct_kwh + arbeitspreis_ct) / 100
            else:
                raise ValueError(f"Expected 'yhat_energy', 'yhat_retail' or 'yhat' column in forecast data, found columns: {list(future_prices.columns)}")
            
            future_prices = future_prices.rename(columns={'ds': 'datetime'})  # Prophet uses 'ds' for datetime
        except Exception as e:
            # Return just base price and network fee if price data loading fails
            return {'total_cost': self.base_price + self.network_fee, 'avg_kwh_price': 0.0}
            
        future_prices['datetime'] = pd.to_datetime(future_prices['datetime'])
        
        # Determine consumption column BEFORE merging to avoid confusion with price data columns
        if 'yhat' in future_consumption.columns:
            consumption_column = 'yhat'
        elif 'value' in future_consumption.columns:
            consumption_column = 'value'
        else:
            raise ValueError("Expected 'yhat' or 'value' column in consumption data")
        
        # Only keep necessary columns from price data to avoid column conflicts
        price_columns_to_keep = ['datetime', 'predicted_mean']
        future_prices_clean = future_prices[price_columns_to_keep].copy()
        
        # merge consumption and price data
        future_data = future_consumption.merge(future_prices_clean, on='datetime', how='left')
            
        # Calculate consumption costs
        consumption_costs = future_data.apply(lambda row: row[consumption_column] * row['predicted_mean'], axis=1)
        total_consumption_cost = consumption_costs.sum()
        total_cost = total_consumption_cost + self.base_price + self.network_fee  # Add one-time network fee
        
        # Calculate average kWh price
        total_consumption = future_data[consumption_column].sum()
        avg_kwh_price = future_data['predicted_mean'].mean() if len(future_data) > 0 else 0.0
        
        print(f"Total consumption: {total_consumption} kWh")
        print(f"Total consumption cost: {total_consumption_cost}€")
        print(f"Average kWh price: {avg_kwh_price:.4f}€/kWh")
        print(f"Base price: {self.base_price}€")
        print(f"Network fee (one-time): {self.network_fee}€")
        print(f"Total cost: {total_cost}€")
        
        return {
            'total_cost': total_cost,
            'avg_kwh_price': avg_kwh_price
        }

def slice_seasonal_data(df: pd.DataFrame, start_date: datetime, days: int = 30) -> pd.DataFrame:
    """
    Slice data based on day/month only (ignoring year) for seasonal patterns.
    Cycles through the year if needed.
    Note: This function expects data to already be in hourly kWh format.
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
        print(f"Sliced {days} days of data: {len(final_df)} rows, total consumption: {final_df['value'].sum():.2f} kWh")
        return final_df
    else:
        return pd.DataFrame(columns=['datetime', 'value'])