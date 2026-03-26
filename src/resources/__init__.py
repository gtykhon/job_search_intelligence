"""
Resource Management System
Centralized resource management with conflict prevention and connection pooling
"""

import asyncio
import sqlite3
import threading
import time
import json
import sqlite3
import threading
import time
import json
import os
from typing import Dict, Optional, Any, List, ContextManager, Generator
from contextlib import contextmanager, asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import logging

@dataclass
class ConnectionInfo:
    """Information about a database connection"""
    connection: Any
    created_at: datetime
    last_used: datetime
    thread_id: int
    is_busy: bool = False
    usage_count: int = 0

class DatabaseConnectionManager:
    """
    Centralized SQLite connection manager preventing locking conflicts
    
    Key features:
    1. Single connection pool for all components
    2. Proper connection cleanup and resource management
    3. Thread-safe connection handling
    4. Connection timeout and retry logic
    5. Automatic cleanup of stale connections
    """
    
    def __init__(self, max_connections: int = 10, connection_timeout: int = 30):
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.connections: Dict[str, ConnectionInfo] = {}
        self._lock = threading.Lock()
        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = 0
        self.max_retries = 3
        self.retry_delay = 1.0
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def get_connection(self, db_name: str, db_path: Optional[str] = None):
        """Get database connection with automatic cleanup"""
        if db_path is None:
            db_path = f"data/{db_name}.db"
        
        connection_key = f"{db_name}_{threading.get_ident()}"
        
        # Periodic cleanup
        self._periodic_cleanup()
        
        try:
            # Try to get existing connection
            with self._lock:
                if connection_key in self.connections:
                    conn_info = self.connections[connection_key]
                    if not conn_info.is_busy:
                        conn_info.is_busy = True
                        conn_info.last_used = datetime.now()
                        conn_info.usage_count += 1
                        try:
                            yield conn_info.connection
                            return
                        finally:
                            conn_info.is_busy = False
            
            # Create new connection with retry logic
            connection = self._create_connection_with_retry(db_name, db_path)
            
            # Store connection info
            with self._lock:
                conn_info = ConnectionInfo(
                    connection=connection,
                    created_at=datetime.now(),
                    last_used=datetime.now(),
                    thread_id=threading.get_ident(),
                    is_busy=True,
                    usage_count=1
                )
                self.connections[connection_key] = conn_info
            
            try:
                yield connection
            finally:
                # Release connection
                with self._lock:
                    if connection_key in self.connections:
                        self.connections[connection_key].is_busy = False
                        
        except Exception as e:
            self.logger.error(f"Database connection error for {db_name}: {e}")
            raise
    
    def _create_connection_with_retry(self, db_name: str, db_path: str) -> sqlite3.Connection:
        """Create database connection with retry logic"""
        for attempt in range(self.max_retries):
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                
                # Create connection with proper settings
                connection = sqlite3.connect(
                    db_path,
                    timeout=self.connection_timeout,
                    isolation_level=None,  # Autocommit mode
                    check_same_thread=False
                )
                
                # Configure for better performance and reliability
                connection.execute("PRAGMA journal_mode=WAL")
                connection.execute("PRAGMA synchronous=NORMAL")
                connection.execute("PRAGMA temp_store=MEMORY")
                connection.execute("PRAGMA mmap_size=268435456")  # 256MB
                connection.execute(f"PRAGMA busy_timeout={int(self.connection_timeout * 1000)}")
                
                self.logger.debug(f"Created database connection for '{db_name}'")
                return connection
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < self.max_retries - 1:
                    self.logger.warning(f"Database locked, retrying in {self.retry_delay}s (attempt {attempt + 1})")
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    raise
        
        raise sqlite3.OperationalError(f"Could not acquire connection for '{db_name}' after {self.max_retries} attempts")
    
    def _periodic_cleanup(self):
        """Periodically clean up old connections"""
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        self._last_cleanup = current_time
        
        with self._lock:
            keys_to_remove = []
            for key, conn_info in self.connections.items():
                # Remove connections that are too old or unused
                age = (datetime.now() - conn_info.created_at).total_seconds()
                idle_time = (datetime.now() - conn_info.last_used).total_seconds()
                
                if (age > 3600 or idle_time > 1800) and not conn_info.is_busy:  # 1 hour max age, 30 min idle
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                conn_info = self.connections[key]
                try:
                    conn_info.connection.close()
                    self.logger.debug(f"Cleaned up old connection: {key}")
                except:
                    pass
                del self.connections[key]
    
    def close_all_connections(self):
        """Close all database connections"""
        with self._lock:
            for conn_info in self.connections.values():
                try:
                    conn_info.connection.close()
                except:
                    pass
            self.connections.clear()
        
        self.logger.info("All database connections closed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        with self._lock:
            active_connections = len([c for c in self.connections.values() if c.is_busy])
            total_connections = len(self.connections)
            
            return {
                'total_connections': total_connections,
                'active_connections': active_connections,
                'max_connections': self.max_connections,
                'connection_details': {
                    key: {
                        'created_at': info.created_at.isoformat(),
                        'last_used': info.last_used.isoformat(),
                        'usage_count': info.usage_count,
                        'is_busy': info.is_busy
                    }
                    for key, info in self.connections.items()
                }
            }

class ConflictPrevention:
    """
    Resource conflict prevention system
    
    Prevents:
    - Database locking conflicts
    - Session file conflicts  
    - File lock conflicts
    """
    
    def __init__(self, lock_directory: str = "data/locks"):
        self.lock_directory = Path(lock_directory)
        self.lock_directory.mkdir(parents=True, exist_ok=True)
        
        self._active_locks: Dict[str, Any] = {}
        self._process_id = os.getpid()
        self.logger = logging.getLogger(__name__)
    
    async def setup(self):
        """Setup conflict prevention"""
        self.logger.info("🛡️  Setting up conflict prevention...")
        
        # Clean up any orphaned locks from previous runs
        await self._cleanup_orphaned_locks()
        
        self.logger.info("✅ Conflict prevention ready")
    
    @asynccontextmanager
    async def acquire_file_lock(self, resource_name: str, lock_type: str = "exclusive"):
        """
        Acquire file lock for resource with automatic cleanup
        
        Args:
            resource_name: Name of the resource to lock
            lock_type: Type of lock (exclusive, shared)
            
        Yields:
            True if lock acquired successfully
        """
        lock_file = self.lock_directory / f"{resource_name}.lock"
        
        try:
            # Check if already locked by another process
            if lock_file.exists():
                if not await self._is_lock_stale(lock_file):
                    raise Exception(f"Resource {resource_name} is locked by another process")
                else:
                    # Remove stale lock
                    lock_file.unlink()
            
            # Create lock file with process info
            lock_info = {
                'process_id': self._process_id,
                'timestamp': datetime.now().isoformat(),
                'lock_type': lock_type,
                'resource_name': resource_name
            }
            
            with open(lock_file, 'w') as f:
                json.dump(lock_info, f)
                # File locking - basic implementation for cross-platform compatibility
            
            # Track lock
            self._active_locks[resource_name] = {
                'lock_file': lock_file,
                'process_id': self._process_id,
                'created_at': datetime.now(),
                'lock_type': lock_type
            }
            
            self.logger.debug(f"🔒 Acquired lock: {resource_name}")
            
            try:
                yield True
            finally:
                # Release lock
                await self._release_lock(resource_name)
                
        except (IOError, OSError) as e:
            raise Exception(f"Failed to acquire lock for {resource_name}: {e}")
    
    async def _release_lock(self, resource_name: str):
        """Release file lock for resource"""
        if resource_name in self._active_locks:
            lock_info = self._active_locks[resource_name]
            try:
                if lock_info['lock_file'].exists():
                    lock_info['lock_file'].unlink()
                del self._active_locks[resource_name]
                self.logger.debug(f"🔓 Released lock: {resource_name}")
            except Exception as e:
                self.logger.error(f"❌ Failed to release lock {resource_name}: {e}")
    
    async def _is_lock_stale(self, lock_file: Path, max_age_minutes: int = 30) -> bool:
        """Check if lock file is stale (from crashed process)"""
        try:
            # Check file age
            stat = lock_file.stat()
            age = datetime.now() - datetime.fromtimestamp(stat.st_mtime)
            
            if age > timedelta(minutes=max_age_minutes):
                return True
            
            # Check if process is still running
            try:
                with open(lock_file, 'r') as f:
                    lock_info = json.load(f)
                    pid = lock_info.get('process_id')
                    
                    if pid:
                        # Try to check if process exists
                        os.kill(pid, 0)  # Doesn't actually kill, just checks
                        return False  # Process exists, lock is valid
                    
            except (json.JSONDecodeError, KeyError, OSError, ProcessLookupError):
                return True  # Process doesn't exist or invalid lock file
            
            return True
            
        except Exception:
            return True  # If we can't read it, consider it stale
    
    async def _cleanup_orphaned_locks(self):
        """Clean up orphaned lock files"""
        cleaned_count = 0
        for lock_file in self.lock_directory.glob("*.lock"):
            if await self._is_lock_stale(lock_file):
                try:
                    lock_file.unlink()
                    cleaned_count += 1
                except Exception as e:
                    self.logger.warning(f"⚠️  Failed to clean orphaned lock {lock_file}: {e}")
        
        if cleaned_count > 0:
            self.logger.info(f"🗑️  Cleaned up {cleaned_count} orphaned locks")
    
    async def cleanup(self):
        """Cleanup all locks created by this process"""
        self.logger.info("🧹 Cleaning up conflict prevention...")
        
        for resource_name in list(self._active_locks.keys()):
            await self._release_lock(resource_name)
        
        self.logger.info("✅ Conflict prevention cleanup completed")

class ResourceManager:
    """
    Centralized resource management system
    
    Manages:
    - Database connections
    - File locks
    - Session management
    - Cache systems
    """
    
    def __init__(self, config):
        self.config = config
        self.db_manager = DatabaseConnectionManager(
            max_connections=config.resources.connection_pool_size,
            connection_timeout=config.resources.connection_timeout
        )
        self.conflict_prevention = ConflictPrevention()
        self.logger = logging.getLogger(__name__)
        self._initialized = False
    
    async def initialize(self):
        """Initialize all resource managers"""
        if self._initialized:
            return True
            
        try:
            await self.conflict_prevention.setup()
            self._initialized = True
            self.logger.info("✅ Resource manager initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Resource manager initialization failed: {e}")
            return False
    
    def get_database_connection(self, db_name: str, db_path: Optional[str] = None):
        """Get database connection with conflict prevention"""
        return self.db_manager.get_connection(db_name, db_path)
    
    async def acquire_file_lock(self, resource_name: str, lock_type: str = "exclusive"):
        """Acquire file lock for resource"""
        return self.conflict_prevention.acquire_file_lock(resource_name, lock_type)
    
    async def cleanup(self):
        """Cleanup all resources"""
        try:
            await self.conflict_prevention.cleanup()
            self.db_manager.close_all_connections()
            self.logger.info("✅ Resource manager cleanup completed")
        except Exception as e:
            self.logger.error(f"❌ Resource cleanup error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive resource statistics"""
        return {
            'database': self.db_manager.get_stats(),
            'active_locks': len(self.conflict_prevention._active_locks),
            'initialized': self._initialized
        }

# Global resource manager
_resource_manager: Optional[ResourceManager] = None

def get_resource_manager(config=None) -> ResourceManager:
    """Get the global resource manager instance"""
    global _resource_manager
    if _resource_manager is None:
        if config is None:
            from ..config import get_config
            config = get_config()
        _resource_manager = ResourceManager(config)
    return _resource_manager

def reset_resource_manager():
    """Reset resource manager (useful for testing)"""
    global _resource_manager
    if _resource_manager:
        import asyncio
        asyncio.create_task(_resource_manager.cleanup())
    _resource_manager = None
