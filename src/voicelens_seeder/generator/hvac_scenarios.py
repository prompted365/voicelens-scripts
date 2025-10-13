"""
HVAC-specific conversation scenarios and templates for VCP generation.

Based on real-world HVAC service call patterns, this module provides
templates for generating realistic synthetic conversation data.
"""

import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Any
from enum import Enum

from ..normalizers.vcp import VCPMode, Provider, CallStatus, GapClass


class HVACScenario(str, Enum):
    """HVAC service call scenarios."""
    BOOKED_SERVICE = "booked_service"
    LIVE_TRANSFER = "live_transfer" 
    SCHEDULED_CALLBACK = "scheduled_callback"
    QUOTE_REQUESTED = "quote_requested"
    OUT_OF_SERVICE_AREA = "out_of_service_area"
    SPAM_FILTERED = "spam_filtered"
    EMERGENCY_SERVICE = "emergency_service"
    NO_SHOW_CANCEL = "no_show_cancel"


class HVACServiceType(str, Enum):
    """Types of HVAC services."""
    AC_REPAIR = "ac_repair"
    FURNACE_REPAIR = "furnace_repair"
    AC_INSTALLATION = "ac_installation"
    FURNACE_INSTALLATION = "furnace_installation"
    MAINTENANCE = "maintenance"
    EMERGENCY_HEATING = "emergency_heating"
    EMERGENCY_COOLING = "emergency_cooling"
    DUCT_CLEANING = "duct_cleaning"
    THERMOSTAT_REPAIR = "thermostat_repair"


# Scenario configuration with realistic distributions
HVAC_SCENARIO_WEIGHTS = {
    HVACScenario.BOOKED_SERVICE: 0.28,
    HVACScenario.LIVE_TRANSFER: 0.14,
    HVACScenario.SCHEDULED_CALLBACK: 0.18,
    HVACScenario.QUOTE_REQUESTED: 0.11,
    HVACScenario.OUT_OF_SERVICE_AREA: 0.09,
    HVACScenario.SPAM_FILTERED: 0.13,
    HVACScenario.EMERGENCY_SERVICE: 0.07,
}

# Service type patterns by scenario
SERVICE_TYPE_PATTERNS = {
    HVACScenario.BOOKED_SERVICE: [
        HVACServiceType.AC_REPAIR,
        HVACServiceType.FURNACE_REPAIR,
        HVACServiceType.MAINTENANCE,
        HVACServiceType.THERMOSTAT_REPAIR,
    ],
    HVACScenario.EMERGENCY_SERVICE: [
        HVACServiceType.EMERGENCY_HEATING,
        HVACServiceType.EMERGENCY_COOLING,
        HVACServiceType.FURNACE_REPAIR,
        HVACServiceType.AC_REPAIR,
    ],
    HVACScenario.QUOTE_REQUESTED: [
        HVACServiceType.AC_INSTALLATION,
        HVACServiceType.FURNACE_INSTALLATION,
        HVACServiceType.DUCT_CLEANING,
    ],
}

# Capabilities invoked by scenario
SCENARIO_CAPABILITIES = {
    HVACScenario.BOOKED_SERVICE: ["calendar_api", "sms_notification"],
    HVACScenario.LIVE_TRANSFER: ["telephony.transfer"],
    HVACScenario.SCHEDULED_CALLBACK: ["crm.create_task", "sms_notification"],
    HVACScenario.QUOTE_REQUESTED: ["crm.create_opportunity", "email_followup"],
    HVACScenario.OUT_OF_SERVICE_AREA: [],
    HVACScenario.SPAM_FILTERED: [],
    HVACScenario.EMERGENCY_SERVICE: ["calendar_api", "priority_flag", "sms_notification"],
    HVACScenario.NO_SHOW_CANCEL: ["calendar_api", "crm.update"],
}

