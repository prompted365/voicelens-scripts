# VCP Schema v0.5 - Complete Specification

## Overview

The Voice Context Protocol (VCP) v0.5 is a comprehensive schema for standardizing voice AI interactions across providers. This document provides the complete specification, implementation details, and validation rules.

## Schema Architecture

### Core Message Structure

Every VCP message follows this root structure:

```python
# From vcp_v05_schema.py
class VCPMessage(BaseModel):
    """Complete VCP v0.5 message structure"""
    vcp_version: VCPVersion = Field(VCPVersion.V05, description="VCP schema version")
    vcp_payload: VCPPayload = Field(..., description="Main VCP payload")
    audit: Audit = Field(..., description="Audit information")
```

### Version Support and Compatibility

VCP supports multiple versions with backward compatibility:

```python
class VCPVersion(str, Enum):
    """Supported VCP versions"""
    V03 = "0.3"  # Foundation version
    V04 = "0.4"  # Added provenance and consent
    V05 = "0.5"  # Current version with full feature set
```

**Version Compatibility Matrix:**

| Feature | v0.3 | v0.4 | v0.5 |
|---------|------|------|------|
| Basic Call Info | ✅ | ✅ | ✅ |
| Outcomes & HCR | ✅ | ✅ | ✅ |
| Provenance | ❌ | ✅ | ✅ |
| Consent Tracking | ❌ | ✅ | ✅ |
| Channel Direction | ❌ | Limited | ✅ |
| Model Attribution | ❌ | Basic | ✅ |
| Business Impact | ❌ | ❌ | ✅ |

## Detailed Field Specifications

### 1. Call Information (`call`)

The call object contains comprehensive information about the voice interaction:

```python
class Call(BaseModel):
    """Enhanced call information from v0.3 with v0.5 extensions"""
    # Required Core Fields
    call_id: str = Field(..., description="Unique identifier for the call")
    session_id: str = Field(..., description="Session identifier for grouping related calls")
    provider: str = Field(..., description="Voice AI provider (e.g., 'openai', 'retell', 'bland')")
    start_time: datetime = Field(..., description="Call start timestamp")
    
    # Optional Core Fields
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
    capabilities_invoked: List[Union[str, CapabilityInvocation]] = Field(
        default_factory=list, 
        description="List of capabilities invoked (backward compatible with v0.3 strings)"
    )
```

#### Channel and Direction Support

VCP v0.5 introduces dual support for channels:

```python
class ChannelType(str, Enum):
    """Communication channel types"""
    # Traditional channel types
    PHONE = "phone"
    WEB = "web"
    MOBILE = "mobile"
    EMBED = "embed"
    API = "api"
    WEBSOCKET = "websocket"
    
    # Directional channels (backward compatibility with v0.4)
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class CallDirection(str, Enum):
    """Call direction types (preferred approach for v0.5+)"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
```

**Implementation Guidelines:**
- **Preferred**: Use `channel` for medium (phone/web) + `direction` for directionality
- **Legacy**: Use `channel="inbound"` or `channel="outbound"` for backward compatibility
- **Transformation**: Systems should map legacy format to preferred format when possible

#### Capability Invocations

Capabilities can be specified as simple strings (v0.3 compatibility) or detailed objects:

```python
class CapabilityType(str, Enum):
    """Types of capabilities that can be invoked during calls"""
    TOOL_CALL = "tool_call"
    FUNCTION_CALL = "function_call"
    API_CALL = "api_call"
    WEBHOOK = "webhook"
    INTEGRATION = "integration"

class CapabilityInvocation(BaseModel):
    """Represents a capability that was invoked during the call"""
    capability_id: str = Field(..., description="Unique identifier for the capability")
    capability_type: CapabilityType = Field(..., description="Type of capability invoked")
    invoked_at: datetime = Field(..., description="When the capability was invoked")
    duration_ms: Optional[int] = Field(None, description="Duration of capability execution in milliseconds")
    success: bool = Field(..., description="Whether the capability executed successfully")
    error_message: Optional[str] = Field(None, description="Error message if capability failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional capability-specific metadata")
```

### 2. Model Selection (`model_selection`)

Comprehensive AI model selection and attribution:

