"""
Advanced Document Classification System
Uses multiple detection strategies for robust document type identification
"""
import re
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of document classification"""
    document_type: str
    confidence: float
    country: Optional[str] = None
    processor_class: Optional[str] = None
    detection_features: Optional[Dict] = None


class DocumentClassifier:
    """Advanced document classifier using multiple detection strategies"""
    
    def __init__(self):
        self.text_patterns = {}
        self.visual_patterns = {}
        self.number_patterns = {}
        self.language_patterns = {}
        self.size_patterns = {}
        
        self._initialize_patterns()
    
    def _initialize_patterns(self):
        """Initialize all detection patterns"""
        
        # Text-based patterns
        self.text_patterns = {
            'emirates_id': {
                'keywords': ['emirates id', 'بطاقة الهوية', 'federal authority', 'uae'],
                'negative_keywords': ['passport', 'license', 'driving'],
                'required_score': 2
            },
            'aadhaar_card': {
                'keywords': ['aadhaar', 'आधार', 'government of india', 'unique identification'],
                'negative_keywords': ['passport', 'license', 'pan card'],
                'required_score': 2
            },
            'driving_license': {
                'keywords': ['driving license', 'driver license', 'dl', 'motor vehicle'],
                'negative_keywords': ['passport', 'id card', 'aadhaar'],
                'required_score': 2
            },
            'passport': {
                'keywords': ['passport', 'travel document', 'republic of', 'nationality'],
                'negative_keywords': ['license', 'id card'],
                'required_score': 2
            }
        }
        
        # Number format patterns
        self.number_patterns = {
            'emirates_id': [r'784[-\s]?\d{4}[-\s]?\d{7}[-\s]?\d'],
            'aadhaar_card': [r'\d{4}\s*\d{4}\s*\d{4}', r'\d{12}'],
            'driving_license': [r'[A-Z]{2}[-\s]?\d{2}[-\s]?\d{4}[-\s]?\d{7}'],
            'passport': [r'[A-Z]\d{7}', r'[A-Z]{2}\d{6,8}']
        }
        
        # Language detection patterns
        self.language_patterns = {
            'emirates_id': ['arabic', 'english'],
            'aadhaar_card': ['hindi', 'english'],
            'driving_license': ['english', 'local'],
            'passport': ['english', 'local']
        }
    
    def classify_document(self, text: str, image: np.ndarray = None) -> List[ClassificationResult]:
        """
        Classify document using multiple strategies
        Returns list of possible classifications sorted by confidence
        """
        results = []
        
        # Text-based classification
        text_results = self._classify_by_text(text)
        results.extend(text_results)
        
        # Number pattern classification
        number_results = self._classify_by_numbers(text)
        results.extend(number_results)
        
        # Visual classification (if image provided)
        if image is not None:
            visual_results = self._classify_by_visual_features(image)
            results.extend(visual_results)
        
        # Merge and rank results
        merged_results = self._merge_classifications(results)
        
        # Sort by confidence
        merged_results.sort(key=lambda x: x.confidence, reverse=True)
        
        return merged_results[:3]  # Return top 3 candidates
    
    def _classify_by_text(self, text: str) -> List[ClassificationResult]:
        """Classify based on text content"""
        results = []
        text_lower = text.lower()
        
        for doc_type, patterns in self.text_patterns.items():
            score = 0
            matched_features = []
            
            # Check positive keywords
            for keyword in patterns['keywords']:
                if keyword.lower() in text_lower:
                    score += 1
                    matched_features.append(f"keyword:{keyword}")
            
            # Check negative keywords (reduce score)
            for neg_keyword in patterns['negative_keywords']:
                if neg_keyword.lower() in text_lower:
                    score -= 0.5
                    matched_features.append(f"negative:{neg_keyword}")
            
            # Calculate confidence
            confidence = min(score / patterns['required_score'], 1.0)
            
            if confidence > 0.3:  # Minimum threshold
                results.append(ClassificationResult(
                    document_type=doc_type,
                    confidence=confidence,
                    detection_features={'text_features': matched_features, 'text_score': score}
                ))
        
        return results
    
    def _classify_by_numbers(self, text: str) -> List[ClassificationResult]:
        """Classify based on number patterns"""
        results = []
        
        for doc_type, patterns in self.number_patterns.items():
            matches = 0
            matched_patterns = []
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matches += 1
                    matched_patterns.append(pattern)
            
            if matches > 0:
                confidence = min(matches / len(patterns), 1.0)
                results.append(ClassificationResult(
                    document_type=doc_type,
                    confidence=confidence,
                    detection_features={'number_patterns': matched_patterns, 'pattern_matches': matches}
                ))
        
        return results
    
    def _classify_by_visual_features(self, image: np.ndarray) -> List[ClassificationResult]:
        """Classify based on visual features"""
        results = []
        
        try:
            # Analyze image dimensions and aspect ratio
            height, width = image.shape[:2]
            aspect_ratio = width / height
            
            # Document size classification
            size_features = {
                'width': width,
                'height': height,
                'aspect_ratio': aspect_ratio
            }
            
            # ID card-like dimensions (roughly 1.6:1 aspect ratio)
            if 1.4 <= aspect_ratio <= 1.8:
                results.append(ClassificationResult(
                    document_type='id_card_format',
                    confidence=0.6,
                    detection_features={'visual_features': size_features}
                ))
            
            # Passport-like dimensions (roughly 1.4:1 aspect ratio)
            elif 1.2 <= aspect_ratio <= 1.5:
                results.append(ClassificationResult(
                    document_type='passport_format',
                    confidence=0.5,
                    detection_features={'visual_features': size_features}
                ))
            
            # Color analysis for security features
            color_features = self._analyze_colors(image)
            if color_features['has_security_colors']:
                for result in results:
                    result.confidence += 0.1
                    result.detection_features['color_analysis'] = color_features
        
        except Exception as e:
            logger.warning(f"Visual classification failed: {e}")
        
        return results
    
    def _analyze_colors(self, image: np.ndarray) -> Dict:
        """Analyze color distribution for security features"""
        try:
            # Convert to HSV for better color analysis
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Define color ranges for common security features
            # Blue range (common in official documents)
            blue_lower = np.array([100, 50, 50])
            blue_upper = np.array([130, 255, 255])
            blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
            blue_percentage = np.sum(blue_mask > 0) / (image.shape[0] * image.shape[1])
            
            # Red range (common in official documents)
            red_lower1 = np.array([0, 50, 50])
            red_upper1 = np.array([10, 255, 255])
            red_lower2 = np.array([170, 50, 50])
            red_upper2 = np.array([180, 255, 255])
            red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
            red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
            red_mask = red_mask1 + red_mask2
            red_percentage = np.sum(red_mask > 0) / (image.shape[0] * image.shape[1])
            
            return {
                'blue_percentage': blue_percentage,
                'red_percentage': red_percentage,
                'has_security_colors': (blue_percentage > 0.05 or red_percentage > 0.05)
            }
        
        except Exception:
            return {'has_security_colors': False}
    
    def _merge_classifications(self, results: List[ClassificationResult]) -> List[ClassificationResult]:
        """Merge multiple classification results for same document type"""
        merged = {}
        
        for result in results:
            doc_type = result.document_type
            
            if doc_type in merged:
                # Combine confidences (weighted average)
                existing = merged[doc_type]
                combined_confidence = (existing.confidence + result.confidence) / 2
                
                # Merge detection features
                if existing.detection_features and result.detection_features:
                    merged_features = {**existing.detection_features, **result.detection_features}
                else:
                    merged_features = existing.detection_features or result.detection_features
                
                merged[doc_type] = ClassificationResult(
                    document_type=doc_type,
                    confidence=combined_confidence,
                    country=existing.country or result.country,
                    processor_class=existing.processor_class or result.processor_class,
                    detection_features=merged_features
                )
            else:
                merged[doc_type] = result
        
        return list(merged.values())
    
    def get_best_match(self, text: str, image: np.ndarray = None) -> Optional[ClassificationResult]:
        """Get the best classification match"""
        results = self.classify_document(text, image)
        return results[0] if results else None


# Global classifier instance
document_classifier = DocumentClassifier()