# Intent mapping
SCENARIO_INTENTS = {
    HVACScenario.BOOKED_SERVICE: "appointment_booking",
    HVACScenario.LIVE_TRANSFER: "speak_to_tech", 
    HVACScenario.SCHEDULED_CALLBACK: "schedule_callback",
    HVACScenario.QUOTE_REQUESTED: "request_quote",
    HVACScenario.OUT_OF_SERVICE_AREA: "service_request",
    HVACScenario.SPAM_FILTERED: "unknown",
    HVACScenario.EMERGENCY_SERVICE: "emergency_service",
    HVACScenario.NO_SHOW_CANCEL: "appointment_booking",
}

# Success criteria by scenario
SCENARIO_SUCCESS_CRITERIA = {
    HVACScenario.BOOKED_SERVICE: {"metric": "task_completion", "evidence": "tool_log#calendar_api"},
    HVACScenario.LIVE_TRANSFER: {"metric": "warm_transfer", "evidence": "tool_log#telephony.transfer"},
    HVACScenario.SCHEDULED_CALLBACK: {"metric": "callback_window_created", "evidence": "tool_log#crm.create_task"},
    HVACScenario.QUOTE_REQUESTED: {"metric": "lead_created", "evidence": "tool_log#crm.create_opportunity"},
    HVACScenario.OUT_OF_SERVICE_AREA: {"metric": "task_completion", "evidence": "rule#not_service_area"},
    HVACScenario.SPAM_FILTERED: {"metric": "screening", "evidence": "heuristic#spam"},
    HVACScenario.EMERGENCY_SERVICE: {"metric": "priority_booking", "evidence": "tool_log#priority_flag"},
    HVACScenario.NO_SHOW_CANCEL: {"metric": "task_completion", "evidence": "tool_log#calendar_api"},
}

# Status and success patterns
SCENARIO_OUTCOMES = {
    HVACScenario.BOOKED_SERVICE: (CallStatus.SUCCESS, True),
    HVACScenario.LIVE_TRANSFER: (CallStatus.SUCCESS, True),
    HVACScenario.SCHEDULED_CALLBACK: (CallStatus.SUCCESS, True),
    HVACScenario.QUOTE_REQUESTED: (CallStatus.SUCCESS, True),
    HVACScenario.OUT_OF_SERVICE_AREA: (CallStatus.PARTIAL, False),
    HVACScenario.SPAM_FILTERED: (CallStatus.FILTERED, True),
    HVACScenario.EMERGENCY_SERVICE: (CallStatus.SUCCESS, True),
    HVACScenario.NO_SHOW_CANCEL: (CallStatus.SUCCESS, True),
}

# Revenue patterns (USD)
SCENARIO_REVENUE_RANGES = {
    HVACScenario.BOOKED_SERVICE: (250, 400),
    HVACScenario.LIVE_TRANSFER: (350, 525),
    HVACScenario.SCHEDULED_CALLBACK: (120, 200),
    HVACScenario.QUOTE_REQUESTED: (250, 650),
    HVACScenario.OUT_OF_SERVICE_AREA: (0, 0),
    HVACScenario.SPAM_FILTERED: (0, 0),
    HVACScenario.EMERGENCY_SERVICE: (450, 800),
    HVACScenario.NO_SHOW_CANCEL: (0, 0),
}

# Duration patterns (seconds)
SCENARIO_DURATION_RANGES = {
    HVACScenario.BOOKED_SERVICE: (140, 200),
    HVACScenario.LIVE_TRANSFER: (120, 180),
    HVACScenario.SCHEDULED_CALLBACK: (90, 150),
    HVACScenario.QUOTE_REQUESTED: (130, 170),
    HVACScenario.OUT_OF_SERVICE_AREA: (80, 120),
    HVACScenario.SPAM_FILTERED: (30, 60),
    HVACScenario.EMERGENCY_SERVICE: (160, 220),
    HVACScenario.NO_SHOW_CANCEL: (140, 180),
}