```python
class ModelSelection(BaseModel):
    """Model selection information (enhanced from v0.3)"""
    policy_id: str = Field(..., description="Policy used for model selection")
    resolved_at: datetime = Field(..., description="When model selection was resolved")
    roles: Dict[ModelRole, ModelRoleInfo] = Field(..., description="Model information by role")
    
    # v0.5 Extensions
    selection_strategy: Optional[str] = Field(None, description="Strategy used for selection")
    total_selection_time_ms: Optional[float] = Field(None, description="Total time for all model selections")

class ModelRole(str, Enum):
    """AI model roles in voice processing pipeline"""
    V2V = "V2V"        # Voice-to-Voice (end-to-end)
    STT = "STT"        # Speech-to-Text
    LLM = "LLM"        # Large Language Model
    TTS = "TTS"        # Text-to-Speech
    VAD = "VAD"        # Voice Activity Detection
    ASR = "ASR"        # Automatic Speech Recognition

class ModelRoleInfo(BaseModel):
    """Information about a model role selection"""
    chosen: str = Field(..., description="Selected model identifier")
    alternatives: List[str] = Field(default_factory=list, description="Alternative models considered")
    reason: List[str] = Field(default_factory=list, description="Reasons for model selection")
    telemetry_prior: Optional[TelemetryPrior] = Field(None, description="Prior performance telemetry")
    fallback_used: bool = Field(False, description="Whether fallback model was used")
    selection_time_ms: Optional[float] = Field(None, description="Time taken for model selection")
```

### 3. Outcomes (`outcomes`)

Comprehensive outcome tracking with objective and perceived assessments:

```python
class Outcomes(BaseModel):
    """Call outcomes (enhanced from v0.3)"""
    perceived: List[str] = Field(default_factory=list, description="Perceived outcomes from user perspective")
    objective: ObjectiveOutcome = Field(..., description="Objective outcome assessment")
    perception_gap: PerceptionGap = Field(..., description="Gap between perceived and objective")
    model_outcome_attribution: ModelOutcomeAttribution = Field(..., description="Attribution to specific models")
    
    # v0.5 Extensions
    user_satisfaction_score: Optional[float] = Field(None, description="User satisfaction (0-1)")
    business_impact: Optional[Dict[str, Any]] = Field(None, description="Business impact metrics")

class OutcomeStatus(str, Enum):
    """Call outcome status"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    ERROR = "error"
    UNKNOWN = "unknown"    # Added for cases where status cannot be determined

class ObjectiveOutcome(BaseModel):
    """Objective outcome assessment"""
    status: OutcomeStatus = Field(..., description="Overall outcome status")
    scored_criteria: List[ScoredCriteria] = Field(default_factory=list, description="List of evaluated criteria")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Outcome metrics")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")
    assessment_time_ms: Optional[float] = Field(None, description="Time taken for assessment")
```

### 4. Human Readable Context (`hcr`)

Summary information for human consumption:

```python
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
```

### 5. Artifacts (`artifacts`)

References to recordings, transcripts, and related data:

```python
class Artifacts(BaseModel):
    """Artifacts and references"""
    provider_raw_payload_ref: Optional[str] = Field(None, description="Reference to raw provider payload")
    audio_recording_ref: Optional[str] = Field(None, description="Reference to audio recording")
    transcript_ref: Optional[str] = Field(None, description="Reference to full transcript")
    
    # v0.5 Extensions
    system_logs_ref: Optional[str] = Field(None, description="Reference to system logs")
    debug_artifacts: Optional[Dict[str, str]] = Field(None, description="Debug artifact references")
    compliance_records: Optional[Dict[str, str]] = Field(None, description="Compliance record references")
```

**Artifact Reference Format:**
```
# S3/Cloud Storage
s3://bucket-name/path/to/artifact.ext
gs://bucket-name/path/to/artifact.ext
azure://container/path/to/artifact.ext

# HTTP URLs
https://domain.com/api/artifacts/123/audio.wav
https://cdn.domain.com/transcripts/abc123.txt

# Internal References
internal://artifact-service/uuid
local://path/to/file.ext
```

### 6. Custom Data (`custom`)

Provider-specific and experimental data:

```python
class Custom(BaseModel):
    """Custom provider-specific data (enhanced from v0.3)"""
    provider_specific: Dict[str, CustomProviderData] = Field(
        default_factory=dict,
        description="Provider-specific custom data"
    )
    
    # v0.5 Extensions
    integrations: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Third-party integration data")
    experimental: Optional[Dict[str, Any]] = Field(None, description="Experimental features data")

class CustomProviderData(BaseModel):
    """Custom provider-specific data structure"""
    data: Dict[str, Any] = Field(..., description="Provider-specific data")
```

**Provider-Specific Data Examples:**

#### Retell AI
```json
{
  "provider_specific": {
    "retell": {
      "data": {
        "call": {
          "call_id": "Jabr9TXYYJHfvl6Syypi88rdAHYHmcq6",
          "direction": "inbound",
          "disconnection_reason": "user_hangup",
          "transcript": "Full conversation transcript...",
          "metadata": {}
        },
        "event": "call_ended"
      }
    }
  }
}
```

