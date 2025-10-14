# VoiceLens Environment Management

This directory contains scripts and configuration for managing the VoiceLens virtual environment consistently across deployments.

## Files Overview

- `requirements.txt` - Python dependencies (no version constraints for flexible resolution)
- `activate_env.sh` - Simple environment activation script
- `activate_and_deploy.sh` - Full deployment script with environment setup
- `ensure_venv.py` - Python script to verify environment status
- `venv/` - Virtual environment directory
- `deploy_local_prod.py` - 🎯 **Recommended** - Production deployment script
- `voicelens_ops_app.py` - Main Flask application (VoiceLens Operations Dashboard)

## Quick Start

### 1. Activate Environment (Manual)
```bash
source venv/bin/activate
```

### 2. Activate Environment (Script)
```bash
source activate_env.sh
```

### 3. Full Deployment (Automatic)
```bash
./activate_and_deploy.sh
```

### 4. VoiceLens Production Deployment (Recommended)
```bash
# Activate environment first
source activate_env.sh

# Run production deployment
python deploy_local_prod.py
```

### 4. Verify Environment (Python)
```bash
python ensure_venv.py
```

## Environment Scripts

### `activate_env.sh`
- Sources the virtual environment
- Creates venv if it doesn't exist
- Installs dependencies if needed
- Sets Flask environment variables

**Usage:**
```bash
source activate_env.sh  # Note: must be sourced, not executed
```

### `activate_and_deploy.sh`
- Full deployment script
- Creates/activates virtual environment
- Installs/updates dependencies
- Starts the VoiceLens application
- Uses port 8080 by default (avoids macOS AirPlay port 5000)

**Usage:**
```bash
./activate_and_deploy.sh
# Or with custom port:
PORT=9000 ./activate_and_deploy.sh
```

### `ensure_venv.py`
- Verifies virtual environment status
- Checks Python executable path
- Validates key dependencies
- Returns exit code 0 on success, 1 on failure

**Usage:**
```bash
python ensure_venv.py
```

## Port Configuration

By default, the deployment script uses port 8080 to avoid conflicts with macOS AirPlay Receiver (which uses port 5000). You can override this:

```bash
PORT=9000 ./activate_and_deploy.sh
```

## Dependency Management

The `requirements.txt` file uses flexible version resolution:
- No upper bounds to avoid dependency conflicts
- No lower bounds to allow latest compatible versions
- Let pip resolve the best versions automatically

To update dependencies:
```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

## Troubleshooting

### Virtual Environment Not Found
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Port Conflicts
If port 8080 is already in use, specify a different port:
```bash
# Use different port
PORT=9000 ./activate_and_deploy.sh

# Or check what's using a specific port
lsof -i :8080
```

### Dependencies Missing
```bash
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Environment Variables

The scripts set these environment variables:
- `FLASK_APP=deploy_local_prod.py` (or voicelens_ops_app.py)
- `FLASK_ENV=production` 
- `PORT=8080` (or custom value)
- `VIRTUAL_ENV=/path/to/venv`

## Integration with CI/CD

For automated deployments, use the verification script:

```bash
# In your deployment pipeline
python ensure_venv.py || exit 1
./activate_and_deploy.sh
```