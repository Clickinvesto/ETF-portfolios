import decimal

from dash import html
from flask import current_app
from src.Dash.utils.functions import get_config
import dash_mantine_components as dmc

# Python is doing Bankers rounding by default. setting the rounding context
context = decimal.getcontext()
context.rounding = decimal.ROUND_HALF_UP


def make_cagr_risk_table(
    cagr, risk, number_of_month, reference_series, selected_series
):
    configuration = get_config("table")

    last_row = [
        configuration.get("inception_text", "Month since inception"),
        "",
        number_of_month,
    ]
    table_header = configuration.get(
        "header", ["Parameter", "Reference Index", "Selected Series"]
    )
    data = [["CAGR"] + cagr.tolist(), ["Risk"] + risk.tolist()]
    if reference_series == selected_series:
        data = [
            ["CAGR"] + cagr.tolist() + cagr.tolist(),
            ["Risk"] + risk.tolist() + risk.tolist(),
        ]

    align_style = {"text-align": "center"}
    header = [
        html.Tr(
            [
                html.Th(table_header[0]),
                html.Th(table_header[1], style=align_style),
                html.Th(
                    dmc.Anchor(
                        table_header[2],
                        href=current_app.config["URL_COMPOSITION"]
                        + f"?series={selected_series}",
                        refresh=True,
                    ),
                    style=align_style,
                ),
            ]
        )
    ]

    rows = [
        html.Tr(
            [
                (
                    html.Td(cell)
                    if index < 1
                    else html.Td(
                        f"{str(round(decimal.Decimal(cell), 2))}%",
                        style=align_style,
                    )
                )
                for index, cell in enumerate(row)
            ]
        )
        for row in data
    ]
    rows.append(
        html.Tr(
            [
                html.Td(cell) if index < 1 else html.Td(cell, style=align_style)
                for index, cell in enumerate(last_row)
            ]
        )
    )
    table = [html.Thead(header), html.Tbody(rows)]
    return [
        dmc.Table(
            children=table,
            striped=True,
            highlightOnHover=True,
            withBorder=True,
            withColumnBorders=True,
        ),
        dmc.Space(h=10),
        dmc.Anchor(
            "Click to uncover the ETFs that make up this portfolio",
            href=current_app.config["URL_COMPOSITION"] + f"?series={selected_series}",
            refresh=True,
        ),
    ]
