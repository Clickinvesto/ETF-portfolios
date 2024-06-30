import dash_mantine_components as dmc
from dash import (
    register_page,
    html,
    dcc,
    callback,
    Input,
    Output,
    State,
    clientside_callback,
    no_update,
    ctx,
)
from flask import current_app, session
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify
from src.Dash.services.API.PaymentGateway import PaymentGateway
from src.Dash.services.API.SubscriptionService import SubscriptionService

db = current_app.db

register_page(__name__, name="Pricing", path=current_app.config["URL_PRICING"])


def create_confirmation_modal():
    return dmc.Modal(
        id="confirmation-modal",
        title="Confirm Cancellation",
        zIndex=10000,
        children=[
            dmc.Text(
                "This action will cancel your current subscription. Are you sure you want to do this?"
            ),
            dmc.Space(h=20),
            dmc.Group(
                [
                    dmc.Button("Yes", id="confirm-cancel-button", color="red"),
                    dmc.Button("No", id="close-modal-button"),
                ],
                justify="flex-end",
            ),
        ],
        size="sm",
        opened=False,
    )


def layout(socket_ids=None, **kwargs):
    if socket_ids is None:
        raise PreventUpdate

    return html.Div(
        [
            dcc.Interval(
                id="interval-component", interval=1, n_intervals=0, max_intervals=1
            ),
            dcc.Location(id="page-location", refresh=True),
            full_layout(user=session.get("user")),
            create_confirmation_modal(),
        ]
    )


def full_layout(user=False):
    signup = dmc.Button(
        "Sign Up",
        id="signup-button",
        variant="filled",
        color="indigo",
        style={
            "border-radius": "5px",
            "margin-top": "20px",
            "min-height": "45px",
        },
    )

    use_free = dmc.Button(
        "Use Free",
        id="use-free-button",
        variant="filled",
        color="indigo",
        style={
            "border-radius": "5px",
            "cursor": "pointer",
            "min-height": "45px",
        },
    )

    active = dmc.Button(
        "Active",
        color="green",
        fullWidth=True,
        style={
            "border-radius": "5px",
            "cursor": "default",
            "min-height": "45px",
            "margin-top": "25px",
        },
    )
    subscribe = html.Div(
        id="paypal-button-container", style={"min-height": "45px", "margin-top": "20px"}
    )

    if user:
        user_id = user.get("id")
        subscription_service = SubscriptionService()
        status = subscription_service.has_active_subscription(user_id)
        button = active if status["item"]["has_active"] else subscribe
    else:
        button = signup

    return dmc.Container(
        [
            dcc.Location(id="redirect", refresh=True),
            dcc.Store(
                id="paypal-store",
                data={
                    "" "scriptLoaded": False,
                    "clientId": current_app.config["PAYPAL_CLIENT_ID"],
                    "planId": current_app.config["PAYPAL_PLAN_ID"],
                },
            ),
            dcc.Store(id="subscription-status"),
            dmc.Grid(
                [
                    dmc.Stack(
                        [
                            dmc.Text(
                                "MONTHLY PLANS",
                                fw=700,
                                c="#004c94",
                                tt="uppercase",
                                size="xl",
                            ),
                            dmc.Group(
                                [
                                    dmc.Card(
                                        children=[
                                            dmc.CardSection(
                                                dmc.Center(
                                                    p="md",
                                                    children=[
                                                        dmc.Text(
                                                            "0 USD",
                                                            fw=700,
                                                            tt="uppercase",
                                                            c="#fff",
                                                            size="xl",
                                                        )
                                                    ],
                                                    style={"height": "160px"},
                                                ),
                                                style={"background-color": "#018BCF"},
                                            ),
                                            dmc.Group(
                                                [
                                                    dmc.Text(
                                                        "FREE",
                                                        fw=500,
                                                        tt="uppercase",
                                                        c="#018bcf",
                                                        size="xl",
                                                    ),
                                                ],
                                                justify="flex-start",
                                                mt="md",
                                                mb="xs",
                                            ),
                                            dmc.List(
                                                icon=DashIconify(
                                                    icon="material-symbols:check",
                                                    width=24,
                                                ),
                                                size="lg",
                                                spacing="sm",
                                                children=[
                                                    dmc.ListItem(
                                                        dmc.Text(
                                                            "10 Source ETF’s, keep growing",
                                                        ),
                                                    ),
                                                    dmc.ListItem(
                                                        "Comparison indexes S&P 500"
                                                    ),
                                                    dmc.ListItem(
                                                        "Access to the ETFs Clickinvesto best portfolios"
                                                    ),
                                                    dmc.ListItem("Monthly updates"),
                                                    dmc.ListItem(
                                                        "Access to the %s of each ETF Clickinvesto best portfolios",
                                                        icon=DashIconify(
                                                            icon="material-symbols:close",
                                                            width=24,
                                                        ),
                                                    ),
                                                ],
                                            ),
                                            dmc.Space(h=35),
                                            use_free,
                                        ],
                                        withBorder=True,
                                        shadow="sm",
                                        radius="md",
                                        style={"width": 350},
                                    ),
                                    dmc.Card(
                                        children=[
                                            dmc.CardSection(
                                                dmc.Center(
                                                    p="md",
                                                    children=[
                                                        dmc.Text(
                                                            "7 USD",
                                                            fw=700,
                                                            tt="uppercase",
                                                            c="#fff",
                                                            size="xl",
                                                        )
                                                    ],
                                                    style={"height": "160px"},
                                                ),
                                                style={"background-color": "#018BCF"},
                                            ),
                                            dmc.Group(
                                                [
                                                    dmc.Text(
                                                        "SILVER",
                                                        fw=500,
                                                        tt="uppercase",
                                                        c="#018bcf",
                                                        size="xl",
                                                    ),
                                                ],
                                                justify="flex-start",
                                                mt="md",
                                                mb="xs",
                                            ),
                                            dmc.List(
                                                icon=DashIconify(
                                                    icon="material-symbols:check",
                                                    width=24,
                                                ),
                                                size="lg",
                                                spacing="sm",
                                                children=[
                                                    dmc.ListItem(
                                                        dmc.Text(
                                                            "10 Source ETF’s, keep growing",
                                                        ),
                                                    ),
                                                    dmc.ListItem(
                                                        "Comparison indexes S&P 500"
                                                    ),
                                                    dmc.ListItem(
                                                        "Access to the ETFs Clickinvesto best portfolios"
                                                    ),
                                                    dmc.ListItem("Monthly updates"),
                                                    dmc.ListItem(
                                                        "Access to the %s of each ETF Clickinvesto best portfolios",
                                                    ),
                                                ],
                                            ),
                                            dmc.Space(h=10),
                                            button,
                                        ],
                                        withBorder=True,
                                        shadow="sm",
                                        radius="md",
                                        style={"width": 350},
                                    ),
                                ],
                                justify="center",
                                gap="xl",
                            ),
                        ],
                        align="center",
                    ),
                ],
                justify="center",
                align="flex-start",
                style={
                    "align-content": "center",
                    "min-width": 0,
                },
            ),
        ],
        fluid=True,
        style={
            "position": "fixed",
            "padding": "10px",
            "display": "block",
            "max-height": "calc(100% - 70px)",
            "width": "calc(100% - 200px)",
        },
    )


