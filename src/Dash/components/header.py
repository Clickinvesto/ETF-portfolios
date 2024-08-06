import dash_mantine_components as dmc
from dash import html
from src.Dash.utils.functions import get_icon
from dash_iconify import DashIconify
from flask import current_app, session


def make_header():
    user = session.get("user")
    links = []
    if user:
        links.append(
            dmc.MenuItem(
                "Account",
                href=current_app.config["URL_CONFIGURATION"],
                leftSection=DashIconify(icon="material-symbols:account-balance"),
                refresh=True,
            )
        )

        links.append(
            dmc.MenuItem(
                "Logout",
                href=current_app.config["URL_LOGOUT"],
                leftSection=DashIconify(icon="material-symbols:logout"),
                refresh=True,
            )
        )
        avatar = dmc.Avatar(radius="xl", color="green")

    if not user:
        links.append(
            dmc.MenuItem(
                "Login",
                href=current_app.config["URL_LOGIN"],
                leftSection=DashIconify(icon="material-symbols:login"),
                refresh=True,
            )
        )
        avatar = dmc.Avatar(radius="xl")
    return dmc.Group(
        [
            dmc.Group(
                [
                    dmc.Burger(id="menue", hiddenFrom="md", opened=False),
                    dmc.Image(
                        src="/assets/images/logo.png",
                        h=50,
                        visibleFrom="sm",
                    ),
                ]
            ),
            dmc.Menu(
                [
                    dmc.MenuTarget(avatar),
                    dmc.MenuDropdown(links),
                ]
            ),
        ],
        justify="space-between",
    )
