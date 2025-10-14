#!/usr/bin/env python3
"""
Voice AI Provider Documentation System
Comprehensive provider mapping and webhook documentation for VoiceLens
"""
import json
import requests
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from pydantic import BaseModel

class AuthMethod(str, Enum):
    """Webhook authentication methods"""
    HMAC_SHA256 = "hmac_sha256"
    BEARER_TOKEN = "bearer_token"
    IP_WHITELIST = "ip_whitelist"
    API_KEY_HEADER = "api_key_header"
    SIGNATURE_HEADER = "signature_header"

class WebhookEventType(str, Enum):
    """Common webhook event types across providers"""
    CALL_STARTED = "call_started"
    CALL_ENDED = "call_ended"
    CALL_ANALYZED = "call_analyzed"
    POST_CALL_TRANSCRIPTION = "post_call_transcription"
    POST_CALL_AUDIO = "post_call_audio"
    END_OF_CALL_REPORT = "end_of_call_report"
    STATUS_UPDATE = "status_update"
    CONVERSATION_UPDATE = "conversation_update"
    TRANSCRIPT_UPDATE = "transcript_update"

@dataclass
class WebhookAuthConfig:
    """Webhook authentication configuration"""
    method: AuthMethod
    header_name: Optional[str] = None
    secret_key_required: bool = False
    ip_addresses: List[str] = None
    validation_example: Optional[str] = None

@dataclass
class WebhookSchema:
    """Webhook payload schema definition"""
    event_type: WebhookEventType
    required_fields: List[str]
    optional_fields: List[str] = None
    nested_objects: Dict[str, List[str]] = None
    example_payload: Dict[str, Any] = None

@dataclass
class ProviderInfo:
    """Complete provider documentation"""
    name: str
    company: str
    website: str
    docs_url: str
    api_base_url: str
    status_page: Optional[str] = None
    changelog_url: Optional[str] = None
    rss_feed: Optional[str] = None
    webhook_auth: WebhookAuthConfig = None
    supported_events: List[WebhookEventType] = None
    webhook_schemas: List[WebhookSchema] = None
    vcp_mapping_rules: Dict[str, str] = None
    last_updated: datetime = None

