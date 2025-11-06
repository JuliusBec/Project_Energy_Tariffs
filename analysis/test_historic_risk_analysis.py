"""
Test script for historic risk analysis functionality
"""
import sys
import os
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from backend.RiskAnalysis import create_historic_risk_analysis, calculate_coincidence_factor


def test_with_user_data():
    """Test historic risk analysis with actual user data"""
    print("="*80)
    print("TESTING HISTORIC RISK ANALYSIS WITH USER DATA")
    print("="*80)
    
    # Load user consumption data
    user_data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'household_data', 'user_data_10265.csv')
    
    if not os.path.exists(user_data_path):
        print(f"❌ User data file not found: {user_data_path}")
        return
    
    print(f"\n✓ Loading user data from: {user_data_path}")
    consumption_data = pd.read_csv(user_data_path)
    consumption_data['datetime'] = pd.to_datetime(consumption_data['datetime'])
    
    print(f"  - Data range: {consumption_data['datetime'].min()} to {consumption_data['datetime'].max()}")
    print(f"  - Total rows: {len(consumption_data)}")
    print(f"  - Columns: {list(consumption_data.columns)}")
    
    # Test with 30 days
    print("\n" + "="*80)
    print("TESTING 30-DAY ANALYSIS")
    print("="*80)
    
    try:
        result = create_historic_risk_analysis(consumption_data, days=30)
        
        print("\n✅ Analysis completed successfully!")
        print(f"\nResults:")
        print(f"  Price file used: {result['price_file_used']}")
        print(f"  Analysis period: {result['analysis_period']['start']} to {result['analysis_period']['end']}")
        print(f"  Days analyzed: {result['days_analyzed']}")
        print(f"  Hours with data: {result['num_hours']}")
        print(f"\n  Market average price: €{result['market_avg_price']:.4f}/kWh")
        print(f"  User weighted price: €{result['user_weighted_price']:.4f}/kWh")
        print(f"  Price differential: €{result['price_differential']:.4f}/kWh ({result['price_differential_pct']:+.2f}%)")
        print(f"  Price volatility (std): €{result['price_volatility']:.4f}/kWh")
        print(f"\n  Total consumption: {result['total_consumption']:.2f} kWh")
        print(f"  Total cost: €{result['total_cost']:.2f}")
        print(f"\n  Risk exposure: {result['risk_exposure'].upper()}")
        print(f"  {result['risk_message']}")
        
        # Interpretation
        print("\n" + "-"*80)
        print("INTERPRETATION:")
        if result['risk_exposure'] == 'favorable':
            print("  ✓ The user has demonstrated good consumption behavior by using more")
            print("    energy during low-price periods, resulting in cost savings.")
        else:
            print("  ⚠ The user's consumption pattern aligns with high-price periods,")
            print("    resulting in higher costs compared to the market average.")
        print("-"*80)
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Test with 7 days
    print("\n\n" + "="*80)
    print("TESTING 7-DAY ANALYSIS")
    print("="*80)
    
    try:
        result_7d = create_historic_risk_analysis(consumption_data, days=7)
        
        print("\n✅ 7-day analysis completed successfully!")
        print(f"\n  Market average price: €{result_7d['market_avg_price']:.4f}/kWh")
        print(f"  User weighted price: €{result_7d['user_weighted_price']:.4f}/kWh")
        print(f"  Price differential: {result_7d['price_differential_pct']:+.2f}%")
        print(f"  Risk exposure: {result_7d['risk_exposure'].upper()}")
        
    except Exception as e:
        print(f"\n❌ Error during 7-day analysis: {str(e)}")


