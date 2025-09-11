import pandas as pd
import matplotlib.pyplot as plt
import os
from src.core import energy_prices


def get_file_path():
    while True:
        file_path = input("Enter the path to the CSV file: ")
        if os.path.isfile(file_path):
            return file_path
        else:
            print("File not found. Please try again.")


def read_csv_from_file(file_path: str) -> pd.DataFrame:
    """
    Reads a CSV file and returns a DataFrame.

    :param file_path: Path to the CSV file.
    :return: DataFrame containing the CSV data.
    """
    return pd.read_csv(file_path)


my_csv = read_csv_from_file("data/sample_customer_17779.csv")


def adjust_df_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adjusts the DataFrame to ensure correct data types and formats.

    :param df: DataFrame to adjust.
    :return: Adjusted DataFrame.
    """
    df["datetime_str"] = df["X"] + " " + df["bis"]
    df["datetime"] = pd.to_datetime(df["datetime_str"])
    df = df.drop(columns=["X", "bis", "datetime_str"])
    return df

adjusted_df = adjust_df_format(my_csv)
print(adjusted_df.head())

def calculate_past_cost(df: pd.DataFrame) -> float:
    german_price_data = energy_prices.adjust_df_format(energy_prices.get_german_price_data())
    print(german_price_data.info())
    df["kWh"] = df["Wert"] * 0.25
    df["market_price"] = german_price_data.iloc[:, 2].values[:len(df)]
    df["cost"] = df["kWh"] * df["market_price"]
    cost = df["cost"].sum()
    cost = round(cost, 2)  # Round to 2 decimal places
    return cost


print("market price of energy consumed in the last year: " + str(calculate_past_cost(adjusted_df)) + " Euro")