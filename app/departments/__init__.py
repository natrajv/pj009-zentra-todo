from flask import Blueprint

bp = Blueprint("departments", __name__, url_prefix="/departments")

from . import routes  # noqa: E402,F401
