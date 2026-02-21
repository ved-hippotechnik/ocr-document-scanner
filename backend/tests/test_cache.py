"""
Tests for caching system
"""
import unittest
import time
import json
from unittest.mock import patch, MagicMock

# Add the backend directory to the path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.cache.memory_cache import MemoryCache, MemoryCacheManager
from app.cache.redis_cache import RedisCache, OCRCache, DocumentCache, SessionCache


class TestMemoryCache(unittest.TestCase):
    """Test cases for memory cache"""
    
    def setUp(self):
        """Set up test environment"""
        self.cache = MemoryCache(max_size=10, default_ttl=1)
    
    def test_set_and_get(self):
        """Test basic set and get operations"""
        self.cache.set('key1', 'value1')
        self.assertEqual(self.cache.get('key1'), 'value1')
        
        # Test non-existent key
        self.assertIsNone(self.cache.get('nonexistent'))
    
    def test_ttl_expiration(self):
        """Test TTL expiration"""
        self.cache.set('key1', 'value1', ttl=1)
        self.assertEqual(self.cache.get('key1'), 'value1')
        
        # Wait for expiration
        time.sleep(1.1)
        self.assertIsNone(self.cache.get('key1'))
    
    def test_max_size_limit(self):
        """Test maximum size limit"""
        # Fill cache to max size
        for i in range(10):
            self.cache.set(f'key{i}', f'value{i}')
        
        # Add one more item (should evict oldest)
        self.cache.set('key10', 'value10')
        
        # First item should be evicted
        self.assertIsNone(self.cache.get('key0'))
        self.assertEqual(self.cache.get('key10'), 'value10')
    
    def test_delete(self):
        """Test delete operation"""
        self.cache.set('key1', 'value1')
        self.assertTrue(self.cache.delete('key1'))
        self.assertIsNone(self.cache.get('key1'))
        
        # Test deleting non-existent key
        self.assertFalse(self.cache.delete('nonexistent'))
    
    def test_exists(self):
        """Test exists operation"""
        self.cache.set('key1', 'value1')
        self.assertTrue(self.cache.exists('key1'))
        self.assertFalse(self.cache.exists('nonexistent'))
    
    def test_clear_pattern(self):
        """Test pattern clearing"""
        self.cache.set('prefix:key1', 'value1')
        self.cache.set('prefix:key2', 'value2')
        self.cache.set('other:key3', 'value3')
        
        cleared = self.cache.clear_pattern('prefix:*')
        self.assertEqual(cleared, 2)
        
        self.assertIsNone(self.cache.get('prefix:key1'))
        self.assertIsNone(self.cache.get('prefix:key2'))
        self.assertEqual(self.cache.get('other:key3'), 'value3')
    
    def test_stats(self):
        """Test cache statistics"""
        # Access some items
        self.cache.set('key1', 'value1')
        self.cache.get('key1')  # Hit
        self.cache.get('nonexistent')  # Miss
        
        stats = self.cache.get_stats()
        self.assertTrue(stats['available'])
        self.assertEqual(stats['type'], 'memory')
        self.assertEqual(stats['size'], 1)
        self.assertEqual(stats['access_count'], 2)
        self.assertEqual(stats['hit_count'], 1)
        self.assertEqual(stats['hit_rate'], 50.0)


