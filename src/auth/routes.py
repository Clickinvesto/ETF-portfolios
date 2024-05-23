import datetime
import jwt
import json
from flask import Blueprint, render_template
from flask import current_app
from flask import (
    Blueprint,
    redirect,
    render_template,
    flash,
    session,
    url_for,
    make_response,
    request,
    jsonify,
)
from flask_login import login_required, logout_user, current_user, login_user

from src import login_manager
from src.models import User, db
from .forms import LoginForm, SignupForm, ResetPasswordForm
from .. import mail
from src.Dash.services.database import OpenPay
from src.Dash.services.NotificationProvider import NotificationProvider

notify = NotificationProvider()
api = OpenPay()

# Register auth_bp as blueprint
auth_bp = Blueprint(
    "auth_bp", __name__, template_folder="templates", static_folder="application/static"
)


def flash_errors(form):
    """Flashes form errors"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(
                f"Error for {field} field: {error}",
                "warning",
            )


@login_manager.user_loader
def load_user(user_id):
    """Check if user is logged-in upon page load."""
    if user_id is not None:
        return User.query.get(user_id)
    return None


@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to Login page."""
    flash("You must be logged in to view that page.", category="warning")
    return redirect(url_for("auth_bp.login"))


@auth_bp.errorhandler(404)
def not_found():
    """Page not found."""
    return make_response(render_template("404.html"), 404)


@auth_bp.route(current_app.config["URL_BASE"], methods=["GET"])
def redirect_to_dash():
    return redirect(current_app.config["URL_EXPLORER"])


@auth_bp.route(current_app.config["URL_LOGIN"], methods=["GET", "POST"])
def login():
    # First we check if the user is already authenticated and directly bring him to the userPage
    # We need to get the right URL for that from the blueprints
    loginForm = LoginForm()

    if current_user.is_authenticated:
        # Log the new last login
        current_user.last_login = datetime.datetime.now()
        db.session.commit()
        # Bring the user to the page he wanted to after lgin
        if "url" in session:
            if session["url"]:
                url = session["url"]
                session["url"] = None
                return redirect(url)
        elif current_user.is_admin:
            return redirect(url_for("admin.index"))
        else:
            return redirect(current_app.config["URL_EXPLORER"])

    # After that we check the form and login the user or give a massage

    if loginForm.validate_on_submit():
        user = User.query.filter_by(email=loginForm.email.data).first()

        # First check if the user really exists
        if user is None:
            flash("This user does not exists. Please sign up.", category="warning")
            return redirect(url_for("auth_bp.login"))

        elif not user.check_password(password=loginForm.password.data):
            flash("The password is incorrect.", category="warning")
            return redirect(url_for("auth_bp.login"))

        elif not user.verified:
            flash(
                "Please check your inbox and validate the account.", category="warning"
            )
            return redirect(url_for("auth_bp.login"))

        is_admin = (
            User.query.with_entities(User.is_admin)
            .filter_by(email=loginForm.email.data)
            .first()
        )[0]
        # Check if the user is verified

        # Check the password of the user
        if user and user.check_password(password=loginForm.password.data):
            # Login User and store last login
            login_user(user)
            user.last_login = datetime.datetime.now()
            user_dict = {
                key: user.__dict__[key]
                for key in ["id", "email", "is_admin", "subscription", "openpay_id"]
            }
            db.session.commit()
            session["user"] = user_dict
            # Redirect the user to the right page, depending if admin or not
            if "url" in session:
                if session["url"]:
                    url = session["url"]
                    session["url"] = None
                    return redirect(url)
            if is_admin:
                # User is admin
                return redirect(url_for("admin.index"))

            if not is_admin:
                # User is not admin
                return redirect(current_app.config["URL_DASH"])

    return render_template(
        "login.jinja2",
        form=loginForm,
        title="Login",
        template="login-page",
    )


@auth_bp.route(current_app.config["URL_LOGOUT"])
@login_required
def logout():
    """User log-out logic."""
    logout_user()
    del session["user"]
    return redirect(url_for("auth_bp.login"))


@auth_bp.route(current_app.config["URL_SIGNUP"], methods=["GET", "POST"])
def signup():
    """
    User sign-up page.

    GET requests serve sign-up page.
    POST requests validate form & user creation.
    """
    form = SignupForm()
    if form.validate_on_submit():
        # Check if user exists if not, create
        existing_user = User.query.filter_by(email=form.email.data).first()
        flash("A user already exists with that email address.", category="warning")

        if existing_user is None:
            user = User(
                email=form.email.data,
                is_admin=form.is_admin.data,
                verified=False,
                created=datetime.datetime.now(),
            )
            user.set_password(form.password.data)

            # Send message for verification
            token = jwt.encode(
                {
                    "email_address": user.email,
                    "exp": datetime.datetime.now(tz=datetime.timezone.utc)
                           + datetime.timedelta(hours=current_app.config["TOKEN_EXPIRE"]),
                },
                current_app.config["SECRET_KEY"],
                algorithm="HS256",
            )
            try:
                mail.send(
                    subject="Please verify your email",
                    receivers=user.email,
                    html_template="verify.html",
                    body_params={"token": token, "user_name": user.email},
                )

                db.session.add(user)
                db.session.commit()
                # User is auto loged in, but we want hom to verify
                logout_user()
                flash(
                    "Your account was created and a verification email sent. Please check your inbox and spam folder",
                    category="success",
                )
            except Exception as e:
                current_app.logger.error(e, exc_info=True)
                current_app.logger.error(
                    f"HOST: {current_app.config['EMAIL_HOST']} and port: {current_app.config['EMAIL_PORT']}"
                )
                current_app.logger.error(
                    f"USERNAME: {current_app.config['EMAIL_USERNAME']}"
                )
                flash(
                    "There was a problem sending the confirmation email. Please try again later.",
                    category="warning",
                )
                print(e)

            return redirect(url_for("auth_bp.login"))

    else:
        flash_errors(form)

    return render_template(
        "signup.jinja2",
        title="Sign Up",
        form=form,
        template="signup-page",
        body="Sign up for a user account.",
    )


