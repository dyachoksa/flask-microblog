import logging
import logging.handlers
import os

import rq
from elasticsearch import Elasticsearch
from flask import Flask, current_app, request
from flask_babel import Babel
from flask_babel import lazy_gettext as _l
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from redis import Redis

from config import Config

db = SQLAlchemy()
migrate = Migrate()

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = _l("Please log in to access this page.")

mail = Mail()

bootstrap = Bootstrap()

moment = Moment()

babel = Babel()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.elasticsearch = (
        Elasticsearch([app.config["ELASTICSEARCH_URL"]])
        if app.config["ELASTICSEARCH_URL"]
        else None
    )
    app.redis = Redis.from_url(app.config["REDIS_URL"])
    app.task_queue = rq.Queue("microblog-tasks", connection=app.redis)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)

    from app.errors import bt as errors_bp  # noqa: 402

    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp  # noqa: 402

    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.main import bp as main_bp  # noqa: 402

    app.register_blueprint(main_bp)

    if not app.debug and not app.testing:
        if app.config["MAIL_SERVER"]:
            auth = None

            if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
                auth = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])

            secure = None
            if app.config["MAIL_USE_TLS"]:
                secure = ()

            mail_handler = logging.handlers.SMTPHandler(
                mailhost=(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
                fromaddr="no-reply@" + app.config["APP_DOMAIN"],
                toaddrs=app.config["ADMINS"],
                subject="Microblog Failure",
                credentials=auth,
                secure=secure,
            )
            mail_handler.setLevel(logging.ERROR)

            app.logger.addHandler(mail_handler)

        if not os.path.exists("logs"):
            os.mkdir("logs")

        file_handler = logging.handlers.RotatingFileHandler(
            "logs/microblog.log", maxBytes=102400, backupCount=3
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("Microblog startup")

    return app


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(current_app.config["LANGUAGES"])


from app import models  # noqa:
