# Voice Context Protocol (VCP) v0.5 Changelog & Migration Guide

## Overview

VCP v0.5 represents a comprehensive consolidation and enhancement of the Voice Context Protocol, merging the real v0.3 production schema with the v0.4 extensions into a unified, production-ready specification.

**Important**: The v0.4 version was discovered to be an incomplete stub implementation. VCP v0.5 properly extends the actual v0.3 schema with all intended v0.4 features.

## Version History

- **v0.3**: Production schema (actual baseline)
- **v0.4**: Incomplete stub implementation (deprecated)
- **v0.5**: Comprehensive schema merging v0.3 + intended v0.4 features (**CURRENT**)
- **v1.0**: Future locked specification (governance-controlled)

## Key Changes in v0.5

### ✅ **Retained from v0.3**
All existing v0.3 structures are preserved with backward compatibility:
- `call` structure with `call_id`, `session_id`, `provider`, timestamps
- `model_selection` with `policy_id`, `resolved_at`, `roles`
- `outcomes` with `perceived`, `objective`, `perception_gap`, `model_outcome_attribution`
- `hcr` (Human Readable Context) structure
- `artifacts` with provider payload references
- `custom.provider_specific` for provider-specific data
- `audit` information with `received_at` and `schema_version`

### 🆕 **New in v0.5**

#### Enhanced Call Information
- **Session Correlation**:
  - `parent_session_id`: Hierarchical session grouping
  - `correlation_id`: Cross-system correlation tracking
- **Channel & Context**:
  - `channel`: Communication channel type (phone, web, mobile, embed, api, websocket)
  - `caller_id`: Anonymized caller identification
  - `geographic_region`: Geographic context
- **Enhanced Capabilities**:
  - Upgraded from simple strings to rich `CapabilityInvocation` objects
  - Tracks `capability_type`, `invoked_at`, `duration_ms`, `success`, `error_message`, `metadata`
  - Backward compatible with v0.3 string format

#### Model Selection Enhancements
- **Selection Strategy**: `selection_strategy` field for tracking optimization approach
- **Timing**: `total_selection_time_ms` and per-role `selection_time_ms` 
- **Enhanced Telemetry**: Cost tracking with `cost_per_token` and `availability` metrics
- **Fallback Tracking**: `fallback_used` flag for model fallback scenarios

#### Comprehensive Outcomes
- **User Satisfaction**: `user_satisfaction_score` (0-1 scale)
- **Business Impact**: Revenue attribution, CLV impact, conversion probability
- **Enhanced Attribution**: Token processing and cost tracking per model role
- **Assessment Timing**: `assessment_time_ms` for performance monitoring

#### Human-Readable Context (HCR) Extensions
- **Detailed Summary**: Full interaction summary beyond key points
- **Recommendations**: AI-generated improvement suggestions
- **Alert Levels**: info/warning/critical classification for operational alerts

#### Artifacts & References
- **System Integration**: `system_logs_ref` for debugging
- **Debug Artifacts**: Structured debug information references
- **Compliance Records**: GDPR, CCPA, retention schedule references

#### Consent Management
New `consent` object for privacy compliance:
- **Consent Tracking**: `consent_id`, `status`, `granted_at`, `expires_at`
- **Scope Definition**: Granular permissions (recording, analytics, storage, ai_processing)
- **Version Control**: Policy version tracking
- **Context**: User agent, hashed IP for audit trails

#### Data Provenance
New `provenance` object for data lineage:
- **Source Tracking**: `source_system`, `created_at`, `created_by`
- **Transformation History**: Complete processing pipeline tracking
- **Compliance**: Data retention policies and compliance flags
- **Quality**: Processing chain and validation history

#### Enhanced Custom Data
- **Integration Data**: Third-party service integration results
- **Experimental Features**: Beta feature data isolation
- **Provider Extensions**: Structured provider-specific extensions

#### Audit Enhancements
- **Processing Metrics**: `processed_at`, `processing_duration_ms`
- **Validation Tracking**: `validation_errors` array
- **Integrity**: Message `checksum` for tamper detection

### 🔧 **Technical Improvements**

#### Pydantic v2 Compatibility
- Updated to modern `@field_validator` and `@model_validator` syntax
- Uses `model_dump()` instead of deprecated `dict()` method
- Full type safety and validation

#### Enhanced Validation
- Cross-field validation (timestamps, capability timing)
- Consent status validation with business logic
- Version compatibility checking

#### Utility Methods
- `compute_checksum()`: Message integrity verification
- `to_v03_compatible()`: Backward compatibility conversion
- `upgrade_from_v03()`: Automatic v0.3 → v0.5 upgrade

## Migration Guide

### Automated Migration (Recommended)

```python
from vcp_v05_schema import VCPValidator

# Upgrade v0.3 message to v0.5
validator = VCPValidator()
v05_message = validator.upgrade_from_v03(v03_data)
```

### Manual Migration

#### 1. Update Version Declaration
```python
# Before (v0.3)
{
  "vcp_version": "0.3",
  ...
}

# After (v0.5)
{
  "vcp_version": "0.5",
  ...
}
```