# Sentiment patterns by scenario
SCENARIO_SENTIMENT_RANGES = {
    HVACScenario.BOOKED_SERVICE: (0.75, 0.90),
    HVACScenario.LIVE_TRANSFER: (0.70, 0.80),
    HVACScenario.SCHEDULED_CALLBACK: (0.80, 0.88),
    HVACScenario.QUOTE_REQUESTED: (0.70, 0.85),
    HVACScenario.OUT_OF_SERVICE_AREA: (0.45, 0.70),
    HVACScenario.SPAM_FILTERED: (0.05, 0.25),
    HVACScenario.EMERGENCY_SERVICE: (0.60, 0.75),  # Stressed but grateful
    HVACScenario.NO_SHOW_CANCEL: (0.65, 0.75),
}

# Confidence patterns
SCENARIO_CONFIDENCE_RANGES = {
    HVACScenario.BOOKED_SERVICE: (0.80, 0.92),
    HVACScenario.LIVE_TRANSFER: (0.75, 0.85),
    HVACScenario.SCHEDULED_CALLBACK: (0.78, 0.88),
    HVACScenario.QUOTE_REQUESTED: (0.70, 0.85),
    HVACScenario.OUT_OF_SERVICE_AREA: (0.70, 0.85),
    HVACScenario.SPAM_FILTERED: (0.85, 0.95),  # System is confident about spam
    HVACScenario.EMERGENCY_SERVICE: (0.85, 0.95),
    HVACScenario.NO_SHOW_CANCEL: (0.75, 0.85),
}

# Perception gap patterns
SCENARIO_GAP_PATTERNS = {
    HVACScenario.BOOKED_SERVICE: {
        "gap_range": (0.01, 0.05),
        "gap_class": GapClass.ALIGNED,
        "drivers": [{"type": "clarity", "weight": 0.6, "note": "clear slot confirmation"}],
    },
    HVACScenario.LIVE_TRANSFER: {
        "gap_range": (0.03, 0.08),
        "gap_class": GapClass.ALIGNED,
        "drivers": [{"type": "response_latency", "weight": 0.4, "note": "slight delay before transfer"}],
    },
    HVACScenario.SCHEDULED_CALLBACK: {
        "gap_range": (0.02, 0.06),
        "gap_class": GapClass.ALIGNED,
        "drivers": [{"type": "expectation_match", "weight": 0.6, "note": "clear window set"}],
    },
    HVACScenario.QUOTE_REQUESTED: {
        "gap_range": (0.04, 0.08),
        "gap_class": GapClass.ALIGNED,
        "drivers": [{"type": "info_request", "weight": 0.5, "note": "additional specs emailed"}],
    },
    HVACScenario.OUT_OF_SERVICE_AREA: {
        "gap_range": (0.10, 0.15),
        "gap_class": GapClass.MILD_MISALIGNMENT,
        "drivers": [{"type": "expectation_mismatch", "weight": 0.7, "note": "zip outside coverage"}],
    },
    HVACScenario.SPAM_FILTERED: {
        "gap_range": (0.0, 0.0),
        "gap_class": GapClass.ALIGNED,  # System correctly identified spam
        "drivers": [],
    },
    HVACScenario.EMERGENCY_SERVICE: {
        "gap_range": (0.03, 0.08),
        "gap_class": GapClass.ALIGNED,
        "drivers": [{"type": "urgency", "weight": 0.5, "note": "heat out"}],
    },
    HVACScenario.NO_SHOW_CANCEL: {
        "gap_range": (0.05, 0.10),
        "gap_class": GapClass.ALIGNED,
        "drivers": [{"type": "expectation_match", "weight": 0.4, "note": "booking successful initially"}],
    },
}

# Provider-specific characteristics
PROVIDER_CHARACTERISTICS = {
    Provider.RETELL: {
        "sentiment_model": "retell-internal",
        "response_latency_range": (1.5, 2.5),
        "interruption_probability": 0.1,
    },
    Provider.VAPI: {
        "sentiment_model": "vapi-internal", 
        "response_latency_range": (2.0, 3.0),
        "interruption_probability": 0.15,
    },
    Provider.BLAND: {
        "sentiment_model": "bland-internal",
        "response_latency_range": (1.8, 2.4),
        "interruption_probability": 0.05,
    },
}

