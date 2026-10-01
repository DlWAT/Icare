"""Flask application factory for Icare Web."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from flask import Flask

from .config import setup_logging

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Build and return the configured Flask app."""
    setup_logging(level=logging.INFO)

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        pkg_root = Path(sys._MEIPASS) / "webapp"  # type: ignore[attr-defined]
    else:
        pkg_root = Path(__file__).resolve().parent

    app = Flask(
        __name__,
        template_folder=str(pkg_root / "templates"),
        static_folder=str(pkg_root / "static"),
        static_url_path="/static",
    )

    # Register blueprints lazily to avoid premature imports
    from .api_experiment import api_experiment_bp
    from .api_health import api_health_bp
    from .api_live import api_live_bp
    from .api_palettes import api_palettes_bp
    from .api_sequence import api_sequence_bp
    from .api_settings import api_settings_bp
    from .api_show import api_show_bp
    from .pages import pages_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(api_experiment_bp)
    app.register_blueprint(api_sequence_bp)
    app.register_blueprint(api_live_bp)
    app.register_blueprint(api_health_bp)
    app.register_blueprint(api_palettes_bp)
    app.register_blueprint(api_settings_bp)
    app.register_blueprint(api_show_bp)

    logger.info("Icare Web app created")
    return app
