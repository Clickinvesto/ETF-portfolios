import dash_mantine_components as dmc
import dash
import polars as pl
from pathlib import Path
from dash import (
    register_page,
    long_callback,
    html,
    dcc,
    callback,
    Input,
    Output,
    State,
    ctx,
    no_update,
    ALL,
)
from decimal import Decimal, getcontext
import pandas as pd
import numpy as np
import decimal
import time
from math import comb
from flask import current_app
from dash.exceptions import PreventUpdate
from itertools import combinations, product
from flask import session, redirect
from src.Dash.services.API import CalculateCombinations
from src.Dash.services.graph import plotting_engine

from dash.long_callback import DiskcacheLongCallbackManager
import diskcache

cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)

api = CalculateCombinations()
plotter = plotting_engine()

app = dash.get_app()

context = decimal.getcontext()
context.rounding = decimal.ROUND_HALF_UP

import itertools
import numpy as np

register_page(__name__, path=current_app.config["URL_SETTINGS"])
page_name = "settings"


def get_valid_weights(
    partitions, increment, total=1.0, precision=8, tolerance=1e-2, get_weights=False
):
    getcontext().prec = precision  # Set precision for Decimal operations

    increment = Decimal(str(increment))
    total = Decimal(str(total))
    tolerance = Decimal(str(tolerance))
    # Generate all possible weights with the given increment
    weights = [i * increment for i in range(int((total / increment)) + 1)]

    # Exclude combinations where one weight is 100% and find valid combinations
    valid_weights = [
        comb  # Sort to treat different orders as the same combination
        for comb in itertools.product(weights, repeat=partitions)
        if abs(sum(comb) - total) <= tolerance
        and sum(weight > Decimal("0") for weight in comb) == partitions
    ]

    if get_weights:
        return valid_weights
    return len(valid_weights)


def get_number_of_portfolios(column_names, partitions, interval_increment):
    # Calculate all unique combinations of these elements of length 'partitions'
    number_portfolios = 0
    # Calculate the number of valid weight distributions for each combination
    for partiton in range(0, partitions):
        partiton += 1
        total_combinations = list(itertools.combinations(column_names, partiton))
        partitions_per_combination = get_valid_weights(
            partitions=partiton, increment=interval_increment
        )
        number_portfolios += len(total_combinations) * partitions_per_combination

    return number_portfolios


def precompute_weight_combinations(max_items, partition):
    """Precompute all valid weight combinations for portfolios of sizes 1 to max_items."""
    weight_combinations = {}
    increment = 1 / partition
    possible_weights = np.arange(increment, 1.01, increment)
    for size in range(1, max_items + 1):
        weight_combinations[size] = [
            combo
            for combo in itertools.product(possible_weights, repeat=size)
            if np.isclose(sum(combo), 1.0)
        ]
    return weight_combinations


def generate_portfolios(column_names, weight_combinations):
    """Generate portfolios and perform calculations for each."""
    for size in range(1, len(column_names) + 1):
        for indices_combo in itertools.combinations(column_names, size):
            for weights in weight_combinations[size]:
                # Perform your specific calculation for the portfolio here
                # Example: calculate_portfolio_value(indices_combo, weights)
                pass


def layout(socket_ids=None, **kwargs):
    if socket_ids == None:
        raise PreventUpdate
    # ToDo in the future we can add other information here as well for example from the user
    user = session.get("user", False)
    if not user:
        return dmc.Container()
    # Wait for the socket to be connected
    return full_layout()


def full_layout():
    return dmc.Container(
        [
            dmc.Title("Weight Calculation", order=2),
            dmc.Grid(
                dmc.Paper(
                    [
                        dmc.Group(
                            [
                                dmc.NumberInput(
                                    label="Portfolio Partitions",
                                    description="Default is 4",
                                    value=4,
                                    max=10,
                                    min=1,
                                    step=1,
                                    style={"width": 200},
                                    id="partitions",
                                ),
                                dmc.NumberInput(
                                    label="Step size of distribution",
                                    description="Default is 0.2 and recommended",
                                    value=0.2,
                                    max=1,
                                    min=0,
                                    step=0.01,
                                    precision=6,
                                    style={"width": 200},
                                    id="step_size",
                                ),
                                dmc.NumberInput(
                                    label="Limit the result to the top X regardin CARG",
                                    description="Default is 2000",
                                    value=2000,
                                    max=5000,
                                    min=100,
                                    step=100,
                                    style={"width": 200},
                                    id="top_x",
                                ),
                                dmc.Button("Run calibration", id="run_calibration"),
                                dmc.Button(
                                    "Cancle Calibration",
                                    id="cancle_calibration",
                                    disabled=True,
                                ),
                            ]
                        ),
                        dmc.Space(h=20),
                        dmc.Text(id="total_number_portfolio"),
                        dmc.Space(h=20),
                        dmc.Progress(
                            animate=True,
                            id="progress_bar",
                            size="xl",
                        ),
                        dmc.Space(h=20),
                        dmc.Text(id="calculation_time"),
                    ]
                ),
                gutter="xl",
                style={
                    "width": "calc(100% - 1px)",
                },
            ),
        ],
        style={
            "overflow-y": "scroll",
            "position": "fixed",
            "padding": "10px",
            "display": "block",
            "max-height": "calc(100% - 70px)",
        },
        fluid=True,
    )


