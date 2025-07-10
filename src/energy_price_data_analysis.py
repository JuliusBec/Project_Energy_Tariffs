import pandas as pd
import energy_prices
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose
import time

# auslesen der csv datei
temperature_data = pd.read_csv("data/temperature_data_01:21-05:25.csv")

temperature_data['datetime'] = pd.to_datetime(temperature_data['MESS_DATUM'], format='%Y%m%d%H')
temperature_data.drop(columns=['MESS_DATUM', "STATIONS_ID", "eor", "QN_9"], inplace=True)

# Rename columns
temperature_data.rename(columns={'TT_TU': 'temperature', 'RF_TU': 'relative_humidity'}, inplace=True)

# Move 'datetime' to the first column
cols = ['datetime'] + [col for col in temperature_data.columns if col != 'datetime']
temperature_data = temperature_data[cols]

market_data = energy_prices.adjust_df_format(energy_prices.get_german_price_data())

market_data = market_data.sort_values('datetime')
temperature_data = temperature_data.sort_values('datetime')

# Use merge_asof to forward-fill temperature data for each market_data row
combined_data = pd.merge_asof(
    market_data,
    temperature_data,
    on='datetime',
    direction='backward'
)

# save combined data to CSV
combined_data.to_csv("data/combined_market_temperature_data.csv", index=False)

def plot_energy_prices(data: pd.DataFrame):
    """
    Plot energy prices over time.
    
    :param data: DataFrame containing energy prices with a 'datetime' column.
    """
    plt.figure(figsize=(12, 6))
    plt.plot(data['datetime'], data['market_price'], label='Market Price', color='blue')
    plt.xlabel('Date')
    plt.ylabel('Price (EUR/MWh)')
    plt.title('Energy Prices Over Time')
    plt.legend()
    plt.grid()
    plt.show()

def check_stationarity(series: pd.Series):
    """
    Check if a time series is stationary using the Augmented Dickey-Fuller test.
    
    :param series: Time series data.
    :return: Tuple of test statistic and p-value.
    """
    result = adfuller(series)
    p_value = result[1]
    print(f"ADF Statistic: {result[0]}")
    print(f"p-value: {p_value}")
    if p_value < 0.05:
        print("The time series is stationary.")
    else:
        print("The time series is non-stationary. Differencing may be required.")
        
def seasonal_decompose_and_plot(series: pd.Series):
    """
    Decompose a time series into trend, seasonal, and residual components.

    :param series: Time series data.
    """
    # Daily seasonality (96 periods per day for 15-min intervals)
    decomp_daily = seasonal_decompose(series.tail(96 * 20), model='additive', period=96)
    fig1 = decomp_daily.plot()
    fig1.suptitle('Daily Seasonality Decomposition', fontsize=16)
    # Reduce marker size for residual and seasonal subplots
    for i, ax in enumerate(fig1.axes):
        for line in ax.get_lines():
            line.set_linewidth(1)
        # If this is the residual subplot (usually the last one), plot as scatter with small dots
        if i == 3:  # residual is usually the 4th subplot
            ax.cla()  # clear the current lines
            ax.scatter(
                decomp_daily.resid.index, 
                decomp_daily.resid.values, 
                s=5, 
                color='tab:red', 
                alpha=0.7, 
            )
            ax.set_ylabel('resid')
            ax.legend()
    plt.tight_layout()
    plt.show()

    # Monthly seasonality
    monthly_data = series.resample('D').mean()  # Resample to daily frequency
    decomp_monthly = seasonal_decompose(monthly_data, model="additive", period=30)  # 30 days for monthly seasonality
    fig2 = decomp_monthly.plot()
    fig2.suptitle('Monthly Seasonality Decomposition', fontsize=16)
    # Reduce marker size for residual and seasonal subplots
    for i, ax in enumerate(fig2.axes):
        for line in ax.get_lines():
            line.set_linewidth(1)
        if i == 3:
            ax.cla()
            ax.scatter(
                decomp_monthly.resid.index, 
                decomp_monthly.resid.values, 
                s=5, 
                color='tab:red', 
                alpha=0.7, 
            )
            ax.set_ylabel('resid')
            ax.legend()
    plt.tight_layout()
    plt.show()
    
    
check_stationarity(combined_data['market_price'])

# Set the index to the datetime column before decomposition and plotting
series_with_datetime_index = combined_data.set_index('datetime')['market_price']
# seasonal_decompose_and_plot(series_with_datetime_index)

# lags = 96 for 15-minute intervals, adjust as needed
def plot_acf_pacf(series: pd.Series, lags=96):
    """
    Plot ACF and PACF for a time series.
    
    :param series: Time series data.
    :param lags: Number of lags to consider.
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    plot_acf(series, lags=lags, ax=axes[0])
    plot_pacf(series, lags=lags, ax=axes[1])
    axes[0].set_title('Autocorrelation Function (ACF)')
    axes[1].set_title('Partial Autocorrelation Function (PACF)')
    plt.tight_layout()
    plt.show()
