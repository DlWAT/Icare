"""User settings (theme, last-used port, last sequence, ...) REST API."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from .services import settings

api_settings_bp = Blueprint("api_settings", __name__)


_ALLOWED_KEYS = {"theme", "last_com_port", "last_sequence", "base_color_channel"}


@api_settings_bp.get("/api/settings")
def api_settings_get():
    return jsonify({"ok": True, "settings": settings.to_dict()})


@api_settings_bp.post("/api/settings")
def api_settings_set():
    payload = request.get_json(silent=True) or {}
    updates = {k: v for k, v in payload.items() if k in _ALLOWED_KEYS}
    if not updates:
        return jsonify({"ok": False, "error": "No valid settings provided"}), 400
    if "theme" in updates and updates["theme"] not in {"dark", "light"}:
        return jsonify({"ok": False, "error": "theme must be 'dark' or 'light'"}), 400
    if "base_color_channel" in updates:
        try:
            updates["base_color_channel"] = int(updates["base_color_channel"])
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "base_color_channel must be int"}), 400
    settings.update(**updates)
    return jsonify({"ok": True, "settings": settings.to_dict()})