def test_with_multiple_users():
    """Test with multiple user files to see different risk profiles"""
    print("\n\n" + "="*80)
    print("TESTING MULTIPLE USER PROFILES")
    print("="*80)
    
    household_data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'household_data')
    
    # Test with a few different users
    test_users = ['user_data_10265.csv', 'user_data_10625.csv', 'user_data_11220.csv']
    
    results_comparison = []
    
    for user_file in test_users:
        user_path = os.path.join(household_data_dir, user_file)
        
        if not os.path.exists(user_path):
            print(f"\n⚠ Skipping {user_file} (not found)")
            continue
        
        print(f"\n{'='*40}")
        print(f"Analyzing: {user_file}")
        print('='*40)
        
        try:
            consumption_data = pd.read_csv(user_path)
            result = create_historic_risk_analysis(consumption_data, days=30)
            
            results_comparison.append({
                'user': user_file,
                'weighted_price': result['user_weighted_price'],
                'differential_pct': result['price_differential_pct'],
                'exposure': result['risk_exposure'],
                'total_consumption': result['total_consumption']
            })
            
            print(f"  Weighted price: €{result['user_weighted_price']:.4f}/kWh")
            print(f"  Differential: {result['price_differential_pct']:+.2f}%")
            print(f"  Exposure: {result['risk_exposure']}")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    if results_comparison:
        print("\n" + "="*80)
        print("COMPARISON SUMMARY")
        print("="*80)
        
        for r in results_comparison:
            status = "✓" if r['exposure'] == 'favorable' else "⚠"
            print(f"{status} {r['user']:30s} | €{r['weighted_price']:.4f}/kWh | {r['differential_pct']:+6.2f}%")


