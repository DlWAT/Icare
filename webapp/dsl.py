"""Sequence "function string" DSL parser.

Each cell of a sequence row is a string describing what a single fixture
should do for the current step:

* ``""``                              — keep current state
* ``"|"``                             — continue the previous multi-step effect
* ``"uni_<n>_<R>_<G>_<B>"``           — uniform colour for ``n`` steps
* ``"fond_<n>_<R1>_<G1>_<B1>_<R2>_<G2>_<B2>"`` — linear fade from c1 to c2
* ``"str_<n>_<R>_<G>_<B>_<freq>"``    — strobe at ``freq`` for ``n`` steps

This module turns those strings into typed dataclasses so the live player can
consume them safely.
"""

from __future__ import annotations

from dataclasses import dataclass

RGB = tuple[int, int, int]


class DSLError(ValueError):
    """Raised when a function string cannot be parsed."""


@dataclass(frozen=True)
class UniformEffect:
    length: int
    color: RGB

    kind: str = "uni"


@dataclass(frozen=True)
class FadeEffect:
    length: int
    color_from: RGB
    color_to: RGB

    kind: str = "fond"


@dataclass(frozen=True)
class StrobeEffect:
    length: int
    color: RGB
    freq: int

    kind: str = "str"


@dataclass(frozen=True)
class ContinueEffect:
    """The ``|`` token: continue the previous multi-step effect."""

    kind: str = "continue"


Effect = UniformEffect | FadeEffect | StrobeEffect | ContinueEffect | None


def _parse_rgb(parts) -> RGB:
    r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
    for v in (r, g, b):
        if not 0 <= v <= 255:
            raise DSLError(f"RGB component out of range: {v}")
    return (r, g, b)


def parse(token: str) -> Effect:
    """Parse a single function-string token. Returns ``None`` for empty input."""
    if token is None or token == "":
        return None
    if token == "|":
        return ContinueEffect()
    parts = token.split("_")
    head = parts[0]
    try:
        if head == "uni":
            # uni_n_R_G_B
            if len(parts) != 5:
                raise DSLError(f"uni_ expects 4 args, got {len(parts) - 1}")
            n = max(1, int(parts[1]))
            color = _parse_rgb(parts[2:5])
            return UniformEffect(length=n, color=color)
        if head == "fond":
            # fond_n_R1_G1_B1_R2_G2_B2
            if len(parts) != 8:
                raise DSLError(f"fond_ expects 7 args, got {len(parts) - 1}")
            n = max(1, int(parts[1]))
            c1 = _parse_rgb(parts[2:5])
            c2 = _parse_rgb(parts[5:8])
            return FadeEffect(length=n, color_from=c1, color_to=c2)
        if head == "str":
            # str_n_R_G_B_freq  (freq optional)
            if len(parts) not in (5, 6):
                raise DSLError(f"str_ expects 4 or 5 args, got {len(parts) - 1}")
            n = max(1, int(parts[1]))
            color = _parse_rgb(parts[2:5])
            freq = int(parts[5]) if len(parts) == 6 else 60
            return StrobeEffect(length=n, color=color, freq=max(1, freq))
        raise DSLError(f"unknown effect prefix: {head!r}")
    except (ValueError, IndexError) as exc:
        raise DSLError(f"could not parse {token!r}: {exc}") from exc


def encode_uniform(length: int, color: RGB) -> str:
    r, g, b = color
    return f"uni_{int(length)}_{int(r)}_{int(g)}_{int(b)}"


def encode_fade(length: int, c_from: RGB, c_to: RGB) -> str:
    return (
        f"fond_{int(length)}"
        f"_{int(c_from[0])}_{int(c_from[1])}_{int(c_from[2])}"
        f"_{int(c_to[0])}_{int(c_to[1])}_{int(c_to[2])}"
    )


def encode_strobe(length: int, color: RGB, freq: int) -> str:
    r, g, b = color
    return f"str_{int(length)}_{int(r)}_{int(g)}_{int(b)}_{int(freq)}"
