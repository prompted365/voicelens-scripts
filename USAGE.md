# VoiceLens Scripts Usage Guide

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/prompted365/voicelens-scripts.git
cd voicelens-scripts
```

2. Create a virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

## Basic Usage

### Generate Baseline Examples

Generate the 8 baseline HVAC examples matching your original curl commands:

```bash
python -m voicelens_seeder.cli generate baseline
```

This creates 8 reproducible VCP 0.3 payloads in the `baseline_examples/` directory:

- `hvac_001_booked_service_retell.json` - After-hours AC repair booking
- `hvac_002_live_transfer_vapi.json` - Live transfer to dispatcher
- `hvac_003_scheduled_callback_bland.json` - Callback window scheduled
- `hvac_004_quote_requested_retell.json` - Furnace install quote
- `hvac_005_out_of_service_area_vapi.json` - Out of service area
- `hvac_006_spam_filtered_retell.json` - Spam/non-lead filtered
- `hvac_007_no_show_cancel_bland.json` - No-show/cancellation
- `hvac_008_emergency_service_retell.json` - Emergency heat out

### Generate Synthetic Conversations

Generate a larger dataset of synthetic conversations:

```bash
# Generate 50 conversations over the past 30 days
python -m voicelens_seeder.cli generate conversations --count 50

# Generate for a specific provider
python -m voicelens_seeder.cli generate conversations --count 25 --provider retell

# Generate with reproducible seed
python -m voicelens_seeder.cli generate conversations --count 100 --seed 12345

# Generate to a specific directory
python -m voicelens_seeder.cli generate conversations --count 20 --out ./my_data
```

## Advanced Usage

### Command Line Options

```bash
# Full conversation generation options
python -m voicelens_seeder.cli generate conversations \
  --count 200 \
  --provider all \
  --start-days-ago 60 \
  --vcp-mode gtm \
  --seed 42 \
  --out ./generated_data

# Baseline generation options  
python -m voicelens_seeder.cli generate baseline \
  --seed 42 \
  --out ./baseline_data
```

### Provider Options

- `retell` - Retell AI conversations only
- `vapi` - VAPI conversations only  
- `bland` - Bland AI conversations only
- `all` - Mix of all providers (default)

### VCP Mode Options

- `gtm` - Streamlined GTM mode (default)
- `full` - Complete VCP 0.3 compliance mode

## Programming Interface

### Using the Generator Directly

```python
from datetime import datetime, timezone, timedelta
from voicelens_seeder.generator.synthetic import VCPSyntheticGenerator
from voicelens_seeder.normalizers.vcp import Provider
from voicelens_seeder.generator.hvac_scenarios import HVACScenario

# Initialize generator
generator = VCPSyntheticGenerator(seed=42)

# Generate baseline examples
baseline = generator.generate_baseline_examples()
print(f"Generated {len(baseline)} baseline examples")

# Generate time series data
end_time = datetime.now(timezone.utc)
start_time = end_time - timedelta(days=7)

calls = list(generator.generate_call_batch(
    count=100,
    start_date=start_time,
    end_date=end_time,
    providers=[Provider.RETELL, Provider.VAPI]
))

# Save as JSON files
from pathlib import Path
output_dir = Path("./my_synthetic_data")
generator.save_examples_as_json(calls, output_dir)

# Access individual payloads
for call in calls:
    print(f"Call ID: {call.call_id}")
    print(f"Provider: {call.vcp_payload.call.provider}")
    print(f"Scenario: {call.vcp_payload.custom.outcome_hint}")
    print(f"Duration: {call.vcp_payload.call.duration_sec}s")
    print(f"Status: {call.vcp_payload.outcomes.objective.status}")
    print("---")
```

### Scenario Types

The generator supports these HVAC scenarios:

- `BOOKED_SERVICE` - Successful service appointment booking
- `LIVE_TRANSFER` - Transfer to human dispatcher
- `SCHEDULED_CALLBACK` - Callback window scheduled
- `QUOTE_REQUESTED` - Installation or repair quote
- `OUT_OF_SERVICE_AREA` - Outside service coverage
- `SPAM_FILTERED` - Non-lead/spam call filtered
- `NO_SHOW_CANCEL` - Appointment cancellation
- `EMERGENCY_SERVICE` - Emergency HVAC service

## Data Format

All generated data follows the VCP 0.3 standard with:

- **Call Information**: Provider, timing, capabilities, success criteria
- **Outcomes**: Perceived sentiment, objective metrics, perception gaps
- **Artifacts**: Recording URLs, transcript refs, provider payloads  
- **Custom Fields**: Provider-specific data, synthetic markers
- **Audit Trail**: Processing timestamps, schema versioning

### Example Payload Structure

```json
{
  "call_id": "uuid",
  "vcp_version": "0.3",
  "vcp_payload": {
    "call": { /* call info */ },
    "outcomes": {
      "perceived": [{ /* sentiment analysis */ }],
      "objective": { /* metrics and status */ },
      "perception_gap": { /* gap analysis */ }
    },
    "artifacts": { /* URLs and refs */ },
    "custom": { 
      "synthetic": true,
      "outcome_hint": "booked_service"
    },
    "audit": { /* processing trail */ }
  }
}
```

## Integration

### Testing VoiceLens Endpoints

Use generated data to test your VoiceLens endpoints:

```bash
# Generate test data
python -m voicelens_seeder.cli generate baseline --out ./test_data

# Send to endpoint (example)
for file in test_data/*.json; do
  curl -X POST https://your-voicelens-endpoint.com/conversations \
    -H "Content-Type: application/json" \
    -d @"$file"
done
```

### Dashboard Development

Load synthetic data for dashboard prototyping:

```python
import json
from pathlib import Path

# Load all generated conversations
data_dir = Path("./synthetic_data")
conversations = []

for json_file in data_dir.glob("*.json"):
    with open(json_file) as f:
        conversations.append(json.load(f))

# Extract metrics for dashboard
metrics = []
for conv in conversations:
    payload = conv["vcp_payload"]
    metrics.append({
        "provider": payload["call"]["provider"],
        "duration": payload["call"]["duration_sec"],
        "status": payload["outcomes"]["objective"]["status"],
        "sentiment": payload["outcomes"]["perceived"][0]["sentiment"]["score"],
        "value": payload["outcomes"]["objective"]["metrics"]["estimated_value_usd"],
        "scenario": payload["custom"]["outcome_hint"]
    })

# Now use metrics for charts, tables, etc.
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Make sure you've activated the virtual environment and installed with `pip install -e .`

2. **Permission errors**: Ensure you have write permissions to the output directory

3. **Invalid provider**: Use one of: retell, vapi, bland, all

4. **Memory issues with large batches**: Generate in smaller chunks if creating thousands of conversations

### Getting Help

```bash
# View all available commands
python -m voicelens_seeder.cli --help

# Get help for specific commands
python -m voicelens_seeder.cli generate --help
python -m voicelens_seeder.cli generate baseline --help
```