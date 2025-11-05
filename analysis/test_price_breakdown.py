#!/usr/bin/env python3
"""
Test script for the price breakdown functionality
"""

import sys
import os

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.backend.forecasting.price_forecasting.EnergyPriceForecast import get_price_breakdown
import json

def test_price_breakdown():
    """Test the price breakdown function"""
    print("Testing price breakdown function...\n")
    
    # Test with default parameters (uses latest forecast)
    print("1. Testing with latest forecast data:")
    breakdown = get_price_breakdown()
    
    if breakdown:
        print("\n✅ Price breakdown generated successfully!\n")
        print(json.dumps(breakdown, indent=2))
        print("\n" + "="*60)
        
        # Display in a more readable format
        print("\nPRICE COMPONENT BREAKDOWN:")
        print("="*60)
        print(f"Wholesale Market Price: {breakdown['wholesale_price_eur_per_mwh']:.2f} EUR/MWh")
        print(f"                       ({breakdown['wholesale_price_eur_per_kwh']:.4f} EUR/kWh)")
        print(f"\nEstimated Total End-User Price: {breakdown['total_price_eur_per_kwh']:.4f} EUR/kWh")
        print("\nComponent Breakdown:")
        print("-" * 60)
        
        for i, label in enumerate(breakdown['labels']):
            percentage = breakdown['values'][i]
            price = breakdown['prices_eur_per_kwh'][i]
            desc = breakdown['descriptions'][i]
            print(f"\n{label}:")
            print(f"  {percentage}% | {price:.4f} EUR/kWh")
            print(f"  {desc}")
        
        print("\n" + "="*60)
        print(f"\n⚠️  NOTE: {breakdown['note']}")
    else:
        print("❌ Failed to generate price breakdown")
        return False
    
    # Test with custom price
    print("\n\n2. Testing with custom wholesale price (150 EUR/MWh):")
    breakdown_custom = get_price_breakdown(avg_price_eur_per_mwh=150.0)
    
    if breakdown_custom:
        print(f"✅ Custom price breakdown generated!")
        print(f"   Total end-user price: {breakdown_custom['total_price_eur_per_kwh']:.4f} EUR/kWh")
    else:
        print("❌ Failed with custom price")
    
    return True

if __name__ == "__main__":
    success = test_price_breakdown()
    sys.exit(0 if success else 1)
