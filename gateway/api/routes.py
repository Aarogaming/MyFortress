import time
from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from gateway.api.models import (
    FrigateCamerasResponse,
    FrigateEventsResponse,
    FrigateProbeRequest,
    FrigateProbeResponse,
    HomeMerlinProbeRequest,
    HomeMerlinProbeResponse,
    HomeMerlinServiceRequest,
    HomeMerlinServiceResponse,
    HomeMerlinStateRequest,
    HomeMerlinStateResponse,
    SnapshotRequest,
    SnapshotResponse,
)
from gateway.config import Settings, get_settings
from gateway.domain.models import GatewaySnapshot
from gateway.integrations.frigate import FrigateClient
from gateway.integrations.frigate_events_stream import stream_events
from gateway.integrations.home_assistant import HomeMerlinClient

router = APIRouter()
_SNAPSHOT_CACHE: Dict[str, Any] = {}


@router.post(
    "/home-assistant/probe",
    response_model=HomeMerlinProbeResponse,
    summary="Probe Home Merlin entities",
)
async def home_assistant_probe(
    req: HomeMerlinProbeRequest, settings: Settings = Depends(get_settings)
):
    entities = req.entities or settings.home_assistant_entities
    client = HomeMerlinClient(
        settings=settings,
        base_url=req.base_url or settings.home_assistant_url,
        token=req.token or settings.home_assistant_token,
        verify_ssl=req.verify_ssl,
        timeout=settings.home_assistant_timeout,
    )
    return await client.probe_entities(entities)


@router.post(
    "/home-assistant/service",
    response_model=HomeMerlinServiceResponse,
    summary="Invoke Home Merlin service",
)
async def home_assistant_service(
    req: HomeMerlinServiceRequest, settings: Settings = Depends(get_settings)
):
    client = HomeMerlinClient(
        settings=settings,
        base_url=req.base_url or settings.home_assistant_url,
        token=req.token or settings.home_assistant_token,
        verify_ssl=settings.home_assistant_verify_ssl,
        timeout=settings.home_assistant_timeout,
    )
    return await client.call_service(req.domain, req.service, req.data)


@router.post(
    "/home-assistant/state",
    response_model=HomeMerlinStateResponse,
    summary="Set Home Merlin entity state",
)
async def home_assistant_state(
    req: HomeMerlinStateRequest, settings: Settings = Depends(get_settings)
):
    client = HomeMerlinClient(
        settings=settings,
        base_url=req.base_url or settings.home_assistant_url,
        token=req.token or settings.home_assistant_token,
        verify_ssl=settings.home_assistant_verify_ssl,
        timeout=settings.home_assistant_timeout,
    )
    return await client.set_state(req.entity_id, req.state, req.attributes)


@router.post(
    "/frigate/probe",
    response_model=FrigateProbeResponse,
    summary="Probe Frigate version",
)
async def frigate_probe(
    req: FrigateProbeRequest, settings: Settings = Depends(get_settings)
):
    client = FrigateClient(
        settings=settings,
        base_url=req.base_url or settings.frigate_url,
        api_key=req.api_key or settings.frigate_api_key,
        timeout=settings.frigate_timeout,
    )
    return await client.fetch_version()


@router.get(
    "/frigate/cameras",
    response_model=FrigateCamerasResponse,
    summary="List Frigate cameras from config",
)
async def frigate_cameras(settings: Settings = Depends(get_settings)):
    client = FrigateClient(
        settings=settings,
        base_url=settings.frigate_url,
        api_key=settings.frigate_api_key,
        timeout=settings.frigate_timeout,
    )
    return await client.list_cameras()


@router.get(
    "/frigate/events",
    response_model=FrigateEventsResponse,
    summary="List Frigate events",
)
async def frigate_events(limit: int = 50, settings: Settings = Depends(get_settings)):
    client = FrigateClient(
        settings=settings,
        base_url=settings.frigate_url,
        api_key=settings.frigate_api_key,
        timeout=settings.frigate_timeout,
    )
    events = await client.fetch_events(limit=limit)
    events["stream_supported"] = True  # hint for future SSE clients
    return events


@router.get(
    "/frigate/events/stream",
    summary="Stream Frigate events (Server-Sent Events)",
    response_class=StreamingResponse,
)
async def frigate_events_stream(settings: Settings = Depends(get_settings)):
    if not settings.frigate_url:
        return StreamingResponse(iter([]), media_type="text/event-stream")

    async def _event_generator():
        async for ev in stream_events(
            settings=settings, base_url=settings.frigate_url, api_key=settings.frigate_api_key
        ):
            yield f"data: {ev.get('raw','')}\n\n"

    return StreamingResponse(_event_generator(), media_type="text/event-stream")


@router.post(
    "/snapshot",
    response_model=SnapshotResponse,
    summary="Aggregate snapshot across Home Merlin and Frigate",
)
async def snapshot(
    req: SnapshotRequest, settings: Settings = Depends(get_settings)
):
    now = time.time()
    cache_key = (
        f"ha:{req.include_home_assistant}"
        f":fr:{req.include_frigate}"
        f":cam:{req.include_frigate_cameras}"
        f":entities:{','.join(sorted(req.home_assistant_entities or settings.home_assistant_entities))}"
    )
    ttl = settings.snapshot_cache_ttl
    cached = _SNAPSHOT_CACHE.get(cache_key)
    if cached and cached["expires_at"] > now:
        return cached["data"]

    import asyncio

    ha_snapshot = None
    frigate_snapshot = None

    tasks = []

    if req.include_home_assistant:
        ha_entities = req.home_assistant_entities or settings.home_assistant_entities
        ha_client = HomeMerlinClient(
            settings=settings,
            base_url=settings.home_assistant_url,
            token=settings.home_assistant_token,
            verify_ssl=settings.home_assistant_verify_ssl,
        )
        tasks.append(ha_client.probe_entities(ha_entities))
    else:
        tasks.append(asyncio.sleep(0))

    if req.include_frigate:
        frigate_client = FrigateClient(
            settings=settings,
            base_url=settings.frigate_url,
            api_key=settings.frigate_api_key,
        )
        if req.include_frigate_cameras:
            tasks.append(frigate_client.fetch_snapshot())
        else:
            tasks.append(frigate_client.fetch_version())
    else:
        tasks.append(asyncio.sleep(0))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    if req.include_home_assistant and not isinstance(results[0], Exception):
        ha_snapshot = results[0]
    if req.include_frigate and not isinstance(results[1], Exception):
        frigate_snapshot = results[1]

    snapshot_data = GatewaySnapshot(
        home_assistant=ha_snapshot,
        frigate=frigate_snapshot,
    )
    _SNAPSHOT_CACHE[cache_key] = {
        "data": snapshot_data,
        "expires_at": now + ttl,
    }
    return snapshot_data
