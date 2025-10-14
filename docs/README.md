# Voice Context Protocol (VCP) System - Complete Documentation

## Overview

The Voice Context Protocol (VCP) system is a comprehensive framework for normalizing, processing, and analyzing voice AI interactions across multiple providers. This documentation provides everything needed to understand, implement, and deploy VCP-compatible systems in any environment.

## Documentation Structure

This documentation is organized into several comprehensive guides that together provide complete coverage of the VCP system:

### 📚 Core Documentation

1. **[System Overview](./VCP_SYSTEM_OVERVIEW.md)** - High-level architecture, components, and features
2. **[Schema Specification](./VCP_SCHEMA_SPECIFICATION.md)** - Complete VCP v0.5 schema with validation rules
3. **[Provider Integration Guide](./PROVIDER_INTEGRATION_GUIDE.md)** - Webhook integration and mapping implementation
4. **[Deployment & Operations Guide](./DEPLOYMENT_OPERATIONS_GUIDE.md)** - Production deployment and monitoring

## Quick Start

### Understanding the VCP System

The VCP system consists of four main layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                    VCP System Architecture                      │
├─────────────────────────────────────────────────────────────────┤
│  Provider Layer    │  Normalization    │  Analytics Engine     │
│  ┌─────────────────┐│  ┌─────────────────┐│  ┌─────────────────┐│
│  │ Retell AI       ││  │ VCP v0.5 Schema ││  │ Performance     ││
│  │ Bland AI        ││  │ Field Mapping   ││  │ Success Rates   ││
│  │ Vapi            ││  │ Transformation  ││  │ Cost Analysis   ││
│  │ ElevenLabs      ││  │ Validation      ││  │ Business Impact ││
│  │ OpenAI Realtime ││  │                 ││  │                 ││
│  │ Assistable AI   ││  │                 ││  │                 ││
│  └─────────────────┘│  └─────────────────┘│  └─────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│            Monitoring & Alerting           │  Web Dashboard    │
│                                            │                   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features

- **Universal Schema**: VCP v0.5 provides comprehensive, version-compatible normalization
- **6+ Provider Support**: Pre-built integrations with major voice AI providers
- **Real-time Processing**: Millisecond webhook transformation and validation
- **Business Intelligence**: Advanced analytics with Assistable AI extractions
- **Monitoring**: Automated provider health checks and change detection
- **Developer-Friendly**: Complete REST API, interactive dashboard, extensive docs

## Implementation Guide

### 1. Choose Your Implementation Approach

#### Python Implementation (Reference)
The reference implementation is in Python with Flask:

```python
# From voicelens_ops_app.py
from provider_documentation import VoiceAIProviderRegistry, VCPMapper
from vcp_v05_schema import VCPMessage, VCPValidator

# Initialize system
registry = VoiceAIProviderRegistry()
mapper = VCPMapper(registry)
validator = VCPValidator()

@app.route('/webhook/<provider>', methods=['POST'])
def handle_webhook(provider: str):
    # Transform provider webhook to VCP
    vcp_message = mapper.map_to_vcp(provider, request.json)
    
    # Validate VCP schema
    validation = validator.validate_v05(vcp_message)
    
    # Process and store
    return jsonify({'success': True, 'validation': validation})
```

#### TypeScript/Node.js Implementation

```typescript
interface VCPMessage {
  vcp_version: "0.5";
  vcp_payload: VCPPayload;
  audit: Audit;
}

class VCPSystem {
  async processWebhook(provider: string, payload: any): Promise<VCPMessage> {
    // 1. Transform to VCP
    const vcpMessage = await this.mapper.mapToVCP(provider, payload);
    
    // 2. Validate
    const validation = this.validator.validate(vcpMessage);
    
    // 3. Store and analyze
    await this.store(vcpMessage);
    
    return vcpMessage;
  }
}
```

### 2. Core Components to Implement

#### A. VCP Schema (Required)
Implement the VCP v0.5 schema in your target language:

**Core Models:**
- `VCPMessage` (root container)
- `Call` (call information with channel/direction support)
- `ModelSelection` (AI model attribution)
- `Outcomes` (objective and perceived results)
- `HumanReadableContext` (summary for humans)
- `Artifacts` (references to recordings/transcripts)
- `Custom` (provider-specific data)
- `ConsentRecord` (consent tracking)
- `Provenance` (data lineage)
- `Audit` (processing metadata)

#### B. Provider Registry (Required)
Implement provider information management:

```python
# Provider configuration structure
@dataclass
class ProviderInfo:
    name: str
    company: str
    website: str
    docs_url: str
    api_base_url: str
    webhook_auth: WebhookAuthConfig
    supported_events: List[WebhookEventType]
    webhook_schemas: List[WebhookSchema]
    vcp_mapping_rules: Dict[str, str]  # provider_path -> vcp_path
```

