import dash_mantine_components as dmc
from dash import callback, Input, Output, html, State, ctx, ALL
from dash.exceptions import PreventUpdate
from flask import current_app, session
import copy
from src.Dash.utils.functions import get_icon

tabs = [
    [
        "Portfolio Exploration",
        current_app.config["URL_DASH"][:-1] + current_app.config["URL_EXPLORER"],
        "material-symbols:home",
    ],
    [
        "Portfolio Compostion",
        current_app.config["URL_DASH"][:-1] + current_app.config["URL_COMPOSITION"],
        "material-symbols:find-in-page",
    ],
    [
        "Pricing",
        current_app.config["URL_DASH"][:-1] + current_app.config["URL_PRICING"],
        "streamline:subscription-cashflow",
    ],
]


def make_nav_links(is_admin, user):
    temp = copy.deepcopy(tabs)
    if user:
        temp.append(
            [
                "Configuration",
                current_app.config["URL_DASH"][:-1]
                + current_app.config["URL_CONFIGURATION"],
                "material-symbols:settings",
            ]
        )
    if is_admin:
        temp.append(
            [
                "Combination Calculation",
                current_app.config["URL_DASH"][:-1]
                + current_app.config["URL_SETTINGS"],
                "material-symbols:settings",
            ],
        )
    tabs_content = dmc.Stack(
        [
            (
                dmc.NavLink(
                    label=tab[0],
                    href=tab[1],
                    id={"type": "nav-Link", "index": tab[1]},
                    icon=get_icon(tab[2]),
                )
                if len(tab) > 1
                else dmc.Divider(size="sm")
            )
            for tab in temp
        ]
    )

    if user:
        nav = dmc.Group(
            [
                tabs_content,
                dmc.NavLink(
                    label="Logout",
                    href=current_app.config["URL_LOGOUT"],
                    refresh=True,
                    icon=get_icon("material-symbols:logout"),
                ),
            ]
        )
    else:
        nav = dmc.Group(
            [
                tabs_content,
                dmc.NavLink(
                    label="Login",
                    href=current_app.config["URL_LOGIN"],
                    refresh=True,
                    icon=get_icon("material-symbols:login"),
                ),
            ]
        )
    return nav


def make_drawer_links(is_admin, user):
    temp = copy.deepcopy(tabs)
    if user:
        temp.append(
            [
                "Configuration",
                current_app.config["URL_DASH"][:-1]
                + current_app.config["URL_CONFIGURATION"],
                "material-symbols:settings",
            ]
        )
    if is_admin:
        temp.append(
            [
                "Combination Calculation",
                current_app.config["URL_DASH"][:-1]
                + current_app.config["URL_SETTINGS"],
                "material-symbols:settings",
            ],
        )
    tabs_content = dmc.Stack(
        [
            (
                dmc.NavLink(
                    label=tab[0],
                    href=tab[1],
                    id={"type": "drawer-Link", "index": tab[1]},
                    icon=get_icon(tab[2]),
                )
                if len(tab) > 1
                else dmc.Divider(size="sm")
            )
            for tab in temp
        ]
    )
    if user:
        nav = dmc.Group(
            [
                tabs_content,
                dmc.NavLink(
                    label="Logout",
                    href=current_app.config["URL_LOGOUT"],
                    refresh=True,
                    icon=get_icon("material-symbols:logout"),
                ),
            ]
        )
    else:
        nav = dmc.Group(
            [
                tabs_content,
                dmc.NavLink(
                    label="Login",
                    href=current_app.config["URL_LOGIN"],
                    refresh=True,
                    icon=get_icon("material-symbols:login"),
                ),
            ]
        )
    return nav


def make_navbar():
    # Here we check if there is a user in the session, then he logged in.
    # We check if the user is admin to show the admin page
    user = session.get("user", False)
    if user:
        is_admin = user.get("is_admin", "False")
    else:
        is_admin = False
    return html.Div(
        [
            dmc.Drawer(
                dmc.Navbar(
                    children=[make_drawer_links(is_admin, user)],
                ),
                opened=False,
                withCloseButton=False,
                id="drawer_nav",
            ),
            dmc.MediaQuery(
                dmc.Navbar(
                    children=[make_nav_links(is_admin, user)],
                ),
                smallerThan="lg",
                styles={"display": "none"},
            ),
        ]
    )


@callback(
    Output({"type": "nav-Link", "index": ALL}, "active"),
    Input("url", "pathname"),
    State({"type": "nav-Link", "index": ALL}, "href"),
)
def update_active_link(pathname, current_navs):
    return [True if tab == pathname else False for tab in current_navs]


@callback(
    Output("drawer_nav", "opened"),
    Input("menue", "n_clicks"),
    State("drawer_nav", "opened"),
    prevent_initial_call=True,
)
def open(n_clicks, opened):
    if ctx.triggered_id == "menue" and not opened:
        return True
    if ctx.triggered_id == "menue" and opened:
        return False
    raise PreventUpdate
