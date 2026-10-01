"""Sequence (file editor) REST API."""

from __future__ import annotations

import json
import logging
import os

from flask import Blueprint, jsonify, request

from .schemas import normalize_sequence
from .services import SEQ_DIR
from .utils import safe_json_path

logger = logging.getLogger(__name__)
api_sequence_bp = Blueprint("api_sequence", __name__)


def _safe_path(name: str) -> str | None:
    """Return an absolute, sanitized path inside SEQ_DIR, or None on bad input."""
    return safe_json_path(name, SEQ_DIR)


@api_sequence_bp.get("/api/sequence/list")
def api_sequence_list():
    try:
        files = []
        if os.path.isdir(SEQ_DIR):
            for f in os.listdir(SEQ_DIR):
                if f.lower().endswith(".json"):
                    files.append(f)
        return jsonify({"ok": True, "files": sorted(files)})
    except OSError as exc:
        logger.exception("Could not list sequences")
        return jsonify({"ok": False, "error": str(exc)}), 500


@api_sequence_bp.get("/api/sequence/load")
def api_sequence_load():
    name = request.args.get("name", "")
    path = _safe_path(name)
    if path is None:
        return jsonify({"ok": False, "error": "Invalid file name"}), 400
    if not os.path.isfile(path):
        return jsonify({"ok": False, "error": "File not found"}), 404
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        data = normalize_sequence(raw)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        logger.exception("Could not load sequence %s", name)
        return jsonify({"ok": False, "error": str(exc)}), 422
    return jsonify({"ok": True, "data": data})


@api_sequence_bp.post("/api/sequence/save")
def api_sequence_save():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "")
    data = payload.get("data")
    if not name:
        return jsonify({"ok": False, "error": "Missing name"}), 400
    if data is None:
        return jsonify({"ok": False, "error": "Missing data"}), 400
    path = _safe_path(name)
    if path is None:
        return jsonify({"ok": False, "error": "Invalid file name"}), 400
    try:
        # Validate by normalising round-trip
        normalized = normalize_sequence(data)
        os.makedirs(SEQ_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(normalized, fh, indent=2, ensure_ascii=False)
    except (OSError, ValueError) as exc:
        logger.exception("Could not save sequence %s", name)
        return jsonify({"ok": False, "error": str(exc)}), 500
    return jsonify({"ok": True, "saved": os.path.basename(path)})


@api_sequence_bp.post("/api/sequence/delete")
def api_sequence_delete():
    payload = request.get_json(silent=True) or {}
    path = _safe_path(payload.get("name", ""))
    if path is None:
        return jsonify({"ok": False, "error": "Invalid file name"}), 400
    if not os.path.isfile(path):
        return jsonify({"ok": False, "error": "File not found"}), 404
    try:
        os.remove(path)
    except OSError as exc:
        logger.exception("Could not delete sequence")
        return jsonify({"ok": False, "error": str(exc)}), 500
    return jsonify({"ok": True})
