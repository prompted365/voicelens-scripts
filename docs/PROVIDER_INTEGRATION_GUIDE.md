# Provider Integration & Mapping Implementation Guide

## Overview

This document provides comprehensive guidance for integrating voice AI providers into the VCP system, including webhook schemas, authentication methods, mapping rules, and transformation logic.

## Provider Integration Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                Provider Integration System                   │
├─────────────────────────────────────────────────────────────┤
│  Provider Registry  │  Webhook Handler  │  VCP Transformer │
│  ┌─────────────────┐│  ┌─────────────────┐│  ┌─────────────────┐│
│  │ Provider Info   ││  │ Authentication  ││  │ Field Mapping   ││
│  │ Schema Defs     ││  │ Validation      ││  │ Type Conversion ││
│  │ Auth Config     ││  │ Rate Limiting   ││  │ Status Transform││
│  │ Mapping Rules   ││  │ Error Handling  ││  │ Enrichment      ││
│  └─────────────────┘│  └─────────────────┘│  └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Provider Registry System

The provider registry is implemented in `provider_documentation.py`:

```python
class VoiceAIProviderRegistry:
    """Central registry for voice AI provider information"""
    
    def __init__(self):
        self.providers = self._initialize_providers()
    
    def _initialize_providers(self) -> Dict[str, ProviderInfo]:
        """Initialize provider database with research data"""
        return {
            "retell": self._create_retell_provider(),
            "bland": self._create_bland_provider(),
            "vapi": self._create_vapi_provider(),
            "elevenlabs": self._create_elevenlabs_provider(),
            "openai_realtime": self._create_openai_provider(),
            "assistable": self._create_assistable_provider()
        }
```

## Supported Providers

### 1. Retell AI Integration

**Overview**: Retell AI provides conversational voice AI with robust webhook support and signature validation.

#### Configuration

```python
@dataclass
class ProviderInfo:
    """Complete provider documentation"""
    name: str = "Retell AI"
    company: str = "Retell AI"
    website: str = "https://www.retellai.com"
    docs_url: str = "https://docs.retellai.com"
    api_base_url: str = "https://api.retellai.com"
    status_page: str = "https://status.retellai.com"
    changelog_url: str = "https://www.retellai.com/changelog"
```

#### Authentication

```python
webhook_auth = WebhookAuthConfig(
    method=AuthMethod.SIGNATURE_HEADER,
    header_name="x-retell-signature",
    secret_key_required=True,
    ip_addresses=["100.20.5.228"],
    validation_example="Retell.verify(payload, api_key, signature)"
)
```

#### Webhook Schema

```python
webhook_schemas = [
    WebhookSchema(
        event_type=WebhookEventType.CALL_ENDED,
        required_fields=[
            "event", "call.call_id", "call.from_number", 
            "call.to_number", "call.direction", "call.start_timestamp",
            "call.end_timestamp", "call.disconnection_reason"
        ],
        optional_fields=[
            "call.transcript", "call.transcript_object", 
            "call.metadata", "call.call_analysis"
        ],
        nested_objects={
            "call": ["call_id", "agent_id", "call_status", "transcript", "metadata"],
            "transcript_object": ["role", "content", "timestamp"]
        }
    )
]
```

#### VCP Mapping Rules

```python
vcp_mapping_rules = {
    "call.call_id": "call.call_id",
    "call.from_number": "call.from_",
    "call.to_number": "call.to",
    "call.direction": "call.direction",  # Uses new direction field
    "call.start_timestamp": "call.start_time",
    "call.end_timestamp": "call.end_time",
    "call.transcript": "artifacts.transcript",
    "event": "audit.event_type"
}
```

#### Example Webhook Payload

```json
{
  "event": "call_ended",
  "call": {
    "call_id": "Jabr9TXYYJHfvl6Syypi88rdAHYHmcq6",
    "from_number": "+12137771234",
    "to_number": "+12137771235",
    "direction": "inbound",
    "start_timestamp": 1714608475945,
    "end_timestamp": 1714608491736,
    "disconnection_reason": "user_hangup",
    "transcript": "Full conversation transcript...",
    "metadata": {}
  }
}
```

