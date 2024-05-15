from os import environ, path, system
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, ".env"))
database_path = path.join(basedir, "instance", "database.db")


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

    # Database
    DATABASE_PATH = f"{database_path}"
    SQLALCHEMY_DATABASE_URI = environ.get("DATABASE_URI", "sqlite:///database.db")
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SMTP
    EMAIL_HOST = environ.get("EMAIL_HOST", "localhost")
    EMAIL_PORT = int(environ.get("EMAIL_PORT", 587))
    EMAIL_USERNAME = environ.get("EMAIL_USERNAME", None)
    EMAIL_PASSWORD = environ.get("EMAIL_PASSWORD", None)
    EMAIL_SENDER = environ.get("EMAIL_SENDER", None)
    TOKEN_EXPIRE = 24

    OPENPAY_PRODUCTION = False
    OPENPAY_APIKEY = environ.get("OPENPAY_APIKEY")
    OPENPAY_VERIFY_SSL_CERTS = False
    OPENPAY_MERCHANT_ID = environ.get("OPENPAY_MERCHANT_ID")
    OPENPAY_COUNTRY = environ.get("OPENPAY_COUNTRY")


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
