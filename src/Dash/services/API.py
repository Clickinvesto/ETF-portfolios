import json
import decimal
import ast
import logging
from io import BytesIO

import polars as pl
from pathlib import Path
import pandas as pd
import numpy as np
from itertools import combinations, product
from .mixins.S3mixin import S3Mixin

# Python is doing Bankers rounding by default. setting the rounding context
context = decimal.getcontext()
context.rounding = decimal.ROUND_HALF_UP


class API(S3Mixin):

    def __init__(self) -> None:
        self.working_directory = Path.cwd()
        self.data_folder = "src/Dash/data"
        self.dispersion_file = "new_result.csv"
        self.series_file = "Series.csv"

        self.dispersion_path = Path.joinpath(
            self.working_directory, self.data_folder, self.dispersion_file
        )
        self.series_path = Path.joinpath(
            self.working_directory, self.data_folder, self.series_file
        )

        self.config_folder = "src/Dash/config"
        self.graph_file = "graphs.json"
        self.graph_path = Path.joinpath(
            self.working_directory, self.config_folder, self.graph_file
        )

    def update_config(self):
        f = open(self.graph_path)
        data = json.load(f)
        self.cofiguration = data

    def load_dispersion_data(self):

        s3file = self.get_data_file("data/" + self.dispersion_file)
        s3_file_content = s3file.read()
        # Convert bytes to BytesIO for compatibility with Polars
        file_like_object = BytesIO(s3_file_content)
        df = pl.read_csv(
            file_like_object,
            separator=",",
            low_memory=True,
            new_columns=["Series", "Combination", "Weights", "CAGR", "Risk"],
        )
        logging.error("Finished")
        return df

    def get_dispersion_data(self):
        df = self.load_dispersion_data()
        df = df.select(["Series", "CAGR", "Risk"])
        return df

    def get_series_combination_weights(self, series):
        df = self.load_dispersion_data()
        selected_row = df.filter(pl.col("Series") == series)
        combination = list(ast.literal_eval(selected_row["Combination"][0]))
        weights = list(ast.literal_eval(selected_row["Weights"][0]))
        weights = [float(weight) for weight in weights]
        return combination, weights

    def get_weighted_series(self, series):
        self.update_config()
        configuration = self.cofiguration.get("performance")
        reference_series = configuration.get("reference_series", "RI")

        combination, weights = self.get_series_combination_weights(series)
        df = pd.read_csv(
            self.get_data_file("data/" + self.series_file),
            sep=",",
            header=0,
            decimal=".",
        )

        df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")
        df.set_index("Date", inplace=True)

        highest_valid_index = max(df[col].first_valid_index() for col in combination)
        normalized_series = pd.DataFrame(
            {
                col: df[col]
                .loc[df.index >= highest_valid_index]
                .div(df[col].loc[highest_valid_index])
                * 100
                * weight
                for col, weight in zip(combination, weights)
                if weight > 0
            }
        )
        combined_series = normalized_series.sum(axis=1)
        data = pd.concat(
            [
                df.loc[normalized_series.index, reference_series]
                / df.loc[normalized_series.index, reference_series][0]
                * 100,
                combined_series,
            ],
            axis=1,
        )
        data.columns = [reference_series, series]
        return data, reference_series, len(data)

    def get_series_data(self, series=False, polar=False):
        df = pd.read_csv(
            self.get_data_file("data/" + self.series_file),
            sep=",",
            header=0,
            decimal=".",
        )
        if polar:
            polars_df = pl.from_pandas(df)
            # columns_to_cast = polars_df.columns[1:]
            # print(columns_to_cast)
            # polars_df = polars_df.with_columns(
            #    [
            #        pl.col(column).cast(pl.Float64).alias(column)
            #        for column in columns_to_cast
            #    ]
            # )
            return polars_df

        df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")
        df.set_index("Date", inplace=True)

        return df

    def calc_CAGR(self, normalised_data, number_of_month=False):
        if not number_of_month:
            number_of_month = len(normalised_data)
        cagr = (
            normalised_data.iloc[-1].apply(
                lambda x: (x / 100) ** (12 / number_of_month) - 1
            )
            * 100
        )

        risk = normalised_data / normalised_data.shift()
        risk = risk[risk < 1.0].count() / number_of_month * 100
        return cagr, risk

    def get_series(self, series=False):
        df = self.load_dispersion_data()
        return df.select("Series").to_series().to_list()


