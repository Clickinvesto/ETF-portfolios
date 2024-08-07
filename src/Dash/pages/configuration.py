import json
from unittest import result
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
from flask_login import logout_user, current_user

from src.Dash.services.API.PaymentGateway import PaymentGateway
from src.Dash.services.API.PaymentGatway import PaymentGatway
from src.Dash.services.NotificationProvider import NotificationProvider
from src.Dash.components.account_information import (
    create_subscription_paper,
    create_credit_card_paper, create_paypal_subscription_paper, create_payment_history_table,
)
from src.models import PaypalSubscription

notify = NotificationProvider()
payment_gateway = PaymentGateway()
api = PaymentGatway()
db = current_app.db

register_page(
    __name__, name="Configuration", path=current_app.config["URL_CONFIGURATION"]
)


def layout(socket_ids=None, **kwargs):
    if socket_ids is None:
        raise PreventUpdate
    user = session.get("user", False)
    if not user:
        return dmc.Container()
    return full_layout()


def full_layout():
    return dmc.Container(
        [
            dmc.Title("Customer Configuration", order=2),
            dmc.Space(h=10),
            dmc.Flex(
                [
                    dmc.Paper(
                        [
                            dmc.Stack(
                                [
                                    dmc.Stack(
                                        [
                                            dmc.Text(
                                                "Subscription Plan:",
                                                size="md",
                                                style={
                                                    "textDecoration": "underline",
                                                    "fontWeight": 500,
                                                },
                                            ),
                                            dmc.Space(h=10),
                                            dmc.Skeleton(
                                                height=30,
                                                width="100%",
                                                animate=True,
                                            ),
                                            dmc.Space(h=10),
                                            dmc.Skeleton(
                                                height=30, width="50%", animate=True
                                            ),

                                            dmc.Stack(
                                                [
                                                    dmc.Space(h=5),
                                                    dmc.Skeleton(
                                                        height=30,
                                                        width="30%",
                                                        animate=True,
                                                    ),
                                                ],
                                                display="flex",
                                                align="flex-end"
                                            )
                                        ],
                                        id="subscription_paper",
                                        justify="flex-start",
                                    ),
                                ],
                                justify="space-between",
                                style={"height": "100%"},
                            ),
                        ],
                    ),
                    dmc.Space(h=20),
                    # Add new Paper for payment history
                    dmc.Paper(
                        [
                            dmc.Stack(
                                [
                                    dmc.Text(
                                        "Payment History:",
                                        size="md",
                                        style={
                                            "textDecoration": "underline",
                                            "fontWeight": 500,
                                        },
                                    ),
                                    dmc.Space(h=10),
                                    dmc.Table(
                                        id="payments_table",
                                        withTableBorder=True,
                                        withColumnBorders=True,
                                        withRowBorders=True,
                                    ),
                                ],
                                justify="space-between",
                                style={"height": "100%"},
                            ),
                        ],
                    ),
                    dmc.Space(h=20),
                    dcc.Location(id="redirect", refresh=True),
                    html.Div(id="redirect-trigger", style={"display": "none"}),
                    dcc.Store(id="store-account-data", storage_type="memory"),
                ],
                style={
                    "width": "calc(100% - 1px)",
                    "display": "flex",
                    "flex-direction": "column",
                    "align": "center",
                    # "justify-content": "space-around",
                    "flex-wrap": "wrap",
                    "gap": "10px",
                },
            ),
        ],
        fluid=True,
    )


@callback(
    [
        Output("subscription_paper", "children", allow_duplicate=True),
        Output("payments_table", "children"),
    ],
    Input("subscription_paper", "id"),
    State("dash_websocket", "socketId"),
    prevent_initial_call="initial_duplicate",
)
def update_subscription_paper(_, socket_id):
    user = session.get("user", False)

    content = create_paypal_subscription_paper(user["id"])
    payment_history = create_payment_history_table(user["id"])

    return content, payment_history


# @callback(
#     Output("credit_cards_paper", "children"),
#     Input("credit_cards_paper", "id"),
#     State("dash_websocket", "socketId"),
#     prevent_initial_call="initial_duplicate",
# )
# def update_credit_cards_paper(_, socket_id):
#     user = session.get("user", False)
#     openpay_id = user.get("openpay_id", False)
#
#     if not openpay_id:
#         raise PreventUpdate
#     result = api.fetch_subscription_and_plan(openpay_id)
#     subscription, plan = result["item"]
#     if result["error"]:
#         notify.send_socket(
#             to=socket_id,
#             type="error",
#             title="Something went wrong",
#             message=result["error"],
#         )
#         return []
#
#     subscription_card_ids = subscription["card"]
#     result = api.fetch_credit_cards(openpay_id)
#     credit_cards = result["item"]
#     return create_credit_card_paper(credit_cards, openpay_id, subscription_card_ids)


