"""Minimal Open Sound Control (OSC 1.0) encoder/decoder.

Only what Icare needs to talk to AbletonOSC: int, float, string, true/false
arguments. Messages are padded to 4-byte boundaries as the spec requires.
"""

from __future__ import annotations

import struct
from typing import Any


def _padded(data: bytes) -> bytes:
    """Null-terminate an OSC string and pad it to a multiple of 4 bytes."""
    return data + b"\x00" * (4 - (len(data) % 4))


def encode(address: str, *args: Any) -> bytes:
    """Encode an OSC message into bytes."""
    if not address.startswith("/"):
        raise ValueError(f"OSC address must start with '/': {address!r}")
    out = _padded(address.encode("utf-8"))
    tags = ","
    body = b""
    for arg in args:
        if isinstance(arg, bool):
            tags += "i"
            body += struct.pack(">i", 1 if arg else 0)
        elif isinstance(arg, int):
            tags += "i"
            body += struct.pack(">i", arg)
        elif isinstance(arg, float):
            tags += "f"
            body += struct.pack(">f", arg)
        elif isinstance(arg, str):
            tags += "s"
            body += _padded(arg.encode("utf-8"))
        else:
            raise TypeError(f"unsupported OSC argument type: {type(arg).__name__}")
    return out + _padded(tags.encode("utf-8")) + body


def _read_string(data: bytes, index: int) -> tuple[str, int]:
    end = data.find(b"\x00", index)
    if end == -1:
        end = len(data)
    text = data[index:end].decode("utf-8", "replace")
    index = end + 1
    while index % 4 != 0:
        index += 1
    return text, index


def decode(data: bytes) -> tuple[str, list[Any]]:
    """Decode bytes into ``(address, args)``."""
    address, index = _read_string(data, 0)
    if index >= len(data):
        return address, []
    tags, index = _read_string(data, index)
    if tags.startswith(","):
        tags = tags[1:]
    args: list[Any] = []
    for tag in tags:
        if tag == "i":
            if index + 4 > len(data):
                break
            args.append(struct.unpack_from(">i", data, index)[0])
            index += 4
        elif tag == "f":
            if index + 4 > len(data):
                break
            args.append(round(struct.unpack_from(">f", data, index)[0], 6))
            index += 4
        elif tag == "d":
            if index + 8 > len(data):
                break
            args.append(struct.unpack_from(">d", data, index)[0])
            index += 8
        elif tag == "s":
            value, index = _read_string(data, index)
            args.append(value)
        elif tag == "T":
            args.append(True)
        elif tag == "F":
            args.append(False)
        else:
            break
    return address, args
