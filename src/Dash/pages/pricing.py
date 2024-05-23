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


def layout(socket_ids=None, **kwargs):
    if socket_ids == None:
        raise PreventUpdate

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

    subscribe = dmc.Anchor(
        "Subscribe",
        href=current_app.config["URL_SUBSCRIBTION"],
        refresh=True,
        style={
            "backgrund-color": "#004c94",
            "border-radius": "20px",
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
                                fw=700,
                                c="#004c94",
                                tt="uppercase",
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
                                                            fw=700,
                                                            tt="uppercase",
                                                            c="#fff",
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
                                                        fw=500,
                                                        tt="uppercase",
                                                        c="#018bcf",
                                                        size="xl",
                                                    ),
                                                ],
                                                justify="flex-start",
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
                                                style={"color": "#004c94"},
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
                                                            fw=700,
                                                            tt="uppercase",
                                                            c="#fff",
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
                                                        fw=500,
                                                        tt="uppercase",
                                                        c="#018bcf",
                                                        size="xl",
                                                    ),
                                                ],
                                                justify="flex-start",
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
                                justify="center",
                                gap="xl",
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
