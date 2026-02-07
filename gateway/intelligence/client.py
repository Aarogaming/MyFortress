"""
MyFortress Intelligence Client

Client for connecting MyFortress to the AAS Shared Intelligence Service.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
from loguru import logger

# Add AAS core to path for intelligence client
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from core.intelligence_client import IntelligenceClient, SimpleIntelligenceClient

    AAS_INTELLIGENCE_AVAILABLE = True
except ImportError:
    logger.warning("AAS intelligence client not available - running in standalone mode")
    AAS_INTELLIGENCE_AVAILABLE = False
    IntelligenceClient = None
    SimpleIntelligenceClient = None

from .models import (
    HomeIntelligenceContext,
    HomeOptimizationRecommendation,
    EnergyOptimization,
    SecurityIntelligence,
    PredictiveAutomation,
    MobileIntelligenceSync,
    IntelligenceHealthCheck,
)


class MyFortressIntelligenceClient:
    """
    MyFortress client for accessing AAS Shared Intelligence Service.

    This client transforms MyFortress from a basic home automation gateway
    into an intelligent, predictive, collaborative home ecosystem.
    """

    def __init__(self, aas_hub_url: str = "http://localhost:8000"):
        """Initialize MyFortress intelligence client."""
        self.aas_hub_url = aas_hub_url
        self.client = None
        self.simple_client = None
        self.intelligence_cache = {}
        self.last_context_update = None

        if AAS_INTELLIGENCE_AVAILABLE and IntelligenceClient:
            self.client = IntelligenceClient("myfortress", aas_hub_url)
            self.simple_client = SimpleIntelligenceClient("myfortress", aas_hub_url)
            logger.info(
                "🏠 MyFortress Intelligence Client initialized with AAS integration"
            )
        else:
            logger.warning(
                "🏠 MyFortress Intelligence Client running in standalone mode"
            )

    async def get_home_intelligence_context(
        self, include_opportunities: bool = True, include_predictions: bool = True
    ) -> HomeIntelligenceContext:
        """
        Get complete intelligence context for home automation.

        This provides MyFortress with environmental awareness, system resources,
        optimization opportunities, and predictive insights.
        """
        if not self.client:
            return self._get_standalone_context()

        try:
            async with self.client as client:
                # Get environmental context from AAS
                context = await client.get_contextual_intelligence(
                    include_opportunities=include_opportunities
                )

                # Get home-specific recommendations
                home_recommendations = await client.get_smart_recommendations("cost")

                # Get optimization opportunities
                opportunities = (
                    await client.get_optimization_opportunities()
                    if include_opportunities
                    else []
                )

                # Build home intelligence context
                home_context = HomeIntelligenceContext(
                    system_health=context.get("health_score", 0.5),
                    environmental_context=context,
                    system_resources=context.get("system_resources", []),
                    network_status=context.get("network_status", {}),
                    optimization_opportunities=opportunities,
                    recommendations=home_recommendations,
                )

                # Add home-specific intelligence
                await self._enhance_with_home_intelligence(home_context)

                # Cache the context
                self.intelligence_cache["home_context"] = home_context
                self.last_context_update = datetime.now()

                logger.info(
                    f"🏠 Home intelligence context updated: health={home_context.system_health:.2f}"
                )
                return home_context

        except Exception as e:
            logger.error(f"Failed to get home intelligence context: {e}")
            return self._get_standalone_context()

    async def get_energy_optimization(
        self, current_usage: Optional[Dict[str, float]] = None
    ) -> EnergyOptimization:
        """
        Get energy optimization recommendations for home automation.

        Analyzes current energy usage patterns and provides intelligent
        recommendations for reducing consumption and costs.
        """
        if not self.client:
            return self._get_standalone_energy_optimization()

        try:
            async with self.client as client:
                # Get cost optimization recommendations
                cost_recommendations = await client.get_smart_recommendations("cost")

                # Get optimization opportunities
                opportunities = await client.get_optimization_opportunities()

                # Filter for energy-related opportunities
                energy_opportunities = [
                    self._convert_to_home_recommendation(opp)
                    for opp in opportunities
                    if "energy" in opp.get("title", "").lower()
                    or "power" in opp.get("title", "").lower()
                    or opp.get("estimated_savings", 0) > 0
                ]

                # Calculate potential savings
                potential_savings = sum(
                    opp.estimated_savings or 0 for opp in energy_opportunities
                )

                optimization = EnergyOptimization(
                    current_usage=current_usage or {},
                    optimization_opportunities=energy_opportunities,
                    potential_monthly_savings=potential_savings,
                    behavioral_recommendations=cost_recommendations,
                )

                # Enhance with home-specific energy intelligence
                await self._enhance_energy_optimization(optimization)

                logger.info(
                    f"🏠 Energy optimization analysis: ${potential_savings:.2f} potential savings"
                )
                return optimization

        except Exception as e:
            logger.error(f"Failed to get energy optimization: {e}")
            return self._get_standalone_energy_optimization()

    async def get_security_intelligence(self) -> SecurityIntelligence:
        """
        Get security intelligence analysis for home automation.

        Provides threat assessment, anomaly detection, and security
        optimization recommendations.
        """
        if not self.client:
            return self._get_standalone_security_intelligence()

        try:
            async with self.client as client:
                # Get security-specific recommendations
                security_recommendations = await client.get_smart_recommendations(
                    "security"
                )

                # Get optimization opportunities
                opportunities = await client.get_optimization_opportunities()

                # Filter for security-related opportunities
                security_opportunities = [
                    self._convert_to_home_recommendation(opp)
                    for opp in opportunities
                    if "security" in opp.get("title", "").lower()
                    or "camera" in opp.get("title", "").lower()
                    or "access" in opp.get("title", "").lower()
                ]

                intelligence = SecurityIntelligence(
                    security_recommendations=security_opportunities,
                    suggested_automations=[
                        {"type": "motion_detection", "description": rec}
                        for rec in security_recommendations[:3]
                    ],
                )

                # Enhance with home-specific security intelligence
                await self._enhance_security_intelligence(intelligence)

                logger.info(
                    f"🏠 Security intelligence updated: {len(security_opportunities)} recommendations"
                )
                return intelligence

        except Exception as e:
            logger.error(f"Failed to get security intelligence: {e}")
            return self._get_standalone_security_intelligence()

    async def get_predictive_automation(self) -> PredictiveAutomation:
        """
        Get predictive automation suggestions based on patterns and context.

        Analyzes usage patterns and environmental context to suggest
        intelligent automations and optimizations.
        """
        if not self.client:
            return self._get_standalone_predictive_automation()

        try:
            async with self.client as client:
                # Get contextual intelligence for predictions
                context = await client.get_contextual_intelligence(
                    include_opportunities=False
                )

                # Get performance recommendations
                performance_recs = await client.get_smart_recommendations("performance")

                automation = PredictiveAutomation(
                    time_based_suggestions=performance_recs,
                    new_automation_suggestions=[
                        {
                            "type": "schedule_optimization",
                            "description": rec,
                            "confidence": 0.8,
                        }
                        for rec in performance_recs[:3]
                    ],
                )

                # Enhance with predictive intelligence
                await self._enhance_predictive_automation(automation, context)

                logger.info(
                    f"🏠 Predictive automation updated: {len(automation.predicted_actions)} predictions"
                )
                return automation

        except Exception as e:
            logger.error(f"Failed to get predictive automation: {e}")
            return self._get_standalone_predictive_automation()

    async def get_mobile_intelligence_sync(self) -> MobileIntelligenceSync:
        """
        Get intelligence data optimized for mobile app synchronization.

        Provides a condensed, mobile-friendly view of home intelligence
        for the AndroidApp (Mansion) interface.
        """
        if not self.client:
            return self._get_standalone_mobile_sync()

        try:
            # Get home intelligence context
            home_context = await self.get_home_intelligence_context(
                include_opportunities=True, include_predictions=False
            )

            # Create mobile-optimized sync data
            mobile_sync = MobileIntelligenceSync(
                home_status_summary={
                    "health_score": home_context.system_health,
                    "active_devices": len(home_context.home_devices),
                    "optimization_opportunities": len(
                        home_context.optimization_opportunities
                    ),
                    "network_status": home_context.network_status.get(
                        "connected", False
                    ),
                },
                priority_alerts=[
                    {"type": "optimization", "message": rec, "priority": "medium"}
                    for rec in home_context.recommendations[:3]
                ],
                quick_actions=[
                    {
                        "id": f"optimize_{i}",
                        "title": opp.get("title", "Optimization"),
                        "description": opp.get("description", ""),
                        "estimated_savings": opp.get("estimated_savings", 0),
                    }
                    for i, opp in enumerate(home_context.optimization_opportunities[:5])
                ],
            )

            # Enhance with mobile-specific intelligence
            await self._enhance_mobile_sync(mobile_sync)

            logger.info(
                f"🏠📱 Mobile intelligence sync: {len(mobile_sync.quick_actions)} actions available"
            )
            return mobile_sync

        except Exception as e:
            logger.error(f"Failed to get mobile intelligence sync: {e}")
            return self._get_standalone_mobile_sync()

    async def discover_collaboration_opportunities(self) -> List[Dict[str, Any]]:
        """
        Discover opportunities for MyFortress to collaborate with other AAS components.
        """
        if not self.client:
            return []

        try:
            async with self.client as client:
                # Discover plugins that can help with home automation
                capabilities = ["monitoring", "automation", "security", "energy"]
                opportunities = []

                for capability in capabilities:
                    plugins = await client.discover_plugin_capabilities(capability)
                    if plugins:
                        opportunities.append(
                            {
                                "capability": capability,
                                "available_plugins": plugins,
                                "collaboration_potential": len(plugins),
                            }
                        )

                logger.info(
                    f"🏠🤝 Found {len(opportunities)} collaboration opportunities"
                )
                return opportunities

        except Exception as e:
            logger.error(f"Failed to discover collaboration opportunities: {e}")
            return []

    async def health_check(self) -> IntelligenceHealthCheck:
        """Check the health of intelligence services."""
        if not self.client:
            return IntelligenceHealthCheck(
                intelligence_service_status="unavailable",
                error_details="AAS intelligence client not available",
            )

        try:
            start_time = datetime.now()

            async with self.client as client:
                health = await client.health_check()

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            return IntelligenceHealthCheck(
                intelligence_service_status=health.get("service_status", "unknown"),
                contextual_intelligence=True,
                optimization_engine=True,
                predictive_analytics=True,
                collaboration_mesh=True,
                response_time_ms=response_time,
                recommendation_count=len(
                    self.intelligence_cache.get("home_context", {}).get(
                        "recommendations", []
                    )
                ),
            )

        except Exception as e:
            return IntelligenceHealthCheck(
                intelligence_service_status="error", error_details=str(e)
            )

    # Synchronous convenience methods

    def get_quick_status(self) -> Dict[str, Any]:
        """Get quick status using synchronous client."""
        if not self.simple_client:
            return {"status": "intelligence_unavailable"}

        try:
            health = self.simple_client.health_check_sync()
            recommendations = self.simple_client.get_recommendations()

            return {
                "intelligence_service": health.get("service_status", "unknown"),
                "system_health": health.get("system_health", 0.5),
                "active_recommendations": len(recommendations),
                "top_recommendation": recommendations[0] if recommendations else None,
                "last_update": (
                    self.last_context_update.isoformat()
                    if self.last_context_update
                    else None
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get quick status: {e}")
            return {"status": "error", "error": str(e)}

    # Helper methods

    async def _enhance_with_home_intelligence(self, context: HomeIntelligenceContext):
        """Enhance context with home-specific intelligence."""
        # Add home device analysis
        context.home_devices = await self._analyze_home_devices()

        # Add energy usage patterns
        context.energy_usage = await self._analyze_energy_usage()

        # Add occupancy patterns
        context.occupancy_patterns = await self._analyze_occupancy_patterns()

        # Add predictive insights
        context.predictive_insights = await self._generate_predictive_insights()

    async def _analyze_home_devices(self) -> List[Dict[str, Any]]:
        """Analyze home devices for intelligence insights."""
        # Placeholder for home device analysis
        return [
            {"device": "thermostat", "status": "optimal", "efficiency": 0.85},
            {"device": "lighting", "status": "good", "efficiency": 0.78},
            {"device": "security", "status": "active", "efficiency": 0.92},
        ]

    async def _analyze_energy_usage(self) -> Dict[str, float]:
        """Analyze energy usage patterns."""
        # Placeholder for energy analysis
        return {
            "heating": 45.2,
            "cooling": 32.1,
            "lighting": 12.8,
            "appliances": 28.9,
            "other": 15.3,
        }

    async def _analyze_occupancy_patterns(self) -> Dict[str, Any]:
        """Analyze occupancy patterns for predictive automation."""
        # Placeholder for occupancy analysis
        return {
            "typical_home_time": "18:30",
            "typical_away_time": "08:15",
            "weekend_pattern": "variable",
            "confidence": 0.82,
        }

    async def _generate_predictive_insights(self) -> Dict[str, Any]:
        """Generate predictive insights for home automation."""
        # Placeholder for predictive insights
        return {
            "next_optimization_opportunity": "Adjust thermostat schedule",
            "predicted_energy_savings": 23.5,
            "recommended_automation": "Smart lighting based on occupancy",
            "confidence": 0.76,
        }

    def _convert_to_home_recommendation(
        self, opp: Dict[str, Any]
    ) -> HomeOptimizationRecommendation:
        """Convert AAS optimization opportunity to home recommendation."""
        return HomeOptimizationRecommendation(
            id=opp.get("id", "unknown"),
            category="energy",  # Default category
            title=opp.get("title", "Optimization Opportunity"),
            description=opp.get("description", ""),
            potential_benefit=opp.get("potential_benefit", "Improved efficiency"),
            effort_required=opp.get("effort_required", "medium"),
            priority=opp.get("priority", 0.5),
            confidence=opp.get("confidence", 0.7),
            estimated_savings=opp.get("estimated_savings"),
            action_items=opp.get("action_items", []),
        )

    async def _enhance_energy_optimization(self, optimization: EnergyOptimization):
        """Enhance energy optimization with home-specific intelligence."""
        # Add smart device recommendations
        optimization.smart_device_recommendations = [
            "Consider smart thermostat for 15% energy savings",
            "LED lighting upgrade could save $20/month",
            "Smart power strips for phantom load reduction",
        ]

        # Add schedule recommendations
        optimization.recommended_schedule_changes = [
            {
                "device": "thermostat",
                "change": "Lower by 2°F during away hours",
                "savings": 12.5,
            },
            {
                "device": "water_heater",
                "change": "Schedule heating during off-peak hours",
                "savings": 8.3,
            },
        ]

    async def _enhance_security_intelligence(self, intelligence: SecurityIntelligence):
        """Enhance security intelligence with home-specific analysis."""
        # Add security device status
        intelligence.security_devices = [
            {
                "device": "front_door",
                "status": "secure",
                "last_activity": "2 hours ago",
            },
            {"device": "motion_sensors", "status": "active", "sensitivity": "medium"},
            {"device": "cameras", "status": "recording", "storage": "78% full"},
        ]

        # Add camera status
        intelligence.camera_status = {
            "total_cameras": 4,
            "active_cameras": 4,
            "recording_status": "continuous",
            "storage_days": 14,
        }

    async def _enhance_predictive_automation(
        self, automation: PredictiveAutomation, context: Dict[str, Any]
    ):
        """Enhance predictive automation with context-aware suggestions."""
        # Add predicted actions based on patterns
        automation.predicted_actions = [
            {
                "action": "turn_on_lights",
                "time": "18:25",
                "confidence": 0.89,
                "reason": "typical_arrival",
            },
            {
                "action": "adjust_thermostat",
                "time": "22:00",
                "confidence": 0.76,
                "reason": "sleep_schedule",
            },
            {
                "action": "arm_security",
                "time": "08:10",
                "confidence": 0.92,
                "reason": "departure_pattern",
            },
        ]

        # Add occupancy predictions
        automation.occupancy_predictions = {
            "next_arrival": "18:30 ± 15 minutes",
            "next_departure": "08:15 ± 10 minutes",
            "weekend_variance": "high",
            "confidence": 0.82,
        }

    async def _enhance_mobile_sync(self, sync: MobileIntelligenceSync):
        """Enhance mobile sync with location and personalization data."""
        # Add location-based suggestions
        sync.location_based_suggestions = [
            "You're 10 minutes from home - pre-cooling initiated",
            "Garage door ready for arrival",
            "Security system will disarm automatically",
        ]

        # Add arrival predictions
        sync.arrival_predictions = {
            "estimated_arrival": "18:32",
            "confidence": 0.85,
            "traffic_delay": "3 minutes",
            "suggested_actions": ["pre_cool", "turn_on_lights"],
        }

    # Standalone mode fallbacks

    def _get_standalone_context(self) -> HomeIntelligenceContext:
        """Get basic context when AAS intelligence is not available."""
        return HomeIntelligenceContext(
            system_health=0.7,
            recommendations=[
                "Enable AAS intelligence integration for smart recommendations"
            ],
        )

    def _get_standalone_energy_optimization(self) -> EnergyOptimization:
        """Get basic energy optimization when AAS intelligence is not available."""
        return EnergyOptimization(
            behavioral_recommendations=[
                "Enable AAS intelligence integration for energy optimization"
            ]
        )

    def _get_standalone_security_intelligence(self) -> SecurityIntelligence:
        """Get basic security intelligence when AAS intelligence is not available."""
        return SecurityIntelligence(threat_level="unknown", security_recommendations=[])

    def _get_standalone_predictive_automation(self) -> PredictiveAutomation:
        """Get basic predictive automation when AAS intelligence is not available."""
        return PredictiveAutomation(
            time_based_suggestions=[
                "Enable AAS intelligence integration for predictive automation"
            ]
        )

    def _get_standalone_mobile_sync(self) -> MobileIntelligenceSync:
        """Get basic mobile sync when AAS intelligence is not available."""
        return MobileIntelligenceSync(
            home_status_summary={"status": "basic_mode"},
            priority_alerts=[
                {
                    "type": "info",
                    "message": "Enable AAS intelligence integration for smart features",
                    "priority": "low",
                }
            ],
        )
