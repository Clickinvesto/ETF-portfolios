import json
import datetime
import pandas as pd
import polars as pl
import dash_credit_cards as dcs
from dash_iconify import DashIconify
import dash_mantine_components as dmc
from dash import html
from pathlib import Path


def get_config(sub_dict):
    working_directory = Path.cwd()
    config_folder = "src/Dash/config"
    graph_file = "graphs.json"
    graph_path = Path.joinpath(working_directory, config_folder, graph_file)
    f = open(graph_path)
    data = json.load(f)
    return data.get(sub_dict)


def get_date_formatted(date):
    formats = ["%m/%d/%Y", "%d/%m/%y", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date, fmt)
        except ValueError:
            continue
    return None


def get_icon(icon, height=16):
    return DashIconify(icon=icon, height=height)


def get_countries(dict_output=False):
    working_directory = Path.cwd()
    data_folder = "src/Dash/data"
    file = "countries.csv"
    path_file = Path.joinpath(working_directory, data_folder, file)
    dataframe = pl.read_csv(
        path_file,
        separator=",",
        new_columns=["label", "value"],
    )
    if dict_output:
        return [{"label": row[0], "value": row[1]} for row in dataframe.iter_rows()]

    mapping = {row[1]: row[0] for row in dataframe.iter_rows()}
    values = {row[1]: row[1] for row in dataframe.iter_rows()}
    return mapping, values


def create_subscription_paper(plan, subscription):
    if not plan:
        return [
            dmc.Text(
                "No Subscription found",
                size="md",
                fw=700,
                c="red",
            ),
            dmc.Text(
                f"Plan Name: {plan['name']}" if plan else "No active plan",
                id="subscription_plan",
                style={"display": "none", "fontWeight": 700},
            ),
            dmc.Text(
                f"Price: $ {plan['amount']}" if plan else "",
                id="subscription_price",
                style={"display": "none", "fontWeight": 700},
            ),
        ]
    content = [
        dmc.Text(
            "Subscription Plan:",
            size="md",
            style={"textDecoration": "underline", "fontWeight": 500},
        ),
        dmc.Space(h=10),
        dmc.Text(
            f"Plan Name: {plan['name']}" if plan else "No active plan",
            id="subscription_plan",
            style={"fontWeight": 700},
        ),
        dmc.Text(
            f"Price: $ {plan['amount']}" if plan else "",
            id="subscription_price",
            style={"fontWeight": 700},
        ),
    ]
    if subscription:
        if subscription.cancel_at_period_end:
            content.append(
                dmc.Text(
                    f"Valid until: {subscription['period_end_date']}",
                    id="subscription_valid",
                    fw=700,
                )
            )
        else:
            content.append(
                dmc.Text(
                    f"Status: {subscription['status']}",
                    id="subscription_valid",
                    fw=700,
                )
            )
    return content


def create_credit_card_paper(credit_cards, openpay_id, subscription_card_ids):
    if not credit_cards:
        return [html.Div("No cards available")]
    return [
        dmc.Text(
            "Credit Cards:",
            size="md",
            style={
                "textDecoration": "underline",
                "marginLeft": 20,
                "fontWeight": 500,
            },
        ),
        dmc.Space(h=10),
        html.Div(
            id="credit_cards_display",
            children=(
                [
                    html.Div(
                        [
                            dmc.ActionIcon(
                                DashIconify(
                                    icon=(
                                        "radix-icons:minus-circled"
                                        if card["id"] not in subscription_card_ids
                                        else "radix-icons:check-circled"
                                    ),
                                    width=20,
                                ),
                                id=(
                                    {
                                        "type": "delete_credit_card",
                                        "card_id": card["id"],
                                        "customer_id": openpay_id,
                                    }
                                    if card["id"] not in subscription_card_ids
                                    else {"type": "used_credit_card"}
                                ),
                                size="lg",
                                variant="filled",
                                style={
                                    "background": "transparent",
                                    "color": (
                                        "red"
                                        if card["id"] not in subscription_card_ids
                                        else "yellow"
                                    ),
                                    "position": "absolute",
                                    "top": "150px",
                                    "right": "0px",
                                    "border": "none",
                                    "cursor": (
                                        "pointer"
                                        if card["id"] not in subscription_card_ids
                                        else "default"
                                    ),
                                    "zIndex": 999,
                                },
                            ),
                            dcs.DashCreditCards(
                                number=card["card_number"],
                                name=card["holder_name"],
                                expiry=f"{card['expiration_month']}/{card['expiration_year']}",
                                issuer=card["brand"],
                            ),
                        ],
                        style={
                            "position": "relative",
                            "padding": "0px",
                            "borderRadius": "15px",
                        },
                    )
                    for card in credit_cards
                ]
                or [html.Div("No cards available")]
            ),
            style={
                "display": "flex",
                "flexWrap": "wrap",
                "justifyContent": "space-between",
                "position": "relative",
                "gap": "10px",
                "margin": "10px",
                "padding": "12px",
            },
        ),
    ]
