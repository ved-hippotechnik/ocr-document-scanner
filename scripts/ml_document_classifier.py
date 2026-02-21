#!/usr/bin/env python3
"""
Machine Learning Document Classification System
Provides ML-powered document type detection and field extraction with higher accuracy
"""

import os
import cv2
import numpy as np
import pickle
import json
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import time
import logging

# ML Libraries
try:
    import tensorflow as tf
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
    from tensorflow.keras.models import Model
    from tensorflow.keras.preprocessing.image import img_to_array
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

try:
    from sklearn.ensemble import RandomForestClassifier, VotingClassifier
    from sklearn.svm import SVC
    from sklearn.naive_bayes import GaussianNB
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics import classification_report, confusion_matrix
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Image processing
from PIL import Image
import pytesseract

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MLClassificationResult:
    """Result from ML classification"""
    document_type: str
    confidence_score: float
    field_predictions: Dict[str, Any]
    processing_time: float
    model_used: str
    features_extracted: Dict[str, Any]

class FeatureExtractor:
    """Advanced feature extraction for document classification"""
    
    def __init__(self):
        self.text_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        ) if SKLEARN_AVAILABLE else None
        
    def extract_text_features(self, text: str) -> Dict[str, Any]:
        """Extract text-based features from OCR text"""
        features = {
            'text_length': len(text),
            'word_count': len(text.split()),
            'line_count': len(text.splitlines()),
            'digit_ratio': sum(c.isdigit() for c in text) / len(text) if text else 0,
            'upper_ratio': sum(c.isupper() for c in text) / len(text) if text else 0,
            'special_char_ratio': sum(not c.isalnum() and not c.isspace() for c in text) / len(text) if text else 0
        }
        
        # Document-specific patterns
        features.update({
            'has_aadhaar_pattern': bool(self._check_aadhaar_pattern(text)),
            'has_pan_pattern': bool(self._check_pan_pattern(text)),
            'has_passport_pattern': bool(self._check_passport_pattern(text)),
            'has_driving_license_pattern': bool(self._check_driving_license_pattern(text)),
            'has_voter_id_pattern': bool(self._check_voter_id_pattern(text)),
            'has_emirates_id_pattern': bool(self._check_emirates_id_pattern(text)),
            'has_date_pattern': bool(self._check_date_pattern(text)),
            'has_government_keywords': bool(self._check_government_keywords(text)),
            'has_hindi_text': bool(self._check_hindi_text(text)),
            'has_arabic_text': bool(self._check_arabic_text(text))
        })
        
        return features
    
    def extract_image_features(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract image-based features"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        features = {
            'image_width': image.shape[1],
            'image_height': image.shape[0],
            'aspect_ratio': image.shape[1] / image.shape[0],
            'mean_brightness': np.mean(gray),
            'brightness_std': np.std(gray),
            'contrast': np.std(gray) / np.mean(gray) if np.mean(gray) > 0 else 0
        }
        
        # Edge detection features
        edges = cv2.Canny(gray, 50, 150)
        features.update({
            'edge_density': np.sum(edges > 0) / (image.shape[0] * image.shape[1]),
            'horizontal_edges': self._count_horizontal_edges(edges),
            'vertical_edges': self._count_vertical_edges(edges)
        })
        
        # Color features (if color image)
        if len(image.shape) == 3:
            features.update({
                'mean_red': np.mean(image[:,:,0]),
                'mean_green': np.mean(image[:,:,1]),
                'mean_blue': np.mean(image[:,:,2]),
                'color_variance': np.var(image)
            })
        
        return features
    
    def _check_aadhaar_pattern(self, text: str) -> List[str]:
        """Check for Aadhaar card patterns"""
        import re
        patterns = [
            r'\b\d{4}\s*\d{4}\s*\d{4}\b',  # 12-digit Aadhaar number
            r'आधार|aadhaar|aadhar',
            r'unique identification',
            r'government of india',
            r'भारत सरकार'
        ]
        return [p for p in patterns if re.search(p, text, re.IGNORECASE)]
    
    def _check_pan_pattern(self, text: str) -> List[str]:
        """Check for PAN card patterns"""
        import re
        patterns = [
            r'\b[A-Z]{5}\d{4}[A-Z]\b',  # PAN format
            r'permanent account number',
            r'income tax department',
            r'pan card'
        ]
        return [p for p in patterns if re.search(p, text, re.IGNORECASE)]
    
    def _check_passport_pattern(self, text: str) -> List[str]:
        """Check for passport patterns"""
        import re
        patterns = [
            r'passport',
            r'republic of india',
            r'type.*p',
            r'country code.*ind',
            r'nationality.*indian'
        ]
        return [p for p in patterns if re.search(p, text, re.IGNORECASE)]
    
    def _check_driving_license_pattern(self, text: str) -> List[str]:
        """Check for driving license patterns"""
        import re
        patterns = [
            r'driving.*licen[cs]e',
            r'transport.*department',
            r'dl.*no',
            r'license.*no'
        ]
        return [p for p in patterns if re.search(p, text, re.IGNORECASE)]
    
    def _check_voter_id_pattern(self, text: str) -> List[str]:
        """Check for voter ID patterns"""
        import re
        patterns = [
            r'election.*commission',
            r'voter.*id',
            r'epic.*no',
            r'electoral.*photo'
        ]
        return [p for p in patterns if re.search(p, text, re.IGNORECASE)]
    
    def _check_emirates_id_pattern(self, text: str) -> List[str]:
        """Check for Emirates ID patterns"""
        import re
        patterns = [
            r'emirates.*id',
            r'united arab emirates',
            r'identity.*card',
            r'الإمارات العربية المتحدة'
        ]
        return [p for p in patterns if re.search(p, text, re.IGNORECASE)]
    
    def _check_date_pattern(self, text: str) -> List[str]:
        """Check for date patterns"""
        import re
        patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{1,2}\s+\w+\s+\d{4}\b',
            r'date.*of.*birth',
            r'dob',
            r'expiry.*date'
        ]
        return [p for p in patterns if re.search(p, text, re.IGNORECASE)]
    
    def _check_government_keywords(self, text: str) -> List[str]:
        """Check for government-related keywords"""
        import re
        keywords = [
            'government', 'ministry', 'department', 'authority', 'commission',
            'republic', 'भारत', 'सरकार', 'india', 'official'
        ]
        return [k for k in keywords if re.search(k, text, re.IGNORECASE)]
    
    def _check_hindi_text(self, text: str) -> bool:
        """Check if text contains Hindi/Devanagari script"""
        import re
        return bool(re.search(r'[\u0900-\u097F]', text))
    
    def _check_arabic_text(self, text: str) -> bool:
        """Check if text contains Arabic script"""
        import re
        return bool(re.search(r'[\u0600-\u06FF]', text))
    
    def _count_horizontal_edges(self, edges: np.ndarray) -> int:
        """Count horizontal edges in image"""
        horizontal_kernel = np.ones((1, 5), np.uint8)
        horizontal_edges = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel)
        return np.sum(horizontal_edges > 0)
    
    def _count_vertical_edges(self, edges: np.ndarray) -> int:
        """Count vertical edges in image"""
        vertical_kernel = np.ones((5, 1), np.uint8)
        vertical_edges = cv2.morphologyEx(edges, cv2.MORPH_OPEN, vertical_kernel)
        return np.sum(vertical_edges > 0)

