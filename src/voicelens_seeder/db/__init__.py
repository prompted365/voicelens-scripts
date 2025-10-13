"""
Database utilities for VoiceLens Seeder

Handles SQLite schema initialization, migrations, and connection management.
Optimized for VCP 0.3 data storage and analytics workloads.
"""

import sqlite3
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

import orjson
from rich.console import Console

console = Console()

class DatabaseManager:
    """Manages SQLite database operations with WAL mode and performance optimizations."""
    
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self) -> None:
        """Ensure the database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def connection(self):
        """Context manager for database connections with proper cleanup."""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def init_schema(self) -> bool:
        """Initialize database with schema from schema.sql file."""
        schema_file = Path(__file__).parent / "schema.sql"
        
        if not schema_file.exists():
            console.print(f"❌ Schema file not found: {schema_file}")
            return False
        
        try:
            schema_sql = schema_file.read_text()
            
            with self.connection() as conn:
                # Execute schema creation
                conn.executescript(schema_sql)
                conn.commit()
                
                # Verify schema was created
                cursor = conn.execute(
                    "SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1"
                )
                version = cursor.fetchone()
                
                if version:
                    console.print(f"✅ Database schema initialized (version {version[0]})")
                    return True
                else:
                    console.print("❌ Schema initialization failed - no version recorded")
                    return False
                    
        except sqlite3.Error as e:
            console.print(f"❌ Database error: {e}")
            return False
        except Exception as e:
            console.print(f"❌ Unexpected error: {e}")
            return False
    
    def get_schema_version(self) -> Optional[str]:
        """Get current database schema version."""
        try:
            with self.connection() as conn:
                cursor = conn.execute(
                    "SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1"
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error:
            return None
    
    def validate_schema(self) -> bool:
        """Validate that all expected tables exist with proper structure."""
        expected_tables = [
            'schema_version', 'seeder_runs', 'vcp_raw', 'conversations', 
            'participants', 'turns', 'metrics', 'classifications', 
            'perception_gaps', 'normalizations', 'endpoints', 
            'endpoint_calls', 'profiles'
        ]
        
        try:
            with self.connection() as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                actual_tables = {row[0] for row in cursor.fetchall()}
                
                missing_tables = set(expected_tables) - actual_tables
                
                if missing_tables:
                    console.print(f"❌ Missing tables: {', '.join(missing_tables)}")
                    return False
                
                console.print("✅ Schema validation passed")
                return True
                
        except sqlite3.Error as e:
            console.print(f"❌ Schema validation error: {e}")
            return False
    
    def create_run(self, profile_name: Optional[str] = None, 
                   vcp_mode: str = "gtm", git_sha: Optional[str] = None) -> str:
        """Create a new seeder run and return the run ID."""
        run_id = str(uuid.uuid4())
        
        try:
            with self.connection() as conn:
                conn.execute(
                    """
                    INSERT INTO seeder_runs 
                    (id, profile_name, vcp_mode, git_sha, version, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (run_id, profile_name, vcp_mode, git_sha, "0.1.0", "running")
                )
                conn.commit()
                return run_id
                
        except sqlite3.Error as e:
            console.print(f"❌ Error creating run: {e}")
            raise
    
    def finish_run(self, run_id: str, seed_count: int = 0, 
                   normalize_count: int = 0, error_count: int = 0,
                   status: str = "completed", notes: Optional[str] = None) -> None:
        """Mark a seeder run as finished with final counts."""
        try:
            with self.connection() as conn:
                conn.execute(
                    """
                    UPDATE seeder_runs 
                    SET finished_at = datetime('now', 'utc'),
                        seed_count = ?, normalize_count = ?, error_count = ?,
                        status = ?, notes = ?
                    WHERE id = ?
                    """,
                    (seed_count, normalize_count, error_count, status, notes, run_id)
                )
                conn.commit()
                
        except sqlite3.Error as e:
            console.print(f"❌ Error finishing run: {e}")
            raise
    
    def store_vcp_raw(self, call_id: str, payload: Dict[str, Any], 
                      source: str = "synthetic", provider: Optional[str] = None,
                      run_id: Optional[str] = None) -> str:
        """Store a raw VCP payload and return the vcp_id."""
        vcp_id = str(uuid.uuid4())
        payload_json = orjson.dumps(payload).decode()
        
        try:
            with self.connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO vcp_raw 
                    (vcp_id, run_id, call_id, payload_json, source, provider)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (vcp_id, run_id, call_id, payload_json, source, provider)
                )
                conn.commit()
                return vcp_id
                
        except sqlite3.Error as e:
            console.print(f"❌ Error storing VCP payload: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics for monitoring."""
        try:
            with self.connection() as conn:
                stats = {}
                
                # Table row counts
                tables = ['conversations', 'participants', 'turns', 'metrics', 
                         'classifications', 'perception_gaps', 'vcp_raw', 'endpoints']
                
                for table in tables:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]
                
                # Recent activity
                cursor = conn.execute(
                    """
                    SELECT COUNT(*) as recent_conversations 
                    FROM conversations 
                    WHERE created_at > datetime('now', '-24 hours')
                    """
                )
                stats["conversations_last_24h"] = cursor.fetchone()[0]
                
                # Database size
                cursor = conn.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                cursor = conn.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]
                stats["database_size_mb"] = (page_count * page_size) / (1024 * 1024)
                
                return stats
                
        except sqlite3.Error as e:
            console.print(f"❌ Error getting stats: {e}")
            return {}
    
    def vacuum_and_analyze(self) -> bool:
        """Run VACUUM and ANALYZE for performance optimization."""
        try:
            with self.connection() as conn:
                console.print("🧹 Running database maintenance...")
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
                console.print("✅ Database maintenance completed")
                return True
                
        except sqlite3.Error as e:
            console.print(f"❌ Error during maintenance: {e}")
            return False


def get_db_manager(db_path: Optional[Path] = None) -> DatabaseManager:
    """Get a DatabaseManager instance with default path if not specified."""
    if db_path is None:
        db_path = Path.cwd() / "data" / "voicelens.db"
    
    return DatabaseManager(db_path)