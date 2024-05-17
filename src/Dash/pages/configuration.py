import json

import dash_credit_cards as dcs
import dash_mantine_components as dmc
from dash import (
    ALL,
    dcc,
    callback_context,
    register_page,
    no_update,
    html,
    callback,
    Input,
    Output,
)
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify
from flask import current_app, session, flash
from flask_login import logout_user

from src.Dash.services.database import OpenPay

api = OpenPay()

register_page(
    __name__, name="Configuration", path=current_app.config["URL_CONFIGURATION"]
)


def layout(**kwargs):
    user = session.get("user", False)
    if not user:
        return dmc.Container()
    openpay_id = user.get("openpay_id", "")
    if openpay_id is None or openpay_id == "":
        return full_layout(
            None,
            None,
            None,
            {
                "message": "No Subscription found",
                "error_message": "No OpenPay ID found for the user.",
            },
        )
    else:
        customer, subscription, plan, error_message = api.fetch_subscription_and_plan(
            user.get("openpay_id", "")
        )
    return full_layout(customer["id"], subscription, plan, error_message)


def full_layout(customer_id, subscription, plan, error_message):
    if error_message["error_message"] is not None:
        return html.Div(
            [
                dmc.Title("Configuration", order=2),
                dmc.Space(h=10),
                dmc.Text(
                    error_message["message"],
                    size="md",
                    fw=700,
                    c="red",
                ),
            ],
            style={"padding": "20px"},
        )
    else:
        subscription_card_ids = [
            sub["card"]["id"]
            for sub in api.subscription_data["data"]
            if sub["status"] == "active"
        ]
        return html.Div(
            [
                dmc.Title("Customer Configuration", order=2),
                dmc.Space(h=10),
                dmc.Text(
                    "Subscription Plan:",
                    size="md",
                    style={
                        "textDecoration": "underline",
                        "marginLeft": 20,
                        "fontWeight": 500,
                    },
                ),
                dmc.Space(h=10),
                dmc.Container(
                    [
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
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "border": "1px solid purple",
                        "padding": 20,
                        "marginLeft": 20,
                    },
                ),
                dmc.Space(h=20),
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
                            dmc.Paper(
                                [
                                    dmc.ActionIcon(
                                        DashIconify(
                                            icon=(
                                                "radix-icons:minus-circled"
                                                if card["id"]
                                                not in subscription_card_ids
                                                else "radix-icons:check-circled"
                                            ),
                                            width=20,
                                        ),
                                        id=(
                                            {
                                                "type": "delete_credit_card",
                                                "card_id": card["id"],
                                                "customer_id": customer_id,
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
                                                if card["id"]
                                                not in subscription_card_ids
                                                else "yellow"
                                            ),
                                            "position": "absolute",
                                            "top": "150px",
                                            "right": "0px",
                                            "border": "none",
                                            "cursor": (
                                                "pointer"
                                                if card["id"]
                                                not in subscription_card_ids
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
                            for card in api.cards_data
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
                dmc.Text("", id="credit_card_deleted_message", fw=200, c="red"),
                dmc.Space(h=10),
                dmc.Group(
                    [
                        dmc.Button("Delete User", color="red", id="delete_user"),
                        dmc.Space(w=10),
                        dmc.Button(
                            "Delete Openpay Account",
                            color="orange",
                            id="delete_openpay_account",
                        ),
                    ],
                    position="left",
                ),
                dmc.Text("", id="account_deleted_message", fw=200, c="red"),
                # Add a hidden dcc.Location, div to trigger for redirection
                dcc.Location(id="redirect", refresh=True),
                html.Div(id="redirect-trigger", style={"display": "none"}),
                dcc.Store(id="store-account-data", storage_type="memory"),
            ],
            style={
                "padding": "20px",
            },
        )


@callback(
    Output("credit_cards_display", "children", allow_duplicate=True),
    Output("credit_card_deleted_message", "children"),
    Input(
        {"type": "delete_credit_card", "card_id": ALL, "customer_id": ALL}, "n_clicks"
    ),
    prevent_initial_call=True,
)
def delete_credit_card_callback(n_clicks_list):
    if not any(n_clicks_list):
        raise PreventUpdate

    triggered_id_str = callback_context.triggered[0]["prop_id"].split(".")[0]
    triggered_id = json.loads(triggered_id_str)
    card_id = triggered_id["card_id"]
    if card_id:
        api.cards_data = [card for card in api.cards_data if card.get("id") != card_id]
        if not api.delete_card_from_openpay(triggered_id["customer_id"], card_id):
            return no_update, "Error: deleting card from OpenPay"

        # Handle the case where there are no subscriptions
        if api.subscription_data and "data" in api.subscription_data:
            subscription_card_ids = [
                sub["card"]["id"]
                for sub in api.subscription_data["data"]
                if sub["status"] == "active"
            ]
        else:
            subscription_card_ids = []
        if api.cards_data:
            updated_card_displays = [
                dmc.Paper(
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
                                    "customer_id": triggered_id["customer_id"],
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
                for card in api.cards_data
            ]
            return updated_card_displays, "Card deleted successfully!"
        else:
            return [html.Div("No cards available")], ""


@callback(
    [
        Output("account_deleted_message", "children", allow_duplicate=True),
        Output("redirect", "href"),
    ],
    Input("delete_user", "n_clicks"),
    prevent_initial_call=True,
)
def delete_user_callback(n_clicks):
    if n_clicks:
        user_session = session["user"]
        email = user_session.get("email", "")
        openpay_id = user_session.get("openpay_id", "")
        if openpay_id is None or openpay_id == "":
            return "No OpenPay ID found for the user.", no_update
        # Delete OpenPay account first
        if api.delete_account_from_openpay(openpay_id):
            if api.delete_user(email, openpay_id, True, True, True):
                logout_user()
                flash("Account deleted successfully.", "warning")
                return "Account deleted successfully.", current_app.config["URL_SIGNUP"]
            else:
                return (
                    "Failed to delete user data from the database. Please try again later.",
                    no_update,
                )
        else:
            return (
                "Failed to delete OpenPay account. Please try again later.",
                no_update,
            )
    raise PreventUpdate


@callback(
    Output("account_deleted_message", "children", allow_duplicate=True),
    Output("redirect-trigger", "children"),
    Output("store-account-data", "data"),
    Input("delete_openpay_account", "n_clicks"),
    prevent_initial_call=True,
)
def delete_openpay_account_callback(n_clicks):
    if n_clicks:
        user_session = session["user"]
        email = user_session.get("email", "")
        openpay_id = user_session.get("openpay_id", "")
        if openpay_id:
            if api.delete_account_from_openpay(openpay_id):
                api.delete_user(email, openpay_id, False, True, True)
                return (
                    "Openpay account and associated data deleted successfully.",
                    dcc.Location(
                        pathname=current_app.config["URL_CONFIGURATION"], id="redirect"
                    ),
                    {"refresh": True},
                )
            else:
                return (
                    "Failed to delete OpenPay account. Please try again later.",
                    no_update,
                    no_update,
                )
        else:
            return "No OpenPay ID found for the user.", no_update, no_update
    raise PreventUpdate


@callback(
    Output("credit_cards_display", "children", allow_duplicate=True),
    Output("subscription_plan", "children"),
    Output("subscription_price", "children"),
    Output("account_deleted_message", "children", allow_duplicate=True),
    Input("store-account-data", "data"),
    prevent_initial_call=True,
)
def refresh_data(store_data):
    if store_data and store_data.get("refresh"):
        openpay_id = session["user"].get("openpay_id", "")
        customer, subscription, plan, message = api.fetch_subscription_and_plan(
            openpay_id
        )

        if plan:
            plan_name = f"Plan Name: {plan['name']}"
            plan_price = f"Price: $ {plan['amount']}"
        else:
            plan_name = "No subscription available"
            plan_price = ""

        if api.cards_data:
            subscription_card_ids = [
                sub["card"]["id"]
                for sub in api.subscription_data["data"]
                if sub["status"] == "active"
            ]
            card_displays = [
                dmc.Paper(
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
                                    "customer_id": customer["id"],
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
                for card in api.cards_data
            ]
            return (
                card_displays,
                plan_name.plan_price,
                "Openpay account and associated data deleted successfully.",
            )
        else:
            return (
                [html.Div("No cards available")],
                plan_name,
                plan_price,
                "Openpay account and associated data deleted successfully.",
            )
    raise PreventUpdate
