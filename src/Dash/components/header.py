import dash_mantine_components as dmc
from dash import html
from src.Dash.utils.functions import get_icon


def make_header():
    return dmc.Header(
        height=60,
        children=[
            dmc.Group(
                [
                    dmc.MediaQuery(
                        dmc.Button(
                            get_icon("material-symbols:menu", height=30),
                            variant="subtle",
                            color="gray",
                            id="menue",
                        ),
                        largerThan="lg",
                        styles={"display": "none"},
                    ),
                    dmc.Image(
                        src="/assets/images/logo.png",
                        width=150,
                    ),
                ],
                style={"padding-left": "20px", "padding-top": "10px"},
            )
        ],
    )
