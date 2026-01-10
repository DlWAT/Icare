from flask import Blueprint, render_template

pages_bp = Blueprint("pages", __name__)

@pages_bp.route("/")
def index():
    return render_template("index.html")

@pages_bp.route("/experiment")
def experiment():
    return render_template("experiment.html")

@pages_bp.route("/sequence")
def sequence_page():
    return render_template("sequence.html")

@pages_bp.route("/live")
def live_page():
    return render_template("live.html")