#### Assistable AI with Extractions
```json
{
  "provider_specific": {
    "assistable": {
      "data": {
        "call_id": "assistable_call_abc123",
        "call_type": "outbound_sales",
        "direction": "outbound",
        "extractions": {
          "contact_zip_code": "90210",
          "customer_interest_level": "high",
          "next_followup_date": "2025-10-21",
          "product_interest": "premium_package",
          "budget_range": "$500-1000",
          "decision_maker": true,
          "purchase_timeline": "within_30_days"
        }
      }
    }
  },
  "integrations": {
    "crm_system": {
      "provider": "assistable_extractions",
      "lead_score": "high",
      "contact_data": {
        "contact_zip_code": "90210",
        "customer_interest_level": "high"
      }
    },
    "sales_system": {
      "provider": "assistable_sales_intelligence",
      "opportunity_data": {
        "budget_range": "$500-1000",
        "purchase_timeline": "within_30_days",
        "decision_maker": true
      },
      "qualification_score": 0.85
    }
  }
}
```

### 7. Consent Tracking (`consent`)

User consent management for compliance:

```python
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

class ConsentStatus(str, Enum):
    """User consent status for data processing"""
    GRANTED = "granted"
    DENIED = "denied"
    PENDING = "pending"
    EXPIRED = "expired"
    REVOKED = "revoked"
```

### 8. Provenance (`provenance`)

Data lineage and processing history:

```python
class Provenance(BaseModel):
    """Data provenance and lineage information"""
    source_system: str = Field(..., description="System that generated this VCP record")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = Field(None, description="Service/user that created this record")
    transformation_history: List[str] = Field(default_factory=list, description="History of transformations applied")
    data_retention_policy: Optional[str] = Field(None, description="Applicable data retention policy")
    compliance_flags: Optional[List[str]] = Field(None, description="Compliance flags (GDPR, CCPA, etc.)")
```

### 9. Audit Information (`audit`)

Processing and validation metadata:

```python
class Audit(BaseModel):
    """Audit information (enhanced from v0.3)"""
    received_at: datetime = Field(..., description="When the record was received")
    schema_version: str = Field(..., description="VCP schema version")
    
    # v0.5 Extensions
    processed_at: Optional[datetime] = Field(None, description="When processing completed")
    processing_duration_ms: Optional[float] = Field(None, description="Processing duration in milliseconds")
    validation_errors: Optional[List[str]] = Field(None, description="Validation errors encountered")
    checksum: Optional[str] = Field(None, description="Record checksum for integrity")
```

## Validation Rules

### Schema Validation

The VCP validator implements comprehensive validation:

```python
class VCPValidator:
    """Enhanced VCP validator supporting multiple versions"""
    
    @staticmethod
    def validate_v05(message: VCPMessage) -> Dict[str, List[str]]:
        """Validate VCP v0.5 message"""
        errors = []
        warnings = []
        
        try:
            # 1. Basic validation via pydantic
            message.model_dump()
            
            # 2. Business logic validation
            if message.vcp_payload.call.end_time and message.vcp_payload.call.start_time:
                if message.vcp_payload.call.end_time < message.vcp_payload.call.start_time:
                    errors.append("Call end_time cannot be before start_time")
            
            # 3. Capability validation
            for capability in message.vcp_payload.call.capabilities_invoked:
                if isinstance(capability, dict):
                    cap_obj = CapabilityInvocation(**capability)
                    if cap_obj.invoked_at < message.vcp_payload.call.start_time:
                        warnings.append(f"Capability {cap_obj.capability_id} invoked before call start")
            
            # 4. Consent validation
            if message.vcp_payload.consent:
                if message.vcp_payload.consent.status == ConsentStatus.EXPIRED:
                    warnings.append("User consent has expired")
                elif message.vcp_payload.consent.status == ConsentStatus.REVOKED:
                    errors.append("Cannot process data with revoked consent")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return {"errors": errors, "warnings": warnings}
```

### Required Field Matrix

| Component | Required Fields | Optional Fields |
|-----------|----------------|-----------------|
| **VCPMessage** | vcp_version, vcp_payload, audit | - |
| **Call** | call_id, session_id, provider, start_time | end_time, duration_sec, channel, direction |
| **ModelSelection** | policy_id, resolved_at, roles | selection_strategy, total_selection_time_ms |
| **Outcomes** | objective, perception_gap, model_outcome_attribution | perceived, user_satisfaction_score |
| **ObjectiveOutcome** | status | scored_criteria, metrics, confidence |
| **HumanReadableContext** | audience, headline, outcome_status | key_points, summary, recommendations |
| **Audit** | received_at, schema_version | processed_at, validation_errors |

## Version Upgrade Path

### From v0.3 to v0.5

