"""High-level DMX controller orchestrating the output thread.

The controller maintains the desired output state (RGB, amplitude, pan/tilt)
and a small state machine of "modes" (steady, strobe, random, audio-reactive,
procedural effects). A daemon thread translates that state into DMX frames and
pushes them through :class:`pydmxIcare.DMX_Icare` at a steady rate.
"""

from __future__ import annotations

import logging
import os
import random as _rnd
import sys
import threading
import time

# Local imports — make sure the project root is reachable
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import pydmxIcare  # noqa: E402

from .config import Channels, Timings, UserSettings  # noqa: E402

logger = logging.getLogger(__name__)


class DMXController:
    """Background DMX output engine.

    Modes (mutually exclusive, except for the *overlay* strobe which layers on
    top of any other mode):

    * ``steady``      — push the current RGB/amp/pan/tilt at ~20 Hz.
    * ``strobe``      — square-wave strobe with frequency + duty cycle.
    * ``random``      — random RGB colours at a configurable rate, optionally
                        smoothed with exponential interpolation.
    * ``effect``      — procedural built-in effect (rainbow, fire, police, chase).
    * ``audio``       — values are driven by client-side analysis and pushed
                        via :meth:`audio_push` (no internal generator).
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, settings: UserSettings | None = None) -> None:
        self.mydmx = pydmxIcare.DMX_Icare()
        self.settings = settings

        # ---- Mode flags ----
        self.enabled = False
        self.strobe_enabled = False
        self.random_enabled = False
        self.effect_enabled = False
        self.audio_enabled = False

        # ---- Strobe parameters ----
        self.freq = 60
        self.shuffle = 50

        # ---- Output values ----
        self.r = 0
        self.g = 0
        self.b = 0
        self.amp = 0
        self.pan = 0
        self.tilt = 0
        self.base_color_channel = (
            settings.base_color_channel if settings else Channels.BASE_COLOR_DEFAULT
        )

        # ---- Last error (surfaced via /api/health) ----
        self.last_error: str | None = None

        # ---- Thread management ----
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # Overlay strobe (non-destructive): toggles output on top of current values
        self.overlay = {
            "active": False,
            "freq_hz": 10.0,
            "duty": 0.5,
            "until": 0.0,
            "channel": 0,
        }

        # Random color mode
        self.random_params = {
            "freq_hz": 1.0,
            "smooth": 0.5,
            "brightness": 128,
        }
        self._random_target = (0, 0, 0)
        self._random_next = time.time()

        # Procedural effects
        self.effect_params = {
            "name": None,  # 'rainbow' | 'fire' | 'police' | 'chase'
            "speed": 1.0,  # arbitrary
            "brightness": 200,
        }
        self._effect_t0 = time.time()

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------
    def connection(self, port: str | None = None) -> bool:
        """Open the DMX serial connection. Re-raises on failure for the API."""
        try:
            self.mydmx.connection(port=port or None)
            self.last_error = None
            if self.settings is not None and port:
                self.settings.update(last_com_port=port)
            return True
        except Exception as exc:
            self.last_error = str(exc)
            raise

    @property
    def connected(self) -> bool:
        return self.mydmx.is_connected

    def health(self) -> dict:
        return {
            "connected": self.connected,
            "lastError": self.last_error,
            "modes": {
                "enabled": self.enabled,
                "strobe": self.strobe_enabled,
                "random": self.random_enabled,
                "effect": self.effect_enabled,
                "audio": self.audio_enabled,
                "overlayActive": bool(self.overlay.get("active")),
            },
        }

    # ------------------------------------------------------------------
    # Frame senders
    # ------------------------------------------------------------------
    def _send_current(self) -> None:
        try:
            self.mydmx.set_channel(Channels.MASTER, 255)
            self.mydmx.set_channel(Channels.SHUTTER, 0)
            self.mydmx.set_channel(Channels.AMPLITUDE, int(self.amp))
            base = int(self.base_color_channel)
            self.mydmx.set_channel(base + 0, int(self.r))
            self.mydmx.set_channel(base + 1, int(self.g))
            self.mydmx.set_channel(base + 2, int(self.b))
            self.mydmx.set_channel(Channels.PAN, int(self.pan))
            self.mydmx.set_channel(Channels.TILT, int(self.tilt))
            self.mydmx.send_data()
        except Exception:
            logger.exception("Error sending DMX frame")

    def _send_black(self) -> None:
        try:
            base = int(self.base_color_channel)
            self.mydmx.set_channel(Channels.AMPLITUDE, 0)
            self.mydmx.set_channel(base + 0, 0)
            self.mydmx.set_channel(base + 1, 0)
            self.mydmx.set_channel(base + 2, 0)
            self.mydmx.send_data()
        except Exception:
            logger.exception("Error sending blackout frame")

    def _send_with_overlay(self) -> None:
        now = time.time()
        if self.overlay["active"]:
            if now >= self.overlay["until"]:
                self.overlay["active"] = False
            else:
                phase = (now * float(self.overlay["freq_hz"])) % 1.0
                on_phase = phase < float(self.overlay["duty"])
                ch = int(self.overlay.get("channel", 0))
                if ch > 0:
                    try:
                        self._send_current()
                        self.mydmx.set_channel(ch, 255 if on_phase else 0)
                        self.mydmx.send_data()
                    except Exception:
                        logger.exception("Error applying overlay on channel %s", ch)
                    return
                if on_phase:
                    self._send_current()
                else:
                    self._send_black()
                return
        self._send_current()

    # ------------------------------------------------------------------
    # State setters
    # ------------------------------------------------------------------
    def set_values(
        self,
        r: int | None = None,
        g: int | None = None,
        b: int | None = None,
        amp: int | None = None,
        pan: int | None = None,
        tilt: int | None = None,
    ) -> None:
        if r is not None:
            self.r = max(0, min(255, int(r)))
        if g is not None:
            self.g = max(0, min(255, int(g)))
        if b is not None:
            self.b = max(0, min(255, int(b)))
        if amp is not None:
            self.amp = max(0, min(255, int(amp)))
        if pan is not None:
            self.pan = max(0, min(255, int(pan)))
        if tilt is not None:
            self.tilt = max(0, min(255, int(tilt)))
        self._send_current()

    def set_base_channel(self, base: int) -> None:
        base = int(base)
        if not 0 <= base <= 509:  # need room for base+2
            raise ValueError(f"base channel out of range (0..509): {base}")
        self.base_color_channel = base
        if self.settings is not None:
            self.settings.update(base_color_channel=base)

    # ------------------------------------------------------------------
    # Mode control
    # ------------------------------------------------------------------
    def _switch_mode(
        self, *, steady=False, strobe=False, random=False, effect=False, audio=False
    ) -> None:
        self.enabled = steady
        self.strobe_enabled = strobe
        self.random_enabled = random
        self.effect_enabled = effect
        self.audio_enabled = audio

    def start(self) -> None:
        self._switch_mode(steady=True)
        self._ensure_thread()

    def stop(self) -> None:
        self._switch_mode()
        self._stop_thread()

    def blackout(self) -> None:
        self._switch_mode()
        self.r = self.g = self.b = 0
        self.amp = 0
        try:
            base = int(self.base_color_channel)
            for offset in (0, 1, 2):
                self.mydmx.set_channel(base + offset, 0)
            self.mydmx.set_channel(Channels.AMPLITUDE, 0)
            self.mydmx.send_data()
        except Exception:
            logger.exception("Blackout failed")

    def strobe(self, freq: int, shuffle: int = 50) -> None:
        self.freq = max(1, int(freq))
        self.shuffle = max(0, min(100, int(shuffle)))
        self._switch_mode(strobe=True)
        self._ensure_thread()

    # ---- Random ----
    def random_config(
        self,
        freq_hz: float | None = None,
        smooth: float | None = None,
        brightness: int | None = None,
    ) -> None:
        try:
            if freq_hz is not None:
                self.random_params["freq_hz"] = max(0.1, float(freq_hz))
            if smooth is not None:
                self.random_params["smooth"] = max(0.0, min(1.0, float(smooth)))
            if brightness is not None:
                self.random_params["brightness"] = max(0, min(255, int(brightness)))
        except (TypeError, ValueError) as exc:
            logger.warning("Invalid random config payload: %s", exc)

    def random_start(self) -> None:
        self._switch_mode(random=True)
        self._ensure_thread()

    def random_stop(self) -> None:
        self.random_enabled = False

    # ---- Procedural effects ----
    def effect_start(self, name: str, speed: float = 1.0, brightness: int = 200) -> None:
        if name not in {"rainbow", "fire", "police", "chase"}:
            raise ValueError(f"unknown effect: {name}")
        self.effect_params["name"] = name
        self.effect_params["speed"] = max(0.05, float(speed))
        self.effect_params["brightness"] = max(0, min(255, int(brightness)))
        self._switch_mode(effect=True)
        self._effect_t0 = time.time()
        self._ensure_thread()

    def effect_stop(self) -> None:
        self.effect_enabled = False
        self.effect_params["name"] = None

    # ---- Audio-reactive (driven from client) ----
    def audio_start(self) -> None:
        self._switch_mode(audio=True)
        self._ensure_thread()

    def audio_stop(self) -> None:
        self.audio_enabled = False

    def audio_push(self, level: float, color_hex: str | None = None) -> None:
        """Apply a single audio sample. ``level`` is in [0..1]."""
        if not self.audio_enabled:
            return
        level = max(0.0, min(1.0, float(level)))
        if color_hex:
            try:
                hx = color_hex.lstrip("#")
                self.r = int(hx[0:2], 16)
                self.g = int(hx[2:4], 16)
                self.b = int(hx[4:6], 16)
            except (ValueError, IndexError):
                pass
        self.amp = int(level * 255)
        self._send_with_overlay()

    # ------------------------------------------------------------------
    # Thread management
    # ------------------------------------------------------------------
    def _ensure_thread(self) -> None:
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True, name="dmx-out")
            self._thread.start()

    def _stop_thread(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=1.5)
        self._thread = None

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def _run(self) -> None:  # noqa: C901 - intentional state machine
        while not self._stop_event.is_set():
            try:
                if self.enabled:
                    self._send_with_overlay()
                    time.sleep(Timings.STEADY_LOOP)
                elif self.strobe_enabled:
                    self._step_strobe()
                elif self.random_enabled:
                    self._step_random()
                elif self.effect_enabled:
                    self._step_effect()
                elif self.audio_enabled:
                    # Audio mode is push-driven; keep the loop alive cheaply
                    time.sleep(Timings.IDLE_LOOP)
                else:
                    time.sleep(Timings.IDLE_LOOP)
            except Exception:
                logger.exception("DMX loop error; pausing 0.5 s")
                time.sleep(0.5)

    def _step_strobe(self) -> None:
        self._send_with_overlay()
        on_time = max(0.001, 60 / self.freq * (self.shuffle / 100))
        time.sleep(on_time)
        # Off period
        try:
            base = int(self.base_color_channel)
            self.mydmx.set_channel(base + 0, 0)
            self.mydmx.set_channel(base + 1, 0)
            self.mydmx.set_channel(base + 2, 0)
            self.mydmx.send_data()
        except Exception:
            logger.exception("Strobe off-frame failed")
        off_time = max(0.001, 60 / max(1, self.freq) * (1 - self.shuffle / 100))
        time.sleep(off_time)

    def _step_random(self) -> None:
        now = time.time()
        if now >= self._random_next:
            self._random_target = (
                _rnd.randint(0, 255),
                _rnd.randint(0, 255),
                _rnd.randint(0, 255),
            )
            self._random_next = now + (1.0 / max(0.1, self.random_params["freq_hz"]))
        smooth = float(self.random_params.get("smooth", 0.0))
        if smooth <= 0.01:
            self.r, self.g, self.b = self._random_target
        else:
            alpha = max(0.01, min(0.35, smooth * 0.18))
            self.r = int(self.r + alpha * (self._random_target[0] - self.r))
            self.g = int(self.g + alpha * (self._random_target[1] - self.g))
            self.b = int(self.b + alpha * (self._random_target[2] - self.b))
        self.amp = int(self.random_params.get("brightness", 128))
        self._send_with_overlay()
        time.sleep(Timings.RANDOM_LOOP)

    # ---- Procedural effects ----
    def _step_effect(self) -> None:
        name = self.effect_params.get("name")
        speed = float(self.effect_params.get("speed", 1.0))
        bright = int(self.effect_params.get("brightness", 200))
        t = (time.time() - self._effect_t0) * speed

        if name == "rainbow":
            r, g, b = self._hsv_to_rgb((t * 60) % 360, 1.0, 1.0)
        elif name == "fire":
            # warm flicker around orange/red
            base_h = 18 + (_rnd.random() - 0.5) * 12
            v = 0.55 + 0.45 * _rnd.random()
            r, g, b = self._hsv_to_rgb(base_h, 1.0, v)
        elif name == "police":
            phase = int(t * 4) % 2
            r, g, b = (255, 0, 0) if phase == 0 else (0, 0, 255)
        elif name == "chase":
            # Cycle through R, G, B
            phase = int(t * 3) % 3
            r, g, b = [(255, 0, 0), (0, 255, 0), (0, 0, 255)][phase]
        else:
            time.sleep(Timings.IDLE_LOOP)
            return

        self.r, self.g, self.b = int(r), int(g), int(b)
        self.amp = bright
        self._send_with_overlay()
        time.sleep(Timings.EFFECT_LOOP)

    @staticmethod
    def _hsv_to_rgb(h: float, s: float, v: float) -> tuple:
        # h in [0..360), s/v in [0..1]
        h = h % 360
        c = v * s
        x = c * (1 - abs(((h / 60) % 2) - 1))
        m = v - c
        if h < 60:
            r1, g1, b1 = c, x, 0
        elif h < 120:
            r1, g1, b1 = x, c, 0
        elif h < 180:
            r1, g1, b1 = 0, c, x
        elif h < 240:
            r1, g1, b1 = 0, x, c
        elif h < 300:
            r1, g1, b1 = x, 0, c
        else:
            r1, g1, b1 = c, 0, x
        return int((r1 + m) * 255), int((g1 + m) * 255), int((b1 + m) * 255)
