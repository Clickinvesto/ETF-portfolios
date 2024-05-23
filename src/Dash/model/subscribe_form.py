import dash_mantine_components as dmc
from typing import Literal
from dash import Input, Output, State, callback, html
from dash_pydantic_form import ModelForm
from pydantic import BaseModel, Field, ValidationError, PaymentCardNumber
from src.Dash.utils.functions import get_countries
from dash_pydantic_form import FormSection, ModelForm, Sections, fields
from enum import Enum

email_regex = r"^\S+@\S+\.\S+$"

mapping, values = get_countries()


def create_enum_from_dict(name, dictionary):
    return Enum(name, dictionary)


Countries = create_enum_from_dict("Countries", values)


class Address(BaseModel):
    city: str = Field(placeholder="City")
    country: Countries = Field(placeholder="Country")
    postcode: str = Field(placeholder="Postcode")
    adress_line_1: str = Field(placeholder="Street")
    state: str = Field(placeholder="State")


class CreditCard(BaseModel):
    card_number: str = Field(
        placeholder="Credit card number", min_length=12, max_length=19
    )
    expiry_date: str = Field(placeholder="MM / YY")
    ccv: str = Field(placeholder="xxx")


class SubscribeData(BaseModel):
    first_name: str = Field(placeholder="Your first name")
    last_name: str = Field(placeholder="Your last name")
    address: Address = Field(title="Address")


sub_form = ModelForm(
    SubscribeData,
    aio_id="subscription_data",
    form_id="subscription_form",
    fields_repr={
        # Using a dict will pass the arguments to the default field input
        "first_name": fields.Text(n_cols=1),
        "last_name": fields.Text(n_cols=1),
        "address": {
            "fields_repr": {
                "city": fields.Text(n_cols=1),
                "country": fields.Select(
                    required=False, options_labels=mapping, n_cols=1
                ),
                "postcode": fields.Text(n_cols=1),
                "adress_line_1": fields.Text(n_cols=1),
                "state": fields.Text(n_cols=1),
            },
            # You can also pass the field repr directly
        },
    },
)