```python
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
    
    # Convert simple capabilities to enhanced format
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
```

### Backward Compatibility

```python
def to_v03_compatible(self) -> Dict[str, Any]:
    """Convert to v0.3 compatible format"""
    data = self.model_dump()
    
    # Remove v0.5-specific fields
    if 'consent' in data['vcp_payload']:
        del data['vcp_payload']['consent']
    if 'provenance' in data['vcp_payload']:
        del data['vcp_payload']['provenance']
    
    # Simplify capabilities to string list
    call = data['vcp_payload']['call']
    if 'capabilities_invoked' in call:
        capabilities = call['capabilities_invoked']
        if isinstance(capabilities, list) and capabilities:
            simple_capabilities = []
            for cap in capabilities:
                if isinstance(cap, dict) and 'capability_id' in cap:
                    simple_capabilities.append(cap['capability_id'])
                elif isinstance(cap, str):
                    simple_capabilities.append(cap)
            call['capabilities_invoked'] = simple_capabilities
    
    data['vcp_version'] = "0.3"
    return data
```

## Implementation Examples

### Complete VCP v0.5 Message

```python
example_message = VCPMessage(
    vcp_version=VCPVersion.V05,
    vcp_payload=VCPPayload(
        call=Call(
            call_id="call_openai_v05_demo_123",
            session_id="sess_openai_demo_789",
            provider="openai",
            start_time=datetime(2025, 10, 14, 12, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 10, 14, 12, 3, 15, tzinfo=timezone.utc),
            duration_sec=195,
            channel=ChannelType.WEB,
            direction=CallDirection.INBOUND,
            from_="+12345678901",
            to="+19876543210",
            capabilities_invoked=[
                CapabilityInvocation(
                    capability_id="book_appointment",
                    capability_type=CapabilityType.TOOL_CALL,
                    invoked_at=datetime(2025, 10, 14, 12, 1, 0, tzinfo=timezone.utc),
                    duration_ms=2300,
                    success=True,
                    metadata={"appointment_type": "consultation"}
                )
            ]
        ),
        model_selection=ModelSelection(
            policy_id="openai-realtime-v05",
            resolved_at=datetime(2025, 10, 14, 12, 0, 0, tzinfo=timezone.utc),
            roles={
                ModelRole.V2V: ModelRoleInfo(
                    chosen="openai.realtime-v1-2024-12",
                    alternatives=["openai.realtime-preview"],
                    reason=["native_speech_to_speech", "low_latency"]
                )
            }
        ),
        outcomes=Outcomes(
            perceived=["Appointment scheduled successfully"],
            objective=ObjectiveOutcome(
                status=OutcomeStatus.SUCCESS,
                metrics={"task_completion_rate": 1.0}
            ),
            perception_gap=PerceptionGap(
                gap_score=0.15,
                gap_class=GapClass.ALIGNED
            ),
            model_outcome_attribution=ModelOutcomeAttribution(
                roles={
                    ModelRole.V2V: ModelAttributionRole(
                        model_id="openai.realtime-v1-2024-12",
                        minutes=3.25,
                        errors=0,
                        cost_usd=0.043
                    )
                },
                kpis={"cost_per_call_usd": 0.043}
            )
        ),
        hcr=HumanReadableContext(
            audience="agent",
            headline="Appointment booking completed successfully",
            outcome_status=OutcomeStatus.SUCCESS,
            key_points=["Voice interface used", "Single tool call", "No errors"]
        ),
        artifacts=Artifacts(
            audio_recording_ref="s3://vcp-audio/sess_openai_demo_789.wav",
            transcript_ref="s3://vcp-transcripts/sess_openai_demo_789.txt"
        ),
        custom=Custom(
            provider_specific={
                "openai": CustomProviderData(data={
                    "model": "gpt-4o-realtime-preview-2024-12-17",
                    "voice": "alloy",
                    "temperature": 0.7
                })
            }
        ),
        consent=ConsentRecord(
            consent_id="consent_user_abc123_v2",
            status=ConsentStatus.GRANTED,
            scope=["recording", "analytics", "storage"],
            version="2.1"
        ),
        provenance=Provenance(
            source_system="openai.realtime_api",
            created_by="voicelens.webhook_processor",
            transformation_history=[
                "extracted_from_openai_webhook",
                "enhanced_with_capability_details",
                "validated_v0.5_schema"
            ]
        )
    ),
    audit=Audit(
        received_at=datetime(2025, 10, 14, 12, 3, 17, tzinfo=timezone.utc),
        schema_version="0.5",
        processing_duration_ms=234.7
    )
)
```

This comprehensive specification provides everything needed to implement VCP v0.5 in any programming language or environment, with complete validation rules, upgrade paths, and real-world examples.