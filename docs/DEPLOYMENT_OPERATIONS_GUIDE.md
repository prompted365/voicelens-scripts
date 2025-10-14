# VCP System Deployment & Operations Guide

## Overview

This guide provides comprehensive instructions for deploying, configuring, and operating the VCP system in production environments. It covers Docker deployment, Kubernetes orchestration, monitoring setup, and operational best practices.

## System Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB
- **Python**: 3.9+
- **Database**: PostgreSQL 12+ or SQLite 3+

### Recommended Production Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 100GB+ (SSD preferred)
- **Database**: PostgreSQL 14+ with connection pooling
- **Cache**: Redis 6+
- **Load Balancer**: nginx or similar

## Environment Configuration

### Core Environment Variables

```bash
# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8080
SERVICE_ENV=production  # development, staging, production

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/voicelens
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis Configuration (optional but recommended)
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=10

# Webhook Security
WEBHOOK_SECRET_RETELL=your_retell_webhook_secret
WEBHOOK_SECRET_ELEVENLABS=your_elevenlabs_webhook_secret
WEBHOOK_SECRET_VAPI=your_vapi_secret

# Provider API Keys
RETELL_API_KEY=your_retell_api_key
VAPI_API_KEY=your_vapi_api_key
ASSISTABLE_API_KEY=your_assistable_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
OPENAI_API_KEY=your_openai_api_key

# Monitoring Configuration
MONITORING_ENABLED=true
CRON_SCHEDULE="0 */6 * * *"  # Every 6 hours
ALERT_WEBHOOK_URL=https://hooks.slack.com/your/webhook/url

# Security
SECRET_KEY=your_secret_key_here
CORS_ORIGINS=https://yourdomain.com,https://dashboard.yourdomain.com

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json  # json, text
```

### Security Configuration

```bash
# SSL/TLS (recommended for production)
SSL_CERT_PATH=/etc/ssl/certs/voicelens.crt
SSL_KEY_PATH=/etc/ssl/private/voicelens.key

# Authentication (if implementing auth)
JWT_SECRET_KEY=your_jwt_secret
JWT_EXPIRATION_HOURS=24

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# IP Whitelisting for webhooks (comma-separated)
ALLOWED_WEBHOOK_IPS=100.20.5.228,34.67.146.145,35.204.38.71
```

## Docker Deployment

### Production Dockerfile

```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV SERVICE_ENV=production

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        cron \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN groupadd -r voicelens && useradd -r -g voicelens voicelens

# Copy application code
COPY --chown=voicelens:voicelens . .

# Set up monitoring cron jobs
COPY scripts/setup_monitoring_cron.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/setup_monitoring_cron.sh
RUN /usr/local/bin/setup_monitoring_cron.sh

# Create necessary directories
RUN mkdir -p /app/logs /app/data \
    && chown -R voicelens:voicelens /app/logs /app/data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${SERVICE_PORT:-8080}/health || exit 1

# Switch to non-root user
USER voicelens

# Expose port
EXPOSE 8080

# Start application
CMD ["python", "voicelens_ops_app.py"]
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  voicelens-app:
    build: .
    container_name: voicelens-app
    ports:
      - "8080:8080"
    environment:
      - SERVICE_HOST=0.0.0.0
      - SERVICE_PORT=8080
      - DATABASE_URL=postgresql://voicelens:password@postgres:5432/voicelens
      - REDIS_URL=redis://redis:6379/0
      - MONITORING_ENABLED=true
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    networks:
      - voicelens-network

  postgres:
    image: postgres:14-alpine
    container_name: voicelens-postgres
    environment:
      - POSTGRES_DB=voicelens
      - POSTGRES_USER=voicelens
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    networks:
      - voicelens-network

  redis:
    image: redis:7-alpine
    container_name: voicelens-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - voicelens-network

  nginx:
    image: nginx:alpine
    container_name: voicelens-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - voicelens-app
    restart: unless-stopped
    networks:
      - voicelens-network

volumes:
  postgres_data:
  redis_data:

networks:
  voicelens-network:
    driver: bridge
```

