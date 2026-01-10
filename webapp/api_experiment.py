from flask import Blueprint, request, jsonify
import time

from .services import dmx

api_experiment_bp = Blueprint("api_experiment", __name__)

@api_experiment_bp.post("/api/experiment/connect")
def api_connect():
    try:
        data = request.get_json(silent=True) or {}
        base = data.get("baseChannel")
        if base is not None:
            try:
                dmx.base_color_channel = int(base)
            except Exception:
                pass
        dmx.connection()
        return jsonify({"ok": True, "baseChannel": dmx.base_color_channel})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@api_experiment_bp.post("/api/experiment/base-channel")
def api_experiment_base_channel():
    data = request.get_json(force=True) or {}
    base = data.get("baseChannel")
    if base is None:
        return jsonify({"ok": False, "error": "Missing baseChannel"}), 400
    try:
        dmx.base_color_channel = int(base)
        return jsonify({"ok": True, "baseChannel": dmx.base_color_channel})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@api_experiment_bp.post("/api/experiment/set-values")
def api_set_values():
    data = request.get_json(force=True) or {}
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


@api_experiment_bp.post("/api/experiment/strobe")
def api_strobe():
    data = request.get_json(force=True) or {}
    freq = int(data.get("freq", 60))
    shuffle = int(data.get("shuffle", 50))
    dmx.strobe_random_enabled = False
    dmx.strobe(freq=freq, shuffle=shuffle)
    return jsonify({"ok": True})


@api_experiment_bp.post("/api/experiment/random")
def api_random():
    # Backward compatible: can accept parameters
    data = request.get_json(force=True) or {}
    dmx.random_config(
        freq_hz=data.get("freqHz"),
        smooth=data.get("smooth"),
        brightness=data.get("brightness"),
    )
    dmx.random_start()
    return jsonify({"ok": True, "random": dmx.random_params})


@api_experiment_bp.post("/api/experiment/strobe-random")
def api_strobe_random():
    # Deprecated in UI: keep endpoint for compatibility but return error
    return jsonify({"ok": False, "error": "strobe-random mode deprecated; use strobe-overlay."}), 400


@api_experiment_bp.get("/api/experiment/status")
def api_experiment_status():
    return jsonify({
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
        }
    })


@api_experiment_bp.post("/api/experiment/mode/strobe-overlay")
def api_experiment_strobe_overlay():
    data = request.get_json(force=True) or {}
    freq_hz = float(data.get("freqHz", 10.0))
    duty = float(data.get("duty", 0.5))
    duration = float(data.get("durationSec", 5.0))
    channel = int(data.get("channel", 0))
    dmx.overlay = {
        "active": True,
        "freq_hz": max(0.1, freq_hz),
        "duty": max(0.0, min(1.0, duty)),
        "until": time.time() + max(0.0, duration),
        "channel": max(0, channel),
    }
    return jsonify({"ok": True, "overlay": dmx.overlay})


@api_experiment_bp.post("/api/experiment/mode/random-config")
def api_experiment_random_config():
    data = request.get_json(force=True) or {}
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
