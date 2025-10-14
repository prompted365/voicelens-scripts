# VoiceLens Scripts

VoiceLens provider documentation and monitoring scripts for voice AI webhook management.

## Overview

This repository contains the comprehensive VoiceLens system for managing voice AI providers and implementing the Voice Context Protocol (VCP) v0.5. It provides unified webhook processing, provider monitoring, and operational management tools for voice AI integrations.

### Key Components

- **🔧 VCP v0.5 Schema** (`vcp_v05_schema.py`): Complete Voice Context Protocol implementation with validation, backward compatibility, and migration tools
- **📚 Provider Documentation** (`provider_documentation.py`): Webhook mappings and documentation for major voice AI providers (Retell, Bland, Vapi, ElevenLabs, OpenAI)  
- **📊 Provider Monitoring** (`provider_monitoring.py`): Change detection and health monitoring system with automated alerts
- **🎛️ Operations Dashboard** (`voicelens_ops_app.py`): Web-based management interface for testing, monitoring, and analytics

### Voice Context Protocol (VCP) v0.5

VCP v0.5 is the comprehensive voice AI interaction schema that extends the real v0.3 production structure with advanced features:

- **Session Correlation**: Hierarchical session tracking and cross-system correlation
- **Enhanced Capabilities**: Rich capability tracking with timing, success metrics, and metadata
- **Consent Management**: GDPR/CCPA compliant user consent tracking
- **Data Provenance**: Complete data lineage and transformation history
- **Business Impact**: Revenue attribution, user satisfaction, and conversion tracking
- **Backward Compatibility**: Full v0.3 compatibility with automatic upgrade tools

## Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd voicelens-scripts

# Set up Python environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Test VCP v0.5 schema
python vcp_v05_schema.py

# Test provider webhook mapping
python provider_documentation.py

# Run operations dashboard
python voicelens_ops_app.py
# Access at http://localhost:5000

# Start provider monitoring
python provider_monitoring.py --daemon
```

## Core Features

### 1. Voice Context Protocol (VCP) v0.5

Complete implementation of the Voice Context Protocol with comprehensive validation:

```python
from vcp_v05_schema import VCPValidator, VCPMessage, create_example_v05_message

# Create and validate VCP message
example = create_example_v05_message()
validator = VCPValidator()
results = validator.validate_v05(example)

# Upgrade from v0.3
v05_message = validator.upgrade_from_v03(v03_data)

# Convert to v0.3 compatibility  
v03_compatible = example.to_v03_compatible()
```

### 2. Provider Webhook Integration

Unified webhook processing for major voice AI providers:

```python
from provider_documentation import VoiceAIProviderRegistry, VCPMapper

# Map webhook to VCP
registry = VoiceAIProviderRegistry()
mapper = VCPMapper(registry)

vcp_result = mapper.map_to_vcp("retell", webhook_payload)
# Returns standardized VCP v0.5 structure
```

**Supported Providers:**
- **Retell AI**: Complete webhook and authentication support
- **Bland AI**: Post-call transcription and analysis webhooks
- **Vapi**: End-of-call reports and status updates
- **ElevenLabs**: Voice synthesis completion webhooks
- **OpenAI Realtime API**: Conversation and status updates

### 3. Provider Monitoring System

Automated monitoring with change detection and health checks:

```python
from provider_monitoring import VoiceLensMonitoringSystem

# Initialize monitoring
monitor = VoiceLensMonitoringSystem()

# Run monitoring cycle
monitor.run_monitoring_cycle()

# Check recent changes
changes = monitor.get_recent_changes(hours=24)

# Health status
health = monitor.check_provider_health("retell")
```

**Monitoring Features:**
- Documentation change detection
- API health monitoring
- RSS feed monitoring for changelogs
- Slack/email notifications
- Historical change tracking

### 4. Operations Dashboard

Web-based management interface with comprehensive tools:

- **Provider Management**: View and compare all voice AI providers
- **Webhook Testing**: Test webhook transformations in real-time
- **VCP Validation**: Validate and transform VCP messages
- **Analytics**: Performance metrics and success rates
- **Change Monitoring**: Real-time provider change notifications

## Advanced Usage

### Custom Provider Integration

Add support for new voice AI providers:

```python
from provider_documentation import ProviderInfo, WebhookAuthConfig, WebhookSchema
from provider_documentation import AuthMethod, WebhookEventType

