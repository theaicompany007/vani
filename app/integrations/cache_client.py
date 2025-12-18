"""
In-memory cache client with TTL support
Used as fallback when Redis is unavailable
"""
import time
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class InMemoryCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize in-memory cache
        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        Args:
            key: Cache key
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if time.time() > entry['expires_at']:
            del self._cache[key]
            return None
        
        return entry['data']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not provided)
        """
        ttl = ttl or self._default_ttl
        self._cache[key] = {
            'data': value,
            'expires_at': time.time() + ttl
        }
    
    def delete(self, key: str):
        """
        Delete key from cache
        Args:
            key: Cache key to delete
        """
        if key in self._cache:
            del self._cache[key]
    
    def clear_pattern(self, pattern: str):
        """
        Clear all keys matching pattern
        Args:
            pattern: Pattern to match (e.g., 'targets:*')
        """
        prefix = pattern.rstrip('*')
        keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
        for key in keys_to_delete:
            del self._cache[key]
        logger.debug(f"Cleared {len(keys_to_delete)} keys matching pattern: {pattern}")
    
    def clear(self):
        """Clear all cache entries"""
        count = len(self._cache)
        self._cache.clear()
        logger.debug(f"Cleared all cache entries ({count} keys)")
    
    def size(self) -> int:
        """Get number of cached entries"""
        return len(self._cache)


# Global cache instance
cache = InMemoryCache(default_ttl=300)





