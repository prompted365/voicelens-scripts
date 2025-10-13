#!/usr/bin/env python3
"""
Quick integration test for the synthetic VCP generator.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from voicelens_seeder.generator.synthetic import VCPSyntheticGenerator
from voicelens_seeder.normalizers.vcp import Provider
from voicelens_seeder.generator.hvac_scenarios import HVACScenario


def test_baseline_examples():
    """Test generating the 8 baseline examples."""
    print("🔧 Testing baseline example generation...")
    
    generator = VCPSyntheticGenerator(seed=42)  # Reproducible
    examples = generator.generate_baseline_examples()
    
    print(f"✅ Generated {len(examples)} baseline examples")
    
    # Test first example
    first = examples[0]
    print(f"📋 First example call_id: {first.call_id}")
    print(f"🏷️  Scenario: {first.vcp_payload.custom.outcome_hint}")
    print(f"📞 Provider: {first.vcp_payload.call.provider}")
    
    # Validate structure
    assert first.vcp_version == "0.3"
    assert first.vcp_payload.call.call_id == first.call_id
    assert first.vcp_payload.outcomes.objective.metrics.aht_sec > 0
    assert first.vcp_payload.custom.synthetic is True
    
    print("✅ Structure validation passed")


def test_batch_generation():
    """Test batch generation functionality."""
    print("\n🔧 Testing batch generation...")
    
    generator = VCPSyntheticGenerator(seed=123)
    
    # Generate 5 calls for the last 24 hours
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=1)
    
    batch = list(generator.generate_call_batch(
        count=5,
        start_date=start_time,
        end_date=end_time,
        providers=[Provider.RETELL, Provider.VAPI]
    ))
    
    print(f"✅ Generated batch of {len(batch)} calls")
    
    # Verify diversity
    providers = set(call.vcp_payload.call.provider for call in batch)
    scenarios = set(call.vcp_payload.custom.outcome_hint for call in batch)
    
    print(f"🎯 Providers used: {providers}")
    print(f"🎯 Scenarios used: {scenarios}")
    
    # Validate timing
    for call in batch:
        call_time = datetime.fromisoformat(
            call.vcp_payload.call.start_time.rstrip('Z')
        ).replace(tzinfo=timezone.utc)
        
        assert start_time <= call_time <= end_time
    
    print("✅ Timing validation passed")


def test_json_serialization():
    """Test that generated payloads can be serialized to JSON."""
    print("\n🔧 Testing JSON serialization...")
    
    generator = VCPSyntheticGenerator(seed=456)
    payload = generator.generate_vcp_payload(
        call_time=datetime.now(timezone.utc),
        scenario=HVACScenario.BOOKED_SERVICE,
        provider=Provider.RETELL
    )
    
    # Test Pydantic JSON serialization
    json_str = payload.model_dump_json(indent=2)
    parsed = json.loads(json_str)
    
    print(f"✅ JSON serialization successful ({len(json_str)} chars)")
    
    # Verify key fields exist
    assert "call_id" in parsed
    assert "vcp_version" in parsed  
    assert "vcp_payload" in parsed
    assert parsed["vcp_version"] == "0.3"
    
    print("✅ JSON structure validation passed")


def save_sample_output():
    """Save a sample output for manual inspection."""
    print("\n💾 Saving sample output...")
    
    generator = VCPSyntheticGenerator(seed=789)
    example = generator.generate_baseline_examples()[0]
    
    output_path = Path("sample_vcp_output.json")
    with open(output_path, 'w') as f:
        f.write(example.model_dump_json(indent=2))
    
    print(f"✅ Sample saved to {output_path}")
    
    # Also print a compact version
    print("\n📄 Sample payload preview:")
    print("=" * 50)
    compact = json.loads(example.model_dump_json())
    
    # Show key fields
    call_info = compact["vcp_payload"]["call"]
    outcomes = compact["vcp_payload"]["outcomes"]
    
    print(f"Call ID: {compact['call_id']}")
    print(f"Provider: {call_info['provider']}")
    print(f"Duration: {call_info['duration_sec']}s")
    print(f"Scenario: {compact['vcp_payload']['custom']['outcome_hint']}")
    print(f"Status: {outcomes['objective']['status']}")
    print(f"Sentiment: {outcomes['perceived'][0]['sentiment']['score']:.2f}")
    print("=" * 50)


if __name__ == "__main__":
    print("🚀 Running VCP Synthetic Generator Integration Tests\n")
    
    try:
        test_baseline_examples()
        test_batch_generation()
        test_json_serialization()
        save_sample_output()
        
        print("\n🎉 All tests passed! Generator is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)