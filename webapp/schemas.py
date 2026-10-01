"""Sequence file schema definitions and a migration helper.

Two schemas are tolerated when loading a JSON sequence:

1. **Modern** schema (canonical, what the editor produces)::

       {
         "Header": {
           "Structure": [str, ...],
           "Tempo": "60",
           "Modules": [str, ...],
           "Line":  [str, ...]
         },
         "data": {
           "1": {"section": "Intro", "function": ["uni_4_255_0_0", ...]},
           ...
         }
       }

2. **Legacy** schema (early prototype, e.g. ``Doctor_doctor.json``)::

       {
         "headers": {"structure": ["intro", "Couplet1", ...]},
         "data": {"intro": [[2, 125, 20, 35], ...], ...}
       }

   Each row is a 4-tuple ``[duration_beats, R, G, B]``.

:func:`normalize_sequence` returns the modern shape regardless of which one is
provided so the rest of the codebase only has to deal with one layout.
"""

from __future__ import annotations

from typing import Any

from .dsl import encode_uniform


def is_modern(raw: dict[str, Any]) -> bool:
    return isinstance(raw, dict) and "Header" in raw and "data" in raw


def is_legacy(raw: dict[str, Any]) -> bool:
    return isinstance(raw, dict) and "headers" in raw and "data" in raw


def normalize_sequence(raw: dict[str, Any]) -> dict[str, Any]:
    """Return the sequence in the modern shape. Migrates legacy on the fly."""
    if is_modern(raw):
        return _validate_modern(raw)
    if is_legacy(raw):
        return _legacy_to_modern(raw)
    raise ValueError("Unknown sequence schema (no Header/headers key)")


def _validate_modern(raw: dict[str, Any]) -> dict[str, Any]:
    header = raw.get("Header", {}) or {}
    data = raw.get("data", {}) or {}
    modules = header.get("Modules") or []
    if not isinstance(modules, list):
        raise ValueError("Header.Modules must be a list")
    # Coerce data keys to strings, "1", "2", ... and ensure each row has the
    # right shape.
    norm_data: dict[str, dict[str, Any]] = {}
    for key, row in data.items():
        if not isinstance(row, dict):
            continue
        funcs = row.get("function") or []
        if not isinstance(funcs, list):
            funcs = []
        # Pad/truncate to len(modules)
        if len(funcs) < len(modules):
            funcs = list(funcs) + [""] * (len(modules) - len(funcs))
        elif len(funcs) > len(modules):
            funcs = funcs[: len(modules)]
        norm_data[str(key)] = {
            "section": str(row.get("section", "")),
            "function": [str(f) if f is not None else "" for f in funcs],
        }
    return {
        "Header": {
            "Structure": list(header.get("Structure") or []),
            "Tempo": str(header.get("Tempo", "60")),
            "Modules": list(modules),
            "Line": list(header.get("Line") or sorted(norm_data.keys(), key=int)),
        },
        "data": norm_data,
    }


def _legacy_to_modern(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert a legacy-schema dict to the modern one.

    Legacy rows look like ``[duration_beats, R, G, B]``. We:

    * use the section name as the structure entry,
    * expand a row's ``duration`` into that many beats — first beat with
      ``uni_<n>_<R>_<G>_<B>``, the following ones with ``"|"``,
    * use a single dummy module called ``ParLED1`` since the legacy schema
      doesn't carry per-fixture data.
    """
    structure_in: list[str] = list(raw.get("headers", {}).get("structure", []))
    sections_in: dict[str, list[list[float]]] = raw.get("data", {}) or {}

    modules = ["ParLED1"]
    structure: list[str] = []
    line_labels: list[str] = []
    data: dict[str, dict[str, Any]] = {}

    line_no = 0
    for section_name in structure_in:
        rows = sections_in.get(section_name, []) or []
        for row in rows:
            if not isinstance(row, (list, tuple)) or len(row) < 4:
                continue
            duration = max(1, int(round(float(row[0]) * 2)))  # beats (0.5 -> 1, 2 -> 4)
            r, g, b = int(row[1]), int(row[2]), int(row[3])
            for beat in range(duration):
                line_no += 1
                key = str(line_no)
                token = encode_uniform(duration, (r, g, b)) if beat == 0 else "|"
                data[key] = {"section": section_name, "function": [token]}
                structure.append(section_name)
                line_labels.append(key)

    return {
        "Header": {
            "Structure": structure,
            "Tempo": "60",
            "Modules": modules,
            "Line": line_labels,
        },
        "data": data,
    }
