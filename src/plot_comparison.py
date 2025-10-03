#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import matplotlib.pyplot as plt

def plot_price_comparison():
    """Create a clear comparison plot of actual vs forecasted prices"""
    try:
        # Read the data
        actual_data = pd.read_csv('output/smard_dayahead_de.csv')
        forecast = pd.read_csv('output/forecast.csv')
        
        # Convert dates
        actual_data['ds'] = pd.to_datetime(actual_data['ds'])
        forecast['ds'] = pd.to_datetime(forecast['ds'])
        
        # Set up the plot with a clean style
        plt.style.use('bmh')  # Using a built-in style that's good for data visualization
        plt.figure(figsize=(20, 10))
        
        # Plot historical prices
        plt.plot(actual_data['ds'], actual_data['price_eur_per_mwh'], 
                label='Historical Prices', color='blue', alpha=0.6, linewidth=2)
        
        # Plot forecast
        plt.plot(forecast['ds'], forecast['yhat'], 
                label='Forecasted Prices', color='red', linestyle='--', linewidth=2)
        
        # Add confidence intervals
        plt.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'],
                        color='red', alpha=0.1, label='95% Confidence Interval')
        
        # Customize plot
        plt.title('Energy Price Forecast Comparison', fontsize=16, pad=20)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Price (EUR/MWh)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=12)
        
        # Add vertical line for current date
        current_date = pd.Timestamp.now()
        plt.axvline(x=current_date, color='green', linestyle=':', label='Current Date')
        
        # Adjust layout and save
        plt.tight_layout()
        
        # Save to desktop for easy access
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        output_path = os.path.join(desktop, 'price_comparison.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Comparison plot saved to: {output_path}")
        
    except Exception as e:
        print(f"Error creating comparison plot: {str(e)}")

if __name__ == "__main__":
    plot_price_comparison()