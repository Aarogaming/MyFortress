from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EntityReading(BaseModel):
    entity_id: str
    state: Optional[Any] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class HomeMerlinSnapshot(BaseModel):
    healthy: bool
    readings: Dict[str, EntityReading] = Field(default_factory=dict)
    error: Optional[str] = None


class FrigateVersion(BaseModel):
    version: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class FrigateSnapshot(BaseModel):
    healthy: bool
    version: Optional[FrigateVersion] = None
    error: Optional[str] = None
    cameras: Optional[List[str]] = None


class GatewaySnapshot(BaseModel):
    home_assistant: Optional[HomeMerlinSnapshot] = None
    frigate: Optional[FrigateSnapshot] = None
