"""Data models."""

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from . import db
from datetime import datetime, timezone


class User(UserMixin, db.Model):
    """Data model for user accounts."""

    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), index=True, unique=True, nullable=False)
    password = db.Column(
        db.String(200), primary_key=False, unique=False, nullable=False
    )
    is_admin = db.Column(
        db.Boolean, index=False, unique=False, nullable=False, default=False
    )
    verified = db.Column(
        db.Boolean, index=False, unique=False, nullable=False, default=False
    )
    created = db.Column(db.DateTime, index=False, unique=False, nullable=False)
    last_login = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    subscription = db.Column(db.String(200))
    openpay_id = db.Column(db.String(200))
    data_consent = db.Column(db.Boolean, index=False, unique=False, nullable=False, default=False)

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)

    @staticmethod
    def create(
        email, password, is_admin, verified, date, subscription
    ):  # create new user
        new_user = User(
            email=email,
            is_admin=is_admin,
            verified=verified,
            created=date,
            subscription=subscription,
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

    def __repr__(self):
        return "<User {}>".format(self.email)


class Plan(db.Model):
    __tablename__ = "plans"
    id = db.Column(db.String(25), primary_key=True, nullable=False)
    name = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return "<Plan {}>".format(self.name)


class Card(db.Model):
    __tablename__ = "cards"
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.String(100), nullable=False)
    customer_id = db.Column(db.String(100), nullable=False)
    card_number = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return "<Card {}>".format(self.card_number)


class Purchases(db.Model):
    __tablename = "purchases"
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.String(25), nullable=False)
    customer_id = db.Column(db.String(200), nullable=False)
    card_id = db.Column(db.String(20), nullable=False)
    plan_id = db.Column(db.String(25), nullable=False)
    purchase_date = db.Column(
        db.DateTime, nullable=False, default=datetime.now(timezone.utc)
    )

    def __repr__(self):
        return "<Purchase {}>".format(self.id)


# Define a subscription model
class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    subscription_id = db.Column(db.String(100), nullable=False)
    plan_id = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    next_billing_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(100), nullable=False)


class PaypalPlans(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    interval_unit = db.Column(db.String(50), nullable=False)
    interval_count = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PaypalSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    subscription_id = db.Column(db.String(255), nullable=False)
    plan_id = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    next_billing_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<subscription_id: {self.subscription_id}:, plan_id: {self.plan_id}, status: {self.status}, start_date: {self.start_date}, next_billing_date: {self.next_billing_date} '
