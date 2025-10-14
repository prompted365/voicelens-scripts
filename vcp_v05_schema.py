#!/usr/bin/env python3
"""
Voice Context Protocol (VCP) v0.5 Schema
Comprehensive schema merging the real v0.3 structure with v0.4 extensions

This is the definitive VCP v0.5 implementation that properly extends the actual
v0.3 schema structure with provenance, consent, session correlation, channels,
and capabilities tracking features.
"""
from typing import Dict, List, Any, Optional, Union, Literal
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
import json
import hashlib
import uuid

class VCPVersion(str, Enum):
    """Supported VCP versions"""
    V03 = "0.3"
    V04 = "0.4"  # Stub version that was incomplete
    V05 = "0.5"  # Current comprehensive version

class DeploymentMode(str, Enum):
    """Deployment modes for voice AI systems"""
    NATIVE = "native"
    HOSTED_AI = "hosted_ai"
    HYBRID = "hybrid"

class CapabilityType(str, Enum):
    """Types of capabilities that can be invoked during calls"""
    TOOL_CALL = "tool_call"
    FUNCTION_CALL = "function_call"
    API_CALL = "api_call"
    WEBHOOK = "webhook"
    INTEGRATION = "integration"

class ModelRole(str, Enum):
    """AI model roles in voice processing pipeline"""
    V2V = "V2V"        # Voice-to-Voice (end-to-end)
    STT = "STT"        # Speech-to-Text
    LLM = "LLM"        # Large Language Model
    TTS = "TTS"        # Text-to-Speech
    VAD = "VAD"        # Voice Activity Detection
    ASR = "ASR"        # Automatic Speech Recognition

class ConsentStatus(str, Enum):
    """User consent status for data processing"""
    GRANTED = "granted"
    DENIED = "denied"
    PENDING = "pending"
    EXPIRED = "expired"
    REVOKED = "revoked"

class ChannelType(str, Enum):
    """Communication channel types"""
    PHONE = "phone"
    WEB = "web"
    MOBILE = "mobile"
    EMBED = "embed"
    API = "api"
    WEBSOCKET = "websocket"
    # Directional channels (for backward compatibility with v0.4)
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class CallDirection(str, Enum):
    """Call direction types (preferred approach for v0.5+)"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class OutcomeStatus(str, Enum):
    """Call outcome status"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    ERROR = "error"
    UNKNOWN = "unknown"

class GapClass(str, Enum):
    """Perception gap classification"""
    ALIGNED = "aligned"
    MINOR_DEVIATION = "minor_deviation" 
    MAJOR_DEVIATION = "major_deviation"
    CONTRADICTORY = "contradictory"

# Core VCP Models

class CapabilityInvocation(BaseModel):
    """Represents a capability that was invoked during the call"""
    capability_id: str = Field(..., description="Unique identifier for the capability")
    capability_type: CapabilityType = Field(..., description="Type of capability invoked")
    invoked_at: datetime = Field(..., description="When the capability was invoked")
    duration_ms: Optional[int] = Field(None, description="Duration of capability execution in milliseconds")
    success: bool = Field(..., description="Whether the capability executed successfully")
    error_message: Optional[str] = Field(None, description="Error message if capability failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional capability-specific metadata")

class Call(BaseModel):
    """Enhanced call information from v0.3 with v0.5 extensions"""
    call_id: str = Field(..., description="Unique identifier for the call")
    session_id: str = Field(..., description="Session identifier for grouping related calls")
    provider: str = Field(..., description="Voice AI provider (e.g., 'openai', 'retell', 'bland')")
    start_time: datetime = Field(..., description="Call start timestamp")
    end_time: Optional[datetime] = Field(None, description="Call end timestamp")
    duration_sec: Optional[int] = Field(None, description="Total call duration in seconds")
    
    # v0.5 Extensions
    parent_session_id: Optional[str] = Field(None, description="Parent session for hierarchical grouping")
    correlation_id: Optional[str] = Field(None, description="Cross-system correlation identifier")
    channel: Optional[ChannelType] = Field(None, description="Communication channel type")
    direction: Optional[CallDirection] = Field(None, description="Call direction (inbound/outbound)")
    from_: Optional[str] = Field(None, alias="from", description="Originating phone number or identifier")
    to: Optional[str] = Field(None, description="Destination phone number or identifier")
    caller_id: Optional[str] = Field(None, description="Caller identification (anonymized)")
    geographic_region: Optional[str] = Field(None, description="Geographic region of the call")
    
    # Capabilities (enhanced from v0.3)
    capabilities_invoked: List[Union[str, CapabilityInvocation]] = Field(
        default_factory=list, 
        description="List of capabilities invoked (backward compatible with v0.3 strings)"
    )

