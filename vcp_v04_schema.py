#!/usr/bin/env python3
"""
Voice Context Protocol (VCP) v0.4 Schema Implementation
Updated schema with provenance, consent, and enhanced business metrics
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union, Literal
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class VCPVersion(str, Enum):
    """Supported VCP versions"""
    V03 = "0.3"
    V04 = "0.4"


class CallDirection(str, Enum):
    """Call direction types"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class ConsentMethod(str, Enum):
    """Consent acquisition methods"""
    EXPLICIT = "explicit"
    IMPLICIT = "implicit"
    INFERRED = "inferred"


class DisconnectReason(str, Enum):
    """Call disconnect reasons"""
    CUSTOMER_HANGUP = "customer_hangup"
    AGENT_HANGUP = "agent_hangup"
    TIMEOUT = "timeout"
    TECHNICAL_ERROR = "technical_error"
    COMPLETED = "completed"
    TRANSFERRED = "transferred"


class PerceptionGapClass(str, Enum):
    """Perception gap classification"""
    ALIGNED = "aligned"
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"


# New v0.4 Objects
class ProvenanceData(BaseModel):
    """Data lineage and capture information (v0.4+)"""
    captured_at: datetime = Field(..., description="Original capture timestamp")
    captured_by: str = Field(..., description="System/agent that captured data")
    source_system: str = Field(..., description="Originating platform")
    processing_chain: List[str] = Field(default_factory=list, description="Systems that processed data")
    data_quality_score: float = Field(..., ge=0, le=1, description="Quality metric (0-1)")


class ConsentData(BaseModel):
    """User consent tracking (v0.4+)"""
    recording_consent: bool = Field(..., description="User consented to recording")
    consent_timestamp: datetime = Field(..., description="When consent was obtained")
    consent_method: ConsentMethod = Field(..., description="How consent was obtained")
    data_retention_days: int = Field(..., gt=0, description="Agreed retention period")
    sharing_allowed: bool = Field(..., description="Can data be shared with third parties")
    anonymization_required: bool = Field(..., description="Must data be anonymized")


# Enhanced existing objects for v0.4
class CallData(BaseModel):
    """Core call metadata"""
    call_id: str = Field(..., description="Unique call identifier")
    session_id: Optional[str] = Field(None, description="Multi-turn session ID (v0.4+)")
    provider: str = Field(..., description="Voice AI provider")
    start_time: datetime = Field(..., description="Call start time")
    end_time: datetime = Field(..., description="Call end time")
    duration_sec: int = Field(..., ge=0, description="Call duration in seconds")
    
    # v0.4 additions
    channel: Optional[CallDirection] = Field(None, description="Call direction (v0.4+)")
    to: Optional[str] = Field(None, description="Destination phone number/identifier (v0.4+)")
    from_: Optional[str] = Field(None, alias="from", description="Source phone number/identifier (v0.4+)")
    capabilities_invoked: List[str] = Field(default_factory=list, description="Tools/APIs used during call (v0.4+)")
    
    # Existing fields
    purpose_contract: Optional[Dict[str, Any]] = None


class BusinessMetrics(BaseModel):
    """Enhanced business metrics (v0.4)"""
    aht_sec: Optional[int] = Field(None, description="Average Handle Time")
    first_contact_resolution: Optional[bool] = Field(None, description="FCR KPI")
    first_response_sec: Optional[float] = Field(None, description="Time to first agent response")
    estimated_value_usd: Optional[float] = Field(None, description="Business value estimate")
    interruptions: Optional[int] = Field(None, ge=0, description="Number of interruptions")
    handoff_performed: Optional[bool] = Field(None, description="Was call transferred to human")


class PerceptionGapDrivers(BaseModel):
    """Enhanced perception gap analysis (v0.4)"""
    gap_score: float = Field(..., ge=0, le=1, description="Perception gap score")
    gap_class: PerceptionGapClass = Field(..., description="Gap classification")
    drivers: List[str] = Field(default_factory=list, description="Qualitative reasons for gap (v0.4+)")
    components: Optional[Dict[str, float]] = Field(None, description="Component breakdown (v0.4+)")


class ObjectiveOutcome(BaseModel):
    """Objective call outcome assessment"""
    status: str = Field(..., description="Outcome status")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="AI confidence score (v0.4+)")
    disconnect_reason: Optional[DisconnectReason] = Field(None, description="Why call ended (v0.4+)")
    scored_criteria: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: BusinessMetrics = Field(default_factory=BusinessMetrics)


class OutcomesData(BaseModel):
    """Call outcomes and assessments"""
    perceived: List[Dict[str, Any]] = Field(default_factory=list)
    objective: ObjectiveOutcome
    extractions: Optional[Dict[str, Any]] = Field(None, description="Custom entity extractions (v0.4+)")
    perception_gap: Optional[PerceptionGapDrivers] = None


class ArtifactsData(BaseModel):
    """Call artifacts and recordings"""
    recording_url: Optional[str] = None
    transcript_url: Optional[str] = None
    summary: Optional[str] = Field(None, description="Human-readable call summary (v0.4+)")
    provider_raw_payload_ref: Optional[str] = None


class CustomData(BaseModel):
    """Provider-specific and custom data"""
    provider_specific: Dict[str, Any] = Field(default_factory=dict)
    outcome_hint: Optional[str] = None
    synthetic: bool = False
    synthetic_recipe: Optional[str] = None


