import dash_credit_cards as dcs
import dash_mantine_components as dmc
from dash import dcc, html
from dash_iconify import DashIconify
from src.Dash.services.API.PaymentGateway import PaymentGateway
from src.Dash.services.API.SubscriptionService import SubscriptionService
from src.models import PaypalPlans

subscription_service = SubscriptionService()
payment_gateway = PaymentGateway()


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


def create_paypal_subscription_paper(user_id):
    subscription_data = subscription_service.get_latest_user_subscription(user_id)
    subscription = subscription_data["item"]
    error = subscription_data["error"]

    if error:
        return html.Div(
            children=[
                dmc.Text(
                    "Subscription Plan:",
                    size="lg",
                    style={
                        "textDecoration": "underline",
                        "fontWeight": 500,
                    },
                ),
                dmc.Space(h=10),
                dmc.Text(
                    "No subscription found.",
                    size="lg",
                ),
            ],
            style={"radius": "md", "margin": "10px"},
        )

    subscription_details = payment_gateway.fetch_subscription(
        subscription.subscription_id
    )
    if subscription_details["error"]:
        return html.Div(
            children=[
                dmc.Text(
                    "Subscription Plan:",
                    size="lg",
                    style={
                        "textDecoration": "underline",
                        "fontWeight": 500,
                    },
                ),
                dmc.Space(h=10),
                dmc.Text(
                    f"Error fetching subscription: {subscription_details['error']}",
                    size="lg",
                ),
            ],
            style={"radius": "md", "margin": "10px"},
        )

    details = subscription_details["item"]
    plan_id = details["plan_id"]
    plan = PaypalPlans.query.filter_by(plan_id=plan_id).first()
    trial_period = subscription_service.is_trial_period_over(details["billing_info"])
    trial_badge = (
        dmc.Badge("Trial", color="red", style={"cursor": "default"})
        if trial_period
        else None
    )
    return html.Div(
        children=[
            dcc.Store(id="subscription-id", data=details["id"]),
            dcc.Store(id="cancel-subscription-response"),
            dmc.NotificationProvider(id="cancel-subscription-notification"),
            dmc.Text(
                "Subscription Plan:",
                size="lg",
                style={
                    "textDecoration": "underline",
                    "fontWeight": 500,
                },
            ),
            dmc.Space(h=10),
            dmc.Group(
                [
                    dmc.Group(
                        [
                            dmc.Text(f"{plan.name} Plan", fw=400),
                            # dmc.Text(f"({plan_id})", size="sm", c="dimmed"),
                        ]
                    ),
                    dmc.Group(
                        [
                            trial_badge if trial_badge else None,
                            dmc.Badge(
                                (
                                    "Active"
                                    if subscription.status == "ACTIVE"
                                    else "Expired"
                                ),
                                color=(
                                    "green"
                                    if subscription.status == "ACTIVE"
                                    else "red"
                                ),
                                style={"cursor": "default"},
                            ),
                        ],
                        justify="space-between",
                        style={
                            "display": "flex",
                        },
                    ),
                ],
                justify="space-between",
                style={
                    "display": "flex",
                    "marginTop": "md",
                    "marginBottom": "xs",
                },
            ),
            dmc.Space(h=5),
            dmc.Text(
                plan.description or "No description available.",
                size="sm",
                c="dimmed",
            ),
            dmc.Group(
                [
                    dmc.Text(f"Payment Date: ", size="sm"),
                    dmc.Text(
                        f"{subscription.start_date.strftime('%Y-%m-%d')}",
                        c="blue" if subscription.status == "ACTIVE" else "red",
                        size="sm",
                    ),
                ],
                style={
                    "direction": "column",
                    "align": "flex-start",
                    "spacing": "xs",
                    "marginTop": "md",
                },
            ),
            dmc.Group(
                [
                    dmc.Text(f"Active till date: ", size="sm"),
                    dmc.Text(
                        f"{subscription.next_billing_date.strftime('%Y-%m-%d') if subscription.next_billing_date else 'N/A'}",
                        c="blue" if subscription.status == "ACTIVE" else "red",
                        size="sm",
                    ),
                ],
                style={
                    "direction": "column",
                    "align": "flex-start",
                    "spacing": "xs",
                    "marginTop": "md",
                },
            ),
            dmc.Group(
                [
                    dmc.Button(
                        "Cancel Subscription",
                        leftSection=DashIconify(icon="radix-icons:cross-1"),
                        color="blue",
                        size="xs",
                        disabled=False if subscription.status == "ACTIVE" else True,
                        id="cancel-subscription-btn",
                        style={"marginTop": "md", "radius": "md"},
                    ),
                ],
                style={
                    "display": "flex",
                    "direction": "row",
                    "justify-content": "flex-end",
                },
            ),
        ],
        style={"radius": "md", "margin": "10px"},
    )
