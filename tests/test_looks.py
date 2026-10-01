"""Tests for looks (resolution and storage)."""

from webapp.fixtures import Fixture
from webapp.looks import Look, list_looks, load_look, resolve, save_look


def make_patch():
    return [
        Fixture("Par1", "rgbwa_par_5ch", 0, group="pars"),
        Fixture("Par2", "rgbwa_par_5ch", 5, group="pars"),
        Fixture("Wash1", "wild_wash_132_6ch", 10, group="wash"),
    ]


def test_resolve_wildcard_and_scaling():
    look = Look(
        name="blue",
        targets={"*": {"r": 0, "g": 0, "b": 255, "dimmer": 128}},
    )
    out = resolve(look, make_patch())

    # PAR has no dimmer -> colour is scaled by 128/255.
    assert out["Par1"]["b"] == round(255 * 128 / 255)
    assert "dimmer" not in out["Par1"]
    # Wash has a dimmer -> dimmer written, colour untouched.
    assert out["Wash1"]["dimmer"] == 128
    assert out["Wash1"]["b"] == 255


def test_specific_target_overrides_wildcard():
    look = Look(
        name="mixed",
        targets={
            "*": {"dimmer": 100},
            "Par2": {"r": 255, "g": 0, "b": 0, "dimmer": 255},
        },
    )
    out = resolve(look, make_patch())
    assert out["Par2"]["r"] == 255
    # Par2 has no dimmer -> full intensity means unscaled red.
    assert out["Par2"]["g"] == 0
    # Par1 only got the dimmer wildcard and no colour -> it stays off.
    assert out.get("Par1", {}).get("r", 0) == 0


def test_unknown_target_is_ignored():
    look = Look(name="x", targets={"Ghost": {"r": 255}})
    assert resolve(look, make_patch()) == {}


def test_save_load_round_trip(tmp_path):
    directory = str(tmp_path)
    look = Look(
        name="refrain",
        targets={"*": {"b": 200}},
        fog={"level": 120},
        motion={"type": "wave", "speed": 0.5, "amount": 0.4},
    )
    save_look(directory, look)

    assert "refrain" in list_looks(directory)
    back = load_look(directory, "refrain")
    assert back.name == "refrain"
    assert back.targets["*"]["b"] == 200
    assert back.fog["level"] == 120
    assert back.motion["type"] == "wave"
    assert back.motion["speed"] == 0.5