class TelemetryPrior(BaseModel):
    """Prior telemetry data for model selection"""
    latency_p95: Optional[float] = Field(None, description="95th percentile latency in milliseconds")
    success_rate: Optional[float] = Field(None, description="Success rate (0-1)")
    cost_per_token: Optional[float] = Field(None, description="Cost per token in USD")
    availability: Optional[float] = Field(None, description="Service availability (0-1)")

class ModelRoleInfo(BaseModel):
    """Information about a model role selection"""
    chosen: str = Field(..., description="Selected model identifier")
    alternatives: List[str] = Field(default_factory=list, description="Alternative models considered")
    reason: List[str] = Field(default_factory=list, description="Reasons for model selection")
    telemetry_prior: Optional[TelemetryPrior] = Field(None, description="Prior performance telemetry")
    fallback_used: bool = Field(False, description="Whether fallback model was used")
    selection_time_ms: Optional[float] = Field(None, description="Time taken for model selection")

class ModelSelection(BaseModel):
    """Model selection information (enhanced from v0.3)"""
    policy_id: str = Field(..., description="Policy used for model selection")
    resolved_at: datetime = Field(..., description="When model selection was resolved")
    roles: Dict[ModelRole, ModelRoleInfo] = Field(..., description="Model information by role")
    
    # v0.5 Extensions
    selection_strategy: Optional[str] = Field(None, description="Strategy used for selection (e.g., 'cost_optimized', 'performance')")
    total_selection_time_ms: Optional[float] = Field(None, description="Total time for all model selections")

class ScoredCriteria(BaseModel):
    """Scored evaluation criteria"""
    id: str = Field(..., description="Criteria identifier")
    met: bool = Field(..., description="Whether criteria was met")
    evidence_ref: Optional[str] = Field(None, description="Reference to evidence")
    score: Optional[float] = Field(None, description="Numeric score if applicable")
    weight: Optional[float] = Field(None, description="Weighting of this criteria")

class ObjectiveOutcome(BaseModel):
    """Objective outcome assessment"""
    status: OutcomeStatus = Field(..., description="Overall outcome status")
    scored_criteria: List[ScoredCriteria] = Field(default_factory=list, description="List of evaluated criteria")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Outcome metrics")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")
    assessment_time_ms: Optional[float] = Field(None, description="Time taken for assessment")

class PerceptionGap(BaseModel):
    """Perception gap analysis"""
    gap_score: float = Field(..., description="Gap score (0-1, where 0 is perfect alignment)")
    gap_class: GapClass = Field(..., description="Classification of the gap")
    factors: Optional[List[str]] = Field(None, description="Factors contributing to the gap")
    analysis: Optional[str] = Field(None, description="Detailed gap analysis")

class ModelAttributionRole(BaseModel):
    """Model attribution for a specific role"""
    model_id: str = Field(..., description="Model identifier")
    minutes: float = Field(..., description="Minutes of usage")
    errors: int = Field(0, description="Number of errors")
    tokens_processed: Optional[int] = Field(None, description="Tokens processed by this model")
    cost_usd: Optional[float] = Field(None, description="Cost in USD")

class ModelOutcomeAttribution(BaseModel):
    """Attribution of outcomes to specific models"""
    roles: Dict[ModelRole, ModelAttributionRole] = Field(..., description="Attribution by model role")
    kpis: Dict[str, Any] = Field(..., description="Key performance indicators")
    total_cost_usd: Optional[float] = Field(None, description="Total cost across all models")
    efficiency_score: Optional[float] = Field(None, description="Overall efficiency score")