### 2. Vapi Integration

**Overview**: Vapi provides end-of-call reports with comprehensive conversation data.

#### Configuration

```python
"vapi": ProviderInfo(
    name="Vapi",
    company="Vapi",
    website="https://vapi.ai",
    docs_url="https://docs.vapi.ai",
    api_base_url="https://api.vapi.ai",
    status_page="https://status.vapi.ai"
)
```

#### Webhook Schema

```python
webhook_schemas = [
    WebhookSchema(
        event_type=WebhookEventType.END_OF_CALL_REPORT,
        required_fields=[
            "message.type", "message.call.id", 
            "message.endedReason", "message.artifact"
        ],
        optional_fields=[
            "message.artifact.transcript",
            "message.artifact.recording", 
            "message.artifact.messages"
        ],
        nested_objects={
            "message": ["type", "call", "endedReason", "artifact"],
            "call": ["id", "phoneNumber", "status"],
            "artifact": ["transcript", "recording", "messages"]
        }
    )
]
```

#### VCP Mapping with Status Conversion

```python
vcp_mapping_rules = {
    "message.call.id": "call.call_id",
    "message.endedReason": "outcomes.objective.status",  # Requires conversion
    "message.artifact.transcript": "artifacts.transcript",
    "message.artifact.recording": "artifacts.recording_url"
}

def _convert_vapi_ended_reason_to_status(self, ended_reason: str) -> str:
    """Convert Vapi endedReason to VCP outcome status"""
    reason = ended_reason.lower()
    
    if reason in ["completed", "success", "assistant_ended"]:
        return "success"
    elif reason in ["hangup", "user_hangup", "customer_hangup"]:
        return "success"  # Normal hangup is successful completion
    elif reason in ["timeout", "no_answer", "voicemail", "busy"]:
        return "timeout"
    elif reason in ["error", "failed", "connection_error", "technical_error"]:
        return "error"
    elif reason in ["transferred", "forwarded"]:
        return "partial"
    else:
        return "unknown"
```

### 3. Assistable AI Advanced Integration

**Overview**: Assistable AI provides the most sophisticated webhook integration with AI-powered extractions and business intelligence.

#### Configuration

```python
"assistable": ProviderInfo(
    name="Assistable AI",
    company="Assistable AI",
    website="https://assistable.ai",
    docs_url="https://docs.assistable.ai",
    api_base_url="https://api.assistable.ai",
    status_page="https://status.assistable.ai"
)
```

#### Authentication

```python
webhook_auth = WebhookAuthConfig(
    method=AuthMethod.API_KEY_HEADER,
    header_name="Authorization",
    secret_key_required=False  # Optional for some endpoints
)
```

#### Complex Webhook Schema

```python
webhook_schemas = [
    WebhookSchema(
        event_type=WebhookEventType.CALL_ENDED,
        required_fields=[
            "call_id", "call_type", "direction", "to", "from",
            "disconnection_reason", "call_completion", "assistant_task_completion",
            "call_time_ms", "call_time_seconds", "start_timestamp", "end_timestamp"
        ],
        optional_fields=[
            "args", "metadata", "contact_id", "user_sentiment", "call_summary",
            "call_completion_reason", "recording_url", "full_transcript",
            "added_to_wallet", "extractions"
        ],
        nested_objects={
            "args": ["contact_address_zip_code"],  # Dynamic - customizable per assistant
            "metadata": ["contact_id", "location_id"],  # Dynamic - customizable per assistant
            "extractions": []  # Completely dynamic - AI-extracted data
        }
    )
]
```

#### Advanced VCP Mapping

