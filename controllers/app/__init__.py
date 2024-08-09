from flask import Blueprint

from utils.libs.external_api import ExternalApi

bp = Blueprint('file', __name__, url_prefix='/file/api')
api = ExternalApi(bp)

from . import completion