class Outcomes(BaseModel):
    """Call outcomes (enhanced from v0.3)"""
    perceived: List[str] = Field(default_factory=list, description="Perceived outcomes from user perspective")
    objective: ObjectiveOutcome = Field(..., description="Objective outcome assessment")
    perception_gap: PerceptionGap = Field(..., description="Gap between perceived and objective")
    model_outcome_attribution: ModelOutcomeAttribution = Field(..., description="Attribution to specific models")
    
    # v0.5 Extensions
    user_satisfaction_score: Optional[float] = Field(None, description="User satisfaction (0-1)")
    business_impact: Optional[Dict[str, Any]] = Field(None, description="Business impact metrics")

class HumanReadableContext(BaseModel):
    """Human-readable context (HCR) from v0.3"""
    audience: str = Field(..., description="Target audience for this context")
    headline: str = Field(..., description="Brief headline summary")
    outcome_status: OutcomeStatus = Field(..., description="Outcome status")
    key_points: List[str] = Field(default_factory=list, description="Key points from the interaction")
    impact_metrics: Dict[str, Any] = Field(default_factory=dict, description="Impact metrics")
    
    # v0.5 Extensions
    summary: Optional[str] = Field(None, description="Detailed summary")
    recommendations: Optional[List[str]] = Field(None, description="Recommendations for improvement")
    alert_level: Optional[Literal["info", "warning", "critical"]] = Field(None, description="Alert level if applicable")

class Artifacts(BaseModel):
    """Artifacts and references"""
    provider_raw_payload_ref: Optional[str] = Field(None, description="Reference to raw provider payload")
    audio_recording_ref: Optional[str] = Field(None, description="Reference to audio recording")
    transcript_ref: Optional[str] = Field(None, description="Reference to full transcript")
    
    # v0.5 Extensions
    system_logs_ref: Optional[str] = Field(None, description="Reference to system logs")
    debug_artifacts: Optional[Dict[str, str]] = Field(None, description="Debug artifact references")
    compliance_records: Optional[Dict[str, str]] = Field(None, description="Compliance record references")

class CustomProviderData(BaseModel):
    """Custom provider-specific data structure"""
    data: Dict[str, Any] = Field(..., description="Provider-specific data")

class Custom(BaseModel):
    """Custom provider-specific data (enhanced from v0.3)"""
    provider_specific: Dict[str, CustomProviderData] = Field(
        default_factory=dict,
        description="Provider-specific custom data"
    )
    
    # v0.5 Extensions
    integrations: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Third-party integration data")
    experimental: Optional[Dict[str, Any]] = Field(None, description="Experimental features data")

class ConsentRecord(BaseModel):
    """User consent information"""
    consent_id: str = Field(..., description="Unique consent identifier")
    status: ConsentStatus = Field(..., description="Current consent status")
    granted_at: Optional[datetime] = Field(None, description="When consent was granted")
    expires_at: Optional[datetime] = Field(None, description="When consent expires")
    scope: List[str] = Field(..., description="Scope of consent (e.g., 'recording', 'analytics', 'storage')")
    version: str = Field(..., description="Consent policy version")
    user_agent: Optional[str] = Field(None, description="User agent when consent was given")
    ip_address_hash: Optional[str] = Field(None, description="Hashed IP address")

class Provenance(BaseModel):
    """Data provenance and lineage information"""
    source_system: str = Field(..., description="System that generated this VCP record")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = Field(None, description="Service/user that created this record")
    transformation_history: List[str] = Field(default_factory=list, description="History of transformations applied")
    data_retention_policy: Optional[str] = Field(None, description="Applicable data retention policy")
    compliance_flags: Optional[List[str]] = Field(None, description="Compliance flags (GDPR, CCPA, etc.)")

