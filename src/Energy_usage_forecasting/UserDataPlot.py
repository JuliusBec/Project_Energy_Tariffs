import matplotlib.pyplot as plt
import pandas as pd
import sys

user_id = input("Enter User ID: ")

print(f"Loading data for user ID: {user_id}")
usage_df = pd.read_csv("data/user_data/user_data_"+str(user_id)+".csv", parse_dates=["datetime"])

def plot_forecast(forecast_df):
    #parse datetime objects
    forecast_df["datetime"] = pd.to_datetime(forecast_df["datetime"])
    plt.figure(figsize=(12, 6))
    plt.plot(forecast_df["datetime"], forecast_df["usage_forecast_mean"], label="Forecasted Usage")
    plt.fill_between(forecast_df["datetime"], forecast_df["usage_lower_95"], forecast_df["usage_upper_95"], alpha=0.2)
    plt.xlabel("Date")
    plt.ylabel("Energy Usage (kWh)")
    plt.title("Energy Usage Forecast")
    
    plt.legend()
    plt.tight_layout()
    plt.show()
    
def plot_usage(usage_df):
    # Create a copy to avoid modifying original data
    df = usage_df.copy()
    
    # Extract hour of week (0-167: 0=Monday 00:00, 167=Sunday 23:00)
    df['hour_of_week'] = (df['datetime'].dt.dayofweek * 24 + df['datetime'].dt.hour)
    
    # Group by hour of week and calculate statistics
    weekly_stats = df.groupby('hour_of_week')['value'].agg([
        'mean',
        lambda x: x.quantile(0.05),  # 5th percentile (lower bound for 90%)
        lambda x: x.quantile(0.95)   # 95th percentile (upper bound for 90%)
    ]).reset_index()

    weekly_stats.columns = ['hour_of_week', 'mean_usage', 'lower_90', 'upper_90']

    # Create datetime index for plotting (using a reference week)
    import pandas as pd
    reference_date = pd.Timestamp('2024-01-01')  # Start on a Monday
    weekly_stats['datetime'] = reference_date + pd.to_timedelta(weekly_stats['hour_of_week'], unit='hours')
    
    plt.figure(figsize=(12, 6))
    plt.plot(weekly_stats["datetime"], weekly_stats["mean_usage"], label="Average Weekly Usage", color="orange", linewidth=2)
    plt.fill_between(weekly_stats["datetime"], weekly_stats["lower_90"], weekly_stats["upper_90"], 
                     alpha=0.3, color="orange", label="90% of days fall within")
    plt.xlabel("Day of Week")
    plt.ylabel("Energy Usage (kWh)")
    plt.title("Average Weekly Energy Usage Pattern")
    plt.ylim(bottom=0)
    
    # Format x-axis to show day names
    import matplotlib.dates as mdates
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%A'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.xticks(rotation=45)
    
    plt.legend()
    plt.tight_layout()
    plt.show()

plot_usage(usage_df)

chronos_forecast = pd.read_csv("data/usage_forecasting/user_data_" + str(user_id) + "_forecast_chronos.csv")

plot_forecast(chronos_forecast)