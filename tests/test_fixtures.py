"""Tests for the fixture profiles and the DMX patch."""

import pytest

from webapp.fixtures import (
    PROFILES,
    Fixture,
    default_patch,
    patch_from_json,
    patch_to_json,
    validate_patch,
)


def test_profile_sizes():
    assert PROFILES["rgbwa_par_5ch"].size == 5
    assert PROFILES["wild_wash_132_6ch"].size == 6
    assert PROFILES["cameo_qspot40_9ch"].size == 9
    assert PROFILES["stairville_mfog1500_3ch"].size == 3


def test_default_patch_is_valid_and_contiguous():
    patch = validate_patch(default_patch())
    assert len(patch) == 11  # 6 par + 2 wash + 2 q-spot + 1 fog
    assert patch[0].name == "ParLED1"
    assert patch[0].address == 0
    # No overlaps and increasing addresses are guaranteed by validate_patch,
    # but check the total span is modest.
    assert patch[-1].end == 5 * 6 + 6 * 2 + 9 * 2 + 3


def test_validate_rejects_overlap():
    patch = [
        Fixture("A", "rgbwa_par_5ch", 0),
        Fixture("B", "rgbwa_par_5ch", 3),  # overlaps A
    ]
    with pytest.raises(ValueError, match="overlap"):
        validate_patch(patch)


def test_validate_rejects_unknown_profile():
    with pytest.raises(ValueError, match="unknown profile"):
        validate_patch([Fixture("A", "nope", 0)])


def test_validate_rejects_out_of_range():
    with pytest.raises(ValueError, match="out of range"):
        validate_patch([Fixture("A", "cameo_qspot40_9ch", 510)])


def test_validate_rejects_duplicate_names():
    patch = [
        Fixture("A", "rgbwa_par_5ch", 0),
        Fixture("A", "rgbwa_par_5ch", 5),
    ]
    with pytest.raises(ValueError, match="duplicate"):
        validate_patch(patch)


def test_patch_json_round_trip():
    patch = default_patch()
    dumped = patch_to_json(patch)
    back = patch_from_json(dumped)
    assert [f.name for f in back] == [f.name for f in patch]
    assert [f.address for f in back] == [f.address for f in patch]
    assert [f.x for f in back] == [f.x for f in patch]
    assert [f.angle for f in back] == [f.angle for f in patch]
