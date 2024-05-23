import dash_mantine_components as dmc
from dash import html
from src.Dash.utils.functions import get_icon
from dash_iconify import DashIconify
from flask import current_app, session


def make_header():
    user = session.get("user")
    print(f"the user is {user}")
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

    if not user:
        links.append(
            dmc.MenuItem(
                "Login",
                href=current_app.config["URL_LOGIN"],
                leftSection=DashIconify(icon="material-symbols:login"),
                refresh=True,
            )
        )
    return dmc.Group(
        [
            dmc.Group(
                [
                    dmc.Burger(id="menue", hiddenFrom="md", opened=False),
                    dmc.Image(src="/assets/images/logo.png", h=50),
                ]
            ),
            dmc.Menu(
                [
                    dmc.MenuTarget(
                        dmc.Avatar(radius="xl"),
                    ),
                    dmc.MenuDropdown(links),
                ]
            ),
        ],
        justify="space-between",
    )
