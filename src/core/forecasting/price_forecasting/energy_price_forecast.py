import pandas as pd
import requests
from datetime import datetime, timedelta
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt
import logging
import sys
import os

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/forecast.log', mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Print startup message
print("Starting Energy Price Forecast...", flush=True)
sys.stdout.flush()

# Configure matplotlib for non-interactive backend
plt.switch_backend('Agg')

class EnergyPriceForecast:
    def __init__(self):
        # SMARD API (German electricity market data)
        self.smard_base_url = "https://www.smard.de/app"
        self.smard_api = f"{self.smard_base_url}/chart_data/{{market_data_id}}/{{region}}/{{resolution}}/{{start}}/{{end}}"
        
        # SMARD API parameters
        self.market_data_id = "4169"  # ID for electricity spot market prices
        self.region = "DE"  # Germany
        self.resolution = "hour"  # Hourly resolution

    def fetch_historical_data(self, start_date, end_date):
        """
        Create sample historical data for testing
        Args:
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
        Returns:
            pd.DataFrame: DataFrame with columns ['timestamp', 'price', 'datetime']
        """
        try:
            # Generate sample data
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            date_range = pd.date_range(start=start_dt, end=end_dt, freq='H')
            
            # Create sample prices with daily and weekly patterns
            n_hours = len(date_range)
            base_price = 50
            
            # Add daily pattern (higher during day, lower at night)
            hour_pattern = 15 * np.sin(np.pi * date_range.hour / 12)
            
            # Add weekly pattern (lower on weekends)
            week_pattern = -10 * (date_range.dayofweek >= 5)
            
            # Add some random noise
            noise = np.random.normal(0, 5, n_hours)
            
            # Combine patterns
            prices = base_price + hour_pattern + week_pattern + noise
            
            # Create DataFrame
            df = pd.DataFrame({
                'datetime': date_range,
                'timestamp': date_range.astype(np.int64) // 10**6,  # Convert to milliseconds
                'price': prices
            })
            
            print(f"Generated {len(df)} sample records")
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from API: {str(e)}")
            return None
        except ValueError as e:
            print(f"Error processing data: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return None

    def preprocess_data(self, data):
        """
        Clean and prepare data for modeling
        Args:
            data (pd.DataFrame): Raw data from API
        Returns:
            tuple: (X, y) feature matrix and target vector
        """
        if data is None or data.empty:
            print("No data to preprocess")
            return None, None
            
        try:
            # Create copy to avoid modifying original data
            df = data.copy()
            
            # Clean missing values
            df = df.dropna()
            
            # Create time-based features
            df['hour'] = df['datetime'].dt.hour
            df['day_of_week'] = df['datetime'].dt.dayofweek
            df['month'] = df['datetime'].dt.month
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            
            # Create lag features
            df['price_lag_1'] = df['price'].shift(1)
            df['price_lag_24'] = df['price'].shift(24)  # 24-hour lag
            df['price_lag_168'] = df['price'].shift(168)  # Week lag
            
            # Create rolling mean features
            df['price_rolling_24h'] = df['price'].rolling(window=24).mean()
            df['price_rolling_7d'] = df['price'].rolling(window=168).mean()
            
            # Drop rows with NaN created by lag features
            df = df.dropna()
            
            # Prepare features (X) and target (y)
            feature_cols = ['hour', 'day_of_week', 'month', 'is_weekend', 
                          'price_lag_1', 'price_lag_24', 'price_lag_168',
                          'price_rolling_24h', 'price_rolling_7d']
            X = df[feature_cols]
            y = df['price']
            
            print(f"Preprocessed data shape: {X.shape}")
            return X, y
            
        except Exception as e:
            print(f"Error preprocessing data: {str(e)}")
            return None, None

    def train_model(self, X, y):
        """
        Train the prediction model
        Args:
            X (pd.DataFrame): Feature matrix
            y (pd.Series): Target vector
        Returns:
            tuple: (model, X_test, y_test) trained model and test data
        """
        try:
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Initialize and train model
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=20,
                min_samples_split=10,
                random_state=42,
                n_jobs=-1  # Use all CPU cores
            )
            model.fit(X_train, y_train)
            
            # Print feature importance
            feature_importance = pd.DataFrame({
                'feature': X.columns,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            print("\nFeature Importance:")
            print(feature_importance)
            
            return model, X_test, y_test
            
        except Exception as e:
            print(f"Error training model: {str(e)}")
            return None, None, None

    def predict_next_month(self, model, last_data):
        """
        Predict energy prices for the next month
        Args:
            model: Trained model
            last_data: Last known data point with features
        Returns:
            tuple: (dates, predictions) for the next month
        """
        try:
            # Get the last datetime and create future dates
            last_date = last_data.index[-1]
            future_dates = pd.date_range(
                start=last_date + timedelta(hours=1),
                periods=24 * 30,  # 30 days
                freq='h'
            )
            
            # Create future features DataFrame
            future_features = pd.DataFrame(index=future_dates)
            future_features['hour'] = future_dates.hour
            future_features['day_of_week'] = future_dates.dayofweek
            future_features['month'] = future_dates.month
            future_features['is_weekend'] = future_dates.dayofweek.isin([5, 6]).astype(int)
            
            # Initialize price lags with last known values
            last_prices = last_data[['price_lag_1', 'price_lag_24', 'price_lag_168',
                                   'price_rolling_24h', 'price_rolling_7d']].iloc[-1]
            
            predictions = []
            current_rolling_prices = last_data['price'].tolist()[-168:]  # Last week of prices
            
            # Predict one hour at a time
            for i in range(len(future_dates)):
                # Update lag features
                future_features.loc[future_dates[i], 'price_lag_1'] = last_prices['price_lag_1']
                future_features.loc[future_dates[i], 'price_lag_24'] = last_prices['price_lag_24']
                future_features.loc[future_dates[i], 'price_lag_168'] = last_prices['price_lag_168']
                future_features.loc[future_dates[i], 'price_rolling_24h'] = last_prices['price_rolling_24h']
                future_features.loc[future_dates[i], 'price_rolling_7d'] = last_prices['price_rolling_7d']
                
                # Make prediction for current hour
                current_prediction = model.predict(future_features.iloc[[i]])[0]
                predictions.append(current_prediction)
                
                # Update lag values for next iteration
                last_prices['price_lag_168'] = last_prices['price_lag_167'] if i >= 167 else current_prediction
                last_prices['price_lag_24'] = last_prices['price_lag_23'] if i >= 23 else current_prediction
                last_prices['price_lag_1'] = current_prediction
                
                # Update rolling averages
                current_rolling_prices.append(current_prediction)
                last_prices['price_rolling_24h'] = np.mean(current_rolling_prices[-24:])
                last_prices['price_rolling_7d'] = np.mean(current_rolling_prices[-168:])
            
            return future_dates, predictions
            
        except Exception as e:
            print(f"Error predicting future prices: {str(e)}")
            return None, None

    def plot_predictions(self, dates, predictions, title="Energy Price Forecast", include_history=None):
        """
        Plot price predictions
        Args:
            dates: Array of future dates
            predictions: Array of predicted prices
            title: Plot title
            include_history: Optional DataFrame with historical data to include
        """
        plt.figure(figsize=(15, 7))
        
        if include_history is not None:
            plt.plot(include_history.index, include_history['price'],
                    label='Historical', color='blue', alpha=0.5)
        
        plt.plot(dates, predictions, label='Forecast', color='red',
                linestyle='--' if include_history is not None else '-')
        
        plt.title(title)
        plt.xlabel('Date')
        plt.ylabel('Price (EUR/MWh)')
        plt.legend()
        plt.grid(True)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        
        # Add price statistics
        avg_price = np.mean(predictions)
        max_price = np.max(predictions)
        min_price = np.min(predictions)
        plt.axhline(y=avg_price, color='g', linestyle=':', label=f'Avg: {avg_price:.2f}')
        
        # Add text box with statistics
        stats_text = f'Forecast Statistics:\nAvg: {avg_price:.2f}\nMax: {max_price:.2f}\nMin: {min_price:.2f}'
        plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
                bbox=dict(facecolor='white', alpha=0.8),
                verticalalignment='top', fontsize=10)
        
        plt.tight_layout()
        plt.savefig('forecast_plot.png')
        plt.close()

def main():
    try:
        # Create output directory if it doesn't exist
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize forecaster
        logging.info("Initializing Energy Price Forecaster")
        forecaster = EnergyPriceForecast()
        
        # Set date range for historical data
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        logging.info(f"Date range: {start_date} to {end_date}")
        
        # Fetch and prepare data
        logging.info("Fetching historical data...")
        historical_data = forecaster.fetch_historical_data(start_date, end_date)
        if historical_data is None:
            logging.error("Failed to fetch historical data")
            return
        logging.info(f"Fetched {len(historical_data)} records")
        
        # Preprocess data
        logging.info("Preprocessing data...")
        X, y = forecaster.preprocess_data(historical_data)
        if X is None or y is None:
            logging.error("Failed to preprocess data")
            return
        logging.info(f"Preprocessed data shape: {X.shape}")
        
        # Train model
        logging.info("Training model...")
        model, X_test, y_test = forecaster.train_model(X, y)
        if model is None:
            logging.error("Failed to train model")
            return
        
        # Evaluate model on test set
        test_predictions = model.predict(X_test)
        mse = mean_squared_error(y_test, test_predictions)
        mae = mean_absolute_error(y_test, test_predictions)
        rmse = np.sqrt(mse)
        
        logging.info("Model Performance:")
        logging.info(f"Root Mean Square Error: {rmse:.2f} EUR/MWh")
        logging.info(f"Mean Absolute Error: {mae:.2f} EUR/MWh")
        
        # Generate next month predictions
        logging.info("Generating one-month forecast...")
        future_dates, future_predictions = forecaster.predict_next_month(model, X)
        if future_predictions is None:
            logging.error("Failed to generate forecast")
            return
        
        # Save predictions to CSV
        forecast_path = os.path.join(output_dir, 'forecast_results.csv')
        forecast_df = pd.DataFrame({
            'datetime': future_dates,
            'predicted_price': future_predictions
        })
        forecast_df.to_csv(forecast_path, index=False)
        logging.info(f"Forecast saved to '{forecast_path}'")
        
        # Calculate forecast statistics
        avg_price = np.mean(future_predictions)
        max_price = np.max(future_predictions)
        min_price = np.min(future_predictions)
        
        logging.info("\nForecast Statistics:")
        logging.info(f"Average Price: {avg_price:.2f} EUR/MWh")
        logging.info(f"Maximum Price: {max_price:.2f} EUR/MWh")
        logging.info(f"Minimum Price: {min_price:.2f} EUR/MWh")
        
        # Plot the forecast
        logging.info("Generating forecast plot...")
        historical_df = pd.DataFrame({'price': y}, index=X.index)
        forecaster.plot_predictions(
            future_dates, 
            future_predictions,
            title="Energy Price Forecast - Next 30 Days",
            include_history=historical_df
        )
        
        plot_path = os.path.join(output_dir, 'forecast_plot.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        logging.info(f"Plot saved to '{plot_path}'")
        
        # Save model performance metrics
        metrics_path = os.path.join(output_dir, 'model_metrics.txt')
        with open(metrics_path, 'w') as f:
            f.write(f"Model Performance Metrics\n")
            f.write(f"------------------------\n")
            f.write(f"Root Mean Square Error: {rmse:.2f} EUR/MWh\n")
            f.write(f"Mean Absolute Error: {mae:.2f} EUR/MWh\n\n")
            f.write(f"Forecast Statistics\n")
            f.write(f"------------------\n")
            f.write(f"Average Price: {avg_price:.2f} EUR/MWh\n")
            f.write(f"Maximum Price: {max_price:.2f} EUR/MWh\n")
            f.write(f"Minimum Price: {min_price:.2f} EUR/MWh\n")
        logging.info(f"Metrics saved to '{metrics_path}'")
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
