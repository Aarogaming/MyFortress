import time
import psutil
import platform
import socket
from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from gateway.api.models import (
    AgentAnalyticsResponse,
    AgentPerformanceMetrics,
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
    PluginAnalyticsResponse,
    PluginMetricsResponse,
    SnapshotRequest,
    SnapshotResponse,
    SystemInfoResponse,
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
            settings=settings,
            base_url=settings.frigate_url,
            api_key=settings.frigate_api_key,
        ):
            yield f"data: {ev.get('raw','')}\n\n"

    return StreamingResponse(_event_generator(), media_type="text/event-stream")


@router.post(
    "/snapshot",
    response_model=SnapshotResponse,
    summary="Aggregate snapshot across Home Merlin and Frigate",
)
async def snapshot(req: SnapshotRequest, settings: Settings = Depends(get_settings)):
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


@router.get(
    "/system/info",
    response_model=SystemInfoResponse,
    summary="Get system information",
)
async def get_system_info():
    """Get system information from MyFortress gateway."""
    try:
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net = psutil.net_if_addrs()

        return SystemInfoResponse(
            os=platform.system(),
            os_release=platform.release(),
            os_version=platform.version(),
            architecture=platform.machine(),
            hostname=socket.gethostname(),
            cpu_count=psutil.cpu_count(logical=True),
            cpu_usage_percent=psutil.cpu_percent(interval=0.1),
            memory_total_gb=round(mem.total / (1024**3), 2),
            memory_available_gb=round(mem.available / (1024**3), 2),
            memory_usage_percent=mem.percent,
            disk_total_gb=round(disk.total / (1024**3), 2),
            disk_free_gb=round(disk.free / (1024**3), 2),
            disk_usage_percent=disk.percent,
            network_interfaces=list(net.keys()),
        )
    except Exception as e:
        return SystemInfoResponse(
            os="",
            os_release="",
            os_version="",
            architecture="",
            hostname="",
            cpu_count=0,
            cpu_usage_percent=0.0,
            memory_total_gb=0.0,
            memory_available_gb=0.0,
            memory_usage_percent=0.0,
            disk_total_gb=0.0,
            disk_free_gb=0.0,
            disk_usage_percent=0.0,
            network_interfaces=[],
            error=str(e),
        )


