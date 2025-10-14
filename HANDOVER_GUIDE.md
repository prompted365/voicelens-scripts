# VoiceLens Dataset Generation & Delivery Handover Guide

## Overview

This guide provides complete instructions for generating and delivering synthetic HVAC conversation datasets using the VoiceLens system. All processes have been tested and validated with a successful 1,800 conversation delivery achieving 100% success rate.

## Quick Start Commands

### Generate and Send 60-Day Dataset (1,800 conversations)
```bash
# 1. Generate dataset
python -m voicelens_seeder.cli generate conversations --count 1800 --start-days-ago 60 --out ./synthetic_60d_data --seed 42

# 2. Send to webhook
python send_large_batch.py ./synthetic_60d_data https://ogqwehdmnlvpdjxdqhkt.functions.supabase.co/vcp-webhook/a/voiceai4hvac/c/localhvac/s/YXjNgJgboxK2VTJt1uDQHJ
```

### Generate Other Time Periods
```bash
# 30 days (900 conversations)
python -m voicelens_seeder.cli generate conversations --count 900 --start-days-ago 30 --out ./synthetic_30d_data --seed 42

# 90 days (2,700 conversations) 
python -m voicelens_seeder.cli generate conversations --count 2700 --start-days-ago 90 --out ./synthetic_90d_data --seed 42

# Custom date range with specific provider
python -m voicelens_seeder.cli generate conversations --count 500 --start-days-ago 45 --provider retell --seed 100
```

## System Architecture

### Prerequisites
- Python 3.13+ with virtual environment
- VoiceLens CLI installed (`voicelens_seeder` module)
- Required packages: `aiohttp`, `aiofiles`, `tqdm`

### Project Structure
```
voicelens-scripts/
├── src/voicelens_seeder/           # CLI source code
├── synthetic_60d_data/             # Generated datasets
├── reports/                        # Analysis and quality reports
├── send_large_batch.py            # Async batch delivery tool
├── analyze_delivery.py            # Quality analysis tool
├── manifest.json                  # Complete dataset manifest
└── delivery.log                   # Delivery execution logs
```

## Webhook Configuration

### Endpoint Details
- **URL**: `https://ogqwehdmnlvpdjxdqhkt.functions.supabase.co/vcp-webhook/a/voiceai4hvac/c/localhvac/s/YXjNgJgboxK2VTJt1uDQHJ`
- **Method**: POST
- **Content-Type**: application/json
- **Expected Response**: HTTP 200 for success
- **Rate Limits**: Tested stable at 10 RPS, supports up to 15 RPS
- **Timeout**: 30 seconds per request

### Payload Format
Each conversation is sent as a VCP 0.3 compliant JSON object with structure:
```json
{
  "call_id": "uuid",
  "vcp_version": "0.3",
  "vcp_payload": {
    "call": { "provider": "retell|vapi|bland", "duration_sec": 130, ... },
    "outcomes": { "objective": {...}, "perceived": [...] },
    "custom": { "outcome_hint": "scenario_name", "synthetic": true }
  }
}
```

## Volume Guidelines

### Recommended Conversation Counts
| Time Period | Conversations | Avg/Day | Use Case |
|-------------|---------------|---------|----------|
| 30 days     | 900          | 30      | Quick testing |
| 60 days     | 1,800        | 30      | Standard dataset |
| 90 days     | 2,700        | 30      | Extended analysis |
| 120 days    | 3,600        | 30      | Long-term trends |

### Performance Expectations
- **Generation**: 40 conversations/second
- **Delivery**: 9-10 conversations/second  
- **60-day dataset**: ~5 minutes total (1 min generate + 3 min deliver)
- **Memory usage**: ~50MB for 1,800 conversations

## Scenario Distribution

The system generates 7 different HVAC scenarios with realistic distributions:

| Scenario | Weight | Description |
|----------|--------|-------------|
| scheduled_callback | ~20% | Follow-up appointments |
| spam_filtered | ~18% | Filtered unwanted calls |
| booked_service | ~17% | Successful service bookings |
| emergency_service | ~16% | Urgent HVAC issues |
| live_transfer | ~14% | Escalation to human agents |
| out_of_service_area | ~9% | Geographic limitations |
| quote_requested | ~5% | Price quotation requests |

## Quality Assurance Process

### Automatic Validation
After delivery, run quality analysis:
```bash
python analyze_delivery.py ./synthetic_60d_data
```

