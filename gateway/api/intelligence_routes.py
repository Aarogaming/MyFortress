"""
MyFortress Intelligence API Routes

REST API endpoints for accessing MyFortress intelligence features.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from gateway.config import Settings, get_settings
from gateway.intelligence.manager import get_intelligence_manager
from gateway.intelligence.models import (
    HomeIntelligenceContext,
    EnergyOptimization,
    SecurityIntelligence,
    PredictiveAutomation,
    MobileIntelligenceSync,
    IntelligenceHealthCheck,
)

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


# Request/Response models
class IntelligentAutomationRequest(BaseModel):
    automation_id: str
    context: Optional[Dict[str, Any]] = None


class IntelligentAutomationResponse(BaseModel):
    automation_id: str
    status: str
    execution_time: str
    intelligence_applied: bool
    optimizations: Dict[str, Any]
    error: Optional[str] = None


class HomeOptimizationRequest(BaseModel):
    include_energy: bool = True
    include_security: bool = True
    include_system: bool = True
    apply_optimizations: bool = False


class HomeOptimizationResponse(BaseModel):
    timestamp: str
    optimizations_applied: int
    energy_savings_potential: float
    cost_savings_potential: float
    details: list
    error: Optional[str] = None


@router.get(
    "/dashboard",
    summary="Get comprehensive intelligence dashboard",
    description="Get complete home intelligence overview including context, optimization opportunities, and predictions",
)
async def get_intelligence_dashboard(
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """Get comprehensive intelligence dashboard for MyFortress."""
    try:
        manager = get_intelligence_manager()
        dashboard = await manager.get_home_intelligence_dashboard()
        return {"success": True, "data": dashboard}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get intelligence dashboard: {e}"
        )


@router.get(
    "/context",
    response_model=HomeIntelligenceContext,
    summary="Get home intelligence context",
    description="Get environmental context, system resources, and optimization opportunities for home automation",
)
async def get_home_intelligence_context(
    include_opportunities: bool = Query(
        True, description="Include optimization opportunities"
    ),
    include_predictions: bool = Query(True, description="Include predictive insights"),
    settings: Settings = Depends(get_settings),
):
    """Get home intelligence context."""
    try:
        manager = get_intelligence_manager()
        context = await manager.get_cached_home_context()
        return context
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get home intelligence context: {e}"
        )


@router.get(
    "/energy",
    response_model=EnergyOptimization,
    summary="Get energy optimization recommendations",
    description="Get intelligent energy usage analysis and optimization recommendations",
)
async def get_energy_optimization(settings: Settings = Depends(get_settings)):
    """Get energy optimization recommendations."""
    try:
        manager = get_intelligence_manager()
        energy = await manager.get_cached_energy_optimization()
        return energy
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get energy optimization: {e}"
        )


@router.get(
    "/security",
    response_model=SecurityIntelligence,
    summary="Get security intelligence analysis",
    description="Get security threat assessment, anomaly detection, and security recommendations",
)
async def get_security_intelligence(settings: Settings = Depends(get_settings)):
    """Get security intelligence analysis."""
    try:
        manager = get_intelligence_manager()
        security = await manager.get_cached_security_intelligence()
        return security
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get security intelligence: {e}"
        )


@router.get(
    "/predictions",
    response_model=PredictiveAutomation,
    summary="Get predictive automation suggestions",
    description="Get AI-powered predictions and automation suggestions based on patterns and context",
)
async def get_predictive_automation(settings: Settings = Depends(get_settings)):
    """Get predictive automation suggestions."""
    try:
        manager = get_intelligence_manager()
        client = manager.client
        predictions = await client.get_predictive_automation()
        return predictions
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get predictive automation: {e}"
        )


@router.get(
    "/mobile-sync",
    response_model=MobileIntelligenceSync,
    summary="Get mobile intelligence sync data",
    description="Get intelligence data optimized for mobile app (AndroidApp/Mansion) synchronization",
)
async def get_mobile_intelligence_sync(settings: Settings = Depends(get_settings)):
    """Get mobile intelligence sync data."""
    try:
        manager = get_intelligence_manager()
        mobile_sync = await manager.get_cached_mobile_sync()
        return mobile_sync
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get mobile intelligence sync: {e}"
        )


@router.get(
    "/health",
    response_model=IntelligenceHealthCheck,
    summary="Check intelligence service health",
    description="Check the health and status of all intelligence services and capabilities",
)
async def intelligence_health_check(settings: Settings = Depends(get_settings)):
    """Check intelligence service health."""
    try:
        manager = get_intelligence_manager()
        health = await manager.client.health_check()
        return health
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Intelligence health check failed: {e}"
        )


@router.get(
    "/recommendations",
    summary="Get smart recommendations",
    description="Get context-aware smart recommendations for home automation optimization",
)
async def get_smart_recommendations(
    context: Optional[str] = Query(
        None, description="Context filter: energy, security, comfort, performance"
    ),
    limit: int = Query(
        10, ge=1, le=50, description="Maximum number of recommendations"
    ),
    settings: Settings = Depends(get_settings),
):
    """Get smart recommendations for home automation."""
    try:
        manager = get_intelligence_manager()
        home_context = await manager.get_cached_home_context()

        # Filter recommendations by context if specified
        recommendations = home_context.recommendations
        if context:
            recommendations = [
                rec for rec in recommendations if context.lower() in rec.lower()
            ]

        return {
            "success": True,
            "data": {
                "recommendations": recommendations[:limit],
                "total_available": len(home_context.recommendations),
                "context_filter": context,
                "timestamp": home_context.timestamp.isoformat(),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get recommendations: {e}"
        )


@router.get(
    "/collaboration",
    summary="Get collaboration opportunities",
    description="Discover opportunities for MyFortress to collaborate with other AAS components",
)
async def get_collaboration_opportunities(settings: Settings = Depends(get_settings)):
    """Get collaboration opportunities with other AAS components."""
    try:
        manager = get_intelligence_manager()
        opportunities = await manager.client.discover_collaboration_opportunities()

        return {
            "success": True,
            "data": {
                "opportunities": opportunities,
                "total_opportunities": len(opportunities),
                "timestamp": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get collaboration opportunities: {e}"
        )


@router.post(
    "/automation/execute",
    response_model=IntelligentAutomationResponse,
    summary="Execute intelligent automation",
    description="Execute home automation with intelligence optimization and context awareness",
)
async def execute_intelligent_automation(
    request: IntelligentAutomationRequest, settings: Settings = Depends(get_settings)
):
    """Execute intelligent automation with context awareness."""
    try:
        manager = get_intelligence_manager()
        result = await manager.execute_intelligent_automation(
            automation_id=request.automation_id, context=request.context
        )

        return IntelligentAutomationResponse(
            automation_id=result["automation_id"],
            status=result["status"],
            execution_time=result["execution_time"],
            intelligence_applied=result["intelligence_applied"],
            optimizations=result["optimizations"],
            error=result.get("error"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to execute intelligent automation: {e}"
        )


@router.post(
    "/optimize",
    response_model=HomeOptimizationResponse,
    summary="Optimize home performance",
    description="Perform comprehensive home performance optimization using AI analysis",
)
async def optimize_home_performance(
    request: HomeOptimizationRequest, settings: Settings = Depends(get_settings)
):
    """Perform comprehensive home performance optimization."""
    try:
        manager = get_intelligence_manager()

        if request.apply_optimizations:
            result = await manager.optimize_home_performance()
        else:
            # Just analyze without applying
            dashboard = await manager.get_home_intelligence_dashboard()
            result = {
                "timestamp": dashboard["timestamp"],
                "optimizations_applied": 0,
                "energy_savings_potential": dashboard["overview"].get(
                    "potential_monthly_savings", 0
                ),
                "cost_savings_potential": dashboard["overview"].get(
                    "potential_monthly_savings", 0
                ),
                "details": dashboard["quick_actions"],
            }

        return HomeOptimizationResponse(
            timestamp=result["timestamp"],
            optimizations_applied=result["optimizations_applied"],
            energy_savings_potential=result.get("energy_savings_potential", 0),
            cost_savings_potential=result.get("cost_savings_potential", 0),
            details=result.get("details", []),
            error=result.get("error"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to optimize home performance: {e}"
        )


@router.get(
    "/status",
    summary="Get intelligence status summary",
    description="Get quick status summary of intelligence services and capabilities",
)
async def get_intelligence_status(settings: Settings = Depends(get_settings)):
    """Get quick intelligence status summary."""
    try:
        manager = get_intelligence_manager()
        status = manager.client.get_quick_status()

        return {
            "success": True,
            "data": {
                "intelligence_service": status.get("intelligence_service", "unknown"),
                "system_health": status.get("system_health", 0.5),
                "active_recommendations": status.get("active_recommendations", 0),
                "top_recommendation": status.get("top_recommendation"),
                "last_update": status.get("last_update"),
                "cache_status": {
                    "entries": len(manager.cache),
                    "last_refresh": (
                        max(manager.cache_timestamps.values()).isoformat()
                        if manager.cache_timestamps
                        else None
                    ),
                },
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get intelligence status: {e}"
        )


# Background task management endpoints


@router.post(
    "/background/start",
    summary="Start background intelligence tasks",
    description="Start background tasks for continuous intelligence monitoring and optimization",
)
async def start_background_intelligence(settings: Settings = Depends(get_settings)):
    """Start background intelligence tasks."""
    try:
        manager = get_intelligence_manager()
        await manager.start_background_intelligence()

        return {
            "success": True,
            "message": "Background intelligence tasks started",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start background intelligence: {e}"
        )


@router.post(
    "/background/stop",
    summary="Stop background intelligence tasks",
    description="Stop background intelligence monitoring and optimization tasks",
)
async def stop_background_intelligence(settings: Settings = Depends(get_settings)):
    """Stop background intelligence tasks."""
    try:
        manager = get_intelligence_manager()
        await manager.stop_background_intelligence()

        return {
            "success": True,
            "message": "Background intelligence tasks stopped",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to stop background intelligence: {e}"
        )


# Import datetime for timestamp generation
from datetime import datetime
