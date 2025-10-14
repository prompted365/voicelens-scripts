#!/usr/bin/env python3
"""
Script to send baseline JSON files to the webhook endpoint
"""
import json
import requests
import os
import sys
from pathlib import Path

# Webhook endpoint
WEBHOOK_URL = "https://ogqwehdmnlvpdjxdqhkt.functions.supabase.co/vcp-webhook/a/voiceai4hvac/c/localhvac/s/YXjNgJgboxK2VTJt1uDQHJ"

def send_baseline_files(baseline_dir):
    """Send all JSON files in the baseline directory to the webhook endpoint"""
    baseline_path = Path(baseline_dir)
    
    if not baseline_path.exists():
        print(f"❌ Directory {baseline_dir} does not exist")
        return False
    
    # Find all JSON files
    json_files = list(baseline_path.glob("*.json"))
    
    if not json_files:
        print(f"❌ No JSON files found in {baseline_dir}")
        return False
    
    print(f"📤 Found {len(json_files)} baseline files to send")
    
    success_count = 0
    failed_files = []
    
    for json_file in sorted(json_files):
        try:
            # Read the JSON file
            with open(json_file, 'r') as f:
                payload = json.load(f)
            
            # Send POST request
            print(f"📨 Sending {json_file.name}...")
            
            response = requests.post(
                WEBHOOK_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ Successfully sent {json_file.name} (HTTP {response.status_code})")
                success_count += 1
            else:
                print(f"⚠️  {json_file.name} returned HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                failed_files.append(json_file.name)
                
        except requests.RequestException as e:
            print(f"❌ Network error sending {json_file.name}: {e}")
            failed_files.append(json_file.name)
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error in {json_file.name}: {e}")
            failed_files.append(json_file.name)
        except Exception as e:
            print(f"❌ Unexpected error with {json_file.name}: {e}")
            failed_files.append(json_file.name)
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Successfully sent: {success_count}/{len(json_files)} files")
    
    if failed_files:
        print(f"   ❌ Failed files: {', '.join(failed_files)}")
        return False
    else:
        print(f"   🎉 All files sent successfully!")
        return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python send_baselines.py <baseline_directory>")
        print("Example: python send_baselines.py /tmp/baseline_output")
        sys.exit(1)
    
    baseline_dir = sys.argv[1]
    success = send_baseline_files(baseline_dir)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()