class Audit(BaseModel):
    """Audit information (enhanced from v0.3)"""
    received_at: datetime = Field(..., description="When the record was received")
    schema_version: str = Field(..., description="VCP schema version")
    
    # v0.5 Extensions
    processed_at: Optional[datetime] = Field(None, description="When processing completed")
    processing_duration_ms: Optional[float] = Field(None, description="Processing duration in milliseconds")
    validation_errors: Optional[List[str]] = Field(None, description="Validation errors encountered")
    checksum: Optional[str] = Field(None, description="Record checksum for integrity")

# Main VCP Message Structure

class VCPPayload(BaseModel):
    """The main VCP payload structure"""
    call: Call
    model_selection: ModelSelection
    outcomes: Outcomes
    hcr: HumanReadableContext
    artifacts: Artifacts
    custom: Custom
    
    # v0.5 Extensions
    consent: Optional[ConsentRecord] = Field(None, description="User consent information")
    provenance: Provenance = Field(..., description="Data provenance information")

class VCPMessage(BaseModel):
    """Complete VCP v0.5 message structure"""
    vcp_version: VCPVersion = Field(VCPVersion.V05, description="VCP schema version")
    vcp_payload: VCPPayload = Field(..., description="Main VCP payload")
    audit: Audit = Field(..., description="Audit information")

    @field_validator('vcp_version')
    @classmethod
    def validate_version(cls, v):
        """Validate VCP version"""
        if v not in [VCPVersion.V03, VCPVersion.V04, VCPVersion.V05]:
            raise ValueError(f"Unsupported VCP version: {v}")
        return v

    @model_validator(mode='after')
    def validate_version_compatibility(self):
        """Validate version compatibility"""
        version = self.vcp_version
        payload = self.vcp_payload
        
        if version == VCPVersion.V03:
            # v0.3 compatibility checks
            if payload and hasattr(payload, 'consent') and payload.consent:
                raise ValueError("Consent field not supported in v0.3")
            if payload and hasattr(payload, 'provenance') and payload.provenance:
                raise ValueError("Provenance field not supported in v0.3")
        
        return self

    def compute_checksum(self) -> str:
        """Compute checksum for the VCP message"""
        content = json.dumps(self.model_dump(exclude={'audit': {'checksum'}}), sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()

    def to_v03_compatible(self) -> Dict[str, Any]:
        """Convert to v0.3 compatible format"""
        data = self.model_dump()
        
        # Remove v0.5-specific fields
        if 'consent' in data['vcp_payload']:
            del data['vcp_payload']['consent']
        if 'provenance' in data['vcp_payload']:
            del data['vcp_payload']['provenance']
        
        # Simplify capabilities to string list for v0.3 compatibility
        call = data['vcp_payload']['call']
        if 'capabilities_invoked' in call:
            capabilities = call['capabilities_invoked']
            if isinstance(capabilities, list) and capabilities:
                # Convert CapabilityInvocation objects to strings
                simple_capabilities = []
                for cap in capabilities:
                    if isinstance(cap, dict) and 'capability_id' in cap:
                        simple_capabilities.append(cap['capability_id'])
                    elif isinstance(cap, str):
                        simple_capabilities.append(cap)
                call['capabilities_invoked'] = simple_capabilities
        
        data['vcp_version'] = "0.3"
        return data

# Utility Classes

class VCPValidator:
    """Enhanced VCP validator supporting multiple versions"""
    
    @staticmethod
    def validate_v05(message: VCPMessage) -> Dict[str, List[str]]:
        """Validate VCP v0.5 message"""
        errors = []
        warnings = []
        
        try:
            # Basic validation via pydantic
            message.model_dump()
            
            # Additional business logic validation
            if message.vcp_payload.call.end_time and message.vcp_payload.call.start_time:
                if message.vcp_payload.call.end_time < message.vcp_payload.call.start_time:
                    errors.append("Call end_time cannot be before start_time")
            
            # Capability validation
            for capability in message.vcp_payload.call.capabilities_invoked:
                if isinstance(capability, dict):
                    cap_obj = CapabilityInvocation(**capability)
                    if cap_obj.invoked_at < message.vcp_payload.call.start_time:
                        warnings.append(f"Capability {cap_obj.capability_id} invoked before call start")
            
            # Consent validation
            if message.vcp_payload.consent:
                if message.vcp_payload.consent.status == ConsentStatus.EXPIRED:
                    warnings.append("User consent has expired")
                elif message.vcp_payload.consent.status == ConsentStatus.REVOKED:
                    errors.append("Cannot process data with revoked consent")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return {"errors": errors, "warnings": warnings}
    
    @staticmethod
    def upgrade_from_v03(v03_data: Dict[str, Any]) -> VCPMessage:
        """Upgrade v0.3 message to v0.5"""
        # Add required v0.5 fields
        v03_data['vcp_version'] = "0.5"
        
        # Add provenance
        if 'provenance' not in v03_data.get('vcp_payload', {}):
            v03_data['vcp_payload']['provenance'] = {
                "source_system": v03_data['vcp_payload']['call']['provider'],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "transformation_history": ["upgraded_from_v0.3"]
            }
        
        # Convert simple capabilities to enhanced format if needed
        call = v03_data['vcp_payload']['call']
        if 'capabilities_invoked' in call and call['capabilities_invoked']:
            enhanced_caps = []
            for cap in call['capabilities_invoked']:
                if isinstance(cap, str):
                    enhanced_caps.append({
                        "capability_id": cap,
                        "capability_type": "tool_call",
                        "invoked_at": call['start_time'],
                        "success": True
                    })
                else:
                    enhanced_caps.append(cap)
            call['capabilities_invoked'] = enhanced_caps
        
        return VCPMessage(**v03_data)

def create_example_v05_message() -> VCPMessage:
    """Create a comprehensive VCP v0.5 example message"""
    now = datetime.now(timezone.utc)
    call_start = now.replace(second=0, microsecond=0)
    call_end = call_start.replace(minute=call_start.minute + 3, second=15)
    
    return VCPMessage(
        vcp_version=VCPVersion.V05,
        vcp_payload=VCPPayload(
            call=Call(
                call_id="call_openai_v05_demo_123",
                session_id="sess_openai_demo_789", 
                provider="openai",
                start_time=call_start,
                end_time=call_end,
                duration_sec=195,
                parent_session_id="parent_sess_456",
                correlation_id=str(uuid.uuid4()),
                channel=ChannelType.WEB,
                caller_id="caller_anon_abc123",
                geographic_region="us-west",
                capabilities_invoked=[
                    CapabilityInvocation(
                        capability_id="book_appointment",
                        capability_type=CapabilityType.TOOL_CALL,
                        invoked_at=call_start.replace(minute=call_start.minute + 1),
                        duration_ms=2300,
                        success=True,
                        metadata={"appointment_type": "consultation", "scheduled_for": "2025-10-15T14:00:00Z"}
                    ),
                    CapabilityInvocation(
                        capability_id="send_confirmation_email",
                        capability_type=CapabilityType.INTEGRATION,
                        invoked_at=call_start.replace(minute=call_start.minute + 2),
                        duration_ms=850,
                        success=True,
                        metadata={"email_template": "appointment_confirmation", "recipient": "user@example.com"}
                    )
                ]
            ),
            model_selection=ModelSelection(
                policy_id="openai-realtime-v05",
                resolved_at=call_start,
                selection_strategy="performance_optimized",
                total_selection_time_ms=45.2,
                roles={
                    ModelRole.V2V: ModelRoleInfo(
                        chosen="openai.realtime-v1-2024-12",
                        alternatives=["openai.realtime-preview"],
                        reason=["native_speech_to_speech", "low_latency", "production_ready"],
                        telemetry_prior=TelemetryPrior(
                            latency_p95=250,
                            success_rate=0.94,
                            cost_per_token=0.00002,
                            availability=0.99
                        ),
                        selection_time_ms=15.3
                    ),
                    ModelRole.STT: ModelRoleInfo(
                        chosen="openai.whisper-v1",
                        alternatives=[],
                        reason=["integrated_realtime"],
                        selection_time_ms=5.1
                    ),
                    ModelRole.LLM: ModelRoleInfo(
                        chosen="openai.gpt-4o-realtime",
                        alternatives=["openai.gpt-4-turbo"],
                        reason=["integrated_realtime", "function_calling"],
                        selection_time_ms=12.8
                    ),
                    ModelRole.TTS: ModelRoleInfo(
                        chosen="openai.tts-realtime",
                        alternatives=[],
                        reason=["integrated_realtime", "natural_voice"],
                        selection_time_ms=8.0
                    )
                }
            ),
            outcomes=Outcomes(
                perceived=["Appointment scheduled successfully", "Helpful and efficient"],
                objective=ObjectiveOutcome(
                    status=OutcomeStatus.SUCCESS,
                    scored_criteria=[
                        ScoredCriteria(
                            id="tool_0",
                            met=True,
                            evidence_ref="tool_log#book_appointment",
                            score=0.95,
                            weight=0.4
                        ),
                        ScoredCriteria(
                            id="confirmation_sent",
                            met=True,
                            evidence_ref="integration_log#send_confirmation_email",
                            score=1.0,
                            weight=0.3
                        ),
                        ScoredCriteria(
                            id="user_satisfaction",
                            met=True,
                            evidence_ref="sentiment_analysis#final",
                            score=0.87,
                            weight=0.3
                        )
                    ],
                    metrics={
                        "aht_sec": 195,
                        "first_contact_resolution": True,
                        "user_effort_score": 1.2,
                        "task_completion_rate": 1.0
                    },
                    confidence=0.92,
                    assessment_time_ms=156.3
                ),
                perception_gap=PerceptionGap(
                    gap_score=0.15,
                    gap_class=GapClass.ALIGNED,
                    factors=["user_tone_positive", "task_completed"],
                    analysis="High alignment between perceived and objective outcomes"
                ),
                model_outcome_attribution=ModelOutcomeAttribution(
                    roles={
                        ModelRole.V2V: ModelAttributionRole(
                            model_id="openai.realtime-v1-2024-12",
                            minutes=3.25,
                            errors=0,
                            tokens_processed=2150,
                            cost_usd=0.043
                        ),
                        ModelRole.STT: ModelAttributionRole(
                            model_id="openai.whisper-v1",
                            minutes=3.25,
                            errors=0,
                            tokens_processed=1200,
                            cost_usd=0.024
                        ),
                        ModelRole.LLM: ModelAttributionRole(
                            model_id="openai.gpt-4o-realtime",
                            minutes=3.25,
                            errors=0,
                            tokens_processed=950,
                            cost_usd=0.038
                        ),
                        ModelRole.TTS: ModelAttributionRole(
                            model_id="openai.tts-realtime",
                            minutes=3.25,
                            errors=0,
                            tokens_processed=800,
                            cost_usd=0.016
                        )
                    },
                    kpis={
                        "conversion": True,
                        "aht_sec": 195,
                        "gap_score": 0.15,
                        "cost_per_call_usd": 0.121
                    },
                    total_cost_usd=0.121,
                    efficiency_score=0.89
                ),
                user_satisfaction_score=0.87,
                business_impact={
                    "revenue_attributed_usd": 150.00,
                    "customer_lifetime_value_impact": 0.05,
                    "conversion_probability": 0.92
                }
            ),
            hcr=HumanReadableContext(
                audience="agent",
                headline="Appointment booking completed successfully via realtime voice",
                outcome_status=OutcomeStatus.SUCCESS,
                key_points=[
                    "Voice: alloy",
                    "Tools called: 2 (book_appointment, send_confirmation_email)",
                    "Audio tokens: 21,250",
                    "Cost: $0.121"
                ],
                impact_metrics={
                    "aht_sec": 195,
                    "cost_efficiency": 0.89,
                    "user_satisfaction": 0.87
                },
                summary="User successfully booked a consultation appointment via voice interface. Both appointment booking and email confirmation completed without errors.",
                recommendations=[
                    "Consider pre-loading user preferences to reduce booking time",
                    "Implement voice confirmation for critical appointment details"
                ],
                alert_level="info"
            ),
            artifacts=Artifacts(
                provider_raw_payload_ref="s3://vcp-raw/openai/sess_openai_demo_789.json",
                audio_recording_ref="s3://vcp-audio/sess_openai_demo_789.wav",
                transcript_ref="s3://vcp-transcripts/sess_openai_demo_789.txt",
                system_logs_ref="s3://vcp-logs/sess_openai_demo_789.log",
                debug_artifacts={
                    "model_selection_trace": "s3://vcp-debug/selection_trace_demo_789.json",
                    "capability_execution_log": "s3://vcp-debug/capabilities_demo_789.json"
                },
                compliance_records={
                    "gdpr_processing_record": "s3://vcp-compliance/gdpr_demo_789.json",
                    "retention_schedule": "s3://vcp-compliance/retention_demo_789.json"
                }
            ),
            custom=Custom(
                provider_specific={
                    "openai": CustomProviderData(data={
                        "model": "gpt-4o-realtime-preview-2024-12-17",
                        "usage": {
                            "total_tokens": 2150,
                            "input_audio_tokens": 12500,
                            "output_audio_tokens": 8750,
                            "cached_tokens": 0
                        },
                        "voice": "alloy",
                        "response_format": "audio",
                        "temperature": 0.7,
                        "tools_available": ["book_appointment", "send_email", "lookup_availability"]
                    })
                },
                integrations={
                    "calendar_service": {
                        "provider": "google_calendar",
                        "api_version": "v3",
                        "success": True,
                        "response_time_ms": 234
                    },
                    "email_service": {
                        "provider": "sendgrid",
                        "template_id": "appointment_confirmation_v2",
                        "success": True,
                        "response_time_ms": 156
                    }
                },
                experimental={
                    "sentiment_tracking": {
                        "initial_sentiment": 0.65,
                        "final_sentiment": 0.87,
                        "sentiment_trajectory": "improving"
                    },
                    "voice_biometrics": {
                        "stress_level": 0.23,
                        "confidence_level": 0.78,
                        "speech_rate": "normal"
                    }
                }
            ),
            consent=ConsentRecord(
                consent_id="consent_user_abc123_v2",
                status=ConsentStatus.GRANTED,
                granted_at=call_start.replace(minute=call_start.minute - 5),
                expires_at=call_start.replace(year=call_start.year + 1),
                scope=["recording", "analytics", "storage", "ai_processing", "integration_calls"],
                version="2.1",
                user_agent="Mozilla/5.0 (compatible; VoiceLens/1.0)",
                ip_address_hash="sha256:abc123def456..."
            ),
            provenance=Provenance(
                source_system="openai.realtime_api",
                created_at=call_end.replace(second=call_end.second + 5),
                created_by="voicelens.webhook_processor",
                transformation_history=[
                    "extracted_from_openai_webhook", 
                    "enhanced_with_capability_details",
                    "added_business_impact_metrics",
                    "validated_v0.5_schema"
                ],
                data_retention_policy="voice_ai_standard_7_years",
                compliance_flags=["GDPR", "CCPA", "HIPAA_COMPLIANT"]
            )
        ),
        audit=Audit(
            received_at=call_end.replace(second=call_end.second + 2),
            schema_version="0.5",
            processed_at=call_end.replace(second=call_end.second + 8),
            processing_duration_ms=234.7,
            validation_errors=None,
            checksum=None  # Will be computed after creation
        )
    )

if __name__ == "__main__":
    # Example usage
    example = create_example_v05_message()
    example.audit.checksum = example.compute_checksum()
    
    print("VCP v0.5 Example:")
    print(json.dumps(example.model_dump(), indent=2, default=str))
    
    # Test validation
    validator = VCPValidator()
    validation_result = validator.validate_v05(example)
    print(f"\nValidation Result: {validation_result}")
    
    # Test v0.3 compatibility
    v03_compatible = example.to_v03_compatible()
    print(f"\nv0.3 Compatible Version Available: {len(json.dumps(v03_compatible, default=str))} bytes")
