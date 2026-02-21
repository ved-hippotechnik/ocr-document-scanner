"""
Tests for AI document classification system
"""

import unittest
import numpy as np
from PIL import Image
import io
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.ai.document_classifier import DocumentClassifier

class TestDocumentClassifier(unittest.TestCase):
    """Test cases for DocumentClassifier"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.classifier = DocumentClassifier()
        
    def create_test_image(self, size=(400, 600), color_pattern=None):
        """Create a test image with optional color pattern"""
        img_array = np.random.randint(0, 255, (*size, 3), dtype=np.uint8)
        
        if color_pattern:
            # Add color pattern to differentiate document types
            if color_pattern == 'red':
                img_array[50:100, 50:200] = [255, 0, 0]
            elif color_pattern == 'green':
                img_array[100:150, 100:250] = [0, 255, 0]
            elif color_pattern == 'blue':
                img_array[200:250, 200:350] = [0, 0, 255]
        
        img = Image.fromarray(img_array, 'RGB')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        return img_bytes.getvalue()
    
    def test_classifier_initialization(self):
        """Test classifier initialization"""
        self.assertIsNotNone(self.classifier)
        self.assertEqual(self.classifier.confidence_threshold, 0.7)
        self.assertIsNotNone(self.classifier.document_types)
        self.assertIn('aadhaar', self.classifier.document_types)
        self.assertIn('emirates_id', self.classifier.document_types)
    
    def test_feature_extraction(self):
        """Test feature extraction from image"""
        test_image = self.create_test_image()
        features = self.classifier.extract_features(test_image)
        
        self.assertIsInstance(features, np.ndarray)
        self.assertEqual(len(features), self.classifier._get_feature_dimension())
        self.assertFalse(np.any(np.isnan(features)))
    
    def test_feature_extraction_empty_image(self):
        """Test feature extraction with empty image data"""
        features = self.classifier.extract_features(b'')
        
        self.assertIsInstance(features, np.ndarray)
        self.assertEqual(len(features), self.classifier._get_feature_dimension())
        # Should return zero vector for invalid image
        self.assertTrue(np.all(features == 0))
    
    def test_color_features(self):
        """Test color feature extraction"""
        test_image = self.create_test_image(color_pattern='red')
        img_array = np.frombuffer(test_image, np.uint8)
        
        # This should not raise an exception
        features = self.classifier._extract_color_features(img_array.reshape(400, 600, 3))
        self.assertIsInstance(features, list)
        self.assertGreater(len(features), 0)
    
    def test_classification_without_model(self):
        """Test classification when model is not loaded"""
        test_image = self.create_test_image()
        
        # Ensure model is None
        self.classifier.model = None
        
        result = self.classifier.classify_document(test_image)
        
        self.assertIsInstance(result, dict)
        self.assertIn('document_type', result)
        self.assertEqual(result['document_type'], 'unknown')
        self.assertEqual(result['confidence'], 0.0)
        self.assertIn('error', result)
    
    def test_classification_with_mock_model(self):
        """Test classification with mocked model"""
        test_image = self.create_test_image()
        
        # Mock the model and scaler
        mock_model = MagicMock()
        mock_model.predict.return_value = ['aadhaar']
        mock_model.predict_proba.return_value = [[0.1, 0.8, 0.1]]
        mock_model.classes_ = ['emirates_id', 'aadhaar', 'passport']
        
        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = np.array([[1, 2, 3, 4, 5]])
        
        self.classifier.model = mock_model
        self.classifier.scaler = mock_scaler
        
        result = self.classifier.classify_document(test_image)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['document_type'], 'aadhaar')
        self.assertEqual(result['confidence'], 0.8)
        self.assertIn('all_probabilities', result)
        self.assertIn('is_confident', result)
    
    def test_training_with_insufficient_data(self):
        """Test training with insufficient data"""
        # Create minimal training data
        training_data = [
            (self.create_test_image(), 'aadhaar'),
            (self.create_test_image(), 'passport')
        ]
        
        result = self.classifier.train_model(training_data)
        
        # Should fail due to insufficient data for proper train/test split
        self.assertIn('success', result)
        self.assertIn('error', result)
    
    def test_training_with_sufficient_data(self):
        """Test training with sufficient data"""
        # Create sufficient training data
        training_data = []
        doc_types = ['aadhaar', 'emirates_id', 'passport']
        
        for doc_type in doc_types:
            for i in range(10):  # 10 samples per type
                training_data.append((self.create_test_image(), doc_type))
        
        result = self.classifier.train_model(training_data)
        
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        
        if result['success']:
            self.assertIn('train_accuracy', result)
            self.assertIn('test_accuracy', result)
            self.assertIn('samples_count', result)
            self.assertEqual(result['samples_count'], 30)
    
    def test_performance_metrics(self):
        """Test performance metrics tracking"""
        metrics = self.classifier.get_performance_metrics()
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('total_classifications', metrics)
        self.assertIn('correct_classifications', metrics)
        self.assertIn('accuracy', metrics)
        self.assertIn('last_updated', metrics)
    
    def test_feedback_update(self):
        """Test feedback update functionality"""
        image_hash = 'test_hash_123'
        actual_type = 'aadhaar'
        predicted_type = 'passport'
        
        # Record initial metrics
        initial_metrics = self.classifier.get_performance_metrics()
        
        # Update feedback
        self.classifier.update_feedback(image_hash, actual_type, predicted_type)
        
        # Check that metrics were updated
        updated_metrics = self.classifier.get_performance_metrics()
        self.assertGreaterEqual(
            updated_metrics['total_classifications'],
            initial_metrics['total_classifications']
        )
    
    def test_supported_document_types(self):
        """Test getting supported document types"""
        supported_types = self.classifier.get_supported_document_types()
        
        self.assertIsInstance(supported_types, list)
        self.assertGreater(len(supported_types), 0)
        
        for doc_type in supported_types:
            self.assertIn('type', doc_type)
            self.assertIn('name', doc_type)
            self.assertIn('supported', doc_type)
            self.assertTrue(doc_type['supported'])
    
    def test_confidence_threshold_update(self):
        """Test confidence threshold updates"""
        original_threshold = self.classifier.confidence_threshold
        new_threshold = 0.85
        
        self.classifier.confidence_threshold = new_threshold
        self.assertEqual(self.classifier.confidence_threshold, new_threshold)
        
        # Reset to original
        self.classifier.confidence_threshold = original_threshold
    
    def test_edge_detection_features(self):
        """Test edge detection feature extraction"""
        test_image = self.create_test_image()
        
        # Convert to image array for testing
        img_array = np.frombuffer(test_image, np.uint8)
        
        # This should not raise an exception
        try:
            # Test with a simple 2D array
            features = self.classifier._extract_edge_features(np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8))
            self.assertIsInstance(features, list)
            self.assertGreater(len(features), 0)
        except Exception as e:
            self.fail(f"Edge detection failed: {e}")
    
    def test_text_features(self):
        """Test text feature extraction"""
        test_image = self.create_test_image()
        
        # Test with a simple 2D array
        features = self.classifier._extract_text_features(np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8))
        self.assertIsInstance(features, list)
        self.assertEqual(len(features), 3)  # Should return 3 text features
    
    def test_geometric_features(self):
        """Test geometric feature extraction"""
        test_image = self.create_test_image()
        
        # Test with a simple 2D array
        features = self.classifier._extract_geometric_features(np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8))
        self.assertIsInstance(features, list)
        self.assertEqual(len(features), 4)  # Should return 4 geometric features
    
    def test_texture_features(self):
        """Test texture feature extraction"""
        test_image = self.create_test_image()
        
        # Test with a simple 2D array
        features = self.classifier._extract_texture_features(np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8))
        self.assertIsInstance(features, list)
        self.assertEqual(len(features), 3)  # Should return 3 texture features
    
    def test_feature_dimension_consistency(self):
        """Test that feature dimension is consistent"""
        # Test multiple images
        for i in range(5):
            test_image = self.create_test_image()
            features = self.classifier.extract_features(test_image)
            
            expected_dim = self.classifier._get_feature_dimension()
            self.assertEqual(len(features), expected_dim)
    
    @patch('joblib.dump')
    def test_model_saving(self, mock_dump):
        """Test model saving functionality"""
        # Mock a trained model
        self.classifier.model = MagicMock()
        self.classifier.scaler = MagicMock()
        
        # Test saving
        self.classifier.save_model()
        
        # Verify joblib.dump was called
        self.assertEqual(mock_dump.call_count, 2)  # Model and scaler
    
    def test_invalid_image_handling(self):
        """Test handling of invalid image data"""
        invalid_data = b'invalid_image_data'
        
        result = self.classifier.classify_document(invalid_data)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['document_type'], 'unknown')
        self.assertEqual(result['confidence'], 0.0)

class TestAIRoutes(unittest.TestCase):
    """Test cases for AI classification routes"""
    
    def setUp(self):
        """Set up test fixtures"""
        # This would require setting up a test Flask app
        # For now, we'll just test the core functionality
        pass
    
    def test_route_setup(self):
        """Test that routes are properly set up"""
        # Import the blueprint
        from app.ai.routes import ai_bp
        
        self.assertIsNotNone(ai_bp)
        self.assertEqual(ai_bp.name, 'ai')
        self.assertEqual(ai_bp.url_prefix, '/api/ai')

if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestDocumentClassifier))
    suite.addTest(unittest.makeSuite(TestAIRoutes))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)