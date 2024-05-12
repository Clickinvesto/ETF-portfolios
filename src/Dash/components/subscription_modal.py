import dash_mantine_components as dmc
from dash_credit_cards import DashCreditCards, DashParallaxTilt, DashCreditCardInput
from dash import html, callback, Input, State, Output, ctx, no_update, callback_context
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify
from src.Dash.services.database import OpenPay
from flask import session

api = OpenPay()


sub_modal = dmc.Modal(
    id="subscription_modal",
    centered=True,
    zIndex=10000,
    size="55%",
    children=dmc.Container(
        [
            dmc.Group(
                [
                    dmc.Text(id="plan_text", weight=700, size="lg"),
                ],
                position="center",
            ),
            dmc.Space(h=15),
            DashParallaxTilt(
                id="input",
                children=[
                    DashCreditCards(
                        id="credit_card",
                        name="",
                        number="",
                        expiry="",
                        cvc="",
                        focused="",
                        preview=True,
                        issuer="visa",
                        locale={"valid": "VALID THRU"},
                    )
                ],
                tiltReverse=True,
                glareEnable=True,
                glareMaxOpacity=0.8,
                glareColor="#ffffff",
                glareBorderRadius="20px",
                glarePosition="bottom",
                glareReverse=True,
            ),
            dmc.Space(h=10),
            dmc.Group(
                [
                    dmc.TextInput(
                        id="first_name_form",
                        # label="First Name",
                        style={"width": 200},
                        placeholder="Your First Name",
                    ),
                    dmc.TextInput(
                        id="last_name_form",
                        # label="Last Name",
                        style={"width": 200},
                        placeholder="Your Last Name",
                    ),
                ],
                position="center",
            ),
            dmc.Space(h=10),
            html.Center(
                DashCreditCardInput(
                    id="credit_card_input",
                    cardNumber="",
                    cvc="",
                    expiry="",
                    cardNumberInputProps={"value": ""},
                    cardExpiryInputProps={"value": ""},
                    cardCVCInputProps={"value": ""},
                    fieldClassName="input",
                )
            ),
            dmc.Space(h=10),
            dmc.Group(
                [
                    dmc.TextInput(
                        id="city", placeholder="City", style={"width": "200"}
                    ),
                    dmc.TextInput(
                        id="country_code",
                        placeholder="Your Country",
                        style={"width": "200"},
                    ),
                    dmc.TextInput(
                        id="postal_code",
                        placeholder="Your Country",
                        style={"width": "200"},
                    ),
                    dmc.TextInput(
                        id="line1", placeholder="Address line 1", style={"width": "200"}
                    ),
                    dmc.TextInput(
                        id="line2", placeholder="Address line 2", style={"width": "200"}
                    ),
                    dmc.TextInput(
                        id="line3", placeholder="Address line 3", style={"width": "200"}
                    ),
                    dmc.TextInput(
                        id="state", placeholder="Your State", style={"width": "200"}
                    ),
                ],
                position="center",
            ),
            dmc.Space(h=10),
            html.P(id="error_element", style={"color": "red"}),
            dmc.Space(h=5),
            dmc.Group(
                [
                    dmc.Button("Clear", color="red", id="clear"),
                    dmc.Space(w=10),
                    dmc.Button("Subscribe", color="green", id="make_subscription"),
                ],
                position="center",
            ),
        ],
        style={"width": "60%"},
        fluid=True,
    ),
)


@callback(
    Output("credit_card", "name", allow_duplicate=True),
    Output("credit_card", "number", allow_duplicate=True),
    Output("credit_card", "expiry", allow_duplicate=True),
    Output("credit_card", "cvc", allow_duplicate=True),
    Output("credit_card", "issuer", allow_duplicate=True),
    Output("credit_card", "focused", allow_duplicate=True),
    Input("first_name_form", "value"),
    Input("last_name_form", "value"),
    Input("credit_card_input", "cardNumber"),
    Input("credit_card_input", "expiry"),
    Input("credit_card_input", "cvc"),
    prevent_initial_call=True,
)
def update_credit_card(first_name, last_name, card_input, expiry, cvc):
    if not any([card_input, expiry, cvc, first_name, last_name]):
        return no_update
    # Remove spaces and slash from expiry
    expiry = expiry.replace(" ", "").replace("/", "")

    first_digit = card_input[0] if card_input else ""
    if first_digit == "2" or first_digit == "5":
        issuer = "mastercard"
    elif first_digit == "4":
        issuer = "visa"
    elif first_digit == "3":
        issuer = "amex"
    elif first_digit == "6":
        issuer = "discover"
    else:
        issuer = ""

    # print(expiry, cvc)
    ctx = callback_context
    triggered_component = ctx.triggered[0]["prop_id"].split(".")[0]

    input_focus = None
    if triggered_component == "credit_card_input":
        input_field = ctx.triggered[0]["prop_id"].split(".")[1]
        if input_field == "cvc":
            input_focus = "cvc"
        else:
            input_focus = "name"

    name = f"{first_name} {last_name}"
    return name, card_input, expiry, cvc, issuer, input_focus


