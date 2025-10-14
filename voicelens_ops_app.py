#!/usr/bin/env python3
"""
VoiceLens Operations Application
Internal operations dashboard for managing voice AI providers and VCP operations
"""
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timezone, timedelta
import json
import sqlite3
from typing import Dict, List, Any, Optional
import logging
from dataclasses import asdict
import os
from pathlib import Path

# Import our modules
from provider_documentation import VoiceAIProviderRegistry, VCPMapper, generate_provider_comparison_matrix
from provider_monitoring import VoiceLensMonitoringSystem, ChangeEvent, ChangeType, SeverityLevel
from vcp_v05_schema import VCPValidator, VCPMessage, create_example_v05_message

# Setup Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'voicelens-ops-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voicelens_ops.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebhookTest(db.Model):
    """Store webhook test results"""
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)
    test_type = db.Column(db.String(50), nullable=False)  # 'payload_test', 'signature_test'
    payload = db.Column(db.Text)
    expected_vcp = db.Column(db.Text)
    actual_vcp = db.Column(db.Text)
    success = db.Column(db.Boolean)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VCPTransformation(db.Model):
    """Store VCP transformation records"""
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)
    source_format = db.Column(db.String(20))  # 'webhook', 'api_response'
    source_payload = db.Column(db.Text, nullable=False)
    vcp_version = db.Column(db.String(10), default='0.5')
    vcp_payload = db.Column(db.Text, nullable=False)
    transformation_time_ms = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize database when app starts
def init_db():
    with app.app_context():
        db.create_all()

# Initialize registry and monitoring
registry = VoiceAIProviderRegistry()
vcp_mapper = VCPMapper(registry)
vcp_validator = VCPValidator()
monitoring_system = VoiceLensMonitoringSystem()

@app.route('/')
def dashboard():
    """Main dashboard view"""
    return render_template('dashboard.html')

@app.route('/api/providers')
def get_providers():
    """Get all provider information"""
    providers = registry.get_all_providers()
    provider_data = []
    
    for provider in providers:
        provider_dict = {
            'name': provider.name,
            'company': provider.company,
            'website': provider.website,
            'docs_url': provider.docs_url,
            'api_base_url': provider.api_base_url,
            'status_page': provider.status_page,
            'changelog_url': provider.changelog_url,
            'webhook_auth': {
                'method': provider.webhook_auth.method.value if provider.webhook_auth else None,
                'header_name': provider.webhook_auth.header_name if provider.webhook_auth else None,
                'requires_secret': provider.webhook_auth.secret_key_required if provider.webhook_auth else False,
                'ip_addresses': provider.webhook_auth.ip_addresses if provider.webhook_auth else []
            },
            'supported_events': [event.value for event in provider.supported_events] if provider.supported_events else [],
            'webhook_schemas': len(provider.webhook_schemas) if provider.webhook_schemas else 0,
            'vcp_mapping_fields': len(provider.vcp_mapping_rules) if provider.vcp_mapping_rules else 0,
            'last_updated': provider.last_updated.isoformat() if provider.last_updated else None
        }
        provider_data.append(provider_dict)
    
    return jsonify(provider_data)

@app.route('/api/providers/<provider_name>')
def get_provider_details(provider_name):
    """Get detailed information for a specific provider"""
    provider = registry.get_provider(provider_name)
    
    if not provider:
        return jsonify({'error': 'Provider not found'}), 404
    
    # Get webhook schemas with examples
    schemas = []
    if provider.webhook_schemas:
        for schema in provider.webhook_schemas:
            schemas.append({
                'event_type': schema.event_type.value,
                'required_fields': schema.required_fields,
                'optional_fields': schema.optional_fields or [],
                'nested_objects': schema.nested_objects or {},
                'example_payload': schema.example_payload
            })
    
    provider_data = {
        'name': provider.name,
        'company': provider.company,
        'website': provider.website,
        'docs_url': provider.docs_url,
        'api_base_url': provider.api_base_url,
        'status_page': provider.status_page,
        'changelog_url': provider.changelog_url,
        'rss_feed': provider.rss_feed,
        'webhook_auth': asdict(provider.webhook_auth) if provider.webhook_auth else None,
        'supported_events': [event.value for event in provider.supported_events] if provider.supported_events else [],
        'webhook_schemas': schemas,
        'vcp_mapping_rules': provider.vcp_mapping_rules or {},
        'last_updated': provider.last_updated.isoformat() if provider.last_updated else None
    }
    
    return jsonify(provider_data)

