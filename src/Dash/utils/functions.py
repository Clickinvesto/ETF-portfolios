import json
import pandas as pd
import polars as pl
from dash_iconify import DashIconify
from pathlib import Path


def get_config(sub_dict):
    working_directory = Path.cwd()
    config_folder = "src/Dash/config"
    graph_file = "graphs.json"
    graph_path = Path.joinpath(working_directory, config_folder, graph_file)
    f = open(graph_path)
    data = json.load(f)
    return data.get(sub_dict)


def get_icon(icon, height=16):
    return DashIconify(icon=icon, height=height)


def get_countries():
    working_directory = Path.cwd()
    data_folder = "src/Dash/data"
    file = "countries.csv"
    path_file = Path.joinpath(working_directory, data_folder, file)
    dataframe = pl.read_csv(
        path_file,
        separator=",",
        new_columns=["label", "value"],
    )
    mapping = {row[1]: row[0] for row in dataframe.iter_rows()}
    values = {row[1]: row[1] for row in dataframe.iter_rows()}
    return mapping, values