class TestMemoryCacheManager(unittest.TestCase):
    """Test cases for memory cache manager"""
    
    def setUp(self):
        """Set up test environment"""
        self.cache_manager = MemoryCacheManager(max_size=100)
    
    def test_ocr_cache(self):
        """Test OCR result caching"""
        image_hash = 'test_hash_123'
        document_type = 'passport'
        result = {
            'document_type': document_type,
            'confidence': 0.95,
            'extracted_info': {'name': 'John Doe'}
        }
        
        # Set OCR result
        self.assertTrue(self.cache_manager.set_ocr_result(image_hash, result, document_type))
        
        # Get OCR result
        cached_result = self.cache_manager.get_ocr_result(image_hash, document_type)
        self.assertIsNotNone(cached_result)
        self.assertEqual(cached_result['result'], result)
        self.assertEqual(cached_result['document_type'], document_type)
    
    def test_document_cache(self):
        """Test document processing cache"""
        document_data = {
            'image_hash': 'test_hash_456',
            'processing_options': {'quality_check': True}
        }
        result = {
            'status': 'success',
            'processing_time': 2.5
        }
        
        # Set document result
        self.assertTrue(self.cache_manager.set_document_result(document_data, result))
        
        # Get document result
        cached_result = self.cache_manager.get_document_result(document_data)
        self.assertIsNotNone(cached_result)
        self.assertEqual(cached_result['result'], result)
    
    def test_session_cache(self):
        """Test session data caching"""
        session_id = 'session_123'
        session_data = {
            'user_id': 'user_456',
            'preferences': {'theme': 'dark'}
        }
        
        # Set session data
        self.assertTrue(self.cache_manager.set_session_data(session_id, session_data))
        
        # Get session data
        cached_data = self.cache_manager.get_session_data(session_id)
        self.assertEqual(cached_data, session_data)
        
        # Clear session
        self.assertTrue(self.cache_manager.clear_session(session_id))
        self.assertIsNone(self.cache_manager.get_session_data(session_id))
    
    def test_cache_stats(self):
        """Test cache statistics"""
        # Add some data
        self.cache_manager.set_ocr_result('hash1', {'result': 'data1'})
        self.cache_manager.set_document_result({'key': 'value'}, {'result': 'data2'})
        self.cache_manager.set_session_data('session1', {'data': 'value'})
        
        stats = self.cache_manager.get_stats()
        self.assertTrue(stats['available'])
        self.assertGreater(stats['size'], 0)
        self.assertEqual(stats['ocr_cache_keys'], 1)
        self.assertEqual(stats['document_cache_keys'], 1)
        self.assertEqual(stats['session_cache_keys'], 1)
    
    def test_clear_all(self):
        """Test clearing all caches"""
        # Add some data
        self.cache_manager.set_ocr_result('hash1', {'result': 'data1'})
        self.cache_manager.set_document_result({'key': 'value'}, {'result': 'data2'})
        self.cache_manager.set_session_data('session1', {'data': 'value'})
        
        # Clear all
        result = self.cache_manager.clear_all()
        self.assertIsInstance(result, dict)
        self.assertIn('ocr_cache', result)
        self.assertIn('document_cache', result)
        self.assertIn('session_cache', result)
        
        # Verify data is cleared
        self.assertIsNone(self.cache_manager.get_ocr_result('hash1'))
        self.assertIsNone(self.cache_manager.get_document_result({'key': 'value'}))
        self.assertIsNone(self.cache_manager.get_session_data('session1'))


class TestRedisCache(unittest.TestCase):
    """Test cases for Redis cache (mocked)"""
    
    def setUp(self):
        """Set up test environment"""
        self.redis_patcher = patch('app.cache.redis_cache.redis.from_url')
        self.mock_redis = self.redis_patcher.start()
        
        # Mock Redis client
        self.mock_client = MagicMock()
        self.mock_redis.return_value = self.mock_client
        self.mock_client.ping.return_value = True
        
        self.cache = RedisCache('redis://localhost:6379/0')
    
    def tearDown(self):
        """Clean up test environment"""
        self.redis_patcher.stop()
    
    def test_redis_connection(self):
        """Test Redis connection"""
        self.assertTrue(self.cache.is_available)
        self.mock_client.ping.assert_called_once()
    
    def test_redis_set_get(self):
        """Test Redis set and get operations"""
        # Mock Redis responses
        self.mock_client.get.return_value = '"test_value"'
        self.mock_client.setex.return_value = True
        
        # Test set
        result = self.cache.set('test_key', 'test_value', 3600)
        self.assertTrue(result)
        self.mock_client.setex.assert_called_once()
        
        # Test get
        value = self.cache.get('test_key')
        self.assertEqual(value, 'test_value')
        self.mock_client.get.assert_called_once_with('test_key')
    
    def test_redis_delete(self):
        """Test Redis delete operation"""
        self.mock_client.delete.return_value = 1
        
        result = self.cache.delete('test_key')
        self.assertTrue(result)
        self.mock_client.delete.assert_called_once_with('test_key')
    
    def test_redis_exists(self):
        """Test Redis exists operation"""
        self.mock_client.exists.return_value = 1
        
        result = self.cache.exists('test_key')
        self.assertTrue(result)
        self.mock_client.exists.assert_called_once_with('test_key')
    
    def test_redis_pattern_clear(self):
        """Test Redis pattern clearing"""
        self.mock_client.keys.return_value = ['key1', 'key2', 'key3']
        self.mock_client.delete.return_value = 3
        
        result = self.cache.clear_pattern('prefix:*')
        self.assertEqual(result, 3)
        self.mock_client.keys.assert_called_once_with('prefix:*')
        self.mock_client.delete.assert_called_once_with('key1', 'key2', 'key3')
    
    def test_redis_stats(self):
        """Test Redis statistics"""
        self.mock_client.info.return_value = {
            'used_memory_human': '1.2M',
            'connected_clients': 5,
            'total_commands_processed': 1000,
            'keyspace_hits': 800,
            'keyspace_misses': 200
        }
        
        stats = self.cache.get_stats()
        self.assertTrue(stats['available'])
        self.assertEqual(stats['used_memory'], '1.2M')
        self.assertEqual(stats['connected_clients'], 5)
        self.assertEqual(stats['hit_rate'], 80.0)


