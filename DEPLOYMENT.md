# VoiceLens Scripts Deployment Guide

This guide covers deploying the VoiceLens voice AI provider monitoring and VCP operations system.

## Overview

The VoiceLens Scripts system provides:
- **Voice Context Protocol (VCP) v0.5**: Unified schema for voice AI interactions
- **Provider Documentation**: Webhook mappings for major voice AI providers
- **Provider Monitoring**: Change detection and health monitoring system
- **Operations Dashboard**: Web-based management interface
- **VCP Validation**: Schema validation and transformation utilities

## Prerequisites

### Required
- Python 3.8+ with pip
- Git
- Modern web browser (for operations dashboard)

### Optional
- Docker (for containerized deployment)
- Nginx (for reverse proxy)
- PostgreSQL (for production database)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd voicelens-scripts

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Create Configuration

```bash
# Create environment file
cp .env.example .env

# Edit configuration
nano .env
```

### 3. Initialize Database

```bash
# Run operations app to create database tables
python voicelens_ops_app.py &
sleep 2
kill %1  # Stop after initialization

# Or initialize monitoring database
python provider_monitoring.py --init-db
```

### 4. Run Services

```bash
# Start operations dashboard
python voicelens_ops_app.py &

# Start monitoring system (in another terminal)
python provider_monitoring.py --daemon &

# Access dashboard at http://localhost:5000
```

## Configuration

### Environment Variables

Create `.env` file with the following variables:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
FLASK_DEBUG=false

# Database Configuration
DATABASE_URL=sqlite:///voicelens_ops.db
# or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/voicelens

# Monitoring Configuration  
MONITORING_INTERVAL_MINUTES=60
MONITORING_DATABASE=monitoring.db

# Notification Configuration (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=alerts@yourdomain.com
EMAIL_PASSWORD=your-app-password

# Provider API Keys (optional, for enhanced monitoring)
RETELL_API_KEY=your-retell-api-key
BLAND_API_KEY=your-bland-api-key  
VAPI_API_KEY=your-vapi-api-key
ELEVENLABS_API_KEY=your-elevenlabs-api-key
OPENAI_API_KEY=your-openai-api-key

# Security (production)
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
CORS_ORIGINS=https://yourdomain.com
```

### Advanced Configuration

For production deployments, create `config.yaml`:

```yaml
monitoring:
  interval_minutes: 30
  max_retries: 3
  timeout_seconds: 30
  
  providers:
    retell:
      enabled: true
      priority: high
      check_endpoints: ["https://api.retellai.com/health"]
      
    bland:
      enabled: true  
      priority: medium
      
    vapi:
      enabled: true
      priority: high
      
  notifications:
    slack:
      enabled: true
      channel: "#voice-ai-alerts"
      min_severity: medium
      
    email:
      enabled: true
      recipients: ["ops@company.com", "dev@company.com"]
      min_severity: high

dashboard:
  host: "0.0.0.0"
  port: 5000
  debug: false
  
  database:
    url: "postgresql://voicelens:password@localhost:5432/voicelens"
    pool_size: 10
    max_overflow: 20
    
  security:
    rate_limiting: true
    requests_per_minute: 100
    
  features:
    webhook_testing: true
    provider_comparison: true
    analytics: true
```

## Deployment Options

### Option 1: Development Deployment

For development and testing:

```bash
# Install in development mode
pip install -e .

# Run with hot reloading
export FLASK_ENV=development
export FLASK_DEBUG=true
python voicelens_ops_app.py

# Run monitoring with verbose logging  
python provider_monitoring.py --verbose --daemon
```

### Option 2: Production Deployment (systemd)

For production Linux deployments:

```bash
# Create application user
sudo useradd --system --create-home --shell /bin/false voicelens

# Install to system location
sudo mkdir -p /opt/voicelens
sudo cp -r . /opt/voicelens/
sudo chown -R voicelens:voicelens /opt/voicelens

