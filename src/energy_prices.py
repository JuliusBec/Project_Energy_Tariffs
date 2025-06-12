import pandas as pd
import matplotlib.pyplot as plt

def get_german_price_data():
    price_data = pd.read_csv('data/Gro_handelspreise_202311010000_202411020000_Viertelstunde.csv', sep=';')
    german_price_data = price_data.iloc[:,0:3]
    return german_price_data

def adjust_df_format(df: pd.DataFrame) -> pd.DataFrame:
# Convert the first three columns to appropriate formats
    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], format='%d.%m.%Y %H:%M')
    df.iloc[:, 1] = pd.to_datetime(df.iloc[:, 1], format='%d.%m.%Y %H:%M')
    df.iloc[:, 2] = df.iloc[:, 2].str.replace(',', '.').astype(float)
    df.iloc[:, 2] = df.iloc[:, 2] / 1000  # Convert from Euro/MWh to Euro/kWh
    return df

def sample_data(df: pd.DataFrame, interval: int) -> pd.DataFrame:
# Sample every 6th hour (24 rows for 24 hours)
    sampled_data = df.iloc[::24, :]
    return sampled_data

def plot_energy_prices(df: pd.DataFrame):
# Plot the sampled data
    plt.plot(df.iloc[:, 0], df.iloc[:, 2])
    plt.ylabel("Strompreis in Euro pro MWh")
    plt.xlabel("Zeit")
    plt.title('Every 6th Hour Price Data')
    plt.tight_layout()
    plt.show()
