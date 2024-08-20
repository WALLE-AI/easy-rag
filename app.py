import json
import os
import sys
from logging.handlers import RotatingFileHandler

import loguru
from flask import Flask, Response
from flask_cors import CORS

from config import app_config
from services.database import migrate_db, postgres_db
from services.database.postgres_db import db
from services.storge import storage


class StarApp(Flask):
    pass



def initialize_extensions(app):
    # Since the application instance is now created, pass it to each Flask
    # extension instance to bind it to the Flask application instance (app)
    storage.init_app(app)
    postgres_db.init_app(app)
    migrate_db.init(app,db)


def create_flask_app_with_configs() -> Flask:
    """
    create a raw flask app
    with configs loaded from .env file
    """
    star_app = StarApp(__name__)
    star_app.config.from_mapping(app_config.model_dump())
    ##set api key env
    for key, value in star_app.config.items():
        if key == "OPENROUTER_API_KEY":
            loguru.logger.info(f"set openrouter api key")
            os.environ[key] = value
        elif key == "TONGYI_DASHSCOPE_API_KEY":
            loguru.logger.info(f"set tongyi api key")
            os.environ[key] = value
        elif key == "SILICONFLOW_API_KEY":
            loguru.logger.info(f"set siliconflow api key")
            os.environ[key] = value
    
    return star_app

def create_app():
    app = create_flask_app_with_configs()

    app.secret_key = app.config['SECRET_KEY']

    log_handlers = None
    log_file = app.config.get('LOG_FILE')
    if log_file:
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)
        log_handlers = [
            RotatingFileHandler(
                filename=log_file,
                maxBytes=1024 * 1024 * 1024,
                backupCount=5
            ),
            loguru.logger.info(sys.stdout)
        ]

    register_blueprints(app)
    initialize_extensions(app)

    return app


# register blueprint routers
def register_blueprints(app):
    from controllers.file import bp as files_bp
    from controllers.app import bp as app_bp

    CORS(files_bp,
         # resources={
         #     r"/*": {"origins": app.config['CONSOLE_CORS_ALLOW_ORIGINS']}},
         # supports_credentials=True,
         allow_headers=['Content-Type'],
         methods=['GET', 'PUT', 'POST', 'DELETE', 'OPTIONS', 'PATCH']
         )
    app.register_blueprint(files_bp)

    CORS(app_bp,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'PUT', 'POST', 'DELETE', 'OPTIONS', 'PATCH'],
         expose_headers=['X-Version', 'X-Env']
         )

    app.register_blueprint(app_bp)


app = create_app()

if app.config.get('TESTING'):
    print("App is running in TESTING mode")


@app.after_request
def after_request(response):
    """Add Version headers to the response."""
    response.set_cookie('remember_token', '', expires=0)
    response.headers.add('X-Version', app_config.CURRENT_VERSION)
    response.headers.add('X-Env', app_config.DEPLOY_ENV)
    return response


@app.route('/health')
def health():
    return Response(json.dumps({
        'pid': os.getpid(),
        'status': 'ok',
        'version': app_config.CURRENT_VERSION
    }), status=200, content_type="application/json")

if __name__ == "__main__":
    loguru.logger.info(f"esay-rag start")
    app.run(host='0.0.0.0', port=9990)