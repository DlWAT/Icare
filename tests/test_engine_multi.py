"""Tests for the multi-fixture DMX controller (no hardware required)."""

from webapp.dmx_controller import DMXController
from webapp.fixtures import Fixture


def make_engine():
    patch = [
        Fixture("Par1", "rgbwa_par_5ch", 0),  # no dimmer -> scaled
        Fixture("Wash1", "wild_wash_132_6ch", 5),  # dimmer + strobe
        Fixture("Spot1", "cameo_qspot40_9ch", 11),  # dimmer + w
        Fixture("Fog", "stairville_mfog1500_3ch", 20),
    ]
    return DMXController(patch=patch)


def test_set_values_writes_dimmer_and_scaled_colour():
    c = make_engine()
    c.set_values(r=255, g=128, b=0, amp=200)
    data = c.mydmx.data

    # RGBWA par (no dimmer): colours scaled by amp/255.
    scale = 200 / 255
    assert data[0] == round(255 * scale)  # r
    assert data[1] == round(128 * scale)  # g
    assert data[2] == 0  # b
    assert data[3] == 0  # w
    assert data[4] == 0  # a

    # Wild Wash: dimmer=amp, then raw colours.
    assert data[5] == 200  # dimmer
    assert data[6] == 0  # strobe
    assert data[7] == 255  # r
    assert data[8] == 128  # g

    # Q-Spot: dimmer, dim fine, strobe, r, g, b, w
    assert data[11] == 200  # dimmer
    assert data[12] == 0  # dimmer fine
    assert data[13] == 0  # strobe
    assert data[14] == 255  # r
    assert data[15] == 128  # g


def test_white_and_amber_channels_on_qspot():
    c = make_engine()
    c.set_values(r=0, g=0, b=0, w=200, a=100, amp=255)
    data = c.mydmx.data
    # Q-Spot profile has a white channel but no amber channel.
    assert data[17] == 200  # w
    # Amber has nowhere to go on the Q-Spot -> no exception, channel stays 0.
    assert data[18] == 0


def test_fog_channel():
    c = make_engine()
    c.set_fog(level=180, interval=10, duration=20)
    data = c.mydmx.data
    assert data[20] == 180
    assert data[21] == 10
    assert data[22] == 20


def test_blackout_zeroes_lights_but_keeps_patch():
    c = make_engine()
    c.set_values(r=255, g=255, b=255, amp=255)
    c.set_fog(level=100)
    c.blackout()
    data = c.mydmx.data
    assert data[0] == 0
    assert data[5] == 0
    assert len(c.patch) == 4


def test_snapshot_has_positions_and_values():
    c = make_engine()
    c.set_values(r=255, g=0, b=0, amp=255)
    snap = c.snapshot()
    assert [f["name"] for f in snap["fixtures"]] == ["Par1", "Wash1", "Spot1", "Fog"]
    par = next(f for f in snap["fixtures"] if f["name"] == "Par1")
    assert par["values"]["r"] == 255
    assert "x" in par and "z" in par and "angle" in par
    assert "fog" in snap and "master" in snap


def test_apply_look_sets_per_fixture_state():
    c = make_engine()
    c.apply_look(
        {
            "Par1": {"r": 0, "g": 255, "b": 0, "w": 0, "a": 0},
            "Wash1": {"dimmer": 128, "r": 255, "g": 0, "b": 0},
        }
    )
    data = c.mydmx.data
    assert data[0] == 0
    assert data[1] == 255  # Par1 green
    assert data[5] == 128  # Wash1 dimmer
    assert data[7] == 255  # Wash1 red
    # Spot1 not in the look -> stays off.
    assert data[11] == 0
