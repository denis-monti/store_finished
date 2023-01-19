from flask import Blueprint

bp = Blueprint('catalog', __name__)

from app.catalog import routes