class AuditData(BaseModel):
    """Processing audit trail"""
    received_at: datetime
    normalized_at: datetime
    schema_version: VCPVersion


class VCPPayload(BaseModel):
    """Main VCP payload structure"""
    call: CallData
    outcomes: OutcomesData
    artifacts: ArtifactsData = Field(default_factory=ArtifactsData)
    
    # v0.4 required fields
    provenance: Optional[ProvenanceData] = Field(None, description="Data lineage (required for v0.4)")
    consent: Optional[ConsentData] = Field(None, description="Consent tracking (required for v0.4)")
    
    # Optional sections
    custom: CustomData = Field(default_factory=CustomData)
    audit: AuditData


class VCPMessage(BaseModel):
    """Complete VCP message wrapper"""
    call_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vcp_version: VCPVersion = Field(VCPVersion.V04, description="VCP schema version")
    vcp_payload: VCPPayload


class VCPValidator:
    """Validation utilities for VCP messages"""
    
    @staticmethod
    def validate_version_compatibility(message: VCPMessage) -> Dict[str, List[str]]:
        """Validate version-specific requirements"""
        warnings = []
        errors = []
        
        if message.vcp_version == VCPVersion.V04:
            # v0.4 requires provenance and consent
            if not message.vcp_payload.provenance:
                errors.append("VCP v0.4 requires provenance object")
            if not message.vcp_payload.consent:
                errors.append("VCP v0.4 requires consent object")
        
        # Check for deprecated fields or patterns
        if hasattr(message.vcp_payload.call, 'from') and message.vcp_payload.call.from_:
            warnings.append("Use 'from_' field instead of 'from' (reserved keyword)")
        
        return {"warnings": warnings, "errors": errors}
    
    @staticmethod
    def upgrade_v03_to_v04(v03_message: Dict[str, Any]) -> VCPMessage:
        """Upgrade v0.3 message to v0.4 format"""
        # Create default v0.4 fields
        now = datetime.now(timezone.utc)
        
        # Add provenance if missing
        if "provenance" not in v03_message.get("vcp_payload", {}):
            v03_message["vcp_payload"]["provenance"] = {
                "captured_at": now.isoformat(),
                "captured_by": "vcp_upgrade_utility",
                "source_system": v03_message["vcp_payload"].get("call", {}).get("provider", "unknown"),
                "processing_chain": ["vcp_v03_to_v04_upgrade"],
                "data_quality_score": 0.8
            }
        
        # Add consent if missing (with conservative defaults)
        if "consent" not in v03_message.get("vcp_payload", {}):
            v03_message["vcp_payload"]["consent"] = {
                "recording_consent": False,  # Conservative default
                "consent_timestamp": now.isoformat(),
                "consent_method": "inferred",
                "data_retention_days": 30,
                "sharing_allowed": False,
                "anonymization_required": True
            }
        
        # Update version
        v03_message["vcp_version"] = "0.4"
        
        return VCPMessage(**v03_message)


def create_example_v04_message() -> VCPMessage:
    """Create an example VCP v0.4 message"""
    now = datetime.now(timezone.utc)
    call_id = str(uuid.uuid4())
    
    return VCPMessage(
        call_id=call_id,
        vcp_version=VCPVersion.V04,
        vcp_payload=VCPPayload(
            call=CallData(
                call_id=call_id,
                session_id=f"{call_id}-session",
                provider="retell",
                start_time=now,
                end_time=now,
                duration_sec=180,
                channel=CallDirection.INBOUND,
                to="+1555123456",
                from_="+1555987654",
                capabilities_invoked=["calendar_api", "sms_notification"]
            ),
            outcomes=OutcomesData(
                objective=ObjectiveOutcome(
                    status="success",
                    confidence=0.85,
                    disconnect_reason=DisconnectReason.COMPLETED,
                    metrics=BusinessMetrics(
                        aht_sec=180,
                        first_contact_resolution=True,
                        first_response_sec=2.3,
                        estimated_value_usd=150.0,
                        interruptions=2,
                        handoff_performed=False
                    )
                ),
                extractions={
                    "customer_name": "John Smith",
                    "issue_type": "hvac_repair",
                    "urgency": "high"
                }
            ),
            provenance=ProvenanceData(
                captured_at=now,
                captured_by="retell_webhook_handler",
                source_system="retell",
                processing_chain=["retell_api", "vcp_normalizer", "voicelens_processor"],
                data_quality_score=0.92
            ),
            consent=ConsentData(
                recording_consent=True,
                consent_timestamp=now,
                consent_method=ConsentMethod.EXPLICIT,
                data_retention_days=90,
                sharing_allowed=True,
                anonymization_required=False
            ),
            audit=AuditData(
                received_at=now,
                normalized_at=now,
                schema_version=VCPVersion.V04
            )
        )
    )


if __name__ == "__main__":
    # Example usage
    example_message = create_example_v04_message()
    print("VCP v0.4 Example Message:")
    print(example_message.model_dump_json(indent=2))
    
    # Validation example
    validator = VCPValidator()
    validation_results = validator.validate_version_compatibility(example_message)
    print(f"\nValidation Results: {validation_results}")