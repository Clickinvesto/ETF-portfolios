import os
from .mixins.DatabaseMixin import DatabaseMixin
from flask import current_app, session
from datetime import datetime, timezone

db = current_app.db
openpay = current_app.Openpay


class OpenPay(DatabaseMixin):
    def update_user_subscription(self, subscription, email):

        update_user_query = """UPDATE users
            SET subscription = :subscription
            WHERE email = :email
            """
        self.execute_query(
            update_user_query, {"subscription": subscription, "email": email}
        )
        user = session["user"]
        user["subscription"] = subscription
        session["user"] = user

    def update_user_openpay_id(self, customer_id, email):
        update_user_query = """UPDATE users
            SET openpay_id = :id
            WHERE email = :email
            """
        result = self.execute_query(
            update_user_query, {"id": customer_id, "email": email}
        )

    def create_card(
        self,
        customer,
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
        try:
            card = customer.cards.create(
                card_number=card_number.replace(" ", ""),
                holder_name=f"{first_name} {last_name}",
                expiration_year=int(expiry.split("/")[1]),
                expiration_month=int(expiry.split("/")[0]),
                cvv2=cvc,
                address={
                    "city": city,
                    "country_code": country_code,
                    "postal_code": postal_code,
                    "line1": line1,
                    "line2": line2,
                    "line3": line3,
                    "state": state,
                },
            )
            # print(card)     # print newly created card details
            print("Card created successfully! Card ID:", card.id)
            return card, None
        except openpay.OpenpayError as e:
            error_message = str(e)
            print(error_message)
            return None, "Error: Unable to create card. Check console for more details"

    def insert_card_details(self, card_id, customer_id, card_number):
        insert_card_query = """
            INSERT INTO cards (card_id, customer_id, card_number)
            VALUES (:card_id, :customer_id, :card_number)
        """
        result = self.execute_query(
            insert_card_query,
            {
                "card_id": card_id,
                "customer_id": customer_id,
                "card_number": card_number,
            },
        )

    @staticmethod
    def create_subscription(customer, card_id):
        try:
            subscription = customer.subscriptions.create(
                plan_id=os.getenv("OPENPAY_MONTHLY_PLAN_ID"),
                trial_days=os.getenv("OPENPAY_MONTHLY_PLAN_DURATION"),
                card_id=card_id,
            )
            # print(subscription)        # print subscription details
            print(
                "Subscription created successfully! Subscription ID:", subscription.id
            )
            return subscription, None
        except openpay.OpenpayError as e:
            error_message = str(e)
            print(error_message)
            return (
                None,
                "Error: Unable to create subscription. Check console for more details",
            )

    def insert_purchase_details(self, subscription_id, customer_id, card_id):
        insert_purchase_query = """
                INSERT INTO purchases (subscription_id, customer_id, card_id, plan_id, purchase_date)
                VALUES (:subscription_id, :customer_id, :card_id, :plan_id, :purchase_date)
            """

        self.execute_query(
            insert_purchase_query,
            {
                "subscription_id": subscription_id,
                "customer_id": customer_id,
                "card_id": card_id,
                "plan_id": os.getenv("OPENPAY_MONTHLY_PLAN_ID"),
                "purchase_date": datetime.now(timezone.utc),
            },
        )

    @staticmethod
    def create_customer(
        first_name,
        last_name,
        email,
        department,
        city,
        country_code,
        postal_code,
        line1,
        line2="",
        line3="",
    ):
        try:
            customer = openpay.Customer.create(
                name=first_name,
                last_name=last_name,
                email=email,
                customer_address={
                    "department": department,
                    "city": city,
                    "additional": f"{line1} {line2} {line3} {postal_code} {country_code}",
                },
            )
            # print(customer)     # print newly created customer details
            print("Customer created successfully! Openpay Customer ID: ", customer.id)
            return customer, None
        except openpay.OpenpayError as e:
            error_message = str(e)
            print(error_message)
            return (
                None,
                "Error: Unable to create customer. Check console for more details.",
            )

    def create_customer_subscription(
        self,
        first_name,
        last_name,
        email,
        department,
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
        customer, customer_api_error = self.create_customer(
            first_name,
            last_name,
            email,
            department,
            city,
            country_code,
            postal_code,
            line1,
            line2,
            line3,
        )
        if customer is None:
            return None, None, customer_api_error

        self.update_user_openpay_id(customer.id, email)

        card, card_api_error = self.create_card(
            customer,
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
        )
        if card is None:
            return customer, None, customer_api_error

        self.insert_card_details(card.id, customer.id, card_number)

        subscription, subscription_api_error = self.create_subscription(
            customer, card.id
        )
        if subscription is None:
            return customer, None, subscription_api_error
        self.update_user_subscription("Silver", email)
        self.insert_purchase_details(subscription.id, customer.id, card.id)

        return customer, subscription, None
