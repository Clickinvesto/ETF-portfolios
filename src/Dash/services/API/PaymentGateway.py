import requests
from flask import current_app
from requests.auth import HTTPBasicAuth
from src.models import PaypalSubscription, User

db = current_app.db


class PaymentGateway:

    def __init__(self):
        self.base_url = current_app.config['PAYPAL_API_BASE_URL']
        self.client_id = current_app.config['PAYPAL_CLIENT_ID']
        self.client_secret = current_app.config['PAYPAL_CLIENT_SECRET']

    def get_access_token(self):
        url = f"{self.base_url}/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
        }
        data = {
            "grant_type": "client_credentials",
        }
        auth = HTTPBasicAuth(self.client_id, self.client_secret)
        response = requests.post(url, headers=headers, data=data, auth=auth)
        response.raise_for_status()
        return response.json()["access_token"]

    def fetch_subscription(self, subscription_id):
        try:
            access_token = self.get_access_token()
            url = f"{self.base_url}/v1/billing/subscriptions/{subscription_id}"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return {
                "item": response.json(),
                "error": False,
            }
        except Exception as e:
            return {
                "item": False,
                "error": str(e),
            }

    # def cancel_subscription(self, subscription_id):
    #     try:
    #         access_token = self.get_access_token()
    #         url = f"{self.base_url}/v1/billing/subscriptions/{subscription_id}/cancel"
    #         headers = {
    #             "Content-Type": "application/json",
    #             "Authorization": f"Bearer {access_token}"
    #         }
    #         data = {
    #             "reason": "User requested cancellation"
    #         }
    #         response = requests.post(url, headers=headers, json=data)
    #         if response.status_code == 204:
    #             return {
    #                 "item": "Subscription cancelled successfully",
    #                 "error": False
    #             }
    #         else:
    #             return {
    #                 "item": False,
    #                 "error": "Error cancelling subscription"
    #             }
    #     except Exception as e:
    #         return {
    #             "item": False,
    #             "error": str(e)
    #         }

    def cancel_subscription(self, user_id=None, subscription_id=None):
        try:
            if user_id:
                # Retrieve the user's active subscription
                subscription = PaypalSubscription.query.filter_by(user_id=user_id, status='ACTIVE').first()
                if not subscription:
                    return {
                        "item": False,
                        "error": "No active subscription found for the user"
                    }
                subscription_id = subscription.subscription_id
            elif subscription_id:
                # Retrieve the subscription by its ID
                subscription = PaypalSubscription.query.filter_by(subscription_id=subscription_id,
                                                                  status='ACTIVE').first()
                if not subscription:
                    return {
                        "item": False,
                        "error": "No active subscription found with the given ID"
                    }
            else:
                return {
                    "item": False,
                    "error": "Either user_id or subscription_id must be provided"
                }

            # Make a request to PayPal API to cancel the subscription
            access_token = self.get_access_token()
            url = f"{self.base_url}/v1/billing/subscriptions/{subscription_id}/cancel"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            data = {
                "reason": "User requested cancellation"
            }
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 204:
                # Update subscription status in the database
                subscription.status = 'CANCELLED'
                db.session.commit()

                # Update the user's subscription column to NULL
                user = User.query.filter_by(id=user_id).first()
                user.subscription = None
                db.session.commit()

                return {
                    "item": {
                        "message": "Subscription cancelled successfully",
                        "subscription": self.subscription_to_dict(subscription),
                    },
                    "error": False
                }
            else:
                return {
                    "item": False,
                    "error": "Error cancelling subscription"
                }
        except Exception as e:
            return {
                "item": False,
                "error": str(e)
            }

    @staticmethod
    def subscription_to_dict(subscription):
        return {
            "subscription_id": subscription.subscription_id,
            "plan_id": subscription.plan_id,
            "user_id": subscription.user_id,
            "status": subscription.status,
            "start_date": subscription.start_date.isoformat() if subscription.start_date else None,
            "next_billing_date": subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
        }

    def cancel_user_subscription(self, user_id):
        try:
            # Retrieve the user's active subscription
            subscription = PaypalSubscription.query.filter_by(user_id=user_id, status='ACTIVE').first()
            if not subscription:
                return {'status': 'error', 'message': 'No active subscription found'}

            # Make a request to PayPal API to cancel the subscription
            response = requests.post(
                f"{self.base_url}/v1/billing/subscriptions/{subscription.subscription_id}/cancel",
                headers={
                    "Authorization": f"Bearer {self.get_access_token()}",
                    "Content-Type": "application/json"
                },
                json={
                    "reason": "User requested cancellation"
                }
            )
            if response.status_code == 204:
                # Update subscription status in the database
                subscription.status = 'CANCELLED'
                db.session.commit()
                return {
                    "item": "Subscription cancelled successfully",
                    "error": False
                }
            else:
                return {
                    "item": False,
                    "error": "Failed to cancel subscription."
                }
        except Exception as e:
            print(f"Error cancelling subscription: {e}")
            return {
                "item": False,
                "error": str(e)
            }
