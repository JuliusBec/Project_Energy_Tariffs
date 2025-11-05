#!/usr/bin/env python3
"""
Test script to verify tariff calculations are correct
"""

import sys
import os
from datetime import datetime

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.backend.EnergyTariff import FixedTariff, DynamicTariff

def test_fixed_tariff():
    """Test fixed tariff calculation with known values"""
    print("="*80)
    print("TESTING FIXED TARIFF")
    print("="*80)
    
    # Create a simple fixed tariff
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tariff = FixedTariff(
        name="Test Fixed",
        provider="Test",
        base_price=10.00,  # €10/month base fee
        kwh_rate=0.30,     # €0.30/kWh
        start_date=start_date
    )
    
    # Test with 3500 kWh annual consumption
    annual_consumption = 3500
    print(f"\nTest Case: {annual_consumption} kWh annual consumption")
    print(f"Base price: €{tariff.base_price}/month")
    print(f"kWh rate: €{tariff.kwh_rate}/kWh")
    
    # Expected calculation for ONE MONTH:
    # - Monthly consumption: 3500 / 12 = ~291.67 kWh
    # - Monthly energy cost: 291.67 * 0.30 = €87.50
    # - Monthly base fee: €10.00
    # - Total monthly: €97.50
    # - Total annual: €97.50 * 12 = €1170
    expected_monthly_consumption = annual_consumption / 12
    expected_monthly_energy_cost = expected_monthly_consumption * tariff.kwh_rate
    expected_monthly_total = expected_monthly_energy_cost + tariff.base_price
    expected_annual_total = expected_monthly_total * 12
    
    print(f"\nExpected calculation:")
    print(f"  Monthly consumption: {expected_monthly_consumption:.2f} kWh")
    print(f"  Monthly energy cost: €{expected_monthly_energy_cost:.2f}")
    print(f"  Monthly base fee: €{tariff.base_price:.2f}")
    print(f"  Total monthly: €{expected_monthly_total:.2f}")
    print(f"  Total annual: €{expected_annual_total:.2f}")
    
    # Actual calculation
    try:
        actual_cost = tariff.calculate_cost(annual_consumption)
        print(f"\nActual calculation:")
        print(f"  Returned cost: €{actual_cost:.2f}")
        print(f"  Annual (x12): €{actual_cost * 12:.2f}")
        
        # Check if the cost is reasonable (within 20% of expected monthly)
        if abs(actual_cost - expected_monthly_total) / expected_monthly_total < 0.20:
            print(f"\n✅ Result is within expected range (monthly cost)")
        elif abs(actual_cost - expected_annual_total) / expected_annual_total < 0.20:
            print(f"\n⚠️  Result appears to be ANNUAL cost, not monthly!")
        else:
            print(f"\n❌ Result is outside expected range!")
            print(f"   Difference: €{actual_cost - expected_monthly_total:.2f} from expected monthly")
            
            # Check if it's using annual consumption directly
            wrong_calc = (annual_consumption * tariff.kwh_rate) + tariff.base_price
            if abs(actual_cost - wrong_calc) < 1.0:
                print(f"   ⚠️  BUG FOUND: Using annual consumption for monthly calculation!")
                print(f"   Wrong calculation: ({annual_consumption} * {tariff.kwh_rate}) + {tariff.base_price} = €{wrong_calc:.2f}")
        
    except Exception as e:
        print(f"\n❌ Error during calculation: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80 + "\n")

def test_dynamic_tariff():
    """Test dynamic tariff calculation"""
    print("="*80)
    print("TESTING DYNAMIC TARIFF")
    print("="*80)
    
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tariff = DynamicTariff(
        name="Test Dynamic",
        provider="Test",
        base_price=10.00,  # €10/month base fee
        markup=0.20,       # €0.20/kWh markup on wholesale
        start_date=start_date
    )
    
    annual_consumption = 3500
    print(f"\nTest Case: {annual_consumption} kWh annual consumption")
    print(f"Base price: €{tariff.base_price}/month")
    print(f"Markup: €{tariff.markup}/kWh")
    
    # Expected: similar to fixed but with dynamic pricing
    # Assuming average price ~€0.30/kWh total (including markup)
    expected_monthly_consumption = annual_consumption / 12
    expected_avg_price = 0.30  # This will vary based on market data
    expected_monthly_energy_cost = expected_monthly_consumption * expected_avg_price
    expected_monthly_total = expected_monthly_energy_cost + tariff.base_price
    expected_annual_total = expected_monthly_total * 12
    
    print(f"\nExpected calculation (assuming €{expected_avg_price}/kWh avg):")
    print(f"  Monthly consumption: {expected_monthly_consumption:.2f} kWh")
    print(f"  Monthly energy cost: ~€{expected_monthly_energy_cost:.2f}")
    print(f"  Monthly base fee: €{tariff.base_price:.2f}")
    print(f"  Total monthly: ~€{expected_monthly_total:.2f}")
    print(f"  Total annual: ~€{expected_annual_total:.2f}")
    
    try:
        result = tariff.calculate_cost_with_breakdown(annual_consumption)
        actual_cost = result['total_cost']
        avg_kwh_price = result['avg_kwh_price']
        
        print(f"\nActual calculation:")
        print(f"  Returned cost: €{actual_cost:.2f}")
        print(f"  Average kWh price: €{avg_kwh_price:.4f}")
        print(f"  Annual (x12): €{actual_cost * 12:.2f}")
        
        # Recalculate expected with actual average price
        actual_expected_monthly = (expected_monthly_consumption * avg_kwh_price) + tariff.base_price
        actual_expected_annual = actual_expected_monthly * 12
        
        print(f"\nExpected with actual avg price:")
        print(f"  Monthly: €{actual_expected_monthly:.2f}")
        print(f"  Annual: €{actual_expected_annual:.2f}")
        
        if abs(actual_cost - actual_expected_monthly) / actual_expected_monthly < 0.20:
            print(f"\n✅ Result is within expected range (monthly cost)")
        elif abs(actual_cost - actual_expected_annual) / actual_expected_annual < 0.20:
            print(f"\n⚠️  Result appears to be ANNUAL cost, not monthly!")
        else:
            print(f"\n❌ Result is outside expected range!")
            
    except Exception as e:
        print(f"\n❌ Error during calculation: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    test_fixed_tariff()
    test_dynamic_tariff()