# Define provider
new_provider = ProviderInfo(
    name="New Voice AI",
    company="New Voice AI Inc",
    website="https://newvoiceai.com",
    docs_url="https://docs.newvoiceai.com",
    api_base_url="https://api.newvoiceai.com",
    webhook_auth=WebhookAuthConfig(
        method=AuthMethod.HMAC_SHA256,
        header_name="X-NewVoiceAI-Signature",
        secret_key_required=True
    ),
    supported_events=[WebhookEventType.CALL_ENDED],
    vcp_mapping_rules={
        "call_id": "call.call_id",
        "duration": "call.duration_sec",
        "transcript": "artifacts.transcript"
    }
)

# Register provider
registry.add_provider("newvoiceai", new_provider)
```

### Custom VCP Extensions

Extend VCP v0.5 for specific use cases:

```python
from vcp_v05_schema import VCPMessage, Custom

# Create custom VCP message
message = VCPMessage(
    vcp_version="0.5",
    vcp_payload=VCPPayload(
        # ... standard fields ...
        custom=Custom(
            integrations={
                "crm_system": {
                    "provider": "salesforce",
                    "contact_id": "003XX000000abc123",
                    "opportunity_created": True
                }
            },
            experimental={
                "sentiment_analysis": {
                    "overall_sentiment": 0.8,
                    "sentiment_trajectory": "improving"
                }
            }
        )
    ),
    audit=Audit(
        received_at=datetime.now(timezone.utc),
        schema_version="0.5"
    )
)
```

### Monitoring Configuration

Configure advanced monitoring with custom rules:

```python
from provider_monitoring import ChangeType, SeverityLevel

# Custom monitoring rules
monitor = VoiceLensMonitoringSystem()
monitor.add_monitoring_rule(
    provider="retell",
    url_pattern="https://docs.retellai.com/webhooks/*",
    change_types=[ChangeType.API_CHANGE, ChangeType.SCHEMA_CHANGE],
    severity=SeverityLevel.HIGH,
    notification_channels=["slack", "email"]
)

# Custom severity assessment
def assess_change_severity(change_event):
    if "breaking" in change_event.description.lower():
        return SeverityLevel.CRITICAL
    elif "webhook" in change_event.description.lower():
        return SeverityLevel.HIGH
    else:
        return SeverityLevel.MEDIUM
```

## Configuration

### Environment Variables

Create `.env` file:

```bash
# Database
DATABASE_URL=sqlite:///voicelens_ops.db
MONITORING_DATABASE=monitoring.db

# Notifications  
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_FROM=alerts@yourdomain.com

# Provider API Keys (optional)
RETELL_API_KEY=your-retell-key
BLAND_API_KEY=your-bland-key
VAPI_API_KEY=your-vapi-key
ELEVENLABS_API_KEY=your-elevenlabs-key
OPENAI_API_KEY=your-openai-key
```

### Advanced Configuration

Create `config.yaml` for production:

```yaml
monitoring:
  interval_minutes: 30
  providers:
    retell:
      enabled: true
      priority: high
    bland:
      enabled: true
      priority: medium

notifications:
  slack:
    channel: "#voice-ai-alerts"
    min_severity: medium
  email:
    recipients: ["ops@company.com"]
    min_severity: high

dashboard:
  host: "0.0.0.0"
  port: 5000
  features:
    webhook_testing: true
    analytics: true
```

## Deployment

### Production Deployment

```bash
# Install to system location
sudo mkdir -p /opt/voicelens
sudo cp -r . /opt/voicelens/

# Create systemd services
sudo systemctl enable voicelens-dashboard
sudo systemctl enable voicelens-monitoring
sudo systemctl start voicelens-dashboard voicelens-monitoring
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Scale services
docker-compose up -d --scale voicelens-dashboard=2
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment guides including systemd, Docker, Kubernetes, and cloud deployments.

## API Reference

### VCP v0.5 Schema API