class MLDocumentClassifier:
    """Machine Learning-powered document classification system"""
    
    def __init__(self, model_path: str = "models/"):
        self.model_path = Path(model_path)
        self.model_path.mkdir(exist_ok=True)
        
        self.feature_extractor = FeatureExtractor()
        self.models = {}
        self.is_trained = False
        
        # Document type mapping
        self.document_types = {
            'aadhaar': 'Aadhaar Card',
            'pan': 'PAN Card',
            'passport': 'Passport',
            'driving_license': 'Driving License',
            'voter_id': 'Voter ID',
            'emirates_id': 'Emirates ID',
            'other': 'Other Document'
        }
        
        # Load pre-trained models if available
        self.load_models()
    
    def train_classifier(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train the ML classifier with labeled data"""
        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn not available for training")
            return {'error': 'scikit-learn not available'}
        
        logger.info("Training ML classifier...")
        start_time = time.time()
        
        # Prepare features and labels
        X_text = []
        X_image = []
        y = []
        
        for data in training_data:
            # Extract features
            text_features = self.feature_extractor.extract_text_features(data['text'])
            image_features = self.feature_extractor.extract_image_features(data['image'])
            
            # Combine features
            combined_features = {**text_features, **image_features}
            feature_vector = [combined_features[key] for key in sorted(combined_features.keys())]
            
            X_text.append(feature_vector)
            y.append(data['document_type'])
        
        X_text = np.array(X_text)
        
        # Train ensemble classifier
        classifiers = [
            ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
            ('svm', SVC(probability=True, random_state=42)),
            ('nb', GaussianNB())
        ]
        
        ensemble_classifier = VotingClassifier(
            estimators=classifiers,
            voting='soft'
        )
        
        ensemble_classifier.fit(X_text, y)
        
        self.models['ensemble'] = ensemble_classifier
        self.is_trained = True
        
        # Save models
        self.save_models()
        
        training_time = time.time() - start_time
        logger.info(f"Training completed in {training_time:.2f} seconds")
        
        return {
            'success': True,
            'training_time': training_time,
            'samples_trained': len(training_data),
            'accuracy': self.evaluate_model(X_text, y)
        }
    
    def classify_document(self, image: np.ndarray, text: str) -> MLClassificationResult:
        """Classify document using ML models"""
        start_time = time.time()
        
        # Extract features
        text_features = self.feature_extractor.extract_text_features(text)
        image_features = self.feature_extractor.extract_image_features(image)
        
        # Combine features
        combined_features = {**text_features, **image_features}
        feature_vector = np.array([combined_features[key] for key in sorted(combined_features.keys())])
        
        # Rule-based classification (fallback)
        rule_based_result = self._rule_based_classification(text, image)
        
        # ML classification (if models available)
        if self.is_trained and 'ensemble' in self.models:
            try:
                # Predict using ensemble
                prediction = self.models['ensemble'].predict([feature_vector])[0]
                confidence = max(self.models['ensemble'].predict_proba([feature_vector])[0])
                
                document_type = self.document_types.get(prediction, prediction)
                model_used = 'ML Ensemble'
                
            except Exception as e:
                logger.error(f"ML classification failed: {e}")
                document_type = rule_based_result['document_type']
                confidence = rule_based_result['confidence']
                model_used = 'Rule-based (ML fallback)'
        else:
            document_type = rule_based_result['document_type']
            confidence = rule_based_result['confidence']
            model_used = 'Rule-based'
        
        # Field-specific predictions
        field_predictions = self._predict_fields(text, document_type)
        
        processing_time = time.time() - start_time
        
        return MLClassificationResult(
            document_type=document_type,
            confidence_score=confidence,
            field_predictions=field_predictions,
            processing_time=processing_time,
            model_used=model_used,
            features_extracted=combined_features
        )
    
    def _rule_based_classification(self, text: str, image: np.ndarray) -> Dict[str, Any]:
        """Rule-based classification as fallback"""
        text_lower = text.lower()
        confidence = 0.6  # Default confidence for rule-based
        
        # Aadhaar Card
        if any(keyword in text_lower for keyword in ['aadhaar', 'aadhar', 'unique identification']):
            if self.feature_extractor._check_aadhaar_pattern(text):
                return {'document_type': 'Aadhaar Card', 'confidence': 0.9}
            return {'document_type': 'Aadhaar Card', 'confidence': 0.7}
        
        # PAN Card
        if any(keyword in text_lower for keyword in ['permanent account', 'income tax', 'pan']):
            if self.feature_extractor._check_pan_pattern(text):
                return {'document_type': 'PAN Card', 'confidence': 0.9}
            return {'document_type': 'PAN Card', 'confidence': 0.7}
        
        # Passport
        if any(keyword in text_lower for keyword in ['passport', 'republic of india', 'type p']):
            return {'document_type': 'Passport', 'confidence': 0.85}
        
        # Driving License
        if any(keyword in text_lower for keyword in ['driving', 'license', 'transport']):
            return {'document_type': 'Driving License', 'confidence': 0.8}
        
        # Voter ID
        if any(keyword in text_lower for keyword in ['election', 'voter', 'epic']):
            return {'document_type': 'Voter ID', 'confidence': 0.8}
        
        # Emirates ID
        if any(keyword in text_lower for keyword in ['emirates', 'uae', 'united arab emirates']):
            return {'document_type': 'Emirates ID', 'confidence': 0.8}
        
        # Default to Other Document
        return {'document_type': 'Other Document', 'confidence': 0.4}
    
    def _predict_fields(self, text: str, document_type: str) -> Dict[str, Any]:
        """Predict specific fields based on document type"""
        import re
        
        predictions = {}
        
        if document_type == 'Aadhaar Card':
            # Aadhaar number
            aadhaar_match = re.search(r'\b\d{4}\s*\d{4}\s*\d{4}\b', text)
            if aadhaar_match:
                predictions['aadhaar_number'] = aadhaar_match.group()
            
            # Name extraction (after "Name:" or similar)
            name_match = re.search(r'(?:name|नाम)[:\s]*([A-Za-z\s]+)', text, re.IGNORECASE)
            if name_match:
                predictions['name'] = name_match.group(1).strip()
        
        elif document_type == 'PAN Card':
            # PAN number
            pan_match = re.search(r'\b[A-Z]{5}\d{4}[A-Z]\b', text)
            if pan_match:
                predictions['pan_number'] = pan_match.group()
        
        # Common fields for all documents
        # Date of birth
        dob_match = re.search(r'(?:dob|date.*birth|जन्म)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text, re.IGNORECASE)
        if dob_match:
            predictions['date_of_birth'] = dob_match.group(1)
        
        # Gender
        gender_match = re.search(r'(?:gender|sex|लिंग)[:\s]*(male|female|पुरुष|महिला|m|f)', text, re.IGNORECASE)
        if gender_match:
            predictions['gender'] = gender_match.group(1)
        
        return predictions
    
    def save_models(self):
        """Save trained models to disk"""
        if not self.is_trained:
            return
        
        try:
            model_file = self.model_path / "ml_classifier.pkl"
            with open(model_file, 'wb') as f:
                pickle.dump(self.models, f)
            logger.info(f"Models saved to {model_file}")
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
    
    def load_models(self):
        """Load pre-trained models from disk"""
        try:
            model_file = self.model_path / "ml_classifier.pkl"
            if model_file.exists():
                with open(model_file, 'rb') as f:
                    self.models = pickle.load(f)
                self.is_trained = True
                logger.info(f"Models loaded from {model_file}")
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
    
    def evaluate_model(self, X: np.ndarray, y: List[str]) -> float:
        """Evaluate model accuracy"""
        if not self.is_trained or 'ensemble' not in self.models:
            return 0.0
        
        try:
            predictions = self.models['ensemble'].predict(X)
            accuracy = sum(1 for pred, true in zip(predictions, y) if pred == true) / len(y)
            return accuracy
        except Exception as e:
            logger.error(f"Model evaluation failed: {e}")
            return 0.0
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        return {
            'is_trained': self.is_trained,
            'available_models': list(self.models.keys()),
            'supported_document_types': list(self.document_types.values()),
            'tensorflow_available': TENSORFLOW_AVAILABLE,
            'sklearn_available': SKLEARN_AVAILABLE
        }

class MLTrainingDataGenerator:
    """Generate training data for ML models"""
    
    def __init__(self):
        self.synthetic_data = []
    
    def generate_synthetic_training_data(self, num_samples: int = 1000) -> List[Dict[str, Any]]:
        """Generate synthetic training data for different document types"""
        logger.info(f"Generating {num_samples} synthetic training samples...")
        
        training_data = []
        
        # Generate samples for each document type
        types_per_sample = num_samples // 6  # 6 main document types
        
        for doc_type in ['aadhaar', 'pan', 'passport', 'driving_license', 'voter_id', 'emirates_id']:
            for i in range(types_per_sample):
                # Generate synthetic text and image
                text = self._generate_synthetic_text(doc_type)
                image = self._generate_synthetic_image(doc_type)
                
                training_data.append({
                    'text': text,
                    'image': image,
                    'document_type': doc_type
                })
        
        logger.info(f"Generated {len(training_data)} training samples")
        return training_data
    
    def _generate_synthetic_text(self, doc_type: str) -> str:
        """Generate synthetic text for a document type"""
        import random
        
        if doc_type == 'aadhaar':
            templates = [
                "Government of India Unique Identification Authority of India आधार Aadhaar Number: {aadhaar} Name: {name} Date of Birth: {dob} Gender: {gender}",
                "भारत सरकार UIDAI Aadhaar {aadhaar} नाम {name} जन्म तिथि {dob} लिंग {gender}",
                "Unique Identification Authority Aadhaar Card {aadhaar} {name} DOB: {dob} {gender}"
            ]
            
            template = random.choice(templates)
            return template.format(
                aadhaar=self._generate_aadhaar_number(),
                name=self._generate_name(),
                dob=self._generate_date(),
                gender=random.choice(['Male', 'Female', 'पुरुष', 'महिला'])
            )
        
        elif doc_type == 'pan':
            templates = [
                "Income Tax Department Government of India Permanent Account Number {pan} Name: {name} Date of Birth: {dob}",
                "PAN Card {pan} {name} DOB {dob}",
                "Permanent Account Number Card {pan} {name}"
            ]
            
            template = random.choice(templates)
            return template.format(
                pan=self._generate_pan_number(),
                name=self._generate_name(),
                dob=self._generate_date()
            )
        
        elif doc_type == 'passport':
            templates = [
                "Passport Republic of India Type P Country Code IND {name} Nationality Indian Date of Birth {dob}",
                "भारत गणराज्य Passport {name} Indian {dob}",
                "Republic of India Passport {name} DOB {dob} Nationality Indian"
            ]
            
            template = random.choice(templates)
            return template.format(
                name=self._generate_name(),
                dob=self._generate_date()
            )
        
        # Add more document types as needed
        return f"Sample {doc_type} document text"
    
    def _generate_synthetic_image(self, doc_type: str) -> np.ndarray:
        """Generate synthetic image for a document type"""
        # Create a simple synthetic image
        height, width = 400, 600
        image = np.random.randint(200, 255, (height, width, 3), dtype=np.uint8)
        
        # Add some document-like features
        cv2.rectangle(image, (50, 50), (width-50, height-50), (255, 255, 255), -1)
        cv2.rectangle(image, (50, 50), (width-50, height-50), (0, 0, 0), 2)
        
        return image
    
    def _generate_aadhaar_number(self) -> str:
        """Generate a synthetic Aadhaar number"""
        import random
        return f"{random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}"
    
    def _generate_pan_number(self) -> str:
        """Generate a synthetic PAN number"""
        import random
        import string
        letters = ''.join(random.choices(string.ascii_uppercase, k=5))
        digits = ''.join(random.choices(string.digits, k=4))
        last_letter = random.choice(string.ascii_uppercase)
        return f"{letters}{digits}{last_letter}"
    
    def _generate_name(self) -> str:
        """Generate a synthetic name"""
        import random
        first_names = ['Amit', 'Priya', 'Raj', 'Sunita', 'Vikram', 'Kavitha', 'Suresh', 'Meera']
        last_names = ['Sharma', 'Patel', 'Kumar', 'Singh', 'Gupta', 'Reddy', 'Nair', 'Mehta']
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    def _generate_date(self) -> str:
        """Generate a synthetic date"""
        import random
        day = random.randint(1, 28)
        month = random.randint(1, 12)
        year = random.randint(1960, 2005)
        return f"{day:02d}/{month:02d}/{year}"

# Usage example and testing
if __name__ == "__main__":
    print("🤖 ML DOCUMENT CLASSIFIER - INITIALIZATION")
    print("=" * 60)
    
    # Initialize classifier
    classifier = MLDocumentClassifier()
    
    # Show model info
    info = classifier.get_model_info()
    print(f"\n📊 MODEL INFORMATION:")
    print(f"   TensorFlow Available: {info['tensorflow_available']}")
    print(f"   Scikit-learn Available: {info['sklearn_available']}")
    print(f"   Is Trained: {info['is_trained']}")
    print(f"   Available Models: {info['available_models']}")
    print(f"   Supported Document Types: {', '.join(info['supported_document_types'])}")
    
    # Generate training data if models not trained
    if not info['is_trained'] and SKLEARN_AVAILABLE:
        print(f"\n🎯 GENERATING TRAINING DATA...")
        generator = MLTrainingDataGenerator()
        training_data = generator.generate_synthetic_training_data(600)
        
        print(f"\n🎓 TRAINING ML MODELS...")
        training_result = classifier.train_classifier(training_data)
        
        if training_result.get('success'):
            print(f"   ✅ Training completed successfully!")
            print(f"   Training Time: {training_result['training_time']:.2f} seconds")
            print(f"   Samples Trained: {training_result['samples_trained']}")
            print(f"   Model Accuracy: {training_result['accuracy']:.3f}")
        else:
            print(f"   ❌ Training failed: {training_result.get('error', 'Unknown error')}")
    
    # Test classification
    print(f"\n🧪 TESTING CLASSIFICATION...")
    
    # Test with sample Aadhaar text
    test_text = "Government of India Unique Identification Authority of India आधार Aadhaar Number: 9704 7285 0296 Name: Ved Thampi Date of Birth: 05/09/2000 Gender: Male"
    test_image = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)
    
    result = classifier.classify_document(test_image, test_text)
    
    print(f"   📄 Document Type: {result.document_type}")
    print(f"   📊 Confidence: {result.confidence_score:.3f}")
    print(f"   ⚙️  Model Used: {result.model_used}")
    print(f"   ⏱️  Processing Time: {result.processing_time:.3f} seconds")
    print(f"   🔍 Field Predictions: {result.field_predictions}")
    
    print(f"\n✅ ML DOCUMENT CLASSIFIER READY!")
    print("   • Use classify_document() to classify documents")
    print("   • Use train_classifier() to train with your data")
    print("   • Models are automatically saved and loaded")
    print("   • Supports ensemble ML classification with rule-based fallback")
