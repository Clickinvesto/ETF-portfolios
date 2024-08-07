from os import environ, path, system
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, ".env"))
database_path = path.join(basedir, "instance", "database.db")


def str_to_bool(value):
    return str(value).lower() in ("true", "1", "t", "y", "yes")


class Config:
    # General Flask configuration
    HOST = environ.get("HOST")
    PORT = environ.get("PORT")
    PRODUCT_NAME = environ.get("PRODUCT_NAME")
    DEBUG = environ.get("DEBUG")
    ADMIN_EMAIL = "admin@test.com"
    ADMIN_PASSWORD = "test"
    NO_ADMIN_EMAIL = "no_admin@test.com"
    NO_ADMIN_PASSWORD = "test"
    FLASK_ADMIN_SWATCH = environ.get("FLASK_ADMIN_SWATCH", "materia")
    SECRET_KEY = environ.get("SECRET_KEY", "teasfouho1234nn124uh")
    DATABASE_URL = environ.get("DATABASE_URL")
    # Database
    DATABASE_PATH = f"{database_path}"
    uri = environ.get("DATABASE_URL", "sqlite:///database.db")
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = uri
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SMTP
    REDMAIL_USE_SSL = True
    EMAIL_HOST = environ.get("EMAIL_HOST", "localhost")
    EMAIL_PORT = int(environ.get("EMAIL_PORT", 587))
    EMAIL_USERNAME = environ.get("EMAIL_USERNAME", None)
    EMAIL_PASSWORD = environ.get("EMAIL_PASSWORD", None)
    EMAIL_SENDER = environ.get("EMAIL_SENDER", None)
    USE_SSL = True
    EMAIL_USE_STARTTLS = str_to_bool(environ.get("EMAIL_USE_STARTTLS", False))
    TOKEN_EXPIRE = 24

    OPENPAY_PRODUCTION = False
    OPENPAY_APIKEY = environ.get("OPENPAY_APIKEY")
    OPENPAY_VERIFY_SSL_CERTS = False
    OPENPAY_MERCHANT_ID = environ.get("OPENPAY_MERCHANT_ID")
    OPENPAY_COUNTRY = environ.get("OPENPAY_COUNTRY")

    S3_BUCKET = environ.get("BUCKETEER_BUCKET_NAME")
    AWS_KEY_ID = environ.get("BUCKETEER_AWS_ACCESS_KEY_ID")
    AWS_SECRET_KEY = environ.get("BUCKETEER_AWS_SECRET_ACCESS_KEY")
    AWS_REGION = environ.get("BUCKETEER_AWS_REGION")

    PAYPAL_SANDBOX = environ.get("PAYPAL_SANDBOX", False)
    PAYPAL_CLIENT_ID = environ.get("PAYPAL_CLIENT_ID")
    PAYPAL_CLIENT_SECRET = environ.get("PAYPAL_CLIENT_SECRET")
    PAYPAL_PLAN_ID = environ.get("PAYPAL_PLAN_ID")
    PAYPAL_API_BASE_URL = (
        "https://api-m.sandbox.paypal.com"
        if PAYPAL_SANDBOX
        else "https://api.paypal.com"
    )


class URL:
    # Flask URLS
    URL_BASE = "/"
    URL_DASH = "/"
    URL_EXPLORER = "/exploration"
    URL_COMPOSITION = "/composition"
    URL_PRICING = "/pricing"
    URL_SETTINGS = "/settings"
    URL_LOGIN = "/login"
    URL_SIGNUP = "/signup"
    URL_RESET_PASSWORD = "/reset"
    URL_NEW_PASSWORD = "/new-password/<token>"
    URL_CHANGE_PASSWORD = "/change-password"
    URL_LOGOUT = "/logout"
    URL_RESEND_VERIFY = "/verify"
    URL_VERIFY_EMAIL = "/vefify-email/<token>"
    URL_CONFIGURATION = "/configuration"
    URL_SUBSCRIBTION = "/subscribtion"
    URL_DISCLAIMER = "/disclaimer"
    URL_PRIVACY_POLICY = "/terms-condition"

    URL_SAVE_SUBSCRIPTION = "/save-subscription"
    URL_CANCEL_SUBSCRIPTION = "/cancel-subscription"
