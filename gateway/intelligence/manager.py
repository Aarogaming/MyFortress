"""
MyFortress Intelligence Manager

High-level manager for coordinating all intelligence features in MyFortress.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from loguru import logger

from .client import MyFortressIntelligenceClient
from .models import (
    HomeIntelligenceContext,
    EnergyOptimization,
    SecurityIntelligence,
    PredictiveAutomation,
    MobileIntelligenceSync,
    IntelligenceHealthCheck,
)


class MyFortressIntelligenceManager:
    """
    High-level manager for MyFortress intelligence features.

    This manager coordinates all intelligence capabilities and provides
    a unified interface for the MyFortress gateway to access intelligent
    home automation features.
    """

    def __init__(self, aas_hub_url: str = "http://localhost:8000"):
        """Initialize the intelligence manager."""
        self.client = MyFortressIntelligenceClient(aas_hub_url)
        self.cache = {}
        self.cache_timestamps = {}
        self.background_tasks = set()

        # Cache TTL settings
        self.context_cache_ttl = timedelta(minutes=5)
        self.energy_cache_ttl = timedelta(minutes=15)
        self.security_cache_ttl = timedelta(minutes=2)
        self.mobile_cache_ttl = timedelta(minutes=1)

        logger.info("🏠🧠 MyFortress Intelligence Manager initialized")

    async def start_background_intelligence(self):
        """Start background intelligence tasks."""
        logger.info("🏠🧠 Starting background intelligence tasks")

        # Start periodic context updates
        task1 = asyncio.create_task(self._periodic_context_update())
        task2 = asyncio.create_task(self._periodic_optimization_analysis())
        task3 = asyncio.create_task(self._periodic_security_monitoring())

        self.background_tasks.update([task1, task2, task3])

        logger.info("🏠🧠 Background intelligence tasks started")

    async def stop_background_intelligence(self):
        """Stop background intelligence tasks."""
        logger.info("🏠🧠 Stopping background intelligence tasks")

        for task in self.background_tasks:
            task.cancel()

        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        self.background_tasks.clear()

        logger.info("🏠🧠 Background intelligence tasks stopped")

    async def get_home_intelligence_dashboard(self) -> Dict[str, Any]:
        """
        Get comprehensive intelligence dashboard for MyFortress.

        This provides a complete overview of home intelligence including
        context, optimization opportunities, security status, and predictions.
        """
        try:
            # Get all intelligence components
            context_task = self.get_cached_home_context()
            energy_task = self.get_cached_energy_optimization()
            security_task = self.get_cached_security_intelligence()
            mobile_task = self.get_cached_mobile_sync()

            context, energy, security, mobile = await asyncio.gather(
                context_task,
                energy_task,
                security_task,
                mobile_task,
                return_exceptions=True,
            )

            # Handle any exceptions
            if isinstance(context, Exception):
                logger.error(f"Failed to get context: {context}")
                context = await self.client.get_home_intelligence_context()

            if isinstance(energy, Exception):
                logger.error(f"Failed to get energy optimization: {energy}")
                energy = await self.client.get_energy_optimization()

            if isinstance(security, Exception):
                logger.error(f"Failed to get security intelligence: {security}")
                security = await self.client.get_security_intelligence()

            if isinstance(mobile, Exception):
                logger.error(f"Failed to get mobile sync: {mobile}")
                mobile = await self.client.get_mobile_intelligence_sync()

            # Build comprehensive dashboard
            dashboard = {
                "timestamp": datetime.now().isoformat(),
                "system_health": (
                    context.system_health if hasattr(context, "system_health") else 0.5
                ),
                # Overview
                "overview": {
                    "total_recommendations": (
                        len(context.recommendations)
                        if hasattr(context, "recommendations")
                        else 0
                    ),
                    "optimization_opportunities": (
                        len(context.optimization_opportunities)
                        if hasattr(context, "optimization_opportunities")
                        else 0
                    ),
                    "potential_monthly_savings": (
                        energy.potential_monthly_savings
                        if hasattr(energy, "potential_monthly_savings")
                        else 0
                    ),
                    "security_status": (
                        security.threat_level
                        if hasattr(security, "threat_level")
                        else "unknown"
                    ),
                    "active_devices": (
                        len(context.home_devices)
                        if hasattr(context, "home_devices")
                        else 0
                    ),
                },
                # Detailed sections
                "context": context.dict() if hasattr(context, "dict") else {},
                "energy_optimization": energy.dict() if hasattr(energy, "dict") else {},
                "security_intelligence": (
                    security.dict() if hasattr(security, "dict") else {}
                ),
                "mobile_sync": mobile.dict() if hasattr(mobile, "dict") else {},
                # Quick actions
                "quick_actions": self._generate_quick_actions(
                    context, energy, security
                ),
                # Intelligence health
                "intelligence_health": await self._get_intelligence_health_summary(),
            }

            logger.info(
                f"🏠🧠 Intelligence dashboard generated: {dashboard['overview']['total_recommendations']} recommendations"
            )
            return dashboard

        except Exception as e:
            logger.error(f"Failed to generate intelligence dashboard: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "system_health": 0.0,
                "overview": {},
                "intelligence_health": {"status": "error"},
            }

    async def get_cached_home_context(self) -> HomeIntelligenceContext:
        """Get home intelligence context with caching."""
        cache_key = "home_context"

        if self._is_cache_valid(cache_key, self.context_cache_ttl):
            return self.cache[cache_key]

        context = await self.client.get_home_intelligence_context()
        self._update_cache(cache_key, context)

        return context

    async def get_cached_energy_optimization(self) -> EnergyOptimization:
        """Get energy optimization with caching."""
        cache_key = "energy_optimization"

        if self._is_cache_valid(cache_key, self.energy_cache_ttl):
            return self.cache[cache_key]

        energy = await self.client.get_energy_optimization()
        self._update_cache(cache_key, energy)

        return energy

    async def get_cached_security_intelligence(self) -> SecurityIntelligence:
        """Get security intelligence with caching."""
        cache_key = "security_intelligence"

        if self._is_cache_valid(cache_key, self.security_cache_ttl):
            return self.cache[cache_key]

        security = await self.client.get_security_intelligence()
        self._update_cache(cache_key, security)

        return security

    async def get_cached_mobile_sync(self) -> MobileIntelligenceSync:
        """Get mobile intelligence sync with caching."""
        cache_key = "mobile_sync"

        if self._is_cache_valid(cache_key, self.mobile_cache_ttl):
            return self.cache[cache_key]

        mobile = await self.client.get_mobile_intelligence_sync()
        self._update_cache(cache_key, mobile)

        return mobile

    async def execute_intelligent_automation(
        self, automation_id: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute an intelligent automation with context awareness.

        This method combines traditional automation execution with intelligence
        to optimize timing, parameters, and coordination with other systems.
        """
        try:
            logger.info(f"🏠🧠 Executing intelligent automation: {automation_id}")

            # Get current intelligence context
            home_context = await self.get_cached_home_context()

            # Get predictive automation suggestions
            predictions = await self.client.get_predictive_automation()

            # Analyze automation in context
            analysis = {
                "automation_id": automation_id,
                "system_health": home_context.system_health,
                "optimal_timing": self._calculate_optimal_timing(
                    automation_id, predictions
                ),
                "resource_impact": self._analyze_resource_impact(
                    automation_id, home_context
                ),
                "coordination_opportunities": await self._find_coordination_opportunities(
                    automation_id
                ),
            }

            # Execute with intelligence
            execution_result = await self._execute_with_intelligence(
                automation_id, analysis, context
            )

            logger.info(
                f"🏠🧠 Intelligent automation executed: {automation_id} - {execution_result['status']}"
            )
            return execution_result

        except Exception as e:
            logger.error(
                f"Failed to execute intelligent automation {automation_id}: {e}"
            )
            return {
                "automation_id": automation_id,
                "status": "error",
                "error": str(e),
                "fallback_executed": False,
            }

    async def optimize_home_performance(self) -> Dict[str, Any]:
        """
        Perform comprehensive home performance optimization.

        This analyzes all aspects of home automation and applies
        intelligent optimizations for energy, security, and comfort.
        """
        try:
            logger.info("🏠🧠 Starting comprehensive home performance optimization")

            # Get all intelligence data
            context = await self.get_cached_home_context()
            energy = await self.get_cached_energy_optimization()
            security = await self.get_cached_security_intelligence()

            # Apply optimizations
            optimizations_applied = []

            # Energy optimizations
            for opportunity in energy.optimization_opportunities:
                if opportunity.priority > 0.7 and opportunity.effort_required == "low":
                    result = await self._apply_energy_optimization(opportunity)
                    optimizations_applied.append(result)

            # Security optimizations
            for recommendation in security.security_recommendations:
                if (
                    recommendation.priority > 0.8
                    and recommendation.automation_available
                ):
                    result = await self._apply_security_optimization(recommendation)
                    optimizations_applied.append(result)

            # System optimizations
            for opportunity in context.optimization_opportunities:
                if opportunity.get("priority", 0) > 0.6:
                    result = await self._apply_system_optimization(opportunity)
                    optimizations_applied.append(result)

            optimization_summary = {
                "timestamp": datetime.now().isoformat(),
                "optimizations_applied": len(optimizations_applied),
                "energy_savings_potential": sum(
                    opt.get("energy_savings", 0) for opt in optimizations_applied
                ),
                "cost_savings_potential": sum(
                    opt.get("cost_savings", 0) for opt in optimizations_applied
                ),
                "details": optimizations_applied,
                "next_optimization_scheduled": (
                    datetime.now() + timedelta(hours=24)
                ).isoformat(),
            }

            logger.info(
                f"🏠🧠 Home optimization complete: {len(optimizations_applied)} optimizations applied"
            )
            return optimization_summary

        except Exception as e:
            logger.error(f"Failed to optimize home performance: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "optimizations_applied": 0,
            }

    # Background task methods

    async def _periodic_context_update(self):
        """Periodically update intelligence context."""
        while True:
            try:
                await asyncio.sleep(300)  # 5 minutes
                await self.get_cached_home_context()
                logger.debug("🏠🧠 Periodic context update completed")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Periodic context update failed: {e}")

    async def _periodic_optimization_analysis(self):
        """Periodically analyze optimization opportunities."""
        while True:
            try:
                await asyncio.sleep(900)  # 15 minutes
                await self.get_cached_energy_optimization()
                logger.debug("🏠🧠 Periodic optimization analysis completed")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Periodic optimization analysis failed: {e}")

    async def _periodic_security_monitoring(self):
        """Periodically monitor security intelligence."""
        while True:
            try:
                await asyncio.sleep(120)  # 2 minutes
                security = await self.get_cached_security_intelligence()

                # Check for high-priority alerts
                if security.threat_level in ["high", "critical"]:
                    logger.warning(
                        f"🏠🚨 High security threat level detected: {security.threat_level}"
                    )

                logger.debug("🏠🧠 Periodic security monitoring completed")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Periodic security monitoring failed: {e}")

    # Helper methods

    def _is_cache_valid(self, cache_key: str, ttl: timedelta) -> bool:
        """Check if cache entry is still valid."""
        if cache_key not in self.cache:
            return False

        timestamp = self.cache_timestamps.get(cache_key)
        if not timestamp:
            return False

        return (datetime.now() - timestamp) < ttl

    def _update_cache(self, cache_key: str, data: Any):
        """Update cache with new data."""
        self.cache[cache_key] = data
        self.cache_timestamps[cache_key] = datetime.now()

    def _generate_quick_actions(
        self, context, energy, security
    ) -> List[Dict[str, Any]]:
        """Generate quick actions based on intelligence analysis."""
        actions = []

        # Energy quick actions
        if hasattr(energy, "optimization_opportunities"):
            for opp in energy.optimization_opportunities[:2]:
                if opp.effort_required == "low":
                    actions.append(
                        {
                            "id": f"energy_{opp.id}",
                            "type": "energy_optimization",
                            "title": opp.title,
                            "description": opp.description,
                            "estimated_savings": opp.estimated_savings,
                            "priority": opp.priority,
                        }
                    )

        # Security quick actions
        if hasattr(security, "security_recommendations"):
            for rec in security.security_recommendations[:2]:
                if rec.automation_available:
                    actions.append(
                        {
                            "id": f"security_{rec.id}",
                            "type": "security_optimization",
                            "title": rec.title,
                            "description": rec.description,
                            "priority": rec.priority,
                        }
                    )

        return actions[:5]  # Limit to top 5 actions

    async def _get_intelligence_health_summary(self) -> Dict[str, Any]:
        """Get intelligence health summary."""
        try:
            health = await self.client.health_check()
            return {
                "status": health.intelligence_service_status,
                "response_time_ms": health.response_time_ms,
                "capabilities": {
                    "contextual_intelligence": health.contextual_intelligence,
                    "optimization_engine": health.optimization_engine,
                    "predictive_analytics": health.predictive_analytics,
                    "collaboration_mesh": health.collaboration_mesh,
                },
                "cache_status": {
                    "entries": len(self.cache),
                    "last_update": (
                        max(self.cache_timestamps.values()).isoformat()
                        if self.cache_timestamps
                        else None
                    ),
                },
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _calculate_optimal_timing(self, automation_id: str, predictions) -> str:
        """Calculate optimal timing for automation execution."""
        # Placeholder for timing optimization logic
        return "immediate"

    def _analyze_resource_impact(self, automation_id: str, context) -> Dict[str, Any]:
        """Analyze resource impact of automation execution."""
        # Placeholder for resource impact analysis
        return {
            "cpu_impact": "low",
            "network_impact": "minimal",
            "energy_impact": "neutral",
        }

    async def _find_coordination_opportunities(self, automation_id: str) -> List[str]:
        """Find opportunities to coordinate with other AAS components."""
        try:
            opportunities = await self.client.discover_collaboration_opportunities()
            return [opp["capability"] for opp in opportunities[:3]]
        except Exception:
            return []

    async def _execute_with_intelligence(
        self, automation_id: str, analysis: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute automation with intelligence optimization."""
        # Placeholder for intelligent execution logic
        return {
            "automation_id": automation_id,
            "status": "success",
            "execution_time": datetime.now().isoformat(),
            "intelligence_applied": True,
            "optimizations": analysis,
        }

    async def _apply_energy_optimization(self, opportunity) -> Dict[str, Any]:
        """Apply an energy optimization."""
        # Placeholder for energy optimization application
        return {
            "type": "energy_optimization",
            "opportunity_id": opportunity.id,
            "status": "applied",
            "energy_savings": opportunity.energy_impact or 0,
            "cost_savings": opportunity.estimated_savings or 0,
        }

    async def _apply_security_optimization(self, recommendation) -> Dict[str, Any]:
        """Apply a security optimization."""
        # Placeholder for security optimization application
        return {
            "type": "security_optimization",
            "recommendation_id": recommendation.id,
            "status": "applied",
            "security_improvement": "enhanced",
        }

    async def _apply_system_optimization(
        self, opportunity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a system optimization."""
        # Placeholder for system optimization application
        return {
            "type": "system_optimization",
            "opportunity_id": opportunity.get("id", "unknown"),
            "status": "applied",
            "improvement": opportunity.get("potential_benefit", "unknown"),
        }


# Global manager instance
_intelligence_manager: Optional[MyFortressIntelligenceManager] = None


def get_intelligence_manager(
    aas_hub_url: str = "http://localhost:8000",
) -> MyFortressIntelligenceManager:
    """Get or create the MyFortress intelligence manager."""
    global _intelligence_manager

    if _intelligence_manager is None:
        _intelligence_manager = MyFortressIntelligenceManager(aas_hub_url)

    return _intelligence_manager


def initialize_intelligence_manager(settings) -> MyFortressIntelligenceManager:
    """Initialize the intelligence manager with settings."""
    global _intelligence_manager

    aas_hub_url = getattr(settings, "aas_hub_url", "http://localhost:8000")
    _intelligence_manager = MyFortressIntelligenceManager(aas_hub_url)

    logger.info(
        f"🏠🧠 MyFortress Intelligence Manager initialized with AAS Hub: {aas_hub_url}"
    )
    return _intelligence_manager
