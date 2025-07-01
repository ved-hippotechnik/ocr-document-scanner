"""
Document Quality Assessment System
Evaluates image quality and provides recommendations for better OCR results
"""
import cv2
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class QualityAssessment:
    """Document quality assessment result"""
    overall_score: float  # 0-1 scale
    issues: List[str]
    recommendations: List[str]
    metrics: Dict[str, float]
    processing_confidence: str  # high, medium, low


class DocumentQualityAnalyzer:
    """Analyze document image quality for optimal OCR processing"""
    
    def __init__(self):
        self.quality_thresholds = {
            'blur_threshold': 100,
            'brightness_min': 50,
            'brightness_max': 200,
            'contrast_min': 30,
            'noise_max': 0.1,
            'skew_max': 5.0,
            'resolution_min': 300
        }
    
    def assess_quality(self, image: np.ndarray) -> QualityAssessment:
        """Comprehensive quality assessment of document image"""
        
        metrics = {}
        issues = []
        recommendations = []
        
        # Convert to grayscale for analysis
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 1. Blur Detection
        blur_score = self._detect_blur(gray)
        metrics['blur_score'] = blur_score
        if blur_score < self.quality_thresholds['blur_threshold']:
            issues.append('Image is blurry')
            recommendations.append('Use better focus or capture from closer distance')
        
        # 2. Brightness Analysis
        brightness = self._analyze_brightness(gray)
        metrics['brightness'] = brightness
        if brightness < self.quality_thresholds['brightness_min']:
            issues.append('Image is too dark')
            recommendations.append('Increase lighting or camera exposure')
        elif brightness > self.quality_thresholds['brightness_max']:
            issues.append('Image is too bright/overexposed')
            recommendations.append('Reduce lighting or camera exposure')
        
        # 3. Contrast Analysis
        contrast = self._analyze_contrast(gray)
        metrics['contrast'] = contrast
        if contrast < self.quality_thresholds['contrast_min']:
            issues.append('Low contrast between text and background')
            recommendations.append('Improve lighting conditions or adjust camera settings')
        
        # 4. Noise Detection
        noise_level = self._detect_noise(gray)
        metrics['noise_level'] = noise_level
        if noise_level > self.quality_thresholds['noise_max']:
            issues.append('High noise level detected')
            recommendations.append('Use better lighting or reduce camera ISO')
        
        # 5. Skew Detection
        skew_angle = self._detect_skew(gray)
        metrics['skew_angle'] = abs(skew_angle)
        if abs(skew_angle) > self.quality_thresholds['skew_max']:
            issues.append(f'Document is skewed by {skew_angle:.1f} degrees')
            recommendations.append('Capture document straight-on, parallel to camera')
        
        # 6. Resolution Analysis
        resolution_score = self._analyze_resolution(image)
        metrics['resolution_score'] = resolution_score
        if resolution_score < 0.7:
            issues.append('Low resolution may affect text recognition')
            recommendations.append('Capture at higher resolution or move closer to document')
        
        # 7. Text Region Detection
        text_coverage = self._analyze_text_coverage(gray)
        metrics['text_coverage'] = text_coverage
        if text_coverage < 0.3:
            issues.append('Limited text content detected')
            recommendations.append('Ensure document fills frame and text is clearly visible')
        
        # Calculate overall quality score
        overall_score = self._calculate_overall_score(metrics)
        
        # Determine processing confidence
        if overall_score >= 0.8:
            confidence = 'high'
        elif overall_score >= 0.6:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return QualityAssessment(
            overall_score=overall_score,
            issues=issues,
            recommendations=recommendations,
            metrics=metrics,
            processing_confidence=confidence
        )
    
    def _detect_blur(self, image: np.ndarray) -> float:
        """Detect blur using Laplacian variance"""
        return cv2.Laplacian(image, cv2.CV_64F).var()
    
    def _analyze_brightness(self, image: np.ndarray) -> float:
        """Analyze average brightness"""
        return np.mean(image)
    
    def _analyze_contrast(self, image: np.ndarray) -> float:
        """Analyze contrast using standard deviation"""
        return np.std(image)
    
    def _detect_noise(self, image: np.ndarray) -> float:
        """Detect noise level using median filtering"""
        try:
            # Apply median filter and compare with original
            filtered = cv2.medianBlur(image, 5)
            noise = np.mean(np.abs(image.astype(float) - filtered.astype(float)))
            return noise / 255.0  # Normalize to 0-1
        except Exception:
            return 0.0
    
    def _detect_skew(self, image: np.ndarray) -> float:
        """Detect document skew angle"""
        try:
            # Edge detection
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            
            # Hough line transform
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None:
                angles = []
                for rho, theta in lines[:10]:  # Consider top 10 lines
                    angle = np.degrees(theta) - 90
                    if abs(angle) < 45:  # Filter out vertical lines
                        angles.append(angle)
                
                if angles:
                    return np.median(angles)
            
            return 0.0
        except Exception:
            return 0.0
    
    def _analyze_resolution(self, image: np.ndarray) -> float:
        """Analyze resolution adequacy"""
        height, width = image.shape[:2]
        
        # Check if image has sufficient resolution for OCR
        if min(height, width) < 300:  # Very low resolution
            return 0.3
        elif min(height, width) < 600:  # Low resolution
            return 0.6
        elif min(height, width) < 1200:  # Medium resolution
            return 0.8
        else:  # High resolution
            return 1.0
    
    def _analyze_text_coverage(self, image: np.ndarray) -> float:
        """Analyze text coverage in image"""
        try:
            # Apply adaptive threshold to find text regions
            thresh = cv2.adaptiveThreshold(
                image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Find contours (potential text regions)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours that could be text
            text_area = 0
            total_area = image.shape[0] * image.shape[1]
            
            for contour in contours:
                area = cv2.contourArea(contour)
                _, _, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                
                # Filter based on size and aspect ratio (typical for text)
                if 10 < area < total_area * 0.1 and 0.1 < aspect_ratio < 10:
                    text_area += area
            
            return min(text_area / total_area, 1.0)
        
        except Exception:
            return 0.5  # Default moderate score
    
    def _calculate_overall_score(self, metrics: Dict[str, float]) -> float:
        """Calculate weighted overall quality score"""
        weights = {
            'blur_score': 0.25,
            'brightness': 0.15,
            'contrast': 0.20,
            'noise_level': 0.15,
            'skew_angle': 0.10,
            'resolution_score': 0.10,
            'text_coverage': 0.05
        }
        
        normalized_scores = {}
        
        # Normalize blur score (higher is better, threshold at 100)
        normalized_scores['blur_score'] = min(metrics.get('blur_score', 0) / 100, 1.0)
        
        # Normalize brightness (ideal range 80-180)
        brightness = metrics.get('brightness', 128)
        if 80 <= brightness <= 180:
            normalized_scores['brightness'] = 1.0
        else:
            distance_from_ideal = min(abs(brightness - 80), abs(brightness - 180))
            normalized_scores['brightness'] = max(0, 1.0 - distance_from_ideal / 100)
        
        # Normalize contrast (higher is better, threshold at 50)
        normalized_scores['contrast'] = min(metrics.get('contrast', 0) / 50, 1.0)
        
        # Normalize noise (lower is better)
        normalized_scores['noise_level'] = max(0, 1.0 - metrics.get('noise_level', 0))
        
        # Normalize skew (lower angle is better)
        skew = metrics.get('skew_angle', 0)
        normalized_scores['skew_angle'] = max(0, 1.0 - skew / 45)
        
        # Resolution and text coverage are already 0-1
        normalized_scores['resolution_score'] = metrics.get('resolution_score', 0.5)
        normalized_scores['text_coverage'] = metrics.get('text_coverage', 0.5)
        
        # Calculate weighted average
        total_score = sum(score * weights.get(metric, 0) for metric, score in normalized_scores.items())
        
        return min(max(total_score, 0.0), 1.0)
    
    def get_enhancement_suggestions(self, assessment: QualityAssessment) -> List[str]:
        """Get specific enhancement suggestions based on quality assessment"""
        suggestions = []
        
        metrics = assessment.metrics
        
        # Specific technical suggestions
        if metrics.get('blur_score', 0) < 50:
            suggestions.append('Apply sharpening filter before OCR processing')
        
        if metrics.get('contrast', 0) < 25:
            suggestions.append('Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)')
        
        if metrics.get('brightness', 128) < 60:
            suggestions.append('Apply gamma correction to brighten image')
        elif metrics.get('brightness', 128) > 190:
            suggestions.append('Apply gamma correction to darken image')
        
        if metrics.get('noise_level', 0) > 0.08:
            suggestions.append('Apply bilateral filtering to reduce noise')
        
        if metrics.get('skew_angle', 0) > 3:
            suggestions.append('Apply skew correction before processing')
        
        if metrics.get('text_coverage', 0) < 0.4:
            suggestions.append('Crop image to focus on text regions')
        
        return suggestions


# Global quality analyzer instance
quality_analyzer = DocumentQualityAnalyzer()