```python
# Core Classes
VCPMessage          # Main VCP message structure
VCPPayload          # Core payload data
Call                # Enhanced call information
ModelSelection      # Model selection details
Outcomes            # Call outcomes and attribution
ConsentRecord       # User consent tracking
Provenance          # Data lineage information

# Validation
VCPValidator.validate_v05(message)
VCPValidator.upgrade_from_v03(v03_data)

# Utilities
message.compute_checksum()
message.to_v03_compatible()
```

### Provider Documentation API

```python
# Registry Management
registry = VoiceAIProviderRegistry()
provider = registry.get_provider("retell")
all_providers = registry.get_all_providers()

# Webhook Mapping
mapper = VCPMapper(registry)
vcp_result = mapper.map_to_vcp(provider_name, webhook_payload)

# Signature Validation
is_valid = registry.validate_webhook_signature(
    provider_name, payload, signature, secret
)
```

### Monitoring API

```python
# Monitoring System
monitor = VoiceLensMonitoringSystem()
monitor.run_monitoring_cycle()

# Change Detection
changes = monitor.get_recent_changes(hours=24)
health = monitor.check_provider_health(provider_name)

# Notifications
monitor.send_notification(change_event, channels=["slack"])
```

### Operations Dashboard API

RESTful API endpoints:

- `GET /api/providers` - List all providers
- `GET /api/providers/{name}` - Provider details
- `POST /api/webhook-test` - Test webhook transformation
- `GET /api/monitoring/changes` - Recent changes
- `GET /api/monitoring/health` - Service health status
- `GET /api/analytics/transformation-stats` - Performance analytics

## Migration from v0.3/v0.4

### Automatic Migration

```python
from vcp_v05_schema import VCPValidator

# Upgrade v0.3 to v0.5
validator = VCPValidator()
v05_message = validator.upgrade_from_v03(v03_data)
```

### Key Changes in v0.5

- **Enhanced Capabilities**: Rich capability tracking with metadata
- **Session Correlation**: Parent sessions and correlation IDs
- **Consent Management**: GDPR/CCPA compliance features
- **Data Provenance**: Complete transformation history
- **Business Metrics**: Revenue attribution and satisfaction scores
- **Backward Compatibility**: Full v0.3 compatibility maintained

See [VCP_V0.5_CHANGELOG.md](VCP_V0.5_CHANGELOG.md) for complete migration guide.

## Testing

```bash
# Run all tests
pytest

# Test specific components
python vcp_v05_schema.py
python provider_documentation.py
python provider_monitoring.py --test

# Validate webhook transformations
python -c "
from provider_documentation import VCPMapper, VoiceAIProviderRegistry
registry = VoiceAIProviderRegistry()
mapper = VCPMapper(registry)
result = mapper.map_to_vcp('retell', test_payload)
print('Mapping successful:', bool(result))
"
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Add tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open Pull Request

### Development Setup

```bash
# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest black flake8 pytest-cov

# Run code formatting
black .
flake8 .

# Run tests with coverage
pytest --cov=. --cov-report=html
```

## Changelog

### v0.5.0 (Current)
- ✅ Complete VCP v0.5 schema implementation
- ✅ Provider documentation for 5+ major providers
- ✅ Advanced monitoring with change detection
- ✅ Operations dashboard with analytics
- ✅ Full backward compatibility with v0.3
- ✅ Comprehensive deployment guides

### v0.4.0 (Deprecated)
- ⚠️ Incomplete stub implementation (migrated to v0.5)

### v0.3.0 (Legacy)
- ✅ Basic VCP schema (production baseline)
- ✅ Core provider integrations
- ✅ Basic webhook processing

## Support & Community

- **Documentation**: Complete guides in this repository
- **Issues**: [GitHub Issues](https://github.com/your-org/voicelens-scripts/issues)
- **Contact Information**: See [CONTACT-US.md](./CONTACT-US.md) for all contact methods and support options
- **Community Logistics**: See [LOGISTICS.md](./LOGISTICS.md) for planned community sync and meeting schedules

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Voice AI provider communities for webhook documentation
- VCP v0.3 production users for feedback and requirements
- Open source contributors and maintainers