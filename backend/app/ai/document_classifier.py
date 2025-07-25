"""
AI-Powered Document Classification System
Automatically identifies document types from images using machine learning
"""

import cv2
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
import joblib
import os
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json
from PIL import Image
import hashlib

logger = logging.getLogger(__name__)

class DocumentClassifier:
    """
    Advanced AI-powered document classification system
    """
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or 'models/document_classifier.pkl'
        self.scaler_path = 'models/feature_scaler.pkl'
        self.confidence_threshold = 0.7
        self.model = None
        self.scaler = None
        
        # Document type mappings
        self.document_types = {
            'aadhaar': 'Aadhaar Card',
            'emirates_id': 'Emirates ID',
            'driving_license': 'Driving License',
            'passport': 'Passport',
            'us_drivers_license': 'US Driver\'s License',
            'us_green_card': 'US Green Card',
            'unknown': 'Unknown Document'
        }
        
        # Feature extraction parameters
        self.feature_config = {
            'image_size': (224, 224),
            'color_histogram_bins': 32,
            'edge_detection_threshold': 100,
            'text_regions_threshold': 0.5
        }
        
        # Performance metrics
        self.performance_metrics = {
            'total_classifications': 0,
            'correct_classifications': 0,
            'accuracy': 0.0,
            'last_updated': datetime.now().isoformat()
        }
        
        self.load_model()
        
    def load_model(self):
        """Load the trained model and scaler"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                logger.info(f"Loaded document classifier model from {self.model_path}")
                
            if os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
                logger.info(f"Loaded feature scaler from {self.scaler_path}")
                
            if self.model is None or self.scaler is None:
                logger.warning("Model or scaler not found, initializing with default model")
                self.initialize_default_model()
                
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.initialize_default_model()
    
    def initialize_default_model(self):
        """Initialize a default model for document classification"""
        self.model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            max_depth=10,
            min_samples_split=5
        )
        self.scaler = StandardScaler()
        logger.info("Initialized default document classifier model")
    
    def extract_features(self, image_data: bytes) -> np.ndarray:
        """
        Extract comprehensive features from document image
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Feature vector as numpy array
        """
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Could not decode image")
                
            # Resize image to standard size
            image = cv2.resize(image, self.feature_config['image_size'])
            
            features = []
            
            # 1. Color histogram features
            color_features = self._extract_color_features(image)
            features.extend(color_features)
            
            # 2. Edge detection features
            edge_features = self._extract_edge_features(image)
            features.extend(edge_features)
            
            # 3. Text region features
            text_features = self._extract_text_features(image)
            features.extend(text_features)
            
            # 4. Geometric features
            geometric_features = self._extract_geometric_features(image)
            features.extend(geometric_features)
            
            # 5. Texture features
            texture_features = self._extract_texture_features(image)
            features.extend(texture_features)
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            # Return zero vector if feature extraction fails
            return np.zeros(self._get_feature_dimension())
    
    def _extract_color_features(self, image: np.ndarray) -> List[float]:
        """Extract color histogram features"""
        features = []
        
        # HSV color space histogram
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        for i in range(3):
            hist = cv2.calcHist([hsv], [i], None, [self.feature_config['color_histogram_bins']], [0, 256])
            features.extend(hist.flatten() / hist.sum())
        
        # Color moments (mean, std, skewness)
        for channel in cv2.split(image):
            features.extend([
                np.mean(channel),
                np.std(channel),
                np.mean((channel - np.mean(channel)) ** 3)
            ])
        
        return features
    
    def _extract_edge_features(self, image: np.ndarray) -> List[float]:
        """Extract edge detection features"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Canny edge detection
        edges = cv2.Canny(gray, 50, self.feature_config['edge_detection_threshold'])
        
        # Edge density
        edge_density = np.sum(edges > 0) / edges.size
        
        # Edge orientation histogram
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        orientation = np.arctan2(sobel_y, sobel_x)
        orientation_hist, _ = np.histogram(orientation, bins=8, range=(-np.pi, np.pi))
        orientation_hist = orientation_hist / orientation_hist.sum()
        
        # Line detection using Hough transform
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                               minLineLength=50, maxLineGap=10)
        
        line_count = len(lines) if lines is not None else 0
        
        return [edge_density, line_count] + orientation_hist.tolist()
    
    def _extract_text_features(self, image: np.ndarray) -> List[float]:
        """Extract text region features"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # MSER (Maximally Stable Extremal Regions) for text detection
        mser = cv2.MSER_create()
        regions, _ = mser.detectRegions(gray)
        
        # Text region statistics
        text_region_count = len(regions)
        
        # Calculate text region density
        total_area = gray.shape[0] * gray.shape[1]
        text_area = sum(len(region) for region in regions)
        text_density = text_area / total_area if total_area > 0 else 0
        
        # Character-like region analysis
        char_regions = []
        for region in regions:
            if len(region) > 10:  # Filter small regions
                x, y, w, h = cv2.boundingRect(region.reshape(-1, 1, 2))
                aspect_ratio = w / h if h > 0 else 0
                if 0.1 < aspect_ratio < 3.0:  # Character-like aspect ratio
                    char_regions.append((x, y, w, h))
        
        char_region_count = len(char_regions)
        
        return [text_region_count, text_density, char_region_count]
    
    def _extract_geometric_features(self, image: np.ndarray) -> List[float]:
        """Extract geometric features"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Contour analysis
        contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Contour statistics
        contour_count = len(contours)
        
        if contours:
            areas = [cv2.contourArea(cnt) for cnt in contours]
            perimeters = [cv2.arcLength(cnt, True) for cnt in contours]
            
            avg_area = np.mean(areas) if areas else 0
            avg_perimeter = np.mean(perimeters) if perimeters else 0
            
            # Rectangular regions (document-like shapes)
            rect_count = 0
            for cnt in contours:
                if cv2.contourArea(cnt) > 1000:  # Filter small contours
                    epsilon = 0.02 * cv2.arcLength(cnt, True)
                    approx = cv2.approxPolyDP(cnt, epsilon, True)
                    if len(approx) == 4:  # Rectangle
                        rect_count += 1
        else:
            avg_area = avg_perimeter = rect_count = 0
        
        return [contour_count, avg_area, avg_perimeter, rect_count]
    
    def _extract_texture_features(self, image: np.ndarray) -> List[float]:
        """Extract texture features using Local Binary Patterns"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Simple texture measures
        # Calculate standard deviation in local windows
        kernel = np.ones((5, 5), np.float32) / 25
        local_mean = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        local_var = cv2.filter2D((gray.astype(np.float32) - local_mean) ** 2, -1, kernel)
        
        texture_variance = np.mean(local_var)
        texture_std = np.std(local_var)
        
        # Gradient features
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        avg_gradient = np.mean(gradient_magnitude)
        
        return [texture_variance, texture_std, avg_gradient]
    
    def _get_feature_dimension(self) -> int:
        """Get the total feature dimension"""
        # Color features: 3 * 32 (histogram) + 3 * 3 (moments) = 105
        # Edge features: 2 + 8 = 10
        # Text features: 3
        # Geometric features: 4
        # Texture features: 3
        return 105 + 10 + 3 + 4 + 3  # Total: 125 features
    
    def classify_document(self, image_data: bytes) -> Dict:
        """
        Classify document type from image
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary containing classification results
        """
        try:
            # Extract features
            features = self.extract_features(image_data)
            
            if self.model is None:
                return {
                    'document_type': 'unknown',
                    'confidence': 0.0,
                    'error': 'Model not loaded'
                }
            
            # Scale features
            if self.scaler is not None:
                features = self.scaler.transform(features.reshape(1, -1))
            else:
                features = features.reshape(1, -1)
            
            # Predict
            prediction = self.model.predict(features)[0]
            probabilities = self.model.predict_proba(features)[0]
            
            # Get confidence score
            confidence = np.max(probabilities)
            
            # Map prediction to document type
            document_type = prediction if prediction in self.document_types else 'unknown'
            
            # Generate classification results
            result = {
                'document_type': document_type,
                'document_name': self.document_types.get(document_type, 'Unknown Document'),
                'confidence': float(confidence),
                'all_probabilities': {
                    doc_type: float(prob) for doc_type, prob in 
                    zip(self.model.classes_, probabilities)
                } if hasattr(self.model, 'classes_') else {},
                'is_confident': confidence >= self.confidence_threshold,
                'timestamp': datetime.now().isoformat(),
                'feature_count': len(features.flatten())
            }
            
            # Update performance metrics
            self.performance_metrics['total_classifications'] += 1
            
            logger.info(f"Document classified as {document_type} with confidence {confidence:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Document classification failed: {e}")
            return {
                'document_type': 'unknown',
                'confidence': 0.0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def train_model(self, training_data: List[Tuple[bytes, str]]):
        """
        Train the document classifier with provided data
        
        Args:
            training_data: List of (image_data, document_type) tuples
        """
        try:
            logger.info(f"Training document classifier with {len(training_data)} samples")
            
            # Extract features for all training samples
            X = []
            y = []
            
            for image_data, document_type in training_data:
                features = self.extract_features(image_data)
                X.append(features)
                y.append(document_type)
            
            X = np.array(X)
            y = np.array(y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=10,
                min_samples_split=5
            )
            
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            train_accuracy = accuracy_score(y_train, self.model.predict(X_train_scaled))
            test_accuracy = accuracy_score(y_test, self.model.predict(X_test_scaled))
            
            logger.info(f"Training accuracy: {train_accuracy:.3f}")
            logger.info(f"Test accuracy: {test_accuracy:.3f}")
            
            # Save model
            self.save_model()
            
            # Update performance metrics
            self.performance_metrics['accuracy'] = test_accuracy
            self.performance_metrics['last_updated'] = datetime.now().isoformat()
            
            return {
                'success': True,
                'train_accuracy': train_accuracy,
                'test_accuracy': test_accuracy,
                'samples_count': len(training_data)
            }
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_model(self):
        """Save the trained model and scaler"""
        try:
            # Ensure model directory exists
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Save model
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            
            logger.info(f"Model saved to {self.model_path}")
            
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def get_performance_metrics(self) -> Dict:
        """Get classifier performance metrics"""
        return self.performance_metrics.copy()
    
    def update_feedback(self, image_hash: str, actual_type: str, predicted_type: str):
        """
        Update model performance based on user feedback
        
        Args:
            image_hash: Hash of the classified image
            actual_type: Actual document type (user feedback)
            predicted_type: Predicted document type
        """
        try:
            if actual_type == predicted_type:
                self.performance_metrics['correct_classifications'] += 1
            
            # Update accuracy
            total = self.performance_metrics['total_classifications']
            correct = self.performance_metrics['correct_classifications']
            
            if total > 0:
                self.performance_metrics['accuracy'] = correct / total
            
            logger.info(f"Feedback updated: {predicted_type} -> {actual_type}")
            
        except Exception as e:
            logger.error(f"Failed to update feedback: {e}")
    
    def get_supported_document_types(self) -> List[Dict]:
        """Get list of supported document types"""
        return [
            {
                'type': doc_type,
                'name': doc_name,
                'supported': True
            }
            for doc_type, doc_name in self.document_types.items()
            if doc_type != 'unknown'
        ]