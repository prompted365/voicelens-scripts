# Voice Context Protocol (VCP) System Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [VCP Protocol Specification](#vcp-protocol-specification)
3. [Normalization & Mapping Architecture](#normalization--mapping-architecture)
4. [Provider Integration System](#provider-integration-system)
5. [Implementation Guide](#implementation-guide)
6. [Deployment & Operations](#deployment--operations)

## System Overview

The Voice Context Protocol (VCP) system is a comprehensive framework for normalizing, processing, and analyzing voice AI interactions across multiple providers. It provides a unified schema, mapping engine, monitoring capabilities, and analytics platform.

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    VCP System Architecture                      │
├─────────────────────────────────────────────────────────────────┤
│  Provider Webhooks  │  VCP Normalization  │  Analytics Engine  │
│  ┌─────────────────┐│  ┌─────────────────┐│  ┌─────────────────┐│
│  │ Retell AI       ││  │ Schema v0.5     ││  │ Performance     ││
│  │ Bland AI        ││  │ Validation      ││  │ Success Rates   ││
│  │ Vapi            ││  │ Transformation  ││  │ Cost Analysis   ││
│  │ ElevenLabs      ││  │ Standardization ││  │ Business Impact ││
│  │ OpenAI Realtime ││  │                 ││  │                 ││
│  │ Assistable AI   ││  │                 ││  │                 ││
│  └─────────────────┘│  └─────────────────┘│  └─────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│            Monitoring & Alerting           │  Web Dashboard    │
│  ┌─────────────────────────────────────────┐│  ┌─────────────────┐│
│  │ Provider Health Checks                  ││  │ Real-time Stats ││
│  │ Documentation Changes                   ││  │ Provider Cards  ││
│  │ RSS Feed Monitoring                     ││  │ Webhook Testing ││
│  │ Endpoint Status Tracking                ││  │ Analytics Viz   ││
│  └─────────────────────────────────────────┘│  └─────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Key Features

- **Universal Schema**: VCP v0.5 provides a comprehensive, version-compatible schema for all voice AI interactions
- **Provider Agnostic**: Supports 6+ major voice AI providers with extensible architecture
- **Real-time Processing**: Handles webhook transformations in milliseconds
- **Comprehensive Analytics**: Business impact metrics, performance tracking, and cost analysis
- **Automated Monitoring**: Provider health checks, documentation change detection, and alerting
- **Developer-Friendly**: Full REST API, interactive dashboard, and extensive documentation

## VCP Protocol Specification

### Schema Evolution

The Voice Context Protocol has evolved through multiple versions to provide comprehensive coverage of voice AI interactions:

- **v0.3**: Foundation schema with basic call information and outcomes
- **v0.4**: Added provenance, consent tracking, and enhanced business metrics
- **v0.5**: Current version with full channel direction support, comprehensive model attribution, and business impact tracking

### VCP v0.5 Schema Structure

```python
# Core Schema Components from vcp_v05_schema.py

class VCPMessage(BaseModel):
    """Complete VCP v0.5 message structure"""
    vcp_version: VCPVersion = Field(VCPVersion.V05, description="VCP schema version")
    vcp_payload: VCPPayload = Field(..., description="Main VCP payload")
    audit: Audit = Field(..., description="Audit information")

class VCPPayload(BaseModel):
    """The main VCP payload structure"""
    call: Call                              # Enhanced call information
    model_selection: ModelSelection         # AI model selection details
    outcomes: Outcomes                      # Call outcomes and assessments
    hcr: HumanReadableContext              # Human-readable summary
    artifacts: Artifacts                    # Recording and transcript references
    custom: Custom                          # Provider-specific data
    consent: Optional[ConsentRecord]        # User consent tracking
    provenance: Provenance                  # Data lineage information
```

### Channel & Direction Support

VCP v0.5 introduces comprehensive support for call directionality:

```python
class ChannelType(str, Enum):
    """Communication channel types"""
    PHONE = "phone"
    WEB = "web"
    MOBILE = "mobile"
    EMBED = "embed"
    API = "api"
    WEBSOCKET = "websocket"
    # Directional channels (for backward compatibility)
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class CallDirection(str, Enum):
    """Call direction types (preferred approach for v0.5+)"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class Call(BaseModel):
    """Enhanced call information with v0.5 extensions"""
    # Core fields
    call_id: str
    session_id: str
    provider: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_sec: Optional[int]
    
    # v0.5 Extensions
    channel: Optional[ChannelType]          # Communication medium
    direction: Optional[CallDirection]       # Call direction
    from_: Optional[str]                    # Originating identifier
    to: Optional[str]                       # Destination identifier
    capabilities_invoked: List[Union[str, CapabilityInvocation]]
```

### Outcome Status Support

The system supports comprehensive outcome tracking:

```python
class OutcomeStatus(str, Enum):
    """Call outcome status"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    ERROR = "error"
    UNKNOWN = "unknown"    # Added in latest version
```

## Normalization & Mapping Architecture

### VCP Mapping Engine

The core normalization system is implemented in `provider_documentation.py` with the `VCPMapper` class:

```python
class VCPMapper:
    """Maps provider webhooks to VCP v0.5 format"""
    
    def map_to_vcp(self, provider_name: str, webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Main transformation method"""
        # 1. Load provider mapping rules
        provider = self.registry.get_provider(provider_name)
        
        # 2. Apply field mappings
        for provider_path, vcp_path in provider.vcp_mapping_rules.items():
            value = self._get_nested_value(webhook_payload, provider_path)
            if value is not None:
                # 3. Apply provider-specific transformations
                transformed_value = self._apply_provider_transformations(
                    provider_name, provider_path, value, vcp_path
                )
                self._set_nested_value(vcp_data, vcp_path, transformed_value)
        
        # 4. Build complete VCP structure with defaults
        return self._build_vcp_structure(provider_name, vcp_data, webhook_payload)
```

### Provider-Specific Transformations

Each provider requires specific data transformations:

#### Retell AI Mapping
```python
# From provider_documentation.py - Retell configuration
"retell": ProviderInfo(
    name="Retell AI",
    vcp_mapping_rules={
        "call.call_id": "call.call_id",
        "call.from_number": "call.from_",
        "call.to_number": "call.to",
        "call.direction": "call.direction",      # Maps to direction field
        "call.start_timestamp": "call.start_time",
        "call.end_timestamp": "call.end_time",
        "call.transcript": "artifacts.transcript",
    }
)
```

#### Vapi Mapping with Status Conversion
```python
# Vapi requires endedReason to VCP status conversion
"vapi": ProviderInfo(
    name="Vapi",
    vcp_mapping_rules={
        "message.call.id": "call.call_id",
        "message.endedReason": "outcomes.objective.status",  # Requires conversion
        "message.artifact.transcript": "artifacts.transcript",
    }
)

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

#### Assistable AI Advanced Mapping
```python
# Assistable AI has the most complex mapping with extractions
"assistable": ProviderInfo(
    vcp_mapping_rules={
        "call_id": "call.call_id",
        "direction": "call.direction",
        "to": "call.to",
        "from": "call.from_",
        "user_sentiment": "outcomes.user_satisfaction_score",
        "extractions": "custom.provider_specific.assistable.extractions",
        "call_completion": "outcomes.objective.metrics.task_completion",
    }
)

def _convert_sentiment_to_score(self, sentiment: str) -> float:
    """Convert Assistable.ai sentiment string to numerical score"""
    sentiment_mapping = {
        "very_positive": 1.0,
        "positive": 0.8,
        "slightly_positive": 0.6,
        "neutral": 0.5,
        "slightly_negative": 0.4,
        "negative": 0.2,
        "very_negative": 0.0
    }
    return sentiment_mapping.get(sentiment.lower(), 0.5)
```

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

## Provider Integration System

### Supported Providers

The system currently supports 6 major voice AI providers, each with comprehensive webhook schemas and mapping rules:

#### 1. Retell AI
```python
# Webhook Schema
webhook_schemas=[
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
        ]
    )
]

# Authentication
webhook_auth=WebhookAuthConfig(
    method=AuthMethod.SIGNATURE_HEADER,
    header_name="x-retell-signature",
    secret_key_required=True,
    ip_addresses=["100.20.5.228"]
)
```

#### 2. Assistable AI (Advanced Integration)
```python
# Complex webhook with extractions and business intelligence
webhook_schemas=[
    WebhookSchema(
        event_type=WebhookEventType.CALL_ENDED,
        required_fields=[
            "call_id", "call_type", "direction", "to", "from",
            "disconnection_reason", "call_completion", "assistant_task_completion"
        ],
        optional_fields=[
            "user_sentiment", "call_summary", "recording_url", "full_transcript",
            "extractions"  # AI-extracted business data
        ],
        nested_objects={
            "extractions": []  # Completely dynamic - AI-extracted data
        }
    )
]

# Example extracted business intelligence
example_extractions = {
    "contact_zip_code": "90210",
    "customer_interest_level": "high",
    "next_followup_date": "2025-10-21",
    "product_interest": "premium_package",
    "budget_range": "$500-1000",
    "decision_maker": True,
    "purchase_timeline": "within_30_days"
}
```

### Provider Registry Architecture

```python
class VoiceAIProviderRegistry:
    """Central registry for voice AI provider information"""
    
    def __init__(self):
        self.providers = self._initialize_providers()
    
    def get_provider(self, provider_name: str) -> Optional[ProviderInfo]:
        """Get provider information by name"""
        return self.providers.get(provider_name.lower())
    
    def get_providers_by_event(self, event_type: WebhookEventType) -> List[ProviderInfo]:
        """Get providers that support a specific event type"""
        return [
            provider for provider in self.providers.values()
            if provider.supported_events and event_type in provider.supported_events
        ]
```

## Implementation Guide

### Core Implementation Steps

#### 1. VCP Schema Implementation

Start by implementing the VCP v0.5 schema in your target language. The Python reference implementation is in `vcp_v05_schema.py`:

```python
# Required models for any implementation
- VCPMessage (root)
- VCPPayload (main content)
- Call (call information)
- ModelSelection (AI model details)
- Outcomes (call results)
- HumanReadableContext (summary)
- Artifacts (references)
- Custom (provider-specific)
- ConsentRecord (consent tracking)
- Provenance (data lineage)
- Audit (processing info)
```

For TypeScript/React implementation:

```typescript
// TypeScript equivalent interfaces
interface VCPMessage {
  vcp_version: "0.5";
  vcp_payload: VCPPayload;
  audit: Audit;
}

interface Call {
  call_id: string;
  session_id: string;
  provider: string;
  start_time: string;  // ISO datetime
  end_time?: string;
  duration_sec?: number;
  channel?: ChannelType;
  direction?: CallDirection;
  from_?: string;
  to?: string;
  capabilities_invoked: (string | CapabilityInvocation)[];
}

type ChannelType = "phone" | "web" | "mobile" | "embed" | "api" | "websocket" | "inbound" | "outbound";
type CallDirection = "inbound" | "outbound";
type OutcomeStatus = "success" | "failure" | "partial" | "timeout" | "error" | "unknown";
```

#### 2. Provider Integration Layer

Implement a provider registry and mapping system:

```typescript
// TypeScript implementation approach
class ProviderRegistry {
  private providers: Map<string, ProviderInfo> = new Map();
  
  constructor() {
    this.initializeProviders();
  }
  
  private initializeProviders() {
    // Add provider configurations
    this.providers.set("retell", {
      name: "Retell AI",
      vcp_mapping_rules: {
        "call.call_id": "call.call_id",
        "call.direction": "call.direction",
        // ... mapping rules
      }
    });
  }
}

class VCPMapper {
  constructor(private registry: ProviderRegistry) {}
  
  async mapToVCP(providerName: string, webhookPayload: any): Promise<VCPMessage> {
    const provider = this.registry.getProvider(providerName);
    if (!provider) throw new Error(`Unknown provider: ${providerName}`);
    
    // Apply mapping rules
    const vcpData = this.applyMappingRules(provider, webhookPayload);
    
    // Build complete VCP structure
    return this.buildVCPMessage(providerName, vcpData, webhookPayload);
  }
}
```

#### 3. Webhook Processing Pipeline

```typescript
// Express.js/Node.js implementation example
import express from 'express';
import { VCPMapper } from './vcp-mapper';
import { validateVCPMessage } from './vcp-validator';

const app = express();
const mapper = new VCPMapper(new ProviderRegistry());

app.post('/webhook/:provider', async (req, res) => {
  const { provider } = req.params;
  const webhookPayload = req.body;
  
  try {
    // 1. Transform to VCP
    const vcpMessage = await mapper.mapToVCP(provider, webhookPayload);
    
    // 2. Validate schema
    const validation = validateVCPMessage(vcpMessage);
    if (validation.errors.length > 0) {
      return res.status(400).json({ 
        success: false, 
        errors: validation.errors 
      });
    }
    
    // 3. Store and process
    await this.storeVCPMessage(vcpMessage);
    await this.processAnalytics(vcpMessage);
    
    res.json({ 
      success: true, 
      transformation_time_ms: Date.now() - startTime 
    });
    
  } catch (error) {
    res.status(500).json({ 
      success: false, 
      error: error.message 
    });
  }
});
```

#### 4. Analytics and Monitoring

Implement analytics processing for business insights:

```typescript
class AnalyticsEngine {
  async processVCPMessage(message: VCPMessage) {
    // Extract key metrics
    const metrics = {
      provider: message.vcp_payload.call.provider,
      duration_sec: message.vcp_payload.call.duration_sec,
      status: message.vcp_payload.outcomes.objective.status,
      cost_usd: this.extractCost(message),
      satisfaction_score: message.vcp_payload.outcomes.user_satisfaction_score,
      capabilities_used: message.vcp_payload.call.capabilities_invoked.length
    };
    
    // Update aggregated stats
    await this.updateProviderStats(metrics);
    await this.updateBusinessMetrics(metrics);
    await this.checkAlertConditions(metrics);
  }
  
  private extractCost(message: VCPMessage): number {
    // Extract cost from model attribution or custom data
    return message.vcp_payload.outcomes.model_outcome_attribution.total_cost_usd || 0;
  }
}
```

### Database Schema Recommendations

For storing VCP messages and analytics:

```sql
-- VCP Messages Table
CREATE TABLE vcp_messages (
    id UUID PRIMARY KEY,
    call_id VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    vcp_version VARCHAR(10) NOT NULL,
    raw_payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexed fields for fast querying
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_sec INTEGER,
    channel VARCHAR(20),
    direction VARCHAR(10),
    status VARCHAR(20),
    
    INDEX idx_provider_created (provider, created_at),
    INDEX idx_call_id (call_id),
    INDEX idx_status (status),
    INDEX idx_timerange (start_time, end_time)
);

-- Analytics Aggregations
CREATE TABLE provider_analytics (
    id UUID PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    total_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    failed_calls INTEGER DEFAULT 0,
    avg_duration_sec DECIMAL(10,2),
    total_cost_usd DECIMAL(10,2),
    avg_satisfaction_score DECIMAL(3,2),
    
    UNIQUE(provider, date)
);
```

## Deployment & Operations

### Environment Configuration

The system supports multiple deployment modes via environment variables:

```bash
# Core Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8080

# Provider API Keys (stored securely)
RETELL_API_KEY=your_retell_key
VAPI_API_KEY=your_vapi_key
ASSISTABLE_API_KEY=your_assistable_key

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/voicelens
REDIS_URL=redis://localhost:6379

# Monitoring Configuration
MONITORING_ENABLED=true
CRON_SCHEDULE="0 */6 * * *"  # Every 6 hours

# Webhook Security
WEBHOOK_SECRET_RETELL=your_retell_webhook_secret
WEBHOOK_SECRET_ELEVENLABS=your_elevenlabs_webhook_secret
```

### Docker Deployment

```dockerfile
# Production Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set up monitoring cron
RUN chmod +x scripts/setup_monitoring_cron.sh
RUN ./scripts/setup_monitoring_cron.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run application
EXPOSE 8080
CMD ["python", "voicelens_ops_app.py"]
```

### Monitoring and Alerting

The system includes comprehensive monitoring capabilities:

```python
# From monitor_provider_changes.py
class VoiceLensMonitoringSystem:
    """Automated monitoring system for provider changes"""
    
    async def run_monitoring_cycle(self):
        """Complete monitoring cycle"""
        changes = []
        
        # 1. Check provider health
        health_changes = await self.check_provider_health()
        changes.extend(health_changes)
        
        # 2. Monitor documentation
        doc_changes = await self.monitor_documentation_changes()
        changes.extend(doc_changes)
        
        # 3. Check RSS feeds
        feed_changes = await self.check_rss_feeds()
        changes.extend(feed_changes)
        
        # 4. Store results
        if changes:
            await self.store_changes(changes)
            await self.send_alerts(changes)
        
        return changes
```

### Performance Optimization

Key performance considerations for large-scale deployment:

#### 1. Webhook Processing
- Implement async processing for webhook transformations
- Use connection pooling for database operations
- Cache provider configurations in memory
- Implement request rate limiting

#### 2. Analytics Performance
- Use time-series databases for metrics storage
- Pre-aggregate common analytics queries
- Implement efficient indexing strategies
- Use caching for frequently accessed data

#### 3. Monitoring Efficiency
- Batch provider health checks
- Use differential monitoring (only check changed content)
- Implement exponential backoff for failed requests
- Cache provider documentation locally

### Scaling Considerations

For high-volume deployments:

```yaml
# Kubernetes deployment example
apiVersion: apps/v1
kind: Deployment
metadata:
  name: voicelens-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: voicelens-api
  template:
    spec:
      containers:
      - name: api
        image: voicelens/api:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: voicelens-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: voicelens-service
spec:
  selector:
    app: voicelens-api
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

This comprehensive documentation provides everything needed to understand, implement, and deploy the VCP system in any environment. The modular architecture, detailed implementation guides, and extensive code examples enable development teams to build compatible systems in their preferred technology stack.