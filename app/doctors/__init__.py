from flask import Blueprint
bp = Blueprint("doctors", __name__, url_prefix="/doctors")
from . import routes
