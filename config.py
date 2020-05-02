import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
default_db_url = "sqlite:///" + os.path.join(basedir, "app.db")

load_dotenv(os.path.join(basedir, ".env"))


class Config:
    APP_DOMAIN = "microblog.local"

    SECRET_KEY = os.environ.get("SECRET_KEY") or "default-super-secret-key"

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or default_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL") is not None
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

    ADMINS = ["admin@example.com"]

    POSTS_PER_PAGE = 25

    LANGUAGES = ["en", "ru"]

    MS_TRANSLATOR_KEY = os.environ.get("MS_TRANSLATOR_KEY")

    ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL")
