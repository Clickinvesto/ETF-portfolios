import dash_mantine_components as dmc
from dash import html, page_container, dcc, callback, Input, State, Output
from src.Dash.components.navbar import make_navbar
from src.Dash.components.header import make_header
from src.Dash.components.subscription_modal import sub_modal
from dash_bootstrap_templates import load_figure_template
from flask import current_app, session, redirect, url_for
from dash.exceptions import PreventUpdate
from dash_socketio import DashSocketIO

# loads the "darkly" template and sets it as the default


navbar_width = 200

base_schema = {
    "shadows": {
        "xs": "4px 5px 21px -3px rgba(66, 68, 90, 1)",
        "sm": "4px 5px 21px -3px rgba(66, 68, 90, 1)",
        "md": "4px 5px 21px -3px rgba(66, 68, 90, 1)",
        "lg": "4px 5px 21px -3px rgba(66, 68, 90, 1)",
        "xl": "4px 5px 21px -3px rgba(66, 68, 90, 1)",
    },
    "components": {
        "Grid": {
            "styles": {
                "root": {
                    "margin": 0,
                    "padding": "10px",
                    "grid-gap": 10,
                    "min-height": "100vh",
                    "min-width": "95vw",
                    "overflow": "auto",
                    "align-content": "flex-start",
                    "align-items": "stretch",
                },
                "col": {
                    "display": "flex",
                    "flex-direction": "column",
                    "grid-gap": "10px",
                    "margin": 0,
                    "padding": 0,
                },
            }
        },
        "Paper": {
            "styles": {
                "root": {
                    "box-shadow": "4px 5px 21px -3px rgba(66, 68, 90, 1)",
                    "padding": 10,
                }
            }
        },
        "Navbar": {
            "styles": {
                "root": {
                    "position": "fixed",
                    "width": f"{navbar_width}px",
                    "padding": "15px",
                    "align-content": "center",
                    "justify-content": "space-between",
                    "border-right": "0px",
                }
            }
        },
        "Stack": {"styles": {"root": {"gap": "10px"}}},
        "Group": {"styles": {"root": {"gap": "10px"}}},
        "Button": {
            "styles": {
                "root": {},
            }
        },
        "Title": {"styles": {"root": {"margine-top": 0}}},
        "Text": {"styles": {"root": {"display": "block", "white-space": "pre-wrap"}}},
        # "Anchor": {"styles": {"root": {"color": yellow}}},
    },
}

base_schema["components"]["NavLink"] = {
    "styles": {
        "root": {
            "padding": 5,
            "&:hover": {
                "border-radius": "10px",
                # "color": base_schema["colors"]["primaryColor"][5],
                "background-color": "#018bcf",
            },
            "&[data-active]": {
                "background-color": "#004C94",
                "color": "#fff",
                "border-radius": "10px",
                # },
                "&[data-active]:hover": {
                    "color": "#000",
                    "background-color": "#018bcf",
                },
            },
            "label": {
                # "&:hover": {"color": base_schema["colors"]["custom"][5]},
            },
        },
    }
}


def layout():
    """We prepare the base layout with the page container, general styling, notifications and the navbar
    current_user
    Returns:
        _type_: _description_
    """
    base_layout = dmc.MantineProvider(
        theme=base_schema,
        inherit=True,
        withCSSVariables=True,
        withGlobalStyles=True,
        withNormalizeCSS=True,
        children=dmc.NotificationsProvider(
            [
                dcc.Location(id="url", refresh=True),
                dcc.Store(id="series_store", storage_type="session"),
                html.Div(id="notify_container"),
                DashSocketIO(
                    id="dash_websocket",
                    eventNames=["notification"],
                ),
                make_header(),
                make_navbar(),
                sub_modal,
                html.Div(
                    html.Div(
                        children=[page_container],
                        className="page-body",
                    ),
                ),
            ],
            containerWidth="25%",
            autoClose=5000,
            zIndex=10000,
            position="top-center",
        ),
    )

    return base_layout


@callback(
    Output("url", "pathname"),
    Input("url", "pathname"),
)
def check_url(pathname):
    if pathname == current_app.config["URL_COMPOSITION"]:
        user = session.get("user", None)
        if not user or user.get("subscription", None) is None:
            # Make sure the user is rooted when clicking on composition and has no subscription
            session["url"] = pathname
            return "/pricing"
    raise PreventUpdate