@router.get(
    "/agent/analytics",
    response_model=AgentAnalyticsResponse,
    summary="Get AI agent performance analytics",
)
async def get_agent_analytics():
    """
    Retrieve AI agent performance analytics and metrics.

    This endpoint provides insights into AI agent task completion rates,
    success rates, average response times, and current agent loads.
    """
    from datetime import datetime, timezone

    try:
        # Mock data for demonstration - in production, this would query Guild system
        # For now, we'll provide sample analytics data showing typical agent performance

        agents_data = [
            AgentPerformanceMetrics(
                agent_id="agent_001",
                agent_name="GitHub Copilot",
                total_tasks=145,
                completed_tasks=138,
                failed_tasks=7,
                success_rate=95.2,
                avg_completion_time=23.5,
                current_load=0.3,
                status="busy",
                capabilities=[
                    "code_generation",
                    "code_review",
                    "testing",
                    "documentation",
                ],
                last_activity=datetime.now(timezone.utc).isoformat(),
            ),
            AgentPerformanceMetrics(
                agent_id="agent_002",
                agent_name="ChatGPT",
                total_tasks=89,
                completed_tasks=86,
                failed_tasks=3,
                success_rate=96.6,
                avg_completion_time=18.2,
                current_load=0.2,
                status="idle",
                capabilities=["research", "analysis", "documentation", "planning"],
                last_activity=datetime.now(timezone.utc).isoformat(),
            ),
            AgentPerformanceMetrics(
                agent_id="agent_003",
                agent_name="Merlin AI",
                total_tasks=112,
                completed_tasks=109,
                failed_tasks=3,
                success_rate=97.3,
                avg_completion_time=15.8,
                current_load=0.4,
                status="busy",
                capabilities=["optimization", "debugging", "testing", "analysis"],
                last_activity=datetime.now(timezone.utc).isoformat(),
            ),
        ]

        total_tasks = sum(agent.total_tasks for agent in agents_data)
        total_completed = sum(agent.completed_tasks for agent in agents_data)

        overall_success_rate = (
            (total_completed / total_tasks * 100) if total_tasks > 0 else 0.0
        )

        # Calculate weighted average completion time
        total_completion_time = sum(
            agent.completed_tasks * agent.avg_completion_time for agent in agents_data
        )
        avg_completion_time = (
            total_completion_time / total_completed if total_completed > 0 else 0.0
        )

        active_agents = sum(1 for agent in agents_data if agent.status != "offline")

        return AgentAnalyticsResponse(
            total_agents=len(agents_data),
            active_agents=active_agents,
            total_tasks_completed=total_completed,
            overall_success_rate=round(overall_success_rate, 1),
            avg_completion_time=round(avg_completion_time, 1),
            agents=agents_data,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        return AgentAnalyticsResponse(
            total_agents=0,
            active_agents=0,
            total_tasks_completed=0,
            overall_success_rate=0.0,
            avg_completion_time=0.0,
            agents=[],
            timestamp=datetime.now(timezone.utc).isoformat(),
            error=str(e),
        )


@router.get(
    "/plugin/analytics",
    response_model=PluginAnalyticsResponse,
    summary="Get Plugin Analytics",
)
async def get_plugin_analytics():
    """
    Get comprehensive plugin analytics including:
    - Usage statistics
    - Performance metrics
    - Health scores
    - Comparative analysis
    """
    try:
        # Mock data for demonstration
        # In production, this would integrate with core/plugins/analytics.py
        from datetime import datetime, timezone

        plugins_data = [
            PluginMetricsResponse(
                plugin_id="plugin_001",
                plugin_name="Task Automation Engine",
                category="automation",
                total_invocations=5234,
                successful_invocations=5100,
                failed_invocations=134,
                success_rate=97.4,
                error_rate=2.6,
                avg_execution_time_ms=145.3,
                health_score=92.5,
                last_used=datetime.now(timezone.utc).isoformat(),
            ),
            PluginMetricsResponse(
                plugin_id="plugin_002",
                plugin_name="Data Processor",
                category="data",
                total_invocations=8912,
                successful_invocations=8750,
                failed_invocations=162,
                success_rate=98.2,
                error_rate=1.8,
                avg_execution_time_ms=89.2,
                health_score=95.1,
                last_used=datetime.now(timezone.utc).isoformat(),
            ),
            PluginMetricsResponse(
                plugin_id="plugin_003",
                plugin_name="AI Model Manager",
                category="ai",
                total_invocations=3421,
                successful_invocations=3280,
                failed_invocations=141,
                success_rate=95.9,
                error_rate=4.1,
                avg_execution_time_ms=523.7,
                health_score=88.3,
                last_used=datetime.now(timezone.utc).isoformat(),
            ),
            PluginMetricsResponse(
                plugin_id="plugin_004",
                plugin_name="System Monitor",
                category="monitoring",
                total_invocations=15678,
                successful_invocations=15650,
                failed_invocations=28,
                success_rate=99.8,
                error_rate=0.2,
                avg_execution_time_ms=23.1,
                health_score=98.9,
                last_used=datetime.now(timezone.utc).isoformat(),
            ),
            PluginMetricsResponse(
                plugin_id="plugin_005",
                plugin_name="Event Stream Handler",
                category="communication",
                total_invocations=12456,
                successful_invocations=12100,
                failed_invocations=356,
                success_rate=97.1,
                error_rate=2.9,
                avg_execution_time_ms=67.4,
                health_score=91.2,
                last_used=datetime.now(timezone.utc).isoformat(),
            ),
        ]

        total_invocations = sum(p.total_invocations for p in plugins_data)
        total_errors = sum(p.failed_invocations for p in plugins_data)
        avg_success_rate = sum(p.success_rate for p in plugins_data) / len(plugins_data)

        global_stats = {
            "total_plugins": 50,
            "active_plugins": 42,
            "total_invocations": total_invocations,
            "total_errors": total_errors,
            "avg_success_rate": round(avg_success_rate, 2),
        }

        comparative_analysis = {
            "fastest_plugin": "System Monitor",
            "slowest_plugin": "AI Model Manager",
            "most_reliable": "System Monitor",
            "least_reliable": "AI Model Manager",
            "most_used": "System Monitor",
            "least_used": "Task Automation Engine",
            "healthiest": "System Monitor",
        }

        # Sort by invocations for top plugins
        top_plugins = sorted(
            plugins_data, key=lambda p: p.total_invocations, reverse=True
        )

        return PluginAnalyticsResponse(
            timestamp=datetime.now(timezone.utc).isoformat(),
            global_stats=global_stats,
            top_plugins=top_plugins,
            comparative_analysis=comparative_analysis,
        )
    except Exception as e:
        return PluginAnalyticsResponse(
            timestamp=datetime.now(timezone.utc).isoformat(),
            global_stats={},
            top_plugins=[],
            comparative_analysis={},
            error=str(e),
        )