@app.route('/api/webhook-test', methods=['POST'])
def test_webhook_transformation():
    """Test webhook payload transformation to VCP"""
    data = request.get_json()
    
    if not data or 'provider' not in data or 'payload' not in data:
        return jsonify({'error': 'Provider and payload are required'}), 400
    
    provider_name = data['provider']
    webhook_payload = data['payload']
    
    try:
        start_time = datetime.now()
        
        # Transform to VCP
        vcp_result = vcp_mapper.map_to_vcp(provider_name, webhook_payload)
        
        transformation_time = (datetime.now() - start_time).total_seconds() * 1000
        
        if not vcp_result:
            error_msg = f"No VCP mapping rules found for provider: {provider_name}"
            
            # Store test result
            test_record = WebhookTest(
                provider=provider_name,
                test_type='payload_test',
                payload=json.dumps(webhook_payload),
                success=False,
                error_message=error_msg
            )
            db.session.add(test_record)
            db.session.commit()
            
            return jsonify({'error': error_msg}), 400
        
        # Validate VCP result
        try:
            vcp_message = VCPMessage(**vcp_result)
            validation_results = vcp_validator.validate_v05(vcp_message)
        except Exception as validation_error:
            validation_results = {
                'errors': [str(validation_error)],
                'warnings': []
            }
        
        # Store successful transformation
        transform_record = VCPTransformation(
            provider=provider_name,
            source_format='webhook',
            source_payload=json.dumps(webhook_payload),
            vcp_payload=json.dumps(vcp_result),
            transformation_time_ms=transformation_time
        )
        db.session.add(transform_record)
        
        test_record = WebhookTest(
            provider=provider_name,
            test_type='payload_test',
            payload=json.dumps(webhook_payload),
            expected_vcp=json.dumps(vcp_result),
            actual_vcp=json.dumps(vcp_result),
            success=len(validation_results.get('errors', [])) == 0
        )
        db.session.add(test_record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'vcp_payload': vcp_result,
            'transformation_time_ms': transformation_time,
            'validation': validation_results
        })
        
    except Exception as e:
        logger.error(f"Error testing webhook transformation: {e}")
        
        # Store failed test
        test_record = WebhookTest(
            provider=provider_name,
            test_type='payload_test',
            payload=json.dumps(webhook_payload),
            success=False,
            error_message=str(e)
        )
        db.session.add(test_record)
        db.session.commit()
        
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/transformation-stats')
def get_transformation_stats():
    """Get VCP transformation analytics"""
    try:
        # Query transformation records
        total_transformations = VCPTransformation.query.count()
        
        # Get provider breakdown with average transformation times
        provider_stats = {}
        for provider_name in ['retell', 'bland', 'vapi', 'elevenlabs', 'openai_realtime', 'assistable']:
            provider_transforms = VCPTransformation.query.filter_by(provider=provider_name).all()
            if provider_transforms:
                avg_time = sum(t.transformation_time_ms or 0 for t in provider_transforms) / len(provider_transforms)
                provider_stats[provider_name] = {
                    'count': len(provider_transforms),
                    'avg_time_ms': round(avg_time, 2)
                }
            else:
                provider_stats[provider_name] = {
                    'count': 0,
                    'avg_time_ms': 0
                }
        
        return jsonify({
            'total_transformations': total_transformations,
            'provider_breakdown': provider_stats,
            'last_updated': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting transformation stats: {e}")
        return jsonify({
            'total_transformations': 0,
            'provider_breakdown': {},
            'error': str(e)
        })

@app.route('/api/analytics/test-results')
def get_test_results():
    """Get webhook test analytics"""
    try:
        # Query test records
        total_tests = WebhookTest.query.count()
        
        # Get test summary by provider
        test_summary = []
        for provider_name in ['retell', 'bland', 'vapi', 'elevenlabs', 'openai_realtime', 'assistable']:
            provider_tests = WebhookTest.query.filter_by(provider=provider_name).all()
            
            if provider_tests:
                successful_tests = [t for t in provider_tests if t.success]
                success_rate = (len(successful_tests) / len(provider_tests)) * 100
            else:
                success_rate = 0
            
            test_summary.append({
                'provider': provider_name,
                'total_tests': len(provider_tests) if provider_tests else 0,
                'success_rate': round(success_rate, 1)
            })
        
        return jsonify({
            'total_tests': total_tests,
            'test_summary': test_summary,
            'last_updated': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting test results: {e}")
        return jsonify({
            'total_tests': 0,
            'test_summary': [],
            'error': str(e)
        })

@app.route('/api/monitoring/changes')
def get_monitoring_changes():
    """Get recent monitoring changes"""
    try:
        # Get recent changes from monitoring system
        changes = monitoring_system.get_recent_changes(limit=10)
        
        # Convert to serializable format
        change_data = []
        for change in changes:
            change_data.append({
                'title': change.title,
                'provider': change.provider,
                'change_type': change.change_type.value,
                'severity': change.severity.value,
                'detected_at': change.detected_at.isoformat(),
                'description': change.description
            })
        
        return jsonify(change_data)
    except Exception as e:
        logger.error(f"Error getting monitoring changes: {e}")
        return jsonify([])

@app.route('/api/monitoring/health')
def get_monitoring_health():
    """Get service health status"""
    try:
        health_data = []
        
        # Check each provider's status
        for provider in registry.get_all_providers():
            try:
                # Simple health check - try to access the provider's status page or API
                import requests
                response_time_start = datetime.now()
                
                if provider.status_page:
                    resp = requests.get(provider.status_page, timeout=5)
                    is_healthy = resp.status_code == 200
                    endpoint = provider.status_page
                elif provider.api_base_url:
                    resp = requests.get(provider.api_base_url, timeout=5)
                    # API endpoints are healthy if they respond (even with auth errors)
                    is_healthy = resp.status_code in [200, 400, 401, 403, 405, 422]  # These indicate the API is running
                    endpoint = provider.api_base_url
                else:
                    is_healthy = True  # No endpoint to check
                    endpoint = "N/A"
                
                response_time = (datetime.now() - response_time_start).total_seconds() * 1000
                
            except requests.exceptions.RequestException as e:
                is_healthy = False
                response_time = 0
                endpoint = provider.status_page or provider.api_base_url or "N/A"
                logger.debug(f"Health check failed for {provider.name} at {endpoint}: {e}")
            except Exception as e:
                is_healthy = False
                response_time = 0
                endpoint = provider.status_page or provider.api_base_url or "N/A"
                logger.debug(f"Unexpected error in health check for {provider.name}: {e}")
            
            health_data.append({
                'provider': provider.name,
                'is_healthy': is_healthy,
                'endpoint': endpoint,
                'response_time_ms': round(response_time, 2)
            })
        
        return jsonify(health_data)
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return jsonify([])

@app.route('/api/webhook-signature-test', methods=['POST'])
def test_webhook_signature():
    """Test webhook signature validation"""
    data = request.get_json()
    
    if not data or 'provider' not in data:
        return jsonify({'error': 'Provider is required'}), 400
    
    provider_name = data['provider']
    payload = data.get('payload', '')
    signature = data.get('signature', '')
    secret = data.get('secret', '')
    
    try:
        is_valid = registry.validate_webhook_signature(provider_name, payload, signature, secret)
        
        # Store test result
        test_record = WebhookTest(
            provider=provider_name,
            test_type='signature_test',
            payload=payload,
            success=is_valid,
            error_message=None if is_valid else "Signature validation failed"
        )
        db.session.add(test_record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'signature_valid': is_valid,
            'provider': provider_name
        })
        
    except Exception as e:
        logger.error(f"Error testing webhook signature: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/vcp-example/<provider_name>')
def get_vcp_example(provider_name):
    """Generate a VCP v0.4 example for a provider"""
    try:
        # Create base example
        example = create_example_v05_message()
        
        # Customize for provider
        provider = registry.get_provider(provider_name)
        if provider:
            example.vcp_payload.call.provider = provider_name
            example.vcp_payload.provenance.source_system = f"{provider_name}_webhook_api"
        
        return jsonify(example.model_dump())
        
    except Exception as e:
        logger.error(f"Error generating VCP example: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/changes')
def get_recent_changes():
    """Get recent provider changes from monitoring system"""
    try:
        # Connect to monitoring database
        db_path = "monitoring.db"
        
        if not os.path.exists(db_path):
            return jsonify([])
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get recent changes (last 30 days)
        cursor.execute("""
            SELECT provider, change_type, severity, title, description, url, detected_at, diff
            FROM change_events
            WHERE detected_at > datetime('now', '-30 days')
            ORDER BY detected_at DESC
            LIMIT 50
        """)
        
        changes = []
        for row in cursor.fetchall():
            changes.append({
                'provider': row['provider'],
                'change_type': row['change_type'],
                'severity': row['severity'],
                'title': row['title'],
                'description': row['description'],
                'url': row['url'],
                'detected_at': row['detected_at'],
                'diff': row['diff']
            })
        
        conn.close()
        return jsonify(changes)
        
    except Exception as e:
        logger.error(f"Error getting monitoring changes: {e}")
        return jsonify([])

@app.route('/api/monitoring/health')
def get_service_health():
    """Get current service health status"""
    try:
        db_path = "monitoring.db"
        
        if not os.path.exists(db_path):
            return jsonify([])
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get latest health status for each provider
        cursor.execute("""
            SELECT provider, endpoint, status_code, response_time_ms, is_healthy, error_message, checked_at
            FROM service_status s1
            WHERE checked_at = (
                SELECT MAX(checked_at) 
                FROM service_status s2 
                WHERE s1.provider = s2.provider AND s1.endpoint = s2.endpoint
            )
            ORDER BY provider
        """)
        
        health_status = []
        for row in cursor.fetchall():
            health_status.append({
                'provider': row['provider'],
                'endpoint': row['endpoint'],
                'status_code': row['status_code'],
                'response_time_ms': row['response_time_ms'],
                'is_healthy': bool(row['is_healthy']),
                'error_message': row['error_message'],
                'checked_at': row['checked_at']
            })
        
        conn.close()
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Error getting service health: {e}")
        return jsonify([])


@app.route('/api/comparison-matrix')
def get_comparison_matrix():
    """Get provider comparison matrix"""
    try:
        matrix = generate_provider_comparison_matrix()
        return jsonify(matrix)
    except Exception as e:
        logger.error(f"Error generating comparison matrix: {e}")
        return jsonify({'error': str(e)}), 500

# HTML Templates (would normally be in separate files)
@app.route('/templates/dashboard.html')
def dashboard_template():
    """Return dashboard HTML template"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VoiceLens Operations Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .provider-card { transition: all 0.3s ease; }
        .provider-card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); }
        .status-indicator.healthy { background-color: #10B981; }
        .status-indicator.unhealthy { background-color: #EF4444; }
        .status-indicator { width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <div class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center py-4">
                <div class="flex items-center space-x-4">
                    <h1 class="text-2xl font-bold text-gray-900">🎙️ VoiceLens Operations</h1>
                    <span class="bg-blue-100 text-blue-800 text-sm font-medium px-2.5 py-0.5 rounded">Internal Dashboard</span>
                </div>
                <div class="flex space-x-2">
                    <button id="refresh-btn" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium">
                        Refresh Data
                    </button>
                </div>
            </div>
        </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <!-- Stats Overview -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="text-2xl">🏢</div>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">Total Providers</dt>
                                <dd class="text-lg font-medium text-gray-900" id="total-providers">-</dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="text-2xl">🔄</div>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">Active Monitoring</dt>
                                <dd class="text-lg font-medium text-gray-900" id="active-monitors">-</dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="text-2xl">📊</div>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">VCP Transformations</dt>
                                <dd class="text-lg font-medium text-gray-900" id="total-transformations">-</dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="text-2xl">✅</div>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">Test Success Rate</dt>
                                <dd class="text-lg font-medium text-gray-900" id="success-rate">-</dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tab Navigation -->
        <div class="border-b border-gray-200 mb-6">
            <nav class="-mb-px flex space-x-8" aria-label="Tabs">
                <button class="tab-btn border-blue-500 text-blue-600 whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm" data-tab="providers">
                    Providers
                </button>
                <button class="tab-btn border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm" data-tab="monitoring">
                    Monitoring
                </button>
                <button class="tab-btn border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm" data-tab="testing">
                    Webhook Testing
                </button>
                <button class="tab-btn border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm" data-tab="analytics">
                    Analytics
                </button>
            </nav>
        </div>

        <!-- Tab Content -->
        <div id="providers-tab" class="tab-content">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="providers-grid">
                <!-- Provider cards will be loaded here -->
            </div>
        </div>

        <div id="monitoring-tab" class="tab-content hidden">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="bg-white shadow rounded-lg p-6">
                    <h3 class="text-lg font-medium text-gray-900 mb-4">Recent Changes</h3>
                    <div id="recent-changes" class="space-y-4">
                        <!-- Recent changes will be loaded here -->
                    </div>
                </div>
                <div class="bg-white shadow rounded-lg p-6">
                    <h3 class="text-lg font-medium text-gray-900 mb-4">Service Health</h3>
                    <div id="service-health" class="space-y-4">
                        <!-- Service health will be loaded here -->
                    </div>
                </div>
            </div>
        </div>

        <div id="testing-tab" class="tab-content hidden">
            <div class="bg-white shadow rounded-lg p-6">
                <h3 class="text-lg font-medium text-gray-900 mb-4">Webhook Testing</h3>
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Provider</label>
                        <select id="test-provider" class="block w-full border-gray-300 rounded-md shadow-sm">
                            <option value="">Select a provider</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Test Type</label>
                        <select id="test-type" class="block w-full border-gray-300 rounded-md shadow-sm">
                            <option value="payload">Payload Transformation</option>
                            <option value="signature">Signature Validation</option>
                        </select>
                    </div>
                </div>
                <div class="mt-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Webhook Payload (JSON)</label>
                    <textarea id="test-payload" rows="10" class="block w-full border-gray-300 rounded-md shadow-sm font-mono text-sm" placeholder="Enter webhook payload JSON here..."></textarea>
                </div>
                <div class="mt-4 flex justify-between">
                    <button id="load-example" class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm font-medium">
                        Load Example
                    </button>
                    <button id="test-webhook" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium">
                        Run Test
                    </button>
                </div>
                <div id="test-results" class="mt-6 hidden">
                    <h4 class="text-md font-medium text-gray-900 mb-2">Test Results</h4>
                    <pre id="test-output" class="bg-gray-100 p-4 rounded-md text-sm overflow-auto max-h-96"></pre>
                </div>
            </div>
        </div>

        <div id="analytics-tab" class="tab-content hidden">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="bg-white shadow rounded-lg p-6">
                    <h3 class="text-lg font-medium text-gray-900 mb-4">Transformation Performance</h3>
                    <canvas id="performance-chart" width="400" height="200"></canvas>
                </div>
                <div class="bg-white shadow rounded-lg p-6">
                    <h3 class="text-lg font-medium text-gray-900 mb-4">Test Success Rates</h3>
                    <canvas id="success-chart" width="400" height="200"></canvas>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Application state
        let providers = [];
        let currentTab = 'providers';

        // Initialize app
        document.addEventListener('DOMContentLoaded', function() {
            loadProviders();
            setupTabSwitching();
            setupEventHandlers();
            loadDashboardData();
        });

        // Tab switching
        function setupTabSwitching() {
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const tabName = this.dataset.tab;
                    switchTab(tabName);
                });
            });
        }

        function switchTab(tabName) {
            // Update tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('border-blue-500', 'text-blue-600');
                btn.classList.add('border-transparent', 'text-gray-500');
            });
            
            document.querySelector(`[data-tab="${tabName}"]`).classList.remove('border-transparent', 'text-gray-500');
            document.querySelector(`[data-tab="${tabName}"]`).classList.add('border-blue-500', 'text-blue-600');

            // Update content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.add('hidden');
            });
            
            document.getElementById(`${tabName}-tab`).classList.remove('hidden');
            currentTab = tabName;

            // Load tab-specific data
            if (tabName === 'monitoring') {
                loadMonitoringData();
            } else if (tabName === 'analytics') {
                loadAnalyticsData();
            }
        }

        // Event handlers
        function setupEventHandlers() {
            document.getElementById('refresh-btn').addEventListener('click', refreshAllData);
            document.getElementById('test-webhook').addEventListener('click', runWebhookTest);
            document.getElementById('load-example').addEventListener('click', loadExamplePayload);
        }

        // Load providers
        async function loadProviders() {
            try {
                const response = await fetch('/api/providers');
                providers = await response.json();
                renderProviders();
                populateProviderSelect();
                updateStats();
            } catch (error) {
                console.error('Error loading providers:', error);
            }
        }

        function renderProviders() {
            const grid = document.getElementById('providers-grid');
            grid.innerHTML = providers.map(provider => `
                <div class="provider-card bg-white shadow rounded-lg p-6 cursor-pointer" onclick="viewProvider('${provider.name}')">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-medium text-gray-900">${provider.name}</h3>
                        <span class="status-indicator ${provider.status_page ? 'healthy' : 'unknown'}"></span>
                    </div>
                    <p class="text-sm text-gray-600 mb-2">Company: ${provider.company}</p>
                    <p class="text-sm text-gray-600 mb-2">Events: ${provider.supported_events.length}</p>
                    <p class="text-sm text-gray-600 mb-4">VCP Fields: ${provider.vcp_mapping_fields}</p>
                    <div class="flex justify-between text-xs text-gray-500">
                        <span>Auth: ${provider.webhook_auth.method || 'None'}</span>
                        <span>Updated: ${provider.last_updated ? new Date(provider.last_updated).toLocaleDateString() : 'Never'}</span>
                    </div>
                </div>
            `).join('');
        }

        function populateProviderSelect() {
            const select = document.getElementById('test-provider');
            select.innerHTML = '<option value="">Select a provider</option>' + 
                providers.map(p => `<option value="${p.name.toLowerCase().replace(/\\s+/g, '_')}">${p.name}</option>`).join('');
        }

        // Load dashboard data
        async function loadDashboardData() {
            try {
                const [transformStats, testResults] = await Promise.all([
                    fetch('/api/analytics/transformation-stats').then(r => r.json()),
                    fetch('/api/analytics/test-results').then(r => r.json())
                ]);

                document.getElementById('total-providers').textContent = providers.length;
                document.getElementById('active-monitors').textContent = providers.filter(p => p.status_page).length;
                document.getElementById('total-transformations').textContent = transformStats.total_transformations || 0;
                
                const overallSuccessRate = testResults.test_summary ? 
                    testResults.test_summary.reduce((acc, test) => acc + test.success_rate, 0) / testResults.test_summary.length : 0;
                document.getElementById('success-rate').textContent = `${overallSuccessRate.toFixed(1)}%`;
                
            } catch (error) {
                console.error('Error loading dashboard data:', error);
            }
        }

        // Load monitoring data
        async function loadMonitoringData() {
            try {
                const [changes, health] = await Promise.all([
                    fetch('/api/monitoring/changes').then(r => r.json()),
                    fetch('/api/monitoring/health').then(r => r.json())
                ]);

                // Render recent changes
                const changesContainer = document.getElementById('recent-changes');
                if (changes.length > 0) {
                    changesContainer.innerHTML = changes.slice(0, 10).map(change => `
                        <div class="border-l-4 ${getSeverityColor(change.severity)} bg-gray-50 p-4">
                            <div class="flex justify-between items-start">
                                <div>
                                    <p class="text-sm font-medium text-gray-900">${change.title}</p>
                                    <p class="text-sm text-gray-600">${change.provider} - ${change.change_type}</p>
                                    <p class="text-xs text-gray-500">${new Date(change.detected_at).toLocaleString()}</p>
                                </div>
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityBadge(change.severity)}">
                                    ${change.severity}
                                </span>
                            </div>
                        </div>
                    `).join('');
                } else {
                    changesContainer.innerHTML = '<p class="text-gray-500">No recent changes detected.</p>';
                }

                // Render service health
                const healthContainer = document.getElementById('service-health');
                if (health.length > 0) {
                    healthContainer.innerHTML = health.map(service => `
                        <div class="flex items-center justify-between p-3 border rounded">
                            <div>
                                <p class="text-sm font-medium text-gray-900">${service.provider}</p>
                                <p class="text-xs text-gray-500">${service.endpoint}</p>
                            </div>
                            <div class="text-right">
                                <span class="status-indicator ${service.is_healthy ? 'healthy' : 'unhealthy'}"></span>
                                <span class="text-sm ${service.is_healthy ? 'text-green-600' : 'text-red-600'}">${service.is_healthy ? 'Healthy' : 'Unhealthy'}</span>
                                <p class="text-xs text-gray-500">${service.response_time_ms?.toFixed(0)}ms</p>
                            </div>
                        </div>
                    `).join('');
                } else {
                    healthContainer.innerHTML = '<p class="text-gray-500">No service health data available.</p>';
                }

            } catch (error) {
                console.error('Error loading monitoring data:', error);
            }
        }

        // Load analytics data and render charts
        async function loadAnalyticsData() {
            try {
                const [transformStats, testResults] = await Promise.all([
                    fetch('/api/analytics/transformation-stats').then(r => r.json()),
                    fetch('/api/analytics/test-results').then(r => r.json())
                ]);

                renderPerformanceChart(transformStats);
                renderSuccessChart(testResults);
            } catch (error) {
                console.error('Error loading analytics data:', error);
            }
        }

        function renderPerformanceChart(stats) {
            const ctx = document.getElementById('performance-chart').getContext('2d');
            const providerNames = Object.keys(stats.provider_breakdown || {});
            const avgTimes = providerNames.map(name => stats.provider_breakdown[name].avg_time_ms);

            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: providerNames,
                    datasets: [{
                        label: 'Avg Transformation Time (ms)',
                        data: avgTimes,
                        backgroundColor: 'rgba(59, 130, 246, 0.6)',
                        borderColor: 'rgba(59, 130, 246, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        }

        function renderSuccessChart(testResults) {
            const ctx = document.getElementById('success-chart').getContext('2d');
            const testData = testResults.test_summary || [];
            const providers = [...new Set(testData.map(t => t.provider))];
            const successRates = providers.map(provider => {
                const providerTests = testData.filter(t => t.provider === provider);
                return providerTests.reduce((acc, test) => acc + test.success_rate, 0) / providerTests.length;
            });

            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: providers,
                    datasets: [{
                        data: successRates,
                        backgroundColor: [
                            'rgba(34, 197, 94, 0.6)',
                            'rgba(59, 130, 246, 0.6)',
                            'rgba(168, 85, 247, 0.6)',
                            'rgba(251, 191, 36, 0.6)',
                            'rgba(239, 68, 68, 0.6)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        }

        // Webhook testing
        async function runWebhookTest() {
            const provider = document.getElementById('test-provider').value;
            const testType = document.getElementById('test-type').value;
            const payload = document.getElementById('test-payload').value;

            if (!provider || !payload) {
                alert('Please select a provider and enter a payload');
                return;
            }

            try {
                const payloadObj = JSON.parse(payload);
                const response = await fetch('/api/webhook-test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ provider, payload: payloadObj })
                });

                const result = await response.json();
                showTestResults(result);
            } catch (error) {
                showTestResults({ error: error.message });
            }
        }

        async function loadExamplePayload() {
            const provider = document.getElementById('test-provider').value;
            if (!provider) {
                alert('Please select a provider first');
                return;
            }

            try {
                const response = await fetch(`/api/providers/${provider}`);
                const providerData = await response.json();
                
                if (providerData.webhook_schemas && providerData.webhook_schemas.length > 0) {
                    const example = providerData.webhook_schemas[0].example_payload;
                    document.getElementById('test-payload').value = JSON.stringify(example, null, 2);
                } else {
                    // Fallback examples for providers
                    const fallbackExamples = {
                        'assistable': {
                            "call_id": "assistable_demo_123",
                            "call_type": "outbound_sales",
                            "direction": "outbound",
                            "to": "+1234567890",
                            "from": "+1987654321",
                            "user_sentiment": "positive",
                            "call_summary": "Customer showed interest in AI solutions",
                            "call_completion": true,
                            "assistant_task_completion": true,
                            "call_time_seconds": 185,
                            "start_timestamp": 1703001600,
                            "end_timestamp": 1703001785,
                            "full_transcript": "Assistant: Hello! How can I help you today?\nCustomer: Hi, I'm interested in your AI solutions.",
                            "extractions": {
                                "customer_interest_level": "high",
                                "product_interest": "ai_solutions",
                                "budget_range": "$1000+",
                                "decision_maker": true,
                                "purchase_timeline": "within_30_days"
                            }
                        }
                    };
                    
                    if (fallbackExamples[provider]) {
                        document.getElementById('test-payload').value = JSON.stringify(fallbackExamples[provider], null, 2);
                    } else {
                        alert('No example payload available for this provider');
                    }
                }
            } catch (error) {
                console.error('Error loading example:', error);
                alert('Error loading example payload');
            }
        }

        function showTestResults(result) {
            const resultsDiv = document.getElementById('test-results');
            const output = document.getElementById('test-output');
            
            resultsDiv.classList.remove('hidden');
            output.textContent = JSON.stringify(result, null, 2);
        }

        // Utility functions
        function getSeverityColor(severity) {
            const colors = {
                'low': 'border-green-400',
                'medium': 'border-yellow-400',
                'high': 'border-orange-400',
                'critical': 'border-red-400'
            };
            return colors[severity] || 'border-gray-400';
        }

        function getSeverityBadge(severity) {
            const badges = {
                'low': 'bg-green-100 text-green-800',
                'medium': 'bg-yellow-100 text-yellow-800',
                'high': 'bg-orange-100 text-orange-800',
                'critical': 'bg-red-100 text-red-800'
            };
            return badges[severity] || 'bg-gray-100 text-gray-800';
        }

        function viewProvider(providerName) {
            // This would open a detailed provider view
            alert(`Provider details for ${providerName} - Feature coming soon!`);
        }

        function refreshAllData() {
            location.reload();
        }
    </script>
</body>
</html>
    """

# Initialize database
init_db()

if __name__ == '__main__':
    # Run the application
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
