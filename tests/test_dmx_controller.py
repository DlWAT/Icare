"""Tests for DMXController state setters (no hardware required)."""

from webapp.dmx_controller import DMXController


def make_controller():
    # The controller will instantiate a serial-less DMX_Icare; sending will
    # silently no-op because is_connected is False.
    return DMXController()


def test_clamping_rgb():
    c = make_controller()
    c.set_values(r=300, g=-10, b=128)
    assert c.r == 255
    assert c.g == 0
    assert c.b == 128


def test_clamping_amp_pan_tilt():
    c = make_controller()
    c.set_values(amp=999, pan=-1, tilt=200)
    assert c.amp == 255
    assert c.pan == 0
    assert c.tilt == 200


def test_set_base_channel_valid():
    c = make_controller()
    c.set_base_channel(20)
    assert c.base_color_channel == 20


def test_set_base_channel_out_of_range():
    c = make_controller()
    import pytest

    with pytest.raises(ValueError):
        c.set_base_channel(600)
    with pytest.raises(ValueError):
        c.set_base_channel(-1)


def test_health_starts_disconnected():
    c = make_controller()
    h = c.health()
    assert h["connected"] is False
    assert h["lastError"] is None
    assert "modes" in h


def test_hsv_to_rgb_red():
    c = make_controller()
    assert c._hsv_to_rgb(0, 1.0, 1.0) == (255, 0, 0)
    assert c._hsv_to_rgb(120, 1.0, 1.0) == (0, 255, 0)
    assert c._hsv_to_rgb(240, 1.0, 1.0) == (0, 0, 255)


def test_effect_start_unknown_raises():
    c = make_controller()
    import pytest

    with pytest.raises(ValueError):
        c.effect_start("not-an-effect")