#### C. VCP Mapping Engine (Required)
Core transformation logic:

```python
class VCPMapper:
    def map_to_vcp(self, provider_name: str, webhook_payload: dict) -> dict:
        # 1. Load provider configuration
        # 2. Apply field mappings
        # 3. Handle provider-specific transformations
        # 4. Build complete VCP structure with defaults
        # 5. Return validated VCP message
```

#### D. Validation System (Required)
Schema validation and business rules:

```python
class VCPValidator:
    def validate_v05(self, message: VCPMessage) -> Dict[str, List[str]]:
        # 1. Schema validation (pydantic/joi/etc.)
        # 2. Business logic validation
        # 3. Cross-field validation
        # 4. Return errors and warnings
```

### 3. Supported Providers

The system includes pre-built integrations for:

| Provider | Complexity | Key Features |
|----------|------------|--------------|
| **Retell AI** | Medium | Signature validation, direction mapping |
| **Vapi** | Medium | End-of-call reports, status conversion |
| **Assistable AI** | Advanced | AI extractions, business intelligence |
| **Bland AI** | Simple | Bearer token auth, basic mapping |
| **ElevenLabs** | Medium | HMAC validation, IP whitelisting |
| **OpenAI Realtime** | Medium | Real-time events, session tracking |

### 4. Channel & Direction Support

VCP v0.5 introduces comprehensive directional support:

```python
# Preferred approach
call = {
    "channel": "phone",      # Communication medium
    "direction": "inbound",  # Call direction
    "from_": "+1234567890",
    "to": "+1987654321"
}

# Legacy support (backward compatible)
call = {
    "channel": "inbound"  # Combined channel+direction
}
```

### 5. Provider-Specific Transformations

Each provider requires specific data transformations:

#### Vapi Status Mapping
```python
def convert_vapi_status(ended_reason: str) -> str:
    mapping = {
        "hangup": "success",           # Normal completion
        "timeout": "timeout",
        "error": "error",
        "completed": "success"
    }
    return mapping.get(ended_reason.lower(), "unknown")
```

#### Assistable AI Business Intelligence
```python
# Automatic extraction to business intelligence
extractions = {
    "customer_interest_level": "high",
    "budget_range": "$500-1000",
    "decision_maker": True,
    "purchase_timeline": "within_30_days"
}

# Automatically mapped to CRM/Sales systems
integrations = {
    "crm_system": {...},
    "sales_system": {...}
}
```

## Architecture Patterns

### Data Flow Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Raw Webhook   │───▶│   VCP Mapper    │───▶│  Validated VCP  │
│                 │    │                 │    │                 │
│ Provider Format │    │ • Field Mapping │    │ • Schema v0.5   │
│ • Retell        │    │ • Type Convert  │    │ • Validation    │
│ • Vapi          │    │ • Status Trans  │    │ • Enrichment    │
│ • Assistable    │    │ • Direction     │    │ • Provenance    │
│ • Bland         │    │ • Sentiment     │    │ • Audit Trail   │
│ • ElevenLabs    │    │ • Extractions   │    │                 │
│ • OpenAI        │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Storage &     │    │    Analytics    │    │   Monitoring    │
│   Archival      │    │    Engine       │    │   & Alerting    │
│                 │    │                 │    │                 │
│ • JSON Storage  │    │ • Performance   │    │ • Validation    │
│ • Searchable    │    │ • Success Rate  │    │ • Failures      │
│ • Timestamped   │    │ • Cost Analysis │    │ • Trends        │
│ • Compressed    │    │ • Business KPI  │    │ • Health Checks │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Database Design

```sql
-- Core VCP storage
CREATE TABLE vcp_messages (
    id UUID PRIMARY KEY,
    call_id VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    vcp_version VARCHAR(10) NOT NULL DEFAULT '0.5',
    raw_payload JSONB NOT NULL,
    
    -- Extracted fields for fast querying
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_sec INTEGER,
    channel VARCHAR(20),
    direction VARCHAR(10),
    status VARCHAR(20),
    user_satisfaction_score DECIMAL(3,2),
    cost_usd DECIMAL(10,4),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Development Workflow

### 1. Setup Development Environment

```bash
# Clone reference implementation
git clone https://github.com/prompted365/voicelens-scripts.git
cd voicelens-scripts

# Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run development server
python voicelens_ops_app.py
```

### 2. Test Provider Integrations

```bash
# Test webhook transformation
curl -X POST http://localhost:8080/api/webhook-test \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "retell",
    "payload": {
      "event": "call_ended",
      "call": {
        "call_id": "test_123",
        "direction": "inbound"
      }
    }
  }'