### Nginx Configuration

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream voicelens-app {
        server voicelens-app:8080;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=webhook:10m rate=10r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;

    server {
        listen 80;
        server_name yourdomain.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        # SSL Configuration
        ssl_certificate /etc/ssl/certs/voicelens.crt;
        ssl_certificate_key /etc/ssl/private/voicelens.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Security Headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Webhook endpoints (stricter rate limiting)
        location ~* ^/webhook/ {
            limit_req zone=webhook burst=5 nodelay;
            
            # IP whitelist for webhooks
            allow 100.20.5.228;      # Retell AI
            allow 34.67.146.145;     # ElevenLabs US
            allow 35.204.38.71;      # ElevenLabs EU
            deny all;

            proxy_pass http://voicelens-app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Webhook-specific timeouts
            proxy_connect_timeout 5s;
            proxy_send_timeout 10s;
            proxy_read_timeout 10s;
        }

        # API endpoints
        location ~* ^/api/ {
            limit_req zone=api burst=10 nodelay;

            proxy_pass http://voicelens-app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # CORS headers
            add_header Access-Control-Allow-Origin "https://dashboard.yourdomain.com" always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        }

        # Dashboard and static files
        location / {
            proxy_pass http://voicelens-app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Cache static files
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 30d;
                add_header Cache-Control "public, immutable";
            }
        }

        # Health check endpoint (no rate limiting)
        location /health {
            access_log off;
            proxy_pass http://voicelens-app;
        }
    }
}
```

## Kubernetes Deployment

### Namespace and ConfigMap

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: voicelens
---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: voicelens-config
  namespace: voicelens
data:
  SERVICE_HOST: "0.0.0.0"
  SERVICE_PORT: "8080"
  SERVICE_ENV: "production"
  MONITORING_ENABLED: "true"
  CRON_SCHEDULE: "0 */6 * * *"
  LOG_LEVEL: "INFO"
  LOG_FORMAT: "json"
```

### Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: voicelens-secrets
  namespace: voicelens
type: Opaque
data:
  # Base64 encoded values
  DATABASE_URL: cG9zdGdyZXNxbDovL3VzZXI6cGFzc3dvcmRAbG9jYWxob3N0OjU0MzIvdm9pY2VsZW5z
  RETELL_API_KEY: eW91cl9yZXRlbGxfYXBpX2tleQ==
  VAPI_API_KEY: eW91cl92YXBpX2FwaV9rZXk=
  WEBHOOK_SECRET_RETELL: eW91cl9yZXRlbGxfd2ViaG9va19zZWNyZXQ=
  SECRET_KEY: eW91cl9zZWNyZXRfa2V5X2hlcmU=
```

### Application Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: voicelens-app
  namespace: voicelens
spec:
  replicas: 3
  selector:
    matchLabels:
      app: voicelens-app
  template:
    metadata:
      labels:
        app: voicelens-app
    spec:
      containers:
      - name: app
        image: voicelens/app:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: voicelens-secrets
              key: DATABASE_URL
        - name: RETELL_API_KEY
          valueFrom:
            secretKeyRef:
              name: voicelens-secrets
              key: RETELL_API_KEY
        envFrom:
        - configMapRef:
            name: voicelens-config
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        volumeMounts:
        - name: logs
          mountPath: /app/logs
        - name: data
          mountPath: /app/data
      volumes:
      - name: logs
        emptyDir: {}
      - name: data
        persistentVolumeClaim:
          claimName: voicelens-data-pvc
---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: voicelens-service
  namespace: voicelens
spec:
  selector:
    app: voicelens-app
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
---
# k8s/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: voicelens-data-pvc
  namespace: voicelens
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
  storageClassName: fast-ssd
```

### Ingress Configuration

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: voicelens-ingress
  namespace: voicelens
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "60"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: voicelens-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: voicelens-service
            port:
              number: 80
```

## Database Setup

### PostgreSQL Schema

```sql
-- init.sql
-- VCP Messages Table
CREATE TABLE IF NOT EXISTS vcp_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    vcp_version VARCHAR(10) NOT NULL DEFAULT '0.5',
    raw_payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexed fields for fast querying
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_sec INTEGER,
    channel VARCHAR(20),
    direction VARCHAR(10),
    status VARCHAR(20),
    user_satisfaction_score DECIMAL(3,2),
    cost_usd DECIMAL(10,4)
);

-- Indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vcp_provider_created ON vcp_messages(provider, created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vcp_call_id ON vcp_messages(call_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vcp_status ON vcp_messages(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vcp_timerange ON vcp_messages(start_time, end_time);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vcp_provider_status ON vcp_messages(provider, status);

-- Provider Analytics Table
CREATE TABLE IF NOT EXISTS provider_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    total_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    failed_calls INTEGER DEFAULT 0,
    avg_duration_sec DECIMAL(10,2),
    total_cost_usd DECIMAL(10,2),
    avg_satisfaction_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(provider, date)
);

-- Monitoring Changes Table
CREATE TABLE IF NOT EXISTS monitoring_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(50) NOT NULL,
    change_type VARCHAR(50) NOT NULL,
    change_data JSONB NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    severity VARCHAR(20) DEFAULT 'info'
);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_monitoring_provider_time ON monitoring_changes(provider, detected_at);

-- Analytics Views
CREATE OR REPLACE VIEW provider_daily_stats AS
SELECT 
    provider,
    DATE(created_at) as date,
    COUNT(*) as total_calls,
    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_calls,
    COUNT(CASE WHEN status != 'success' THEN 1 END) as failed_calls,
    AVG(duration_sec) as avg_duration_sec,
    SUM(cost_usd) as total_cost_usd,
    AVG(user_satisfaction_score) as avg_satisfaction_score
FROM vcp_messages 
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY provider, DATE(created_at)
ORDER BY provider, date DESC;

-- Functions for analytics
CREATE OR REPLACE FUNCTION update_provider_analytics()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO provider_analytics (
        provider, date, total_calls, successful_calls, failed_calls,
        avg_duration_sec, total_cost_usd, avg_satisfaction_score
    )
    SELECT 
        NEW.provider,
        DATE(NEW.created_at),
        1,
        CASE WHEN NEW.status = 'success' THEN 1 ELSE 0 END,
        CASE WHEN NEW.status != 'success' THEN 1 ELSE 0 END,
        NEW.duration_sec,
        NEW.cost_usd,
        NEW.user_satisfaction_score
    ON CONFLICT (provider, date) 
    DO UPDATE SET
        total_calls = provider_analytics.total_calls + 1,
        successful_calls = provider_analytics.successful_calls + 
            CASE WHEN NEW.status = 'success' THEN 1 ELSE 0 END,
        failed_calls = provider_analytics.failed_calls + 
            CASE WHEN NEW.status != 'success' THEN 1 ELSE 0 END,
        avg_duration_sec = (provider_analytics.avg_duration_sec * provider_analytics.total_calls + COALESCE(NEW.duration_sec, 0)) / (provider_analytics.total_calls + 1),
        total_cost_usd = provider_analytics.total_cost_usd + COALESCE(NEW.cost_usd, 0),
        avg_satisfaction_score = (provider_analytics.avg_satisfaction_score * provider_analytics.total_calls + COALESCE(NEW.user_satisfaction_score, 0)) / (provider_analytics.total_calls + 1),
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update analytics
CREATE TRIGGER update_analytics_trigger
    AFTER INSERT ON vcp_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_provider_analytics();
```

## Monitoring and Alerting

### Monitoring Setup Script

```bash
#!/bin/bash
# scripts/setup_monitoring_cron.sh

# Create cron job for provider monitoring
CRON_CMD="0 */6 * * * cd /app && python monitor_provider_changes.py >> /app/logs/monitoring.log 2>&1"

# Add to crontab
echo "$CRON_CMD" | crontab -

# Create log rotation
cat > /etc/logrotate.d/voicelens << EOF
/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 voicelens voicelens
    postrotate
        /usr/bin/killall -USR1 python || true
    endscript
}
EOF

echo "Monitoring cron job and log rotation configured"
```

### Health Check Endpoint

```python
# From voicelens_ops_app.py - Enhanced health check
@app.route('/health')
def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Check database connectivity
        db_status = check_database_connection()
        
        # Check Redis connectivity (if configured)
        redis_status = check_redis_connection()
        
        # Check provider API connectivity
        provider_status = check_provider_apis()
        
        # System metrics
        import psutil
        system_status = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
        
        # Overall status
        all_healthy = (
            db_status.get("healthy", False) and
            redis_status.get("healthy", True) and  # Redis is optional
            all(p.get("healthy", False) for p in provider_status.values())
        )
        
        status_code = 200 if all_healthy else 503
        
        return jsonify({
            "status": "healthy" if all_healthy else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
            "database": db_status,
            "redis": redis_status,
            "providers": provider_status,
            "system": system_status,
            "deployment_modes": ["native", "hosted_ai"]
        }), status_code
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500
```

### Prometheus Metrics

```python
# Optional: Prometheus metrics integration
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Metrics
webhook_requests_total = Counter('voicelens_webhook_requests_total', 
                                'Total webhook requests', ['provider', 'status'])
