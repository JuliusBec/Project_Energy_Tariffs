#!/usr/bin/env python3
"""Test script for the create_chart_data method"""

import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.forecasting.price_forecasting.EnergyPriceForecast import create_chart_data
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_chart_data():
    """Test the create_chart_data method"""
    try:
        logging.info("Testing create_chart_data method...")
        
        # Generate chart data
        chart_data = create_chart_data()
        
        if chart_data is None:
            logging.error("Failed to create chart data")
            return
        
        # Print summary
        logging.info("\n" + "="*80)
        logging.info("CHART DATA SUMMARY")
        logging.info("="*80)
        
        metrics = chart_data['metrics']
        logging.info(f"\nHistorical Data:")
        logging.info(f"  Period: {metrics['historical_start_date']} to {metrics['historical_end_date']}")
        logging.info(f"  Days: {metrics['historical_period_days']}")
        logging.info(f"  Avg Price: {metrics['avg_historical_price']} EUR/MWh")
        logging.info(f"  Price Range: {metrics['min_historical_price']} - {metrics['max_historical_price']} EUR/MWh")
        
        logging.info(f"\nForecast Data:")
        logging.info(f"  Period: {metrics['forecast_start_date']} to {metrics['forecast_end_date']}")
        logging.info(f"  Days: {metrics['forecast_period_days']}")
        logging.info(f"  Avg Price: {metrics['avg_forecast_price']} EUR/MWh")
        logging.info(f"  Price Range: {metrics['min_forecast_price']} - {metrics['max_forecast_price']} EUR/MWh")
        
        logging.info(f"\nPrice Trend:")
        logging.info(f"  Expected Change: {metrics['price_change_percentage']}%")
        
        logging.info(f"\nData Structure:")
        logging.info(f"  Historical timestamps: {len(chart_data['historical_data']['timestamps'])}")
        logging.info(f"  Forecast timestamps: {len(chart_data['forecast_data']['timestamps'])}")
        logging.info(f"  Combined timeline: {len(chart_data['combined_data']['timestamps'])} days")
        
        # Save sample output for frontend integration
        output_dir = 'app_data'
        output_path = os.path.join(output_dir, 'price_chart_data_sample.json')
        with open(output_path, 'w') as f:
            json.dump(chart_data, f, indent=2)
        logging.info(f"\nSample chart data saved to: {output_path}")
        
        logging.info("="*80)
        logging.info("Chart data test completed successfully!")
        
        return chart_data
        
    except Exception as e:
        logging.error(f"Error in chart data test: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    test_chart_data()
