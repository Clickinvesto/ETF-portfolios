import json
import uuid

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
    State,
)
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify
from flask import current_app, session, flash
from flask_login import logout_user

from src.Dash.services.database import OpenPay
from src.Dash.services.NotificationProvider import NotificationProvider

notify = NotificationProvider()
api = OpenPay()

register_page(
    __name__, name="Configuration", path=current_app.config["URL_CONFIGURATION"]
)


def layout(socket_ids=None, **kwargs):
    if socket_ids == None:
        raise PreventUpdate
    user = session.get("user", False)
    if not user:
        return dmc.Container()
    error_message = {"message": None, "error_message": None}
    return full_layout(error_message)


def full_layout(error_message):
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
        return html.Div(
            [
                dmc.Title("Customer Configuration", order=2),
                dmc.Space(h=10),
                dmc.Paper(
                    id="subscription_paper",
                    children=[
                        dmc.Text(
                            "Subscription Plan:",
                            size="md",
                            style={
                                "textDecoration": "underline",
                                "fontWeight": 500,
                            },
                        ),
                        dmc.Space(h=10),
                        dmc.Skeleton(height=30, width="100%", animate=True),
                        dmc.Space(h=10),
                        dmc.Skeleton(height=30, width="50%", animate=True),
                    ],
                ),
                dmc.Space(h=20),
                dmc.Paper(
                    id="credit_cards_paper",
                    children=[
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
                        dmc.Group(
                            children=[
                                dmc.Skeleton(height=150, width="100%", animate=True, style={"flex": 1}),
                                dmc.Skeleton(height=150, width="100%", animate=True, style={"flex": 1}),
                            ],
                            position="apart",
                            spacing="md",
                            grow=True
                        ),
                    ]
                ),
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
                    style={
                        "width": "calc(100% - 1px)",
                        "display": "flex",
                        "flex-direction": "row",
                        "align": "center",
                        "justify-content": "space-around",
                        "flex-wrap": "wrap",
                        "gap": "10px",
                    },
                ),
                # Add a hidden dcc.Location, div to trigger for redirection
                dcc.Location(id="redirect", refresh=True),
                html.Div(id="redirect-trigger", style={"display": "none"}),
                dcc.Store(id="store-account-data", storage_type="memory"),
            ],
            fluid=True,
        )


@callback(
    Output("subscription_paper", "children"),
    [Input("subscription_paper", "id")],
)
def update_subscription_paper(_):
    user = session.get("user", False)
    openpay_id = user.get("openpay_id", "")
    if openpay_id:
        subscription, plan, error_message = api.fetch_subscription_and_plan(openpay_id)
        if error_message["error_message"]:
            return [
                dmc.Text(
                    error_message["message"],
                    size="md",
                    fw=700,
                    c="red",
                )
            ]
        elif subscription is None:
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
        else:
            return [
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


@callback(
    Output("credit_cards_paper", "children"),
    [Input("credit_cards_paper", "id")],
)
def update_credit_cards_paper(_):
    user = session.get("user", False)
    openpay_id = user.get("openpay_id", "")
    api.fetch_credit_cards(openpay_id)

    subscription_card_ids = [
        sub["card"]["id"]
        for sub in api.subscription_data["data"]
        if sub["status"] == "active"
    ]

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
                                        "customer_id": openpay_id,
                                    }
                                    if card["id"]
                                    not in subscription_card_ids
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
    ]