@auth_bp.route(current_app.config["URL_RESEND_VERIFY"], methods=["POST"])
def resent_email():
    existing_user = User.query.filter_by(email=request.form["email"]).first()
    if existing_user is not None:
        token = jwt.encode(
            {
                "email_address": existing_user.email,
                "exp": datetime.datetime.now(tz=datetime.timezone.utc)
                       + datetime.timedelta(hours=current_app.config["TOKEN_EXPIRE"]),
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )
        try:
            mail.send(
                subject="Please verify your email",
                receivers=existing_user.email,
                html_template="new_verify.html",
                body_params={"token": token, "user_name": existing_user.first_name},
            )
            flash(
                "Please check your inbox and spam folder. You should have a new Email for verification.",
                category="success",
            )
            return jsonify("Email sent")
        except Exception as e:
            current_app.logger.error(e, exc_info=True)
            current_app.logger.error(
                f"HOST: {current_app.config['EMAIL_HOST']}, port: {current_app.config['EMAIL_PORT']}, USERNAME: {current_app.config['EMAIL_USERNAME']}"
            )
            flash(
                "There was a problem sending the confirmation email. Please try again later.",
                category="warning",
            )
            jsonify("Problem with Emails")
            print(e)

    flash("There is no user with this Email", category="warning")
    return jsonify("This Email is not registered")


@auth_bp.route(current_app.config["URL_VERIFY_EMAIL"])
def verify_email(token):
    try:
        data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        email = data["email_address"]
        user = User.query.filter_by(email=email).first()
        if user:
            user.verified = True
            db.session.commit()

            # Create OpenPay customer
            openpay_customer, customer_api_error = api.create_openpay_customer(email)
            if customer_api_error:
                flash("Failed to create customer at OpenPay", category="danger")
            else:
                flash("You can log in now", category="success")
        return redirect(url_for("auth_bp.login"))

    except jwt.ExpiredSignatureError:
        flash("The link already expired", category="Warning")
        return redirect(url_for("auth_bp.login"))


@auth_bp.route(current_app.config["URL_RESET_PASSWORD"], methods=["POST"])
def reset_password():
    """
    View for the user to reset his password
    """
    email = request.form["email"]

    existing_user = User.query.filter_by(email=email).first()
    if not existing_user.verified:
        flash(
            "The user is registered but the Email is not verified. Just get a new link below.",
            category="warning",
        )
        return jsonify("This Email is not registered")
    elif existing_user is not None:
        token = jwt.encode(
            {
                "email_address": email,
                "exp": datetime.datetime.now(tz=datetime.timezone.utc)
                       + datetime.timedelta(hours=current_app.config["TOKEN_EXPIRE"]),
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

        try:
            mail.send(
                subject="Reset your password",
                receivers=email,
                html_template="reset_password.html",
                body_params={"token": token, "user_name": existing_user.first_name},
            )
            flash("We sent you an Email, please check yout inbox.", category="success")
            return jsonify("Email sent")
        except Exception as e:
            current_app.logger.error(e, exc_info=True)
            current_app.logger.error(
                f"HOST: {current_app.config['EMAIL_HOST']} and port: {current_app.config['EMAIL_PORT']}"
            )
            current_app.logger.error(
                f"USERNAME: {current_app.config['EMAIL_USERNAME']}"
            )
            flash("Something went wrong. Please try again", category="warning")

    flash("There is no user with this Email", category="warning")
    return jsonify("This Email is not registered")


@auth_bp.route(current_app.config["URL_NEW_PASSWORD"], methods=["GET", "POST"])
def change_password(token):
    form = ResetPasswordForm()

    try:
        data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])

    except jwt.ExpiredSignatureError:
        data = False
        flash("The token already expired", category="warning")

    if form.validate_on_submit():
        email = data["email_address"]
        user = User.query.filter_by(email=email).first()
        user.set_password(form.password.data)
        db.session.commit()
        logout_user()
        flash("You can log in with your new password", category="success")
        return redirect(url_for("auth_bp.login"))
    else:
        flash_errors(form)

    return render_template(
        "change_password.jinja2",
        title="Change Password",
        form=form,
        body="Change the password of your account",
    )
