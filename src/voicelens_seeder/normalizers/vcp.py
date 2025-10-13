"""
VCP 0.3 Pydantic Models and Normalizers

Supports both GTM-focused mode (streamlined) and full VCP 0.3 compliance.
Models match the structure from your curl example and VCP standards.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class VCPMode(str, Enum):
    """VCP payload generation modes."""
    GTM = "gtm"      # Streamlined for GTM demos
    FULL = "full"    # Complete VCP 0.3 compliance


class Provider(str, Enum):
    """Supported voice AI providers."""
    RETELL = "retell"
    VAPI = "vapi"
    BLAND = "bland"
    SYNTHETIC = "synthetic"


class CallStatus(str, Enum):
    """Call outcome status values."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FILTERED = "filtered"
    FAILED = "failed"


class GapClass(str, Enum):
    """Perception gap classification."""
    ALIGNED = "aligned"
    MILD_MISALIGNMENT = "mild_misalignment"
    SIGNIFICANT_GAP = "significant_gap"


# ===== Core VCP Models =====

class SuccessCriteria(BaseModel):
    """Success criteria definition."""
    id: str
    metric: str
    operator: str
    value: Union[bool, str, float, int]


class PurposeContract(BaseModel):
    """Call purpose and success criteria."""
    declared_intent: str
    success_criteria: List[SuccessCriteria]


class CallInfo(BaseModel):
    """Core call information."""
    call_id: str
    session_id: str
    provider: str
    start_time: str = Field(..., description="ISO 8601 UTC timestamp")
    end_time: str = Field(..., description="ISO 8601 UTC timestamp")
    duration_sec: int
    capabilities_invoked: List[str] = Field(default_factory=list)
    purpose_contract: PurposeContract

    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_timestamp(cls, v):
        """Ensure timestamps are in ISO 8601 format."""
        if not v.endswith('Z'):
            raise ValueError('Timestamp must be in UTC with Z suffix')
        return v


class SentimentInfo(BaseModel):
    """Sentiment analysis information."""
    model: str
    score: float = Field(..., ge=0.0, le=1.0)


class PerceivedOutcome(BaseModel):
    """Perceived outcome from a stakeholder perspective."""
    by: str  # "caller", "agent", "supervisor"
    at: Optional[int] = None  # Unix timestamp
    sentiment: SentimentInfo
    confidence: float = Field(..., ge=0.0, le=1.0)


class ScoredCriteria(BaseModel):
    """Scored success criteria result."""
    id: str
    met: bool
    evidence_ref: str


class ObjectiveMetrics(BaseModel):
    """Objective call metrics."""
    aht_sec: int
    first_contact_resolution: bool
    interruptions: int = 0
    handoff_performed: bool = False
    first_response_sec: Optional[float] = None
    estimated_value_usd: Optional[float] = None


class ObjectiveOutcome(BaseModel):
    """Objective outcome assessment."""
    status: CallStatus
    scored_criteria: List[ScoredCriteria]
    metrics: ObjectiveMetrics
    confidence: float = Field(..., ge=0.0, le=1.0)


class PerceptionGapDriver(BaseModel):
    """Driver of perception gap."""
    type: str
    weight: float = Field(..., ge=0.0, le=1.0)
    note: Optional[str] = None


class PerceptionGap(BaseModel):
    """Perception gap analysis."""
    gap_score: float = Field(..., ge=0.0)
    gap_class: GapClass
    drivers: List[PerceptionGapDriver] = Field(default_factory=list)


class OutcomesInfo(BaseModel):
    """Complete outcomes section."""
    perceived: List[PerceivedOutcome]
    objective: ObjectiveOutcome
    perception_gap: PerceptionGap


class ArtifactsInfo(BaseModel):
    """Call artifacts and references."""
    recording_url: Optional[str] = None
    transcript_url: Optional[str] = None
    provider_raw_payload_ref: Optional[str] = None


class CustomInfo(BaseModel):
    """Custom provider-specific information."""
    provider_specific: Dict[str, Any] = Field(default_factory=dict)
    outcome_hint: Optional[str] = None
    synthetic: Optional[bool] = None
    synthetic_recipe: Optional[str] = None


class AuditInfo(BaseModel):
    """Audit trail information."""
    received_at: str = Field(..., description="ISO 8601 UTC timestamp")
    normalized_at: str = Field(..., description="ISO 8601 UTC timestamp")
    schema_version: str = "0.3"

    @field_validator('received_at', 'normalized_at')
    @classmethod
    def validate_audit_timestamp(cls, v):
        """Ensure audit timestamps are in ISO 8601 format."""
        if not v.endswith('Z'):
            raise ValueError('Audit timestamp must be in UTC with Z suffix')
        return v


# ===== Extended VCP Models (Full Mode) =====

class ModelChoice(BaseModel):
    """Model selection details."""
    chosen: str
    alternatives: List[str] = Field(default_factory=list)
    reason: List[str] = Field(default_factory=list)


class ModelRoles(BaseModel):
    """Model roles assignment."""
    V2V: Optional[ModelChoice] = None  # Voice-to-Voice
    LLM: Optional[ModelChoice] = None
    STT: Optional[ModelChoice] = None  # Speech-to-Text
    TTS: Optional[ModelChoice] = None  # Text-to-Speech