# Install system dependencies
sudo apt update
sudo apt install -y python3-venv python3-pip nginx

# Create virtual environment
sudo -u voicelens python3 -m venv /opt/voicelens/venv
sudo -u voicelens /opt/voicelens/venv/bin/pip install -r /opt/voicelens/requirements.txt

# Create systemd service for dashboard
sudo tee /etc/systemd/system/voicelens-dashboard.service > /dev/null <<EOF
[Unit]
Description=VoiceLens Operations Dashboard
After=network.target

[Service]
Type=simple
User=voicelens
Group=voicelens
WorkingDirectory=/opt/voicelens
Environment=PATH=/opt/voicelens/venv/bin
ExecStart=/opt/voicelens/venv/bin/python voicelens_ops_app.py
Restart=always
RestartSec=10

# Environment
EnvironmentFile=/opt/voicelens/.env

# Security
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/voicelens/data

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for monitoring
sudo tee /etc/systemd/system/voicelens-monitoring.service > /dev/null <<EOF
[Unit]
Description=VoiceLens Provider Monitoring
After=network.target

[Service]
Type=simple
User=voicelens
Group=voicelens
WorkingDirectory=/opt/voicelens
Environment=PATH=/opt/voicelens/venv/bin
ExecStart=/opt/voicelens/venv/bin/python provider_monitoring.py --daemon
Restart=always
RestartSec=30

# Environment
EnvironmentFile=/opt/voicelens/.env

# Security
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/voicelens/data

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable voicelens-dashboard voicelens-monitoring
sudo systemctl start voicelens-dashboard voicelens-monitoring

# Check status
sudo systemctl status voicelens-dashboard
sudo systemctl status voicelens-monitoring
```

### Option 3: Docker Deployment

Using Docker for containerized deployment:

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash voicelens
RUN chown -R voicelens:voicelens /app
USER voicelens

# Expose ports
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Start services
CMD ["python", "voicelens_ops_app.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  voicelens-dashboard:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://voicelens:password@db:5432/voicelens
      - MONITORING_DATABASE=/data/monitoring.db
    volumes:
      - voicelens-data:/data
    depends_on:
      - db
    restart: unless-stopped

  voicelens-monitoring:
    build: .
    environment:
      - MONITORING_DATABASE=/data/monitoring.db
    volumes:
      - voicelens-data:/data
    command: ["python", "provider_monitoring.py", "--daemon"]
    restart: unless-stopped

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=voicelens
      - POSTGRES_USER=voicelens  
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - voicelens-dashboard
    restart: unless-stopped

volumes:
  voicelens-data:
  postgres-data:
```

```bash
# Deploy with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f voicelens-dashboard
docker-compose logs -f voicelens-monitoring

# Scale services
docker-compose up -d --scale voicelens-dashboard=2
```

### Option 4: Cloud Deployment

#### AWS ECS

```yaml
# ecs-task-definition.json
{
  "family": "voicelens",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "voicelens-dashboard",
      "image": "your-registry/voicelens:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/voicelens"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/voicelens",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Kubernetes

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: voicelens-dashboard
spec:
  replicas: 2
  selector:
    matchLabels:
      app: voicelens-dashboard
  template:
    metadata:
      labels:
        app: voicelens-dashboard
    spec:
      containers:
      - name: dashboard
        image: voicelens:latest
        ports:
        - containerPort: 5000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: voicelens-secrets
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: voicelens-service
spec:
  selector:
    app: voicelens-dashboard
  ports:
  - port: 80
    targetPort: 5000
  type: LoadBalancer
```

## Nginx Configuration

For production deployments behind a reverse proxy:

