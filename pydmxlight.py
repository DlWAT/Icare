"""DMX fixture descriptors.

Each fixture owns a small numpy buffer for its own channels and validates
``set_channel`` calls. The buffers are not pushed to the DMX interface
themselves — :class:`webapp.dmx_controller.DMXController` is responsible for
that.
"""

from __future__ import annotations

import numpy as np


class _Fixture:
    """Common base for DMX fixtures sharing the same set_channel logic."""

    number_channel: int
    data: np.ndarray
    position: int

    def set_channel(self, num_channel: int, value: int) -> None:
        if not isinstance(num_channel, (int, np.integer)):
            raise TypeError(f"channel index must be int, got {type(num_channel).__name__}")
        if not isinstance(value, (int, np.integer)):
            raise TypeError(f"value must be int, got {type(value).__name__}")
        if not 0 <= num_channel < self.number_channel:
            raise ValueError(f"channel {num_channel} out of range (0..{self.number_channel - 1})")
        if not 0 <= value <= 255:
            raise ValueError(f"value {value} out of range (0..255)")
        self.data[num_channel] = value


class Par_Led_615_AFX(_Fixture):  # noqa: N801 - product name kept for clarity
    """15-channel RGB Par LED."""

    def __init__(self, number_channel: int, position: int) -> None:
        self.number_channel = int(number_channel)
        self.position = int(position)
        self.pos = self.position  # legacy alias
        self.data = np.zeros([self.number_channel], np.uint8)


class Strobe_132_RGB(_Fixture):  # noqa: N801
    """3-channel RGB strobe (one channel per primary color)."""

    def __init__(self, position: int) -> None:
        self.number_channel = 3
        self.position = int(position)
        self.pos = self.position  # legacy alias
        self.data = np.zeros([self.number_channel], np.uint8)