# @callback(
#     Output("subscription_modal", "opened", allow_duplicate=True),
#     Output("plan_text", "children"),
#     Input("subscription", "n_clicks"),
#     prevent_initial_call="initial_duplicate",
#     # prevent_initial_call=True,
# )
# def open_modal(n_clicks):
#     if n_clicks:
#         return True, "You selected the silver plan for 7USD"
#     raise PreventUpdate


# Callback to open the modal
@callback(
    Output("confirmation-modal", "opened", allow_duplicate=True),
    Output("redirect", "pathname"),
    Input("use-free-button", "n_clicks"),
    Input("signup-button", "n_clicks"),
    State("subscription-status", "data"),
    prevent_initial_call=True,
)
def open_modal(n_clicks, sign_up, subscription_status):
    if ctx.triggered_id == "signup-button":
        return no_update, "/login"
    elif subscription_status and subscription_status.get("active"):
        return True, no_update
    else:
        return no_update, current_app.config["URL_EXPLORER"]


# Callback to close the modal
@callback(
    Output("confirmation-modal", "opened", allow_duplicate=True),
    [Input("close-modal-button", "n_clicks")],
    prevent_initial_call=True,
)
def close_modal(n_clicks):
    return False


# Callback to cancel the subscription
@callback(
    Output("confirmation-modal", "opened", allow_duplicate=True),
    Output("subscription-status", "data"),
    Output("paypal-store", "data", allow_duplicate=True),
    Output("page-location", "href"),
    [Input("confirm-cancel-button", "n_clicks")],
    prevent_initial_call=True,
)
def cancel_subscription(n_clicks, socket_id):
    if session.get("user"):
        user_id = session.get("user")["id"]
        payment_gateway = PaymentGateway()
        result = payment_gateway.cancel_subscription(user_id)
        if result["item"] is False:
            return (
                True,
                result,
                {
                    "scriptLoaded": True,
                    "clientId": current_app.config["PAYPAL_CLIENT_ID"],
                    "planId": current_app.config["PAYPAL_PLAN_ID"],
                },
                current_app.config["URL_PRICING"],
            )
    else:
        return no_update, no_update, current_app.config["URL_EXPLORER"]


