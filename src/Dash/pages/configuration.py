import json
import os
import sqlite3

import dash_credit_cards as dcs
import dash_mantine_components as dmc
import openpay
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
from dotenv import load_dotenv
from flask import current_app, session, flash
from flask_login import logout_user

load_dotenv()
openpay.api_key = os.getenv("OPENPAY_APIKEY")
openpay.verify_ssl_certs = os.getenv("OPENPAY_VERIFY_SSL_CERTS") == 'True'
openpay.merchant_id = os.getenv("OPENPAY_MERCHANT_ID")
openpay.country = os.getenv("OPENPAY_COUNTRY")

register_page(__name__, name="Configuration", path=current_app.config["URL_CONFIGURATION"])

subscription_data = []


def layout(**kwargs):
    user = session.get("user", False)
    if not user:
        return dmc.Container()
    openpay_id = user.get("openpay_id", "")
    if openpay_id is None or openpay_id == "":
        return full_layout(None, None, None, {"message": "No OpenPay ID found for the user.",
                                              "error_message": "No OpenPay ID found for the user."})
    else:
        customer, subscription, plan, error_message = fetch_subscription_and_plan(user.get("openpay_id", ""))
    return full_layout(customer["id"], subscription, plan, error_message)


def full_layout(customer_id, subscription, plan, error_message):
    if error_message["error_message"] is not None:
        return html.Div(
            [
                dmc.Title("Configuration", order=2),
                dmc.Space(h=10),
                dmc.Text(error_message["message"],
                         size="md",
                         fw=700,
                         c="red",
                         ),
            ],
            style={"padding": "20px"},
        )
    else:
        # subscription_card_ids = [sub["card"]["id"] for sub in subscription_data["data"]]
        subscription_card_ids = [sub["card"]["id"] for sub in subscription_data["data"] if sub["status"] == "active"]
        return html.Div(
            [
                dmc.Title("Customer Configuration", order=2),
                dmc.Space(h=10),
                dmc.Text("Subscription Plan:",
                         size="md",
                         style={
                             "textDecoration": "underline",
                             "marginLeft": 20,
                             "fontWeight": 500
                         },
                         ),
                dmc.Space(h=10),
                dmc.Container(
                    [
                        dmc.Text(f"Plan Name: {plan['name']}" if plan else "No active plan", style={"fontWeight": 700}),
                        dmc.Text(f"Price: $ {plan['amount']}" if plan else "", id="subscription_price",
                                 style={"fontWeight": 700}),
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
                dmc.Text("Credit Cards:",
                         size="md",
                         style={
                             "textDecoration": "underline",
                             "marginLeft": 20,
                             "fontWeight": 500
                         },
                         ),
                dmc.Space(h=10),
                html.Div(
                    id="credit_cards_display",
                    children=([
                                  dmc.Paper(
                                      [
                                          dmc.ActionIcon(
                                              DashIconify(
                                                  icon="radix-icons:minus-circled" if card[
                                                                                          "id"] not in subscription_card_ids else "radix-icons:check-circled",
                                                  width=20
                                              ),
                                              id={"type": "delete_credit_card", "card_id": card["id"],
                                                  "customer_id": customer_id} if card[
                                                                                     "id"] not in subscription_card_ids else {
                                                  "type": "used_credit_card"},
                                              size="lg",
                                              variant="filled",
                                              style={
                                                  "background": "transparent",
                                                  "color": "red" if card[
                                                                        "id"] not in subscription_card_ids else "yellow",
                                                  "position": "absolute",
                                                  "top": "150px",
                                                  "right": "0px",
                                                  "border": "none",
                                                  "cursor": "pointer" if card[
                                                                             "id"] not in subscription_card_ids else "default",
                                                  "zIndex": 999,
                                              }
                                          ),
                                          dcs.DashCreditCards(
                                              number=card["card_number"],
                                              name=card["holder_name"],
                                              expiry=f"{card['expiration_month']}/{card['expiration_year']}",
                                              issuer=card["brand"],
                                          )
                                      ],
                                      style={
                                          "position": "relative",
                                          "padding": "0px",
                                          "borderRadius": "15px",
                                      }
                                  )
                                  for card in cards_data
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
                        dmc.Button("Delete Openpay Account", color="orange", id="delete_openpay_account"),
                    ],
                    position="left",
                ),
                dmc.Text("", id="account_deleted_message", fw=200, c="red"),
                # Add a hidden dcc.Location, div to trigger for redirection
                dcc.Location(id="redirect", refresh=True),
                html.Div(id="redirect-trigger", style={"display": "none"})
            ],
            style={
                "padding": "20px",
            },
        )


def fetch_subscription_and_plan(openpay_id):
    try:
        customer = openpay.Customer.retrieve(openpay_id)

        global subscription_data
        subscription_data = customer.subscriptions.all()

        global cards_data
        cards_data = fetch_credit_cards(customer)

        active_subscription = None
        for subscription in subscription_data["data"]:
            if subscription.get("status") == "active":
                active_subscription = subscription
                break

        if active_subscription:
            plan = openpay.Plan.retrieve(active_subscription["plan_id"])
            return customer, active_subscription, plan, {"message": None, "error_message": None}
        else:
            return customer, None, None, {"message": "No active subscriptions found.", "error_message": None}
    except openpay.error.OpenpayError as e:
        print("Error fetching subscription details:", e)
        return None, None, None, {"message": None, "error_message": "Error fetching subscription details: {}".format(e)}


# Define a function to fetch user's credit card information from OpenPay
def fetch_credit_cards(customer):
    cards = customer.cards.all()
    return cards["data"]


@callback(
    Output("credit_cards_display", "children"),
    Output("credit_card_deleted_message", "children"),
    Input({"type": "delete_credit_card", "card_id": ALL, "customer_id": ALL}, "n_clicks"),
)
def delete_credit_card_callback(n_clicks_list):
    if not any(n_clicks_list):
        raise PreventUpdate

    triggered_id_str = callback_context.triggered[0]["prop_id"].split(".")[0]
    triggered_id = json.loads(triggered_id_str)
    card_id = triggered_id["card_id"]
    if card_id:
        global cards_data
        cards_data = [card for card in cards_data if card.get("id") != card_id]
        if not delete_card_from_openpay(triggered_id["customer_id"], card_id):
            return no_update, "Error: deleting card from OpenPay"

        # Handle the case where there are no subscriptions
        global subscription_data
        if subscription_data and "data" in subscription_data:
            subscription_card_ids = [sub["card"]["id"] for sub in subscription_data["data"] if
                                     sub["status"] == "active"]
        else:
            subscription_card_ids = []
        # Parse card IDs from subscription data
        # subscription_card_ids = [sub["card"]["id"] for sub in subscription_data["data"]]
        if cards_data:
            updated_card_displays = [
                dmc.Paper(
                    [
                        dmc.ActionIcon(
                            DashIconify(
                                icon="radix-icons:minus-circled" if card[
                                                                        "id"] not in subscription_card_ids else "radix-icons:check-circled",
                                width=20
                            ),
                            id={"type": "delete_credit_card", "card_id": card["id"],
                                "customer_id": triggered_id["customer_id"]} if
                            card["id"] not in subscription_card_ids else {"type": "used_credit_card"},
                            size="lg",
                            variant="filled",
                            style={
                                "background": "transparent",
                                "color": "red" if card["id"] not in subscription_card_ids else "yellow",
                                "position": "absolute",
                                "top": "150px",
                                "right": "0px",
                                "border": "none",
                                "cursor": "pointer" if card["id"] not in subscription_card_ids else "default",
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
                for card in cards_data
            ]
            return updated_card_displays, "Card deleted successfully!"
        else:
            return [html.Div("No cards available")], ""


def delete_card_and_purchases_from_db(card_id):
    try:
        conn = sqlite3.connect(current_app.config["DATABASE_PATH"])
        cursor = conn.cursor()

        delete_purchases_query = """DELETE FROM purchases WHERE card_id = ?"""
        cursor.execute(delete_purchases_query, (card_id,))
        delete_card_query = """DELETE FROM cards WHERE card_id = ?"""
        cursor.execute(delete_card_query, (card_id,))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error deleting card and purchases from database:", e)
        return False


def delete_card_from_openpay(customer_id, card_id):
    try:
        customer = openpay.Customer.retrieve(customer_id)
        card = customer.cards.retrieve(card_id)
        card.delete()
        # Delete card and purchases from the database
        if not delete_card_and_purchases_from_db(card_id):
            raise Exception("Failed to delete card and purchases from the database.")
        return True
    except openpay.error.OpenpayError as e:
        print("Error deleting card from OpenPay:", e)
        return False
    except Exception as e:
        print(e)
        return False


@callback(
    [Output("account_deleted_message", "children", allow_duplicate=True),
     Output("redirect", "href")],
    Input("delete_user", "n_clicks"),
    prevent_initial_call=True
)
def delete_user_callback(n_clicks):
    if n_clicks:
        user_session = session["user"]
        email = user_session.get("email", "")
        openpay_id = user_session.get("openpay_id", "")
        if openpay_id is None or openpay_id == "":
            return "No OpenPay ID found for the user.", no_update
        else:
            if delete_user(email, openpay_id):
                logout_user()
                flash("Account deleted successfully.", "warning")
                return "Account deleted successfully.", current_app.config["URL_SIGNUP"]
            else:
                return "Failed to delete account. Please try again later.", no_update
    raise PreventUpdate


def delete_user(email, openpay_id):
    try:
        conn = sqlite3.connect(current_app.config["DATABASE_PATH"])
        cursor = conn.cursor()

        # Remove user from the users table
        delete_user_query = """DELETE FROM users WHERE email = ?"""
        cursor.execute(delete_user_query, (email,))

        # Remove subscription for that specific customer
        delete_cards_query = """DELETE FROM cards WHERE customer_id = ?"""
        cursor.execute(delete_cards_query, (openpay_id,))

        # Remove purchases for that specific customer
        delete_purchases_query = """DELETE FROM purchases WHERE customer_id = ?"""
        cursor.execute(delete_purchases_query, (openpay_id,))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error deleting user:", e)
        return False


@callback(
    Output("account_deleted_message", "children", allow_duplicate=True),
    Input("delete_openpay_account", "n_clicks"),
    prevent_initial_call=True
)
def delete_openpay_account_callback(n_clicks):
    if n_clicks:
        user_session = session["user"]
        openpay_id = user_session.get("openpay_id", "")
        if openpay_id:
            if delete_account_from_openpay(openpay_id):
                return "Openpay account deleted successfully."
            else:
                return "Failed to delete OpenPay account. Please try again later."
        else:
            return "No OpenPay ID found for the user."
    raise PreventUpdate


def delete_account_from_openpay(customer_id):
    try:
        customer = openpay.Customer.retrieve(customer_id)
        subscriptions = customer.subscriptions.all()
        for subscription in subscriptions["data"]:
            subscription.delete()
        cards = customer.cards.all()
        for card in cards["data"]:
            card.delete()

        # Delete the customer account itself
        # openpay.Customer.delete(customer_id)
        return True
    except openpay.error.OpenpayError as e:
        print("Error deleting account from OpenPay:", e)
        return False
