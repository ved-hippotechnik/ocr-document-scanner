"""
In-memory cache implementation as fallback when Redis is not available
"""
import threading
import time
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
from collections import OrderedDict

logger = logging.getLogger(__name__)

class MemoryCache:
    """Thread-safe in-memory cache with TTL support"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize memory cache
        
        Args:
            max_size: Maximum number of items to store
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.lock = threading.RLock()
        self.access_count = 0
        self.hit_count = 0
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired, daemon=True)
        self.cleanup_thread.start()
        
        logger.info(f"✅ Memory cache initialized (max_size={max_size})")
    
    def _cleanup_expired(self):
        """Background thread to clean up expired entries"""
        while True:
            try:
                time.sleep(60)  # Check every minute
                current_time = time.time()
                
                with self.lock:
                    expired_keys = []
                    for key, (value, expiry) in self.cache.items():
                        if expiry < current_time:
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        del self.cache[key]
                    
                    if expired_keys:
                        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            except Exception as e:
                logger.error(f"Error in cache cleanup thread: {e}")
    
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
        """Get value from cache (thread-safe counters, Q2)"""
        with self.lock:
            self.access_count += 1

            if key not in self.cache:
                return None

            value, expiry = self.cache[key]

            # Check if expired
            if expiry < time.time():
                del self.cache[key]
                return None

            # Move to end (LRU)
            self.cache.move_to_end(key)
            self.hit_count += 1

            return value
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache"""
        with self.lock:
            ttl = ttl or self.default_ttl
            expiry = time.time() + ttl
            
            # Remove oldest items if cache is full
            while len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
            
            self.cache[key] = (value, expiry)
            return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        with self.lock:
            if key not in self.cache:
                return False
            
            # Check if expired
            _, expiry = self.cache[key]
            if expiry < time.time():
                del self.cache[key]
                return False
            
            return True
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern (simple prefix match)"""
        with self.lock:
            # Simple pattern matching - just prefix for now
            prefix = pattern.replace('*', '')
            
            keys_to_remove = []
            for key in self.cache:
                if key.startswith(prefix):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache[key]
            
            return len(keys_to_remove)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            hit_rate = 0.0
            if self.access_count > 0:
                hit_rate = (self.hit_count / self.access_count) * 100
            
            return {
                'available': True,
                'type': 'memory',
                'size': len(self.cache),
                'max_size': self.max_size,
                'hit_rate': round(hit_rate, 2),
                'access_count': self.access_count,
                'hit_count': self.hit_count
            }
    
    def clear_all(self) -> int:
        """Clear all cache entries"""
        with self.lock:
            count = len(self.cache)
            self.cache.clear()
            return count

class MemoryCacheManager:
    """Memory-based cache manager as fallback"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = MemoryCache(max_size)
    
    def is_available(self) -> bool:
        """Memory cache is always available"""
        return True
    
    def get_ocr_result(self, image_hash: str, document_type: str = None) -> Optional[Dict]:
        """Get cached OCR result"""
        key_data = {'image_hash': image_hash}
        if document_type:
            key_data['document_type'] = document_type
        
        key = self.cache._generate_key("ocr", key_data)
        return self.cache.get(key)
    
    def set_ocr_result(self, image_hash: str, result: Dict, document_type: str = None, ttl: int = None) -> bool:
        """Cache OCR result"""
        key_data = {'image_hash': image_hash}
        if document_type:
            key_data['document_type'] = document_type
        
        key = self.cache._generate_key("ocr", key_data)
        
        # Add metadata
        cached_result = {
            'result': result,
            'cached_at': datetime.now().isoformat(),
            'document_type': document_type,
            'image_hash': image_hash
        }
        
        return self.cache.set(key, cached_result, ttl or 3600)
    
    def get_document_result(self, document_data: Dict) -> Optional[Dict]:
        """Get cached document processing result"""
        key = self.cache._generate_key("doc", document_data)
        return self.cache.get(key)
    
    def set_document_result(self, document_data: Dict, result: Dict, ttl: int = None) -> bool:
        """Cache document processing result"""
        key = self.cache._generate_key("doc", document_data)
        
        # Add metadata
        cached_result = {
            'result': result,
            'cached_at': datetime.now().isoformat(),
            'document_data_hash': key
        }
        
        return self.cache.set(key, cached_result, ttl or 7200)
    
    def get_session_data(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        key = f"session:{session_id}"
        return self.cache.get(key)
    
    def set_session_data(self, session_id: str, data: Dict, ttl: int = None) -> bool:
        """Set session data"""
        key = f"session:{session_id}"
        return self.cache.set(key, data, ttl or 1800)
    
    def clear_session(self, session_id: str) -> bool:
        """Clear specific session"""
        key = f"session:{session_id}"
        return self.cache.delete(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats = self.cache.get_stats()
        
        # Add cache-specific stats
        ocr_keys = 0
        doc_keys = 0
        session_keys = 0
        
        for key in self.cache.cache:
            if key.startswith("ocr:"):
                ocr_keys += 1
            elif key.startswith("doc:"):
                doc_keys += 1
            elif key.startswith("session:"):
                session_keys += 1
        
        stats.update({
            'ocr_cache_keys': ocr_keys,
            'document_cache_keys': doc_keys,
            'session_cache_keys': session_keys
        })
        
        return stats
    
    def get_vision_result(self, image_hash: str, operation: str) -> Optional[Dict]:
        """Get cached Vision API result"""
        key = f"vision:{operation}:{image_hash}"
        return self.cache.get(key)

    def set_vision_result(self, image_hash: str, operation: str, result: Dict, ttl: int = None) -> bool:
        """Cache Vision API result (default TTL: 1 hour for classify, 30 min for validate)"""
        key = f"vision:{operation}:{image_hash}"
        default_ttl = 3600 if operation == 'classify' else 1800
        return self.cache.set(key, result, ttl or default_ttl)

    def clear_all(self) -> Dict[str, int]:
        """Clear all caches"""
        ocr_cleared = self.cache.clear_pattern("ocr:*")
        doc_cleared = self.cache.clear_pattern("doc:*")
        session_cleared = self.cache.clear_pattern("session:*")
        vision_cleared = self.cache.clear_pattern("vision:*")

        return {
            'ocr_cache': ocr_cleared,
            'document_cache': doc_cleared,
            'session_cache': session_cleared,
            'vision_cache': vision_cleared,
        }

# Global memory cache manager instance
memory_cache_manager = MemoryCacheManager()