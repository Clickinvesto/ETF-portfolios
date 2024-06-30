import os

import logging
from ..mixins.DatabaseMixin import DatabaseMixin
from flask import current_app, session
from datetime import datetime, timezone

db = current_app.db
# openpay = current_app.Openpay
openpay = None


class PaymentGatway(DatabaseMixin):

    def fetch_customer(self, openpay_id):
        try:
            self.customer = openpay.Customer.retrieve(openpay_id)
            return {"item": self.customer, "error": False}
        except openpay.error.OpenpayError as e:
            logging.error(e)
            return {"item": False, "error": "Error fetching subscription details"}

    def update_user_subscription(self, subscription, email):
        try:
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
            return {"item": False, "error": False}
        except Exception as e:
            logging.error(e)
            return {"item": False, "error": "Failed to update user subscription"}

    def update_user_openpay_id(self, customer_id, email):
        try:
            update_user_query = """UPDATE users
                SET openpay_id = :id
                WHERE email = :email
                """
            result = self.execute_query(
                update_user_query, {"id": customer_id, "email": email}
            )
            return {"item": False, "error": False}
        except Exception as e:
            logging.error(e)
            return {"item": False, "error": "Failed to update open pay id in database"}

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
            print(card)
            return {"item": card, "error": False}
        except openpay.OpenpayError as e:
            error_message = str(e)
            logging.error(e)
            return {
                "item": card,
                "error": "Unable to create card. Are the details correct?",
            }

    def insert_card_details(self, card_id, customer_id, card_number):
        try:
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
            return {"item": False, "error": False}
        except Exception as e:
            logging.error(e)
            return {"item": False, "error": "Unable to add card to database"}

    @staticmethod
    def create_subscription(customer, card_id):
        try:
            subscription = customer.subscriptions.create(
                plan_id=os.getenv("OPENPAY_MONTHLY_PLAN_ID"),
                trial_days=os.getenv("OPENPAY_MONTHLY_PLAN_DURATION"),
                card_id=card_id,
            )

            return {"item": subscription, "error": False}
        except openpay.OpenpayError as e:
            error_message = str(e)
            return {
                "item": False,
                "error": "Something went wrong while creating the subscription.",
            }

    def insert_purchase_details(self, subscription_id, customer_id, card_id):
        try:
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
            return {"item": False, "error": False}
        except Exception as e:
            logging.error(e)
            return {
                "item": False,
                "error": "Could not insert subscription into database",
            }

    def create_openpay_customer(self, email):
        try:
            customer = openpay.Customer.create(
                name="None",
                last_name="",
                email=email,
                customer_address={
                    "department": "None",
                    "city": "None",
                    # "country_code": "CO"
                },
            )
            self.update_user_openpay_id(customer.id, email)

            return {"item": customer, "error": False}
        except openpay.OpenpayError as e:
            error_message = str(e)
            logging.error(e)
            return {
                "item": False,
                "error": "Something went wrong when creating your customer. Please try again.",
            }

    def create_customer_subscription(
        self,
        customer,
        first_name,
        last_name,
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
        result = self.create_card(
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

        if result["error"] is None:
            return {"item": False, "error": result["error"]}
        card = result["item"]
        self.insert_card_details(card.id, customer.id, card_number)

        result = self.create_subscription(customer, card.id)
        if result["error"] is None:
            return {"item": False, "error": result["error"]}
        subscription = result["item"]

        result = self.update_user_subscription("Silver", customer["email"])
        result = self.insert_purchase_details(subscription.id, customer.id, card.id)

        return {"item": subscription, "error": False}

    def fetch_active_subscription(self, openpay_id):
        try:
            customer = openpay.Customer.retrieve(openpay_id)
            subscription = customer.subscriptions.all()["data"][0]
            return {
                "item": subscription,
                "error": False,
            }

        except:
            return {
                "item": False,
                "error": "Error when retriving subscription",
            }

    def fetch_subscription_and_plan(self, openpay_id):
        """"""
        try:
            customer = openpay.Customer.retrieve(openpay_id)
            subscription = customer.subscriptions.all()["data"][0]
            if subscription.get("status") == "active":
                active_subscription = subscription

            if active_subscription:
                plan = openpay.Plan.retrieve(active_subscription["plan_id"])
                return {"item": [active_subscription, plan], "error": False}

            else:
                return {
                    "item": [False, False],
                    "error": "No active subscriptions found.",
                }

        except openpay.error.OpenpayError as e:
            logging.error(e)
            return {
                "item": [False, False],
                "error": "Error fetching subscription details",
            }

    # @staticmethod
    def fetch_credit_cards(self, openpay_id):
        try:
            customer = openpay.Customer.retrieve(openpay_id)
            cards = customer.cards.all()
            return {"item": cards["data"], "error": False}

        except openpay.error.OpenpayError as e:
            logging.error(e)
            return {"item": False, "error": "Error fetching subscription details"}

    def delete_card_and_purchases_from_db(self, card_id):
        try:
            delete_purchases_query = (
                """DELETE FROM purchases WHERE card_id = :card_id"""
            )
            result = self.execute_query(delete_purchases_query, {"card_id": card_id})
            delete_card_query = """DELETE FROM cards WHERE card_id = :card_id"""
            result = self.execute_query(delete_card_query, {"card_id": card_id})
            return {"item": False, "error": False}
        except Exception as e:
            logging.error(e)
            return {
                "item": False,
                "error": "Error deleting card and purchases from database",
            }

    def delete_card_from_openpay(self, customer_id, card_id):
        try:
            customer = openpay.Customer.retrieve(customer_id)
            card = customer.cards.retrieve(card_id)
            card.delete()
            # Delete card and purchases from the database
            if not self.delete_card_and_purchases_from_db(card_id):
                raise Exception(
                    "Failed to delete card and purchases from the database."
                )
            return {"item": False, "error": False}
        except Exception as e:
            logging.error(e)
            return {"item": False, "error": "Error deleting card from OpenPa"}

    def delete_user(
        self,
        email=None,
        openpay_id=None,
        delete_user=False,
        delete_cards=False,
        delete_purchases=False,
    ):
        if not any([delete_user, delete_cards, delete_purchases]):
            return {"item": False, "error": "No deletion action specified."}
        try:
            if delete_user and email:
                # Remove user from the users table
                delete_user_query = """DELETE FROM users WHERE email = :email"""
                result = self.execute_query(delete_user_query, {"email": email})

            if delete_cards and openpay_id:
                # Remove cards for that specific customer
                delete_cards_query = (
                    """DELETE FROM cards WHERE customer_id = :customer_id"""
                )
                result = self.execute_query(
                    delete_cards_query, {"customer_id": openpay_id}
                )

            if delete_purchases and openpay_id:
                # Remove purchases for that specific customer
                delete_purchases_query = (
                    """DELETE FROM purchases WHERE customer_id = :customer_id"""
                )
                result = self.execute_query(
                    delete_purchases_query, {"customer_id": openpay_id}
                )

            return {"item": False, "error": False}
        except Exception as e:
            logging.error(e)
            return {"item": False, "error": "Error deleting user details"}

    @staticmethod
    def delete_account_from_openpay(customer_id):
        try:
            customer = openpay.Customer.retrieve(customer_id)
            subscriptions = customer.subscriptions.all()
            for subscription in subscriptions["data"]:
                if subscription["status"] == "active":
                    subscription.delete()
            cards = customer.cards.all()
            for card in cards["data"]:
                card.delete()

            # Delete the customer account itself
            # openpay.Customer.delete(customer_id)
            return {"item": False, "error": False}
        except openpay.error.OpenpayError as e:
            logging.error(e)
            return {"item": False, "error": "Error deleting account from OpenPay"}

    def delete_subscription(self, user):
        customer_id = user.get("openpay_id", "")
        email = user.get("email", "")
        try:
            customer = openpay.Customer.retrieve(customer_id)
            subscription = customer.subscriptions.all()["data"][0]
            subscription.cancel_at_period_end = True
            subscription.save()
            return {"item": subscription, "error": False}
        except:
            return {
                "item": False,
                "error": "Error deleting subscription from the database",
            }