```python
vcp_mapping_rules = {
    "call_id": "call.call_id",
    "direction": "call.direction",
    "to": "call.to",
    "from": "call.from_",
    "start_timestamp": "call.start_time",
    "end_timestamp": "call.end_time",
    "call_time_seconds": "call.duration_sec",
    "full_transcript": "artifacts.transcript",
    "recording_url": "artifacts.recording_url",
    "call_summary": "hcr.summary",
    "user_sentiment": "outcomes.user_satisfaction_score",  # Requires conversion
    "call_completion": "outcomes.objective.metrics.task_completion",
    "assistant_task_completion": "outcomes.objective.metrics.assistant_success",
    "disconnection_reason": "outcomes.objective.status",
    "extractions": "custom.provider_specific.assistable.extractions",
    "args": "custom.provider_specific.assistable.call_args",
    "metadata": "custom.provider_specific.assistable.metadata",
    "contact_id": "call.caller_id",
    "call_type": "custom.provider_specific.assistable.call_type"
}
```

#### AI Extractions Integration

Assistable AI provides dynamic AI-powered extractions that are automatically mapped to business intelligence:

```python
def _build_integrations_data(self, provider_name: str, webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build integration data from webhook payload"""
    if provider_name != "assistable":
        return {}
    
    integrations = {}
    extractions = webhook_payload.get("extractions", {})
    
    if extractions:
        # Map CRM-like data from extractions
        if "customer_interest_level" in extractions or "lead_score" in extractions:
            integrations["crm_system"] = {
                "provider": "assistable_extractions",
                "lead_score": extractions.get("customer_interest_level", "unknown"),
                "contact_data": {
                    key: value for key, value in extractions.items()
                    if key.startswith(("contact_", "customer_", "lead_"))
                }
            }
        
        # Map scheduling data
        if "next_followup_date" in extractions or "appointment_" in str(extractions):
            integrations["calendar_system"] = {
                "provider": "assistable_scheduling",
                "next_action": extractions.get("next_followup_date"),
                "scheduling_data": {
                    key: value for key, value in extractions.items()
                    if any(term in key.lower() for term in ["appointment", "schedule", "meeting", "followup"])
                }
            }
        
        # Map sales/opportunity data
        sales_indicators = ["budget", "purchase", "product_interest", "decision_maker", "timeline"]
        sales_data = {
            key: value for key, value in extractions.items()
            if any(indicator in key.lower() for indicator in sales_indicators)
        }
        if sales_data:
            integrations["sales_system"] = {
                "provider": "assistable_sales_intelligence",
                "opportunity_data": sales_data,
                "qualification_score": self._calculate_qualification_score(sales_data)
            }
    
    return {"integrations": integrations} if integrations else {}
```

### 4. ElevenLabs Integration

**Overview**: ElevenLabs provides conversational AI with advanced HMAC-based webhook security.

#### Authentication

```python
webhook_auth = WebhookAuthConfig(
    method=AuthMethod.HMAC_SHA256,
    header_name="elevenlabs-signature",
    secret_key_required=True,
    ip_addresses=[
        "34.67.146.145", "34.59.11.47",    # US
        "35.204.38.71", "34.147.113.54",   # EU
        "35.185.187.110", "35.247.157.189" # Asia
    ],
    validation_example="hmac.compare_digest(signature, hmac_sha256(timestamp + payload))"
)
```

#### Webhook Validation

```python
def validate_webhook_signature(self, provider_name: str, payload: str, 
                             signature: str, secret: str = None) -> bool:
    """Validate webhook signature for a provider"""
    if provider_name == "elevenlabs":
        # ElevenLabs format: t=timestamp,v0=hash
        parts = signature.split(',')
        timestamp = parts[0].split('=')[1]
        hash_part = parts[1].split('=')[1]
        
        full_payload = f"{timestamp}.{payload}"
        calculated_hash = hmac.new(
            secret.encode('utf-8'),
            full_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(f'v0={calculated_hash}', f'v0={hash_part}')
    
    return False
```

### 5. OpenAI Realtime API Integration

