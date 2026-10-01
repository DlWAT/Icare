"""A small show player: a timeline of light cues, no Ableton needed.

A *show* is a JSON file with a list of cues. Each cue has a type and a duration
(seconds, or beats at the show tempo), and may carry a fog level:

* ``look``      — recall a look by name (``{"type":"look","name":"CHORUS"}``).
* ``effect``    — start a procedural effect (rainbow / fire / police / chase).
* ``strobe``    — full-frame strobe (``freq``, ``shuffle``).
* ``fog``       — set the fog level (its own cue).
* ``blackout``  — turn everything off.

The player runs in a daemon thread and drives the shared DMX controller, so the
web UI and the 3D simulation follow along. It is a stand-alone way to exercise
the whole chain (patch, looks, effects, fog) without any external software.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time

from .utils import safe_json_path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Show files
# ---------------------------------------------------------------------------
def list_shows(directory: str) -> list[str]:
    if not os.path.isdir(directory):
        return []
    return sorted(f[:-5] for f in os.listdir(directory) if f.lower().endswith(".json"))


def load_show_file(directory: str, name: str) -> dict:
    path = safe_json_path(name, directory)
    if path is None or not os.path.isfile(path):
        raise FileNotFoundError(name)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_show_file(directory: str, name: str, data: dict) -> str:
    path = safe_json_path(name, directory)
    if path is None:
        raise ValueError("invalid show name")
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    return os.path.basename(path)


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------
class ShowPlayer:
    """Plays a timeline of cues in a daemon thread."""

    def __init__(self, dmx, scene_engine) -> None:
        self.dmx = dmx
        self.scene = scene_engine

        self.name = ""
        self.bpm = 120.0
        self.cues: list[dict] = []
        self.index = 0
        self.playing = False
        self.paused = False

        self._thread: threading.Thread | None = None

    # -- loading ----------------------------------------------------------
    def load(self, data: dict) -> dict:
        cues = data.get("cues")
        if not isinstance(cues, list):
            raise ValueError("show must contain a 'cues' list")
        self.stop()
        self.name = str(data.get("name", ""))
        self.bpm = float(data.get("bpm", 120) or 120)
        self.cues = [c for c in cues if isinstance(c, dict)]
        self.index = 0
        return self.status()

    # -- transport --------------------------------------------------------
    def start(self) -> None:
        if not self.cues:
            raise ValueError("no show loaded")
        self.playing = True
        self.paused = False
        self._ensure_thread()

    def pause(self) -> None:
        self.paused = not self.paused

    def stop(self) -> None:
        self.playing = False
        self.paused = False
        self.index = 0

    # -- status -----------------------------------------------------------
    def _label(self, cue: dict) -> str:
        ctype = str(cue.get("type", "look"))
        if ctype == "look":
            return f"look {cue.get('name', '?')}"
        if ctype == "effect":
            return f"effet {cue.get('name', '?')}"
        if ctype == "strobe":
            return f"strobe {cue.get('freq', '?')} Hz"
        if ctype == "fog":
            return f"fumee {cue.get('level', '?')}"
        return ctype

    def status(self) -> dict:
        total = len(self.cues)
        cue = self.cues[self.index] if 0 <= self.index < total else None
        pct = int(100 * self.index / total) if total else 0
        return {
            "name": self.name,
            "playing": self.playing,
            "paused": self.paused,
            "index": self.index,
            "total": total,
            "progress": pct,
            "cue": self._label(cue) if cue else None,
            "next": self._label(self.cues[self.index + 1])
            if cue and self.index + 1 < total
            else None,
        }

    # -- thread -----------------------------------------------------------
    def _ensure_thread(self) -> None:
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, daemon=True, name="show-player")
            self._thread.start()

    def _duration(self, cue: dict) -> float:
        if "seconds" in cue:
            return max(0.2, float(cue["seconds"]))
        beats = float(cue.get("beats", 4))
        return max(0.2, beats * 60.0 / max(1.0, self.bpm))

    def _apply(self, cue: dict) -> None:
        ctype = str(cue.get("type", "look"))
        try:
            if ctype == "look":
                name = cue.get("name")
                if name:
                    self.scene.show_look(str(name))
            elif ctype == "effect":
                self.dmx.effect_start(
                    str(cue.get("name", "rainbow")),
                    speed=float(cue.get("speed", 1.0)),
                    brightness=int(cue.get("brightness", 200)),
                )
            elif ctype == "strobe":
                self.dmx.strobe(int(cue.get("freq", 12)), int(cue.get("shuffle", 50)))
            elif ctype == "fog":
                self.dmx.set_fog(level=int(cue.get("level", 180)))
            elif ctype == "blackout":
                self.dmx.blackout()
        except (ValueError, TypeError) as exc:
            logger.warning("Show cue %r failed: %s", cue, exc)

        # A cue-level fog level wins over the look's own fog.
        fog = cue.get("fog")
        if fog is not None:
            self.dmx.set_fog(level=int(fog))

    def _run(self) -> None:
        while True:
            if not self.playing or self.paused or not self.cues:
                time.sleep(0.05)
                continue
            cue = self.cues[self.index]
            self._apply(cue)
            started = time.monotonic()
            duration = self._duration(cue)
            while time.monotonic() - started < duration:
                if not self.playing or self.paused:
                    break
                time.sleep(0.05)
            if not self.playing or self.paused:
                continue
            self.index += 1
            if self.index >= len(self.cues):
                self.index = 0
                self.playing = False
