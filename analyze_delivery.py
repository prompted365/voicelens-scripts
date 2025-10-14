#!/usr/bin/env python3
"""
Post-run reconciliation and QA analysis for delivered VoiceLens dataset
"""
import json
import os
import sys
import random
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple
import re

class DatasetAnalyzer:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.conversations = []
        self.analysis_results = {}
        
    def load_conversations(self) -> None:
        """Load all conversation JSON files from the directory"""
        print(f"📂 Loading conversations from {self.data_dir}")
        
        json_files = list(self.data_dir.glob("*.json"))
        print(f"Found {len(json_files)} JSON files")
        
        for file_path in json_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self.conversations.append({
                        'file_name': file_path.name,
                        'data': data
                    })
            except Exception as e:
                print(f"⚠️  Error loading {file_path}: {e}")
        
        print(f"✅ Loaded {len(self.conversations)} conversations successfully")
    
    def analyze_counts_and_coverage(self) -> Dict[str, Any]:
        """Analyze basic counts and time coverage"""
        print("\n🔢 Analyzing counts and coverage...")
        
        total_count = len(self.conversations)
        
        # Extract timestamps
        timestamps = []
        for conv in self.conversations:
            try:
                start_time = conv['data']['vcp_payload']['call']['start_time']
                timestamps.append(datetime.fromisoformat(start_time.replace('Z', '+00:00')))
            except Exception as e:
                print(f"⚠️  Could not parse timestamp from {conv['file_name']}: {e}")
        
        # Time range analysis
        if timestamps:
            min_time = min(timestamps)
            max_time = max(timestamps)
            time_span = (max_time - min_time).days
        else:
            min_time = max_time = None
            time_span = 0
        
        results = {
            'total_conversations': total_count,
            'expected_conversations': 1800,  # What we sent
            'coverage_match': total_count == 1800,
            'time_range': {
                'earliest': min_time.isoformat() if min_time else None,
                'latest': max_time.isoformat() if max_time else None,
                'span_days': time_span
            }
        }
        
        print(f"   📊 Total conversations: {total_count}")
        print(f"   📅 Time span: {time_span} days ({min_time.date()} to {max_time.date()})" if timestamps else "   ❌ No valid timestamps")
        print(f"   ✅ Count matches expected" if results['coverage_match'] else f"   ⚠️  Count mismatch: got {total_count}, expected 1800")
        
        return results
    
    def analyze_scenario_distribution(self) -> Dict[str, Any]:
        """Analyze scenario types and their distribution"""
        print("\n🎭 Analyzing scenario distribution...")
        
        scenarios = []
        providers = []
        
        for conv in self.conversations:
            try:
                payload = conv['data']['vcp_payload']
                scenario = payload['custom'].get('outcome_hint', 'unknown')
                provider = payload['call'].get('provider', 'unknown')
                
                scenarios.append(scenario)
                providers.append(provider)
            except Exception as e:
                print(f"⚠️  Could not extract scenario from {conv['file_name']}: {e}")
        
        scenario_counts = Counter(scenarios)
        provider_counts = Counter(providers)
        
        results = {
            'scenario_distribution': dict(scenario_counts),
            'provider_distribution': dict(provider_counts),
            'unique_scenarios': len(scenario_counts),
            'unique_providers': len(provider_counts)
        }
        
        print(f"   🎯 Unique scenarios: {len(scenario_counts)}")
        for scenario, count in scenario_counts.most_common():
            percentage = (count / len(scenarios)) * 100
            print(f"      • {scenario}: {count} ({percentage:.1f}%)")
        
        print(f"   🏢 Provider distribution:")
        for provider, count in provider_counts.items():
            percentage = (count / len(providers)) * 100
            print(f"      • {provider}: {count} ({percentage:.1f}%)")
        
        return results
    
    def analyze_duration_and_metrics(self) -> Dict[str, Any]:
        """Analyze conversation durations and other metrics"""
        print("\n⏱️  Analyzing durations and metrics...")
        
        durations = []
        turn_counts = []
        
        for conv in self.conversations:
            try:
                payload = conv['data']['vcp_payload']
                duration = payload['call'].get('duration_sec', 0)
                durations.append(duration)
                
                # Try to extract turn count (this may vary based on data structure)
                metrics = payload.get('outcomes', {}).get('objective', {}).get('metrics', {})
                # We don't have transcript turn counts in the current format, so we'll skip this
                
            except Exception as e:
                continue
        
        if durations:
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
        else:
            avg_duration = min_duration = max_duration = 0
        
        results = {
            'duration_stats': {
                'average_sec': avg_duration,
                'min_sec': min_duration,
                'max_sec': max_duration,
                'total_conversations_with_duration': len(durations)
            }
        }
        
        print(f"   ⏱️  Average duration: {avg_duration:.1f}s")
        print(f"   📊 Duration range: {min_duration}s - {max_duration}s")
        
        return results
    
    def analyze_time_distribution(self) -> Dict[str, Any]:
        """Analyze temporal distribution patterns"""
        print("\n📅 Analyzing time distribution...")
        
        hourly_counts = defaultdict(int)
        daily_counts = defaultdict(int)
        
        for conv in self.conversations:
            try:
                start_time_str = conv['data']['vcp_payload']['call']['start_time']
                dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                
                # Count by hour of day
                hourly_counts[dt.hour] += 1
                
                # Count by day of week (0=Monday, 6=Sunday)
                daily_counts[dt.weekday()] += 1
                
            except Exception as e:
                continue
        
        results = {
            'hourly_distribution': dict(hourly_counts),
            'daily_distribution': dict(daily_counts)
        }
        
        print(f"   🕐 Peak hours:")
        for hour in sorted(hourly_counts.keys(), key=lambda h: hourly_counts[h], reverse=True)[:5]:
            count = hourly_counts[hour]
            print(f"      • {hour:02d}:00 - {count} conversations")
        
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        print(f"   📆 Daily distribution:")
        for day_idx in range(7):
            count = daily_counts.get(day_idx, 0)
            print(f"      • {day_names[day_idx]}: {count} conversations")
        
        return results
    
    def spot_check_realism(self, sample_size: int = 10) -> Dict[str, Any]:
        """Randomly sample conversations to check for realism and HVAC terminology"""
        print(f"\n🔍 Spot-checking {sample_size} conversations for realism...")
        
        if len(self.conversations) < sample_size:
            sample_size = len(self.conversations)
        
        sampled = random.sample(self.conversations, sample_size)
        
        hvac_terms = [
            'hvac', 'air conditioning', 'ac', 'furnace', 'thermostat', 'heating', 'cooling',
            'temperature', 'filter', 'duct', 'maintenance', 'repair', 'installation',
            'service', 'technician', 'appointment', 'emergency', 'warranty'
        ]
        
        findings = []
        terminology_found = 0
        
        for i, conv in enumerate(sampled, 1):
            try:
                payload = conv['data']['vcp_payload']
                scenario = payload['custom'].get('outcome_hint', 'unknown')
                duration = payload['call'].get('duration_sec', 0)
                
                # Check if content seems HVAC-related by examining the data
                content_str = json.dumps(payload).lower()
                hvac_matches = [term for term in hvac_terms if term in content_str]
                
                if hvac_matches:
                    terminology_found += 1
                
                finding = {
                    'sample_id': i,
                    'file_name': conv['file_name'],
                    'scenario': scenario,
                    'duration_sec': duration,
                    'hvac_terms_found': hvac_matches,
                    'seems_realistic': len(hvac_matches) > 0 and duration > 10
                }
                findings.append(finding)
                
                print(f"   Sample {i}: {scenario} ({duration}s) - {len(hvac_matches)} HVAC terms")
                
            except Exception as e:
                print(f"   ⚠️  Error analyzing sample {i}: {e}")
        
        results = {
            'samples_analyzed': len(findings),
            'samples_with_hvac_terminology': terminology_found,
            'terminology_rate': (terminology_found / len(findings)) * 100 if findings else 0,
            'detailed_findings': findings
        }
        
        print(f"   📊 HVAC terminology rate: {results['terminology_rate']:.1f}%")
        
        return results
    
    def check_pii_compliance(self) -> Dict[str, Any]:
        """Verify no real PII is present"""
        print("\n🔒 Checking PII compliance...")
        
        # Patterns that might indicate real PII
        phone_pattern = re.compile(r'\b\d{3}-\d{3}-\d{4}\b')
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        potential_issues = []
        
        for conv in self.conversations[:100]:  # Sample first 100 for PII check
            try:
                content_str = json.dumps(conv['data'])
                
                # Check for phone numbers
                phone_matches = phone_pattern.findall(content_str)
                email_matches = email_pattern.findall(content_str)
                
                if phone_matches or email_matches:
                    potential_issues.append({
                        'file_name': conv['file_name'],
                        'phone_numbers': phone_matches,
                        'emails': email_matches
                    })
                    
            except Exception as e:
                continue
        
        results = {
            'files_checked': min(100, len(self.conversations)),
            'potential_pii_issues': len(potential_issues),
            'issues': potential_issues[:5],  # Show first 5 issues if any
            'appears_compliant': len(potential_issues) == 0
        }
        
        if results['appears_compliant']:
            print("   ✅ No obvious PII patterns detected")
        else:
            print(f"   ⚠️  Found {len(potential_issues)} potential PII issues")
        
        return results
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive summary report"""
        print("\n📋 Generating summary report...")
        
        counts = self.analyze_counts_and_coverage()
        scenarios = self.analyze_scenario_distribution()
        durations = self.analyze_duration_and_metrics()
        time_dist = self.analyze_time_distribution()
        realism = self.spot_check_realism(20)
        pii = self.check_pii_compliance()
        
        summary = {
            'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
            'data_directory': str(self.data_dir),
            'counts_and_coverage': counts,
            'scenario_analysis': scenarios,
            'duration_analysis': durations,
            'time_distribution': time_dist,
            'realism_check': realism,
            'pii_compliance': pii,
            'overall_quality_score': self._calculate_quality_score(counts, scenarios, realism, pii)
        }
        
        return summary
    
    def _calculate_quality_score(self, counts, scenarios, realism, pii) -> Dict[str, Any]:
        """Calculate an overall quality score"""
        score = 0
        max_score = 100
        issues = []
        
        # Count accuracy (20 points)
        if counts['coverage_match']:
            score += 20
        else:
            issues.append(f"Count mismatch: {counts['total_conversations']} vs expected 1800")
        
        # Scenario diversity (20 points)
        if scenarios['unique_scenarios'] >= 5:
            score += 20
        elif scenarios['unique_scenarios'] >= 3:
            score += 15
        else:
            score += 10
            issues.append(f"Low scenario diversity: {scenarios['unique_scenarios']} unique scenarios")
        
        # Provider distribution (20 points)
        if scenarios['unique_providers'] >= 3:
            score += 20
        else:
            score += 10
            issues.append(f"Limited provider diversity: {scenarios['unique_providers']} providers")
        
        # Realism (20 points)
        if realism['terminology_rate'] >= 80:
            score += 20
        elif realism['terminology_rate'] >= 60:
            score += 15
        else:
            score += 10
            issues.append(f"Low HVAC terminology rate: {realism['terminology_rate']:.1f}%")
        
        # PII compliance (20 points)
        if pii['appears_compliant']:
            score += 20
        else:
            score += 0
            issues.append(f"Potential PII issues: {pii['potential_pii_issues']} files")
        
        return {
            'score': score,
            'max_score': max_score,
            'percentage': (score / max_score) * 100,
            'grade': 'A' if score >= 90 else 'B' if score >= 80 else 'C' if score >= 70 else 'D',
            'issues': issues
        }

def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_delivery.py <data_directory>")
        print("Example: python analyze_delivery.py ./synthetic_60d_data")
        sys.exit(1)
    
    data_dir = Path(sys.argv[1])
    
    if not data_dir.exists():
        print(f"❌ Directory {data_dir} does not exist")
        sys.exit(1)
    
    print(f"🔬 Starting analysis of dataset: {data_dir}")
    print("=" * 60)
    
    analyzer = DatasetAnalyzer(data_dir)
    analyzer.load_conversations()
    
    # Generate comprehensive report
    summary = analyzer.generate_summary_report()
    
    # Save report to file
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    report_file = reports_dir / "delivery_analysis.json"
    with open(report_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Print final summary
    quality = summary['overall_quality_score']
    print(f"\n🏆 Overall Quality Assessment:")
    print(f"   Score: {quality['score']}/{quality['max_score']} ({quality['percentage']:.1f}%) - Grade {quality['grade']}")
    
    if quality['issues']:
        print(f"   Issues found:")
        for issue in quality['issues']:
            print(f"      • {issue}")
    else:
        print(f"   ✅ No major issues detected!")

if __name__ == "__main__":
    main()