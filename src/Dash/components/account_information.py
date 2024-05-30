import dash_credit_cards as dcs
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify


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
