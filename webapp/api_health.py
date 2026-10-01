"""Health-check endpoint exposing the DMX connection + mode state."""

from __future__ import annotations

import platform

from flask import Blueprint, jsonify

from .services import dmx

api_health_bp = Blueprint("api_health", __name__)


@api_health_bp.get("/api/health")
def api_health():
    return jsonify(
        {
            "ok": True,
            "service": "icare-web",
            "python": platform.python_version(),
            "platform": platform.system(),
            "dmx": dmx.health(),
        }
    )
