"""Application-wide singletons.

Keeping these in a dedicated module avoids circular imports between the
blueprints, the controllers, and the configuration layer.
"""

from __future__ import annotations

from .config import PALETTES_DIR, SEQUENCES_DIR, UserSettings
from .dmx_controller import DMXController

# Persistent user preferences (last port, base channel, theme, palettes…)
settings = UserSettings.load()

# Single DMX controller for the whole process
dmx = DMXController(settings=settings)

# Filesystem paths exposed for blueprints (kept as ``str`` for stdlib os.path
# compatibility in places that still use it)
SEQ_DIR = str(SEQUENCES_DIR)
PALETTE_DIR = str(PALETTES_DIR)
