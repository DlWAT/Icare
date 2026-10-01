"""Multi-fixture DMX engine.

The controller owns the DMX patch (see :mod:`webapp.fixtures`) and a daemon
thread that turns the current *mode* into a full 512-channel frame.

Modes (mutually exclusive, except for the *overlay* strobe which layers on top
of any other mode):

* ``steady``  — push the master RGB/amp at ~20 Hz.
* ``strobe``  — square-wave strobe with frequency + duty cycle.
* ``random``  — random RGB colours at a configurable rate, optionally smoothed.
* ``effect``  — procedural built-in effect (rainbow, fire, police, chase).
* ``audio``   — values are pushed from the client via :meth:`audio_push`.
* ``look``    — a static per-fixture state (used by the Ableton scene engine).

Every generative mode is applied to the **whole patch**: a fixture with a
dimmer channel receives it directly, a fixture without one has its colour
channels scaled by the amplitude instead.
"""

from __future__ import annotations

import logging
import os
import random as _rnd
import sys
import threading
import time
from collections.abc import Iterable
from typing import Any

# Local imports — make sure the project root is reachable
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import pydmxIcare  # noqa: E402

from .config import Channels, Timings, UserSettings  # noqa: E402
from .fixtures import (  # noqa: E402
    DIMMER,
    DIMMER_FINE,
    FOG,
    FOG_DURATION,
    FOG_INTERVAL,
    STROBE,
    A,
    B,
    Fixture,
    G,
    R,
    W,
    default_patch,
    validate_patch,
)

logger = logging.getLogger(__name__)

UNIVERSE_SIZE = 512


def _clamp(value: Any, lo: int = 0, hi: int = 255) -> int:
    try:
        v = int(value)
    except (TypeError, ValueError):
        return lo
    return max(lo, min(hi, v))