class VoiceAIProviderRegistry:
    """Central registry for voice AI provider information"""
    
    def __init__(self):
        self.providers = self._initialize_providers()
    
    def _initialize_providers(self) -> Dict[str, ProviderInfo]:
        """Initialize provider database with research data"""
        return {
            "retell": ProviderInfo(
                name="Retell AI",
                company="Retell AI",
                website="https://www.retellai.com",
                docs_url="https://docs.retellai.com",
                api_base_url="https://api.retellai.com",
                status_page="https://status.retellai.com",
                changelog_url="https://www.retellai.com/changelog",
                webhook_auth=WebhookAuthConfig(
                    method=AuthMethod.SIGNATURE_HEADER,
                    header_name="x-retell-signature",
                    secret_key_required=True,
                    ip_addresses=["100.20.5.228"],
                    validation_example="Retell.verify(payload, api_key, signature)"
                ),
                supported_events=[
                    WebhookEventType.CALL_STARTED,
                    WebhookEventType.CALL_ENDED,
                    WebhookEventType.CALL_ANALYZED
                ],
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
                        ],
                        nested_objects={
                            "call": ["call_id", "agent_id", "call_status", "transcript", "metadata"],
                            "transcript_object": ["role", "content", "timestamp"]
                        },
                        example_payload={
                            "event": "call_ended",
                            "call": {
                                "call_id": "Jabr9TXYYJHfvl6Syypi88rdAHYHmcq6",
                                "from_number": "+12137771234",
                                "to_number": "+12137771235",
                                "direction": "inbound",
                                "start_timestamp": 1714608475945,
                                "end_timestamp": 1714608491736,
                                "disconnection_reason": "user_hangup",
                                "transcript": "Full conversation transcript...",
                                "metadata": {}
                            }
                        }
                    )
                ],
                vcp_mapping_rules={
                    "call.call_id": "call.call_id",
                    "call.from_number": "call.from_",
                    "call.to_number": "call.to",
                    "call.direction": "call.channel",
                    "call.start_timestamp": "call.start_time",
                    "call.end_timestamp": "call.end_time",
                    "call.transcript": "artifacts.transcript",
                    "event": "audit.event_type"
                },
                last_updated=datetime.now(timezone.utc)
            ),
            
            "bland": ProviderInfo(
                name="Bland AI",
                company="Bland AI",
                website="https://www.bland.ai",
                docs_url="https://docs.bland.ai",
                api_base_url="https://api.bland.ai",
                webhook_auth=WebhookAuthConfig(
                    method=AuthMethod.BEARER_TOKEN,
                    header_name="Authorization",
                    secret_key_required=False
                ),
                supported_events=[
                    WebhookEventType.CALL_ENDED,
                    WebhookEventType.POST_CALL_TRANSCRIPTION
                ],
                webhook_schemas=[
                    WebhookSchema(
                        event_type=WebhookEventType.CALL_ENDED,
                        required_fields=[
                            "call_id", "from", "to", "call_length",
                            "answered", "completed"
                        ],
                        optional_fields=[
                            "transcript", "recording_url", "pathway_logs",
                            "analysis", "concatenated_transcript"
                        ],
                        example_payload={
                            "call_id": "c47c3e15-acad-4f8b-99e7-81d529dd5dc6",
                            "from": "+12345678901",
                            "to": "+10987654321",
                            "call_length": 120,
                            "answered": True,
                            "completed": True,
                            "transcript": "AI: Hello! How can I help? User: Hi there!",
                            "recording_url": "https://storage.googleapis.com/...",
                            "analysis": {}
                        }
                    )
                ],
                vcp_mapping_rules={
                    "call_id": "call.call_id",
                    "from": "call.from_",
                    "to": "call.to",
                    "call_length": "call.duration_sec",
                    "transcript": "artifacts.transcript",
                    "recording_url": "artifacts.recording_url"
                },
                last_updated=datetime.now(timezone.utc)
            ),
            
            "vapi": ProviderInfo(
                name="Vapi",
                company="Vapi",
                website="https://vapi.ai",
                docs_url="https://docs.vapi.ai",
                api_base_url="https://api.vapi.ai",
                status_page="https://status.vapi.ai",
                supported_events=[
                    WebhookEventType.END_OF_CALL_REPORT,
                    WebhookEventType.STATUS_UPDATE,
                    WebhookEventType.CONVERSATION_UPDATE
                ],
                webhook_schemas=[
                    WebhookSchema(
                        event_type=WebhookEventType.END_OF_CALL_REPORT,
                        required_fields=[
                            "message.type", "message.call.id", 
                            "message.endedReason", "message.artifact"
                        ],
                        optional_fields=[
                            "message.artifact.transcript",
                            "message.artifact.recording", 
                            "message.artifact.messages"
                        ],
                        nested_objects={
                            "message": ["type", "call", "endedReason", "artifact"],
                            "call": ["id", "phoneNumber", "status"],
                            "artifact": ["transcript", "recording", "messages"]
                        },
                        example_payload={
                            "message": {
                                "type": "end-of-call-report",
                                "endedReason": "hangup",
                                "call": {"id": "call_123", "phoneNumber": "+1234567890"},
                                "artifact": {
                                    "transcript": "AI: How can I help? User: What's the weather?",
                                    "messages": [
                                        {"role": "assistant", "message": "How can I help?"},
                                        {"role": "user", "message": "What's the weather?"}
                                    ]
                                }
                            }
                        }
                    )
                ],
                vcp_mapping_rules={
                    "message.call.id": "call.call_id",
                    "message.endedReason": "outcomes.objective.disconnect_reason",
                    "message.artifact.transcript": "artifacts.transcript",
                    "message.artifact.recording": "artifacts.recording_url"
                },
                last_updated=datetime.now(timezone.utc)
            ),
            
            "elevenlabs": ProviderInfo(
                name="ElevenLabs",
                company="ElevenLabs",
                website="https://elevenlabs.io",
                docs_url="https://elevenlabs.io/docs",
                api_base_url="https://api.elevenlabs.io",
                status_page="https://status.elevenlabs.io",
                rss_feed="https://status.elevenlabs.io/feed.rss",
                webhook_auth=WebhookAuthConfig(
                    method=AuthMethod.HMAC_SHA256,
                    header_name="elevenlabs-signature",
                    secret_key_required=True,
                    ip_addresses=[
                        "34.67.146.145", "34.59.11.47",  # US
                        "35.204.38.71", "34.147.113.54",  # EU
                        "35.185.187.110", "35.247.157.189"  # Asia
                    ],
                    validation_example="hmac.compare_digest(signature, hmac_sha256(timestamp + payload))"
                ),
                supported_events=[
                    WebhookEventType.POST_CALL_TRANSCRIPTION,
                    WebhookEventType.POST_CALL_AUDIO
                ],
                webhook_schemas=[
                    WebhookSchema(
                        event_type=WebhookEventType.POST_CALL_TRANSCRIPTION,
                        required_fields=[
                            "type", "event_timestamp", "data.agent_id",
                            "data.conversation_id", "data.transcript"
                        ],
                        optional_fields=[
                            "data.analysis", "data.metadata", 
                            "data.conversation_initiation_client_data"
                        ],
                        nested_objects={
                            "data": ["agent_id", "conversation_id", "transcript", "metadata", "analysis"],
                            "transcript": ["role", "message", "time_in_call_secs"],
                            "metadata": ["start_time_unix_secs", "call_duration_secs", "cost"]
                        },
                        example_payload={
                            "type": "post_call_transcription",
                            "event_timestamp": 1739537297,
                            "data": {
                                "agent_id": "xyz",
                                "conversation_id": "abc",
                                "transcript": [
                                    {
                                        "role": "agent",
                                        "message": "Hello! How can I help?",
                                        "time_in_call_secs": 0
                                    }
                                ],
                                "metadata": {
                                    "start_time_unix_secs": 1739537297,
                                    "call_duration_secs": 22,
                                    "cost": 296
                                }
                            }
                        }
                    )
                ],
                vcp_mapping_rules={
                    "data.conversation_id": "call.call_id",
                    "data.agent_id": "call.agent_id",
                    "data.transcript": "artifacts.transcript_object",
                    "data.metadata.start_time_unix_secs": "call.start_time",
                    "data.metadata.call_duration_secs": "call.duration_sec"
                },
                last_updated=datetime.now(timezone.utc)
            ),
            
            "openai_realtime": ProviderInfo(
                name="OpenAI Realtime API",
                company="OpenAI",
                website="https://platform.openai.com",
                docs_url="https://platform.openai.com/docs/guides/realtime",
                api_base_url="https://api.openai.com/v1/realtime",
                status_page="https://status.openai.com",
                supported_events=[
                    WebhookEventType.STATUS_UPDATE,
                    WebhookEventType.CONVERSATION_UPDATE,
                    WebhookEventType.TRANSCRIPT_UPDATE
                ],
                webhook_schemas=[
                    WebhookSchema(
                        event_type=WebhookEventType.STATUS_UPDATE,
                        required_fields=[
                            "type", "event_id", "session"
                        ],
                        optional_fields=[
                            "previous_item_id", "item", "response"
                        ],
                        nested_objects={
                            "session": ["id", "model", "instructions", "voice"],
                            "item": ["id", "type", "status", "content"]
                        },
                        example_payload={
                            "event_id": "event_1920",
                            "type": "session.updated",
                            "session": {
                                "id": "sess_001",
                                "model": "gpt-realtime",
                                "instructions": "You are a helpful assistant."
                            }
                        }
                    )
                ],
                vcp_mapping_rules={
                    "session.id": "call.session_id",
                    "session.model": "call.model_used",
                    "item.content.transcript": "artifacts.transcript"
                },
                last_updated=datetime.now(timezone.utc)
            ),
            
            "assistable": ProviderInfo(
                name="Assistable AI",
                company="Assistable AI",
                website="https://assistable.ai",
                docs_url="https://docs.assistable.ai",
                api_base_url="https://api.assistable.ai",
                status_page="https://status.assistable.ai",
                webhook_auth=WebhookAuthConfig(
                    method=AuthMethod.API_KEY_HEADER,
                    header_name="Authorization",
                    secret_key_required=False
                ),
                supported_events=[
                    WebhookEventType.CALL_ENDED,
                    WebhookEventType.POST_CALL_TRANSCRIPTION,
                    WebhookEventType.CALL_ANALYZED
                ],
                webhook_schemas=[
                    WebhookSchema(
                        event_type=WebhookEventType.CALL_ENDED,
                        required_fields=[
                            "call_id", "call_type", "direction", "to", "from",
                            "disconnection_reason", "call_completion", "assistant_task_completion",
                            "call_time_ms", "call_time_seconds", "start_timestamp", "end_timestamp"
                        ],
                        optional_fields=[
                            "args", "metadata", "contact_id", "user_sentiment", "call_summary",
                            "call_completion_reason", "recording_url", "full_transcript",
                            "added_to_wallet", "extractions"
                        ],
                        nested_objects={
                            "args": ["contact_address_zip_code"],  # Dynamic - customizable per assistant
                            "metadata": ["contact_id", "location_id"],  # Dynamic - customizable per assistant
                            "extractions": []  # Completely dynamic - AI-extracted data
                        },
                        example_payload={
                            "args": {
                                "contact_address_zip_code": "90210"
                            },
                            "metadata": {
                                "contact_id": "contact_12345",
                                "location_id": "loc_67890"
                            },
                            "call_id": "assistable_call_abc123",
                            "call_type": "outbound_sales",
                            "direction": "outbound",
                            "to": "+1234567890",
                            "from": "+1987654321",
                            "contact_id": "contact_12345",
                            "disconnection_reason": "completed",
                            "user_sentiment": "positive",
                            "call_summary": "Customer showed interest in premium package and requested more information",
                            "call_completion": True,
                            "call_completion_reason": "task_completed",
                            "assistant_task_completion": True,
                            "recording_url": "https://storage.assistable.ai/recordings/call_abc123.mp3",
                            "call_time_ms": 185000,
                            "call_time_seconds": 185,
                            "full_transcript": "Assistant: Hello! This is Sarah from Assistable AI. How are you today?\nCustomer: Hi Sarah, I'm doing well thanks.\nAssistant: Great! I'm calling about our premium AI assistant package...",
                            "start_timestamp": 1703001600,
                            "end_timestamp": 1703001785,
                            "added_to_wallet": False,
                            "extractions": {
                                "contact_zip_code": "90210",
                                "customer_interest_level": "high",
                                "next_followup_date": "2025-10-21",
                                "product_interest": "premium_package",
                                "budget_range": "$500-1000",
                                "decision_maker": True,
                                "purchase_timeline": "within_30_days"
                            }
                        }
                    )
                ],
                vcp_mapping_rules={
                    "call_id": "call.call_id",
                    "direction": "call.channel", 
                    "to": "call.to",
                    "from": "call.from_",
                    "start_timestamp": "call.start_time",
                    "end_timestamp": "call.end_time",
                    "call_time_seconds": "call.duration_sec",
                    "full_transcript": "artifacts.transcript",
                    "recording_url": "artifacts.recording_url",
                    "call_summary": "hcr.summary",
                    "user_sentiment": "outcomes.user_satisfaction_score",
                    "call_completion": "outcomes.objective.metrics.task_completion",
                    "assistant_task_completion": "outcomes.objective.metrics.assistant_success",
                    "disconnection_reason": "outcomes.objective.status",  # Map to objective status
                    "extractions": "custom.provider_specific.assistable.extractions",
                    "args": "custom.provider_specific.assistable.call_args",
                    "metadata": "custom.provider_specific.assistable.metadata",
                    "contact_id": "call.caller_id",
                    "call_type": "custom.provider_specific.assistable.call_type"
                },
                last_updated=datetime.now(timezone.utc)
            )
        }
    
    def get_provider(self, provider_name: str) -> Optional[ProviderInfo]:
        """Get provider information by name"""
        return self.providers.get(provider_name.lower())
    
    def get_all_providers(self) -> List[ProviderInfo]:
        """Get all registered providers"""
        return list(self.providers.values())
    
    def get_providers_by_event(self, event_type: WebhookEventType) -> List[ProviderInfo]:
        """Get providers that support a specific event type"""
        return [
            provider for provider in self.providers.values()
            if provider.supported_events and event_type in provider.supported_events
        ]
    
    def validate_webhook_signature(self, provider_name: str, payload: str, 
                                 signature: str, secret: str = None) -> bool:
        """Validate webhook signature for a provider"""
        provider = self.get_provider(provider_name)
        if not provider or not provider.webhook_auth:
            return False
        
        auth_config = provider.webhook_auth
        
        if auth_config.method == AuthMethod.HMAC_SHA256:
            if provider_name == "elevenlabs":
                # ElevenLabs format: t=timestamp,v0=hash
                parts = signature.split(',')
                timestamp = parts[0].split('=')[1]
                hash_part = parts[1].split('=')[1]
                
                full_payload = f"{timestamp}.{payload}"
                calculated_hash = hmac.new(
                    secret.encode('utf-8'),
                    full_payload.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                return hmac.compare_digest(f'v0={calculated_hash}', f'v0={hash_part}')
        
        elif auth_config.method == AuthMethod.SIGNATURE_HEADER:
            if provider_name == "retell":
                # Use Retell SDK verification method
                # This would require implementing their specific verification logic
                return True  # Placeholder
        
        return False

class VCPMapper:
    """Maps provider webhooks to VCP v0.4 format"""
    
    def __init__(self, registry: VoiceAIProviderRegistry):
        self.registry = registry
    
    def map_to_vcp(self, provider_name: str, webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Map provider webhook to VCP v0.4 format"""
        provider = self.registry.get_provider(provider_name)
        if not provider or not provider.vcp_mapping_rules:
            return {}
        
        from vcp_v04_schema import VCPMessage, CallDirection, ConsentMethod, DisconnectReason
        
        vcp_data = {}
        
        # Apply mapping rules
        for provider_path, vcp_path in provider.vcp_mapping_rules.items():
            value = self._get_nested_value(webhook_payload, provider_path)
            if value is not None:
                # Special handling for Assistable.ai mappings
                if provider_name == "assistable":
                    if provider_path == "user_sentiment":
                        # Convert sentiment string to score
                        sentiment_score = self._convert_sentiment_to_score(value)
                        self._set_nested_value(vcp_data, vcp_path, sentiment_score)
                    elif provider_path == "direction":
                        # Convert direction to channel type
                        channel = self._convert_direction_to_channel(value)
                        self._set_nested_value(vcp_data, vcp_path, channel)
                    elif provider_path == "disconnection_reason":
                        # Convert disconnection reason to outcome status
                        status = self._convert_disconnection_to_status(value)
                        self._set_nested_value(vcp_data, vcp_path, status)
                    else:
                        self._set_nested_value(vcp_data, vcp_path, value)
                else:
                    self._set_nested_value(vcp_data, vcp_path, value)
        
        # Create VCP v0.5 structure with defaults
        now = datetime.now(timezone.utc)
        call_id = self._get_nested_value(vcp_data, 'call.call_id') or str(uuid.uuid4())
        session_id = self._get_nested_value(vcp_data, 'call.session_id') or f"sess_{provider_name}_{call_id[:8]}"
        
        vcp_message = {
            "vcp_version": "0.5",
            "vcp_payload": {
                "call": {
                    "call_id": call_id,
                    "session_id": session_id,
                    "provider": provider_name,
                    "start_time": now.isoformat(),
                    "end_time": now.isoformat(),
                    "duration_sec": 0,
                    "capabilities_invoked": [],
                    **vcp_data.get('call', {})
                },
                "model_selection": {
                    "policy_id": f"{provider_name}_default",
                    "resolved_at": now.isoformat(),
                    "roles": {}
                },
                "outcomes": {
                    "perceived": [],
                    "objective": {
                        "status": "unknown",
                        "scored_criteria": [],
                        "metrics": {}
                    },
                    "perception_gap": {
                        "gap_score": 0.0,
                        "gap_class": "aligned"
                    },
                    "model_outcome_attribution": {
                        "roles": {},
                        "kpis": {}
                    },
                    **vcp_data.get('outcomes', {})
                },
                "hcr": {
                    "audience": "system",
                    "headline": f"{provider_name} call processed",
                    "outcome_status": "success",
                    "key_points": [],
                    "impact_metrics": {}
                },
                "artifacts": vcp_data.get('artifacts', {}),
                "custom": {
                    "provider_specific": {
                        provider_name: self._build_provider_specific_data(provider_name, webhook_payload)
                    },
                    **(self._build_integrations_data(provider_name, webhook_payload) if provider_name == "assistable" else {})
                },
                "consent": {
                    "consent_id": f"consent_{call_id}",
                    "status": "granted",  # Default assumption for operational webhooks
                    "scope": ["recording", "analytics"],
                    "version": "1.0"
                },
                "provenance": {
                    "source_system": f"{provider_name}_webhook_api",
                    "created_at": now.isoformat(),
                    "created_by": f"{provider_name}_webhook_processor",
                    "transformation_history": [
                        f"received_from_{provider_name}_webhook",
                        "mapped_to_vcp_v0.5"
                    ],
                    "data_retention_policy": "standard_30_days",
                    "compliance_flags": []
                }
            },
            "audit": {
                "received_at": now.isoformat(),
                "schema_version": "0.5"
            }
        }
        
        return vcp_message
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any):
        """Set value in nested dictionary using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
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
    
    def _convert_direction_to_channel(self, direction: str) -> str:
        """Convert Assistable.ai direction to VCP channel type"""
        direction_mapping = {
            "inbound": "phone",
            "outbound": "phone",
            "web": "web",
            "api": "api",
            "websocket": "websocket"
        }
        return direction_mapping.get(direction.lower(), "phone")
    
    def _convert_disconnection_to_status(self, disconnection_reason: str) -> str:
        """Convert Assistable.ai disconnection reason to VCP outcome status"""
        reason = disconnection_reason.lower()
        
        if any(term in reason for term in ["completed", "success", "finished"]):
            return "success"
        elif any(term in reason for term in ["timeout", "no_answer", "busy"]):
            return "timeout"
        elif any(term in reason for term in ["error", "failed", "connection"]):
            return "error"
        elif any(term in reason for term in ["partial", "incomplete"]):
            return "partial"
        else:
            return "failure"
    
    def _build_provider_specific_data(self, provider_name: str, webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Build provider-specific custom data"""
        if provider_name == "assistable":
            return {
                "data": webhook_payload,  # Original payload
                "extractions": webhook_payload.get("extractions", {}),
                "call_args": webhook_payload.get("args", {}),
                "metadata": webhook_payload.get("metadata", {}),
                "call_type": webhook_payload.get("call_type"),
                "task_completion": {
                    "call_completed": webhook_payload.get("call_completion", False),
                    "assistant_completed": webhook_payload.get("assistant_task_completion", False),
                    "completion_reason": webhook_payload.get("call_completion_reason")
                },
                "analytics": {
                    "added_to_wallet": webhook_payload.get("added_to_wallet", False),
                    "user_sentiment_raw": webhook_payload.get("user_sentiment"),
                    "disconnection_reason": webhook_payload.get("disconnection_reason")
                }
            }
        else:
            return {"data": webhook_payload}
    
    def _build_integrations_data(self, provider_name: str, webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Build integration data from webhook payload"""
        if provider_name != "assistable":
            return {}
        
        integrations = {}
        
        # Extract CRM-like data from extractions
        extractions = webhook_payload.get("extractions", {})
        if extractions:
            # Map common business extractions to integrations
            if "customer_interest_level" in extractions or "lead_score" in extractions:
                integrations["crm_system"] = {
                    "provider": "assistable_extractions",
                    "lead_score": extractions.get("customer_interest_level", "unknown"),
                    "contact_data": {
                        key: value for key, value in extractions.items()
                        if key.startswith(("contact_", "customer_", "lead_"))
                    }
                }
            
            # Map scheduling data
            if "next_followup_date" in extractions or "appointment_" in str(extractions):
                integrations["calendar_system"] = {
                    "provider": "assistable_scheduling",
                    "next_action": extractions.get("next_followup_date"),
                    "scheduling_data": {
                        key: value for key, value in extractions.items()
                        if any(term in key.lower() for term in ["appointment", "schedule", "meeting", "followup"])
                    }
                }
            
            # Map sales/opportunity data
            sales_indicators = ["budget", "purchase", "product_interest", "decision_maker", "timeline"]
            sales_data = {
                key: value for key, value in extractions.items()
                if any(indicator in key.lower() for indicator in sales_indicators)
            }
            if sales_data:
                integrations["sales_system"] = {
                    "provider": "assistable_sales_intelligence",
                    "opportunity_data": sales_data,
                    "qualification_score": self._calculate_qualification_score(sales_data)
                }
        
        return {"integrations": integrations} if integrations else {}
    
    def _calculate_qualification_score(self, sales_data: Dict[str, Any]) -> float:
        """Calculate lead qualification score from sales data"""
        score = 0.5  # Base score
        
        # Decision maker bonus
        if sales_data.get("decision_maker") is True:
            score += 0.2
        
        # Budget indicators
        budget = sales_data.get("budget_range", "")
        if "$" in str(budget) or "budget" in str(budget).lower():
            score += 0.15
        
        # Timeline urgency
        timeline = str(sales_data.get("purchase_timeline", "")).lower()
        if "30 days" in timeline or "immediate" in timeline or "urgent" in timeline:
            score += 0.15
        elif "90 days" in timeline or "quarter" in timeline:
            score += 0.1
        
        return min(1.0, score)  # Cap at 1.0

def generate_provider_comparison_matrix() -> Dict[str, Any]:
    """Generate comparison matrix of all providers"""
    registry = VoiceAIProviderRegistry()
    providers = registry.get_all_providers()
    
    comparison = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_providers": len(providers),
        "providers": {},
        "feature_matrix": {
            "webhook_auth_methods": {},
            "supported_events": {},
            "vcp_compatibility": {}
        }
    }
    
    # Build provider comparison
    for provider in providers:
        provider_data = {
            "name": provider.name,
            "company": provider.company,
            "website": provider.website,
            "docs_url": provider.docs_url,
            "has_status_page": provider.status_page is not None,
            "has_changelog": provider.changelog_url is not None,
            "webhook_auth_method": provider.webhook_auth.method.value if provider.webhook_auth else None,
            "supported_events": [event.value for event in provider.supported_events] if provider.supported_events else [],
            "total_events": len(provider.supported_events) if provider.supported_events else 0,
            "has_vcp_mapping": provider.vcp_mapping_rules is not None,
            "mapping_fields": len(provider.vcp_mapping_rules) if provider.vcp_mapping_rules else 0
        }
        
        comparison["providers"][provider.name.lower().replace(" ", "_")] = provider_data
    
    return comparison

# Example usage and testing
if __name__ == "__main__":
    # Initialize registry
    registry = VoiceAIProviderRegistry()
    mapper = VCPMapper(registry)
    
    # Example: Map Retell webhook to VCP
    retell_webhook = {
        "event": "call_ended",
        "call": {
            "call_id": "test_call_123",
            "from_number": "+1234567890",
            "to_number": "+0987654321",
            "direction": "inbound",
            "start_timestamp": 1714608475945,
            "end_timestamp": 1714608491736,
            "transcript": "Hello, how can I help you today?",
            "disconnection_reason": "user_hangup"
        }
    }
    
    vcp_mapped = mapper.map_to_vcp("retell", retell_webhook)
    print("VCP Mapped Result:")
    print(json.dumps(vcp_mapped, indent=2))
    
    # Generate comparison matrix
    comparison = generate_provider_comparison_matrix()
    print("\nProvider Comparison Matrix:")
    print(json.dumps(comparison, indent=2))