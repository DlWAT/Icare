from flask import Blueprint, request, jsonify
import os
import json as _json

from .services import SEQ_DIR

api_sequence_bp = Blueprint("api_sequence", __name__)

@api_sequence_bp.get("/api/sequence/list")
def api_sequence_list():
    try:
        files = []
        if os.path.isdir(SEQ_DIR):
            for f in os.listdir(SEQ_DIR):
                if f.lower().endswith(".json"):
                    files.append(f)
        return jsonify({"ok": True, "files": sorted(files)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@api_sequence_bp.get("/api/sequence/load")
def api_sequence_load():
    name = request.args.get("name", "")
    if not name.endswith(".json"):
        return jsonify({"ok": False, "error": "Invalid file name"}), 400
    path = os.path.join(SEQ_DIR, name)
    if not os.path.isfile(path):
        return jsonify({"ok": False, "error": "File not found"}), 404
    with open(path, "r", encoding="utf-8") as f:
        data = f.read()
    return jsonify({"ok": True, "data": _json.loads(data)})


@api_sequence_bp.post("/api/sequence/save")
def api_sequence_save():
    payload = request.get_json(force=True) or {}
    name = payload.get("name", "")
    data = payload.get("data")
    if not name:
        return jsonify({"ok": False, "error": "Missing name"}), 400
    if not name.endswith(".json"):
        name += ".json"
    try:
        os.makedirs(SEQ_DIR, exist_ok=True)
        path = os.path.join(SEQ_DIR, name)
        with open(path, "w", encoding="utf-8") as f:
            _json.dump(data, f, indent=2)
        return jsonify({"ok": True, "saved": name})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