@callback(
    Output("total_number_portfolio", "children"),
    Input("partitions", "value"),
    Input("step_size", "value"),
)
def update_total(number_partitions, interval_increment):
    df = api.get_series_data()
    column_names = df.columns
    column_names = column_names[1:]
    number = get_number_of_portfolios(
        column_names, number_partitions, interval_increment
    )
    return f"The total number of portfolios is: {number}"


def first_non_null_index(col):
    # Use `arg_true` on the `is_not_null` mask to find all non-null indices, then take the first
    indices = col.is_not_null().arg_true()
    return indices[0] if len(indices) > 0 else None


@app.long_callback(
    output=Output("calculation_time", "children"),
    inputs=Input("run_calibration", "n_clicks"),
    state=[
        State("step_size", "value"),
        State("partitions", "value"),
        State("top_x", "value"),
    ],
    running=[
        (Output("run_calibration", "disabled"), True, False),
        (Output("cancle_calibration", "disabled"), False, True),
    ],
    cancel=[Input("cancle_calibration", "n_clicks")],
    manager=long_callback_manager,
    progress=[Output("progress_bar", "value"), Output("progress_bar", "label")],
    progress_default=(0, f"{0}%"),
    interval=1000,
)
def callback(set_progress, n_clicks, interval_size, partitions, top_x):
    if ctx.triggered_id is None:
        raise PreventUpdate
    start_time = time.time()
    df = api.get_series_data(polar=True)
    # First remove the date column from the list
    column_names = df.columns
    column_names = column_names[2:]

    current_directory = Path.cwd() / "src/Dash/data"
    file_name = current_directory / "new_result.csv"
    filtered_path = current_directory / "check.csv"
    total_number = get_number_of_portfolios(column_names, partitions, interval_size)

    # Iterate over each combination and preccacluate the valid weights, exclude the first value which is RI
    index = 1
    percentage = 0
    header_written = False

    # Calculate RI
    normalised_df = (
        df.select(["RI"])
        .filter(pl.col("RI").is_not_null())
        .with_columns((pl.col("RI") / pl.col("RI").first() * 100))
    )
    cagr, risk = api.calc_metrics_polars(
        normalised_df.select(pl.col("RI").alias("sum"))
    )
    combination_params = {
        "name": f"RI",
        "combination": str(("RI",)),
        "weights": str(
            [
                1.0,
            ]
        ),
        "cagr": cagr,
        "risk": risk,
    }
    combination_params_df = pl.DataFrame([combination_params])
    try:
        with open(file_name, "x") as f:
            combination_params_df.write_csv(f)
    except FileExistsError:
        # File already exists, append without header
        with open(file_name, "a") as f:
            combination_params_df.write_csv(f, has_header=False)

    for partition in range(0, partitions):
        partition += 1
        for combination in itertools.combinations(column_names, partition):
            pre_computed_weights = get_valid_weights(
                partition, interval_size, get_weights=True
            )
            filter_condition = pl.col(combination[0]).is_not_null()
            for column in combination[1:]:
                filter_condition = filter_condition & pl.col(column).is_not_null()

            normalised_df = (
                df.select(list(combination))
                .filter(filter_condition)
                .with_columns(
                    [
                        (pl.col(column) / pl.col(column).first() * 100)
                        for column in combination
                    ]
                )
            )
            for weight_comb in pre_computed_weights:
                # Calcuclate Portfolio
                weighted_df = normalised_df.with_columns(
                    [
                        (pl.col(column) * float(weight_comb[i]))
                        for i, column in enumerate(combination)
                    ]
                )
                portfolio = weighted_df.with_columns(sum=pl.sum_horizontal(combination))
                # Calculate values
                cagr, risk = api.calc_metrics_polars(portfolio.select("sum"))
                combination_params = {
                    "name": f"x{index}",
                    "combination": str(combination),
                    "weights": str([float(number) for number in weight_comb]),
                    "cagr": cagr,
                    "risk": risk,
                }
                combination_params_df = pl.DataFrame([combination_params])
                try:
                    with open(file_name, "x") as f:
                        combination_params_df.write_csv(f)
                except FileExistsError:
                    # File already exists, append without header
                    with open(file_name, "a") as f:
                        combination_params_df.write_csv(f, has_header=False)

                new_percentage = int((index - 1) / total_number * 100)
                if new_percentage != percentage:
                    percentage = new_percentage
                    set_progress((percentage, f"{percentage}%"))

                index += 1

        # total_df = total_df.sort("cagr", descending=True).head(top_x)
        # total_df.write_csv(file_name)
    api.upload_files_to_s3([file_name], "data")
    return f"Finished calculating the protfolios. It took {round(time.time() - start_time, 2)}s"
