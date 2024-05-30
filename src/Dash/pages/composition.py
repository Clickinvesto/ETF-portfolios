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
from src.Dash.services.calculation import LocalAPI
from src.Dash.services.graph import plotting_engine, blank_fig
from src.Dash.components.cagr_risk_table import make_cagr_risk_table

api = LocalAPI()
plotter = plotting_engine()

context = decimal.getcontext()
context.rounding = decimal.ROUND_HALF_UP


register_page(__name__, name="Composition", path=current_app.config["URL_COMPOSITION"])
page_name = "compostion"


def layout(socket_ids=None, **kwargs):
    if socket_ids == None:
        raise PreventUpdate
    # This page requires the user to subscripe. So first check if the user is logged in.
    user = session.get("user", False)

    if not user or user.get("subscription", None) is None:
        return dmc.Container()

    return full_layout()


def full_layout():
    return dmc.Container(
        [
            dmc.Flex(
                [
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
                                    withTableBorder=True,
                                    withColumnBorders=True,
                                    withRowBorders=True,
                                ),
                                dmc.Table(
                                    id="risk_table",
                                    withTableBorder=True,
                                    withColumnBorders=True,
                                    withRowBorders=True,
                                ),
                            ]
                        ),
                    ),
                    dmc.Paper(
                        dcc.Graph(
                            id="pie_chart",
                            figure=blank_fig(),
                        )
                    ),
                ],
                style={
                    "width": "calc(100% - 1px)",
                    "display": "flex",
                    "flex-direction": "row",
                    "align": "center",
                    "justify-content": "space-around",
                    "flex-wrap": "wrap",
                    "gap": "10px",
                },
            )
        ],
        fluid=True,
    )


def create_table(header_data, value_data):
    header = [dmc.TableTr([dmc.TableTh(col) for col in header_data])]

    rows = [
        dmc.TableTr(
            [
                (
                    dmc.TableTd(cell)
                    if index < 1
                    else dmc.TableTd(
                        f"{str(round(decimal.Decimal(cell*100), 2))}%",
                    )
                )
                for index, cell in enumerate(row)
            ]
        )
        for row in value_data
    ]
    table = [dmc.TableThead(header), dmc.TableTbody(rows)]
    return table


def create_risk_table(header_data, value_data):
    header = [dmc.TableTr([dmc.TableTh(col) for col in header_data])]

    rows = [
        dmc.TableTr(
            [
                (
                    dmc.TableTd(
                        f"{str(round(decimal.Decimal(cell), 2))}%",
                    )
                )
                for index, cell in enumerate(row)
            ]
        )
        for row in value_data
    ]
    table = [dmc.TableThead(header), dmc.TableTbody(rows)]
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
            selection = store.get("points")[0]
            selected_series = selection.get("text")
            return selected_series
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


@callback(
    Output("risk_table", "children"),
    Input("series_selection", "value"),
    prevent_initial_call=True,
)
def update_risk_table(series):

    normalised_data, reference_series, number_month = api.get_weighted_series(series)

    cagr, risk = api.calc_CAGR(normalised_data, number_month)
    table_header = ["CAGR", "Risk"]
    table_data = [[cagr[series], risk[series]]]
    return create_risk_table(table_header, table_data)