def test_coincidence_factor():
    """Test coincidence factor calculation"""
    print("\n\n" + "="*80)
    print("TESTING COINCIDENCE FACTOR ANALYSIS")
    print("="*80)
    
    # Load user consumption data
    user_data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'household_data', 'user_data_10265.csv')
    
    if not os.path.exists(user_data_path):
        print(f"❌ User data file not found: {user_data_path}")
        return
    
    print(f"\n✓ Loading user data from: {user_data_path}")
    consumption_data = pd.read_csv(user_data_path)
    
    # Test with 20% most expensive hours (default)
    print("\n" + "="*80)
    print("ANALYZING TOP 20% MOST EXPENSIVE HOURS")
    print("="*80)
    
    try:
        result = calculate_coincidence_factor(consumption_data, days=30, expensive_hours_pct=20.0)
        
        print("\n✅ Coincidence analysis completed successfully!")
        print(f"\nAnalysis Parameters:")
        print(f"  Analysis period: {result['analysis_period']['start']} to {result['analysis_period']['end']}")
        print(f"  Days analyzed: {result['days_analyzed']}")
        print(f"  Total hours: {result['total_hours']}")
        print(f"  Expensive hours threshold: Top {result['expensive_hours_pct']:.0f}% ({result['num_expensive_hours']} hours)")
        print(f"  Price threshold: €{result['price_threshold']:.4f}/kWh")
        
        print(f"\nPrice Analysis:")
        print(f"  Average price (expensive hours): €{result['avg_price_expensive_hours']:.4f}/kWh")
        print(f"  Average price (cheap hours): €{result['avg_price_cheap_hours']:.4f}/kWh")
        print(f"  Price difference: €{result['avg_price_expensive_hours'] - result['avg_price_cheap_hours']:.4f}/kWh")
        
        print(f"\nConsumption Analysis:")
        print(f"  Total consumption: {result['total_consumption']:.2f} kWh")
        print(f"  Consumption during expensive hours: {result['consumption_during_expensive_hours']:.2f} kWh ({result['consumption_coincidence_pct']:.2f}%)")
        print(f"  Consumption during cheap hours: {result['consumption_during_cheap_hours']:.2f} kWh ({100 - result['consumption_coincidence_pct']:.2f}%)")
        
        print(f"\nCost Analysis:")
        print(f"  Total cost: €{result['total_cost']:.2f}")
        print(f"  Cost during expensive hours: €{result['cost_during_expensive_hours']:.2f} ({result['cost_coincidence_pct']:.2f}%)")
        print(f"  Cost during cheap hours: €{result['cost_during_cheap_hours']:.2f} ({100 - result['cost_coincidence_pct']:.2f}%)")
        
        print(f"\nRisk Metrics:")
        print(f"  Correlation (consumption vs price): {result['correlation']:.4f}")
        print(f"  Coincidence rating: {result['coincidence_rating'].upper()}")
        print(f"  {result['rating_message']}")
        
        # Interpretation
        print("\n" + "-"*80)
        print("INTERPRETATION:")
        if result['coincidence_rating'] == 'low':
            print("  ✓ Excellent! User demonstrates good consumption behavior by avoiding")
            print("    expensive periods. They consume less during the 20% most expensive hours.")
        elif result['coincidence_rating'] == 'medium':
            print("  ⚠ Neutral. User's consumption is roughly proportional to time.")
            print("    There's room for optimization by shifting usage to cheaper hours.")
        else:
            print("  ⚠ Warning! User consumes significantly more during expensive periods.")
            print("    Consider shifting flexible loads to cheaper hours for cost savings.")
        print("-"*80)
        
    except Exception as e:
        print(f"\n❌ Error during coincidence analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Test with 10% most expensive hours
    print("\n\n" + "="*80)
    print("ANALYZING TOP 10% MOST EXPENSIVE HOURS")
    print("="*80)
    
    try:
        result_10 = calculate_coincidence_factor(consumption_data, days=30, expensive_hours_pct=10.0)
        
        print("\n✅ Analysis completed!")
        print(f"  Top {result_10['expensive_hours_pct']:.0f}% hours: {result_10['num_expensive_hours']} hours")
        print(f"  Consumption during these hours: {result_10['consumption_coincidence_pct']:.2f}%")
        print(f"  Cost during these hours: {result_10['cost_coincidence_pct']:.2f}%")
        print(f"  Rating: {result_10['coincidence_rating'].upper()}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    # Test with 30% most expensive hours
    print("\n\n" + "="*80)
    print("ANALYZING TOP 30% MOST EXPENSIVE HOURS")
    print("="*80)
    
    try:
        result_30 = calculate_coincidence_factor(consumption_data, days=30, expensive_hours_pct=30.0)
        
        print("\n✅ Analysis completed!")
        print(f"  Top {result_30['expensive_hours_pct']:.0f}% hours: {result_30['num_expensive_hours']} hours")
        print(f"  Consumption during these hours: {result_30['consumption_coincidence_pct']:.2f}%")
        print(f"  Cost during these hours: {result_30['cost_coincidence_pct']:.2f}%")
        print(f"  Rating: {result_30['coincidence_rating'].upper()}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


def test_coincidence_comparison():
    """Compare coincidence factors across multiple users"""
    print("\n\n" + "="*80)
    print("COMPARING COINCIDENCE FACTORS ACROSS USERS")
    print("="*80)
    
    household_data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'household_data')
    test_users = ['user_data_10265.csv', 'user_data_10625.csv', 'user_data_11220.csv']
    
    results = []
    
    for user_file in test_users:
        user_path = os.path.join(household_data_dir, user_file)
        
        if not os.path.exists(user_path):
            continue
        
        try:
            consumption_data = pd.read_csv(user_path)
            result = calculate_coincidence_factor(consumption_data, days=30, expensive_hours_pct=20.0)
            
            results.append({
                'user': user_file,
                'consumption_coincidence': result['consumption_coincidence_pct'],
                'cost_coincidence': result['cost_coincidence_pct'],
                'correlation': result['correlation'],
                'rating': result['coincidence_rating']
            })
            
        except Exception as e:
            print(f"⚠ Skipping {user_file}: {str(e)}")
    
    if results:
        print("\n" + "="*80)
        print("COINCIDENCE FACTOR COMPARISON")
        print("="*80)
        print(f"{'User':<30} | {'Consumption %':<15} | {'Cost %':<10} | {'Correlation':<12} | {'Rating'}")
        print("-"*80)
        
        for r in results:
            rating_icon = "✓" if r['rating'] == 'low' else "⚠" if r['rating'] == 'medium' else "✗"
            print(f"{rating_icon} {r['user']:<28} | {r['consumption_coincidence']:>13.2f}% | {r['cost_coincidence']:>8.2f}% | {r['correlation']:>12.4f} | {r['rating']}")
        
        print("\n" + "-"*80)
        print("Legend: ✓ = Good (low coincidence), ⚠ = Neutral (medium), ✗ = Poor (high coincidence)")
        print("-"*80)


if __name__ == "__main__":
    test_with_user_data()
    test_with_multiple_users()
    test_coincidence_factor()
    test_coincidence_comparison()
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)
