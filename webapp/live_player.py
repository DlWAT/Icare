"""Live sequence player.

Walks through the rows of a parsed sequence (see ``schemas.py``) at a
configurable rate (``freq`` is **BPM** here — beats per minute, one beat per
row) and translates each cell into DMX values via the shared controller.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from .dsl import (
    ContinueEffect,
    DSLError,
    Effect,
    FadeEffect,
    StrobeEffect,
    UniformEffect,
    parse,
)
from .schemas import normalize_sequence
from .services import dmx

logger = logging.getLogger(__name__)


class LivePlayer:
    """Plays a parsed sequence beat-by-beat in a daemon thread."""

    def __init__(self) -> None:
        self.data: dict[str, Any] | None = None
        self.bpm: int = 60
        self.index: int = 0
        self.playing: bool = False
        self.paused: bool = False
        self.selected_modules: set[str] = set()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # Visualization state
        self.current_rgb = (0, 0, 0)

        # Per-module continuation state for multi-step effects
        # key = module name -> dict(mode, length, step, c1, c2, freq, toggle)
        self._effect_state: dict[str, dict[str, Any]] = {}

        # Tap-tempo support: timestamps of recent taps (seconds)
        self._taps: list[float] = []
        self._taps_lock = threading.Lock()
        self.TAP_WINDOW = 3.0  # discard taps older than 3 s

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def load(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize and load a sequence dict. Returns the normalized version."""
        data = normalize_sequence(raw)
        self.data = data
        self.index = 0
        self.playing = False
        self.paused = False
        self.selected_modules = set()
        self.current_rgb = (0, 0, 0)
        self._effect_state.clear()
        return data

    # ------------------------------------------------------------------
    # Transport
    # ------------------------------------------------------------------
    def start(self, bpm: int | None = None) -> None:
        if bpm:
            self.bpm = max(1, int(bpm))
        self.playing = True
        self.paused = False
        self._ensure_thread()

    def pause(self) -> None:
        self.paused = not self.paused

    def stop(self) -> None:
        self.playing = False
        self.paused = False
        self.index = 0
        self._effect_state.clear()

    def next(self) -> None:
        if not self.data:
            return
        self.index = min(self.index + 1, len(self.data.get("data", {})))

    def prev(self) -> None:
        self.index = max(self.index - 1, 0)

    # ------------------------------------------------------------------
    # Modules
    # ------------------------------------------------------------------
    def toggle_module(self, name: str) -> None:
        if name in self.selected_modules:
            self.selected_modules.remove(name)
        else:
            self.selected_modules.add(name)

    def select_all(self) -> None:
        if not self.data:
            return
        self.selected_modules = set(self.data.get("Header", {}).get("Modules", []))

    def unselect_all(self) -> None:
        self.selected_modules.clear()

    # ------------------------------------------------------------------
    # Tap-tempo
    # ------------------------------------------------------------------
    def tap(self) -> int | None:
        """Register a tap; once 2+ taps are within the window, return the
        derived BPM and apply it.
        """
        now = time.monotonic()
        with self._taps_lock:
            # Drop taps older than window
            self._taps = [t for t in self._taps if now - t < self.TAP_WINDOW]
            self._taps.append(now)
            if len(self._taps) < 2:
                return None
            intervals = [b - a for a, b in zip(self._taps, self._taps[1:], strict=False)]
            avg = sum(intervals) / len(intervals)
            if avg <= 0:
                return None
            bpm = int(round(60 / avg))
        bpm = max(20, min(300, bpm))
        self.bpm = bpm
        return bpm

    def reset_taps(self) -> None:
        with self._taps_lock:
            self._taps.clear()

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    def status(self) -> dict[str, Any]:
        total = len(self.data.get("data", {})) if self.data else 0
        current_section = None
        if self.data and self.index > 0 and str(self.index) in self.data["data"]:
            current_section = self.data["data"][str(self.index)].get("section")
        pct = int(100 * self.index / total) if total else 0
        return {
            "playing": self.playing,
            "paused": self.paused,
            "index": self.index,
            "total": total,
            "progress": pct,
            "section": current_section,
            "selected": sorted(self.selected_modules),
            "bpm": self.bpm,
            "rgb": {
                "r": int(self.current_rgb[0]),
                "g": int(self.current_rgb[1]),
                "b": int(self.current_rgb[2]),
            },
            "beamAngle": 45,
        }

    # ------------------------------------------------------------------
    # Thread management
    # ------------------------------------------------------------------
    def _ensure_thread(self) -> None:
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True, name="live-player")
            self._thread.start()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def _run(self) -> None:
        while not self._stop_event.is_set():
            if self.playing and not self.paused and self.data:
                total = len(self.data.get("data", {}))
                if total == 0:
                    time.sleep(0.25)
                    continue
                # Advance index, wrap at end
                self.index = min(self.index + 1, total)
                line_key = str(self.index)
                line = self.data["data"].get(line_key, {})
                funcs = line.get("function", [])
                self._apply_step(funcs)
                # one row per beat at the chosen BPM
                time.sleep(60.0 / max(1, self.bpm))
                if self.index >= total:
                    # Hold last frame, then stop playing
                    self.playing = False
            else:
                time.sleep(0.2)

    # ------------------------------------------------------------------
    # Effect application
    # ------------------------------------------------------------------
    def _apply_step(self, funcs: list[str]) -> None:
        if not self.data:
            return
        modules: list[str] = self.data.get("Header", {}).get("Modules", [])

        # If user selected modules, apply to those; else apply to all
        targets = list(self.selected_modules) if self.selected_modules else list(modules)

        # We compute the colour of *one* representative module for the
        # visualisation (the first selected, or the first module of the show).
        first_target = targets[0] if targets else None

        for mod in targets:
            if mod not in modules:
                continue
            idx = modules.index(mod)
            token = funcs[idx] if idx < len(funcs) else ""
            try:
                effect = parse(token) if isinstance(token, str) else None
            except DSLError as exc:
                logger.warning("DSL error on module %s line %s: %s", mod, self.index, exc)
                effect = None
            rgb = self._step_effect_for(mod, effect)
            if mod == first_target and rgb is not None:
                self.current_rgb = rgb

        # Push the representative colour to DMX (single-fixture controller)
        if first_target is not None:
            r, g, b = self.current_rgb
            dmx.set_values(r=int(r), g=int(g), b=int(b))

    def _step_effect_for(self, module: str, effect: Effect):
        """Update per-module effect state and return the colour to apply."""
        state = self._effect_state.get(module)

        if isinstance(effect, UniformEffect):
            self._effect_state[module] = {"mode": "uni", "color": effect.color}
            return effect.color

        if isinstance(effect, FadeEffect):
            self._effect_state[module] = {
                "mode": "fond",
                "length": effect.length,
                "step": 0,
                "c1": effect.color_from,
                "c2": effect.color_to,
            }
            return effect.color_from

        if isinstance(effect, StrobeEffect):
            self._effect_state[module] = {
                "mode": "str",
                "length": effect.length,
                "step": 0,
                "color": effect.color,
                "freq": effect.freq,
                "toggle": True,
            }
            return effect.color

        if isinstance(effect, ContinueEffect):
            if not state:
                return None
            if state["mode"] == "fond":
                state["step"] = min(state["step"] + 1, state["length"] - 1)
                length = state["length"]
                t = 0.0 if length <= 1 else state["step"] / (length - 1)
                c1, c2 = state["c1"], state["c2"]
                return (
                    int(c1[0] + t * (c2[0] - c1[0])),
                    int(c1[1] + t * (c2[1] - c1[1])),
                    int(c1[2] + t * (c2[2] - c1[2])),
                )
            if state["mode"] == "str":
                state["step"] = min(state["step"] + 1, state["length"] - 1)
                state["toggle"] = not state["toggle"]
                return state["color"] if state["toggle"] else (0, 0, 0)
            if state["mode"] == "uni":
                return state["color"]
        return None
