from locale import currency
import dash
import os
import sys
import boto3
import logging
from pathlib import Path
from flask import (
    Flask,
    current_app,
    send_file,
    url_for,
    redirect,
    request,
    session,
    jsonify,
    flash,
)
from flask_admin import Admin, expose, AdminIndexView
from flask_admin.contrib.fileadmin import FileAdmin
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_redmail import RedMail
from flask_migrate import Migrate
from src.admin.s3FileAdmin import S3FileAdmin
from src.services.logging import configure_logger
from flask_admin.contrib.sqla import ModelView

path = Path(__file__).resolve().parent / "Dash"
# Get the directory containing your `src` folder
BASE_DIR = Path(__file__).resolve().parent
# Add it to sys.path
sys.path.append(str(BASE_DIR))

# Currently empty cache manually
current_path = Path(__file__).parent.parent.resolve()
log_path = current_path / "logs"
if not log_path.is_dir():
    log_path.mkdir()


class CustomFileAdmin(FileAdmin):
    can_delete_dirs = False
    can_mkdir = False


class PaypalPlanView(ModelView):
    column_list = ("plan_id", "name", "description", "price", "currency")


admin_manager = Admin(template_mode="bootstrap4", index_view=AdminIndexView())
db = SQLAlchemy()
login_manager = LoginManager()
mail = RedMail()
migrate = Migrate()


def create_app():
    """Construct the core flask_session_tutorial."""
    app = Flask(__name__, instance_relative_config=False)
    app.secret_key = "your_secret_key"
    app.config.from_object("config.Config")
    app.config.from_object("config.URL")
    # Initialize Plugins and register them with the app
    # Set up logging

    configure_logger(
        env=os.environ.get("ENVIRONMENT", "local"),
        log_path=log_path,
        name="default",
    )

    if not app.debug:
        gunicorn_logger = logging.getLogger("gunicorn.error")
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

    engine_config = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        # Add more options as needed
    }
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_config
    app.config["SECRET_KEY"] = "your_secret_key"
    # if os.environ.get("ENVIRONMENT") == "local":
    #    if not os.path.exists(log_path):
    #        os.mkdir(log_path)
    #    engine_config = {
    #        "poolclass": NullPool,
    #    }
    db.init_app(app)
    app.db = db
    migrate.init_app(app, db)
    admin_manager.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "/login"
    mail.init_app(app)

    s3_client = boto3.resource(
        service_name="s3",
        region_name=os.environ.get("BUCKETEER_AWS_REGION"),
        aws_access_key_id=os.environ.get("BUCKETEER_AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("BUCKETEER_AWS_SECRET_ACCESS_KEY"),
    )
    app.config["S3_CLIENT"] = s3_client

    @app.before_request
    def check_login():
        app.logger.debug("Headers: %s", request.headers)
        app.logger.debug("Body: %s", request.get_data())
        block_list = ["/composition"]
        # Check if the requested route is whitelisted
        if request.method == "GET":
            if current_user:
                if request.path not in block_list:
                    # Free path, move on
                    return
                elif request.path in block_list and not current_user.is_authenticated:
                    # User has now account and trys to get to block page
                    flash(
                        "Composition is for subscribers. Please login and subscribe first",
                        category="warning",
                    )
                    return redirect("/login")
                elif request.path in block_list and current_user.subscription == "0":
                    # The user as an account but no subscription -> go to pricing
                    return redirect("/pricing")
                else:
                    for pg in dash.page_registry:
                        if request.path == dash.page_registry[pg]["path"]:
                            session["url"] = request.url
                        return
            return
        else:
            if current_user.is_authenticated:
                data = request.get_json()
                # Check if the request data contains 'inputs' with a 'pathname' attribute
                inputs = data.get("inputs", [])

                return
                if (
                    len(inputs) == 1
                    and inputs[0].get("id", False) == "url"
                    and inputs[0].get("value", False) in block_list
                    and not current_user.is_authenticated
                ):
                    # The page redirect goes to block list and user is not authenticated, redirect
                    session["url"] = request.url
                    return jsonify(
                        {"multi": True, "response": {"url": {"pathname": "/pricing"}}}
                    )
                else:
                    for pg in dash.page_registry:
                        if request.path == dash.page_registry[pg]["path"]:
                            session["url"] = request.url
                        return
            return

    with app.app_context():
        # openpay.production = current_app.config["OPENPAY_PRODUCTION"]
        # openpay.api_key = current_app.config["OPENPAY_APIKEY"]
        # openpay.verify_ssl_certs = current_app.config["OPENPAY_VERIFY_SSL_CERTS"]
        # openpay.merchant_id = current_app.config["OPENPAY_MERCHANT_ID"]
        # openpay.country = current_app.config["OPENPAY_COUNTRY"]
        #
        # current_app.Openpay = openpay

        # Integrate the dash application
        from .auth import routes as auth
        from .models import PaypalPlans, PaypalSubscription, Purchases, Plan

        # Register admin views for managing user and uploading files
        from .models import User

        admin_manager.add_view(
            CustomFileAdmin(log_path, name="Log Files", endpoint="log")
        )
        admin_manager.add_view(ModelView(User, db.session))
        admin_manager.add_view(ModelView(PaypalPlans, db.session))
        admin_manager.add_view(ModelView(PaypalSubscription, db.session))
        admin_manager.add_view(
            CustomFileAdmin(path / "config", name="Config Files", endpoint="config")
        )
        admin_manager.add_view(
            S3FileAdmin(
                s3client=s3_client,
                bucket_name=current_app.config["S3_BUCKET"],
                name="data",
            )
        )

        # Register Blueprints, which are layouts
        app.register_blueprint(auth.auth_bp)

        # Create Database Models
        db.create_all()
        """
        if (
            User.query.filter_by(email=current_app.config["ADMIN_EMAIL"]).first()
            is None
        ):
            current_app.logger.info("Creating Admin User")
            user = User(
                email=current_app.config["ADMIN_EMAIL"],
                is_admin=True,
                verified=True,
                subscription="Silver",
                created=datetime.datetime.now(),
                data_consent=True,
            )
            user.set_password(current_app.config["ADMIN_PASSWORD"])
            db.session.add(user)
            db.session.commit()

            user = User(
                email=current_app.config["NO_ADMIN_EMAIL"],
                is_admin=False,
                verified=True,
                subscription=False,
                created=datetime.datetime.now(),
                data_consent=True,
            )
            user.set_password(current_app.config["NO_ADMIN_PASSWORD"])
            db.session.add(user)
            db.session.commit()
        """
        from .Dash.dashapp import create_dashapp

        app = create_dashapp(app, current_app.config["URL_DASH"])
        # app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
        return app
