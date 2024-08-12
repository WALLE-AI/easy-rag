from flask import Blueprint

from utils.libs.external_api import ExternalApi

bp = Blueprint('app', __name__, url_prefix='/app/api')
api = ExternalApi(bp)

from . import completion