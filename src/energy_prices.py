import pandas as pd
import matplotlib.pyplot as plt

def get_german_price_data():
    price_data = pd.read_csv('data/market_prices_01:21-05:25.csv', sep=';')
    german_price_data = price_data.iloc[:,0:3]
    return german_price_data

def adjust_df_format(df: pd.DataFrame) -> pd.DataFrame:
    df.drop(columns=['Datum bis'], inplace=True)
    df.rename(columns={'Datum von': 'datetime', 'Deutschland/Luxemburg [€/MWh] Berechnete Auflösungen': 'market_price'}, inplace=True)
    df["datetime"] = pd.to_datetime(df["datetime"], format='%d.%m.%Y %H:%M')
    df["market_price"] = (df["market_price"].str.replace(',', '.').astype(float)
    )
    return df

def sample_data(df: pd.DataFrame, interval: int) -> pd.DataFrame:
# Sample energy prices at a given interval
    sampled_data = df.iloc[::interval, :]
    return sampled_data

def plot_energy_prices(df: pd.DataFrame):
# Plot the sampled data
    plt.plot(df["datetime"], df["market_price"])
    plt.ylabel("Strompreis in Euro pro MWh")
    plt.xlabel("Zeit")
    plt.title(f'Price Data')
    plt.tight_layout()
    plt.show()