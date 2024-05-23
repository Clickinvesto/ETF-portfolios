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
                    leftSection=get_icon(tab[2]),
                )
                if len(tab) > 1
                else dmc.Divider(size="sm")
            )
            for tab in temp
        ],
        style={"padding": "10px"},
    )

    nav = dmc.Group([tabs_content])
    return nav


def make_navbar():
    # Here we check if there is a user in the session, then he logged in.
    # We check if the user is admin to show the admin page
    user = session.get("user", False)
    if user:
        is_admin = user.get("is_admin", "False")
    else:
        is_admin = False
    return make_nav_links(is_admin, user)


@callback(
    Output({"type": "nav-Link", "index": ALL}, "active"),
    Input("url", "pathname"),
    State({"type": "nav-Link", "index": ALL}, "href"),
)
def update_active_link(pathname, current_navs):
    return [True if tab == pathname else False for tab in current_navs]


@callback(
    Output("app-shell", "navbar"),
    Input("menue", "opened"),
    State("app-shell", "navbar"),
)
def open(opened, navbar):
    navbar["collapsed"] = {"mobile": not opened}
    return navbar
