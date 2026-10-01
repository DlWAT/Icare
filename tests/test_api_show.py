"""Read-only integration tests for the Show API and page."""

import pytest

from webapp import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as cli:
        yield cli


def test_show_page(client):
    r = client.get("/show")
    assert r.status_code == 200
    assert b"Show" in r.data


def test_patch_endpoint(client):
    r = client.get("/api/patch")
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    assert len(j["patch"]) == 11
    keys = {p["key"] for p in j["profiles"]}
    assert "rgbwa_par_5ch" in keys
    assert "cameo_qspot40_9ch" in keys


def test_patch_rejects_invalid(client):
    r = client.post(
        "/api/patch", json={"fixtures": [{"name": "A", "profile": "nope", "address": 0}]}
    )
    assert r.status_code == 400


def test_ableton_status(client):
    r = client.get("/api/ableton/status")
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    assert j["ableton"]["connected"] is False


def test_scenes_endpoint(client):
    r = client.get("/api/scenes")
    assert r.status_code == 200
    j = r.get_json()
    assert "scenes" in j and "looks" in j and "ableton" in j


def test_looks_list(client):
    r = client.get("/api/looks/list")
    assert r.status_code == 200
    assert r.get_json()["ok"] is True


def test_look_missing_returns_404(client):
    r = client.get("/api/looks/load?name=does-not-exist")
    assert r.status_code == 404


def test_apply_missing_look_returns_422(client):
    r = client.post("/api/looks/apply", json={"name": "does-not-exist"})
    assert r.status_code == 422


def test_simulation_endpoint(client):
    r = client.get("/api/simulation")
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    assert len(j["fixtures"]) == 11
    fog = next(f for f in j["fixtures"] if f["name"] == "Fog")
    assert {"x", "z", "angle", "values"} <= set(fog)
    assert "fog" in j and "master" in j


def test_fog_endpoint(client):
    r = client.post("/api/fog", json={"level": 100})
    assert r.status_code == 200
    assert r.get_json()["fog"]["level"] == 100
