#!/usr/bin/env python3
"""
Voice AI Provider Monitoring and Change Detection System
Monitors documentation, API changes, and service health across providers
"""
import asyncio
import aiohttp
import feedparser
import json
import hashlib
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import smtplib
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import schedule
import time
from pathlib import Path
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChangeType(str, Enum):
    """Types of changes detected"""
    DOCUMENTATION = "documentation"
    API_SCHEMA = "api_schema" 
    SERVICE_STATUS = "service_status"
    WEBHOOK_FORMAT = "webhook_format"
    PRICING = "pricing"
    FEATURE_ADDITION = "feature_addition"
    DEPRECATION = "deprecation"

class SeverityLevel(str, Enum):
    """Change severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ChangeEvent:
    """Detected change event"""
    provider: str
    change_type: ChangeType
    severity: SeverityLevel
    title: str
    description: str
    url: Optional[str] = None
    detected_at: datetime = None
    content_hash: Optional[str] = None
    diff: Optional[str] = None

@dataclass
class MonitoringConfig:
    """Configuration for monitoring a provider"""
    provider_name: str
    docs_url: str
    api_docs_url: Optional[str] = None
    status_url: Optional[str] = None
    changelog_url: Optional[str] = None
    rss_feed: Optional[str] = None
    webhook_endpoints: List[str] = None
    check_interval_minutes: int = 60
    css_selectors: Dict[str, str] = None  # For content extraction

class ProviderMonitor:
    """Monitors individual provider for changes"""
    
    def __init__(self, config: MonitoringConfig, db_path: str = "monitoring.db"):
        self.config = config
        self.db_path = db_path
        self.session = None
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for storing monitoring data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_snapshots (
                id INTEGER PRIMARY KEY,
                provider TEXT,
                url TEXT,
                content_hash TEXT,
                content TEXT,
                created_at TIMESTAMP,
                UNIQUE(provider, url, content_hash)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS change_events (
                id INTEGER PRIMARY KEY,
                provider TEXT,
                change_type TEXT,
                severity TEXT,
                title TEXT,
                description TEXT,
                url TEXT,
                detected_at TIMESTAMP,
                content_hash TEXT,
                diff TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_status (
                id INTEGER PRIMARY KEY,
                provider TEXT,
                endpoint TEXT,
                status_code INTEGER,
                response_time_ms FLOAT,
                is_healthy BOOLEAN,
                error_message TEXT,
                checked_at TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def start_monitoring(self):
        """Start the monitoring session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'VoiceLens-Monitor/1.0 (API Documentation Monitoring)'
            }
        )
    
    async def stop_monitoring(self):
        """Stop the monitoring session"""
        if self.session:
            await self.session.close()
    
    async def check_for_changes(self) -> List[ChangeEvent]:
        """Check all configured endpoints for changes"""
        changes = []
        
        # Check main documentation
        if self.config.docs_url:
            doc_changes = await self._check_documentation_changes()
            changes.extend(doc_changes)
        
        # Check API documentation
        if self.config.api_docs_url:
            api_changes = await self._check_api_changes()
            changes.extend(api_changes)
        
        # Check RSS feed
        if self.config.rss_feed:
            rss_changes = await self._check_rss_feed()
            changes.extend(rss_changes)
        
        # Check service status
        if self.config.status_url:
            status_changes = await self._check_service_status()
            changes.extend(status_changes)
        
        # Store all changes
        for change in changes:
            self._store_change_event(change)
        
        return changes
    
    async def _check_documentation_changes(self) -> List[ChangeEvent]:
        """Check main documentation for changes"""
        changes = []
        
        try:
            async with self.session.get(self.config.docs_url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Extract specific content if selectors provided
                    if self.config.css_selectors:
                        soup = BeautifulSoup(content, 'html.parser')
                        relevant_content = []
                        
                        for section, selector in self.config.css_selectors.items():
                            elements = soup.select(selector)
                            for elem in elements:
                                relevant_content.append(f"[{section}] {elem.get_text(strip=True)}")
                        
                        content = "\n".join(relevant_content)
                    
                    content_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    # Check if content has changed
                    if self._has_content_changed(self.config.docs_url, content_hash):
                        old_content = self._get_previous_content(self.config.docs_url)
                        diff = self._generate_diff(old_content, content)
                        
                        change = ChangeEvent(
                            provider=self.config.provider_name,
                            change_type=ChangeType.DOCUMENTATION,
                            severity=self._assess_severity(diff),
                            title=f"Documentation updated for {self.config.provider_name}",
                            description=f"Changes detected in main documentation",
                            url=self.config.docs_url,
                            detected_at=datetime.now(timezone.utc),
                            content_hash=content_hash,
                            diff=diff[:1000] if diff else None  # Truncate large diffs
                        )
                        changes.append(change)
                        
                        # Store new content snapshot
                        self._store_content_snapshot(self.config.docs_url, content_hash, content)
                
        except Exception as e:
            logger.error(f"Error checking documentation for {self.config.provider_name}: {e}")
        
        return changes
    
    async def _check_api_changes(self) -> List[ChangeEvent]:
        """Check API documentation for changes"""
        changes = []
        
        if not self.config.api_docs_url:
            return changes
        
        try:
            async with self.session.get(self.config.api_docs_url) as response:
                if response.status == 200:
                    content = await response.text()
                    content_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    if self._has_content_changed(self.config.api_docs_url, content_hash):
                        old_content = self._get_previous_content(self.config.api_docs_url)
                        diff = self._generate_diff(old_content, content)
                        
                        # Look for webhook-specific changes
                        webhook_keywords = ['webhook', 'post_call', 'end-of-call', 'callback']
                        is_webhook_change = any(keyword.lower() in diff.lower() for keyword in webhook_keywords)
                        
                        change_type = ChangeType.WEBHOOK_FORMAT if is_webhook_change else ChangeType.API_SCHEMA
                        severity = SeverityLevel.HIGH if is_webhook_change else SeverityLevel.MEDIUM
                        
                        change = ChangeEvent(
                            provider=self.config.provider_name,
                            change_type=change_type,
                            severity=severity,
                            title=f"API documentation updated for {self.config.provider_name}",
                            description=f"{'Webhook' if is_webhook_change else 'API'} changes detected",
                            url=self.config.api_docs_url,
                            detected_at=datetime.now(timezone.utc),
                            content_hash=content_hash,
                            diff=diff[:1000] if diff else None
                        )
                        changes.append(change)
                        
                        self._store_content_snapshot(self.config.api_docs_url, content_hash, content)
                        
        except Exception as e:
            logger.error(f"Error checking API docs for {self.config.provider_name}: {e}")
        
        return changes
    
    async def _check_rss_feed(self) -> List[ChangeEvent]:
        """Check RSS feed for new updates"""
        changes = []
        
        if not self.config.rss_feed:
            return changes
        
        try:
            # Use requests for RSS since feedparser doesn't support async
            response = requests.get(self.config.rss_feed, timeout=30)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                
                # Check for new entries in the last 24 hours
                cutoff_time = datetime.now(timezone.utc) - timedelta(days=1)
                
                for entry in feed.entries[:10]:  # Check latest 10 entries
                    entry_date = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
                    
                    if entry_date > cutoff_time:
                        # Check if this entry is new
                        entry_hash = hashlib.md5(entry.link.encode()).hexdigest()
                        
                        if not self._entry_exists(entry_hash):
                            severity = self._assess_feed_entry_severity(entry.title, entry.description if hasattr(entry, 'description') else "")
                            
                            change = ChangeEvent(
                                provider=self.config.provider_name,
                                change_type=ChangeType.FEATURE_ADDITION,
                                severity=severity,
                                title=entry.title,
                                description=entry.description if hasattr(entry, 'description') else "",
                                url=entry.link,
                                detected_at=entry_date,
                                content_hash=entry_hash
                            )
                            changes.append(change)
                            
                            # Mark entry as seen
                            self._store_content_snapshot(entry.link, entry_hash, entry.title)
                            
        except Exception as e:
            logger.error(f"Error checking RSS feed for {self.config.provider_name}: {e}")
        
        return changes
    
    async def _check_service_status(self) -> List[ChangeEvent]:
        """Check service health and status"""
        changes = []
        
        if not self.config.status_url:
            return changes
        
        try:
            start_time = time.time()
            async with self.session.get(self.config.status_url) as response:
                response_time = (time.time() - start_time) * 1000
                
                is_healthy = response.status == 200
                error_message = None
                
                if not is_healthy:
                    error_message = f"HTTP {response.status}"
                
                # Store current status
                self._store_service_status(
                    self.config.status_url,
                    response.status,
                    response_time,
                    is_healthy,
                    error_message
                )
                
                # Check if status changed from previous check
                previous_status = self._get_previous_service_status(self.config.status_url)
                
                if previous_status and previous_status['is_healthy'] != is_healthy:
                    severity = SeverityLevel.CRITICAL if not is_healthy else SeverityLevel.MEDIUM
                    
                    change = ChangeEvent(
                        provider=self.config.provider_name,
                        change_type=ChangeType.SERVICE_STATUS,
                        severity=severity,
                        title=f"Service status changed for {self.config.provider_name}",
                        description=f"Status changed from {'healthy' if previous_status['is_healthy'] else 'unhealthy'} to {'healthy' if is_healthy else 'unhealthy'}",
                        url=self.config.status_url,
                        detected_at=datetime.now(timezone.utc)
                    )
                    changes.append(change)
                    
        except Exception as e:
            logger.error(f"Error checking service status for {self.config.provider_name}: {e}")
            
            # Store error status
            self._store_service_status(
                self.config.status_url,
                0,
                0,
                False,
                str(e)
            )
        
        return changes
    
    def _has_content_changed(self, url: str, content_hash: str) -> bool:
        """Check if content has changed since last check"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT content_hash FROM content_snapshots 
            WHERE provider = ? AND url = ? 
            ORDER BY created_at DESC LIMIT 1
        """, (self.config.provider_name, url))
        
        result = cursor.fetchone()
        conn.close()
        
        return result is None or result[0] != content_hash
    
    def _get_previous_content(self, url: str) -> Optional[str]:
        """Get previous content for comparison"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT content FROM content_snapshots 
            WHERE provider = ? AND url = ? 
            ORDER BY created_at DESC LIMIT 1
        """, (self.config.provider_name, url))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def _generate_diff(self, old_content: Optional[str], new_content: str) -> str:
        """Generate a simple diff between old and new content"""
        if not old_content:
            return f"New content added ({len(new_content)} characters)"
        
        # Simple diff - could be enhanced with proper diff library
        old_lines = set(old_content.split('\n'))
        new_lines = set(new_content.split('\n'))
        
        added = new_lines - old_lines
        removed = old_lines - new_lines
        
        diff_parts = []
        if added:
            diff_parts.append(f"Added {len(added)} lines")
        if removed:
            diff_parts.append(f"Removed {len(removed)} lines")
        
        return "; ".join(diff_parts) if diff_parts else "Content modified"
    
    def _assess_severity(self, diff: str) -> SeverityLevel:
        """Assess the severity of a change based on diff"""
        if not diff:
            return SeverityLevel.LOW
        
        high_impact_keywords = ['webhook', 'api', 'breaking', 'deprecated', 'removed', 'error']
        medium_impact_keywords = ['updated', 'changed', 'modified', 'new']
        
        diff_lower = diff.lower()
        
        if any(keyword in diff_lower for keyword in high_impact_keywords):
            return SeverityLevel.HIGH
        elif any(keyword in diff_lower for keyword in medium_impact_keywords):
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _assess_feed_entry_severity(self, title: str, description: str) -> SeverityLevel:
        """Assess severity of RSS feed entry"""
        content = (title + " " + description).lower()
        
        critical_keywords = ['outage', 'down', 'critical', 'security']
        high_keywords = ['breaking', 'deprecated', 'webhook', 'api change']
        
        if any(keyword in content for keyword in critical_keywords):
            return SeverityLevel.CRITICAL
        elif any(keyword in content for keyword in high_keywords):
            return SeverityLevel.HIGH
        else:
            return SeverityLevel.MEDIUM
    
    def _entry_exists(self, entry_hash: str) -> bool:
        """Check if RSS entry has been seen before"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 1 FROM content_snapshots 
            WHERE provider = ? AND content_hash = ?
        """, (self.config.provider_name, entry_hash))
        
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    
    def _store_content_snapshot(self, url: str, content_hash: str, content: str):
        """Store content snapshot"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO content_snapshots 
                (provider, url, content_hash, content, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (self.config.provider_name, url, content_hash, content, datetime.now(timezone.utc)))
            
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error storing content snapshot: {e}")
        finally:
            conn.close()
    
    def _store_change_event(self, change: ChangeEvent):
        """Store detected change event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO change_events 
                (provider, change_type, severity, title, description, url, detected_at, content_hash, diff)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                change.provider, change.change_type.value, change.severity.value,
                change.title, change.description, change.url, change.detected_at,
                change.content_hash, change.diff
            ))
            
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error storing change event: {e}")
        finally:
            conn.close()
    
    def _store_service_status(self, endpoint: str, status_code: int, response_time: float, 
                            is_healthy: bool, error_message: Optional[str]):
        """Store service status check result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO service_status 
                (provider, endpoint, status_code, response_time_ms, is_healthy, error_message, checked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.config.provider_name, endpoint, status_code, response_time,
                is_healthy, error_message, datetime.now(timezone.utc)
            ))
            
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error storing service status: {e}")
        finally:
            conn.close()
    
    def _get_previous_service_status(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get previous service status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT is_healthy, status_code, response_time_ms 
            FROM service_status 
            WHERE provider = ? AND endpoint = ? 
            ORDER BY checked_at DESC LIMIT 1 OFFSET 1
        """, (self.config.provider_name, endpoint))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'is_healthy': bool(result[0]),
                'status_code': result[1],
                'response_time_ms': result[2]
            }
        return None