@callback(
    Output("paypal-store", "data", allow_duplicate=True),
    Output("subscription-status", "data", allow_duplicate=True),
    [Input("interval-component", "n_intervals")],
    prevent_initial_call=True,
)
def load_paypal_script(n_intervals):
    if session.get("user"):
        user_id = session.get("user")["id"]
        subscription_service = SubscriptionService()
        result = subscription_service.has_active_subscription(user_id)
        if result["error"] is False:
            subscription_status = {"active": None, "subscription_id": None}
        else:
            subscription_status = {
                "active": result["item"]["has_active"],
                "subscription_id": result["item"]["subscription"]["subscription_id"],
            }
        return {
            "scriptLoaded": True,
            "clientId": current_app.config["PAYPAL_CLIENT_ID"],
            "planId": current_app.config["PAYPAL_PLAN_ID"],
        }, subscription_status
    else:
        return {
            "scriptLoaded": True,
            "clientId": current_app.config["PAYPAL_CLIENT_ID"],
            "planId": current_app.config["PAYPAL_PLAN_ID"],
        }, no_update


clientside_callback(
    """function(n_clicks) {
        console.log(n_clicks);
            if (n_clicks) {
                window.location.href = '/login';
            }
            return dash_clientside.no_update
""",
    Output("signup-button", "n_clicks"),
    Input("signup-button", "n_clicks"),
    prevent_initial_call=True,
)

clientside_callback(
    """
    function (storeData) {
        var scriptLoaded = storeData.scriptLoaded;
        var paypalClientId = storeData.clientId;
        var paypalPlanId = storeData.planId;
        
        console.log("Script Loaded: ", scriptLoaded);
        console.log("PayPal Client ID: ", paypalClientId);
        console.log("PayPal Plan ID: ", paypalPlanId);
        
        if (!scriptLoaded || !paypalClientId) {
            console.log("Script not loaded or PayPal Client ID missing");
            return window.dash_clientside.no_update;
        }
        if (document.querySelector("[id^='zoid-paypal-buttons-uid_']")) {
            console.log("PayPal button already rendered");
            return window.dash_clientside.no_update;
        }
        if (document.getElementById('paypal-sdk')) {
            // Script already exists, just render the button
            console.log("PayPal SDK script already exists, rendering button...");
            renderPayPalButton();
            return window.dash_clientside.no_update;
        }
        // Create the PayPal script element
        var script = document.createElement('script');
        script.id = 'paypal-sdk';
        script.src = 'https://www.paypal.com/sdk/js?client-id=' + paypalClientId + '&components=buttons&currency=USD&vault=true&intent=subscription';
        script.onload = function () {
            console.log("PayPal SDK script loaded, rendering button...");
            renderPayPalButton(paypalClientId, paypalPlanId);
        };
        // Append the script to the body
        document.body.appendChild(script);
        function renderPayPalButton(clientID, planID) {
            console.log("Rendering PayPal button with Client ID:", clientID, "and Plan ID:", planID);
            paypal.Buttons({
                fundingSource: paypal.FUNDING.PAYPAL,
                style: {
                    layout: 'vertical',
                    color: 'gold',
                    shape: 'rect',
                    label: 'paypal',
                    tagline: false
                },
                createSubscription: function(data, actions) {
                    console.log("Creating subscription with Plan ID:", planID);
                    return actions.subscription.create({
                        'plan_id': planID
                    });
                },
                onApprove: function(data, actions) {
                    console.log("Subscription approved with data:", data);
                    return actions.subscription.get().then(function(details) {
                        console.log("Subscription details:", details);
                        // Send subscription details to server
                        fetch('/save-subscription', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                subscriptionID: data.subscriptionID,
                                details: details
                            })
                        }).then(function(response) {
                            console.log("Server response:", response);
                            return response.json();
                        }).then(function(data) {
                            console.log("Response data:", data);
                        });
                    });
                }
            }).render('#paypal-button-container');
        }
    }
    """,
    Output("paypal-button-container", "children"),
    Input("paypal-store", "data"),
    prevent_initial_call=True,
)


# email: info@pure-inference.com : JA2j@uWq
# This is the sandbox application
# Link: https://sandbox.paypal.com
# Email: sb-17qmz31300247@business.example.com : xw{-?U3&
