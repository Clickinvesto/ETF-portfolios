import dash_mantine_components as dmc
from dash import (
    register_page,
    html,
    dcc,
    callback,
    Input,
    Output,
    State,
    ctx,
    no_update,
    ALL,
    clientside_callback,
)
import logging
from flask import current_app
from flask_login import current_user
from dash.exceptions import PreventUpdate

from dash_iconify import DashIconify

from src.Dash.components.header import make_header
from src.Dash.services.calculation import LocalAPI
from src.Dash.services.graph import plotting_engine, blank_fig
from src.Dash.components.cagr_risk_table import make_cagr_risk_table

register_page(__name__, name="Series Explorer", path=current_app.config["URL_EXPLORER"])


api = LocalAPI()
plotter = plotting_engine()


def layout(socket_ids=None, **kwargs):
    if socket_ids == None:
        raise PreventUpdate
    # ToDo in the future we can add other information here as well for example from the user
    # Wait for the socket to be connected
    return full_layout()


def full_layout():
    return dmc.Container(
        [
            dmc.Title("Portfolio Exploration", order=2),
            dmc.Flex(
                [
                    dmc.Paper(
                        [
                            dcc.Graph(
                                id="dispersion_plot",
                                figure=blank_fig(),
                            ),
                            dmc.Text(
                                "*Reference Index RI stands for S&P500 measured by SPY ETF",
                                size="sm",
                            ),
                        ],
                    ),
                    dmc.Paper(
                        [
                            dcc.Graph(
                                id="performance_plot",
                                figure=blank_fig(),
                            ),
                            html.Div(
                                children=[],
                                id="performance_table",
                            ),
                        ],
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
    Output("dispersion_plot", "figure"),
    Output("dispersion_plot", "selectedData"),
    Input("url", "pathname"),
    State("series_store", "data"),
)
def init_graph(path, store):
    data = api.get_dispersion_data()
    figure = plotter.make_dispersion_plot(data)
    if isinstance(store, dict):
        return figure, store

    return figure, no_update


@callback(
    Output("performance_plot", "figure"),
    Output("performance_table", "children"),
    Output("notify_container", "children", allow_duplicate=True),
    Output("series_store", "data"),
    Input("dispersion_plot", "selectedData"),
    prevent_initial_call=True,
)
def display_click_data(selectedData):
    if selectedData is None:
        return blank_fig(), [], no_update, no_update
    selection = selectedData.get("points")[0]
    selected_series = selection.get("text")
    normalised_data, reference_series, number_month = api.get_weighted_series(
        selected_series
    )

    cagr, risk = api.calc_CAGR(normalised_data, number_month)
    figure = plotter.make_performance_plot(normalised_data, selected_series)

    if figure == "error":
        message = dmc.Notification(
            title="There was an error",
            color="red",
            id="simple-notify",
            action="show",
            message=f"{number_month}",
            icon=DashIconify(icon="material-symbols:error-outline"),
        )
        return no_update, [], message, no_update

    table = make_cagr_risk_table(
        cagr, risk, number_month, reference_series, selected_series
    )
    return figure, table, no_update, selectedData
