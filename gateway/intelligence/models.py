"""
MyFortress Intelligence Models

Data models for intelligent home automation features.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HomeIntelligenceContext(BaseModel):
    """Complete intelligence context for home automation."""

    timestamp: datetime = Field(default_factory=datetime.now)
    system_health: float = Field(ge=0.0, le=1.0, description="Overall system health score")

    # Environmental context
    environmental_context: Dict[str, Any] = Field(default_factory=dict)
    system_resources: List[Dict[str, Any]] = Field(default_factory=list)
    network_status: Dict[str, Any] = Field(default_factory=dict)

    # Home-specific context
    home_devices: List[Dict[str, Any]] = Field(default_factory=list)
    energy_usage: Dict[str, float] = Field(default_factory=dict)
    security_status: Dict[str, Any] = Field(default_factory=dict)
    occupancy_patterns: Dict[str, Any] = Field(default_factory=dict)

    # Intelligence insights
    optimization_opportunities: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    predictive_insights: Dict[str, Any] = Field(default_factory=dict)


class HomeOptimizationRecommendation(BaseModel):
    """A specific optimization recommendation for home automation."""

    id: str
    category: str = Field(description="Category: energy, security, comfort, maintenance")
    title: str
    description: str
    potential_benefit: str
    effort_required: str = Field(description="low, medium, high")
    priority: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)

    # Home-specific fields
    affected_devices: List[str] = Field(default_factory=list)
    estimated_savings: Optional[float] = Field(None, description="Monthly savings in dollars")
    energy_impact: Optional[float] = Field(None, description="Energy savings in kWh/month")

    action_items: List[str] = Field(default_factory=list)
    automation_available: bool = Field(default=False)

    created_at: datetime = Field(default_factory=datetime.now)


class EnergyOptimization(BaseModel):
    """Energy optimization analysis and recommendations."""

    current_usage: Dict[str, float] = Field(
        default_factory=dict, description="Current usage by device/area"
    )
    usage_patterns: Dict[str, Any] = Field(default_factory=dict)
    peak_hours: List[int] = Field(default_factory=list)

    optimization_opportunities: List[HomeOptimizationRecommendation] = Field(default_factory=list)
    potential_monthly_savings: float = Field(default=0.0)
    recommended_schedule_changes: List[Dict[str, Any]] = Field(default_factory=list)

    smart_device_recommendations: List[str] = Field(default_factory=list)
    behavioral_recommendations: List[str] = Field(default_factory=list)


class SecurityIntelligence(BaseModel):
    """Security intelligence analysis and recommendations."""

    threat_level: str = Field(default="low", description="low, medium, high, critical")
    active_alerts: List[Dict[str, Any]] = Field(default_factory=list)

    # Anomaly detection
    unusual_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    access_patterns: Dict[str, Any] = Field(default_factory=dict)

    # Recommendations
    security_recommendations: List[HomeOptimizationRecommendation] = Field(default_factory=list)
    suggested_automations: List[Dict[str, Any]] = Field(default_factory=list)

    # Device status
    security_devices: List[Dict[str, Any]] = Field(default_factory=list)
    camera_status: Dict[str, Any] = Field(default_factory=dict)


class PredictiveAutomation(BaseModel):
    """Predictive automation suggestions based on patterns and context."""

    predicted_actions: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)

    # Pattern-based predictions
    occupancy_predictions: Dict[str, Any] = Field(default_factory=dict)
    device_usage_predictions: Dict[str, Any] = Field(default_factory=dict)

    # Suggested automations
    new_automation_suggestions: List[Dict[str, Any]] = Field(default_factory=list)
    automation_optimizations: List[Dict[str, Any]] = Field(default_factory=list)

    # Context-aware suggestions
    weather_based_suggestions: List[str] = Field(default_factory=list)
    time_based_suggestions: List[str] = Field(default_factory=list)
    event_based_suggestions: List[str] = Field(default_factory=list)


class MobileIntelligenceSync(BaseModel):
    """Intelligence data synchronized with mobile app."""

    home_status_summary: Dict[str, Any] = Field(default_factory=dict)
    priority_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    quick_actions: List[Dict[str, Any]] = Field(default_factory=list)

    # Mobile-specific insights
    location_based_suggestions: List[str] = Field(default_factory=list)
    arrival_predictions: Dict[str, Any] = Field(default_factory=dict)
    departure_automations: List[Dict[str, Any]] = Field(default_factory=list)

    # Personalization
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    usage_patterns: Dict[str, Any] = Field(default_factory=dict)

    last_sync: datetime = Field(default_factory=datetime.now)


class IntelligenceHealthCheck(BaseModel):
    """Health check for intelligence services."""

    intelligence_service_status: str = Field(description="healthy, degraded, error")
    last_update: datetime = Field(default_factory=datetime.now)

    # Service capabilities
    contextual_intelligence: bool = Field(default=False)
    optimization_engine: bool = Field(default=False)
    predictive_analytics: bool = Field(default=False)
    collaboration_mesh: bool = Field(default=False)

    # Performance metrics
    response_time_ms: float = Field(default=0.0)
    cache_hit_rate: float = Field(default=0.0)
    recommendation_count: int = Field(default=0)

    error_details: Optional[str] = Field(None)