**Overview**: OpenAI Realtime API integration for real-time voice conversations.

#### Configuration

```python
"openai_realtime": ProviderInfo(
    name="OpenAI Realtime API",
    company="OpenAI",
    website="https://platform.openai.com",
    docs_url="https://platform.openai.com/docs/guides/realtime",
    api_base_url="https://api.openai.com/v1/realtime",
    status_page="https://status.openai.com"
)
```

#### Event Types

```python
supported_events = [
    WebhookEventType.STATUS_UPDATE,
    WebhookEventType.CONVERSATION_UPDATE,
    WebhookEventType.TRANSCRIPT_UPDATE
]
```

### 6. Bland AI Integration

**Overview**: Bland AI provides straightforward voice AI with bearer token authentication.

#### Configuration

```python
"bland": ProviderInfo(
    name="Bland AI",
    company="Bland AI",
    website="https://www.bland.ai",
    docs_url="https://docs.bland.ai",
    api_base_url="https://api.bland.ai"
)
```

#### Simple Authentication

```python
webhook_auth = WebhookAuthConfig(
    method=AuthMethod.BEARER_TOKEN,
    header_name="Authorization",
    secret_key_required=False
)
```

## VCP Mapping Engine Implementation

### Core Mapping Class

The `VCPMapper` class handles all provider transformations:

```python
class VCPMapper:
    """Maps provider webhooks to VCP v0.5 format"""
    
    def __init__(self, registry: VoiceAIProviderRegistry):
        self.registry = registry
    
    def map_to_vcp(self, provider_name: str, webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Main transformation method"""
        provider = self.registry.get_provider(provider_name)
        if not provider or not provider.vcp_mapping_rules:
            return {}
        
        vcp_data = {}
        
        # Apply mapping rules
        for provider_path, vcp_path in provider.vcp_mapping_rules.items():
            value = self._get_nested_value(webhook_payload, provider_path)
            if value is not None:
                self._apply_transformation(provider_name, provider_path, vcp_path, value, vcp_data)
        
        # Build complete VCP structure
        return self._build_vcp_structure(provider_name, vcp_data, webhook_payload)
```

### Field Mapping Logic

```python
def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
    """Get value from nested dictionary using dot notation"""
    keys = path.split('.')
    value = data
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    
    return value

def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any):
    """Set value in nested dictionary using dot notation"""
    keys = path.split('.')
    current = data
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
```

### Transformation Logic

```python
def _apply_transformation(self, provider_name: str, provider_path: str, 
                         vcp_path: str, value: Any, vcp_data: Dict[str, Any]):
    """Apply provider-specific transformations"""
    
    if provider_name == "assistable":
        if provider_path == "user_sentiment":
            # Convert sentiment string to score
            sentiment_score = self._convert_sentiment_to_score(value)
            self._set_nested_value(vcp_data, vcp_path, sentiment_score)
        elif provider_path == "direction":
            # Direction maps to call.direction field directly
            self._set_nested_value(vcp_data, vcp_path, value)
            # Also set channel to phone for Assistable calls
            self._set_nested_value(vcp_data, "call.channel", "phone")
        elif provider_path == "disconnection_reason":
            # Convert disconnection reason to outcome status
            status = self._convert_disconnection_to_status(value)
            self._set_nested_value(vcp_data, vcp_path, status)
        else:
            self._set_nested_value(vcp_data, vcp_path, value)
    
    elif provider_name == "vapi" and provider_path == "message.endedReason":
        # Convert Vapi endedReason to VCP status
        status = self._convert_vapi_ended_reason_to_status(value)
        self._set_nested_value(vcp_data, vcp_path, status)
    
    elif provider_path.endswith(".direction") and vcp_path == "call.direction":
        # Handle direction field for any provider (Retell, etc.)
        self._set_nested_value(vcp_data, vcp_path, value)
        # Set default channel to phone for voice calls with direction
        self._set_nested_value(vcp_data, "call.channel", "phone")
    
    else:
        self._set_nested_value(vcp_data, vcp_path, value)
```

