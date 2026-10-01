"""Tests for the stand-alone show player (no hardware, no Ableton)."""

import pytest

from webapp.ableton import AbletonOSC, SceneEngine
from webapp.dmx_controller import DMXController
from webapp.fixtures import Fixture
from webapp.looks import Look, save_look
from webapp.show_player import ShowPlayer, list_shows, load_show_file, save_show_file


def make_player(tmp_path):
    dmx = DMXController(
        patch=[
            Fixture("Par1", "rgbwa_par_5ch", 0),
            Fixture("Wash1", "wild_wash_132_6ch", 5),
        ]
    )
    client = AbletonOSC()
    scene = SceneEngine(client, dmx, str(tmp_path), tmp_path / "scenes.json")
    save_look(str(tmp_path), Look(name="intro", targets={"Par1": {"g": 255, "dimmer": 255}}))
    return ShowPlayer(dmx, scene), dmx


def test_load_and_status(tmp_path):
    player, _ = make_player(tmp_path)
    status = player.load(
        {
            "name": "t",
            "cues": [
                {"type": "look", "name": "intro", "seconds": 1},
                {"type": "blackout", "seconds": 1},
            ],
        }
    )
    assert status["total"] == 2
    assert status["name"] == "t"


def test_load_rejects_bad_payload(tmp_path):
    player, _ = make_player(tmp_path)
    with pytest.raises(ValueError):
        player.load({"nope": []})


def test_apply_look_cue(tmp_path):
    player, dmx = make_player(tmp_path)
    player.load({"cues": [{"type": "look", "name": "intro", "seconds": 1}]})
    player._apply(player.cues[0])
    assert dmx.mydmx.data[1] == 255  # Par1 green


def test_apply_effect_cue(tmp_path):
    player, dmx = make_player(tmp_path)
    player.load({"bpm": 120, "cues": [{"type": "effect", "name": "rainbow", "seconds": 1}]})
    player._apply(player.cues[0])
    assert dmx.effect_enabled is True


def test_apply_fog_and_blackout(tmp_path):
    player, dmx = make_player(tmp_path)
    player.load({"cues": [{"type": "fog", "level": 200, "seconds": 1}]})
    player._apply(player.cues[0])
    assert dmx.fog["level"] == 200

    player.load({"cues": [{"type": "blackout", "seconds": 1}]})
    player._apply(player.cues[0])
    assert dmx.fog["level"] == 0


def test_duration_seconds_and_beats(tmp_path):
    player, _ = make_player(tmp_path)
    player.bpm = 120
    assert player._duration({"seconds": 3}) == 3
    assert player._duration({"beats": 4}) == 2.0  # 4 beats at 120 BPM


def test_show_files_round_trip(tmp_path):
    directory = str(tmp_path)
    save_show_file(directory, "hello", {"name": "hi", "cues": [{"type": "blackout", "seconds": 1}]})
    assert "hello" in list_shows(directory)
    assert load_show_file(directory, "hello")["name"] == "hi"