# @callback(
#     Output("credit_cards_display", "children", allow_duplicate=True),
#     Input(
#         {"type": "delete_credit_card", "card_id": ALL, "customer_id": ALL}, "n_clicks"
#     ),
#     State("dash_websocket", "socketId"),
#     prevent_initial_call=True,
# )
# def delete_credit_card_callback(n_clicks_list, socket_id):
#     if not any(n_clicks_list):
#         raise PreventUpdate
#     user_session = session["user"]
#     email = user_session.get("email", "")
#     openpay_id = user_session.get("openpay_id", "")
#     triggered_id_str = callback_context.triggered[0]["prop_id"].split(".")[0]
#     triggered_id = json.loads(triggered_id_str)
#     card_id = triggered_id["card_id"] or False
#     if not card_id:
#         raise PreventUpdate
#
#     notification_id = uuid.uuid4().hex
#     notify.send_socket(
#         to=socket_id,
#         type="start_process",
#         title="Deleting Card",
#         id=notification_id,
#     )
#     result = api.delete_card_from_openpay(triggered_id["customer_id"], card_id)
#     if result["error"]:
#         notify.send_socket(
#             to=socket_id,
#             type="error_process",
#             title="Error",
#             message=result["error"],
#             id=notification_id,
#         )
#         raise PreventUpdate
#     result = api.fetch_credit_cards(openpay_id=openpay_id)
#     if result["error"]:
#         notify.send_socket(
#             to=socket_id,
#             type="error_process",
#             title="Error",
#             message=result["error"],
#             id=notification_id,
#         )
#         raise PreventUpdate
#     cards_data = [card for card in result["item"] if card.get("id") != card_id]
#
#     result = api.fetch_subscription_and_plan(openpay_id)
#     subscription, plan = result["item"]
#     subscription_card_ids = subscription.get("card", False)
#
#     if cards_data:
#         notify.send_socket(
#             to=socket_id,
#             type="success_process",
#             title="Success",
#             message="Card deleted successfully!",
#             id=notification_id,
#         )
#         return create_credit_card_paper(cards_data, openpay_id, subscription_card_ids)
#     raise PreventUpdate
#
#
# @callback(
#     Output("redirect", "href"),
#     Input("delete_user", "n_clicks"),
#     State("dash_websocket", "socketId"),
#     prevent_initial_call=True,
# )
# def delete_user_callback(n_clicks, socket_id):
#     if n_clicks:
#         user_session = session["user"]
#         email = user_session.get("email", "")
#         openpay_id = user_session.get("openpay_id", "")
#         if openpay_id is None or openpay_id == "":
#             raise PreventUpdate
#         # Delete OpenPay account first
#         notification_id = uuid.uuid4().hex
#         notify.send_socket(
#             to=socket_id,
#             type="start_process",
#             title="In process",
#             message="We are deleting all related information. This can take a moment.",
#             id=notification_id,
#         )
#         if api.delete_account_from_openpay(openpay_id):
#             if api.delete_user(email, openpay_id, True, True, True):
#                 notify.send_socket(
#                     to=socket_id,
#                     type="success_process",
#                     title="We deleted your account",
#                     message="All information is deleted",
#                     id=notification_id,
#                 )
#                 logout_user()
#                 return [current_app.config["URL_SIGNUP"]]
#             else:
#                 raise PreventUpdate
#         else:
#             raise PreventUpdate
#     raise PreventUpdate
#
#
# @callback(
#     Output("redirect-trigger", "children"),
#     Output("store-account-data", "data"),
#     Input("delete_openpay_account", "n_clicks"),
#     State("dash_websocket", "socketId"),
#     prevent_initial_call=True,
# )
# def delete_openpay_account_callback(n_clicks, socket_id):
#     if n_clicks:
#         user_session = session["user"]
#         email = user_session.get("email", "")
#         openpay_id = user_session.get("openpay_id", "")
#         notification_id = uuid.uuid4().hex
#         if openpay_id:
#             notify.send_socket(
#                 to=socket_id,
#                 id=notification_id,
#                 type="start_process",
#                 title="Deleting user",
#                 message="Deleting user from openpay. Please wait a moment.",
#             )
#
#             deleted_openay = api.delete_account_from_openpay(openpay_id)
#             delete_user = api.delete_user(email, openpay_id, False, True, True)
#             if deleted_openay["error"]:
#                 notify.send_socket(
#                     to=socket_id,
#                     type="error_process",
#                     title="Deleting user",
#                     message=deleted_openay["error"],
#                     id=notification_id,
#                 )
#             if delete_user["error"]:
#                 notify.send_socket(
#                     to=socket_id,
#                     type="error_process",
#                     title="Deleting user",
#                     message=delete_user["error"],
#                     id=notification_id,
#                 )
#
#             notify.send_socket(
#                 to=socket_id,
#                 id=notification_id,
#                 type="success_process",
#                 title="Refreshing Data",
#                 message="Reloading user's data. Please wait!",
#             )
#
#             # Delete the account from the user session
#             user_session["openpay_id"] = None
#             user_session["subscription"] = None
#             session["user"] = user_session
#             return (
#                 dcc.Location(
#                     pathname=current_app.config["URL_CONFIGURATION"],
#                     id="redirect",
#                 ),
#                 {"refresh": True},
#             )
#         else:
#             notify.send_socket(
#                 to=socket_id,
#                 type="error",
#                 title="Deleting user",
#                 message="No OpenPay ID found for the user.",
#             )
#     raise PreventUpdate
#

