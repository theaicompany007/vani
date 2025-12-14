"""
Redis cache client with automatic in-memory fallback
Provides caching for API responses to improve performance
"""
import os
import json
import logging
from functools import wraps
from typing import Optional, Any, Callable, Dict
from flask import request, jsonify

logger = logging.getLogger(__name__)

# Try to import and connect to Redis
REDIS_AVAILABLE = False
redis_client = None

try:
    import redis
    redis_host = os.getenv('REDIS_HOST', '127.0.0.1')  # Default to 127.0.0.1 for WSL compatibility
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    redis_password_raw = os.getenv('REDIS_PASSWORD', None)
    redis_db = int(os.getenv('REDIS_DB', 0))
    
    # Normalize password: treat empty string, whitespace-only, or placeholder text as None
    redis_password = None
    if redis_password_raw:
        redis_password_raw = redis_password_raw.strip()
        
        # Remove comment prefix if present (e.g., "# Optional password")
        if redis_password_raw.startswith('#'):
            redis_password_raw = redis_password_raw[1:].strip()
        
        # Common placeholder values that should be treated as "no password"
        placeholder_values = ['', 'none', 'null', 'i have set it', 'set', 'yes', 'true', 'false', 
                              'optional', 'not set', 'not configured', 'leave empty', 'empty']
        
        # Check if it's a placeholder (exact match or contains placeholder text)
        is_placeholder = (
            redis_password_raw.lower() in placeholder_values or
            any(placeholder in redis_password_raw.lower() for placeholder in ['optional', 'not set', 'not configured', 'leave empty'])
        )
        
        if not is_placeholder and redis_password_raw:
            # Only use if it's a real password (not a placeholder)
            redis_password = redis_password_raw
    
    # Build Redis config - DO NOT include password key at all if None
    redis_config = {
        'host': redis_host,
        'port': redis_port,
        'db': redis_db,
        'decode_responses': True,
        'socket_connect_timeout': 3,  # Slightly longer for WSL
        'socket_timeout': 3,
        'retry_on_timeout': False
    }
    
    # Only add password key if we have a real password value
    # This is critical - Redis client will try to authenticate if password key exists, even if value is None
    if redis_password:
        redis_config['password'] = redis_password
        logger.debug(f"Redis: Using password authentication")
    else:
        logger.debug(f"Redis: No password (password not configured or placeholder detected)")
    
    redis_client = redis.Redis(**redis_config)
    
    # Test connection
    redis_client.ping()
    REDIS_AVAILABLE = True
    password_info = "with password" if redis_password else "no password"
    logger.info(f"✅ Redis connected: {redis_host}:{redis_port} (db={redis_db}, {password_info})")
except ImportError:
    REDIS_AVAILABLE = False
    redis_client = None
    logger.warning("⚠️ Redis package not installed. Install with: pip install redis>=5.0.0")
except redis.ConnectionError as e:
    REDIS_AVAILABLE = False
    redis_client = None
    logger.warning(f"⚠️ Redis connection failed ({redis_host}:{redis_port}), using in-memory cache: {e}")
    logger.info("💡 Tip: Make sure Redis is running. For WSL: sudo service redis-server start")
except redis.AuthenticationError as e:
    REDIS_AVAILABLE = False
    redis_client = None
    logger.warning(f"⚠️ Redis authentication failed ({redis_host}:{redis_port}), using in-memory cache: {e}")
    logger.info("💡 Tip: If Redis doesn't require a password, remove REDIS_PASSWORD from .env.local or set it to empty: REDIS_PASSWORD=")
except Exception as e:
    REDIS_AVAILABLE = False
    redis_client = None
    logger.warning(f"⚠️ Redis unavailable, using in-memory cache: {e}")

# Import in-memory cache fallback
from app.integrations.cache_client import cache as in_memory_cache


def get_cache_key(prefix: str, **kwargs) -> str:
    """
    Build a cache key from prefix and parameters
    Args:
        prefix: Cache key prefix (e.g., 'targets')
        **kwargs: Key-value pairs to include in cache key
    Returns:
        Cache key string
    """
    # Sort kwargs for consistent key generation
    sorted_kwargs = sorted(kwargs.items())
    key_parts = [prefix] + [f"{k}:{v}" for k, v in sorted_kwargs if v is not None]
    return ":".join(key_parts)


