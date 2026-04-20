from typing import Any, Dict, List, Optional

from gateway.domain.models import FrigateSnapshot, GatewaySnapshot, HomeMerlinSnapshot
from pydantic import BaseModel, Field


class HomeMerlinProbeRequest(BaseModel):
    base_url: Optional[str] = Field(default=None, description="Home Merlin base URL")
    token: Optional[str] = Field(default=None, description="Long-lived token")
    entities: List[str] = Field(default_factory=list)
    verify_ssl: bool = Field(default=True)


class HomeMerlinProbeResponse(HomeMerlinSnapshot):
    """Response for Home Merlin probe."""


class FrigateProbeRequest(BaseModel):
    base_url: Optional[str] = Field(default=None, description="Frigate base URL")
    api_key: Optional[str] = Field(default=None, description="API key")
    cameras: List[str] = Field(default_factory=list)


class FrigateProbeResponse(FrigateSnapshot):
    """Response for Frigate probe."""


class FrigateCamerasResponse(BaseModel):
    success: bool
    cameras: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class FrigateEventsResponse(BaseModel):
    success: bool
    events: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
    stream_supported: bool = False


class SnapshotRequest(BaseModel):
    include_home_assistant: bool = True
    include_frigate: bool = True
    home_assistant_entities: List[str] = Field(default_factory=list)
    include_frigate_cameras: bool = Field(default=True, description="Include camera list")


class SnapshotResponse(GatewaySnapshot):
    """Aggregated snapshot response."""


class HomeMerlinServiceRequest(BaseModel):
    """Invoke a Home Merlin service (domain/service)."""

    base_url: Optional[str] = None
    token: Optional[str] = None
    domain: str
    service: str
    data: Dict[str, Any] = Field(default_factory=dict)


class HomeMerlinServiceResponse(BaseModel):
    success: bool
    response: Optional[Any] = None
    error: Optional[str] = None


class HomeMerlinStateRequest(BaseModel):
    base_url: Optional[str] = None
    token: Optional[str] = None
    entity_id: str
    state: Any
    attributes: Dict[str, Any] = Field(default_factory=dict)


class HomeMerlinStateResponse(BaseModel):
    success: bool
    state: Optional[Any] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class SystemInfoResponse(BaseModel):
    """System information from MyFortress gateway."""

    platform: str = Field(description="Operating system name (legacy compatibility field)")
    os: str = Field(description="Operating system name")
    os_release: str = Field(description="OS release version")
    os_version: str = Field(description="Full OS version string")
    python_version: str = Field(description="Python runtime version")
    architecture: str = Field(description="System architecture")
    hostname: str = Field(description="System hostname")
    cpu_count: int = Field(description="Number of CPU cores")
    cpu_usage_percent: float = Field(description="Current CPU usage percentage")
    memory_total_gb: float = Field(description="Total system memory in GB")
    memory_available_gb: float = Field(description="Available system memory in GB")
    memory_usage_percent: float = Field(description="Memory usage percentage")
    disk_total_gb: float = Field(description="Total disk space in GB")
    disk_free_gb: float = Field(description="Free disk space in GB")
    disk_usage_percent: float = Field(description="Disk usage percentage")
    network_interfaces: List[str] = Field(
        default_factory=list, description="Available network interfaces"
    )
    error: Optional[str] = Field(default=None, description="Error message if retrieval failed")


class AgentPerformanceMetrics(BaseModel):
    """Performance metrics for a single agent."""

    agent_id: str = Field(description="Agent identifier")
    agent_name: str = Field(description="Agent display name")
    total_tasks: int = Field(default=0, description="Total tasks assigned")
    completed_tasks: int = Field(default=0, description="Tasks completed")
    failed_tasks: int = Field(default=0, description="Tasks failed")
    success_rate: float = Field(default=0.0, description="Success rate (0-100)")
    avg_completion_time: float = Field(
        default=0.0, description="Average completion time in minutes"
    )
    current_load: float = Field(default=0.0, description="Current load (0-1)")
    status: str = Field(default="idle", description="Current status (idle, busy, offline)")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    last_activity: Optional[str] = Field(default=None, description="Last activity timestamp")


class AgentAnalyticsResponse(BaseModel):
    """Agent analytics response."""

    total_agents: int = Field(default=0, description="Total number of agents")
    active_agents: int = Field(default=0, description="Number of active agents")
    total_tasks_completed: int = Field(
        default=0, description="Total tasks completed across all agents"
    )
    overall_success_rate: float = Field(default=0.0, description="Overall success rate (0-100)")
    avg_completion_time: float = Field(
        default=0.0, description="Average completion time across all agents"
    )
    agents: List[AgentPerformanceMetrics] = Field(
        default_factory=list, description="Individual agent metrics"
    )
    timestamp: str = Field(default="", description="Snapshot timestamp")
    error: Optional[str] = None


class PluginMetricsResponse(BaseModel):
    """Response for plugin metrics"""

    plugin_id: str = Field(description="Unique plugin identifier")
    plugin_name: str = Field(description="Human-readable plugin name")
    category: str = Field(description="Plugin category")
    total_invocations: int = Field(description="Total number of invocations")
    successful_invocations: int = Field(description="Number of successful invocations")
    failed_invocations: int = Field(description="Number of failed invocations")
    success_rate: float = Field(description="Success rate percentage")
    error_rate: float = Field(description="Error rate percentage")
    avg_execution_time_ms: float = Field(description="Average execution time in milliseconds")
    health_score: float = Field(description="Overall health score (0-100)")
    last_used: Optional[str] = Field(default=None, description="Last usage timestamp")


class PluginAnalyticsResponse(BaseModel):
    """Response for plugin analytics"""

    timestamp: str = Field(description="When the analytics were generated")
    global_stats: Dict[str, Any] = Field(description="Global plugin statistics")
    top_plugins: List[PluginMetricsResponse] = Field(
        default_factory=list, description="Top performing plugins"
    )
    comparative_analysis: Dict[str, str] = Field(
        default_factory=dict, description="Comparative analysis across plugins"
    )
    error: Optional[str] = None