```nginx
# /etc/nginx/sites-available/voicelens
server {
    listen 80;
    server_name voicelens.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name voicelens.yourdomain.com;

    ssl_certificate /etc/ssl/certs/voicelens.crt;
    ssl_certificate_key /etc/ssl/private/voicelens.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.tailwindcss.com cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' cdn.tailwindcss.com;" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=voicelens:10m rate=10r/s;
    limit_req zone=voicelens burst=20 nodelay;

    # Gzip compression
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files (if serving directly)
    location /static/ {
        alias /opt/voicelens/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint (no auth)
    location /api/health {
        proxy_pass http://127.0.0.1:5000;
        access_log off;
    }
}
```

## Monitoring & Maintenance

### Health Checks

```bash
# Check service health
curl -f http://localhost:5000/api/health

# Check monitoring system
curl -f http://localhost:5000/api/monitoring/health

# Check database connectivity
python -c "from voicelens_ops_app import db; print('DB OK' if db else 'DB Failed')"
```

### Log Management

```bash
# Application logs (systemd)
sudo journalctl -u voicelens-dashboard -f
sudo journalctl -u voicelens-monitoring -f

# Rotate logs
sudo tee /etc/logrotate.d/voicelens > /dev/null <<EOF
/opt/voicelens/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0644 voicelens voicelens
    postrotate
        systemctl reload voicelens-dashboard voicelens-monitoring
    endscript
}
EOF
```

### Database Maintenance

```bash
# Backup database
pg_dump voicelens > voicelens_backup_$(date +%Y%m%d).sql

# Cleanup old monitoring data (older than 90 days)
python -c "
from provider_monitoring import VoiceLensMonitoringSystem
monitor = VoiceLensMonitoringSystem()
monitor.cleanup_old_data(days=90)
print('Cleanup completed')
"

# Vacuum database
python -c "
import sqlite3
conn = sqlite3.connect('monitoring.db')
conn.execute('VACUUM')
conn.close()
print('Database vacuumed')
"
```

### Updates

```bash
# Update VoiceLens scripts
cd /opt/voicelens
git pull origin main

# Update Python dependencies  
sudo -u voicelens /opt/voicelens/venv/bin/pip install -r requirements.txt

# Restart services
sudo systemctl restart voicelens-dashboard voicelens-monitoring

# Verify deployment
curl -f http://localhost:5000/api/health
```

## Security Considerations

### Network Security
- Use HTTPS in production with proper SSL certificates
- Configure firewall to only allow necessary ports (80, 443)
- Use VPN or private networks for internal access
- Enable rate limiting and DDoS protection

### Application Security
- Change default secret keys and passwords
- Use environment variables for sensitive configuration
- Enable CORS only for trusted origins
- Implement proper authentication for admin features
- Regular security updates and dependency scanning

### Data Protection
- Encrypt sensitive data at rest
- Use hashed IP addresses for privacy
- Implement data retention policies
- Ensure GDPR/CCPA compliance for user data
- Regular database backups with encryption

## Troubleshooting

### Common Issues

1. **Port Already in Use**
```bash
# Check what's using the port
sudo lsof -i :5000
# Kill the process or change port
export FLASK_RUN_PORT=5001
```

2. **Database Connection Failed**
```bash
# Check database status
systemctl status postgresql
# Check connection string in .env file
# Verify database exists and user has permissions
```

3. **Provider Monitoring Not Working**
```bash
# Check network connectivity
curl -I https://api.retellai.com
# Verify API keys are correct
# Check monitoring logs for errors
```

4. **High Memory Usage**
```bash
# Monitor memory usage
top -p $(pgrep -f voicelens)
# Adjust monitoring intervals
# Clean up old monitoring data
```

### Support

- **Documentation**: Check this deployment guide and README files
- **Logs**: Review application and system logs for errors  
- **Issues**: Report bugs and feature requests on GitHub
- **Community**: Join the VoiceLens Discord for support

---

For additional help, consult the individual module documentation:
- `vcp_v05_schema.py` - VCP schema reference
- `provider_documentation.py` - Provider integration guide
- `provider_monitoring.py` - Monitoring system configuration
- `voicelens_ops_app.py` - Operations dashboard usage