def cache_response(ttl: int = 300, key_prefix: str = "api"):
    """
    Decorator to cache API responses
    Uses Redis if available, falls back to in-memory cache
    
    Args:
        ttl: Time-to-live in seconds (default: 5 minutes)
        key_prefix: Prefix for cache keys (default: 'api')
    
    Example:
        @cache_response(ttl=300, key_prefix='targets')
        def list_targets():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            from app.auth import get_current_user
            
            # Build cache key from function name, user, and request parameters
            user = get_current_user()
            user_id = str(user.id) if user else 'anonymous'
            
            # Get relevant request parameters for cache key
            cache_params = {
                'user_id': user_id,
                'industry': request.args.get('industry', 'all'),
                'status': request.args.get('status', 'all'),
                'company': request.args.get('company', 'all'),
                'limit': request.args.get('limit', '100'),
                'offset': request.args.get('offset', '0'),
            }
            
            # Add any kwargs that affect the response
            for key, value in kwargs.items():
                if key not in ['self', 'current_app'] and value is not None:
                    cache_params[key] = str(value)
            
            cache_key = get_cache_key(key_prefix, **cache_params)
            
            # Try Redis first, fallback to in-memory
            cached_response = None
            if REDIS_AVAILABLE:
                try:
                    cached = redis_client.get(cache_key)
                    if cached:
                        cached_response = json.loads(cached)
                        logger.debug(f"✅ Cache HIT (Redis): {cache_key}")
                except Exception as e:
                    logger.warning(f"Redis read error, using fallback: {e}")
            
            # Fallback to in-memory cache
            if cached_response is None:
                cached_response = in_memory_cache.get(cache_key)
                if cached_response:
                    logger.debug(f"✅ Cache HIT (In-Memory): {cache_key}")
            
            # Return cached response if found
            if cached_response:
                return jsonify(cached_response)
            
            # Cache miss - execute function
            logger.debug(f"❌ Cache MISS: {cache_key}")
            result = func(*args, **kwargs)
            
            # Extract JSON data from Flask response
            response_data = None
            if isinstance(result, tuple) and len(result) == 2:
                # Flask can return (response, status_code)
                response_obj = result[0]
                if hasattr(response_obj, 'get_json'):
                    response_data = response_obj.get_json()
                elif hasattr(response_obj, 'data'):
                    try:
                        response_data = json.loads(response_obj.data)
                    except:
                        pass
            elif hasattr(result, 'get_json'):
                # Direct Flask Response object
                response_data = result.get_json()
            elif hasattr(result, 'data'):
                # Response object with data attribute
                try:
                    response_data = json.loads(result.data)
                except:
                    pass
            
            # Cache the response if we got valid JSON
            if response_data:
                try:
                    if REDIS_AVAILABLE:
                        try:
                            redis_client.setex(cache_key, ttl, json.dumps(response_data))
                            logger.debug(f"💾 Cached in Redis: {cache_key} (TTL: {ttl}s)")
                        except Exception as e:
                            logger.warning(f"Redis write error: {e}")
                            # Fallback to in-memory
                            in_memory_cache.set(cache_key, response_data, ttl)
                    else:
                        in_memory_cache.set(cache_key, response_data, ttl)
                        logger.debug(f"💾 Cached in-memory: {cache_key} (TTL: {ttl}s)")
                except Exception as e:
                    logger.warning(f"Error caching response: {e}")
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """
    Invalidate cache entries matching a pattern
    Args:
        pattern: Pattern to match (e.g., 'targets:*' or 'targets:industry:123:*')
    
    Example:
        invalidate_cache('targets:*')  # Clear all target caches
        invalidate_cache('targets:industry:123:*')  # Clear caches for industry 123
    """
    if REDIS_AVAILABLE:
        try:
            # Redis pattern deletion
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                logger.info(f"🗑️ Invalidated {len(keys)} Redis cache keys matching: {pattern}")
        except Exception as e:
            logger.warning(f"Redis invalidation error: {e}")
            # Fallback to in-memory
            in_memory_cache.clear_pattern(pattern)
    else:
        # In-memory pattern deletion
        in_memory_cache.clear_pattern(pattern)
        logger.info(f"🗑️ Invalidated in-memory cache keys matching: {pattern}")


def clear_all_cache():
    """Clear all cache entries (use with caution)"""
    if REDIS_AVAILABLE:
        try:
            redis_client.flushdb()
            logger.warning("🗑️ Cleared all Redis cache")
        except Exception as e:
            logger.warning(f"Error clearing Redis cache: {e}")
    
    in_memory_cache.clear()
    logger.warning("🗑️ Cleared all in-memory cache")


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics
    Returns:
        Dictionary with cache statistics
    """
    stats = {
        'redis_available': REDIS_AVAILABLE,
        'in_memory_size': in_memory_cache.size(),
    }
    
    if REDIS_AVAILABLE:
        try:
            stats['redis_info'] = redis_client.info('memory')
            stats['redis_db_size'] = redis_client.dbsize()
        except Exception as e:
            stats['redis_error'] = str(e)
    
    return stats

