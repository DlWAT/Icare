"""Centralised configuration constants and per-user settings persistence.

Two layers:

* Hard-coded constants (DMX channel layout, refresh rates, paths) live in
  module-level constants below.
* Mutable user preferences (last COM port, base channel, last sequence,
  theme, ...) are persisted to a JSON file next to the executable so they
  survive restarts. See :class:`UserSettings`.
"""

from __future__ import annotations

import json
import logging
import sys
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Filesystem
# ---------------------------------------------------------------------------
def _runtime_root() -> Path:
    """Return a directory that is writable at runtime.

    When packaged with PyInstaller, ``sys._MEIPASS`` is read-only; we still
    need somewhere to drop logs and the user settings file. We pick the
    directory containing the .exe in that case, or the project root in
    development.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _bundle_root() -> Path:
    """Return the directory holding read-only bundled resources."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


RUNTIME_ROOT = _runtime_root()
BUNDLE_ROOT = _bundle_root()

# Sequences: prefer a user-writable copy next to the exe; fall back to bundle
SEQUENCES_DIR = RUNTIME_ROOT / "Sequences"
if not SEQUENCES_DIR.is_dir():
    bundled = BUNDLE_ROOT / "Sequences"
    if bundled.is_dir() and not SEQUENCES_DIR.exists():
        # First run from packaged exe: keep using the bundled (read-only) dir
        SEQUENCES_DIR = bundled
    else:
        SEQUENCES_DIR.mkdir(parents=True, exist_ok=True)

PALETTES_DIR = RUNTIME_ROOT / "Palettes"
PALETTES_DIR.mkdir(parents=True, exist_ok=True)

# Looks (static per-fixture light states) and the DMX patch.
LOOKS_DIR = RUNTIME_ROOT / "Looks"
LOOKS_DIR.mkdir(parents=True, exist_ok=True)
SHOWS_DIR = RUNTIME_ROOT / "Shows"
SHOWS_DIR.mkdir(parents=True, exist_ok=True)
PATCH_FILE = RUNTIME_ROOT / "patch.json"
SCENES_FILE = RUNTIME_ROOT / "scenes.json"

LOG_FILE = RUNTIME_ROOT / "icare.log"
SETTINGS_FILE = RUNTIME_ROOT / "icare_settings.json"


# ---------------------------------------------------------------------------
# DMX channel layout (legacy 1-fixture map taken from ExperimentTab)
# ---------------------------------------------------------------------------
class Channels:
    MASTER = 0  # always 255 to enable output
    AMPLITUDE = 1  # global brightness
    PAN = 3
    TILT = 5
    SHUTTER = 8  # always 0 (no shutter effect)
    BASE_COLOR_DEFAULT = 9  # R, G, B at base, base+1, base+2


# Refresh / loop intervals (seconds)
class Timings:
    STEADY_LOOP = 0.05  # ~20 Hz steady output loop
    RANDOM_LOOP = 0.025  # ~40 Hz for smooth random fades
    EFFECT_LOOP = 0.025  # ~40 Hz for procedural effects
    IDLE_LOOP = 0.10  # idle wait
    CLIENT_POLL_DIRECT_MS = 200
    CLIENT_POLL_LIVE_MS = 250


# ---------------------------------------------------------------------------
# User settings (persistent)
# ---------------------------------------------------------------------------
@dataclass
class UserSettings:
    """Mutable user preferences saved to ``SETTINGS_FILE``."""

    base_color_channel: int = Channels.BASE_COLOR_DEFAULT
    last_com_port: str = ""  # empty string = autodetect
    last_sequence: str = ""  # last loaded JSON file (basename)
    theme: str = "dark"  # 'dark' | 'light'
    favorite_colors: list[str] = field(default_factory=list)  # hex strings #RRGGBB

    # ---- I/O ----
    _lock = threading.Lock()
    _path: Path = SETTINGS_FILE

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Drop private fields
        return {k: v for k, v in d.items() if not k.startswith("_")}

    def save(self) -> None:
        with self._lock:
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                with self._path.open("w", encoding="utf-8") as fh:
                    json.dump(self.to_dict(), fh, indent=2)
            except OSError:
                logger.exception("Could not save user settings to %s", self._path)

    def update(self, **fields_) -> None:
        for key, value in fields_.items():
            if hasattr(self, key) and not key.startswith("_"):
                setattr(self, key, value)
        self.save()

    @classmethod
    def load(cls) -> UserSettings:
        path = SETTINGS_FILE
        if not path.is_file():
            return cls()
        try:
            with path.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except (OSError, json.JSONDecodeError):
            logger.exception("Corrupt settings file at %s; resetting", path)
            return cls()
        # Filter to known fields to avoid TypeErrors
        valid_keys = {f for f in cls.__dataclass_fields__ if not f.startswith("_")}
        filtered = {k: v for k, v in payload.items() if k in valid_keys}
        try:
            return cls(**filtered)
        except TypeError:
            logger.exception("Settings schema mismatch; resetting")
            return cls()


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logging once: console + rotating file next to the exe."""
    if getattr(setup_logging, "_done", False):
        return
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(level)

    # Console
    console = logging.StreamHandler(stream=sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    # Rotating file
    try:
        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=512_000, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except (OSError, PermissionError):
        # Read-only filesystem: skip file logging
        logging.getLogger(__name__).warning(
            "Could not open log file at %s, file logging disabled", LOG_FILE
        )

    # Mute Flask/werkzeug INFO chatter unless DEBUG
    if level > logging.DEBUG:
        logging.getLogger("werkzeug").setLevel(logging.WARNING)

    setup_logging._done = True  # type: ignore[attr-defined]
