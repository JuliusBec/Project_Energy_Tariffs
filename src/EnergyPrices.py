import pip


pip install pandas matplotlib

import pandas as pd
import matplotlib.pyplot as plt

def get_german_price_data(file_path: str = 'data/training_dataset.csv') -> pd.DataFrame:
    price_data = pd.read_csv(file_path, sep=';')
    german_price_data = price_data.iloc[:,0:3]
    return german_price_data

def adjust_df_format(df: pd.DataFrame) -> pd.DataFrame:
    df.drop(columns=['Datum bis'], inplace=True)
    df.columns.values[0:2] = ['datetime', 'market_price']
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