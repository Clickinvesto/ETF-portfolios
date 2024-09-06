import dash_mantine_components as dmc
from dash import html, page_container, dcc, callback, Input, State, Output
from src.Dash.components.footer import make_footer
from src.Dash.components.navbar import make_navbar
from src.Dash.components.header import make_header
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
                "root": {},
            }
        },
        "Paper": {
            "styles": {
                "root": {
                    "box-shadow": "4px 5px 21px -3px rgba(66, 68, 90, 1)",
                    "padding": 10,
                    "flex": "1 1 0",
                    "max-width": "50%",
                    "min-width": "400px",
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
        children=dmc.AppShell(
            [
                dcc.Location(id="url", refresh=True),
                dcc.Store(id="series_store", storage_type="session"),
                dcc.Interval(
                    id="check_login",  # interval=60000),
                    interval=60000,
                ),
                DashSocketIO(
                    id="dash_websocket",
                    eventNames=["notification"],
                ),
                dmc.NotificationProvider(position="top-center", autoClose=3000),
                html.Div(id="notify_container"),
                dmc.AppShellHeader(make_header(), px=25, style={"padding-top": "10px"}),
                dmc.AppShellNavbar(make_navbar()),
                dmc.AppShellMain(page_container, style={"padding-bottom": "50px"}),
                dmc.AppShellFooter(
                    make_footer(), style={"padding": "5px", "height": "40px"}
                ),
            ],
            header={"height": 70},
            padding="10px",
            navbar={
                "width": 200,
                "breakpoint": "md",
                "collapsed": {"mobile": True},
            },
            id="app-shell",
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
        is_admin = user.get("is_admin", "False")
        if not is_admin:
            if not user or user.get("subscription", None) is None:
                # Make sure the user is rooted when clicking on composition and has no subscription
                session["url"] = pathname
                return "/pricing"
        return current_app.config["URL_COMPOSITION"]
    raise PreventUpdate