#### 2. Add Required v0.5 Fields
```python
# Add to vcp_payload
"consent": {
  "consent_id": "consent_" + call_id,
  "status": "granted",
  "scope": ["recording", "analytics"],
  "version": "1.0"
},
"provenance": {
  "source_system": provider_name + "_webhook_api",
  "created_at": now_iso_string,
  "transformation_history": ["upgraded_from_v0.3"]
}
```

#### 3. Enhance Capabilities (Optional)
```python
# Before (v0.3) - simple strings
"capabilities_invoked": ["book_appointment"]

# After (v0.5) - rich objects (backward compatible)
"capabilities_invoked": [
  {
    "capability_id": "book_appointment",
    "capability_type": "tool_call",
    "invoked_at": "2025-10-14T14:30:00Z",
    "duration_ms": 2300,
    "success": true,
    "metadata": {"appointment_type": "consultation"}
  }
]
```

### Breaking Changes

#### ⚠️ **None for v0.3 Users**
VCP v0.5 maintains full backward compatibility with v0.3. All existing v0.3 messages will validate and process correctly.

#### ⚠️ **v0.4 Deprecation**
The incomplete v0.4 implementation is deprecated. Any systems using v0.4 should migrate to v0.5 immediately.

## Provider Integration Updates

### Webhook Mapping
Provider webhook mappings now generate v0.5-compliant VCP messages:

```python
# Updated VCPMapper generates v0.5 structure
vcp_mapper = VCPMapper(registry)
vcp_message = vcp_mapper.map_to_vcp("retell", webhook_payload)
# Returns v0.5 structure with full provenance, consent, and enhanced fields
```

### Example Provider Integration

```python
# Retell webhook → VCP v0.5
retell_webhook = {
  "event": "call_ended",
  "call": {
    "call_id": "retell_123",
    "transcript": "Hello, how can I help?",
    # ... other fields
  }
}

# Maps to comprehensive v0.5 structure
vcp_result = {
  "vcp_version": "0.5",
  "vcp_payload": {
    "call": {
      "call_id": "retell_123",
      "session_id": "sess_retell_retell_12", 
      "provider": "retell",
      # ... enhanced call data
    },
    "consent": { ... },
    "provenance": { 
      "source_system": "retell_webhook_api",
      "transformation_history": ["received_from_retell_webhook", "mapped_to_vcp_v0.5"]
    },
    # ... all other v0.5 fields
  }
}
```

## Validation & Testing

### Schema Validation
```python
from vcp_v05_schema import VCPValidator, VCPMessage

validator = VCPValidator()
message = VCPMessage(**your_data)
results = validator.validate_v05(message)

if results["errors"]:
    print(f"Validation errors: {results['errors']}")
if results["warnings"]:
    print(f"Validation warnings: {results['warnings']}")
```

### Compatibility Testing
```python
# Test v0.3 compatibility
v03_compatible = message.to_v03_compatible()
print(f"v0.3 compatible size: {len(json.dumps(v03_compatible))} bytes")

# Test checksum integrity
checksum = message.compute_checksum()
print(f"Message checksum: {checksum}")
```

## Governance for v1.0

### Version Lock Promise
When VCP reaches v1.0, we commit to:

1. **Schema Stability**: No breaking changes to v1.0 structure
2. **Backward Compatibility**: v1.0 systems must support v0.3, v0.5 messages
3. **Controlled Evolution**: Major changes require community RFC process
4. **LTS Support**: Long-term support for v1.0 with security updates

### v1.0 Roadmap
Planned v1.0 additions:
- **Real-time Streaming**: Live VCP updates during calls
- **Multi-modal Support**: Video, screen sharing context
- **Advanced Analytics**: ML-driven insights and predictions
- **Compliance Automation**: Automated GDPR, CCPA compliance
- **Integration Ecosystem**: Standard connectors for major platforms

### Community Process
Starting with v1.0, changes will follow:
1. **RFC Process**: Formal proposal and community review
2. **Reference Implementation**: Working code before specification
3. **Testing Suite**: Comprehensive validation and compatibility tests
4. **Migration Tools**: Automated upgrade utilities
5. **Documentation**: Complete guides and examples

## Implementation Timeline

- **✅ v0.5 Release**: October 2025 - Comprehensive schema
- **🔄 v0.6-v0.9**: Q1-Q3 2026 - Community feedback integration
- **🎯 v1.0 Target**: Q4 2026 - Production-locked specification

## Support & Resources

### Development Tools
- **Schema Library**: `vcp_v05_schema.py` with full validation
- **Provider Mappings**: Updated webhook transformations  
- **Operations Dashboard**: VoiceLens ops app with v0.5 support
- **Monitoring**: Change detection and health monitoring

### Documentation
- **Schema Reference**: Complete field documentation
- **Provider Guides**: Integration documentation per provider
- **Migration Tools**: Automated upgrade utilities
- **Best Practices**: Implementation guidelines

### Community
- **GitHub Issues**: Bug reports and feature requests
- **RFC Process**: Proposal and discussion forum  
- **Developer Discord**: Real-time community support
- **Monthly Calls**: Community sync and roadmap updates

---

**Migration Deadline**: v0.3 support continues indefinitely. v0.4 systems should migrate to v0.5 by December 2025.

**Questions?** Open an issue or join our developer community at [VoiceLens Discord](https://discord.gg/voicelens)