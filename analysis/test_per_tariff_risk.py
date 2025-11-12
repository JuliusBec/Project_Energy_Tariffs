"""
Test per-tariff risk score calculation
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backend.risk_analysis import (
    create_historic_risk_analysis,
    calculate_coincidence_factor,
    get_aggregated_risk_score
)
import pandas as pd

def test_per_tariff_risk():
    """Test risk calculation for different tariff types"""
    
    print("="*80)
    print("TEST: Per-Tariff Risk Score Calculation")
    print("="*80)
    
    # Load example consumption data
    test_file = os.path.join(os.path.dirname(__file__), "..", "app_data", "example_smart_meter.csv")
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"\n📊 Loading consumption data from: {test_file}")
    consumption_data = pd.read_csv(test_file)
    consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
    
    print(f"✅ Loaded {len(consumption_data)} rows")
    print(f"   Period: {consumption_data['datetime'].min()} to {consumption_data['datetime'].max()}")
    print(f"   Total consumption: {consumption_data['value'].sum():.2f} kWh")
    
    # Calculate base metrics (same for all tariffs)
    print("\n" + "="*80)
    print("STEP 1: Calculate base risk metrics (common for all tariffs)")
    print("="*80)
    
    app_data_dir = os.path.join(os.path.dirname(__file__), "..", "app_data")
    
    historic_risk = create_historic_risk_analysis(consumption_data, days=30, app_data_dir=app_data_dir)
    print(f"\n✅ Historic risk analysis:")
    print(f"   Market avg price: €{historic_risk['market_avg_price']:.4f}/kWh")
    print(f"   User weighted price: €{historic_risk['user_weighted_price']:.4f}/kWh")
    print(f"   Price differential: {historic_risk['price_differential_pct']:.2f}%")
    print(f"   Price volatility (std dev): €{historic_risk['price_volatility']:.4f}/kWh")
    
    coincidence = calculate_coincidence_factor(consumption_data, days=30, expensive_hours_pct=20.0, app_data_dir=app_data_dir)
    print(f"\n✅ Coincidence factor:")
    print(f"   Consumption during expensive hours: {coincidence['consumption_coincidence_pct']:.1f}%")
    print(f"   Expensive hours threshold: {coincidence['expensive_hours_pct']:.1f}%")
    
    # Prepare common parameters
    forecast_price_volatility = {}
    usage_forecast_quality = {}
    
    # Test risk calculation for different tariff types
    print("\n" + "="*80)
    print("STEP 2: Calculate risk scores for different tariff types")
    print("="*80)
    
    tariff_types = [
        {"name": "Dynamic Tariff (EnBW/Tibber/Tado)", "is_dynamic": True},
        {"name": "Fixed Tariff (Conventional)", "is_dynamic": False}
    ]
    
    for tariff_type in tariff_types:
        print(f"\n{'─'*80}")
        print(f"📋 {tariff_type['name']}")
        print(f"   is_dynamic: {tariff_type['is_dynamic']}")
        print(f"{'─'*80}")
        
        risk_assessment = get_aggregated_risk_score(
            historic_risk,
            coincidence,
            forecast_price_volatility,
            tariff_type['is_dynamic'],
            usage_forecast_quality
        )
        
        # Display results
        risk_emoji = {
            'low': '🟢',
            'moderate': '🟡',
            'high': '🔴'
        }.get(risk_assessment['risk_level'], '⚪')
        
        print(f"\n{risk_emoji} Risk Level: {risk_assessment['risk_level'].upper()}")
        print(f"📊 Risk Score: {risk_assessment['risk_score']}/100")
        print(f"💬 Message: {risk_assessment['risk_message']}")
        
        if 'risk_factors' in risk_assessment:
            print(f"\n📌 Risk Factors:")
            for factor in risk_assessment['risk_factors']:
                impact_symbol = {
                    'positive': '✓',
                    'neutral': '○',
                    'negative': '✗'
                }.get(factor['impact'], '?')
                
                print(f"   {impact_symbol} {factor['factor']}: {factor['detail']}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("✅ Test completed successfully!")
    print("\n📝 Key Observations:")
    print("   • Fixed tariffs should have ~25 points lower risk score")
    print("   • Dynamic tariff risk depends on consumption patterns")
    print("   • Both use the same base metrics but different scoring")
    print("="*80)

if __name__ == "__main__":
    test_per_tariff_risk()
