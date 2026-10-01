"""Direct (Experiment) tab REST API."""

from __future__ import annotations

import logging
import time

from flask import Blueprint, jsonify, request

from .services import dmx

logger = logging.getLogger(__name__)
api_experiment_bp = Blueprint("api_experiment", __name__)


def _bad_request(msg: str, code: int = 400):
    return jsonify({"ok": False, "error": msg}), code


# ---------------------------------------------------------------------------
# Connection / base channel
# ---------------------------------------------------------------------------
@api_experiment_bp.post("/api/experiment/connect")
def api_connect():
    data = request.get_json(silent=True) or {}
    base = data.get("baseChannel")
    port = data.get("port")
    if base is not None:
        try:
            dmx.set_base_channel(base)
        except (ValueError, TypeError) as exc:
            return _bad_request(f"Invalid baseChannel: {exc}")
    try:
        dmx.connection(port=port)
    except Exception as exc:
        logger.warning("DMX connection failed: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 503
    return jsonify({"ok": True, "baseChannel": dmx.base_color_channel, "connected": dmx.connected})


@api_experiment_bp.post("/api/experiment/base-channel")
def api_experiment_base_channel():
    data = request.get_json(silent=True) or {}
    base = data.get("baseChannel")
    if base is None:
        return _bad_request("Missing baseChannel")
    try:
        dmx.set_base_channel(base)
    except (ValueError, TypeError) as exc:
        return _bad_request(f"Invalid baseChannel: {exc}")
    return jsonify({"ok": True, "baseChannel": dmx.base_color_channel})


# ---------------------------------------------------------------------------
# Slider values + transport
# ---------------------------------------------------------------------------
@api_experiment_bp.post("/api/experiment/set-values")
def api_set_values():
    data = request.get_json(silent=True) or {}
    dmx.set_values(
        r=data.get("r"),
        g=data.get("g"),
        b=data.get("b"),
        amp=data.get("amp"),
        pan=data.get("pan"),
        tilt=data.get("tilt"),
    )
    return jsonify({"ok": True})


@api_experiment_bp.post("/api/experiment/start")
def api_start():
    dmx.start()
    return jsonify({"ok": True})


@api_experiment_bp.post("/api/experiment/stop")
def api_stop():
    dmx.stop()
    return jsonify({"ok": True})


@api_experiment_bp.post("/api/experiment/blackout")
def api_blackout():
    dmx.blackout()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------
@api_experiment_bp.post("/api/experiment/strobe")
def api_strobe():
    data = request.get_json(silent=True) or {}
    try:
        freq = int(data.get("freq", 60))
        shuffle = int(data.get("shuffle", 50))
    except (TypeError, ValueError) as exc:
        return _bad_request(f"Invalid strobe params: {exc}")
    dmx.strobe(freq=freq, shuffle=shuffle)
    return jsonify({"ok": True})


@api_experiment_bp.post("/api/experiment/random")
def api_random():
    data = request.get_json(silent=True) or {}
    dmx.random_config(
        freq_hz=data.get("freqHz"),
        smooth=data.get("smooth"),
        brightness=data.get("brightness"),
    )
    dmx.random_start()
    return jsonify({"ok": True, "random": dmx.random_params})


@api_experiment_bp.post("/api/experiment/mode/random-config")
def api_experiment_random_config():
    data = request.get_json(silent=True) or {}
    dmx.random_config(
        freq_hz=data.get("freqHz"),
        smooth=data.get("smooth"),
        brightness=data.get("brightness"),
    )
    return jsonify({"ok": True, "random": dmx.random_params})


@api_experiment_bp.post("/api/experiment/random-start")
def api_experiment_random_start():
    dmx.random_start()
    return jsonify({"ok": True})


@api_experiment_bp.post("/api/experiment/random-stop")
def api_experiment_random_stop():
    dmx.random_stop()
    return jsonify({"ok": True})


@api_experiment_bp.post("/api/experiment/mode/strobe-overlay")
def api_experiment_strobe_overlay():
    data = request.get_json(silent=True) or {}
    try:
        freq_hz = float(data.get("freqHz", 10.0))
        duty = float(data.get("duty", 0.5))
        duration = float(data.get("durationSec", 5.0))
        channel = int(data.get("channel", 0))
    except (TypeError, ValueError) as exc:
        return _bad_request(f"Invalid overlay params: {exc}")
    dmx.overlay = {
        "active": True,
        "freq_hz": max(0.1, freq_hz),
        "duty": max(0.0, min(1.0, duty)),
        "until": time.time() + max(0.0, duration),
        "channel": max(0, channel),
    }
    return jsonify({"ok": True, "overlay": dmx.overlay})


# ---- Procedural effects (rainbow / fire / police / chase) ----
@api_experiment_bp.post("/api/experiment/effect/start")
def api_effect_start():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    try:
        speed = float(data.get("speed", 1.0))
        brightness = int(data.get("brightness", 200))
    except (TypeError, ValueError) as exc:
        return _bad_request(f"Invalid effect params: {exc}")
    if not name:
        return _bad_request("Missing effect name")
    try:
        dmx.effect_start(name, speed=speed, brightness=brightness)
    except ValueError as exc:
        return _bad_request(str(exc))
    return jsonify({"ok": True, "effect": dmx.effect_params})


@api_experiment_bp.post("/api/experiment/effect/stop")
def api_effect_stop():
    dmx.effect_stop()
    return jsonify({"ok": True})


# ---- Audio-reactive (push from client) ----
@api_experiment_bp.post("/api/experiment/audio/start")
def api_audio_start():
    dmx.audio_start()
    return jsonify({"ok": True})


@api_experiment_bp.post("/api/experiment/audio/stop")
def api_audio_stop():
    dmx.audio_stop()
    return jsonify({"ok": True})


@api_experiment_bp.post("/api/experiment/audio/push")
def api_audio_push():
    data = request.get_json(silent=True) or {}
    try:
        level = float(data.get("level", 0))
    except (TypeError, ValueError):
        level = 0.0
    color = data.get("color")
    dmx.audio_push(level=level, color_hex=color)
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Status (polled by the front-end)
# ---------------------------------------------------------------------------
@api_experiment_bp.get("/api/experiment/status")
def api_experiment_status():
    return jsonify(
        {
            "ok": True,
            "state": {
                "r": dmx.r,
                "g": dmx.g,
                "b": dmx.b,
                "amp": dmx.amp,
                "pan": dmx.pan,
                "tilt": dmx.tilt,
                "overlay": dmx.overlay,
                "random": {"enabled": dmx.random_enabled, **dmx.random_params},
                "effect": {"enabled": dmx.effect_enabled, **dmx.effect_params},
                "audio": {"enabled": dmx.audio_enabled},
                "connected": dmx.connected,
            },
        }
    )
