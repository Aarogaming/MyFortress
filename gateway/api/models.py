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
