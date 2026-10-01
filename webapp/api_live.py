"""Live playback REST API."""

from __future__ import annotations

import json
import logging
import os

from flask import Blueprint, jsonify, request

from .live_player import LivePlayer
from .services import SEQ_DIR, settings
from .utils import safe_json_path

logger = logging.getLogger(__name__)

# Single instance shared by the API
live_player = LivePlayer()
api_live_bp = Blueprint("api_live", __name__)


def _safe_path(name: str) -> str | None:
    """Return an absolute, sanitized path inside SEQ_DIR, or None on bad input."""
    return safe_json_path(name, SEQ_DIR)


@api_live_bp.get("/api/live/list")
def api_live_list():
    try:
        files = []
        if os.path.isdir(SEQ_DIR):
            for f in os.listdir(SEQ_DIR):
                if f.lower().endswith(".json"):
                    files.append(f)
        return jsonify({"ok": True, "files": sorted(files)})
    except OSError as exc:
        logger.exception("Could not list live sequences")
        return jsonify({"ok": False, "error": str(exc)}), 500


@api_live_bp.post("/api/live/load")
def api_live_load():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "")
    path = _safe_path(name)
    if path is None:
        return jsonify({"ok": False, "error": "Invalid file name"}), 400
    if not os.path.isfile(path):
        return jsonify({"ok": False, "error": "File not found"}), 404
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        data = live_player.load(raw)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        logger.exception("Could not load live sequence %s", name)
        return jsonify({"ok": False, "error": str(exc)}), 422
    settings.update(last_sequence=os.path.basename(path))
    return jsonify({"ok": True, "data": data})


@api_live_bp.post("/api/live/play")
def api_live_play():
    payload = request.get_json(silent=True) or {}
    bpm = payload.get("bpm") or payload.get("freq")  # accept legacy 'freq'
    live_player.start(bpm=bpm)
    return jsonify({"ok": True, "bpm": live_player.bpm})


@api_live_bp.post("/api/live/pause")
def api_live_pause():
    live_player.pause()
    return jsonify({"ok": True, "paused": live_player.paused})


@api_live_bp.post("/api/live/stop")
def api_live_stop():
    live_player.stop()
    return jsonify({"ok": True})


@api_live_bp.post("/api/live/next")
def api_live_next():
    live_player.next()
    return jsonify({"ok": True, "index": live_player.index})


@api_live_bp.post("/api/live/prev")
def api_live_prev():
    live_player.prev()
    return jsonify({"ok": True, "index": live_player.index})


@api_live_bp.post("/api/live/toggle-module")
def api_live_toggle_module():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    if not name:
        return jsonify({"ok": False, "error": "Missing name"}), 400
    live_player.toggle_module(name)
    return jsonify({"ok": True, "selected": sorted(live_player.selected_modules)})


@api_live_bp.post("/api/live/select-all")
def api_live_select_all():
    live_player.select_all()
    return jsonify({"ok": True, "selected": sorted(live_player.selected_modules)})


@api_live_bp.post("/api/live/unselect-all")
def api_live_unselect_all():
    live_player.unselect_all()
    return jsonify({"ok": True, "selected": []})


# ---------------------------------------------------------------------------
# Tap-tempo
# ---------------------------------------------------------------------------
@api_live_bp.post("/api/live/tap")
def api_live_tap():
    bpm = live_player.tap()
    return jsonify({"ok": True, "bpm": bpm, "currentBpm": live_player.bpm})


@api_live_bp.post("/api/live/tap-reset")
def api_live_tap_reset():
    live_player.reset_taps()
    return jsonify({"ok": True})


@api_live_bp.post("/api/live/bpm")
def api_live_set_bpm():
    payload = request.get_json(silent=True) or {}
    try:
        bpm = int(payload.get("bpm", 60))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Invalid bpm"}), 400
    live_player.bpm = max(20, min(300, bpm))
    return jsonify({"ok": True, "bpm": live_player.bpm})


@api_live_bp.get("/api/live/status")
def api_live_status():
    return jsonify({"ok": True, "status": live_player.status()})
