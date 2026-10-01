"""HTML page routes."""

from __future__ import annotations

from flask import Blueprint, render_template

from .services import settings

pages_bp = Blueprint("pages", __name__)


def _ctx():
    return {"theme": settings.theme}


@pages_bp.route("/")
def index():
    return render_template("index.html", page="home", **_ctx())


@pages_bp.route("/experiment")
def experiment():
    return render_template("experiment.html", page="direct", **_ctx())


@pages_bp.route("/sequence")
def sequence_page():
    return render_template("sequence.html", page="sequence", **_ctx())


@pages_bp.route("/live")
def live_page():
    return render_template("live.html", page="live", **_ctx())


@pages_bp.route("/show")
def show_page():
    return render_template("show.html", page="show", **_ctx())
