from datetime import datetime
from flask import current_app
from src.models import PaypalSubscription
from . import PaymentGateway
from ..mixins.DatabaseMixin import DatabaseMixin

db = current_app.db


class SubscriptionService(DatabaseMixin):

    def has_active_subscription(self, user_id):
        subscriptions = PaypalSubscription.query.filter_by(user_id=user_id).all()
        for subscription in subscriptions:
            if subscription.status == 'ACTIVE':
                return {
                    "item": {
                        "has_active": True,
                        "subscription": PaymentGateway.PaymentGateway.subscription_to_dict(subscription),
                    },
                    "error": None
                }
        return {
            "item": {
                "has_active": False,
                "subscription": None,
            },
            "error": False
        }

    # def get_user_subscription_status(self, user_id):
    #     result = self.get_latest_user_subscription(user_id)
    #     if result["item"]:
    #         subscription_status = result["item"].status
    #         plan_id = result["item"].plan_id
    #         return {
    #             "item": {
    #                 "has_subscription": True,
    #                 "status": subscription_status,
    #                 "plan_id": plan_id
    #             },
    #             "error": False,
    #         }
    #     return {
    #             "item": {
    #                 "has_subscription": False,
    #                 "status": None,
    #                 "plan_name": None
    #             },
    #             "error": False,
    #         }

    @staticmethod
    def get_latest_user_subscription(user_id):
        try:
            # Get the latest subscription for the user, ordered by creation date
            subscription = PaypalSubscription.query.filter_by(user_id=user_id).order_by(
                PaypalSubscription.start_date.desc()).first()
            if subscription:
                return {
                    "item": subscription,
                    "error": False,
                }
            else:
                return {
                    "item": None,
                    "error": "No subscription found for the user",
                }
        except Exception as e:
            return {
                "item": None,
                "error": f"Error retrieving subscription: {str(e)}",
            }

    @staticmethod
    def save_subscription(user_id, subscription_id, details):
        start_date = datetime.strptime(details['start_time'], '%Y-%m-%dT%H:%M:%SZ')
        next_billing_date = datetime.strptime(details['billing_info']['next_billing_time'], '%Y-%m-%dT%H:%M:%SZ')

        new_subscription = PaypalSubscription(
            user_id=user_id,
            subscription_id=subscription_id,
            plan_id=details['plan_id'],
            status=details['status'],
            start_date=start_date,
            next_billing_date=next_billing_date
        )
        db.session.add(new_subscription)
        db.session.commit()
        return new_subscription

    @staticmethod
    def is_trial_period_over(billing_info):
        trial_tenure = next(
            (cycle for cycle in billing_info.get('cycle_executions', []) if cycle.get('tenure_type') == 'TRIAL'), None)
        if not trial_tenure:
            return False

        if trial_tenure.get('cycles_remaining') == 0 and trial_tenure.get('cycles_completed') == trial_tenure.get(
                'total_cycles'):
            return True
        return False