```

### 3. Validate VCP Output

Check that your implementation produces valid VCP v0.5 messages:

```python
from vcp_v05_schema import VCPValidator

validator = VCPValidator()
result = validator.validate_v05(your_vcp_message)

print("Validation:", result)
# Should show: {"errors": [], "warnings": []}
```

## Production Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Health check
curl http://localhost:8080/health
```

### Kubernetes Deployment

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Check status
kubectl get pods -n voicelens
```

### Environment Configuration

Key environment variables:

```bash
# Core configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8080
DATABASE_URL=postgresql://...

# Provider API keys
RETELL_API_KEY=your_key
VAPI_API_KEY=your_key
ASSISTABLE_API_KEY=your_key

# Webhook secrets
WEBHOOK_SECRET_RETELL=your_secret
WEBHOOK_SECRET_ELEVENLABS=your_secret

# Monitoring
MONITORING_ENABLED=true
CRON_SCHEDULE="0 */6 * * *"
```

## Advanced Features

### Business Intelligence Integration

The system automatically extracts business intelligence from Assistable AI calls:

```python
# Automatic mapping from AI extractions
webhook_data = {
    "extractions": {
        "customer_interest_level": "high",
        "budget_range": "$500-1000",
        "decision_maker": True,
        "purchase_timeline": "within_30_days"
    }
}

# Automatically becomes VCP business intelligence
vcp_integrations = {
    "crm_system": {
        "provider": "assistable_extractions",
        "lead_score": "high"
    },
    "sales_system": {
        "qualification_score": 0.85,
        "opportunity_data": {...}
    }
}
```

### Monitoring & Alerting

Automated monitoring system:

```python
# From monitor_provider_changes.py
class VoiceLensMonitoringSystem:
    async def run_monitoring_cycle(self):
        # 1. Check provider health
        # 2. Monitor documentation changes
        # 3. Check RSS feeds
        # 4. Store results and send alerts
```

### Analytics Dashboard

Real-time analytics with:
- Provider performance comparison
- Success rate tracking
- Cost analysis
- Business impact metrics
- Webhook testing interface

## Security Considerations

### Webhook Security

1. **IP Whitelisting**: Restrict webhook endpoints to known provider IPs
2. **Signature Validation**: Verify webhook signatures (HMAC, etc.)
3. **Rate Limiting**: Implement rate limiting for all endpoints
4. **Input Validation**: Validate all webhook payloads
5. **HTTPS Only**: Use TLS encryption for all communications

### Data Privacy

1. **Consent Tracking**: Built-in consent management
2. **Data Retention**: Configurable retention policies
3. **Anonymization**: Caller ID hashing and PII protection
4. **Compliance**: GDPR, CCPA compliance flags

## Performance Optimization

### Database Optimization

- Efficient indexing on frequently queried fields
- JSONB storage for flexible provider data
- Automated analytics aggregation
- Connection pooling

### Application Performance

- Redis caching for provider configurations
- Async webhook processing
- Connection pooling
- Rate limiting and request throttling

## Support & Community

### Getting Help

1. **Documentation**: Start with the comprehensive guides in this repository
2. **Examples**: Check the baseline examples and test data
3. **Code**: Review the reference implementation
4. **Issues**: Report bugs or request features via GitHub issues

### Contributing

The VCP system is designed to be extensible:

1. **New Providers**: Add provider configurations to the registry
2. **Schema Extensions**: Propose v0.6+ schema enhancements
3. **Language Implementations**: Create VCP implementations in other languages
4. **Integrations**: Build additional analytics or monitoring integrations

## Roadmap

### Current Version: v0.5
- ✅ Comprehensive schema with channel/direction support
- ✅ 6+ provider integrations
- ✅ Business intelligence extraction
- ✅ Monitoring and alerting
- ✅ Analytics dashboard

### Future Versions
- **v0.6**: Enhanced real-time processing
- **v0.7**: Machine learning integration
- **v0.8**: Advanced business intelligence
- **v1.0**: Enterprise features and governance

## License

This documentation and reference implementation are provided under the MIT License. See LICENSE file for details.

---

**Next Steps:** Choose the documentation section most relevant to your needs:
- **New to VCP?** Start with [System Overview](./VCP_SYSTEM_OVERVIEW.md)
- **Implementing VCP?** See [Schema Specification](./VCP_SCHEMA_SPECIFICATION.md)
- **Adding Providers?** Check [Provider Integration Guide](./PROVIDER_INTEGRATION_GUIDE.md)
- **Deploying to Production?** Review [Deployment & Operations Guide](./DEPLOYMENT_OPERATIONS_GUIDE.md)