### Quality Metrics Tracked
- ✅ **Count Accuracy**: 100% delivery success rate
- ✅ **Scenario Diversity**: 7 distinct scenarios
- ✅ **Provider Balance**: Equal distribution across Retell/Vapi/Bland
- ✅ **HVAC Terminology**: 100% relevant content
- ✅ **PII Compliance**: Zero personal information
- ✅ **Temporal Distribution**: Realistic time patterns

### Expected Quality Score: 100/100 (Grade A)

## Delivery Configuration

### Standard Settings (Tested & Recommended)
```python
DeliveryConfig(
    webhook_url=WEBHOOK_URL,
    max_concurrent=8,        # Conservative concurrency
    rate_limit_rps=10.0,     # Requests per second
    retry_attempts=3,        # Auto-retry failed requests
    retry_backoff=2.0,       # Exponential backoff
    timeout=30.0             # Request timeout
)
```

### High-Volume Settings (For 5,000+ conversations)
```python
DeliveryConfig(
    max_concurrent=12,
    rate_limit_rps=15.0,
    retry_attempts=5,
    timeout=45.0
)
```

## Error Handling & Recovery

### Resume Interrupted Deliveries
The system automatically creates `delivery_progress.json` to track completed deliveries:
```bash
# If delivery is interrupted, simply re-run the same command
python send_large_batch.py ./synthetic_60d_data [WEBHOOK_URL]
# It will resume from where it left off
```

### Common Issues & Solutions

#### Generation Issues
```bash
# Module not found
source venv/bin/activate
pip install -e .

# Permission denied on output directory
mkdir -p ./output_directory
chmod 755 ./output_directory
```

#### Delivery Issues
```bash
# High error rate
# Reduce concurrency and rate limits in send_large_batch.py (lines 276-283)

# Webhook timeouts
# Increase timeout setting or check webhook health
curl -X POST [WEBHOOK_URL] -H "Content-Type: application/json" -d '{"test": true}'
```

## Customization Options

### Custom Seed for Different Data
```bash
# Each seed produces different synthetic conversations
python -m voicelens_seeder.cli generate conversations --seed 100  # Different dataset
python -m voicelens_seeder.cli generate conversations --seed 200  # Another variation
```

### Provider-Specific Generation
```bash
# Only Retell conversations
python -m voicelens_seeder.cli generate conversations --provider retell --count 600

# All providers (default)
python -m voicelens_seeder.cli generate conversations --provider all --count 1800
```

### VCP Mode Selection
```bash
# GTM mode (default) - Optimized for Go-To-Market scenarios
python -m voicelens_seeder.cli generate conversations --vcp-mode gtm

# Full mode - Complete VCP payload structure
python -m voicelens_seeder.cli generate conversations --vcp-mode full
```

## Monitoring & Logs

### Delivery Monitoring
- Real-time progress bar during delivery
- Automatic retry with exponential backoff
- Complete success/failure logging in `delivery.log`

### Log Files Generated
- `delivery.log` - Complete delivery execution log
- `reports/delivery_analysis.json` - Detailed quality analysis
- `reports/summary.json` - Executive summary statistics
- `reports/quality.md` - Human-readable quality report

## Future Enhancements

### Planned Improvements
1. **Conversation Transcripts**: Turn-by-turn dialogue generation
2. **Spanish Language Support**: Bilingual conversation scenarios  
3. **Customer Journey Tracking**: Link related conversations over time
4. **Geographic Distribution**: Regional HVAC service patterns
5. **Sentiment Analysis**: Customer satisfaction scoring

### Scalability Considerations
- Current system handles 10,000+ conversations/hour
- Webhook tested stable at 10 RPS, scalable to 15+ RPS
- For enterprise volumes (50,000+), consider parallel webhook endpoints

## Contact & Support

### Files for Reference
- `manifest.json` - Complete dataset documentation
- `reports/quality.md` - Quality assessment details
- `src/voicelens_seeder/cli.py` - CLI implementation
- `send_large_batch.py` - Delivery system source

### Reproducibility Commands
All operations are fully reproducible with the provided seeds and commands. Store the exact CLI versions and dependency versions for guaranteed reproducibility.

---

**Last Updated**: October 2025  
**Tested With**: 1,800 conversations, 100% success rate  
**Next Review**: After 10,000+ conversation deliveries