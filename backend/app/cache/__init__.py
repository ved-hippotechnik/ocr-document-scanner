"""
Unified caching system with Redis primary and memory fallback
"""
import os
import logging
from typing import Any, Optional, Dict, List
from functools import wraps

logger = logging.getLogger(__name__)

class UnifiedCacheManager:
    """Unified cache manager that uses Redis when available, falls back to memory cache"""
    
    def __init__(self):
        self.redis_cache = None
        self.memory_cache = None
        self.primary_cache = None
        self.fallback_cache = None
        
        self._initialize_caches()
    
    def _initialize_caches(self):
        """Initialize cache systems"""
        # Try to initialize Redis cache
        try:
            from .redis_cache import cache_manager as redis_cache
            if redis_cache.is_available():
                self.redis_cache = redis_cache
                self.primary_cache = redis_cache
                logger.info("✅ Using Redis as primary cache")
            else:
                logger.warning("⚠️  Redis cache not available")
        except ImportError:
            logger.warning("⚠️  Redis dependencies not available")
        
        # Initialize memory cache as fallback
        try:
            from .memory_cache import memory_cache_manager
            self.memory_cache = memory_cache_manager
            
            if self.primary_cache is None:
                self.primary_cache = memory_cache_manager
                logger.info("✅ Using Memory cache as primary cache")
            else:
                self.fallback_cache = memory_cache_manager
                logger.info("✅ Memory cache available as fallback")
        except ImportError:
            logger.error("❌ Memory cache initialization failed")
    
    def is_available(self) -> bool:
        """Check if any cache is available"""
        return self.primary_cache is not None
    
    def get_ocr_result(self, image_hash: str, document_type: str = None) -> Optional[Dict]:
        """Get cached OCR result"""
        if not self.is_available():
            return None
        
        try:
            result = self.primary_cache.get_ocr_result(image_hash, document_type)
            if result:
                return result
            
            # Try fallback cache if available
            if self.fallback_cache:
                return self.fallback_cache.get_ocr_result(image_hash, document_type)
            
            return None
        except Exception as e:
            logger.error(f"Error getting OCR result from cache: {e}")
            return None
    
    def set_ocr_result(self, image_hash: str, result: Dict, document_type: str = None, ttl: int = None) -> bool:
        """Cache OCR result"""
        if not self.is_available():
            return False
        
        success = False
        
        try:
            # Set in primary cache
            if self.primary_cache:
                success = self.primary_cache.set_ocr_result(image_hash, result, document_type, ttl)
            
            # Also set in fallback cache for redundancy
            if self.fallback_cache:
                self.fallback_cache.set_ocr_result(image_hash, result, document_type, ttl)
            
            return success
        except Exception as e:
            logger.error(f"Error setting OCR result in cache: {e}")
            return False
    
    def get_document_result(self, document_data: Dict) -> Optional[Dict]:
        """Get cached document processing result"""
        if not self.is_available():
            return None
        
        try:
            result = self.primary_cache.get_document_result(document_data)
            if result:
                return result
            
            # Try fallback cache if available
            if self.fallback_cache:
                return self.fallback_cache.get_document_result(document_data)
            
            return None
        except Exception as e:
            logger.error(f"Error getting document result from cache: {e}")
            return None
    
    def set_document_result(self, document_data: Dict, result: Dict, ttl: int = None) -> bool:
        """Cache document processing result"""
        if not self.is_available():
            return False
        
        success = False
        
        try:
            # Set in primary cache
            if self.primary_cache:
                success = self.primary_cache.set_document_result(document_data, result, ttl)
            
            # Also set in fallback cache for redundancy
            if self.fallback_cache:
                self.fallback_cache.set_document_result(document_data, result, ttl)
            
            return success
        except Exception as e:
            logger.error(f"Error setting document result in cache: {e}")
            return False
    
    def get_session_data(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        if not self.is_available():
            return None
        
        try:
            return self.primary_cache.get_session_data(session_id)
        except Exception as e:
            logger.error(f"Error getting session data: {e}")
            return None
    
    def set_session_data(self, session_id: str, data: Dict, ttl: int = None) -> bool:
        """Set session data"""
        if not self.is_available():
            return False
        
        try:
            return self.primary_cache.set_session_data(session_id, data, ttl)
        except Exception as e:
            logger.error(f"Error setting session data: {e}")
            return False
    
    def clear_session(self, session_id: str) -> bool:
        """Clear specific session"""
        if not self.is_available():
            return False
        
        try:
            success = self.primary_cache.clear_session(session_id)
            
            # Also clear from fallback cache
            if self.fallback_cache:
                self.fallback_cache.clear_session(session_id)
            
            return success
        except Exception as e:
            logger.error(f"Error clearing session: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        if not self.is_available():
            return {'available': False}
        
        try:
            stats = {
                'available': True,
                'primary_cache': self.primary_cache.get_stats()
            }
            
            if self.fallback_cache:
                stats['fallback_cache'] = self.fallback_cache.get_stats()
            
            return stats
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'available': False, 'error': str(e)}
    
    def clear_all(self) -> Dict[str, Any]:
        """Clear all caches"""
        if not self.is_available():
            return {'cleared': False}
        
        try:
            result = {
                'primary_cache': self.primary_cache.clear_all()
            }
            
            if self.fallback_cache:
                result['fallback_cache'] = self.fallback_cache.clear_all()
            
            return result
        except Exception as e:
            logger.error(f"Error clearing all caches: {e}")
            return {'cleared': False, 'error': str(e)}

# Global unified cache manager
cache = UnifiedCacheManager()

def cached_result(cache_type: str = "document", ttl: int = 3600):
    """
    Decorator to cache function results
    
    Args:
        cache_type: Type of cache ("document", "ocr", "session")
        ttl: Time to live in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cache.is_available():
                return func(*args, **kwargs)
            
            # Generate cache key from function arguments
            cache_key_data = {
                'func_name': func.__name__,
                'args': str(args),
                'kwargs': str(sorted(kwargs.items()))
            }
            
            # Try to get from cache first
            if cache_type == "document":
                cached_result = cache.get_document_result(cache_key_data)
            elif cache_type == "ocr":
                # For OCR, we need image hash
                image_hash = kwargs.get('image_hash') or args[0] if args else None
                if image_hash:
                    cached_result = cache.get_ocr_result(image_hash, kwargs.get('document_type'))
                else:
                    cached_result = cache.get_document_result(cache_key_data)
            else:
                cached_result = cache.get_document_result(cache_key_data)
            
            if cached_result:
                logger.info(f"Cache hit for {func.__name__}")
                return cached_result.get('result', cached_result)
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            if result:  # Only cache non-empty results
                if cache_type == "document":
                    cache.set_document_result(cache_key_data, result, ttl)
                elif cache_type == "ocr":
                    image_hash = kwargs.get('image_hash') or args[0] if args else None
                    if image_hash:
                        cache.set_ocr_result(image_hash, result, kwargs.get('document_type'), ttl)
                    else:
                        cache.set_document_result(cache_key_data, result, ttl)
                else:
                    cache.set_document_result(cache_key_data, result, ttl)
                
                logger.info(f"Cached result for {func.__name__}")
            
            return result
        
        return wrapper
    return decorator

def warm_cache():
    """Warm up cache with common data"""
    if not cache.is_available():
        return
    
    try:
        logger.info("Warming up unified cache...")
        
        # Add any common data that should be pre-loaded
        # This could include ML models, configuration data, etc.
        
        logger.info("✅ Unified cache warmed up successfully")
    except Exception as e:
        logger.error(f"Error warming up cache: {e}")

# Export main interface
cache_manager = cache  # Alias for backward compatibility
__all__ = ['cache', 'cache_manager', 'cached_result', 'warm_cache']