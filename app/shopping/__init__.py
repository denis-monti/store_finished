from flask import Blueprint

bp = Blueprint('shopping', __name__)

from app.shopping import routes