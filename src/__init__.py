import smtplib
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
    def on_model_change(self, form, model, is_created):
        """Called when creating or updating a user model."""
        # Check if the password field is present in the form data
        print(form)

        # Call the superclass implementation
        return super().on_model_change(form, model, is_created)


admin_manager = Admin(
    template_mode="bootstrap4", index_view=AdminIndexView(), name=f"Admin Panel"
)
db = SQLAlchemy()
login_manager = LoginManager()


mail = RedMail()
migrate = Migrate()


class CustomModelView(ModelView):
    edit_template = 'admin/edit.html'

    def get_model_fields(self, model):
        """Get all fields for a given SQLAlchemy model."""
        return model.__table__.columns.keys()

    @expose('/edit/', methods=['GET', 'POST'])
    def edit_view(self, *args, **kwargs):
        if request.method == 'POST':
            user_id = request.args.get('id')
            return redirect(url_for('auth_bp.model_edit', id=user_id))

        user_id = request.args.get('id')
        if not user_id:
            return jsonify({"error": "No user ID provided"}), 400

        from src.models import User
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # fields = [column.name for column in User.__table__.columns]
        fields = {}
        for column in User.__table__.columns:
            print(column)
            default_value = column.default.arg if column.default is not None else None
            field_info = {
                "type": str(column.type),
                "nullable": column.nullable,
                "max_length": column.type.length if hasattr(column.type, 'length') else None,
                "default": default_value
            }
            fields[column.name] = field_info

        return self.render(self.edit_template, user=user, fields=fields, getattr=getattr)


# Add the custom filter to Jinja environment
def pretty_field_name(field_name):
    return field_name.replace('_', ' ').title()


def create_app():
    """Construct the core flask_session_tutorial."""
    app = Flask(__name__, instance_relative_config=False, template_folder="templates")
    app.secret_key = "your_secret_key"
    app.config.from_object("config.Config")
    app.config.from_object("config.URL")
    app.config["EMAIL_CLS_SMTP"] = smtplib.SMTP_SSL
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
    app.jinja_env.filters['pretty'] = pretty_field_name

    @app.before_request
    def check_login():
        block_list = ["/composition"]
        # Check if the requested route is whitelisted
        if request.method == "GET":
            if current_user:
                user = session.get("user", None)
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
                elif (
                    request.path in block_list
                    and user.get("subscription", None) is None
                ):
                    # The user as an account but no subscription -> go to pricing
                    return redirect("/pricing")
                else:
                    for pg in dash.page_registry:
                        if request.path == dash.page_registry[pg]["path"]:
                            session["url"] = request.url
                        return
            return
        elif request.method == "POST":
            pass
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
        # Integrate the dash application
        from .auth import routes as auth
        from .models import PaypalPlans, PaypalSubscription, Purchases, Plan

        # Register admin views for managing user and uploading files
        from .models import User

        admin_manager.add_view(
            CustomFileAdmin(log_path, name="Log Files", endpoint="log")
        )
        admin_manager.add_view(CustomModelView(User, db.session, endpoint="users"))
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
        # Prints all the urls of app
        # print(app.url_map)

        try:
            plan = PaypalPlans(
                plan_id="P-0WC16321VC6721344MZ5EIRY",
                name="Silver",
                price=7,
                currency="USD",
                interval_unit="Days",
                interval_count=30,
            )
            db.session.add(plan)
            db.session.commit()
        except:
            pass
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
