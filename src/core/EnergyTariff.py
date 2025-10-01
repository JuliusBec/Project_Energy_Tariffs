from abc import ABC, abstractmethod
from datetime import datetime, time  
from typing import Optional
import pandas as pd

class EnergyTariff(ABC):
    """
    Abstract base class for electricity contracts.
    """

    def __init__(self, name: str, base_price: float, is_dynamic: bool, start_date: datetime, kwh_rate: Optional[float] = None, 
                 provider: Optional[str] = None, min_duration: Optional[int] = None):
        """
        Initialize the energy tariff.
        """
        self.name = name
        self.provider = provider
        self.min_duration = min_duration
        self.base_price = base_price
        self.kwh_rate = kwh_rate
        self.start_date = start_date

class FixedTariff(EnergyTariff):
    """
    Represents a fixed energy tariff.
    """

    def __init__(self, name: str, base_price: float, kwh_rate: float, start_date: datetime, provider: Optional[str] = None, 
                 min_duration: Optional[int] = None, is_dynamic: bool = False):
        """
        Initialize the fixed tariff with base price and kWh rate.
        """
        super().__init__(name, base_price=base_price, kwh_rate=kwh_rate, start_date=start_date, provider=provider, is_dynamic=False,
                         min_duration=min_duration)

    def calculate_cost(self, consumption_data: pd.DataFrame) -> float:
        """
        Calculate the total cost for a given consumption in kWh.
        """
        
        total_base_price = self.base_price * self.min_duration if self.min_duration else 0

        total_energy_cost = self.kwh_rate * consumption_data['value'].sum() * 0.25  # Assuming 'value' is in kW and we convert to kWh for 15-minute intervals

        return total_base_price + total_energy_cost

class DynamicTariff(EnergyTariff):
    """
    Represents a dynamic energy tariff.
    """

    def __init__(self, name: str, base_price: float, start_date: datetime, provider: Optional[str] = None, is_dynamic: bool = True):
        """
        Initialize the dynamic tariff with base price and kWh rate.
        """
        super().__init__(name, base_price=base_price, start_date=start_date, provider=provider, is_dynamic=True)

    def calculate_energy_consumption(self, consumption_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate the expected energy consumption based on historical data.
        """

        # Make sure consumption_data is in the correct format
        if 'datetime' not in consumption_data.columns:
            consumption_data['datetime'] = pd.to_datetime(consumption_data['Datum'] + ' ' + consumption_data['bis'])
        consumption_data.set_index('datetime', inplace=True)
        
                
        # check if the consumption_data contains data from the same time last year
        last_year = datetime.combine(self.start_date.replace(year=self.start_date.year - 1), time(0, 0))
        end_of_month = last_year + pd.DateOffset(months=1)

        if last_year in consumption_data.index:
            # If data from the same time last year is available, use it
            last_year_data = consumption_data.loc[last_year : end_of_month]
            return sum(last_year_data['value']) * 0.25
        else:
            # If not, use recent trends to calculate expected energy usage
            last_month_data = consumption_data.loc[consumption_data.index[-(30*24*4)]:]
            return sum(last_month_data['value']) * 0.25

    def calculate_cost(self, consumption_data: pd.DataFrame, price_data: pd.DataFrame) -> float:
        """
        Calculate the total cost for a given consumption in kWh.
        """
        expected_consumption = self.calculate_energy_consumption(consumption_data)
        return self.base_price + (expected_consumption * price_data['Wert'].sum() * 0.25)

dynamic_test_tariff = DynamicTariff(name="Dynamic Test Tariff", base_price=15.0, start_date=datetime.today())

fixed_test_tariff = FixedTariff(name="Fixed Test Tariff", base_price=10.0, kwh_rate=0.3, min_duration=12, start_date=datetime.today())

# Only load the first two columns of the Excel file
user_data = pd.read_csv("data/household_data/synthetic_1_person_household.csv")

dynamic_test_tariff.calculate_energy_consumption(user_data)


print("total energy cost for the next year: ", round(fixed_test_tariff.calculate_cost(user_data), 2), "Euro")
print("average monthly cost: ", round(fixed_test_tariff.calculate_cost(user_data) / 12, 2), "Euro")

print("Expected energy consumption: ", round(dynamic_test_tariff.calculate_energy_consumption(user_data), 2), "kWh")
# Example usage