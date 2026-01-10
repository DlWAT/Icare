from flask import Blueprint, request, jsonify
import os
import json as _json

from .services import SEQ_DIR
from .live_player import LivePlayer

# Single instance of LivePlayer
live_player = LivePlayer()

api_live_bp = Blueprint("api_live", __name__)

@api_live_bp.get("/api/live/list")
def api_live_list():
    # Reuse sequence list
    try:
        files = []
        if os.path.isdir(SEQ_DIR):
            for f in os.listdir(SEQ_DIR):
                if f.lower().endswith(".json"):
                    files.append(f)
        return jsonify({"ok": True, "files": sorted(files)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@api_live_bp.post("/api/live/load")
def api_live_load():
    payload = request.get_json(force=True) or {}
    name = payload.get("name", "")
    if not name.endswith(".json"):
        return jsonify({"ok": False, "error": "Invalid file name"}), 400
    path = os.path.join(SEQ_DIR, name)
    if not os.path.isfile(path):
        return jsonify({"ok": False, "error": "File not found"}), 404
    with open(path, "r", encoding="utf-8") as f:
        data = _json.load(f)
    live_player.load(data)
    return jsonify({"ok": True, "data": data})


@api_live_bp.post("/api/live/play")
def api_live_play():
    payload = request.get_json(force=True) or {}
    freq = payload.get("freq")
    live_player.start(freq=freq)
    return jsonify({"ok": True})


@api_live_bp.post("/api/live/pause")
def api_live_pause():
    live_player.pause()
    return jsonify({"ok": True})


@api_live_bp.post("/api/live/stop")
def api_live_stop():
    live_player.stop()
    return jsonify({"ok": True})


@api_live_bp.post("/api/live/next")
def api_live_next():
    live_player.next()
    return jsonify({"ok": True})


@api_live_bp.post("/api/live/prev")
def api_live_prev():
    live_player.prev()
    return jsonify({"ok": True})


@api_live_bp.post("/api/live/toggle-module")
def api_live_toggle_module():
    payload = request.get_json(force=True) or {}
    name = payload.get("name")
    if not name:
        return jsonify({"ok": False, "error": "Missing name"}), 400
    live_player.toggle_module(name)
    return jsonify({"ok": True, "selected": sorted(list(live_player.selected_modules))})


@api_live_bp.post("/api/live/select-all")
def api_live_select_all():
    live_player.select_all()
    return jsonify({"ok": True, "selected": sorted(list(live_player.selected_modules))})


@api_live_bp.post("/api/live/unselect-all")
def api_live_unselect_all():
    live_player.unselect_all()
    return jsonify({"ok": True, "selected": []})


@api_live_bp.get("/api/live/status")
def api_live_status():
    return jsonify({"ok": True, "status": live_player.status()})