class VoiceLensMonitoringSystem:
    """Main monitoring system for all voice AI providers"""
    
    def __init__(self):
        self.monitors = []
        self.notification_handlers = []
        self._init_provider_monitors()
    
    def _init_provider_monitors(self):
        """Initialize monitors for all providers"""
        from provider_documentation import VoiceAIProviderRegistry
        
        registry = VoiceAIProviderRegistry()
        providers = registry.get_all_providers()
        
        for provider in providers:
            config = MonitoringConfig(
                provider_name=provider.name,
                docs_url=provider.docs_url,
                api_docs_url=f"{provider.docs_url}/api-reference" if "/docs" in provider.docs_url else None,
                status_url=provider.status_page,
                changelog_url=provider.changelog_url,
                rss_feed=provider.rss_feed,
                check_interval_minutes=60,
                css_selectors={
                    'webhook_section': '.webhook, .webhooks, #webhooks',
                    'api_changes': '.changelog, .updates, #changelog'
                }
            )
            
            monitor = ProviderMonitor(config)
            self.monitors.append(monitor)
    
    async def start_monitoring(self):
        """Start monitoring all providers"""
        logger.info(f"Starting monitoring for {len(self.monitors)} providers")
        
        for monitor in self.monitors:
            await monitor.start_monitoring()
        
        # Schedule periodic checks
        schedule.every(60).minutes.do(self._run_all_checks)
        
        # Run initial check
        await self._run_all_checks()
    
    async def stop_monitoring(self):
        """Stop all monitoring"""
        for monitor in self.monitors:
            await monitor.stop_monitoring()
    
    async def _run_all_checks(self):
        """Run checks for all providers"""
        all_changes = []
        
        for monitor in self.monitors:
            try:
                changes = await monitor.check_for_changes()
                all_changes.extend(changes)
            except Exception as e:
                logger.error(f"Error checking {monitor.config.provider_name}: {e}")
        
        if all_changes:
            await self._handle_changes(all_changes)
        
        logger.info(f"Monitoring check complete. Found {len(all_changes)} changes.")
    
    async def _handle_changes(self, changes: List[ChangeEvent]):
        """Handle detected changes"""
        # Group changes by severity
        critical_changes = [c for c in changes if c.severity == SeverityLevel.CRITICAL]
        high_changes = [c for c in changes if c.severity == SeverityLevel.HIGH]
        
        # Send immediate notifications for critical/high changes
        if critical_changes or high_changes:
            await self._send_notifications(critical_changes + high_changes)
        
        # Update VCP mappings if webhook changes detected
        webhook_changes = [c for c in changes if c.change_type == ChangeType.WEBHOOK_FORMAT]
        if webhook_changes:
            await self._update_vcp_mappings(webhook_changes)
    
    async def _send_notifications(self, changes: List[ChangeEvent]):
        """Send notifications for important changes"""
        for handler in self.notification_handlers:
            try:
                await handler(changes)
            except Exception as e:
                logger.error(f"Error sending notification: {e}")
    
    async def _update_vcp_mappings(self, webhook_changes: List[ChangeEvent]):
        """Update VCP mappings when webhook formats change"""
        logger.info(f"Webhook changes detected for {len(webhook_changes)} providers")
        # This would trigger a review process for VCP mapping updates
        # Could integrate with provider_documentation.py to update mappings
    
    def get_recent_changes(self, limit: int = 10) -> List[ChangeEvent]:
        """Get recent change events from monitoring database"""
        try:
            # Try to get changes from the new monitoring system first
            from monitor_provider_changes import ProviderMonitor
            monitor = ProviderMonitor()
            
            # Get recent changes from the monitoring database
            raw_changes = monitor.get_recent_changes(limit=limit)
            
            # Convert to ChangeEvent objects
            change_events = []
            for change in raw_changes:
                # Map severity levels
                severity_mapping = {
                    'low': SeverityLevel.LOW,
                    'medium': SeverityLevel.MEDIUM, 
                    'high': SeverityLevel.HIGH,
                    'critical': SeverityLevel.CRITICAL
                }
                
                # Map change types
                change_type_mapping = {
                    'content_changed': ChangeType.DOCUMENTATION_UPDATED,
                    'new_post': ChangeType.CHANGELOG_ENTRY,
                    'status_change': ChangeType.API_CHANGE,
                    'error': ChangeType.OTHER
                }
                
                change_event = ChangeEvent(
                    provider=change.provider,
                    change_type=change_type_mapping.get(change.change_type, ChangeType.OTHER),
                    title=change.summary,
                    description=change.content_diff or '',
                    severity=severity_mapping.get(change.severity, SeverityLevel.MEDIUM),
                    detected_at=change.detected_at,
                    source_url=change.resource_url
                )
                change_events.append(change_event)
            
            return change_events
            
        except Exception as e:
            # Fallback: try to get from the old database structure
            import sqlite3
            try:
                conn = sqlite3.connect("monitoring.db")
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT provider, change_type, severity, title, description, url, detected_at
                    FROM change_events 
                    ORDER BY detected_at DESC LIMIT ?
                """, (limit,))
                
                changes = []
                for row in cursor.fetchall():
                    # Map string values back to enums
                    change_type = getattr(ChangeType, row[1].upper(), ChangeType.OTHER)
                    severity = getattr(SeverityLevel, row[2].upper(), SeverityLevel.MEDIUM)
                    
                    change = ChangeEvent(
                        provider=row[0],
                        change_type=change_type,
                        title=row[3],
                        description=row[4],
                        severity=severity,
                        detected_at=datetime.fromisoformat(row[6]) if row[6] else datetime.now(timezone.utc),
                        source_url=row[5]
                    )
                    changes.append(change)
                
                conn.close()
                return changes
                
            except Exception as db_e:
                print(f"Warning: Could not access monitoring database: {e}, {db_e}")
                return []

# Notification handlers
async def slack_notification_handler(changes: List[ChangeEvent]):
    """Send Slack notification"""
    # Would integrate with Slack API
    message = f"🚨 VoiceLens Provider Alert: {len(changes)} important changes detected\n\n"
    
    for change in changes[:5]:  # Limit to first 5 changes
        message += f"• {change.provider}: {change.title}\n"
    
    logger.info(f"Would send Slack notification: {message}")

async def email_notification_handler(changes: List[ChangeEvent]):
    """Send email notification"""
    # Would integrate with SMTP
    logger.info(f"Would send email notification for {len(changes)} changes")

# CLI interface
def create_monitoring_dashboard():
    """Create a simple monitoring dashboard"""
    import sqlite3
    from tabulate import tabulate
    
    db_path = "monitoring.db"
    conn = sqlite3.connect(db_path)
    
    # Get recent changes
    cursor = conn.cursor()
    cursor.execute("""
        SELECT provider, change_type, severity, title, detected_at 
        FROM change_events 
        ORDER BY detected_at DESC LIMIT 20
    """)
    
    changes = cursor.fetchall()
    
    if changes:
        print("\n📊 Recent Changes:")
        headers = ["Provider", "Type", "Severity", "Title", "Detected"]
        print(tabulate(changes, headers=headers, tablefmt="grid"))
    else:
        print("No recent changes detected.")
    
    # Get service status
    cursor.execute("""
        SELECT provider, endpoint, is_healthy, response_time_ms, checked_at
        FROM service_status 
        WHERE id IN (
            SELECT MAX(id) FROM service_status GROUP BY provider, endpoint
        )
        ORDER BY provider
    """)
    
    status_checks = cursor.fetchall()
    
    if status_checks:
        print("\n🏥 Service Health Status:")
        headers = ["Provider", "Endpoint", "Healthy", "Response (ms)", "Last Check"]
        print(tabulate(status_checks, headers=headers, tablefmt="grid"))
    
    conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VoiceLens Provider Monitoring System")
    parser.add_argument("--dashboard", action="store_true", help="Show monitoring dashboard")
    parser.add_argument("--start", action="store_true", help="Start monitoring (runs indefinitely)")
    
    args = parser.parse_args()
    
    if args.dashboard:
        create_monitoring_dashboard()
    elif args.start:
        # Start the monitoring system
        system = VoiceLensMonitoringSystem()
        system.notification_handlers.extend([
            slack_notification_handler,
            email_notification_handler
        ])
        
        async def run_monitoring():
            await system.start_monitoring()
            
            # Keep running and check schedule
            while True:
                schedule.run_pending()
                await asyncio.sleep(60)
        
        asyncio.run(run_monitoring())
    else:
        parser.print_help()