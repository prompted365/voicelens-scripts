#!/usr/bin/env python3
"""
VoiceLens Local Production Deployment Script
Deploys the VoiceLens system locally with production configuration
"""
import os
import sys
import subprocess
import signal
import time
from pathlib import Path

def setup_environment():
    """Setup production environment"""
    print("🔧 Setting up production environment...")
    
    # Create data directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Set environment variables for production
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'false'
    os.environ['HOST'] = '0.0.0.0'
    os.environ['PORT'] = '8080'
    
    print("✅ Environment configured for production")

def initialize_databases():
    """Initialize production databases"""
    print("🗄️  Initializing databases...")
    
    try:
        # Initialize operations database
        from voicelens_ops_app import app, db
        with app.app_context():
            db.create_all()
        print("✅ Operations database initialized")
        
        # Initialize monitoring database
        from provider_monitoring import VoiceLensMonitoringSystem
        monitor = VoiceLensMonitoringSystem()
        print("✅ Monitoring database initialized")
        
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def start_dashboard():
    """Start the VoiceLens operations dashboard"""
    print("🚀 Starting VoiceLens Operations Dashboard...")
    print("   • Host: 0.0.0.0 (all interfaces)")
    print("   • Port: 8080")
    print("   • Mode: Production")
    print("   • Auth Required: NO (open webhooks)")
    print("   • Debug: Disabled")
    print("")
    print("🌐 Dashboard will be available at:")
    print("   • http://localhost:8080")
    print("   • http://127.0.0.1:8080")  
    print("   • http://[your-ip]:8080")
    print("")
    print("📡 Webhook Endpoints:")
    print("   • POST /api/webhook-test - Test webhook transformations")
    print("   • GET  /api/providers - List all supported providers")
    print("   • GET  /api/providers/{name} - Get provider details")
    print("")
    print("🔓 Authorization Status:")
    print("   • Vapi: NO auth required")
    print("   • OpenAI Realtime API: NO auth required") 
    print("   • Bland AI: Optional Bearer token")
    print("   • Assistable AI: Optional API key")
    print("   • Retell AI: Signature required (but optional validation)")
    print("   • ElevenLabs: HMAC signature required (but optional validation)")
    print("")
    print("Press Ctrl+C to stop...")
    print("=" * 60)
    
    try:
        from voicelens_ops_app import app
        # Run in production mode
        app.run(
            host='0.0.0.0',
            port=8080,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down VoiceLens...")
        print("✅ Goodbye!")

def main():
    """Main deployment function"""
    print("🎙️  VoiceLens Local Production Deployment")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("voicelens_ops_app.py").exists():
        print("❌ Error: voicelens_ops_app.py not found")
        print("Please run this script from the VoiceLens scripts directory")
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Initialize databases
    if not initialize_databases():
        sys.exit(1)
    
    # Test the system
    print("🧪 Running integration tests...")
    try:
        from provider_documentation import VoiceAIProviderRegistry
        registry = VoiceAIProviderRegistry()
        providers = registry.get_all_providers()
        print(f"✅ {len(providers)} providers loaded successfully")
        
        # Test Assistable.ai specifically
        assistable = registry.get_provider('assistable')
        if assistable:
            print(f"✅ Assistable.ai integration ready")
        else:
            print("⚠️  Assistable.ai not found")
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        sys.exit(1)
    
    print("✅ All systems ready!")
    print("")
    
    # Start the dashboard
    start_dashboard()

if __name__ == "__main__":
    main()