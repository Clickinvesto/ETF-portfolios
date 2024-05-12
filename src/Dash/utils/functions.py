import json
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