class ModelSelection(BaseModel):
    """Model selection information (full VCP mode)."""
    policy_id: str
    resolved_at: str = Field(..., description="ISO 8601 UTC timestamp")
    roles: ModelRoles


class ImpactMetrics(BaseModel):
    """Impact metrics for HCR."""
    aht_sec: int
    first_contact_resolution: bool
    estimated_value_usd: Optional[float] = None


class HumanReadableReport(BaseModel):
    """Human-readable report (full VCP mode)."""
    audience: str  # "agent", "supervisor", "customer", etc.
    headline: str
    outcome_status: CallStatus
    key_points: List[str] = Field(default_factory=list)
    impact_metrics: Optional[ImpactMetrics] = None


# ===== Main VCP Payload Models =====

class VCPPayloadGTM(BaseModel):
    """VCP payload for GTM mode (streamlined)."""
    call: CallInfo
    outcomes: OutcomesInfo
    artifacts: ArtifactsInfo
    custom: CustomInfo
    audit: AuditInfo


class VCPPayloadFull(BaseModel):
    """VCP payload for full mode (complete VCP 0.3)."""
    call: CallInfo
    model_selection: Optional[ModelSelection] = None
    outcomes: OutcomesInfo
    hcr: Optional[HumanReadableReport] = None
    artifacts: ArtifactsInfo
    custom: CustomInfo
    audit: AuditInfo


class VCPWrapperBase(BaseModel):
    """Base VCP wrapper with common fields."""
    call_id: str
    vcp_version: str = "0.3"

    @field_validator('call_id')
    @classmethod
    def validate_call_id(cls, v):
        """Ensure call_id is a valid UUID string."""
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError('call_id must be a valid UUID')


class VCPWrapperGTM(VCPWrapperBase):
    """Complete VCP wrapper for GTM mode."""
    vcp_payload: VCPPayloadGTM

    @model_validator(mode='after')
    def validate_call_ids_match(self):
        """Ensure call_id matches between wrapper and payload."""
        if hasattr(self.vcp_payload, 'call') and hasattr(self.vcp_payload.call, 'call_id'):
            if self.call_id != self.vcp_payload.call.call_id:
                raise ValueError(f'call_id mismatch: wrapper={self.call_id}, payload={self.vcp_payload.call.call_id}')
        
        return self

class VCPWrapperFull(VCPWrapperBase):
    """Complete VCP wrapper for full mode."""
    vcp_payload: VCPPayloadFull

    @model_validator(mode='after')
    def validate_call_ids_match(self):
        """Ensure call_id matches between wrapper and payload."""
        if hasattr(self.vcp_payload, 'call') and hasattr(self.vcp_payload.call, 'call_id'):
            if self.call_id != self.vcp_payload.call.call_id:
                raise ValueError(f'call_id mismatch: wrapper={self.call_id}, payload={self.vcp_payload.call.call_id}')
        
        return self


# ===== Union Types =====

VCPPayload = Union[VCPPayloadGTM, VCPPayloadFull]
VCPWrapper = Union[VCPWrapperGTM, VCPWrapperFull]


# ===== Utility Functions =====

def create_vcp_wrapper(mode: VCPMode, **kwargs) -> VCPWrapper:
    """Factory function to create VCP wrapper based on mode."""
    if mode == VCPMode.GTM:
        return VCPWrapperGTM(**kwargs)
    elif mode == VCPMode.FULL:
        return VCPWrapperFull(**kwargs)
    else:
        raise ValueError(f"Unsupported VCP mode: {mode}")


def validate_vcp_payload(payload: Dict[str, Any], mode: VCPMode = VCPMode.GTM) -> VCPWrapper:
    """Validate a VCP payload dictionary against the appropriate model."""
    try:
        if mode == VCPMode.GTM:
            return VCPWrapperGTM(**payload)
        elif mode == VCPMode.FULL:
            return VCPWrapperFull(**payload)
        else:
            raise ValueError(f"Unsupported VCP mode: {mode}")
    except Exception as e:
        raise ValueError(f"VCP validation failed: {str(e)}")


def extract_call_metrics(vcp: VCPWrapper) -> Dict[str, Any]:
    """Extract key metrics from a VCP payload for storage."""
    payload = vcp.vcp_payload
    call = payload.call
    objective = payload.outcomes.objective
    
    return {
        "call_id": call.call_id,
        "provider": call.provider,
        "start_time": call.start_time,
        "end_time": call.end_time,
        "duration_sec": call.duration_sec,
        "declared_intent": call.purpose_contract.declared_intent,
        "status": objective.status.value,
        "estimated_value_usd": objective.metrics.estimated_value_usd,
        "aht_sec": objective.metrics.aht_sec,
        "first_contact_resolution": objective.metrics.first_contact_resolution,
        "interruptions": objective.metrics.interruptions,
        "handoff_performed": objective.metrics.handoff_performed,
        "first_response_sec": objective.metrics.first_response_sec,
        "caller_sentiment": payload.outcomes.perceived[0].sentiment.score if payload.outcomes.perceived else None,
        "provider_confidence": objective.confidence,
        "perception_gap_score": payload.outcomes.perception_gap.gap_score,
        "perception_gap_class": payload.outcomes.perception_gap.gap_class.value,
        "capabilities_invoked": call.capabilities_invoked,
    }