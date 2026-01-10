from flask import Flask

from .pages import pages_bp
from .api_experiment import api_experiment_bp
from .api_sequence import api_sequence_bp
from .api_live import api_live_bp


def create_app():
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(pages_bp)
    app.register_blueprint(api_experiment_bp)
    app.register_blueprint(api_sequence_bp)
    app.register_blueprint(api_live_bp)

    return app