### VCP Structure Building

```python
def _build_vcp_structure(self, provider_name: str, vcp_data: Dict[str, Any], 
                        webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build complete VCP structure with defaults"""
    now = datetime.now(timezone.utc)
    call_id = self._get_nested_value(vcp_data, 'call.call_id') or str(uuid.uuid4())
    session_id = self._get_nested_value(vcp_data, 'call.session_id') or f"sess_{provider_name}_{call_id[:8]}"
    
    vcp_message = {
        "vcp_version": "0.5",
        "vcp_payload": {
            "call": {
                "call_id": call_id,
                "session_id": session_id,
                "provider": provider_name,
                "start_time": now.isoformat(),
                "end_time": now.isoformat(),
                "duration_sec": 0,
                "capabilities_invoked": [],
                **vcp_data.get('call', {})
            },
            "model_selection": {
                "policy_id": f"{provider_name}_default",
                "resolved_at": now.isoformat(),
                "roles": {}
            },
            "outcomes": {
                "perceived": [],
                "objective": {
                    "status": "unknown",
                    "scored_criteria": [],
                    "metrics": {}
                },
                "perception_gap": {
                    "gap_score": 0.0,
                    "gap_class": "aligned"
                },
                "model_outcome_attribution": {
                    "roles": {},
                    "kpis": {}
                },
                **vcp_data.get('outcomes', {})
            },
            "hcr": {
                "audience": "system",
                "headline": f"{provider_name} call processed",
                "outcome_status": "success",
                "key_points": [],
                "impact_metrics": {}
            },
            "artifacts": vcp_data.get('artifacts', {}),
            "custom": {
                "provider_specific": {
                    provider_name: self._build_provider_specific_data(provider_name, webhook_payload)
                },
                **self._build_integrations_data(provider_name, webhook_payload)
            },
            "consent": {
                "consent_id": f"consent_{call_id}",
                "status": "granted",  # Default assumption for operational webhooks
                "scope": ["recording", "analytics"],
                "version": "1.0"
            },
            "provenance": {
                "source_system": f"{provider_name}_webhook_api",
                "created_at": now.isoformat(),
                "created_by": f"{provider_name}_webhook_processor",
                "transformation_history": [
                    f"received_from_{provider_name}_webhook",
                    "mapped_to_vcp_v0.5"
                ],
                "data_retention_policy": "standard_30_days",
                "compliance_flags": []
            }
        },
        "audit": {
            "received_at": now.isoformat(),
            "schema_version": "0.5"
        }
    }
    
    return vcp_message
```

## Implementation in Different Languages

### TypeScript/Node.js Implementation

```typescript
interface ProviderInfo {
  name: string;
  company: string;
  website: string;
  docs_url: string;
  vcp_mapping_rules: Record<string, string>;
  webhook_auth?: WebhookAuthConfig;
}

class ProviderRegistry {
  private providers: Map<string, ProviderInfo> = new Map();
  
  constructor() {
    this.initializeProviders();
  }
  
  private initializeProviders() {
    this.providers.set("retell", {
      name: "Retell AI",
      company: "Retell AI",
      website: "https://www.retellai.com",
      docs_url: "https://docs.retellai.com",
      vcp_mapping_rules: {
        "call.call_id": "call.call_id",
        "call.direction": "call.direction",
        "call.start_timestamp": "call.start_time",
        "call.end_timestamp": "call.end_time",
        "call.transcript": "artifacts.transcript"
      }
    });
    
    // Add other providers...
  }
  
  getProvider(name: string): ProviderInfo | undefined {
    return this.providers.get(name.toLowerCase());
  }
}

class VCPMapper {
  constructor(private registry: ProviderRegistry) {}
  
  async mapToVCP(providerName: string, webhookPayload: any): Promise<VCPMessage> {
    const provider = this.registry.getProvider(providerName);
    if (!provider) {
      throw new Error(`Unknown provider: ${providerName}`);
    }
    
    const vcpData: any = {};
    
    // Apply mapping rules
    for (const [providerPath, vcpPath] of Object.entries(provider.vcp_mapping_rules)) {
      const value = this.getNestedValue(webhookPayload, providerPath);
      if (value !== null && value !== undefined) {
        this.setNestedValue(vcpData, vcpPath, value);
      }
    }
    
    // Build VCP structure
    return this.buildVCPMessage(providerName, vcpData, webhookPayload);
  }
  
  private getNestedValue(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => {
      return current && current[key] !== undefined ? current[key] : null;
    }, obj);
  }
  
  private setNestedValue(obj: any, path: string, value: any): void {
    const keys = path.split('.');
    const lastKey = keys.pop()!;
    const target = keys.reduce((current, key) => {
      return current[key] = current[key] || {};
    }, obj);
    target[lastKey] = value;
  }
}
```

