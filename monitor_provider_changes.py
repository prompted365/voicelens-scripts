#!/usr/bin/env python3
"""
VoiceLens Provider Change Monitor
Automated monitoring for provider documentation, API changes, and status updates
"""

import os
import sys
import json
import time
import hashlib
import requests
import sqlite3
import feedparser
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import difflib
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/breydentaylor/voicelens-scripts/logs/monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ChangeDetection:
    """Detected change in provider resource"""
    provider: str
    resource_type: str  # 'documentation', 'rss', 'status_page', 'api_endpoint'
    resource_url: str
    change_type: str    # 'content_changed', 'new_post', 'status_change', 'error'
    old_hash: Optional[str]
    new_hash: Optional[str]
    content_diff: Optional[str]
    detected_at: datetime
    severity: str       # 'low', 'medium', 'high', 'critical'
    summary: str

class ProviderMonitor:
    """Monitor provider resources for changes"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.db_path = self.data_dir / "monitoring.db"
        self._init_database()
        
        # Load provider configuration
        from provider_documentation import VoiceAIProviderRegistry
        self.registry = VoiceAIProviderRegistry()
    
    def _init_database(self):
        """Initialize monitoring database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitoring_snapshots (
                id INTEGER PRIMARY KEY,
                provider TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_url TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                content_size INTEGER,
                last_checked TIMESTAMP NOT NULL,
                last_modified TIMESTAMP,
                status_code INTEGER,
                UNIQUE(provider, resource_type, resource_url)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS change_events (
                id INTEGER PRIMARY KEY,
                provider TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_url TEXT NOT NULL,
                change_type TEXT NOT NULL,
                old_hash TEXT,
                new_hash TEXT,
                content_diff TEXT,
                detected_at TIMESTAMP NOT NULL,
                severity TEXT NOT NULL,
                summary TEXT NOT NULL,
                notified BOOLEAN DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rss_items (
                id INTEGER PRIMARY KEY,
                provider TEXT NOT NULL,
                feed_url TEXT NOT NULL,
                item_guid TEXT NOT NULL,
                title TEXT NOT NULL,
                link TEXT,
                published TIMESTAMP,
                description TEXT,
                first_seen TIMESTAMP NOT NULL,
                UNIQUE(provider, feed_url, item_guid)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def check_documentation_changes(self) -> List[ChangeDetection]:
        """Check for changes in provider documentation"""
        changes = []
        
        for provider in self.registry.get_all_providers():
            try:
                # Check main documentation
                if provider.docs_url:
                    change = self._check_url_changes(
                        provider.name.lower().replace(' ', '_'),
                        'documentation',
                        provider.docs_url
                    )
                    if change:
                        changes.append(change)
                
                # Check status page
                if provider.status_page:
                    change = self._check_url_changes(
                        provider.name.lower().replace(' ', '_'),
                        'status_page',
                        provider.status_page
                    )
                    if change:
                        changes.append(change)
                
                # Check API endpoint health
                if provider.api_base_url:
                    change = self._check_api_health(
                        provider.name.lower().replace(' ', '_'),
                        provider.api_base_url
                    )
                    if change:
                        changes.append(change)
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error checking {provider.name}: {e}")
                continue
        
        return changes
    
    def check_rss_feeds(self) -> List[ChangeDetection]:
        """Check RSS feeds for new posts"""
        changes = []
        
        for provider in self.registry.get_all_providers():
            if not provider.rss_feed:
                continue
            
            try:
                change = self._check_rss_feed(
                    provider.name.lower().replace(' ', '_'),
                    provider.rss_feed
                )
                if change:
                    changes.extend(change)
                    
                time.sleep(2)  # Rate limiting for RSS
                
            except Exception as e:
                logger.error(f"Error checking RSS for {provider.name}: {e}")
                continue
        
        return changes
    
    def _check_url_changes(self, provider: str, resource_type: str, url: str) -> Optional[ChangeDetection]:
        """Check if URL content has changed"""
        try:
            # Fetch current content
            headers = {
                'User-Agent': 'VoiceLens-Monitor/1.0 (https://voicelens.ai)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            # Handle redirects and errors
            if response.status_code >= 400:
                return ChangeDetection(
                    provider=provider,
                    resource_type=resource_type,
                    resource_url=url,
                    change_type='error',
                    old_hash=None,
                    new_hash=None,
                    content_diff=f"HTTP {response.status_code}",
                    detected_at=datetime.now(timezone.utc),
                    severity='high' if response.status_code >= 500 else 'medium',
                    summary=f"HTTP error {response.status_code} accessing {resource_type}"
                )
            
            # Calculate content hash
            content = response.text
            new_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Get previous snapshot
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT content_hash, content_size FROM monitoring_snapshots 
                WHERE provider = ? AND resource_type = ? AND resource_url = ?
            ''', (provider, resource_type, url))
            
            result = cursor.fetchone()
            
            if result:
                old_hash, old_size = result
                if old_hash != new_hash:
                    # Content changed
                    content_diff = f"Size: {old_size} -> {len(content)} bytes"
                    
                    # Calculate severity based on size change
                    size_change_pct = abs(len(content) - old_size) / old_size * 100 if old_size > 0 else 0
                    if size_change_pct > 50:
                        severity = 'high'
                    elif size_change_pct > 20:
                        severity = 'medium'
                    else:
                        severity = 'low'
                    
                    change = ChangeDetection(
                        provider=provider,
                        resource_type=resource_type,
                        resource_url=url,
                        change_type='content_changed',
                        old_hash=old_hash,
                        new_hash=new_hash,
                        content_diff=content_diff,
                        detected_at=datetime.now(timezone.utc),
                        severity=severity,
                        summary=f"{resource_type} content changed ({size_change_pct:.1f}% size change)"
                    )
                    
                    # Store change event
                    self._store_change_event(change)
                    
                    # Update snapshot
                    cursor.execute('''
                        UPDATE monitoring_snapshots 
                        SET content_hash = ?, content_size = ?, last_checked = ?, status_code = ?
                        WHERE provider = ? AND resource_type = ? AND resource_url = ?
                    ''', (new_hash, len(content), datetime.now(timezone.utc), response.status_code, provider, resource_type, url))
                    
                    conn.commit()
                    conn.close()
                    return change
            else:
                # First time seeing this resource
                cursor.execute('''
                    INSERT INTO monitoring_snapshots 
                    (provider, resource_type, resource_url, content_hash, content_size, last_checked, status_code)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (provider, resource_type, url, new_hash, len(content), datetime.now(timezone.utc), response.status_code))
            
            # Update last checked time
            cursor.execute('''
                UPDATE monitoring_snapshots 
                SET last_checked = ?, status_code = ?
                WHERE provider = ? AND resource_type = ? AND resource_url = ?
            ''', (datetime.now(timezone.utc), response.status_code, provider, resource_type, url))
            
            conn.commit()
            conn.close()
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking {url}: {e}")
            return ChangeDetection(
                provider=provider,
                resource_type=resource_type,
                resource_url=url,
                change_type='error',
                old_hash=None,
                new_hash=None,
                content_diff=str(e),
                detected_at=datetime.now(timezone.utc),
                severity='medium',
                summary=f"Error accessing {resource_type}: {str(e)[:100]}"
            )
    
    def _check_api_health(self, provider: str, api_url: str) -> Optional[ChangeDetection]:
        """Check API endpoint health"""
        try:
            response = requests.get(api_url, timeout=10)
            status_code = response.status_code
            response_time = response.elapsed.total_seconds()
            
            # Check if this is a significant status change
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT status_code FROM monitoring_snapshots 
                WHERE provider = ? AND resource_type = 'api_endpoint' AND resource_url = ?
            ''', (provider, api_url))
            
            result = cursor.fetchone()
            
            if result:
                old_status = result[0]
                if old_status != status_code:
                    # Status changed
                    if status_code >= 500:
                        severity = 'critical'
                    elif status_code >= 400:
                        severity = 'high'
                    elif status_code >= 300:
                        severity = 'medium'
                    else:
                        severity = 'low'
                    
                    change = ChangeDetection(
                        provider=provider,
                        resource_type='api_endpoint',
                        resource_url=api_url,
                        change_type='status_change',
                        old_hash=str(old_status),
                        new_hash=str(status_code),
                        content_diff=f"Status: {old_status} -> {status_code}, Response time: {response_time:.2f}s",
                        detected_at=datetime.now(timezone.utc),
                        severity=severity,
                        summary=f"API status changed from {old_status} to {status_code}"
                    )
                    
                    self._store_change_event(change)
                    conn.close()
                    return change
            
            conn.close()
            return None
            
        except Exception as e:
            return ChangeDetection(
                provider=provider,
                resource_type='api_endpoint',
                resource_url=api_url,
                change_type='error',
                old_hash=None,
                new_hash=None,
                content_diff=str(e),
                detected_at=datetime.now(timezone.utc),
                severity='high',
                summary=f"API health check failed: {str(e)[:100]}"
            )
    
    def _check_rss_feed(self, provider: str, feed_url: str) -> List[ChangeDetection]:
        """Check RSS feed for new items"""
        changes = []
        
        try:
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logger.warning(f"RSS feed parsing warning for {provider}: {feed.bozo_exception}")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for entry in feed.entries[:10]:  # Check last 10 entries
                guid = entry.get('id', entry.get('link', ''))
                title = entry.get('title', 'Untitled')
                link = entry.get('link', '')
                description = entry.get('description', entry.get('summary', ''))
                
                # Parse published date
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                
                # Check if this is a new item
                cursor.execute('''
                    SELECT id FROM rss_items 
                    WHERE provider = ? AND feed_url = ? AND item_guid = ?
                ''', (provider, feed_url, guid))
                
                if not cursor.fetchone():
                    # New RSS item
                    cursor.execute('''
                        INSERT INTO rss_items 
                        (provider, feed_url, item_guid, title, link, published, description, first_seen)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (provider, feed_url, guid, title, link, published, description, datetime.now(timezone.utc)))
                    
                    change = ChangeDetection(
                        provider=provider,
                        resource_type='rss',
                        resource_url=feed_url,
                        change_type='new_post',
                        old_hash=None,
                        new_hash=guid,
                        content_diff=f"Title: {title}\nLink: {link}",
                        detected_at=datetime.now(timezone.utc),
                        severity='low',
                        summary=f"New RSS post: {title}"
                    )
                    
                    self._store_change_event(change)
                    changes.append(change)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error checking RSS feed {feed_url}: {e}")
        
        return changes
    
    def _store_change_event(self, change: ChangeDetection):
        """Store change event in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO change_events 
            (provider, resource_type, resource_url, change_type, old_hash, new_hash, 
             content_diff, detected_at, severity, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            change.provider, change.resource_type, change.resource_url, 
            change.change_type, change.old_hash, change.new_hash,
            change.content_diff, change.detected_at, change.severity, change.summary
        ))
        
        conn.commit()
        conn.close()
    
    def get_recent_changes(self, limit: int = 50) -> List[ChangeDetection]:
        """Get recent change events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT provider, resource_type, resource_url, change_type, old_hash, new_hash,
                   content_diff, detected_at, severity, summary
            FROM change_events 
            ORDER BY detected_at DESC 
            LIMIT ?
        ''', (limit,))
        
        changes = []
        for row in cursor.fetchall():
            change = ChangeDetection(
                provider=row[0],
                resource_type=row[1],
                resource_url=row[2],
                change_type=row[3],
                old_hash=row[4],
                new_hash=row[5],
                content_diff=row[6],
                detected_at=datetime.fromisoformat(row[7]),
                severity=row[8],
                summary=row[9]
            )
            changes.append(change)
        
        conn.close()
        return changes
    
    def run_monitoring_cycle(self):
        """Run complete monitoring cycle"""
        logger.info("Starting monitoring cycle")
        
        # Check documentation changes
        logger.info("Checking documentation changes...")
        doc_changes = self.check_documentation_changes()
        logger.info(f"Found {len(doc_changes)} documentation changes")
        
        # Check RSS feeds
        logger.info("Checking RSS feeds...")
        rss_changes = self.check_rss_feeds()
        logger.info(f"Found {len(rss_changes)} RSS changes")
        
        all_changes = doc_changes + rss_changes
        
        # Log summary
        if all_changes:
            high_priority = [c for c in all_changes if c.severity in ['high', 'critical']]
            logger.info(f"Total changes: {len(all_changes)}, High priority: {len(high_priority)}")
            
            for change in high_priority:
                logger.warning(f"HIGH PRIORITY: {change.provider} - {change.summary}")
        else:
            logger.info("No changes detected")
        
        logger.info("Monitoring cycle completed")
        return all_changes

def main():
    """Main monitoring script"""
    # Create logs directory
    os.makedirs('/Users/breydentaylor/voicelens-scripts/logs', exist_ok=True)
    
    monitor = ProviderMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        # Continuous monitoring mode
        logger.info("Starting continuous monitoring mode")
        while True:
            try:
                monitor.run_monitoring_cycle()
                logger.info("Waiting 1 hour until next check...")
                time.sleep(3600)  # Check every hour
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                time.sleep(300)  # Wait 5 minutes before retry
    else:
        # Single run mode
        changes = monitor.run_monitoring_cycle()
        
        # Print summary
        if changes:
            print(f"\nDetected {len(changes)} changes:")
            for change in changes:
                print(f"  [{change.severity.upper()}] {change.provider}: {change.summary}")
        else:
            print("No changes detected.")

if __name__ == '__main__':
    main()