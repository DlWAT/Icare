"""Show API: patch, looks, Ableton link and scene mapping."""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from .fixtures import (
    Fixture,
    patch_summary,
    profile_catalog,
    validate_patch,
)
from .looks import Look, delete_look, list_looks, load_look, resolve, save_look
from .services import LOOK_DIR, ableton, dmx, scene_engine

logger = logging.getLogger(__name__)
api_show_bp = Blueprint("api_show", __name__)


def _bad(msg: str, code: int = 400):
    return jsonify({"ok": False, "error": msg}), code


# ---------------------------------------------------------------------------
# Patch
# ---------------------------------------------------------------------------
@api_show_bp.get("/api/patch")
def api_patch_get():
    return jsonify(
        {
            "ok": True,
            "patch": patch_summary(dmx.patch),
            "profiles": profile_catalog(),
        }
    )


@api_show_bp.post("/api/patch")
def api_patch_set():
    payload = request.get_json(silent=True) or {}
    raw = payload.get("fixtures")
    if not isinstance(raw, list):
        return _bad("Missing 'fixtures' list")
    try:
        fixtures = validate_patch(Fixture.from_dict(item) for item in raw)
    except (ValueError, KeyError, TypeError) as exc:
        return _bad(f"Invalid patch: {exc}")
    dmx.set_patch(fixtures)
    try:
        from .config import PATCH_FILE
        from .fixtures import save_patch

        save_patch(PATCH_FILE, fixtures)
    except OSError as exc:
        logger.warning("Could not persist patch: %s", exc)
    return jsonify({"ok": True, "patch": patch_summary(dmx.patch)})


# ---------------------------------------------------------------------------
# Looks
# ---------------------------------------------------------------------------
@api_show_bp.get("/api/looks/list")
def api_looks_list():
    return jsonify({"ok": True, "looks": list_looks(LOOK_DIR)})


@api_show_bp.get("/api/looks/load")
def api_looks_load():
    name = request.args.get("name", "")
    try:
        look = load_look(LOOK_DIR, name)
    except FileNotFoundError:
        return _bad("Look not found", 404)
    except (OSError, ValueError) as exc:
        return _bad(str(exc), 422)
    return jsonify({"ok": True, "look": look.to_dict()})


@api_show_bp.post("/api/looks/save")
def api_looks_save():
    payload = request.get_json(silent=True) or {}
    look = Look.from_dict(payload)
    if not look.name:
        return _bad("Missing look name")
    try:
        saved = save_look(LOOK_DIR, look)
    except (OSError, ValueError) as exc:
        return _bad(str(exc), 500)
    return jsonify({"ok": True, "saved": saved})


@api_show_bp.post("/api/looks/delete")
def api_looks_delete():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "")
    if delete_look(LOOK_DIR, name):
        return jsonify({"ok": True})
    return _bad("Look not found", 404)


@api_show_bp.post("/api/looks/apply")
def api_looks_apply():
    payload = request.get_json(silent=True) or {}
    # Either apply a saved look by name, or an inline look from the editor.
    if isinstance(payload.get("look"), dict):
        look = Look.from_dict(payload["look"])
        dmx.apply_look(resolve(look, dmx.patch))
        if look.fog:
            dmx.set_fog(**look.fog)
        scene_engine.active_look = look.name or None
        return jsonify({"ok": True, "active": scene_engine.status()})
    name = payload.get("name", "")
    if not name:
        return _bad("Missing look name")
    if scene_engine.show_look(name):
        return jsonify({"ok": True, "active": scene_engine.status()})
    return _bad(f"Could not apply look {name!r}", 422)


@api_show_bp.get("/api/simulation")
def api_simulation():
    """Current DMX state for the 3D simulation (all fixtures + fog)."""
    return jsonify({"ok": True, **dmx.snapshot()})


# ---------------------------------------------------------------------------
# Ableton link
# ---------------------------------------------------------------------------
@api_show_bp.get("/api/ableton/status")
def api_ableton_status():
    return jsonify(
        {
            "ok": True,
            "ableton": ableton.status(),
            "scenes": scene_engine.status(),
        }
    )


@api_show_bp.post("/api/ableton/connect")
def api_ableton_connect():
    started = ableton.start()
    if not started:
        return _bad("Could not open the OSC port 11001 (already in use?)", 500)
    return jsonify({"ok": True, "ableton": ableton.status()})


@api_show_bp.post("/api/ableton/disconnect")
def api_ableton_disconnect():
    ableton.stop()
    return jsonify({"ok": True, "ableton": ableton.status()})


# ---------------------------------------------------------------------------
# Scene mapping
# ---------------------------------------------------------------------------
@api_show_bp.get("/api/scenes")
def api_scenes_get():
    return jsonify(
        {
            "ok": True,
            "ableton": ableton.status(),
            "scenes": scene_engine.status(),
            "looks": list_looks(LOOK_DIR),
        }
    )


@api_show_bp.post("/api/scenes/mapping")
def api_scenes_set_mapping():
    payload = request.get_json(silent=True) or {}
    scene = payload.get("scene")
    if not scene:
        return _bad("Missing scene name")
    look = payload.get("look") or None
    scene_engine.set_mapping(str(scene), str(look) if look else None)
    return jsonify({"ok": True, "scenes": scene_engine.status()})


@api_show_bp.post("/api/scenes/enabled")
def api_scenes_enabled():
    payload = request.get_json(silent=True) or {}
    scene_engine.set_enabled(bool(payload.get("enabled", True)))
    return jsonify({"ok": True, "scenes": scene_engine.status()})


# ---------------------------------------------------------------------------
# Fog
# ---------------------------------------------------------------------------
@api_show_bp.post("/api/fog")
def api_fog():
    payload = request.get_json(silent=True) or {}
    dmx.set_fog(
        level=payload.get("level"),
        interval=payload.get("interval"),
        duration=payload.get("duration"),
    )
    return jsonify({"ok": True, "fog": dict(dmx.fog)})
