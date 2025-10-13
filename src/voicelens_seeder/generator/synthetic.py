"""
Synthetic VCP 0.3 conversation data generator.

Creates realistic HVAC service call conversations matching the VCP 0.3 standard
with time-based patterns, provider variations, and outcome distributions.
"""

import uuid
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Iterator
from pathlib import Path

from ..normalizers.vcp import (
    VCPMode, Provider, VCPWrapperGTM, VCPPayloadGTM, CallInfo, 
    PurposeContract, SuccessCriteria, OutcomesInfo, PerceivedOutcome,
    SentimentInfo, ObjectiveOutcome, ScoredCriteria, ObjectiveMetrics,
    PerceptionGap, PerceptionGapDriver, ArtifactsInfo, CustomInfo, AuditInfo
)
from .hvac_scenarios import (
    HVACScenario, select_scenario, generate_scenario_details,
    PROVIDER_CHARACTERISTICS
)


class VCPSyntheticGenerator:
    """Generates synthetic VCP 0.3 compliant conversation data."""
    
    def __init__(self, seed: Optional[int] = None, timezone_name: str = "America/Chicago"):
        """Initialize the generator with optional random seed."""
        if seed is not None:
            random.seed(seed)
        
        self.timezone = timezone.utc  # Always generate UTC timestamps
        self.local_tz_name = timezone_name
    
    def generate_call_batch(
        self,
        count: int,
        start_date: datetime,
        end_date: datetime,
        providers: Optional[List[Provider]] = None,
        vcp_mode: VCPMode = VCPMode.GTM
    ) -> Iterator[VCPWrapperGTM]:
        """Generate a batch of synthetic VCP calls within the time window."""
        
        if providers is None:
            providers = [Provider.RETELL, Provider.VAPI, Provider.BLAND]
        
        for i in range(count):
            # Generate random timestamp within window
            time_delta = end_date - start_date
            random_seconds = random.random() * time_delta.total_seconds()
            call_time = start_date + timedelta(seconds=random_seconds)
            
            # Select provider and scenario based on time
            provider = random.choice(providers)
            hour = call_time.hour
            day_of_week = call_time.weekday()  # Monday=0
            scenario = select_scenario(hour, day_of_week)
            
            # Generate VCP payload
            vcp_payload = self.generate_vcp_payload(
                call_time=call_time,
                scenario=scenario,
                provider=provider,
                vcp_mode=vcp_mode
            )
            
            yield vcp_payload
    
    def generate_vcp_payload(
        self,
        call_time: datetime,
        scenario: HVACScenario,
        provider: Provider,
        vcp_mode: VCPMode = VCPMode.GTM
    ) -> VCPWrapperGTM:
        """Generate a single VCP payload for the given parameters."""
        
        # Generate unique call ID
        call_id = str(uuid.uuid4())
        session_id = f"{call_id}-session"
        
        # Get scenario-specific details
        details = generate_scenario_details(scenario, provider)
        
        # Calculate end time
        end_time = call_time + timedelta(seconds=details["duration_sec"])
        
        # Build VCP payload components
        call_info = self._build_call_info(
            call_id=call_id,
            session_id=session_id,
            provider=provider,
            start_time=call_time,
            end_time=end_time,
            duration_sec=details["duration_sec"],
            capabilities_invoked=details["capabilities_invoked"],
            declared_intent=details["declared_intent"],
            success_criteria=details["success_criteria"]
        )
        
        outcomes = self._build_outcomes(
            scenario=scenario,
            details=details,
            call_end_time=end_time
        )
        
        artifacts = self._build_artifacts(call_id, provider)
        custom = self._build_custom(provider, scenario)
        audit = self._build_audit(end_time)
        
        # Create VCP payload
        vcp_payload = VCPPayloadGTM(
            call=call_info,
            outcomes=outcomes,
            artifacts=artifacts,
            custom=custom,
            audit=audit
        )
        
        # Create wrapper
        wrapper = VCPWrapperGTM(
            call_id=call_id,
            vcp_version="0.3",
            vcp_payload=vcp_payload
        )
        
        return wrapper
    
    def _build_call_info(
        self,
        call_id: str,
        session_id: str,
        provider: Provider,
        start_time: datetime,
        end_time: datetime,
        duration_sec: int,
        capabilities_invoked: List[str],
        declared_intent: str,
        success_criteria: Dict[str, str]
    ) -> CallInfo:
        """Build the call information section."""
        
        # Format timestamps in ISO 8601 UTC
        start_iso = start_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        end_iso = end_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        
        # Build success criteria
        criteria = SuccessCriteria(
            id="sc1",
            metric=success_criteria["metric"],
            operator="==",
            value=True
        )
        
        purpose_contract = PurposeContract(
            declared_intent=declared_intent,
            success_criteria=[criteria]
        )
        
        return CallInfo(
            call_id=call_id,
            session_id=session_id,
            provider=provider.value,
            start_time=start_iso,
            end_time=end_iso,
            duration_sec=duration_sec,
            capabilities_invoked=capabilities_invoked,
            purpose_contract=purpose_contract
        )
    
    def _build_outcomes(
        self,
        scenario: HVACScenario,
        details: Dict[str, Any],
        call_end_time: datetime
    ) -> OutcomesInfo:
        """Build the outcomes section."""
        
        # Perceived outcomes (caller perspective)
        sentiment_info = SentimentInfo(
            model=details["sentiment_model"],
            score=details["caller_sentiment"]
        )
        
        # Calculate Unix timestamp for "at" field
        perceived_at = int(call_end_time.timestamp())
        
        perceived = PerceivedOutcome(
            by="caller",
            at=perceived_at,
            sentiment=sentiment_info,
            confidence=details["provider_confidence"]
        )
        
        # Objective outcomes
        scored_criteria = ScoredCriteria(
            id="sc1",
            met=details["success_met"],
            evidence_ref=details["success_criteria"]["evidence"]
        )
        
        objective_metrics = ObjectiveMetrics(
            aht_sec=details["duration_sec"],
            first_contact_resolution=details["status"].value == "success",
            interruptions=details["interruptions"],
            handoff_performed=details["handoff_performed"],
            first_response_sec=details.get("first_response_sec"),
            estimated_value_usd=details.get("estimated_value_usd", 0)
        )
        
        objective = ObjectiveOutcome(
            status=details["status"],
            scored_criteria=[scored_criteria],
            metrics=objective_metrics,
            confidence=details["provider_confidence"]
        )
        
        # Perception gap
        gap_drivers = [
            PerceptionGapDriver(**driver) 
            for driver in details["perception_gap"]["drivers"]
        ]
        
        perception_gap = PerceptionGap(
            gap_score=details["perception_gap"]["gap_score"],
            gap_class=details["perception_gap"]["gap_class"],
            drivers=gap_drivers
        )
        
        return OutcomesInfo(
            perceived=[perceived],
            objective=objective,
            perception_gap=perception_gap
        )
    
    def _build_artifacts(self, call_id: str, provider: Provider) -> ArtifactsInfo:
        """Build the artifacts section."""
        return ArtifactsInfo(
            recording_url=f"https://example.com/rec/{call_id}.mp3",
            provider_raw_payload_ref=f"s3://vcp-raw/{provider.value}/{call_id}.json"
        )
    
    def _build_custom(self, provider: Provider, scenario: HVACScenario) -> CustomInfo:
        """Build the custom section with provider-specific info."""
        # Handle both string and enum scenarios
        scenario_value = scenario.value if hasattr(scenario, 'value') else str(scenario)
        
        return CustomInfo(
            provider_specific={
                provider.value: {"channel": "inbound"}
            },
            outcome_hint=scenario_value,
            synthetic=True,
            synthetic_recipe=f"hvac_standard_v1_{datetime.now().strftime('%Y_%m_%d')}"
        )
    
    def _build_audit(self, call_end_time: datetime) -> AuditInfo:
        """Build the audit section."""
        # Add small delays for realistic processing times
        received_at = call_end_time + timedelta(seconds=1)
        normalized_at = call_end_time + timedelta(seconds=2)
        
        received_iso = received_at.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        normalized_iso = normalized_at.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        
        return AuditInfo(
            received_at=received_iso,
            normalized_at=normalized_iso,
            schema_version="0.3"
        )
    
    def generate_baseline_examples(self) -> List[VCPWrapperGTM]:
        """Generate the 8 baseline examples matching your curl commands."""
        
        # Base timestamp for consistent examples
        base_time = datetime(2025, 10, 10, 19, 42, 10, tzinfo=timezone.utc)
        
        examples = []
        
        # 1. After-hours Booked Service (AC repair)
        examples.append(self.generate_vcp_payload(
            call_time=base_time,
            scenario=HVACScenario.BOOKED_SERVICE,
            provider=Provider.RETELL
        ))
        
        # 2. Live Transfer to dispatcher
        examples.append(self.generate_vcp_payload(
            call_time=base_time - timedelta(days=1, hours=2, minutes=30),
            scenario=HVACScenario.LIVE_TRANSFER,
            provider=Provider.VAPI
        ))
        
        # 3. Scheduled Callback window
        examples.append(self.generate_vcp_payload(
            call_time=base_time - timedelta(days=2, hours=21, minutes=37),
            scenario=HVACScenario.SCHEDULED_CALLBACK,
            provider=Provider.BLAND
        ))
        
        # 4. Quote Requested (furnace install)
        examples.append(self.generate_vcp_payload(
            call_time=base_time - timedelta(days=3, hours=8, minutes=24),
            scenario=HVACScenario.QUOTE_REQUESTED,
            provider=Provider.RETELL
        ))
        
        # 5. Out of Service Area
        examples.append(self.generate_vcp_payload(
            call_time=base_time + timedelta(days=1, hours=19, minutes=21),
            scenario=HVACScenario.OUT_OF_SERVICE_AREA,
            provider=Provider.VAPI
        ))
        
        # 6. Spam/Non-Lead filtered
        examples.append(self.generate_vcp_payload(
            call_time=base_time - timedelta(days=4, hours=10, minutes=28),
            scenario=HVACScenario.SPAM_FILTERED,
            provider=Provider.RETELL
        ))
        
        # 7. No-Show/Cancel
        examples.append(self.generate_vcp_payload(
            call_time=base_time + timedelta(days=2, hours=13, minutes=14),
            scenario=HVACScenario.NO_SHOW_CANCEL,
            provider=Provider.BLAND
        ))
        
        # 8. Emergency After-Hours Heat Out
        examples.append(self.generate_vcp_payload(
            call_time=base_time + timedelta(days=2, hours=4, minutes=24),
            scenario=HVACScenario.EMERGENCY_SERVICE,
            provider=Provider.RETELL
        ))
        
        return examples
    
    def save_examples_as_json(self, examples: List[VCPWrapperGTM], output_dir: Path) -> None:
        """Save examples as individual JSON files for testing."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, example in enumerate(examples, 1):
            scenario = example.vcp_payload.custom.outcome_hint
            provider = example.vcp_payload.call.provider
            filename = f"hvac_{i:03d}_{scenario}_{provider}.json"
            
            file_path = output_dir / filename
            with open(file_path, 'w') as f:
                f.write(example.model_dump_json(indent=2))
        
        print(f"Saved {len(examples)} example files to {output_dir}")
    
    def generate_time_series(
        self,
        days: int = 30,
        base_volume: int = 50,
        providers: Optional[List[Provider]] = None
    ) -> Iterator[VCPWrapperGTM]:
        """Generate a time series of calls over multiple days with realistic patterns."""
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        # Generate calls distributed across the time period
        total_calls = days * base_volume
        
        # Add some randomness to daily volumes
        daily_volumes = []
        for day in range(days):
            # Base volume with some variance
            variance = random.uniform(0.7, 1.3)
            day_volume = int(base_volume * variance)
            
            # Weekend adjustment
            weekday = (start_time + timedelta(days=day)).weekday()
            if weekday >= 5:  # Weekend
                day_volume = int(day_volume * 0.6)
            
            daily_volumes.append(day_volume)
        
        # Generate calls for each day
        for day in range(days):
            day_start = start_time + timedelta(days=day)
            day_end = day_start + timedelta(days=1)
            
            day_calls = self.generate_call_batch(
                count=daily_volumes[day],
                start_date=day_start,
                end_date=day_end,
                providers=providers
            )
            
            for call in day_calls:
                yield call