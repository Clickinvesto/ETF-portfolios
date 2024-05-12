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
    Patch,
)
from flask import current_app, session
from dash.exceptions import PreventUpdate

from dash_iconify import DashIconify

register_page(__name__, name="Pricing", path=current_app.config["URL_PRICING"])


def layout(**kwargs):
    # ToDo in the future we can add other information here as well for example from the user
    # Wait for the socket to be connected
    print(session.get("user"))
    return full_layout(user=session.get("user"))


def full_layout(user=False):
    signup = dmc.Anchor(
        "Sign Up",
        href=current_app.config["URL_SIGNUP"],
        refresh=True,
        style={
            "backgrund-color": "#004c94",
            "border-radius": "20px",
        },
    )

    subscribe = dmc.ActionIcon(
        "Subscribe",
        id="subscription",
        style={
            "color": "rgb(28, 126, 214)",
            "line-height": 1.55,
            "text-decoration": "none",
            "display": "block",
            "white-space": "pre-wrap",
            "background-color": "transparent",
            "cursor": "pointer",
            "padding": 0,
            "border": 0,
        },
    )

    return dmc.Container(
        [
            dmc.Grid(
                [
                    dmc.Stack(
                        [
                            dmc.Text(
                                "MONTHLY PLANS",
                                weight=700,
                                color="#004c94",
                                transform="uppercase",
                                size="xl",
                            ),
                            dmc.Group(
                                [
                                    dmc.Card(
                                        children=[
                                            dmc.CardSection(
                                                dmc.Center(
                                                    p="md",
                                                    children=[
                                                        dmc.Text(
                                                            "0 USD",
                                                            weight=700,
                                                            transform="uppercase",
                                                            color="#fff",
                                                            size="xl",
                                                        )
                                                    ],
                                                    style={"height": "160px"},
                                                ),
                                                style={"background-color": "#018BCF"},
                                            ),
                                            dmc.Group(
                                                [
                                                    dmc.Text(
                                                        "FREE",
                                                        weight=500,
                                                        transform="uppercase",
                                                        color="#018bcf",
                                                        size="xl",
                                                    ),
                                                ],
                                                position="left",
                                                mt="md",
                                                mb="xs",
                                            ),
                                            dmc.List(
                                                icon=DashIconify(
                                                    icon="material-symbols:check",
                                                    width=24,
                                                ),
                                                size="lg",
                                                spacing="sm",
                                                children=[
                                                    dmc.ListItem(
                                                        dmc.Text(
                                                            "10 Source ETF’s, keep growing",
                                                        ),
                                                    ),
                                                    dmc.ListItem(
                                                        "Comparison indexes S&P 500"
                                                    ),
                                                    dmc.ListItem(
                                                        "Access to the ETFs Clickinvesto best portfolios"
                                                    ),
                                                    dmc.ListItem("Monthly updates"),
                                                    dmc.ListItem(
                                                        "Access to the %s of each ETF Clickinvesto best portfolios",
                                                        icon=DashIconify(
                                                            icon="material-symbols:close",
                                                            width=24,
                                                        ),
                                                    ),
                                                ],
                                            ),
                                            dmc.Space(h=10),
                                            dmc.Anchor(
                                                "Use Free",
                                                color="#004c94",
                                                href=current_app.config["URL_EXPLORER"],
                                                refresh=True,
                                            ),
                                        ],
                                        withBorder=True,
                                        shadow="sm",
                                        radius="md",
                                        style={"width": 350},
                                    ),
                                    dmc.Card(
                                        children=[
                                            dmc.CardSection(
                                                dmc.Center(
                                                    p="md",
                                                    children=[
                                                        dmc.Text(
                                                            "7 USD",
                                                            weight=700,
                                                            transform="uppercase",
                                                            color="#fff",
                                                            size="xl",
                                                        )
                                                    ],
                                                    style={"height": "160px"},
                                                ),
                                                style={"background-color": "#018BCF"},
                                            ),
                                            dmc.Group(
                                                [
                                                    dmc.Text(
                                                        "SILVER",
                                                        weight=500,
                                                        transform="uppercase",
                                                        color="#018bcf",
                                                        size="xl",
                                                    ),
                                                ],
                                                position="left",
                                                mt="md",
                                                mb="xs",
                                            ),
                                            dmc.List(
                                                icon=DashIconify(
                                                    icon="material-symbols:check",
                                                    width=24,
                                                ),
                                                size="lg",
                                                spacing="sm",
                                                children=[
                                                    dmc.ListItem(
                                                        dmc.Text(
                                                            "10 Source ETF’s, keep growing",
                                                        ),
                                                    ),
                                                    dmc.ListItem(
                                                        "Comparison indexes S&P 500"
                                                    ),
                                                    dmc.ListItem(
                                                        "Access to the ETFs Clickinvesto best portfolios"
                                                    ),
                                                    dmc.ListItem("Monthly updates"),
                                                    dmc.ListItem(
                                                        "Access to the %s of each ETF Clickinvesto best portfolios",
                                                    ),
                                                ],
                                            ),
                                            dmc.Space(h=10),
                                            subscribe if user else signup,
                                        ],
                                        withBorder=True,
                                        shadow="sm",
                                        radius="md",
                                        style={"width": 350},
                                    ),
                                ],
                                position="center",
                                spacing="xl",
                            ),
                        ],
                        align="center",
                    ),
                ],
                justify="center",
                align="flex-start",
                style={
                    "align-content": "center",
                    "min-width": 0,
                },
            ),
        ],
        fluid=True,
        style={
            "position": "fixed",
            "padding": "10px",
            "display": "block",
            "max-height": "calc(100% - 70px)",
            "width": "calc(100% - 200px)",
        },
    )


@callback(
    Output("subscription_modal", "opened", allow_duplicate=True),
    Output("plan_text", "children"),
    Input("subscription", "n_clicks"),
    prevent_initial_call="initial_duplicate",
    # prevent_inital_call=True,
)
def open_modal(n_clicks):
    if n_clicks:
        return True, "You selected the silver plan for 7USD"
    raise PreventUpdate
