"""Tests for the Ableton scene -> look engine (no Ableton required)."""

from webapp.ableton import AbletonOSC, SceneEngine
from webapp.dmx_controller import DMXController
from webapp.fixtures import Fixture
from webapp.looks import Look, save_look


def make_engine(tmp_path):
    patch = [
        Fixture("Par1", "rgbwa_par_5ch", 0),
        Fixture("Wash1", "wild_wash_132_6ch", 5),
    ]
    dmx = DMXController(patch=patch)
    client = AbletonOSC()
    engine = SceneEngine(client, dmx, str(tmp_path), tmp_path / "scenes.json")
    return client, dmx, engine


def test_scene_triggers_look(tmp_path):
    client, dmx, engine = make_engine(tmp_path)
    save_look(str(tmp_path), Look(name="intro", targets={"Par1": {"g": 255, "dimmer": 255}}))
    engine.set_mapping("INTRO", "intro")

    client.on_scene(0, "INTRO")

    assert engine.active_look == "intro"
    assert dmx.mydmx.data[1] == 255  # Par1 green


def test_unmapped_scene_is_ignored(tmp_path):
    client, dmx, engine = make_engine(tmp_path)
    client.on_scene(1, "SOLO")
    assert engine.active_look is None


def test_mapping_persists(tmp_path):
    client, dmx, engine = make_engine(tmp_path)
    engine.set_mapping("A", "lookA")

    fresh = SceneEngine(client, dmx, str(tmp_path), tmp_path / "scenes.json")
    assert fresh.mapping.get("A") == "lookA"


def test_disabled_engine_does_not_apply(tmp_path):
    client, dmx, engine = make_engine(tmp_path)
    save_look(str(tmp_path), Look(name="intro", targets={"Par1": {"g": 255}}))
    engine.set_mapping("INTRO", "intro")
    engine.set_enabled(False)

    client.on_scene(0, "INTRO")
    assert engine.active_look is None