# Time-based patterns for realistic call distribution
def get_time_weighted_scenarios(hour: int, day_of_week: int) -> Dict[HVACScenario, float]:
    """Get scenario weights adjusted for time of day and day of week."""
    weights = HVAC_SCENARIO_WEIGHTS.copy()
    
    # After hours (6 PM - 9 PM) and weekends have more emergencies
    if hour >= 18 and hour <= 21:
        weights[HVACScenario.EMERGENCY_SERVICE] *= 1.8
        weights[HVACScenario.BOOKED_SERVICE] *= 0.8
    
    # Late night/early morning (9 PM - 8 AM) - mostly emergencies and spam
    if hour >= 21 or hour <= 8:
        weights[HVACScenario.EMERGENCY_SERVICE] *= 2.5
        weights[HVACScenario.SPAM_FILTERED] *= 1.3
        weights[HVACScenario.BOOKED_SERVICE] *= 0.3
        weights[HVACScenario.QUOTE_REQUESTED] *= 0.2
    
    # Weekends (Saturday=5, Sunday=6) 
    if day_of_week >= 5:
        weights[HVACScenario.EMERGENCY_SERVICE] *= 1.4
        weights[HVACScenario.QUOTE_REQUESTED] *= 0.7
    
    # Monday morning (day_of_week=0, hour=8-11) - lots of weekend emergency follow-ups
    if day_of_week == 0 and 8 <= hour <= 11:
        weights[HVACScenario.BOOKED_SERVICE] *= 1.3
        weights[HVACScenario.SCHEDULED_CALLBACK] *= 1.2
    
    # Normalize weights to sum to 1.0
    total = sum(weights.values())
    return {k: v/total for k, v in weights.items()}


def select_scenario(hour: int, day_of_week: int) -> HVACScenario:
    """Select a scenario based on time-weighted probabilities."""
    weights = get_time_weighted_scenarios(hour, day_of_week)
    scenarios = list(weights.keys())
    probabilities = list(weights.values())
    return random.choices(scenarios, weights=probabilities)[0]


def generate_scenario_details(scenario: HVACScenario, provider: Provider) -> Dict[str, Any]:
    """Generate detailed parameters for a specific scenario."""
    # Get base patterns
    duration_range = SCENARIO_DURATION_RANGES[scenario]
    revenue_range = SCENARIO_REVENUE_RANGES[scenario]
    sentiment_range = SCENARIO_SENTIMENT_RANGES[scenario]
    confidence_range = SCENARIO_CONFIDENCE_RANGES[scenario]
    gap_pattern = SCENARIO_GAP_PATTERNS[scenario]
    status, success = SCENARIO_OUTCOMES[scenario]
    
    # Generate specific values
    duration = random.randint(*duration_range)
    revenue = random.randint(*revenue_range) if revenue_range[0] > 0 else 0
    sentiment = round(random.uniform(*sentiment_range), 2)
    confidence = round(random.uniform(*confidence_range), 2)
    
    # Perception gap
    gap_score = round(random.uniform(*gap_pattern["gap_range"]), 2)
    
    # Provider-specific adjustments
    provider_chars = PROVIDER_CHARACTERISTICS[provider]
    response_latency = round(random.uniform(*provider_chars["response_latency_range"]), 1)
    interruptions = 1 if random.random() < provider_chars["interruption_probability"] else 0
    
    return {
        "scenario": scenario,
        "provider": provider,
        "duration_sec": duration,
        "estimated_value_usd": revenue,
        "capabilities_invoked": SCENARIO_CAPABILITIES[scenario],
        "declared_intent": SCENARIO_INTENTS[scenario],
        "success_criteria": SCENARIO_SUCCESS_CRITERIA[scenario],
        "status": status,
        "success_met": success,
        "caller_sentiment": sentiment,
        "provider_confidence": confidence,
        "sentiment_model": provider_chars["sentiment_model"],
        "first_response_sec": response_latency,
        "interruptions": interruptions,
        "handoff_performed": scenario == HVACScenario.LIVE_TRANSFER,
        "perception_gap": {
            "gap_score": gap_score,
            "gap_class": gap_pattern["gap_class"],
            "drivers": gap_pattern["drivers"].copy(),
        },
    }