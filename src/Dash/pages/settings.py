import dash_mantine_components as dmc
import dash
import os
import uuid
import base64
from io import BytesIO
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
from src.Dash.utils.functions import get_icon
from src.Dash.components.checklist import create_check_list
from dash.long_callback import DiskcacheLongCallbackManager
from src.Dash.services.NotificationProvider import NotificationProvider
import diskcache

notify = NotificationProvider()

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
    user = session.get("user", False)
    if not user:
        return dmc.Container()
    # Wait for the socket to be connected
    return full_layout()


def full_layout():
    return dmc.Container(
        [
            dmc.Title("Weight Calculation", order=2),
            dmc.Flex(
                [
                    dmc.Paper(
                        [
                            dmc.Group(
                                [
                                    dcc.Upload(
                                        id="csv_upload",
                                        children=html.Div(
                                            [
                                                "Drag and Drop or ",
                                                html.A("Select Files"),
                                            ]
                                        ),
                                        style={
                                            "width": "400px",
                                            "height": "60px",
                                            "lineHeight": "60px",
                                            "borderWidth": "1px",
                                            "borderStyle": "dashed",
                                            "borderRadius": "5px",
                                            "textAlign": "center",
                                            "margin": "10px",
                                        },
                                        multiple=False,
                                    ),
                                    dmc.Button(
                                        "Save file", id="save_file", disabled=True
                                    ),
                                ]
                            ),
                            dmc.List(
                                icon=dmc.ThemeIcon(
                                    get_icon(
                                        icon="radix-icons:check-circled", height=16
                                    ),
                                    radius="xl",
                                    color="green",
                                    size=24,
                                ),
                                size="sm",
                                spacing="sm",
                                id="check_list",
                            ),
                        ]
                    ),
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
                                        decimalScale=6,
                                        style={"width": 200},
                                        id="step_size",
                                    ),
                                    dmc.NumberInput(
                                        label="Limit the result to the top X regarding CARG",
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
                                value=0,
                                id="progress_bar",
                                size="xl",
                            ),
                            dmc.Space(h=20),
                            dmc.Text(id="calculation_time"),
                        ]
                    ),
                ],
                style={
                    "width": "inherit",
                    "display": "flex",
                    "flex-direction": "row",
                    "align": "center",
                    "justify-content": "space-around",
                    "flex-wrap": "wrap",
                    "gap": "10px",
                },
            ),
        ],
        fluid=True,
    )


@callback(
    Output("check_list", "children", allow_duplicate=True),
    Output("save_file", "disabled"),
    Input("csv_upload", "contents"),
    State("csv_upload", "filename"),
    prevent_initial_call=True,
)
def update_output(content, name):
    content_type, content_string = content.split(",")
    disable_save, check_list = create_check_list(name, content_string)
    return check_list, disable_save


@callback(
    Output("check_list", "children", allow_duplicate=True),
    Output("save_file", "disabled", allow_duplicate=True),
    Input("save_file", "n_clicks"),
    Input("csv_upload", "contents"),
    State("csv_upload", "filename"),
    State("dash_websocket", "socketId"),
    prevent_initial_call=True,
)
def upload_upload(trigger, content, name, socket_id):
    if trigger:
        notification_id = uuid.uuid4().hex
        notify.send_socket(
            to=socket_id,
            type="start_process",
            title="Uploading the file to S3",
            message="Please wait a moment, we are uploading the file",
            id=notification_id,
        )

        content_type, content_string = content.split(",")
        decoded_content = base64.b64decode(content_string)
        file_like_object = BytesIO(decoded_content)

        name = "data/" + name
        status = api.upload_file(file_like_object, name)
        if status:
            notify.send_socket(
                to=socket_id,
                type="success_process",
                title="Upload finished",
                message="You can progress with the calculation",
                id=notification_id,
            )
            return [], True

        notify.send_socket(
            to=socket_id,
            type="error_process",
            title="Something went wrong",
            message="Something went wrong while uploading",
            id=notification_id,
        )

        raise PreventUpdate
    raise PreventUpdate


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
    interval=100,
)
def callback(set_progress, n_clicks, interval_size, partitions, top_x):
    if ctx.triggered_id is None:
        raise PreventUpdate

    start_time = time.time()
    df = api.get_series_data()
    # First remove the date column from the list
    column_names = df.columns
    column_names = column_names[2:]

    current_directory = Path.cwd() / "src/Dash/data"
    file_name = current_directory / "new_result.csv"
    filtered_path = current_directory / "check.csv"
    # Check if the file exists
    if os.path.exists(file_name):
        # Delete the file
        os.remove(file_name)
    else:
        pass
    total_number = get_number_of_portfolios(column_names, partitions, interval_size)

    # Iterate over each combination and preccacluate the valid weights, exclude the first value which is RI
    index = 1
    percentage = 0
    header_written = False

    # Calculate RI
    df["RI"] = pd.to_numeric(df["RI"], errors="coerce")  # Ensure RI is numeric
    normalised_df = df[["RI"]].dropna()
    normalised_df["sum"] = (normalised_df["RI"] / normalised_df["RI"].iloc[0]) * 100

    cagr, risk = api.calc_metrics_pandas(normalised_df["sum"])
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
    combination_params_df = pd.DataFrame([combination_params])
    try:
        with open(file_name, "x") as f:
            combination_params_df.to_csv(f, index=False)
    except FileExistsError:
        # File already exists, append without header
        with open(file_name, "a") as f:
            combination_params_df.to_csv(f, index=False, header=False)

    for partition in range(1, partitions + 1):
        for combination in itertools.combinations(column_names, partition):
            pre_computed_weights = get_valid_weights(
                partition, interval_size, get_weights=True
            )
            # Filter non-null values for the combination of columns
            filtered_df = df.dropna(subset=combination)

            # Normalize the columns
            for column in combination:
                filtered_df[column] = (
                    filtered_df[column] / filtered_df[column].iloc[0]
                ) * 100

            for weight_comb in pre_computed_weights:
                # Calcuclate Portfolio
                weighted_df = filtered_df.copy()
                for i, column in enumerate(combination):
                    weighted_df[column] = weighted_df[column] * float(weight_comb[i])

                weighted_df["sum"] = weighted_df[list(combination)].sum(axis=1)

                cagr, risk = api.calc_metrics_pandas(weighted_df["sum"])

                combination_params = {
                    "name": f"x{index}",
                    "combination": str(combination),
                    "weights": str([float(number) for number in weight_comb]),
                    "cagr": cagr,
                    "risk": risk,
                }

                combination_params_df = pd.DataFrame([combination_params])
                try:
                    with open(file_name, "x") as f:
                        combination_params_df.to_csv(f, index=False)

                except FileExistsError:
                    # File already exists, append without header
                    with open(file_name, "a") as f:
                        combination_params_df.to_csv(f, index=False, header=False)

                new_percentage = int((index - 1) / total_number * 100)
                if new_percentage != percentage:
                    percentage = new_percentage
                    set_progress((percentage, f"{percentage}%"))

                index += 1

        # total_df = total_df.sort("cagr", descending=True).head(top_x)
        # total_df.write_csv(file_name)
    api.upload_files_to_s3([file_name], "data")
    return f"Finished calculating the protfolios. It took {round(time.time() - start_time, 2)}s"
