"""
Debug script to investigate why demo_userdata_2.csv gets a high risk score
despite having good backtest results.
"""
import os
import sys
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backend.risk_analysis import (
    create_historic_risk_analysis,
    calculate_coincidence_factor,
    get_aggregated_risk_score,
    get_price_forecast_volatility
)
from src.backend.forecasting.energy_usage_forecast import create_backtest

def debug_demo_household_2():
    """Debug demo household 2 risk assessment"""
    
    # Load demo household 2 data
    data_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'data', 
        'household_data', 
        'demo_userdata_2.csv'
    )
    
    print("="*80)
    print("DEBUGGING DEMO HOUSEHOLD 2 RISK SCORE")
    print("="*80)
    print(f"\nLoading data from: {data_path}")
    
    if not os.path.exists(data_path):
        print(f"❌ File not found: {data_path}")
        return
    
    df = pd.read_csv(data_path)
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    print(f"✓ Loaded {len(df)} rows")
    print(f"  Date range: {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"  Total consumption: {df['value'].sum() * 0.25:.2f} kWh")  # 15-min intervals
    
    # App data directory
    app_data_dir = os.path.join(os.path.dirname(__file__), '..', 'app_data')
    
    # 1. Calculate historic risk analysis
    print("\n" + "-"*80)
    print("1. HISTORIC RISK ANALYSIS")
    print("-"*80)
    try:
        historic_risk = create_historic_risk_analysis(df, days=30, app_data_dir=app_data_dir)
        print(f"Market avg price: {historic_risk['market_avg_price']:.4f} €/kWh")
        print(f"User weighted price: {historic_risk['user_weighted_price']:.4f} €/kWh")
        print(f"Price differential: {historic_risk['price_differential']:.4f} €/kWh ({historic_risk['price_differential_pct']:.2f}%)")
        print(f"Risk exposure: {historic_risk['risk_exposure']}")
        print(f"Price volatility: {historic_risk['price_volatility']:.4f} €/kWh")
        print(f"Analysis period: {historic_risk['analysis_period']['start']} to {historic_risk['analysis_period']['end']}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        historic_risk = None
    
    # 2. Calculate coincidence factor
    print("\n" + "-"*80)
    print("2. COINCIDENCE FACTOR ANALYSIS")
    print("-"*80)
    try:
        coincidence = calculate_coincidence_factor(df, days=30, expensive_hours_pct=20.0, app_data_dir=app_data_dir)
        print(f"Expensive hours threshold: {coincidence['expensive_hours_pct']:.0f}%")
        print(f"Consumption during expensive hours: {coincidence['consumption_coincidence_pct']:.2f}%")
        print(f"Cost during expensive hours: {coincidence['cost_coincidence_pct']:.2f}%")
        print(f"Coincidence rating: {coincidence['coincidence_rating']}")
        print(f"Correlation (consumption vs price): {coincidence['correlation']:.4f}")
        print(f"Avg price (expensive hours): {coincidence['avg_price_expensive_hours']:.4f} €/kWh")
        print(f"Avg price (cheap hours): {coincidence['avg_price_cheap_hours']:.4f} €/kWh")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        coincidence = None
    
    # 3. Calculate backtest metrics
    print("\n" + "-"*80)
    print("3. BACKTEST ANALYSIS (FORECAST QUALITY)")
    print("-"*80)
    usage_forecast_quality = None
    try:
        backtest_data = create_backtest(df)
        usage_forecast_quality = backtest_data.get('metrics', {})
        
        # Print metrics safely
        mae = usage_forecast_quality.get('mae', 'N/A')
        if mae != 'N/A':
            print(f"MAE: {mae:.4f} kW")
        else:
            print(f"MAE: {mae}")
            
        mape = usage_forecast_quality.get('mape', 'N/A')
        if mape != 'N/A':
            print(f"MAPE: {mape:.2f}%")
        else:
            print(f"MAPE: {mape}")
            
        forecast_err = usage_forecast_quality.get('forecast_error_percentage', 'N/A')
        if forecast_err != 'N/A':
            print(f"Forecast error percentage: {forecast_err:.2f}%")
        else:
            print(f"Forecast error percentage: {forecast_err}")
            
        ci_width = usage_forecast_quality.get('avg_confidence_interval_width', 'N/A')
        if ci_width != 'N/A':
            print(f"Avg confidence interval width: {ci_width:.4f} kW")
        else:
            print(f"Avg confidence interval width: {ci_width}")
            
        rel_ci = usage_forecast_quality.get('relative_confidence_interval_width', 'N/A')
        if rel_ci != 'N/A':
            print(f"Relative CI width: {rel_ci:.2f}%")
        else:
            print(f"Relative CI width: {rel_ci}")
            
        num_pred = usage_forecast_quality.get('num_predictions', 'N/A')
        print(f"Number of predictions: {num_pred}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        usage_forecast_quality = None
    
    # 4. Calculate price forecast volatility
    print("\n" + "-"*80)
    print("4. PRICE FORECAST VOLATILITY")
    print("-"*80)
    try:
        forecast_price_volatility = get_price_forecast_volatility(app_data_dir=app_data_dir)
        print(f"Forecast std dev: {forecast_price_volatility.get('forecast_std_dev', 'N/A'):.4f} €/kWh")
        print(f"Avg CI width: {forecast_price_volatility.get('avg_confidence_interval_width', 'N/A')}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        forecast_price_volatility = {}
    
    # 5. Calculate aggregated risk score
    print("\n" + "="*80)
    print("5. AGGREGATED RISK SCORE (DYNAMIC TARIFF)")
    print("="*80)
    
    # Debug: print what we're passing
    if usage_forecast_quality:
        print(f"\nDebug - Usage forecast quality being passed:")
        print(f"  forecast_error_percentage: {usage_forecast_quality.get('forecast_error_percentage')}")
        print(f"  relative_confidence_interval_width: {usage_forecast_quality.get('relative_confidence_interval_width')}")
    else:
        print(f"\nDebug - No usage forecast quality available")
    
    if historic_risk and coincidence:
        try:
            risk_score = get_aggregated_risk_score(
                historic_risk,
                coincidence,
                forecast_price_volatility,
                is_dynamic=True,
                usage_forecast_quality=usage_forecast_quality
            )
            
            print(f"\nRisk Level: {risk_score['risk_level'].upper()}")
            print(f"Risk Score: {risk_score['risk_score']}/100")
            print(f"\nMessage: {risk_score['risk_message']}")
            print(f"Forecast quality included: {risk_score['forecast_quality_included']}")
            
            print("\nRisk Factors Breakdown:")
            for factor in risk_score['risk_factors']:
                impact_symbol = {
                    'positive': '✓',
                    'neutral': '○',
                    'negative': '✗'
                }.get(factor['impact'], '?')
                print(f"  {impact_symbol} {factor['factor']}: {factor['detail']}")
            
            # Detailed score breakdown
            print("\n" + "-"*80)
            print("SCORE BREAKDOWN ANALYSIS")
            print("-"*80)
            print("\nStarting score: 35 (baseline)")
            
            # Historic risk impact
            price_diff_pct = historic_risk['price_differential_pct']
            if price_diff_pct < -10:
                print(f"Historic risk: -12 points (very favorable, {abs(price_diff_pct):.1f}% below market)")
            elif price_diff_pct < -5:
                print(f"Historic risk: -8 points (favorable, {abs(price_diff_pct):.1f}% below market)")
            elif -5 <= price_diff_pct <= 5:
                print(f"Historic risk: +0 points (neutral, {price_diff_pct:.1f}% vs market)")
            elif price_diff_pct <= 10:
                print(f"Historic risk: +8 points (unfavorable, {price_diff_pct:.1f}% above market)")
            else:
                print(f"Historic risk: +12 points (very unfavorable, {price_diff_pct:.1f}% above market)")
            
            # Coincidence impact
            consumption_coincidence = coincidence['consumption_coincidence_pct']
            expensive_hours_pct = coincidence['expensive_hours_pct']
            coincidence_deviation = consumption_coincidence - expensive_hours_pct
            
            if coincidence_deviation < -10:
                print(f"Coincidence: -12 points (excellent, {consumption_coincidence:.1f}% vs {expensive_hours_pct:.0f}% threshold)")
            elif coincidence_deviation < -5:
                print(f"Coincidence: -8 points (good, {consumption_coincidence:.1f}% vs {expensive_hours_pct:.0f}% threshold)")
            elif -5 <= coincidence_deviation <= 5:
                print(f"Coincidence: +0 points (neutral, {consumption_coincidence:.1f}% vs {expensive_hours_pct:.0f}% threshold)")
            elif coincidence_deviation <= 15:
                print(f"Coincidence: +8 points (unfavorable, {consumption_coincidence:.1f}% vs {expensive_hours_pct:.0f}% threshold)")
            else:
                print(f"Coincidence: +12 points (very unfavorable, {consumption_coincidence:.1f}% vs {expensive_hours_pct:.0f}% threshold)")
            
            # Volatility impact
            volatility = historic_risk['price_volatility']
            if volatility > 0.06:
                print(f"Volatility: +8 points (very high, {volatility:.4f} €/kWh)")
            elif volatility > 0.045:
                print(f"Volatility: +5 points (high, {volatility:.4f} €/kWh)")
            elif volatility > 0.03:
                print(f"Volatility: +2 points (medium, {volatility:.4f} €/kWh)")
            else:
                print(f"Volatility: -3 points (low, {volatility:.4f} €/kWh)")
            
            # Forecast quality impact (prioritize forecast_error_percentage over CI width)
            if usage_forecast_quality:
                forecast_error_pct = usage_forecast_quality.get('forecast_error_percentage')
                relative_ci_width = usage_forecast_quality.get('relative_confidence_interval_width')
                
                if forecast_error_pct is not None:
                    # Use forecast error percentage as primary metric
                    if forecast_error_pct < 10:
                        print(f"Forecast quality: -8 points (excellent, error: {forecast_error_pct:.1f}%)")
                    elif forecast_error_pct < 20:
                        print(f"Forecast quality: -4 points (good, error: {forecast_error_pct:.1f}%)")
                    elif forecast_error_pct < 30:
                        print(f"Forecast quality: +3 points (fair, error: {forecast_error_pct:.1f}%)")
                    else:
                        print(f"Forecast quality: +10 points (poor, error: {forecast_error_pct:.1f}%)")
                elif relative_ci_width is not None:
                    # Fallback to CI width
                    if relative_ci_width < 40:
                        print(f"Forecast quality: -8 points (excellent, CI: {relative_ci_width:.1f}%)")
                    elif relative_ci_width < 80:
                        print(f"Forecast quality: -4 points (good, CI: {relative_ci_width:.1f}%)")
                    elif relative_ci_width < 120:
                        print(f"Forecast quality: +3 points (fair, CI: {relative_ci_width:.1f}%)")
                    else:
                        print(f"Forecast quality: +10 points (poor, CI: {relative_ci_width:.1f}%)")
            
            # Price forecast volatility impact
            price_std_dev = forecast_price_volatility.get('forecast_std_dev')
            if price_std_dev:
                if price_std_dev > 0.05:
                    print(f"Price forecast volatility: +8 points (very high, {price_std_dev:.4f} €/kWh)")
                elif price_std_dev > 0.035:
                    print(f"Price forecast volatility: +5 points (high, {price_std_dev:.4f} €/kWh)")
                elif price_std_dev > 0.025:
                    print(f"Price forecast volatility: +2 points (medium, {price_std_dev:.4f} €/kWh)")
                else:
                    print(f"Price forecast volatility: -3 points (low, {price_std_dev:.4f} €/kWh)")
            
            print(f"\nFinal score: {risk_score['risk_score']}/100")
            
        except Exception as e:
            print(f"❌ Error calculating risk score: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print("Cannot calculate risk score - missing required data")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    debug_demo_household_2()
