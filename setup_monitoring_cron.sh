#!/bin/bash

# Setup cron jobs for VoiceLens provider monitoring
# This script configures automated monitoring schedules

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITOR_SCRIPT="$SCRIPT_DIR/monitor_provider_changes.py"
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python"

# Check if virtual environment exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Virtual environment not found at $PYTHON_PATH"
    echo "Please run 'source activate_env.sh' first to set up the virtual environment"
    exit 1
fi

# Check if monitor script exists
if [ ! -f "$MONITOR_SCRIPT" ]; then
    echo "❌ Monitor script not found at $MONITOR_SCRIPT"
    exit 1
fi

echo "🕐 Setting up VoiceLens provider monitoring cron jobs..."
echo "Script directory: $SCRIPT_DIR"
echo "Monitor script: $MONITOR_SCRIPT"
echo "Python path: $PYTHON_PATH"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Backup existing crontab
echo "📋 Backing up existing crontab..."
crontab -l > "$SCRIPT_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || echo "No existing crontab to backup"

# Create temporary cron file
TEMP_CRON="/tmp/voicelens_cron_$(date +%s)"

# Add existing crontab (if any) to temp file, excluding any existing voicelens monitoring jobs
crontab -l 2>/dev/null | grep -v "voicelens.*monitor" > "$TEMP_CRON" || true

# Add VoiceLens monitoring jobs
echo "" >> "$TEMP_CRON"
echo "# VoiceLens Provider Monitoring Jobs" >> "$TEMP_CRON"
echo "# Check for provider changes every 2 hours" >> "$TEMP_CRON"
echo "0 */2 * * * cd $SCRIPT_DIR && $PYTHON_PATH $MONITOR_SCRIPT >> $SCRIPT_DIR/logs/cron_monitor.log 2>&1" >> "$TEMP_CRON"

echo "# Run intensive documentation diff check once daily at 2 AM" >> "$TEMP_CRON"
echo "0 2 * * * cd $SCRIPT_DIR && $PYTHON_PATH $MONITOR_SCRIPT --detailed >> $SCRIPT_DIR/logs/cron_detailed.log 2>&1" >> "$TEMP_CRON"

echo "# RSS feed check every 30 minutes during business hours (9-18)" >> "$TEMP_CRON"
echo "*/30 9-18 * * * cd $SCRIPT_DIR && $PYTHON_PATH -c \"from monitor_provider_changes import ProviderMonitor; ProviderMonitor().check_rss_feeds()\" >> $SCRIPT_DIR/logs/cron_rss.log 2>&1" >> "$TEMP_CRON"

# Install the new crontab
echo "⚙️  Installing new crontab..."
crontab "$TEMP_CRON"

# Clean up temp file
rm "$TEMP_CRON"

# Create log rotation script
cat > "$SCRIPT_DIR/rotate_monitor_logs.sh" << 'EOF'
#!/bin/bash
# Log rotation for VoiceLens monitoring
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/logs"

# Keep only last 30 days of logs
find "$LOGS_DIR" -name "*.log" -type f -mtime +30 -delete

# Rotate large log files
for log in "$LOGS_DIR"/*.log; do
    if [ -f "$log" ] && [ $(stat -f%z "$log" 2>/dev/null || stat -c%s "$log" 2>/dev/null) -gt 10485760 ]; then
        # Rotate if > 10MB
        mv "$log" "${log}.$(date +%Y%m%d)"
        touch "$log"
    fi
done
EOF

chmod +x "$SCRIPT_DIR/rotate_monitor_logs.sh"

# Add log rotation to crontab
TEMP_CRON="/tmp/voicelens_cron_$(date +%s)"
crontab -l > "$TEMP_CRON"
echo "# Log rotation for VoiceLens monitoring - weekly on Sundays at 3 AM" >> "$TEMP_CRON"
echo "0 3 * * 0 $SCRIPT_DIR/rotate_monitor_logs.sh >> $SCRIPT_DIR/logs/cron_rotation.log 2>&1" >> "$TEMP_CRON"
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo "✅ Cron jobs installed successfully!"
echo ""
echo "📅 Monitoring schedule:"
echo "  • Provider changes: Every 2 hours"
echo "  • Detailed analysis: Daily at 2:00 AM"
echo "  • RSS feeds: Every 30 minutes (9 AM - 6 PM)"
echo "  • Log rotation: Weekly on Sundays at 3:00 AM"
echo ""
echo "📁 Log locations:"
echo "  • General monitoring: $SCRIPT_DIR/logs/cron_monitor.log"
echo "  • Detailed analysis: $SCRIPT_DIR/logs/cron_detailed.log"
echo "  • RSS feeds: $SCRIPT_DIR/logs/cron_rss.log"
echo "  • Monitor application: $SCRIPT_DIR/logs/monitor.log"
echo ""
echo "🔧 Management commands:"
echo "  • View current cron jobs: crontab -l"
echo "  • Remove VoiceLens jobs: crontab -l | grep -v voicelens | crontab -"
echo "  • View monitoring logs: tail -f $SCRIPT_DIR/logs/monitor.log"
echo "  • Test monitoring manually: $PYTHON_PATH $MONITOR_SCRIPT"
echo ""
echo "⚠️  Important:"
echo "  • Ensure your system doesn't sleep during scheduled times"
echo "  • Check logs regularly for any issues"
echo "  • The monitoring database will be created in $SCRIPT_DIR/data/"