class CalculateCombinations(API):
    def calc_metrics_pandas(self, portfolio):
        # Calculate the number of months
        number_of_months = len(portfolio)

        # Calculate the CAGR (Compound Annual Growth Rate)
        temp = portfolio.iloc[-1] / 100
        cagr = (temp ** (12 / number_of_months) - 1) * 100

        # Calculate the risk
        risk = portfolio / portfolio.shift(1)
        risk = risk.dropna()  # Drop NaN values that result from shifting
        risk_below_one = risk[risk < 1.0]
        risk_count = len(risk_below_one)
        risk_percentage = (risk_count / number_of_months) * 100

        return cagr, risk_percentage

    def calc_metrics_polars(self, portfolio):
        number_of_month = portfolio.height
        print(number_of_month)
        temp = portfolio.select(pl.last("sum")) / 100
        cagr = temp.item(0, 0) ** (12 / number_of_month) - 1
        cagr *= 100

        risk = portfolio / portfolio.shift(1)
        print(risk)
        risk = (
            risk.select("sum")
            .filter(pl.col("sum").is_not_null())
            .filter(pl.col("sum") < 1.0)
            .count()
            .item(0, 0)
            / number_of_month
            * 100
        )
        return cagr, risk

    def vec_calc_CAGR(self, normalised_data, number_of_month=None):
        if number_of_month is None:
            number_of_month = len(normalised_data)
        # Convert normalised_data to numpy array for compatibility with np.float
        normalised_data_np = np.array(normalised_data)
        # Calculate CAGR using vectorized operations
        cagr = (normalised_data_np[-1] / 100) ** (12 / number_of_month) - 1
        cagr *= 100

        # Calculate risk using vectorized operations and np.less
        risk = normalised_data_np / np.roll(normalised_data_np, shift=1)
        risk = np.less(risk, 1.0).sum() / number_of_month * 100

        return cagr, risk
        # Generate all combinations of time series with different weights using NumPy broadcasting

    def generate_weight_combinations(self, column_names, step_size=0.2):
        return product(np.arange(0, 1.01, step_size), repeat=len(column_names))

    def calculate_metrics_vectorized(series):
        returns = series.pct_change().dropna()
        CAGR = (series.iloc[-1] / series.iloc[0]) ** (
            1 / len(series.index.year.unique())
        ) - 1
        risk = np.std(returns) * np.sqrt(len(series))
        return CAGR, risk

    def calc_CAGR_Risk_combinations(self):
        # Function to calculate CAGR and risk using vectorized operations
        def calculate_metrics_vectorized(series):
            returns = series.pct_change().dropna()
            CAGR = (series.iloc[-1] / series.iloc[0]) ** (
                1 / len(series.index.year.unique())
            ) - 1
            risk = np.std(returns) * np.sqrt(len(series))
            return CAGR, risk

        df = self.get_series_data()
        column_names = df.columns
        column_names = column_names[1:]

        # Set the chunk size
        chunk_size = 100

        weights_list = product(np.arange(0, 1.01, 0.25), repeat=len(column_names))
        # Get the total number of combinations
        total_combinations = len(
            list(combinations(column_names, r=len(column_names)))
        ) * 5 ** len(column_names)

        # Counter variable for progress tracking
        progress_counter = 0

        header_written = False
        result_csv_path = "/home/simon/Documents/Pure_Inference/Kunden/Andres/dashboard/src/Dash/data/result.csv"
        index = 1

        # Iterate over combinations of weights
        for combo_weights in product(np.arange(0, 1.01, 0.2), repeat=len(column_names)):
            # Check if the weights sum up to 1.0
            if np.isclose(np.sum(combo_weights), 1.0):

                # Filter only time series with non-zero weights
                valid_columns = [
                    col
                    for col, weight in zip(column_names, combo_weights)
                    if weight > 0
                ]
                valid_weights = [weight for weight in combo_weights if weight > 0]
                # Find the highest valid index among valid time series
                highest_valid_index = max(
                    df[col].first_valid_index() for col in valid_columns
                )
                # Normalize each selected time series individually
                normalized_series = pd.DataFrame(
                    {
                        col: df[col]
                        .loc[df.index >= highest_valid_index]
                        .div(df[col].loc[highest_valid_index])
                        * 100
                        * weight
                        for col, weight in zip(valid_columns, valid_weights)
                    }
                )

                # Sum the normalized and weighted time series to get a single series
                combined_series = normalized_series.sum(axis=1)

                # Calculate CAGR and risk using vectorized operations
                cagr, risk = self.vec_calc_CAGR(combined_series)

                # Save combination parameters and metrics in a dictionary
                combination_params = {
                    "name": f"x{index}",
                    "combination": valid_columns,
                    "weights": valid_weights,
                    "cagr": cagr,
                    "risk": risk,
                }

                # Append the results to the CSV file
                if not header_written:
                    combination_params_df = pd.DataFrame([combination_params])
                    combination_params_df.to_csv(result_csv_path, mode="a", index=False)
                    header_written = True
                else:
                    combination_params_df = pd.DataFrame([combination_params])
                    combination_params_df.to_csv(
                        result_csv_path, mode="a", index=False, header=False
                    )

                # Increment the progress counter
                progress_counter += 1
                index += 1

                # Print progress
                if progress_counter % 100 == 0:
                    print(
                        f"Progress: {progress_counter} / {total_combinations} combinations processed"
                    )
