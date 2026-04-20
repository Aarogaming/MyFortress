"""
MyFortress Intelligence Integration

This module integrates MyFortress with the AAS Shared Intelligence Service,
transforming it from a basic home automation gateway into an intelligent,
predictive, collaborative home ecosystem.
"""

from .client import MyFortressIntelligenceClient
from .manager import MyFortressIntelligenceManager
from .models import (
    EnergyOptimization,
    HomeIntelligenceContext,
    HomeOptimizationRecommendation,
    PredictiveAutomation,
    SecurityIntelligence,
)

__all__ = [
    "MyFortressIntelligenceClient",
    "MyFortressIntelligenceManager",
    "HomeIntelligenceContext",
    "HomeOptimizationRecommendation",
    "EnergyOptimization",
    "SecurityIntelligence",
    "PredictiveAutomation",
]
