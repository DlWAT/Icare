"""Application-wide singletons.

Keeping these in a dedicated module avoids circular imports between the
blueprints, the controllers, and the configuration layer.
"""

from __future__ import annotations

from .ableton import AbletonOSC, SceneEngine
from .config import (
    LOOKS_DIR,
    PALETTES_DIR,
    PATCH_FILE,
    SCENES_FILE,
    SEQUENCES_DIR,
    UserSettings,
)
from .dmx_controller import DMXController
from .fixtures import load_patch

# Persistent user preferences (last port, base channel, theme, palettes…)
settings = UserSettings.load()

# The DMX patch (adapts to the physical rig; falls back to the default).
patch = load_patch(PATCH_FILE)

# Single DMX controller for the whole process
dmx = DMXController(settings=settings, patch=patch)

# Ableton link (starts on demand) and the scene -> look engine.
ableton = AbletonOSC()
scene_engine = SceneEngine(ableton, dmx, str(LOOKS_DIR), SCENES_FILE)

# Filesystem paths exposed for blueprints (kept as ``str`` for stdlib os.path
# compatibility in places that still use it)
SEQ_DIR = str(SEQUENCES_DIR)
PALETTE_DIR = str(PALETTES_DIR)
LOOK_DIR = str(LOOKS_DIR)
