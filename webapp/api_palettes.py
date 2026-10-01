"""Color palettes API.

A *palette* is a small JSON file under ``Palettes/``::

    { "name": "MyShow", "colors": ["#ff0000", "#00ff00", ...] }

Used by the Direct tab to save and reuse favourite colours.
"""

from __future__ import annotations

import json
import logging
import os
import re

from flask import Blueprint, jsonify, request

from .services import PALETTE_DIR, settings
from .utils import safe_json_path

logger = logging.getLogger(__name__)
api_palettes_bp = Blueprint("api_palettes", __name__)

HEX_COLOR_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")


def _normalize_hex(c: str) -> str | None:
    if not isinstance(c, str):
        return None
    if HEX_COLOR_RE.match(c):
        return ("#" + c.lstrip("#")).lower()
    return None


def _safe_path(name: str) -> str | None:
    """Return an absolute, sanitized path inside PALETTE_DIR, or None on bad input."""
    return safe_json_path(name, PALETTE_DIR)


# ---------------------------------------------------------------------------
# Favourite colours (single user-wide list, persisted in settings)
# ---------------------------------------------------------------------------
@api_palettes_bp.get("/api/palettes/favorites")
def api_favorites_list():
    return jsonify({"ok": True, "colors": settings.favorite_colors})


@api_palettes_bp.post("/api/palettes/favorites/add")
def api_favorites_add():
    payload = request.get_json(silent=True) or {}
    color = _normalize_hex(payload.get("color", ""))
    if not color:
        return jsonify({"ok": False, "error": "Invalid color"}), 400
    if color not in settings.favorite_colors:
        settings.favorite_colors.append(color)
        # Cap to 32
        settings.favorite_colors = settings.favorite_colors[-32:]
        settings.save()
    return jsonify({"ok": True, "colors": settings.favorite_colors})


@api_palettes_bp.post("/api/palettes/favorites/remove")
def api_favorites_remove():
    payload = request.get_json(silent=True) or {}
    color = _normalize_hex(payload.get("color", ""))
    if not color:
        return jsonify({"ok": False, "error": "Invalid color"}), 400
    settings.favorite_colors = [c for c in settings.favorite_colors if c != color]
    settings.save()
    return jsonify({"ok": True, "colors": settings.favorite_colors})


# ---------------------------------------------------------------------------
# Named palettes (per-show files)
# ---------------------------------------------------------------------------
@api_palettes_bp.get("/api/palettes/list")
def api_palettes_list():
    files = []
    if os.path.isdir(PALETTE_DIR):
        for f in os.listdir(PALETTE_DIR):
            if f.lower().endswith(".json"):
                files.append(f)
    return jsonify({"ok": True, "files": sorted(files)})


@api_palettes_bp.get("/api/palettes/load")
def api_palettes_load():
    name = request.args.get("name", "")
    path = _safe_path(name)
    if path is None:
        return jsonify({"ok": False, "error": "Invalid file name"}), 400
    if not os.path.isfile(path):
        return jsonify({"ok": False, "error": "File not found"}), 404
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        logger.exception("Could not load palette")
        return jsonify({"ok": False, "error": str(exc)}), 422
    return jsonify({"ok": True, "data": data})


@api_palettes_bp.post("/api/palettes/save")
def api_palettes_save():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "")
    colors = payload.get("colors") or []
    if not isinstance(colors, list):
        return jsonify({"ok": False, "error": "colors must be a list"}), 400
    cleaned = [c for c in (_normalize_hex(c) for c in colors) if c]
    path = _safe_path(name)
    if path is None:
        return jsonify({"ok": False, "error": "Invalid file name"}), 400
    try:
        os.makedirs(PALETTE_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"name": os.path.basename(path)[:-5], "colors": cleaned}, fh, indent=2)
    except OSError as exc:
        logger.exception("Could not save palette")
        return jsonify({"ok": False, "error": str(exc)}), 500
    return jsonify({"ok": True, "saved": os.path.basename(path)})


@api_palettes_bp.post("/api/palettes/delete")
def api_palettes_delete():
    payload = request.get_json(silent=True) or {}
    path = _safe_path(payload.get("name", ""))
    if path is None or not os.path.isfile(path):
        return jsonify({"ok": False, "error": "File not found"}), 404
    try:
        os.remove(path)
    except OSError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500
    return jsonify({"ok": True})
