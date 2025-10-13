-- VoiceLens Seeder Database Schema v1.0
-- Optimized for VCP 0.3 data storage and GTM analytics

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 134217728; -- 128MB

-- Schema versioning and migrations
CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    migration_sql TEXT,
    rollback_sql TEXT
);

-- Run tracking and audit
CREATE TABLE IF NOT EXISTS seeder_runs (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    finished_at TEXT,
    profile_name TEXT,
    vcp_mode TEXT DEFAULT 'gtm', -- 'gtm' or 'full'
    seed_count INTEGER DEFAULT 0,
    normalize_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    git_sha TEXT,
    version TEXT,
    status TEXT DEFAULT 'running', -- 'running', 'completed', 'failed'
    notes TEXT
);

-- Raw VCP payloads (source of truth)
CREATE TABLE IF NOT EXISTS vcp_raw (
    vcp_id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES seeder_runs(id) ON DELETE SET NULL,
    call_id TEXT NOT NULL, -- From VCP payload
    vcp_version TEXT NOT NULL DEFAULT '0.3',
    payload_json TEXT NOT NULL,
    source TEXT DEFAULT 'synthetic', -- 'synthetic', 'retell', 'vapi', etc.
    provider TEXT, -- extracted from payload
    captured_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    processed INTEGER DEFAULT 0,
    UNIQUE(call_id, source)
);

-- Normalized conversation data
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY, -- Same as VCP call_id
    external_id TEXT,
    vcp_id TEXT REFERENCES vcp_raw(vcp_id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    provider TEXT, -- retell, vapi, bland, etc.
    
    -- Timing
    started_at TEXT NOT NULL,
    ended_at TEXT NOT NULL,
    duration_sec INTEGER NOT NULL,
    time_zone TEXT DEFAULT 'UTC',
    
    -- Channel and context
    channel TEXT DEFAULT 'voice', -- voice, chat, sms
    language TEXT DEFAULT 'en-US',
    session_id TEXT,
    
    -- Outcomes
    outcome TEXT, -- success, partial, filtered, failed
    outcome_reason TEXT,
    declared_intent TEXT,
    success_score REAL,
    
    -- Key metrics
    handle_time_sec INTEGER,
    transferred INTEGER DEFAULT 0,
    escalated INTEGER DEFAULT 0,
    fcr INTEGER DEFAULT 1, -- First Contact Resolution
    interruptions INTEGER DEFAULT 0,
    handoff_performed INTEGER DEFAULT 0,
    first_response_sec REAL,
    
    -- Capabilities and tools
    capabilities_invoked TEXT, -- JSON array
    tools_used TEXT, -- JSON array
    
    -- Value metrics  
    estimated_value_usd REAL DEFAULT 0,
    
    -- Perception and confidence
    caller_sentiment REAL,
    provider_confidence REAL,
    perception_gap_score REAL,
    perception_gap_class TEXT, -- aligned, mild_misalignment, significant_gap
    
    -- Audit
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    updated_at TEXT DEFAULT (datetime('now', 'utc'))
);

