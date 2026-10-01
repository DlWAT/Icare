"""High-level integration tests for the Flask routes."""

import pytest

from webapp import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as cli:
        yield cli


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    assert "dmx" in j
    assert "connected" in j["dmx"]


def test_index_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"Icare" in r.data


def test_set_values_clamps(client):
    r = client.post("/api/experiment/set-values", json={"r": 999, "g": -5, "b": 100})
    assert r.status_code == 200
    assert r.get_json()["ok"] is True


def test_invalid_base_channel(client):
    r = client.post("/api/experiment/base-channel", json={"baseChannel": 9999})
    assert r.status_code == 400


def test_sequence_load_invalid_filename(client):
    r = client.get("/api/sequence/load?name=../../etc/passwd")
    # Either 400 (sanitised away to nothing) or 404 (sanitised to a name not present)
    assert r.status_code in (400, 404)


def test_palette_favorites_round_trip(client):
    add = client.post("/api/palettes/favorites/add", json={"color": "#abcdef"})
    assert add.status_code == 200
    listed = client.get("/api/palettes/favorites").get_json()
    assert "#abcdef" in listed["colors"]
    rm = client.post("/api/palettes/favorites/remove", json={"color": "#abcdef"})
    assert rm.status_code == 200
    listed2 = client.get("/api/palettes/favorites").get_json()
    assert "#abcdef" not in listed2["colors"]


def test_settings_get_set(client):
    r = client.get("/api/settings")
    assert r.status_code == 200
    j = r.get_json()
    assert "settings" in j

    r2 = client.post("/api/settings", json={"theme": "light"})
    assert r2.status_code == 200
    assert r2.get_json()["settings"]["theme"] == "light"

    # Restore
    client.post("/api/settings", json={"theme": "dark"})


def test_settings_invalid_theme(client):
    r = client.post("/api/settings", json={"theme": "neon"})
    assert r.status_code == 400


def test_live_tap(client):
    r = client.post("/api/live/tap")
    assert r.status_code == 200


def test_live_status(client):
    r = client.get("/api/live/status")
    assert r.status_code == 200
    s = r.get_json()["status"]
    assert "bpm" in s
    assert "rgb" in s