class TestOCRCache(unittest.TestCase):
    """Test cases for OCR cache"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_redis_cache = MagicMock()
        self.ocr_cache = OCRCache(self.mock_redis_cache)
    
    def test_ocr_result_caching(self):
        """Test OCR result caching"""
        image_hash = 'test_hash_789'
        document_type = 'driving_license'
        result = {
            'document_type': document_type,
            'confidence': 0.88,
            'extracted_info': {'license_number': 'DL123456'}
        }
        
        # Mock cache behavior
        self.mock_redis_cache._generate_key.return_value = 'ocr:generated_key'
        self.mock_redis_cache.set.return_value = True
        
        # Set OCR result
        success = self.ocr_cache.set_ocr_result(image_hash, result, document_type)
        self.assertTrue(success)
        
        # Verify cache was called correctly
        self.mock_redis_cache.set.assert_called_once()
        args, kwargs = self.mock_redis_cache.set.call_args
        self.assertEqual(args[0], 'ocr:generated_key')
        self.assertIn('result', args[1])
        self.assertIn('cached_at', args[1])
    
    def test_get_ocr_result(self):
        """Test getting OCR result from cache"""
        image_hash = 'test_hash_789'
        document_type = 'driving_license'
        
        # Mock cache behavior
        self.mock_redis_cache._generate_key.return_value = 'ocr:generated_key'
        self.mock_redis_cache.get.return_value = {
            'result': {'document_type': document_type},
            'cached_at': '2023-01-01T12:00:00Z'
        }
        
        # Get OCR result
        result = self.ocr_cache.get_ocr_result(image_hash, document_type)
        self.assertIsNotNone(result)
        self.assertEqual(result['result']['document_type'], document_type)
        
        # Verify cache was called correctly
        self.mock_redis_cache.get.assert_called_once_with('ocr:generated_key')


class TestUnifiedCache(unittest.TestCase):
    """Test cases for unified cache system"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock Redis to be unavailable
        with patch('app.cache.redis_cache.cache_manager') as mock_redis:
            mock_redis.is_available.return_value = False
            
            # Initialize unified cache (should fall back to memory)
            from app.cache import UnifiedCacheManager
            self.unified_cache = UnifiedCacheManager()
    
    def test_fallback_to_memory(self):
        """Test fallback to memory cache when Redis is unavailable"""
        self.assertTrue(self.unified_cache.is_available())
        
        # Should be using memory cache as primary
        self.assertIsNotNone(self.unified_cache.primary_cache)
        self.assertEqual(self.unified_cache.primary_cache.get_stats()['type'], 'memory')
    
    def test_unified_cache_operations(self):
        """Test unified cache operations"""
        # Test document caching
        document_data = {'test': 'data'}
        result = {'status': 'success'}
        
        self.assertTrue(self.unified_cache.set_document_result(document_data, result))
        cached_result = self.unified_cache.get_document_result(document_data)
        self.assertEqual(cached_result['result'], result)
        
        # Test OCR caching
        image_hash = 'test_hash_unified'
        ocr_result = {'document_type': 'passport'}
        
        self.assertTrue(self.unified_cache.set_ocr_result(image_hash, ocr_result))
        cached_ocr = self.unified_cache.get_ocr_result(image_hash)
        self.assertEqual(cached_ocr['result'], ocr_result)
        
        # Test session caching
        session_id = 'session_unified'
        session_data = {'user_id': 'user_123'}
        
        self.assertTrue(self.unified_cache.set_session_data(session_id, session_data))
        cached_session = self.unified_cache.get_session_data(session_id)
        self.assertEqual(cached_session, session_data)
    
    def test_unified_cache_stats(self):
        """Test unified cache statistics"""
        stats = self.unified_cache.get_stats()
        self.assertTrue(stats['available'])
        self.assertIn('primary_cache', stats)
    
    def test_unified_cache_clear(self):
        """Test unified cache clearing"""
        # Add some data
        self.unified_cache.set_document_result({'key': 'value'}, {'result': 'data'})
        
        # Clear all
        result = self.unified_cache.clear_all()
        self.assertIn('primary_cache', result)


if __name__ == '__main__':
    unittest.main()