@callback(
    Output("subscription_modal", "opened"),
    Output("error_element", "children"),
    Output("first_name_form", "value"),
    Output("last_name_form", "value"),
    Output("credit_card_input", "cardNumber"),
    Output("credit_card_input", "expiry"),
    Output("credit_card_input", "cvc"),
    Output("credit_card", "name"),
    Output("credit_card", "number"),
    Output("credit_card", "expiry"),
    Output("credit_card", "cvc"),
    Output("credit_card", "focused"),
    Output("credit_card", "issuer"),
    Output("city", "value"),
    Output("country_code", "value"),
    Output("postal_code", "value"),
    Output("line1", "value"),
    Output("line2", "value"),
    Output("line3", "value"),
    Output("state", "value"),
    Output("notify_container", "children"),
    Input("make_subscription", "n_clicks"),
    Input("clear", "n_clicks"),
    State("first_name_form", "value"),
    State("last_name_form", "value"),
    State("credit_card_input", "cardNumber"),
    State("credit_card_input", "expiry"),
    State("credit_card_input", "cvc"),
    State("city", "value"),
    State("country_code", "value"),
    State("postal_code", "value"),
    State("line1", "value"),
    State("line2", "value"),
    State("line3", "value"),
    State("state", "value"),
    prevent_initial_call=True,
)
def update_output(
    submit_n_clicks,
    clear_n_clicks,
    first_name,
    last_name,
    card_number,
    expiry,
    cvc,
    city,
    country_code,
    postal_code,
    line1,
    line2,
    line3,
    state,
):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if button_id == "make_subscription":
        error_message = validate_input(
            first_name,
            last_name,
            card_number,
            expiry,
            cvc,
            city,
            country_code,
            postal_code,
            line1,
            state,
        )

        if error_message is not None:
            message = dmc.Notification(
                id="my-notification",
                title="Wrong input",
                message="Please check your input",
                color="red",
                action="show",
                autoClose=True,
                icon=DashIconify(icon="material-symbols-light:error-outline"),
            )
            # print("Error (Form validation): ", error_message)
            return (
                no_update,
                error_message,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                message,
            )

        user_session = session["user"]
        email = user_session.get("email", "")
        customer, subscription, api_error = api.create_customer_subscription(
            first_name,
            last_name,
            email,
            "None",
            card_number,
            expiry,
            cvc,
            city,
            country_code,
            postal_code,
            line1,
            line2,
            line3,
            state,
        )

        # an error occur while making an api calls
        if api_error is not None:
            message = dmc.Notification(
                id="my-notification",
                title="Something wrong at the API",
                message="We could not process your request. Pleas try again later",
                color="red",
                action="show",
                autoClose=True,
                icon=DashIconify(icon="material-symbols-light:error-outline"),
            )
            return (
                no_update,
                api_error,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                message,
            )
        # All api calls are successful
        if customer is not None and subscription is not None:
            message = dmc.Notification(
                id="my-notification",
                title="Success",
                message="Thank you for subscribing to our service!",
                color="green",
                action="show",
                autoClose=True,
                icon=DashIconify(icon="material-symbols-light:error-outline"),
            )
            return (
                False,
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                message,
            )
        elif button_id == "clear":
            return (
                True,
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                no_update,
            )


def validate_input(
    first_name,
    last_name,
    card_number,
    expiry,
    cvc,
    city,
    country_code,
    postal_code,
    line1,
    state,
):
    # check if all the fields are empty
    if not any(
        [
            first_name,
            last_name,
            card_number,
            expiry,
            cvc,
            city,
            country_code,
            postal_code,
            line1,
            state,
        ]
    ):
        return "All fields are required."
    # check each field individually
    if not first_name:
        return "First name is required."
    if not last_name:
        return "Last name is required."
    if not card_number:
        return "Card number is required."
    if not expiry:
        return "Expiry date is required."
    if not cvc:
        return "CVC code is required."
    if not city:
        return "City is required."
    if not country_code:
        return "Country code is required."
    elif len(country_code) != 2:
        return "Country code must be 2 characters."
    if not postal_code:
        return "Postal code is required."
    if not line1:
        return "Address line1 is required."
    if not state:
        return "State is required."

    # return None (no error and form is filled)
    return None
