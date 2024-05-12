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
)
import decimal
from flask import current_app, session, url_for
from flask_login import current_user
from dash.exceptions import PreventUpdate

from dash_iconify import DashIconify

from src.Dash.components.header import make_header
from src.Dash.services.API import API
from src.Dash.services.graph import plotting_engine, blank_fig
from src.Dash.components.cagr_risk_table import make_cagr_risk_table

api = API()
plotter = plotting_engine()

context = decimal.getcontext()
context.rounding = decimal.ROUND_HALF_UP


register_page(__name__, name="Composition", path=current_app.config["URL_COMPOSITION"])
page_name = "compostion"


def layout(**kwargs):
    # This page requires the user to subscripe. So first check if the user is logged in.
    user = session.get("user", False)

    if not user or user.get("subscription", None) is None:
        return dmc.Container()

    return full_layout()


def full_layout():
    return dmc.Container(
        [
            dmc.Grid(
                [
                    dmc.Col(
                        dmc.Paper(
                            dmc.Stack(
                                [
                                    dmc.Select(
                                        label="Select a Series",
                                        data=api.get_series(),
                                        id="series_selection",
                                        style={"width": 200},
                                    ),
                                    dmc.Table(
                                        id="composition_table",
                                        striped=True,
                                        highlightOnHover=True,
                                        withBorder=True,
                                        withColumnBorders=True,
                                    ),
                                ]
                            )
                        ),
                        span=12,
                        lg=5,
                    ),
                    dmc.Col(
                        dmc.Paper(
                            dcc.Graph(
                                id="pie_chart",
                                figure=blank_fig(),
                            )
                        ),
                        span=12,
                        lg=5,
                    ),
                ],
                gutter="xl",
                style={
                    "width": "calc(100% - 1px)",
                },
            )
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


def create_table(header_data, value_data):
    header = [html.Tr([html.Th(col) for col in header_data])]

    rows = [
        html.Tr(
            [
                (
                    html.Td(cell)
                    if index < 1
                    else html.Td(
                        f"{str(round(decimal.Decimal(cell*100), 2))}%",
                    )
                )
                for index, cell in enumerate(row)
            ]
        )
        for row in value_data
    ]
    table = [html.Thead(header), html.Tbody(rows)]
    return table


@callback(
    Output("series_selection", "value"),
    Input("url", "pathname"),
    State("series_store", "data"),
    State("series_selection", "value"),
)
def fill_selection(pathname, store, current_selection):
    if current_selection is None:
        if store:
            return store
        else:
            return "x1"
    raise PreventUpdate


@callback(
    Output("pie_chart", "figure"),
    Output("composition_table", "children"),
    Input("series_selection", "value"),
    prevent_initial_call=True,
)
def update_page(series):

    indices, weights = api.get_series_combination_weights(series)
    filtered_indices, filtered_weights = zip(
        *[(index, weight) for index, weight in zip(indices, weights) if weight != 0]
    )
    # Since zip returns a tuple, if you need lists, convert them back to lists
    filtered_indices = list(filtered_indices)
    filtered_weights = list(filtered_weights)
    figure = plotter.make_pie_chart(filtered_indices, filtered_weights, series)
    table_header = ["Selected Symbol", "Percentage"]
    table_data = [list(pair) for pair in zip(filtered_indices, filtered_weights)]
    return figure, create_table(table_header, table_data)
