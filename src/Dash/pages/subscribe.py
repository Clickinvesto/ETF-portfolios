import dash_mantine_components as dmc
import json
import uuid
from dash_credit_cards import DashCreditCards, DashParallaxTilt, DashCreditCardInput
from dash import (
    register_page,
    html,
    dcc,
    callback,
    Input,
    Output,
    State,
    ctx,
    no_update,
    MATCH,
    Patch,
    clientside_callback,
)
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify
from src.Dash.services.database import OpenPay
from src.Dash.utils.functions import get_countries
from flask import session, current_app
from src.Dash.services.NotificationProvider import NotificationProvider
from src.Dash.model.subscribe_form import sub_form, SubscribeData
from dash_pydantic_form import FormSection, ModelForm, Sections, fields, ids
from pydantic import BaseModel, Field, ValidationError

notify = NotificationProvider()
api = OpenPay()

register_page(__name__, name="Pricing", path=current_app.config["URL_SUBSCRIBTION"])


def layout(socket_ids=None, **kwargs):
    if socket_ids == None:
        raise PreventUpdate

    return full_layout(user=session.get("user"))


def full_layout(user=False):
    return dmc.Container(
        [
            dmc.Text(
                "You choose a silver plan for 7 USD", fw=700, size="lg", ta="center"
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
                        label="First Name",
                        style={"width": 200},
                        required=True,
                    ),
                    dmc.TextInput(
                        id="last_name_form",
                        label="Last Name",
                        style={"width": 200},
                        required=True,
                    ),
                ],
                justify="center",
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
                        id="city",
                        label="City",
                        style={"width": "200"},
                        required=True,
                    ),
                    dmc.Select(
                        label="Country",
                        placeholder="Select your country",
                        id="country_code",
                        searchable=True,
                        data=get_countries(dict_output=True),
                        style={"width": 200},
                        required=True,
                    ),
                    dmc.TextInput(
                        label="Postal Code",
                        id="postal_code",
                        style={"width": "200"},
                        required=True,
                    ),
                    dmc.TextInput(
                        id="line1",
                        label="Street, House number",
                        style={"width": "200"},
                        required=True,
                    ),
                    dmc.TextInput(
                        id="line2", label="Address line 2", style={"width": "200"}
                    ),
                    dmc.TextInput(
                        id="line3", label="Address line 3", style={"width": "200"}
                    ),
                    dmc.TextInput(
                        id="state", label="State", style={"width": "200"}, required=True
                    ),
                ],
                justify="center",
            ),
            dmc.Space(h=10),
            # html.P(id="error_element", style={"color": "red"}),
            dmc.Space(h=5),
            dmc.Group(
                [
                    dmc.Button("Clear", color="red", id="clear"),
                    dmc.Space(w=10),
                    dmc.Button("Subscribe", color="green", id="make_subscription"),
                ],
                justify="center",
            ),
        ],
        style={"width": "60%"},
        fluid=True,
    )


"""
@callback(
    Output("output", "children"),
    Input("make_subscription", "n_clicks"),
    Input(ModelForm.ids.form("subscription_data", "subscription_form"), "data-submit"),
    State(ModelForm.ids.main("subscription_data", "subscription_form"), "data"),
)
def check_form(_trigger: int, _trigger2: int, form_data: dict):
    print(form_data)
    try:
        SubscribeData.model_validate(form_data)
    except ValidationError as exc:
        return [
            dmc.Text("Validation errors", fw=500, c="red"),
            dmc.List(
                [
                    dmc.ListItem(
                        [
                            ".".join([str(x) for x in error["loc"]]),
                            f" : {error['msg']}, got {error['input']}",
                        ],
                    )
                    for error in exc.errors()
                ],
                size="sm",
                c="red",
            ),
        ]

    return ""
"""


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
    State("dash_websocket", "socketId"),
    prevent_initial_call=True,
)
def update_credit_card(first_name, last_name, card_input, expiry, cvc, socketid):
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
    State("dash_websocket", "socketId"),
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
    socket_id,
):
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
            notify.send_socket(
                to=socket_id,
                type="error",
                title="Wrong input",
                message="Please check your input",
            )
            return (
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
                no_update,
            )

        user_session = session["user"]
        openpay_id = user_session.get("openpay_id", "")
        api.fetch_customer(openpay_id)
        notification_id = uuid.uuid4().hex
        notify.send_socket(
            to=socket_id,
            type="start_process",
            title="Creating subscription",
            message="We check the credit card and add the subscription. Please wait a moment.",
            id=notification_id,
        )
        subscription, api_error = api.create_customer_subscription(
            api.customer,
            first_name,
            last_name,
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
        if api_error is None:
            notify.send_socket(
                to=socket_id,
                type="error_process",
                title="Something wrong at the API",
                message="We could not process your request. Check the credit card and try again.",
                id=notification_id,
            )
            return (
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
                no_update,
            )
        # All api calls are successful
        if subscription is not None:
            notify.send_socket(
                to=socket_id,
                type="success_process",
                title="Success",
                message="Thank you for subscribing to our service!",
                id=notification_id,
            )
            return (
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
            )
    elif button_id == "clear":
            return (
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
            )

        #


clientside_callback(
    """(notification) => {
        if (!notification) return dash_clientside.no_update
        return notification
    }""",
    Output("notify_container", "children", allow_duplicate=True),
    Input("dash_websocket", "data-notification"),
    prevent_initial_call=True,
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
