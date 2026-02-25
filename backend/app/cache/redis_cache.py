"""
Redis-based caching system for OCR results and document processing
"""
import redis
import json
import hashlib
import pickle
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
from functools import wraps
import os

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache manager for OCR results and document processing"""
    
    def __init__(self, redis_url: str = None, default_ttl: int = 3600):
        """
        Initialize Redis cache
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live in seconds
        """
        self.redis_url = redis_url or os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        self.default_ttl = default_ttl
        self.redis_client = None
        self.is_available = False
        
        self._connect()
    
    def _connect(self):
        """Connect to Redis with socket timeouts to prevent hanging (Q3)."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
            # Test connection
            self.redis_client.ping()
            self.is_available = True
            self._last_reconnect_attempt = 0
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning("Redis cache not available: %s", e)
            self.is_available = False
            self.redis_client = None

    def _reconnect_if_needed(self):
        """
        Attempt reconnection if Redis was previously unavailable (Q1).

        Uses a cooldown of 5 seconds between attempts to avoid
        hammering a dead Redis instance.
        """
        if self.is_available:
            return
        import time as _time
        now = _time.time()
        if now - getattr(self, '_last_reconnect_attempt', 0) < 5:
            return  # Cooldown not elapsed
        self._last_reconnect_attempt = now
        try:
            from ..monitoring import redis_reconnection_attempts
            redis_reconnection_attempts.labels(result='attempt').inc()
        except Exception:
            pass
        logger.info("Attempting Redis reconnection...")
        self._connect()
        try:
            from ..monitoring import redis_reconnection_attempts
            result = 'success' if self.is_available else 'failure'
            redis_reconnection_attempts.labels(result=result).inc()
        except Exception:
            pass
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """Generate cache key from data"""
        if isinstance(data, dict):
            # Sort dictionary for consistent hashing
            data_str = json.dumps(data, sort_keys=True)
        elif isinstance(data, (list, tuple)):
            data_str = json.dumps(data)
        else:
            data_str = str(data)
        
        # Create hash of the data
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        return f"{prefix}:{data_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.is_available:
            self._reconnect_if_needed()
        if not self.is_available:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                try:
                    return pickle.loads(value.encode('latin-1'))
                except:
                    return value
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache"""
        if not self.is_available:
            self._reconnect_if_needed()
        if not self.is_available:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            
            # Try to serialize as JSON first, then pickle
            try:
                serialized_value = json.dumps(value)
            except (TypeError, ValueError):
                try:
                    serialized_value = pickle.dumps(value).decode('latin-1')
                except:
                    serialized_value = str(value)
            
            self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.is_available:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.is_available:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern using SCAN (non-blocking, Q2)."""
        if not self.is_available:
            return 0

        try:
            deleted = 0
            cursor = 0
            while True:
                cursor, keys = self.redis_client.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    deleted += self.redis_client.delete(*keys)
                if cursor == 0:
                    break
            return deleted
        except Exception as e:
            logger.error("Error clearing cache pattern %s: %s", pattern, e)
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.is_available:
            return {'available': False}
        
        try:
            info = self.redis_client.info()
            return {
                'available': True,
                'used_memory': info.get('used_memory_human', 'N/A'),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(info)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'available': False, 'error': str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round((hits / total) * 100, 2)

class OCRCache:
    """Specialized cache for OCR results"""
    
    def __init__(self, redis_cache: RedisCache):
        self.cache = redis_cache
        self.prefix = "ocr"
    
    def get_ocr_result(self, image_hash: str, document_type: str = None) -> Optional[Dict]:
        """Get cached OCR result"""
        key_data = {'image_hash': image_hash}
        if document_type:
            key_data['document_type'] = document_type
        
        key = self.cache._generate_key(self.prefix, key_data)
        return self.cache.get(key)
    
    def set_ocr_result(self, image_hash: str, result: Dict, document_type: str = None, ttl: int = None) -> bool:
        """Cache OCR result"""
        key_data = {'image_hash': image_hash}
        if document_type:
            key_data['document_type'] = document_type
        
        key = self.cache._generate_key(self.prefix, key_data)
        
        # Add metadata
        cached_result = {
            'result': result,
            'cached_at': datetime.now().isoformat(),
            'document_type': document_type,
            'image_hash': image_hash
        }
        
        return self.cache.set(key, cached_result, ttl or 3600)  # 1 hour default
    
    def clear_ocr_cache(self) -> int:
        """Clear all OCR cache"""
        return self.cache.clear_pattern(f"{self.prefix}:*")

class DocumentCache:
    """Specialized cache for document processing results"""
    
    def __init__(self, redis_cache: RedisCache):
        self.cache = redis_cache
        self.prefix = "doc"
    
    def get_document_result(self, document_data: Dict) -> Optional[Dict]:
        """Get cached document processing result"""
        key = self.cache._generate_key(self.prefix, document_data)
        return self.cache.get(key)
    
    def set_document_result(self, document_data: Dict, result: Dict, ttl: int = None) -> bool:
        """Cache document processing result"""
        key = self.cache._generate_key(self.prefix, document_data)
        
        # Add metadata
        cached_result = {
            'result': result,
            'cached_at': datetime.now().isoformat(),
            'document_data_hash': key
        }
        
        return self.cache.set(key, cached_result, ttl or 7200)  # 2 hours default
    
    def clear_document_cache(self) -> int:
        """Clear all document cache"""
        return self.cache.clear_pattern(f"{self.prefix}:*")

class SessionCache:
    """Specialized cache for user sessions and temporary data"""
    
    def __init__(self, redis_cache: RedisCache):
        self.cache = redis_cache
        self.prefix = "session"
    
    def get_session_data(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        key = f"{self.prefix}:{session_id}"
        return self.cache.get(key)
    
    def set_session_data(self, session_id: str, data: Dict, ttl: int = None) -> bool:
        """Set session data"""
        key = f"{self.prefix}:{session_id}"
        return self.cache.set(key, data, ttl or 1800)  # 30 minutes default
    
    def clear_session(self, session_id: str) -> bool:
        """Clear specific session"""
        key = f"{self.prefix}:{session_id}"
        return self.cache.delete(key)

class CacheManager:
    """Main cache manager combining all cache types"""
    
    def __init__(self, redis_url: str = None):
        self.redis_cache = RedisCache(redis_url)
        self.ocr_cache = OCRCache(self.redis_cache)
        self.document_cache = DocumentCache(self.redis_cache)
        self.session_cache = SessionCache(self.redis_cache)
    
    def is_available(self) -> bool:
        """Check if cache is available"""
        return self.redis_cache.is_available
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics using SCAN (non-blocking, Q2)."""
        stats = self.redis_cache.get_stats()

        if stats.get('available') and self.redis_cache.redis_client:
            # Use SCAN instead of KEYS to avoid blocking Redis (Q2)
            stats.update({
                'ocr_cache_keys': self._count_keys("ocr:*"),
                'document_cache_keys': self._count_keys("doc:*"),
                'session_cache_keys': self._count_keys("session:*"),
            })

        return stats

    def _count_keys(self, pattern: str) -> int:
        """Count keys matching pattern using non-blocking SCAN."""
        try:
            count = 0
            cursor = 0
            while True:
                cursor, keys = self.redis_cache.redis_client.scan(
                    cursor=cursor, match=pattern, count=100
                )
                count += len(keys)
                if cursor == 0:
                    break
            return count
        except Exception:
            return 0
    
    def clear_all(self) -> Dict[str, int]:
        """Clear all caches"""
        return {
            'ocr_cache': self.ocr_cache.clear_ocr_cache(),
            'document_cache': self.document_cache.clear_document_cache(),
            'session_cache': self.redis_cache.clear_pattern("session:*")
        }

# Global cache manager instance
cache_manager = CacheManager()

def cached_ocr_result(ttl: int = 3600):
    """Decorator to cache OCR results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cache_manager.is_available():
                return func(*args, **kwargs)
            
            # Generate cache key from function arguments
            cache_key_data = {
                'func_name': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            
            # Try to get from cache first
            cached_result = cache_manager.document_cache.get_document_result(cache_key_data)
            if cached_result:
                logger.info(f"Cache hit for {func.__name__}")
                return cached_result['result']
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            if result:  # Only cache non-empty results
                cache_manager.document_cache.set_document_result(cache_key_data, result, ttl)
                logger.info(f"Cached result for {func.__name__}")
            
            return result
        
        return wrapper
    return decorator

def image_hash(image_data: bytes) -> str:
    """Generate hash for image data"""
    return hashlib.sha256(image_data).hexdigest()

def warm_cache():
    """Warm up cache with common data"""
    if not cache_manager.is_available():
        return
    
    try:
        # Pre-load commonly used data
        logger.info("Warming up cache...")
        
        # Add any initialization data here
        # For example, commonly used ML models, configuration data, etc.
        
        logger.info("Cache warmed up successfully")
    except Exception as e:
        logger.error(f"Error warming up cache: {e}")

def cleanup_expired_cache():
    """Clean up expired cache entries (Redis handles this automatically, but we can add custom logic)"""
    if not cache_manager.is_available():
        return
    
    try:
        # Add custom cleanup logic here if needed
        # Redis automatically handles TTL expiration
        logger.info("Cache cleanup completed")
    except Exception as e:
        logger.error(f"Error during cache cleanup: {e}")