"""Fixture profiles and the DMX patch.

A **profile** describes the channel layout of a fixture model: which DMX
channel does what (red, dimmer, strobe, ...). A **patch entry** places a
profile in the universe at a given start address and gives it a name and an
optional group.

The patch serialises to a small JSON file so the operator can adapt it to the
physical rig without touching code. Everything is validated on load: unknown
profiles, overlaps and out-of-range addresses are refused.

Profiles currently shipped (matching the material):

* ``rgbwa_par_5ch``        — 6× generic RGBWA PAR, 5 channels.
* ``wild_wash_132_6ch``    — 2× Stairville Wild Wash 132 LED RGB, 6 channels.
* ``cameo_qspot40_9ch``    — 2× Cameo Q-Spot 40 RGBW, 9 channels.
* ``stairville_mfog1500_3ch`` — 1× Stairville M-Fog 1500, 3 channels.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

UNIVERSE_SIZE = 512

# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------
# Semantic channel functions. The renderer only needs to know these keys; any
# other channel is simply written as 0.
DIMMER = "dimmer"
DIMMER_FINE = "dimmer_fine"
STROBE = "strobe"
R, G, B, W, A = "r", "g", "b", "w", "a"
PAN, TILT = "pan", "tilt"
MACRO = "macro"
COLOR_TEMP = "color_temp"
SOUND = "sound"
FOG = "fog"
FOG_INTERVAL = "fog_interval"
FOG_DURATION = "fog_duration"


@dataclass(frozen=True)
class ChannelSpec:
    """One DMX channel of a profile."""

    fn: str
    label: str
    default: int = 0


@dataclass(frozen=True)
class FixtureProfile:
    """Channel layout of a fixture model."""

    key: str
    label: str
    channels: tuple[ChannelSpec, ...]
    beam_angle: float = 25.0  # full beam angle in degrees (0 = no beam)

    @property
    def size(self) -> int:
        return len(self.channels)

    def index_of(self, fn: str) -> int | None:
        for i, ch in enumerate(self.channels):
            if ch.fn == fn:
                return i
        return None

    def functions(self) -> set[str]:
        return {ch.fn for ch in self.channels}


def _ch(fn: str, label: str, default: int = 0) -> ChannelSpec:
    return ChannelSpec(fn, label, default)


PROFILES: dict[str, FixtureProfile] = {}


def _register(profile: FixtureProfile) -> FixtureProfile:
    PROFILES[profile.key] = profile
    return profile


_register(
    FixtureProfile(
        "rgbwa_par_5ch",
        "PAR LED RGBWA (5 canaux)",
        (
            _ch(R, "Rouge"),
            _ch(G, "Vert"),
            _ch(B, "Bleu"),
            _ch(W, "Blanc"),
            _ch(A, "Ambre"),
        ),
        beam_angle=30.0,
    )
)

_register(
    FixtureProfile(
        "wild_wash_132_6ch",
        "Stairville Wild Wash 132 LED RGB (6 canaux)",
        (
            _ch(DIMMER, "Intensité", 255),
            _ch(STROBE, "Strobe"),
            _ch(R, "Rouge"),
            _ch(G, "Vert"),
            _ch(B, "Bleu"),
            _ch(SOUND, "Sensibilité son"),
        ),
        beam_angle=75.0,  # large wash
    )
)

_register(
    FixtureProfile(
        "cameo_qspot40_9ch",
        "Cameo Q-Spot 40 RGBW (9 canaux)",
        (
            _ch(DIMMER, "Intensité", 255),
            _ch(DIMMER_FINE, "Intensité fine"),
            _ch(STROBE, "Strobe"),
            _ch(R, "Rouge"),
            _ch(G, "Vert"),
            _ch(B, "Bleu"),
            _ch(W, "Blanc"),
            _ch(MACRO, "Macro couleur"),
            _ch(COLOR_TEMP, "Température de couleur"),
        ),
        beam_angle=15.0,  # tight pin spot
    )
)

_register(
    FixtureProfile(
        "stairville_mfog1500_3ch",
        "Stairville M-Fog 1500 (3 canaux)",
        (
            _ch(FOG, "Volume brouillard"),
            _ch(FOG_INTERVAL, "Vitesse / intervalle"),
            _ch(FOG_DURATION, "Durée"),
        ),
        beam_angle=0.0,
    )
)


# ---------------------------------------------------------------------------
# Patch
# ---------------------------------------------------------------------------
@dataclass
class Fixture:
    """A physical fixture placed in the universe.

    ``x``/``z``/``angle`` are only used by the 3D simulation: they place the
    fixture on the virtual stage (metres) and give the direction its beam
    points to (degrees, 0 = towards the audience, +Z).
    """

    name: str
    profile: str
    address: int  # 0-based start channel
    group: str = ""
    x: float = 0.0
    z: float = 0.0
    angle: float = 0.0

    @property
    def profile_obj(self) -> FixtureProfile:
        return PROFILES[self.profile]

    @property
    def end(self) -> int:
        """First channel *after* this fixture (exclusive)."""
        return self.address + self.profile_obj.size

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "profile": self.profile,
            "address": self.address,
            "group": self.group,
            "x": self.x,
            "z": self.z,
            "angle": self.angle,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Fixture:
        return cls(
            name=str(raw["name"]),
            profile=str(raw["profile"]),
            address=int(raw["address"]),
            group=str(raw.get("group", "")),
            x=float(raw.get("x", 0.0)),
            z=float(raw.get("z", 0.0)),
            angle=float(raw.get("angle", 0.0)),
        )


def default_patch() -> list[Fixture]:
    """Return the patch matching the documented rig, packed from channel 0.

    Stage coordinates are a simple, tidy layout: the six PARs form a back line,
    the washes sit at the sides, the two spots are near the centre and the fog
    machine is front-right.
    """
    out: list[Fixture] = []
    addr = 0

    for i in range(1, 7):  # 6× RGBWA PAR — back line
        out.append(
            Fixture(
                f"ParLED{i}",
                "rgbwa_par_5ch",
                addr,
                group="pars",
                x=-5.0 + (i - 1) * 2.0,
                z=-2.5,
                angle=0.0,
            )
        )
        addr += PROFILES["rgbwa_par_5ch"].size

    for i in range(1, 3):  # 2× Wild Wash — sides, aimed inwards
        out.append(
            Fixture(
                f"Wash{i}",
                "wild_wash_132_6ch",
                addr,
                group="wash",
                x=-5.5 if i == 1 else 5.5,
                z=-1.5,
                angle=35.0 if i == 1 else -35.0,
            )
        )
        addr += PROFILES["wild_wash_132_6ch"].size

    for i in range(1, 3):  # 2× Cameo Q-Spot — near centre
        out.append(
            Fixture(
                f"QSpot{i}",
                "cameo_qspot40_9ch",
                addr,
                group="spots",
                x=-2.0 if i == 1 else 2.0,
                z=-2.2,
                angle=0.0,
            )
        )
        addr += PROFILES["cameo_qspot40_9ch"].size

    out.append(Fixture("Fog", "stairville_mfog1500_3ch", addr, group="fx", x=0.0, z=1.5, angle=0.0))
    return out


def validate_patch(patch: Iterable[Fixture]) -> list[Fixture]:
    """Return the patch as a list, raising ``ValueError`` if it is invalid."""
    fixtures = list(patch)
    if not fixtures:
        raise ValueError("patch is empty")

    names: set[str] = set()
    used: dict[int, str] = {}
    for fx in fixtures:
        if fx.profile not in PROFILES:
            raise ValueError(f"unknown profile {fx.profile!r} on {fx.name!r}")
        if not fx.name:
            raise ValueError("every fixture needs a name")
        if fx.name in names:
            raise ValueError(f"duplicate fixture name {fx.name!r}")
        names.add(fx.name)

        size = PROFILES[fx.profile].size
        if not 0 <= fx.address <= UNIVERSE_SIZE - size:
            raise ValueError(
                f"{fx.name}: address {fx.address} out of range "
                f"(0..{UNIVERSE_SIZE - size}) for a {size}-channel profile"
            )
        for ch in range(fx.address, fx.end):
            if ch in used:
                raise ValueError(f"{fx.name} overlaps {used[ch]!r} on channel {ch}")
            used[ch] = fx.name
    return fixtures


def patch_to_json(patch: Iterable[Fixture]) -> dict[str, Any]:
    return {"fixtures": [fx.to_dict() for fx in patch]}


def patch_from_json(data: dict[str, Any]) -> list[Fixture]:
    raw = data.get("fixtures")
    if not isinstance(raw, list):
        raise ValueError("patch JSON must contain a 'fixtures' list")
    return validate_patch(Fixture.from_dict(item) for item in raw)


def load_patch(path: Path) -> list[Fixture]:
    """Load a patch from ``path``; fall back to the default on any problem."""
    if not path.is_file():
        return default_patch()
    try:
        with path.open("r", encoding="utf-8") as fh:
            return patch_from_json(json.load(fh))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return default_patch()


def save_patch(path: Path, patch: Iterable[Fixture]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(patch_to_json(patch), fh, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------
def patch_summary(patch: Iterable[Fixture]) -> list[dict[str, Any]]:
    """Return a JSON-friendly description of the patch (for the web UI)."""
    out = []
    for fx in patch:
        prof = fx.profile_obj
        out.append(
            {
                "name": fx.name,
                "profile": fx.profile,
                "profileLabel": prof.label,
                "group": fx.group,
                "address": fx.address,
                "channels": prof.size,
                "end": fx.end,
                "x": fx.x,
                "z": fx.z,
                "angle": fx.angle,
                "beamAngle": prof.beam_angle,
            }
        )
    return out


def profile_catalog() -> list[dict[str, Any]]:
    """Return the list of known profiles (for the web UI)."""
    return [
        {
            "key": p.key,
            "label": p.label,
            "size": p.size,
            "beamAngle": p.beam_angle,
            "channels": [{"fn": c.fn, "label": c.label, "default": c.default} for c in p.channels],
        }
        for p in PROFILES.values()
    ]
