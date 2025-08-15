import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from Chronos import ChronosModel, TimeSeries
import matplotlib.pyplot as plt

class ChronosForecaster:
    """
    A time series forecaster using Chronos, reading data from a CSV file in the data folder.
    """

    def __init__(self, csv_filename, date_col='datetime', value_col='market_price', forecast_steps=96):
        self.csv_filename = csv_filename
        self.date_col = date_col
        self.value_col = value_col
        self.forecast_steps = forecast_steps
        self.data = None
        self.ts = None
        self.model = None
        self.forecast_result = None

    def read_data(self):
        """Read the CSV file and prepare the time series."""
        self.data = pd.read_csv(self.csv_filename, sep=None, engine='python')
        self.data[self.date_col] = pd.to_datetime(self.data[self.date_col])
        self.data.set_index(self.date_col, inplace=True)
        self.ts = TimeSeries.from_dataframe(self.data, time_col=self.date_col, value_cols=[self.value_col])

    def fit(self, model_name="chronos_forecaster", epochs=10):
        """Fit a Chronos model to the time series."""
        if self.ts is None:
            self.read_data()
        self.model = ChronosModel(model_name=model_name)
        self.model.fit(self.ts, epochs=epochs)
        print(f"Model '{model_name}' fitted.")

    def forecast(self):
        """Forecast future values using Chronos."""
        if self.model is None:
            raise ValueError("Model must be fit before forecasting.")
        self.forecast_result = self.model.forecast(self.ts, steps=self.forecast_steps)
        forecast_index = pd.date_range(start=self.data.index[-1], periods=self.forecast_steps+1, freq='15T')[1:]
        forecast_df = pd.DataFrame({
            'forecast': self.forecast_result['forecast'],
            'lower_ci': self.forecast_result.get('lower_ci', self.forecast_result['forecast']),
            'upper_ci': self.forecast_result.get('upper_ci', self.forecast_result['forecast'])
        }, index=forecast_index)
        return forecast_df

    def plot_forecast(self, forecast_df):
        """Plot the historical data and forecast."""
        plt.figure(figsize=(12, 6))
        plt.plot(self.data.index, self.data[self.value_col], label='Historical')
        plt.plot(forecast_df.index, forecast_df['forecast'], color='red', label='Forecast')
        plt.fill_between(forecast_df.index, forecast_df['lower_ci'], forecast_df['upper_ci'], color='pink', alpha=0.3)
        plt.axvline(x=self.data.index[-1], color='black', linestyle='--', alpha=0.7)
        plt.title('Chronos Forecast')
        plt.xlabel('Date')
        plt.ylabel(self.value_col)
        plt.legend()
        plt.tight_layout()
        plt.show()

# Example usage:
# forecaster = ChronosForecaster('data/combined_market_temperature_data.csv')
# forecaster.fit()
# forecast_df = forecaster.forecast()
# forecaster.plot_forecast(forecast_df)
