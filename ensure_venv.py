#!/usr/bin/env python3
"""
VoiceLens Virtual Environment Verification Script
Ensures that the virtual environment is properly activated before running the application.
"""

import os
import sys
import subprocess
from pathlib import Path


def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.absolute()


def get_venv_path():
    """Get the path to the virtual environment."""
    return get_project_root() / "venv"


def is_venv_activated():
    """Check if the virtual environment is currently activated."""
    venv_path = get_venv_path()
    virtual_env = os.environ.get('VIRTUAL_ENV')
    
    if virtual_env:
        return Path(virtual_env) == venv_path
    return False


def get_python_executable():
    """Get the correct Python executable path."""
    if is_venv_activated():
        return sys.executable
    else:
        venv_python = get_venv_path() / "bin" / "python"
        return str(venv_python) if venv_python.exists() else None


def verify_dependencies():
    """Verify that key dependencies are available."""
    try:
        import flask
        import pydantic
        import requests
        import flask_sqlalchemy
        import flask_cors
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False


def get_entry_points():
    """Find available application entry points."""
    project_root = get_project_root()
    entry_points = []
    
    # Check for VoiceLens-specific entry points first
    if (project_root / "deploy_local_prod.py").exists():
        entry_points.append("deploy_local_prod.py")
    if (project_root / "voicelens_ops_app.py").exists():
        entry_points.append("voicelens_ops_app.py")
    
    # Check for standard entry points
    if (project_root / "app.py").exists():
        entry_points.append("app.py")
    if (project_root / "main.py").exists():
        entry_points.append("main.py")
    
    return entry_points


def main():
    """Main verification function."""
    print("🔍 VoiceLens Environment Verification")
    print("=" * 40)
    
    project_root = get_project_root()
    venv_path = get_venv_path()
    
    print(f"📁 Project root: {project_root}")
    print(f"🐍 Virtual environment: {venv_path}")
    
    # Check if venv exists
    if not venv_path.exists():
        print("❌ Virtual environment not found!")
        print("   Run: python3 -m venv venv")
        return False
    
    # Check if venv is activated
    if is_venv_activated():
        print("✅ Virtual environment is activated")
    else:
        print("⚠️  Virtual environment is not activated")
        print("   Run: source venv/bin/activate")
        return False
    
    # Verify Python executable
    python_exe = get_python_executable()
    if python_exe:
        print(f"🐍 Python executable: {python_exe}")
    else:
        print("❌ Python executable not found in virtual environment")
        return False
    
    # Verify dependencies
    if verify_dependencies():
        print("✅ All key dependencies are available")
    else:
        print("❌ Some dependencies are missing")
        print("   Run: pip install -r requirements.txt")
        return False
    
    # Check for application entry points
    entry_points = get_entry_points()
    if entry_points:
        print(f"✅ Found application entry points: {', '.join(entry_points)}")
        print(f"🎯 Recommended: {entry_points[0]}")
    else:
        print("⚠️  No recognized application entry points found")
        print("   Expected: deploy_local_prod.py, voicelens_ops_app.py, app.py, or main.py")
        return False
    
    print("\n🚀 Environment is ready for VoiceLens deployment!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)