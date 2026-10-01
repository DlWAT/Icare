"""Tests for the sequence schema normaliser/migrator."""

import pytest

from webapp.schemas import is_legacy, is_modern, normalize_sequence


def test_modern_passthrough():
    raw = {
        "Header": {
            "Structure": ["Intro"],
            "Tempo": "60",
            "Modules": ["ParLED1", "ParLED2"],
            "Line": ["1"],
        },
        "data": {
            "1": {"section": "Intro", "function": ["uni_1_255_0_0", ""]},
        },
    }
    out = normalize_sequence(raw)
    assert out["Header"]["Modules"] == ["ParLED1", "ParLED2"]
    assert out["data"]["1"]["function"] == ["uni_1_255_0_0", ""]


def test_modern_pads_short_function_lists():
    raw = {
        "Header": {"Structure": [], "Tempo": "60", "Modules": ["A", "B", "C"], "Line": []},
        "data": {"1": {"section": "X", "function": ["uni_1_1_1_1"]}},
    }
    out = normalize_sequence(raw)
    assert out["data"]["1"]["function"] == ["uni_1_1_1_1", "", ""]


def test_legacy_migration():
    raw = {
        "headers": {"structure": ["intro", "Refrain1"]},
        "data": {
            "intro": [[2, 125, 20, 35], [2, 20, 53, 128]],
            "Refrain1": [[0.5, 100, 100, 100]],
        },
    }
    assert is_legacy(raw) and not is_modern(raw)
    out = normalize_sequence(raw)
    # Modern shape
    assert "Header" in out and "data" in out
    assert "ParLED1" in out["Header"]["Modules"]
    # Each row produced N beats; first row has 2*2 = 4 beats
    rows = list(out["data"].values())
    assert len(rows) >= 5
    assert rows[0]["function"][0].startswith("uni_")
    assert rows[1]["function"][0] == "|"


def test_unknown_schema_raises():
    with pytest.raises(ValueError):
        normalize_sequence({"foo": "bar"})
