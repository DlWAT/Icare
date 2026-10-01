"""Low-level DMX USB Pro (Enttec-compatible) wrapper.

Builds a 512-channel DMX frame and sends it over a serial port at 250 000 baud
using the Enttec USB Pro framing (0x7E start byte, 0xE7 end byte).
"""

from __future__ import annotations

import logging

import numpy as np
import serial
import serial.tools.list_ports

logger = logging.getLogger(__name__)

NUM_CHANNELS = 512
BAUDRATE = 250_000
START_BYTE = 0x7E
END_BYTE = 0xE7
LABEL_DMX_TX = 0x06  # "Output Only Send DMX Packet Request"


class DMXConnectionError(RuntimeError):
    """Raised when the DMX interface cannot be opened."""


class DMX_Icare:
    """Wraps a serial DMX-USB-Pro adapter and a 512-channel buffer."""

    def __init__(self) -> None:
        # Header: 0x7E, label, len_lsb, len_msb, then DATA, then 0xE7
        payload_len = NUM_CHANNELS + 1  # 1 start code + 512 channels
        self.start_byte = np.array(
            [
                START_BYTE,
                LABEL_DMX_TX,
                payload_len & 0xFF,
                (payload_len >> 8) & 0xFF,
                0x00,  # DMX start code
            ],
            np.uint8,
        )
        self.end_byte = np.array([END_BYTE], np.uint8)
        self.data = np.zeros([NUM_CHANNELS], np.uint8)
        self.com: serial.Serial | None = None

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------
    def connection(self, port: str | None = None) -> bool:
        """Open the serial port. Returns True on success.

        If ``port`` is ``None``, auto-detects the first port whose description
        contains 'USB'.
        """
        if port is None:
            port = self._autodetect_port()
            if port is None:
                logger.warning("No USB-DMX adapter found among COM ports")
                raise DMXConnectionError("No USB-DMX adapter found")
        try:
            self.com = serial.Serial(port, baudrate=BAUDRATE)
        except (serial.SerialException, OSError) as exc:
            logger.exception("Failed to open serial port %s", port)
            raise DMXConnectionError(f"Cannot open {port}: {exc}") from exc
        logger.info("DMX interface connected on %s", port)
        return True

    @staticmethod
    def _autodetect_port() -> str | None:
        for port_no, description, _address in serial.tools.list_ports.comports():
            if "USB" in description:
                return str(port_no)
        return None

    @property
    def is_connected(self) -> bool:
        return self.com is not None and self.com.is_open

    def close(self) -> None:
        if self.com is not None:
            try:
                self.com.close()
            except Exception:  # pragma: no cover
                logger.exception("Error closing serial port")
            self.com = None

    # ------------------------------------------------------------------
    # Channel I/O
    # ------------------------------------------------------------------
    def set_channel(self, num_channel: int, value: int) -> None:
        if not isinstance(num_channel, (int, np.integer)):
            raise TypeError(f"channel index must be int, got {type(num_channel).__name__}")
        if not isinstance(value, (int, np.integer)):
            raise TypeError(f"value must be int, got {type(value).__name__}")
        if not 0 <= num_channel < NUM_CHANNELS:
            raise ValueError(f"channel {num_channel} out of range (0..{NUM_CHANNELS - 1})")
        if not 0 <= value <= 255:
            raise ValueError(f"value {value} out of range (0..255)")
        self.data[num_channel] = value

    def set_data(self, data_in, index_addr: int, number_channel: int) -> None:
        self.data[index_addr : index_addr + number_channel] = data_in

    def send_data(self) -> None:
        if not self.is_connected:
            return
        frame = np.concatenate((self.start_byte, self.data, self.end_byte)).tobytes()
        try:
            self.com.write(frame)
        except (serial.SerialException, OSError):
            logger.exception("Error writing DMX frame; closing port")
            self.close()


class light_group:  # noqa: N801 - kept for backward compatibility
    """Aggregate of fixtures sharing the same channel layout."""

    def __init__(self, number_channel: int) -> None:
        self.number_channel = number_channel
        self.group_data = np.zeros([number_channel], np.uint8)
        self.members: list = []

    def addtogroup(self, lightsystem) -> None:
        if self.number_channel != lightsystem.number_channel:
            raise ValueError("Number of channels must match for grouped fixtures")
        self.members.append(lightsystem)