class DMXController:
    """Background DMX output engine driving a whole patch of fixtures."""

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(
        self,
        settings: UserSettings | None = None,
        patch: Iterable[Fixture] | None = None,
    ) -> None:
        self.mydmx = pydmxIcare.DMX_Icare()
        self.settings = settings

        self.patch: list[Fixture] = validate_patch(list(patch) if patch else default_patch())

        # ---- Mode flags ----
        self.enabled = False
        self.strobe_enabled = False
        self.random_enabled = False
        self.effect_enabled = False
        self.audio_enabled = False
        self.look_enabled = False

        # ---- Strobe parameters ----
        self.freq = 60
        self.shuffle = 50

        # ---- Master output values (applied to the whole patch) ----
        self.r = 0
        self.g = 0
        self.b = 0
        self.w = 0
        self.a = 0
        self.amp = 0
        self.pan = 0
        self.tilt = 0
        # Legacy single-fixture base channel (kept for API compatibility).
        self.base_color_channel = (
            settings.base_color_channel if settings else Channels.BASE_COLOR_DEFAULT
        )

        # ---- Fog machine (independent of the light modes) ----
        self.fog: dict[str, int] = {"level": 0, "interval": 0, "duration": 0}

        # ---- Current look (per-fixture static state) ----
        self._look_state: dict[str, dict[str, int]] = {}

        # ---- Last error (surfaced via /api/health) ----
        self.last_error: str | None = None

        # ---- Thread management ----
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # Overlay strobe (non-destructive): toggles output on top of current values
        self.overlay: dict[str, Any] = {
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
        self.effect_params: dict[str, Any] = {
            "name": None,  # 'rainbow' | 'fire' | 'police' | 'chase'
            "speed": 1.0,
            "brightness": 200,
        }
        self._effect_t0 = time.time()

    # ------------------------------------------------------------------
    # Patch
    # ------------------------------------------------------------------
    def set_patch(self, patch: Iterable[Fixture]) -> None:
        """Replace the patch (validates first)."""
        self.patch = validate_patch(patch)
        self._look_state = {}
        self._render_with_overlay()

    def fixture_names(self) -> list[str]:
        return [fx.name for fx in self.patch]

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
            "fixtures": len(self.patch),
            "modes": {
                "enabled": self.enabled,
                "strobe": self.strobe_enabled,
                "random": self.random_enabled,
                "effect": self.effect_enabled,
                "audio": self.audio_enabled,
                "look": self.look_enabled,
                "overlayActive": bool(self.overlay.get("active")),
            },
        }

    # ------------------------------------------------------------------
    # Frame composition
    # ------------------------------------------------------------------
    def _write_color(
        self,
        values: dict[int, int],
        fx: Fixture,
        r: int,
        g: int,
        b: int,
        w: int,
        a: int,
        amp: int,
        strobe: int = 0,
    ) -> None:
        """Write one fixture's colour according to its profile."""
        prof = fx.profile_obj
        fns = prof.functions()
        has_dimmer = DIMMER in fns
        scale = 1.0 if has_dimmer else _clamp(amp) / 255.0

        def sc(v: int) -> int:
            return _clamp(round(v * scale))

        if has_dimmer:
            values[fx.address + prof.index_of(DIMMER)] = _clamp(amp)
        if DIMMER_FINE in fns:
            values[fx.address + prof.index_of(DIMMER_FINE)] = 0
        if R in fns:
            values[fx.address + prof.index_of(R)] = sc(r)
        if G in fns:
            values[fx.address + prof.index_of(G)] = sc(g)
        if B in fns:
            values[fx.address + prof.index_of(B)] = sc(b)
        if W in fns:
            values[fx.address + prof.index_of(W)] = sc(w)
        if A in fns:
            values[fx.address + prof.index_of(A)] = sc(a)
        if STROBE in fns:
            values[fx.address + prof.index_of(STROBE)] = _clamp(strobe)
        # sound / macro / color_temp deliberately left at 0

    def _compose_fog(self, values: dict[int, int]) -> None:
        for fx in self.patch:
            prof = fx.profile_obj
            fns = prof.functions()
            if FOG in fns:
                values[fx.address + prof.index_of(FOG)] = _clamp(self.fog["level"])
            if FOG_INTERVAL in fns:
                values[fx.address + prof.index_of(FOG_INTERVAL)] = _clamp(self.fog["interval"])
            if FOG_DURATION in fns:
                values[fx.address + prof.index_of(FOG_DURATION)] = _clamp(self.fog["duration"])

    def _compose_look(self, values: dict[int, int]) -> None:
        for fx in self.patch:
            state = self._look_state.get(fx.name)
            if not state:
                continue
            prof = fx.profile_obj
            for i, ch in enumerate(prof.channels):
                if ch.fn in state:
                    values[fx.address + i] = _clamp(state[ch.fn])

    def _compose_generative(self, values: dict[int, int], strobe: int = 0) -> None:
        for fx in self.patch:
            self._write_color(
                values,
                fx,
                self.r,
                self.g,
                self.b,
                self.w,
                self.a,
                self.amp,
                strobe=strobe,
            )

    def _compose(self, black: bool = False, strobe: int = 0) -> dict[int, int]:
        values: dict[int, int] = {}
        if not black:
            if self.look_enabled:
                self._compose_look(values)
            else:
                self._compose_generative(values, strobe=strobe)
        self._compose_fog(values)
        return values

    def _apply(self, values: dict[int, int], extra: dict[int, int] | None = None) -> None:
        try:
            data = self.mydmx.data
            data[:] = 0
            for addr, val in values.items():
                if 0 <= addr < UNIVERSE_SIZE:
                    data[addr] = _clamp(val)
            if extra:
                for addr, val in extra.items():
                    if 0 <= addr < UNIVERSE_SIZE:
                        data[addr] = _clamp(val)
            self.mydmx.send_data()
        except Exception:
            logger.exception("Error sending DMX frame")

    # ------------------------------------------------------------------
    # Overlay + send
    # ------------------------------------------------------------------
    def _render_with_overlay(self, strobe: int = 0) -> None:
        now = time.time()
        if self.overlay.get("active"):
            if now >= self.overlay["until"]:
                self.overlay["active"] = False
            else:
                phase = (now * float(self.overlay["freq_hz"])) % 1.0
                on_phase = phase < float(self.overlay["duty"])
                ch = int(self.overlay.get("channel", 0))
                if ch > 0:
                    self._apply(
                        self._compose(strobe=strobe),
                        extra={ch: 255 if on_phase else 0},
                    )
                    return
                self._apply(self._compose(black=not on_phase, strobe=strobe))
                return
        self._apply(self._compose(strobe=strobe))

    # ------------------------------------------------------------------
    # Simulation snapshot
    # ------------------------------------------------------------------
    def snapshot(self) -> dict:
        """Return the current per-fixture channel values (for the 3D stage)."""
        values = self._compose()
        fixtures = []
        for fx in self.patch:
            prof = fx.profile_obj
            state = {
                ch.fn: int(values.get(fx.address + i, 0)) for i, ch in enumerate(prof.channels)
            }
            fixtures.append(
                {
                    "name": fx.name,
                    "group": fx.group,
                    "profile": fx.profile,
                    "x": fx.x,
                    "z": fx.z,
                    "angle": fx.angle,
                    "beamAngle": prof.beam_angle,
                    "values": state,
                }
            )
        return {
            "fixtures": fixtures,
            "fog": dict(self.fog),
            "master": {
                "r": self.r,
                "g": self.g,
                "b": self.b,
                "w": self.w,
                "a": self.a,
                "amp": self.amp,
            },
            "modes": {
                "steady": self.enabled,
                "strobe": self.strobe_enabled,
                "random": self.random_enabled,
                "effect": self.effect_enabled,
                "audio": self.audio_enabled,
                "look": self.look_enabled,
            },
            "connected": self.connected,
        }

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
        w: int | None = None,
        a: int | None = None,
    ) -> None:
        if r is not None:
            self.r = _clamp(r)
        if g is not None:
            self.g = _clamp(g)
        if b is not None:
            self.b = _clamp(b)
        if w is not None:
            self.w = _clamp(w)
        if a is not None:
            self.a = _clamp(a)
        if amp is not None:
            self.amp = _clamp(amp)
        if pan is not None:
            self.pan = _clamp(pan)
        if tilt is not None:
            self.tilt = _clamp(tilt)
        self._render_with_overlay()

    def set_fog(
        self,
        level: int | None = None,
        interval: int | None = None,
        duration: int | None = None,
    ) -> None:
        if level is not None:
            self.fog["level"] = _clamp(level)
        if interval is not None:
            self.fog["interval"] = _clamp(interval)
        if duration is not None:
            self.fog["duration"] = _clamp(duration)
        self._render_with_overlay()

    def set_base_channel(self, base: int) -> None:
        """Legacy single-fixture API — kept so old clients keep working."""
        base = int(base)
        if not 0 <= base <= 509:
            raise ValueError(f"base channel out of range (0..509): {base}")
        self.base_color_channel = base
        if self.settings is not None:
            self.settings.update(base_color_channel=base)

    # ------------------------------------------------------------------
    # Mode control
    # ------------------------------------------------------------------
    def _switch_mode(
        self,
        *,
        steady: bool = False,
        strobe: bool = False,
        random: bool = False,
        effect: bool = False,
        audio: bool = False,
        look: bool = False,
    ) -> None:
        self.enabled = steady
        self.strobe_enabled = strobe
        self.random_enabled = random
        self.effect_enabled = effect
        self.audio_enabled = audio
        self.look_enabled = look

    def start(self) -> None:
        self._switch_mode(steady=True)
        self._ensure_thread()

    def stop(self) -> None:
        self._switch_mode()
        self._stop_thread()

    def blackout(self) -> None:
        self._switch_mode()
        self.r = self.g = self.b = self.w = self.a = 0
        self.amp = 0
        self.fog["level"] = 0
        self._look_state = {}
        self._render_with_overlay()

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
                self.random_params["brightness"] = _clamp(brightness)
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
        self.effect_params["brightness"] = _clamp(brightness)
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
        self._render_with_overlay()

    # ------------------------------------------------------------------
    # Looks
    # ------------------------------------------------------------------
    def apply_look(self, fixture_states: dict[str, dict[str, int]]) -> None:
        """Show a static per-fixture state (used by the scene engine)."""
        self._look_state = {k: dict(v) for k, v in fixture_states.items()}
        self._switch_mode(look=True)
        self._ensure_thread()
        self._render_with_overlay()

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
                    self._render_with_overlay()
                    time.sleep(Timings.STEADY_LOOP)
                elif self.look_enabled:
                    self._render_with_overlay()
                    time.sleep(Timings.STEADY_LOOP)
                elif self.strobe_enabled:
                    self._step_strobe()
                elif self.random_enabled:
                    self._step_random()
                elif self.effect_enabled:
                    self._step_effect()
                elif self.audio_enabled:
                    time.sleep(Timings.IDLE_LOOP)
                else:
                    time.sleep(Timings.IDLE_LOOP)
            except Exception:
                logger.exception("DMX loop error; pausing 0.5 s")
                time.sleep(0.5)

    def _step_strobe(self) -> None:
        self._render_with_overlay(strobe=255)
        on_time = max(0.001, 60 / self.freq * (self.shuffle / 100))
        time.sleep(on_time)
        # Off period: black out the lights (keep fog).
        self._apply(self._compose(black=True, strobe=0))
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
        self.amp = _clamp(self.random_params.get("brightness", 128))
        self._render_with_overlay()
        time.sleep(Timings.RANDOM_LOOP)

    def _step_effect(self) -> None:
        name = self.effect_params.get("name")
        speed = float(self.effect_params.get("speed", 1.0))
        bright = _clamp(self.effect_params.get("brightness", 200))
        t = (time.time() - self._effect_t0) * speed

        if name == "rainbow":
            r, g, b = self._hsv_to_rgb((t * 60) % 360, 1.0, 1.0)
        elif name == "fire":
            base_h = 18 + (_rnd.random() - 0.5) * 12
            v = 0.55 + 0.45 * _rnd.random()
            r, g, b = self._hsv_to_rgb(base_h, 1.0, v)
        elif name == "police":
            phase = int(t * 4) % 2
            r, g, b = (255, 0, 0) if phase == 0 else (0, 0, 255)
        elif name == "chase":
            phase = int(t * 3) % 3
            r, g, b = [(255, 0, 0), (0, 255, 0), (0, 0, 255)][phase]
        else:
            time.sleep(Timings.IDLE_LOOP)
            return

        self.r, self.g, self.b = int(r), int(g), int(b)
        self.amp = bright
        self._render_with_overlay()
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
