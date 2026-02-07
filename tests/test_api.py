import respx
from fastapi.testclient import TestClient
from gateway.api.server import app
from gateway.config import Settings, get_settings


def _override_settings() -> Settings:
    return Settings(
        home_assistant_url="http://ha.local",
        frigate_url="http://frigate.local",
    )


app.dependency_overrides[get_settings] = _override_settings
client = TestClient(app)


@respx.mock
def test_snapshot_endpoint_returns_data():
    respx.get("http://ha.local/api/states/sensor.temp").respond(
        json={"state": "on", "attributes": {"friendly_name": "Temp"}}
    )
    respx.get("http://frigate.local/api/version").respond(json={"version": "1.2.3"})
    respx.get("http://frigate.local/api/config").respond(
        json={"cameras": {"front": {}, "back": {}}}
    )

    resp = client.post("/snapshot", json={"home_assistant_entities": ["sensor.temp"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["home_assistant"]["healthy"] is True
    assert data["frigate"]["healthy"] is True
    assert data["home_assistant"]["readings"]["sensor.temp"]["state"] == "on"
    assert "front" in data["frigate"]["cameras"]


@respx.mock
def test_home_assistant_service():
    respx.post("http://ha.local/api/services/light/toggle").respond(
        json={"result": "ok"}
    )
    resp = client.post(
        "/home-assistant/service",
        json={
            "domain": "light",
            "service": "toggle",
            "data": {"entity_id": "light.kitchen"},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["response"]["result"] == "ok"


@respx.mock
def test_frigate_cameras():
    respx.get("http://frigate.local/api/config").respond(
        json={"cameras": {"front": {}, "back": {}}}
    )
    resp = client.get("/frigate/cameras")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "front" in body["cameras"]


@respx.mock
def test_home_assistant_state():
    respx.post("http://ha.local/api/states/light.kitchen").respond(
        json={"state": "on", "attributes": {"brightness": 150}}
    )
    resp = client.post(
        "/home-assistant/state",
        json={
            "entity_id": "light.kitchen",
            "state": "on",
            "attributes": {"brightness": 150},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["attributes"]["brightness"] == 150


@respx.mock
def test_frigate_events():
    respx.get("http://frigate.local/api/events").respond(
        json=[{"id": "1", "camera": "front"}]
    )
    resp = client.get("/frigate/events", params={"limit": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["events"][0]["id"] == "1"
    assert body["stream_supported"] is True


def test_health_and_readiness():
    health = client.get("/health")
    ready = client.get("/readiness")
    assert health.status_code == 200
    assert ready.status_code == 200
    assert "status" in health.json()
    assert ready.json()["status"] == "ready"


def test_system_info():
    resp = client.get("/system/info")
    assert resp.status_code == 200
    data = resp.json()
    assert "platform" in data
    assert "python_version" in data
