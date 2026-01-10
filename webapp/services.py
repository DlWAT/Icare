import os
from .dmx_controller import DMXController

# Global service instances

dmx = DMXController()

# Paths
REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
SEQ_DIR = os.path.join(REPO_ROOT, "Sequences")
