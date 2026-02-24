"""
Cache initialization and configuration
"""
import os
import logging
from flask import Flask
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Global cache instance
cache = None

def init_cache(app: Flask) -> Optional[Any]:
    """
    Initialize cache system with Redis fallback to memory
    """
    global cache
    
    cache_type = os.getenv('CACHE_TYPE', 'redis' if app.config.get('FLASK_ENV') == 'production' else 'memory')
    
    if cache_type == 'redis':
        try:
            from .redis_cache import RedisCache
            redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            cache = RedisCache(redis_url)
            logger.info(f"Redis cache initialized: {redis_url.split('@')[-1]}")
            return cache
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {e}. Falling back to memory cache.")
            cache_type = 'memory'
    
    if cache_type == 'memory':
        from .memory_cache import MemoryCache
        max_size = app.config.get('CACHE_MAX_SIZE', 1000)
        cache = MemoryCache(max_size=max_size)
        logger.info(f"Memory cache initialized with max size: {max_size}")

    warm_cache()
    return cache

def warm_cache():
    """Pre-populate cache with rarely-changing data on startup."""
    if cache is None:
        return

    try:
        from ..processors import processor_registry
        supported = processor_registry.list_supported_documents()
        cache.set('processors:supported_documents', supported, ttl=86400)
        logger.info("Cache warmed: %d supported document types cached", len(supported))
    except Exception as e:
        logger.warning("Cache warming failed (non-fatal): %s", e)


def get_cache():
    """Get the current cache instance"""
    return cache

# Export cache operations
__all__ = ['init_cache', 'get_cache', 'warm_cache', 'cache']