webhook_processing_time = Histogram('voicelens_webhook_processing_seconds',
                                  'Webhook processing time', ['provider'])
active_connections = Gauge('voicelens_active_connections',
                          'Active database connections')

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}
```

## Backup and Recovery

### Database Backup Script

```bash
#!/bin/bash
# scripts/backup.sh

set -e

# Configuration
DB_NAME="voicelens"
DB_USER="voicelens"
BACKUP_DIR="/app/backups"
S3_BUCKET="voicelens-backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database dump
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > $BACKUP_DIR/voicelens_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/voicelens_$DATE.sql

# Upload to S3 (optional)
if [ -n "$S3_BUCKET" ]; then
    aws s3 cp $BACKUP_DIR/voicelens_$DATE.sql.gz s3://$S3_BUCKET/database/
fi

# Clean up old backups (keep last 30 days)
find $BACKUP_DIR -name "voicelens_*.sql.gz" -mtime +30 -delete

echo "Backup completed: voicelens_$DATE.sql.gz"
```

### Recovery Procedure

```bash
#!/bin/bash
# scripts/recovery.sh

BACKUP_FILE=$1
DB_NAME="voicelens"
DB_USER="voicelens"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Stop application
kubectl scale deployment voicelens-app --replicas=0 -n voicelens

# Drop and recreate database
psql -h $DB_HOST -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
psql -h $DB_HOST -U postgres -c "CREATE DATABASE $DB_NAME;"

# Restore from backup
gunzip -c $BACKUP_FILE | psql -h $DB_HOST -U $DB_USER -d $DB_NAME

# Restart application
kubectl scale deployment voicelens-app --replicas=3 -n voicelens

echo "Recovery completed from $BACKUP_FILE"
```

## Security Best Practices

### Application Security

1. **Environment Variables**: Never commit secrets to version control
2. **Input Validation**: Validate all webhook payloads
3. **Rate Limiting**: Implement rate limiting for all endpoints
4. **IP Whitelisting**: Restrict webhook endpoints to known provider IPs
5. **HTTPS Only**: Use TLS encryption for all communications
6. **Security Headers**: Implement proper HTTP security headers

### Webhook Security

```python
# Enhanced webhook validation
def validate_webhook_request(provider: str, request):
    """Comprehensive webhook validation"""
    
    # 1. IP validation
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if not is_ip_whitelisted(provider, client_ip):
        raise SecurityError(f"Invalid IP {client_ip} for provider {provider}")
    
    # 2. Signature validation
    if not validate_webhook_signature(provider, request):
        raise SecurityError("Invalid webhook signature")
    
    # 3. Rate limiting
    if is_rate_limited(client_ip):
        raise RateLimitError("Rate limit exceeded")
    
    # 4. Payload validation
    payload = request.get_json()
    if not payload:
        raise ValidationError("Empty payload")
    
    # 5. Schema validation
    if not validate_webhook_schema(provider, payload):
        raise ValidationError("Invalid webhook schema")
    
    return True
```

## Performance Optimization

### Database Optimization

```sql
-- Performance optimization queries
ANALYZE vcp_messages;

-- Index usage monitoring
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE schemaname = 'public' 
ORDER BY idx_scan DESC;

-- Query performance monitoring
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements 
WHERE query LIKE '%vcp_messages%'
ORDER BY total_time DESC;
```

### Application Optimization

```python
# Connection pooling configuration
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Redis caching
import redis
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def get_provider_info_cached(provider_name: str):
    """Cache provider information"""
    cache_key = f"provider:{provider_name}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    provider_info = registry.get_provider(provider_name)
    if provider_info:
        redis_client.setex(cache_key, 3600, json.dumps(asdict(provider_info)))
    
    return provider_info
```

This comprehensive deployment and operations guide provides everything needed to successfully deploy, monitor, and maintain the VCP system in production environments with high availability, security, and performance.