-- Conversation participants (agents, customers, etc.)
CREATE TABLE IF NOT EXISTS participants (
    participant_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    
    -- Identity
    role TEXT NOT NULL, -- caller, agent, supervisor, system
    agent_id TEXT,
    agent_name TEXT,
    display_name TEXT,
    
    -- Organizational context
    team TEXT,
    region TEXT,
    time_zone TEXT,
    tenure_months INTEGER,
    
    -- Classification metadata
    role_confidence REAL,
    role_source TEXT, -- declared, inferred, manual
    
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

-- Conversation turns and utterances
CREATE TABLE IF NOT EXISTS turns (
    turn_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    participant_id TEXT NOT NULL REFERENCES participants(participant_id) ON DELETE CASCADE,
    
    seq INTEGER NOT NULL, -- Turn sequence number
    started_at TEXT NOT NULL,
    ended_at TEXT NOT NULL,
    duration_sec REAL,
    
    -- Content (optional - may be redacted)
    text TEXT,
    tokens INTEGER,
    silence_ms INTEGER,
    
    -- Analysis
    sentiment REAL,
    toxicity REAL,
    keywords TEXT, -- JSON array
    ai_summary TEXT,
    
    -- Redaction tracking
    redactions_applied INTEGER DEFAULT 0,
    
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

-- Structured metrics extracted from conversations
CREATE TABLE IF NOT EXISTS metrics (
    metric_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    
    name TEXT NOT NULL, -- aht_sec, interruptions, sentiment_avg, etc.
    value REAL NOT NULL,
    unit TEXT, -- seconds, count, ratio, etc.
    dimension TEXT, -- overall, agent, caller, system
    category TEXT, -- performance, quality, experience
    
    captured_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

-- Agent role and intent classifications
CREATE TABLE IF NOT EXISTS classifications (
    classification_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    participant_id TEXT REFERENCES participants(participant_id) ON DELETE SET NULL,
    
    classifier_type TEXT NOT NULL, -- intent, role, sentiment, outcome
    classifier_version TEXT NOT NULL,
    
    predicted_label TEXT NOT NULL,
    confidence REAL NOT NULL,
    
    -- Explainability
    rules_fired TEXT, -- JSON array of rule names
    feature_weights TEXT, -- JSON object
    
    -- Ground truth comparison
    ground_truth_label TEXT,
    is_correct INTEGER,
    
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

-- Perception gaps between system confidence and human perception
CREATE TABLE IF NOT EXISTS perception_gaps (
    gap_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    
    dimension TEXT NOT NULL, -- outcome, sentiment, quality, resolution
    
    -- System perspective
    system_score REAL NOT NULL,
    system_confidence REAL NOT NULL,
    
    -- Human/caller perspective  
    human_score REAL NOT NULL,
    human_source TEXT, -- caller_reported, agent_assessed, manual_review
    
    -- Gap analysis
    gap_score REAL NOT NULL, -- abs(system_score - human_score)
    gap_class TEXT NOT NULL, -- aligned, mild_misalignment, significant_gap
    
    -- Context and drivers
    drivers TEXT, -- JSON array of gap driver objects
    explanation TEXT,
    impact_severity TEXT, -- low, medium, high, critical
    
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

-- Normalization tracking
CREATE TABLE IF NOT EXISTS normalizations (
    norm_id TEXT PRIMARY KEY,
    vcp_id TEXT NOT NULL REFERENCES vcp_raw(vcp_id) ON DELETE CASCADE,
    
    normalized_by TEXT NOT NULL, -- normalizer version/name
    status TEXT NOT NULL DEFAULT 'pending', -- pending, success, failed, partial
    
    errors TEXT, -- JSON array of error objects
    warnings TEXT, -- JSON array of warning objects
    
    records_created INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    
    started_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    finished_at TEXT
);

-- Remote endpoints for sending data
CREATE TABLE IF NOT EXISTS endpoints (
    endpoint_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    url TEXT NOT NULL,
    method TEXT DEFAULT 'POST',
    
    -- Authentication
    auth_type TEXT, -- none, bearer, basic, api_key
    headers_json TEXT, -- Additional headers as JSON
    
    -- Configuration
    enabled INTEGER DEFAULT 1,
    timeout_sec INTEGER DEFAULT 30,
    retry_attempts INTEGER DEFAULT 3,
    rate_limit_per_sec REAL DEFAULT 10,
    
    -- Status tracking
    last_used_at TEXT,
    last_status INTEGER,
    last_error TEXT,
    
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    updated_at TEXT DEFAULT (datetime('now', 'utc'))
);

-- Endpoint call logs
CREATE TABLE IF NOT EXISTS endpoint_calls (
    call_id TEXT PRIMARY KEY,
    endpoint_id TEXT REFERENCES endpoints(endpoint_id) ON DELETE SET NULL,
    run_id TEXT REFERENCES seeder_runs(id) ON DELETE SET NULL,
    conversation_id TEXT REFERENCES conversations(conversation_id) ON DELETE SET NULL,
    
    -- Request details
    request_method TEXT NOT NULL,
    request_url TEXT NOT NULL,
    request_headers TEXT, -- JSON
    request_body_size INTEGER,
    request_body_excerpt TEXT, -- First 500 chars for debugging
    
    -- Response details
    response_status INTEGER,
    response_headers TEXT, -- JSON
    response_body_size INTEGER,
    response_ms INTEGER,
    
    -- Error tracking
    error_type TEXT,
    error_message TEXT,
    retry_attempt INTEGER DEFAULT 0,
    
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

-- Configuration profiles
CREATE TABLE IF NOT EXISTS profiles (
    profile_name TEXT PRIMARY KEY,
    description TEXT,
    config_json TEXT NOT NULL,
    version TEXT DEFAULT '1.0',
    
    -- Usage tracking
    last_used_at TEXT,
    usage_count INTEGER DEFAULT 0,
    
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    updated_at TEXT DEFAULT (datetime('now', 'utc'))
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_conv_started ON conversations(started_at);
CREATE INDEX IF NOT EXISTS idx_conv_provider ON conversations(provider);
CREATE INDEX IF NOT EXISTS idx_conv_outcome ON conversations(outcome);
CREATE INDEX IF NOT EXISTS idx_conv_source ON conversations(source);
CREATE INDEX IF NOT EXISTS idx_conv_created ON conversations(created_at);

CREATE INDEX IF NOT EXISTS idx_participants_conv ON participants(conversation_id);
CREATE INDEX IF NOT EXISTS idx_participants_role ON participants(role);
CREATE INDEX IF NOT EXISTS idx_participants_agent ON participants(agent_id);

CREATE INDEX IF NOT EXISTS idx_turns_conv_seq ON turns(conversation_id, seq);
CREATE INDEX IF NOT EXISTS idx_turns_participant ON turns(participant_id);
CREATE INDEX IF NOT EXISTS idx_turns_started ON turns(started_at);

CREATE INDEX IF NOT EXISTS idx_metrics_conv ON metrics(conversation_id);
CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(name);
CREATE INDEX IF NOT EXISTS idx_metrics_category ON metrics(category);

CREATE INDEX IF NOT EXISTS idx_classifications_conv ON classifications(conversation_id);
CREATE INDEX IF NOT EXISTS idx_classifications_type ON classifications(classifier_type);
CREATE INDEX IF NOT EXISTS idx_classifications_confidence ON classifications(confidence);

CREATE INDEX IF NOT EXISTS idx_gaps_conv ON perception_gaps(conversation_id);
CREATE INDEX IF NOT EXISTS idx_gaps_dimension ON perception_gaps(dimension);
CREATE INDEX IF NOT EXISTS idx_gaps_class ON perception_gaps(gap_class);
CREATE INDEX IF NOT EXISTS idx_gaps_score ON perception_gaps(gap_score);

CREATE INDEX IF NOT EXISTS idx_vcp_call_id ON vcp_raw(call_id);
CREATE INDEX IF NOT EXISTS idx_vcp_provider ON vcp_raw(provider);
CREATE INDEX IF NOT EXISTS idx_vcp_source ON vcp_raw(source);
CREATE INDEX IF NOT EXISTS idx_vcp_captured ON vcp_raw(captured_at);

CREATE INDEX IF NOT EXISTS idx_endpoint_calls_endpoint ON endpoint_calls(endpoint_id);
CREATE INDEX IF NOT EXISTS idx_endpoint_calls_status ON endpoint_calls(response_status);
CREATE INDEX IF NOT EXISTS idx_endpoint_calls_created ON endpoint_calls(created_at);

-- Insert initial schema version
INSERT OR REPLACE INTO schema_version (version, migration_sql) 
VALUES ('1.0.0', '-- Initial schema creation');

-- Performance optimization
VACUUM;
ANALYZE;