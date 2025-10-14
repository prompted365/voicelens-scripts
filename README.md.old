# VoiceLens Scripts

> **Synthetic Data Generation & Analytics for Voice AI Systems**

A powerful CLI toolkit for generating realistic conversation data, computing perception gaps, and creating compelling GTM narratives for voice AI platforms.

## 🎯 What This Is

VoiceLens Scripts is designed to rapidly generate high-quality synthetic conversation data that mirrors real-world patterns for:

- **GTM Demo Data**: Create compelling, realistic datasets for sales demonstrations
- **Dashboard Testing**: Rapidly populate dashboards with varied scenarios
- **Agent Classification**: Test and train agent role detection systems  
- **Perception Gap Analysis**: Model and analyze alignment between customer perception and system confidence
- **Narrative Crafting**: Generate data-driven insights for strategic messaging

## ⚡ Quick Start

```bash
# Clone and install
git clone https://github.com/prompted365/voicelens-scripts.git
cd voicelens-scripts
pip install -e .

# Create your first dataset
voicelens demo happy-path --profile happy_path_us

# Export for visualization
voicelens export csv --tables conversations,perception_gaps --out exports/demo_data
```

## 🏗️ Architecture

```
Data Flow: Generate → Normalize → Classify → Analyze → Export/Send
Storage: SQLite with WAL mode for fast concurrent access
Output: CSV, JSON, direct API sends to VoiceLens endpoints
```

### Key Components

- **Synthetic Generator**: Realistic conversation patterns with configurable scenarios
- **VCP Normalizer**: Transforms Voice Call Payload (VCP) format into structured data
- **Agent Classifier**: Rule-based system for agent role detection
- **Perception Gap Computer**: Quantifies misalignment between system confidence and customer sentiment
- **Analytics Engine**: GTM-focused insights and summaries
- **Export System**: Multiple output formats for downstream tools

## 🎮 Command Groups

| Command | Purpose | Example |
|---------|---------|---------|
| `init-db` | Initialize SQLite schema | `voicelens init-db --db data/conversations.db` |
| `config` | Manage profiles and settings | `voicelens config save --name enterprise_support` |
| `generate` | Create synthetic conversations | `voicelens generate --count 1000 --profile mixed_scenarios` |
| `normalize` | Process VCP payloads | `voicelens normalize --input data/vcp_batch.jsonl` |
| `classify` | Run agent role detection | `voicelens classify roles --rules config/classification_rules.yaml` |
| `gaps` | Compute perception gaps | `voicelens gaps compute --dimensions outcome,sentiment` |
| `analyze` | Generate insights | `voicelens analyze summary --window 30d --json` |
| `export` | Export to CSV/Parquet | `voicelens export csv --tables conversations,participants` |
| `send` | Push to remote endpoints | `voicelens send --endpoint production --limit 500` |
| `demo` | Guided workflows | `voicelens demo happy-path` |

## 📊 GTM Use Cases

### Sales Demonstration
```bash
# Generate 30 days of "happy path" conversations
voicelens demo happy-path --profile enterprise_demo
voicelens analyze summary --out reports/executive_summary.json
```

### Agent Performance Testing
```bash
# Create mixed performance scenarios
voicelens generate --count 2000 --profile agent_performance_mix
voicelens classify roles --confidence-threshold 0.7
voicelens gaps compute --min-confidence 0.5
```

### Dashboard Population
```bash
# Quick dataset for UI testing
voicelens generate --count 500 --start-days-ago 7 --profile dashboard_test
voicelens export csv --out data/dashboard_seed.csv
```

## 🔧 Configuration

Profiles are stored in `~/.voicelens/profiles/` and support:

- **Time Patterns**: Business hours, regional time zones, seasonal variations
- **Scenario Mix**: Success rates, escalation patterns, transfer frequencies
- **Agent Distribution**: Team compositions, skill levels, tenure patterns  
- **Outcome Weights**: Customizable success/failure/neutral distributions
- **Quality Settings**: Sentiment ranges, confidence calibration, realistic noise

Example profile snippet:
```yaml
dataset_name: "enterprise_support"
scenario_mix:
  billing_inquiry: 0.35
  technical_support: 0.40  
  account_changes: 0.25
outcome_distributions:
  success: 0.75
  transfer: 0.12
  escalation: 0.08
  unresolved: 0.05
```

## 🚀 Development Status

- ✅ **Repository & Governance** - MIT license, issue templates, contribution guidelines
- 🚧 **Core CLI & Schema** - Typer-based commands, SQLite with migrations  
- 🚧 **Synthetic Generation** - Realistic patterns, configurable scenarios
- 📋 **Classification System** - Rule-based agent detection
- 📋 **Analytics & Export** - GTM insights, multiple output formats
- 📋 **Remote Integration** - Endpoint management, safe sending
- 📋 **Documentation** - Comprehensive guides, narrative templates

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built with ❤️ by [Prompted LLC](https://prompted.com) for the VoiceLens ecosystem**