# @callback(
#     Output("credit_cards_paper", "children", allow_duplicate=True),
#     Output("subscription_paper", "children"),
#     Input("store-account-data", "data"),
#     prevent_initial_call=True,
# )
# def refresh_data(store_data):
#     if store_data and store_data.get("refresh"):
#         openpay_id = session["user"].get("openpay_id", "")
#         result = api.fetch_subscription_and_plan(openpay_id)
#         subscription, plan = result["item"]
#         subscription_card_ids = subscription.get("card", False)
#         content_subscription = create_subscription_paper(plan, subscription)
#
#         result = api.fetch_credit_cards(openpay_id)
#         credit_cards = result["item"]
#
#         content_card = create_credit_card_paper(
#             credit_cards, openpay_id, subscription_card_ids
#         )
#         return content_card, content_subscription
#     raise PreventUpdate
#
#
# @callback(
#     Output("subscription_paper", "children", allow_duplicate=True),
#     Input("cancle_subscription", "n_clicks"),
#     State("dash_websocket", "socketId"),
#     prevent_initial_call=True,
# )
# def update_subscription(n_clicks, socket_id):
#     user = session["user"]
#     notification_id = uuid.uuid4().hex
#     notify.send_socket(
#         to=socket_id,
#         id=notification_id,
#         type="start_process",
#         title="Canceling subscription",
#         message="We are canceling your subscription to the end of the period",
#     )
#     result = api.delete_subscription(user)
#     if result["error"]:
#         notify.send_socket(
#             to=socket_id,
#             id=notification_id,
#             type="error_process",
#             title="Canceling subscription",
#             message="Something went wrong. Please try again later",
#         )
#         raise PreventUpdate()
#
#     notify.send_socket(
#         to=socket_id,
#         id=notification_id,
#         type="success_process",
#         title="Cancling subscription",
#         message="Your subscription is cancled",
#     )
#     # Todo We should add until when the subscription is active
#     return [
#         dmc.Text(
#             "Subscription Plan:",
#             size="md",
#             style={
#                 "textDecoration": "underline",
#                 "fontWeight": 500,
#             },
#         ),
#         dmc.Space(h=10),
#         dmc.Skeleton(
#             height=30,
#             width="100%",
#             animate=True,
#         ),
#         dmc.Space(h=10),
#         dmc.Skeleton(height=30, width="50%", animate=True),
#     ]


@callback(
    Output("cancel-subscription-response", "data"),
    [Input("cancel-subscription-btn", "n_clicks")],
    [
        State("subscription-id", "data"),
        State("dash_websocket", "socketId")
    ],
    prevent_initial_call=True
)
def cancel_subscription(n_clicks, subscription_id, socket_id):
    if not session.get("user"):
        return {"error": "Must be logged in."}
    if not subscription_id:
        return {"error": "Subscription ID is required"}

    subscription = PaypalSubscription.query.filter_by(subscription_id=subscription_id, status='ACTIVE').first()
    if not subscription:
        return {"error": "Subscription not found"}

    notification_id = uuid.uuid4().hex
    notify.send_socket(
        to=socket_id,
        type="start_process",
        title="In process",
        message="We are deleting all related information. This can take a moment.",
        id=notification_id,
    )
    # Cancel the subscription through PayPal API
    user_id = session.get("user")["id"]
    response = payment_gateway.cancel_subscription(user_id=user_id, subscription_id=subscription_id)
    if response and response["item"] is False:
        return {
            "item": {
                "message": response["error"],
                "socket_id": socket_id,
                "notification_id": notification_id
            },
            "error": True,
        }

    # Update the subscription status in the database
    subscription.status = 'CANCELLED'
    db.session.commit()

    return {
        "item": {
            "message": "Subscription cancelled successfully",
            "socket_id": socket_id,
            "notification_id": notification_id
        },
        "error": False,
    }


@callback(
    Output("subscription_paper", "children", allow_duplicate=True),
    [Input("cancel-subscription-response", "data")],
    prevent_initial_call=True
)
def display_cancel_notification(response):
    if response and response["error"]:
        notify.send_socket(
            to=response["item"]["socket_id"],
            type="error_process",
            title="Something went wrong",
            message=response["item"]["message"],
            id=response["item"]["notification_id"]
        )
        raise PreventUpdate
    if response and response["error"] is False:
        notify.send_socket(
            to=response["item"]["socket_id"],
            type="success_process",
            title=response["item"]["message"],
            message=response["item"]["message"],
            id=response["item"]["notification_id"]
        )

    user = session.get("user", False)
    return create_paypal_subscription_paper(user["id"])
