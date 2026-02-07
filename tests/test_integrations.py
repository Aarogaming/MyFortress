import pytest
import respx
from gateway.config import Settings
from gateway.integrations.frigate import FrigateClient
from gateway.integrations.home_assistant import HomeMerlinClient


@pytest.mark.asyncio
@respx.mock
async def test_home_assistant_probe_success():
    settings = Settings(home_assistant_url="http://ha.local")
    respx.get("http://ha.local/api/states/sensor.temp").respond(
        json={"state": "on", "attributes": {"friendly_name": "Temp"}}
    )

    client = HomeMerlinClient(settings=settings)
    snapshot = await client.probe_entities(["sensor.temp"])

    assert snapshot.healthy is True
    assert "sensor.temp" in snapshot.readings
    assert snapshot.readings["sensor.temp"].state == "on"


@pytest.mark.asyncio
@respx.mock
async def test_frigate_probe_handles_error():
    settings = Settings(frigate_url="http://frigate.local")
    respx.get("http://frigate.local/api/version").respond(status_code=500)

    client = FrigateClient(settings=settings)
    snapshot = await client.fetch_version()

    assert snapshot.healthy is False
    assert snapshot.error is not None


@pytest.mark.asyncio
@respx.mock
async def test_home_assistant_service_call():
    settings = Settings(home_assistant_url="http://ha.local")
    respx.post("http://ha.local/api/services/light/toggle").respond(
        json={"result": "ok"}
    )

    client = HomeMerlinClient(settings=settings)
    resp = await client.call_service("light", "toggle", {"entity_id": "light.kitchen"})

    assert resp["success"] is True
    assert resp["response"]["result"] == "ok"


@pytest.mark.asyncio
@respx.mock
async def test_frigate_cameras():
    settings = Settings(frigate_url="http://frigate.local")
    respx.get("http://frigate.local/api/config").respond(
        json={"cameras": {"front": {}, "back": {}}}
    )

    client = FrigateClient(settings=settings)
    resp = await client.list_cameras()

    assert resp["success"] is True
    assert "front" in resp["cameras"]


@pytest.mark.asyncio
@respx.mock
async def test_home_assistant_set_state():
    settings = Settings(home_assistant_url="http://ha.local")
    respx.post("http://ha.local/api/states/light.kitchen").respond(
        json={"state": "on", "attributes": {"brightness": 150}}
    )

    client = HomeMerlinClient(settings=settings)
    resp = await client.set_state("light.kitchen", "on", {"brightness": 150})

    assert resp["success"] is True
    assert resp["state"] == "on"
    assert resp["attributes"]["brightness"] == 150


@pytest.mark.asyncio
@respx.mock
async def test_frigate_events():
    settings = Settings(frigate_url="http://frigate.local")
    respx.get("http://frigate.local/api/events").respond(
        json=[{"id": "1", "camera": "front"}]
    )

    client = FrigateClient(settings=settings)
    resp = await client.fetch_events(limit=10)

    assert resp["success"] is True
    assert resp["events"][0]["id"] == "1"
