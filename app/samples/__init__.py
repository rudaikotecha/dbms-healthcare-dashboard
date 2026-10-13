from flask import Blueprint
bp = Blueprint("samples", __name__, url_prefix="/samples")
from . import routes