### Python Flask Integration

```python
from flask import Flask, request, jsonify
from provider_documentation import VoiceAIProviderRegistry, VCPMapper
from vcp_v05_schema import VCPValidator

app = Flask(__name__)
registry = VoiceAIProviderRegistry()
mapper = VCPMapper(registry)
validator = VCPValidator()

@app.route('/webhook/<provider>', methods=['POST'])
def handle_webhook(provider: str):
    try:
        # 1. Validate provider
        provider_info = registry.get_provider(provider)
        if not provider_info:
            return jsonify({'error': f'Unknown provider: {provider}'}), 400
        
        # 2. Validate webhook signature (if required)
        if provider_info.webhook_auth and provider_info.webhook_auth.secret_key_required:
            signature = request.headers.get(provider_info.webhook_auth.header_name)
            if not signature or not registry.validate_webhook_signature(
                provider, request.get_data(as_text=True), signature
            ):
                return jsonify({'error': 'Invalid signature'}), 401
        
        # 3. Transform to VCP
        webhook_payload = request.get_json()
        vcp_message = mapper.map_to_vcp(provider, webhook_payload)
        
        # 4. Validate VCP schema
        validation_result = validator.validate_v05(vcp_message)
        
        # 5. Store and process (implement your storage logic here)
        # store_vcp_message(vcp_message)
        # process_analytics(vcp_message)
        
        return jsonify({
            'success': True,
            'validation': validation_result,
            'vcp_payload': vcp_message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)
```

## Testing and Validation

### Provider Integration Testing

```python
def test_provider_integration():
    """Test all provider integrations"""
    registry = VoiceAIProviderRegistry()
    mapper = VCPMapper(registry)
    
    test_cases = [
        {
            "provider": "retell",
            "webhook": {
                "event": "call_ended",
                "call": {
                    "call_id": "test_123",
                    "direction": "inbound",
                    "start_timestamp": 1714608475945,
                    "end_timestamp": 1714608491736
                }
            }
        },
        {
            "provider": "vapi",
            "webhook": {
                "message": {
                    "type": "end-of-call-report",
                    "call": {"id": "vapi_123"},
                    "endedReason": "hangup",
                    "artifact": {"transcript": "Hello world"}
                }
            }
        }
        # Add more test cases...
    ]
    
    for test_case in test_cases:
        try:
            result = mapper.map_to_vcp(test_case["provider"], test_case["webhook"])
            print(f"✅ {test_case['provider']} integration successful")
            
            # Validate VCP schema
            validator = VCPValidator()
            validation = validator.validate_v05(result)
            if validation["errors"]:
                print(f"❌ {test_case['provider']} validation errors: {validation['errors']}")
            else:
                print(f"✅ {test_case['provider']} VCP validation passed")
                
        except Exception as e:
            print(f"❌ {test_case['provider']} integration failed: {e}")
```

This comprehensive guide provides everything needed to integrate any voice AI provider into the VCP system, with detailed examples, authentication methods, and transformation logic for all supported providers.