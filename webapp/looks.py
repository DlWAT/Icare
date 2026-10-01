"""Light *looks* — static per-fixture states you can recall from Ableton.

A look is a small JSON file::

    {
      "name": "Refrain",
      "targets": {
        "pars":   {"r": 0, "g": 0, "b": 255, "dimmer": 220},
        "QSpot1": {"r": 255, "g": 80, "b": 0},
        "*":      {"dimmer": 180}
      },
      "fog": {"level": 120}
    }

Targets are matched in order ``"*"`` (all), then the fixture's group, then the
fixture name, so a look can set a global base and override specific fixtures.
:func:`resolve` turns the look into concrete channel functions per fixture,
scaling colours for profiles that have no dimmer channel.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from .fixtures import DIMMER, A, B, Fixture, G, R, W
from .utils import safe_json_path

COLOR_FNS = (R, G, B, W, A)


@dataclass
class Look:
    name: str
    targets: dict[str, dict[str, int]] = field(default_factory=dict)
    fog: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "targets": self.targets,
            "fog": self.fog,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Look:
        targets: dict[str, dict[str, int]] = {}
        for key, state in (raw.get("targets") or {}).items():
            if isinstance(state, dict):
                targets[str(key)] = {str(k): int(v) for k, v in state.items()}
        fog = {str(k): int(v) for k, v in (raw.get("fog") or {}).items()}
        return cls(name=str(raw.get("name", "")), targets=targets, fog=fog)


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------
def _clamp(value: int) -> int:
    return max(0, min(255, int(value)))


def resolve(look: Look, patch: Iterable[Fixture]) -> dict[str, dict[str, int]]:
    """Turn a look into ``{fixture_name: {channel_fn: value}}``.

    Colours are scaled by the target intensity for profiles that have no
    dimmer channel, so a look behaves the same on every fixture.
    """
    out: dict[str, dict[str, int]] = {}
    for fx in patch:
        merged: dict[str, int] = {}
        matched = False
        for key in ("*", fx.group, fx.name):
            if key and key in look.targets:
                merged.update(look.targets[key])
                matched = True
        if not matched:
            continue

        prof = fx.profile_obj
        fns = prof.functions()
        dimmer = _clamp(merged.get("dimmer", 255))
        state: dict[str, int] = {}

        if DIMMER in fns:
            state[DIMMER] = dimmer
            scale = 1.0
        else:
            scale = dimmer / 255.0

        for fn in (*COLOR_FNS, "strobe"):
            if fn in fns and fn in merged:
                value = merged[fn] if fn not in COLOR_FNS else round(merged[fn] * scale)
                state[fn] = _clamp(value)

        if state:
            out[fx.name] = state
    return out


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
def _look_path(directory: str, name: str) -> str | None:
    return safe_json_path(name, directory)


def list_looks(directory: str) -> list[str]:
    if not os.path.isdir(directory):
        return []
    return sorted(f[:-5] for f in os.listdir(directory) if f.lower().endswith(".json"))


def load_look(directory: str, name: str) -> Look:
    path = _look_path(directory, name)
    if path is None or not os.path.isfile(path):
        raise FileNotFoundError(name)
    with open(path, encoding="utf-8") as fh:
        return Look.from_dict(json.load(fh))


def save_look(directory: str, look: Look) -> str:
    path = _look_path(directory, look.name)
    if path is None:
        raise ValueError("invalid look name")
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(look.to_dict(), fh, indent=2, ensure_ascii=False)
    return os.path.basename(path)


def delete_look(directory: str, name: str) -> bool:
    path = _look_path(directory, name)
    if path is None or not os.path.isfile(path):
        return False
    os.remove(path)
    return True
