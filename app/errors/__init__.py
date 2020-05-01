from flask import Blueprint

bt = Blueprint("errors", __name__)

from . import handlers  # noqa:
