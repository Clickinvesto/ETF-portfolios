import dash_mantine_components as dmc
from dash import html


def make_footer():
    return html.Div(
        style={"textAlign": "center"},
        children=dmc.Anchor(
            "Disclaimer",
            href="/disclaimer",
            target="_blank"
        )
    )