@callback(
    Output("credit_cards_display", "children", allow_duplicate=True),
    Input(
        {"type": "delete_credit_card", "card_id": ALL, "customer_id": ALL}, "n_clicks"
    ),
    State("dash_websocket", "socketId"),
    prevent_initial_call=True,
)
def delete_credit_card_callback(n_clicks_list, socket_id):
    if not any(n_clicks_list):
        raise PreventUpdate

    triggered_id_str = callback_context.triggered[0]["prop_id"].split(".")[0]
    triggered_id = json.loads(triggered_id_str)
    card_id = triggered_id["card_id"] or None
    if card_id:
        notification_id = uuid.uuid4().hex
        notify.send_socket(
            to=socket_id,
            type="start_process",
            title="Deleting Card",
            id=notification_id,
        )
        if not api.delete_card_from_openpay(triggered_id["customer_id"], card_id):
            notify.send_socket(
                to=socket_id,
                type="error_process",
                title="Error",
                message="Unable to delete credit card. Try again.",
                id=notification_id,
            )
            return no_update

        api.cards_data = [card for card in api.cards_data if card.get("id") != card_id]
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
            notify.send_socket(
                to=socket_id,
                type="success_process",
                title="Success",
                message="Card deleted successfully!",
                id=notification_id,
            )
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
            return updated_card_displays
        else:
            return [html.Div("No cards available")]


@callback(
    [
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
            raise PreventUpdate
        # Delete OpenPay account first
        if api.delete_account_from_openpay(openpay_id):
            if api.delete_user(email, openpay_id, True, True, True):
                logout_user()
                flash("Account deleted successfully.", "warning")
                return [current_app.config["URL_SIGNUP"]]
            else:
                raise PreventUpdate
        else:
            raise PreventUpdate
    raise PreventUpdate


@callback(
    Output("redirect-trigger", "children"),
    Output("store-account-data", "data"),
    Input("delete_openpay_account", "n_clicks"),
    State("dash_websocket", "socketId"),
    prevent_initial_call=True,
)
def delete_openpay_account_callback(n_clicks, socket_id):
    if n_clicks:
        user_session = session["user"]
        email = user_session.get("email", "")
        openpay_id = user_session.get("openpay_id", "")
        notification_id = uuid.uuid4().hex
        if openpay_id:
            notify.send_socket(
                to=socket_id,
                type="success",
                title="Deleting user",
                message="Deleting user from openpay. Please wait a moment.",
            )
            if api.delete_account_from_openpay(openpay_id):
                notify.send_socket(
                    to=socket_id,
                    type="success",
                    title="Deleting user",
                    message="User from openpay deleted successfully!",
                )
                if api.delete_user(email, openpay_id, False, True, True):
                    notify.send_socket(
                        to=socket_id,
                        type="success_process",
                        title="Deleting user",
                        message="Openpay account and associated data deleted successfully.",
                    )
                    notify.send_socket(
                        to=socket_id,
                        type="success",
                        title="Refreshing Data",
                        message="Reloading user's data. Please wait!",
                    )
                    return (
                        dcc.Location(
                            pathname=current_app.config["URL_CONFIGURATION"], id="redirect"
                        ),
                        {"refresh": True},
                    )
            else:
                notify.send_socket(
                    to=socket_id,
                    type="error_process",
                    title="Deleting user",
                    message="Failed to delete OpenPay account. Please try again later.",
                    id=notification_id,
                )
                return (
                    no_update,
                    no_update,
                )
        else:
            notify.send_socket(
                to=socket_id,
                type="error_process",
                title="Deleting user",
                message="No OpenPay ID found for the user.",
                id=notification_id,
            )
            return no_update, no_update
    raise PreventUpdate


@callback(
    Output("credit_cards_display", "children", allow_duplicate=True),
    Output("subscription_plan", "children"),
    Output("subscription_price", "children"),
    Input("store-account-data", "data"),
    prevent_initial_call=True,
)
def refresh_data(store_data):
    if store_data and store_data.get("refresh"):
        openpay_id = session["user"].get("openpay_id", "")
        subscription, plan, message = api.fetch_subscription_and_plan(
            openpay_id
        )

        if plan:
            plan_name = f"Plan Name: {plan['name']}"
            plan_price = f"Price: $ {plan['amount']}"
        else:
            plan_name = "No subscription available"
            plan_price = ""

        api.fetch_credit_cards(openpay_id)
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
                for card in api.cards_data
            ]
            return (
                card_displays,
                plan_name,
                plan_price,
            )
        else:
            return (
                [html.Div("No cards available")],
                plan_name,
                plan_price,
            )
    raise PreventUpdate
