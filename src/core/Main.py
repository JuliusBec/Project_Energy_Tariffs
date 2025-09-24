import pandas as pd
import EnergyTariff

def calculate_tariff_costs(usage_data, tariff: EnergyTariff,):
    # Example function to calculate costs based on usage data and tariff
    costs = usage_data * tariff.rate_per_kwh
    return costs.sum()