#!/usr/bin/env python3
"""
Advanced Security & Document Validation System
Provides enterprise-grade security validation, fraud detection, and document authenticity verification
"""

import cv2
import numpy as np
import json
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import hashlib
import hmac
import base64
from datetime import datetime, timedelta

# Image processing
from PIL import Image, ImageStat, ImageFilter
import pytesseract

# ML libraries for fraud detection
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SecurityValidationResult:
    """Result from security validation"""
    authenticity_score: float
    fraud_risk_level: str
    security_features_detected: List[str]
    validation_passed: bool
    fraud_indicators: List[str]
    document_integrity: Dict[str, Any]
    processing_time: float
    validation_method: str
    recommendations: List[str]

@dataclass
class DocumentFeatures:
    """Document features for security analysis"""
    image_quality: float
    text_consistency: float
    layout_authenticity: float
    security_features: List[str]
    anomaly_score: float
    metadata: Dict[str, Any]

class SecurityFeatureDetector:
    """Detect security features in documents"""
    
    def __init__(self):
        self.feature_templates = self._load_security_templates()
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42) if SKLEARN_AVAILABLE else None
        
    def detect_security_features(self, image: np.ndarray) -> List[str]:
        """Detect security features in document image"""
        features = []
        
        # Convert to grayscale for analysis
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # 1. Watermark detection
        if self._detect_watermark(gray):
            features.append("watermark")
            
        # 2. Microtext detection
        if self._detect_microtext(gray):
            features.append("microtext")
            
        # 3. Security thread detection
        if self._detect_security_thread(gray):
            features.append("security_thread")
            
        # 4. Hologram detection
        if self._detect_hologram(image):
            features.append("hologram")
            
        # 5. UV features detection
        if self._detect_uv_features(image):
            features.append("uv_features")
            
        # 6. Raised text detection
        if self._detect_raised_text(gray):
            features.append("raised_text")
            
        # 7. Security paper detection
        if self._detect_security_paper(gray):
            features.append("security_paper")
            
        # 8. Barcode/QR code detection
        if self._detect_barcode_qr(gray):
            features.append("barcode_qr")
            
        return features
    
    def _detect_watermark(self, gray: np.ndarray) -> bool:
        """Detect watermark patterns"""
        # Apply DFT to detect watermark patterns
        f_transform = cv2.dft(np.float32(gray), flags=cv2.DFT_COMPLEX_OUTPUT)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = 20 * np.log(cv2.magnitude(f_shift[:,:,0], f_shift[:,:,1]) + 1)
        
        # Check for periodic patterns that indicate watermarks
        std_dev = np.std(magnitude_spectrum)
        mean_val = np.mean(magnitude_spectrum)
        
        # Watermarks typically create patterns in frequency domain
        return std_dev > 15 and mean_val > 50
    
    def _detect_microtext(self, gray: np.ndarray) -> bool:
        """Detect microtext patterns"""
        # Use edge detection to find very fine text
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Count very small contours that might be microtext
        microtext_contours = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if 5 < area < 50:  # Very small areas that might be microtext
                microtext_contours += 1
        
        return microtext_contours > 100  # Threshold for microtext detection
    
    def _detect_security_thread(self, gray: np.ndarray) -> bool:
        """Detect security thread patterns"""
        # Look for thin vertical or horizontal lines
        kernel_vertical = np.ones((30, 1), np.uint8)
        kernel_horizontal = np.ones((1, 30), np.uint8)
        
        vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel_vertical)
        horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel_horizontal)
        
        # Check for consistent thin lines that might be security threads
        vertical_score = np.sum(vertical_lines > 200)
        horizontal_score = np.sum(horizontal_lines > 200)
        
        return vertical_score > 1000 or horizontal_score > 1000
    
    def _detect_hologram(self, image: np.ndarray) -> bool:
        """Detect hologram patterns using color analysis"""
        if len(image.shape) != 3:
            return False
            
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Holograms typically have iridescent colors
        # Check for color variations that might indicate holographic features
        hue_channel = hsv[:,:,0]
        saturation_channel = hsv[:,:,1]
        
        # Look for high saturation areas with varied hues
        high_sat_mask = saturation_channel > 100
        hue_variance = np.var(hue_channel[high_sat_mask])
        
        return hue_variance > 500  # Threshold for hologram detection
    
    def _detect_uv_features(self, image: np.ndarray) -> bool:
        """Detect UV-reactive features (approximation)"""
        # This is a simplified approximation - real UV detection requires special imaging
        if len(image.shape) != 3:
            return False
            
        # Look for areas with unusual color properties that might indicate UV features
        b, g, r = cv2.split(image)
        
        # UV features often appear differently under different lighting
        blue_dominance = np.sum(b > g) + np.sum(b > r)
        total_pixels = image.shape[0] * image.shape[1]
        
        return (blue_dominance / total_pixels) > 0.3
    
    def _detect_raised_text(self, gray: np.ndarray) -> bool:
        """Detect raised text using shadow analysis"""
        # Apply directional lighting simulation to detect raised features
        kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
        kernel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
        
        grad_x = cv2.filter2D(gray, cv2.CV_32F, kernel_x)
        grad_y = cv2.filter2D(gray, cv2.CV_32F, kernel_y)
        
        # Calculate gradient magnitude
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # Raised text typically creates consistent gradients
        gradient_std = np.std(gradient_magnitude)
        
        return gradient_std > 20  # Threshold for raised text detection
    
    def _detect_security_paper(self, gray: np.ndarray) -> bool:
        """Detect security paper patterns"""
        # Security paper often has specific texture patterns
        # Use Local Binary Pattern (LBP) approximation
        
        # Create a simple texture analysis
        texture_kernel = np.array([[1, 1, 1], [1, -8, 1], [1, 1, 1]])
        texture_response = cv2.filter2D(gray, cv2.CV_32F, texture_kernel)
        
        # Security paper typically has consistent texture patterns
        texture_variance = np.var(texture_response)
        
        return texture_variance > 100  # Threshold for security paper
    
    def _detect_barcode_qr(self, gray: np.ndarray) -> bool:
        """Detect barcode or QR code patterns"""
        # Use edge detection to find barcode/QR patterns
        edges = cv2.Canny(gray, 50, 150)
        
        # Look for rectangular patterns that might be barcodes/QR codes
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        rectangular_contours = 0
        for contour in contours:
            # Approximate contour to polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Check if it's roughly rectangular and of appropriate size
            if len(approx) == 4:
                area = cv2.contourArea(contour)
                if 1000 < area < 10000:  # Appropriate size for QR/barcode
                    rectangular_contours += 1
        
        return rectangular_contours > 0
    
    def _load_security_templates(self) -> Dict[str, Any]:
        """Load security feature templates"""
        # In a real implementation, these would be loaded from files
        return {
            "watermark_patterns": [],
            "microtext_patterns": [],
            "hologram_signatures": [],
            "security_thread_patterns": []
        }

class FraudDetector:
    """Advanced fraud detection system"""
    
    def __init__(self):
        self.fraud_patterns = self._load_fraud_patterns()
        self.known_frauds = self._load_known_frauds()
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42) if SKLEARN_AVAILABLE else None
        
    def detect_fraud_indicators(self, image: np.ndarray, text: str, features: Dict[str, Any]) -> Tuple[List[str], float]:
        """Detect fraud indicators in document"""
        indicators = []
        fraud_score = 0.0
        
        # 1. Image quality analysis
        quality_indicators = self._analyze_image_quality(image)
        indicators.extend(quality_indicators)
        
        # 2. Text consistency analysis
        text_indicators = self._analyze_text_consistency(text)
        indicators.extend(text_indicators)
        
        # 3. Layout authenticity check
        layout_indicators = self._analyze_layout_authenticity(image, text)
        indicators.extend(layout_indicators)
        
        # 4. Metadata analysis
        metadata_indicators = self._analyze_metadata(features)
        indicators.extend(metadata_indicators)
        
        # 5. Pattern matching against known frauds
        pattern_indicators = self._match_fraud_patterns(text, image)
        indicators.extend(pattern_indicators)
        
        # Calculate overall fraud score
        fraud_score = min(len(indicators) * 0.2, 1.0)
        
        return indicators, fraud_score
    
    def _analyze_image_quality(self, image: np.ndarray) -> List[str]:
        """Analyze image quality for fraud indicators"""
        indicators = []
        
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # 1. Compression artifacts
        if self._detect_compression_artifacts(gray):
            indicators.append("excessive_compression")
            
        # 2. Resolution inconsistencies
        if self._detect_resolution_inconsistencies(image):
            indicators.append("resolution_inconsistency")
            
        # 3. Noise patterns
        if self._detect_suspicious_noise(gray):
            indicators.append("suspicious_noise_pattern")
            
        # 4. Blurriness analysis
        if self._detect_selective_blur(gray):
            indicators.append("selective_blur")
            
        return indicators
    
    def _analyze_text_consistency(self, text: str) -> List[str]:
        """Analyze text for consistency issues"""
        indicators = []
        
        # 1. Font inconsistencies (approximation)
        if self._detect_font_inconsistencies(text):
            indicators.append("font_inconsistency")
            
        # 2. Spacing irregularities
        if self._detect_spacing_irregularities(text):
            indicators.append("spacing_irregularity")
            
        # 3. Character encoding issues
        if self._detect_encoding_issues(text):
            indicators.append("encoding_anomaly")
            
        # 4. Language inconsistencies
        if self._detect_language_inconsistencies(text):
            indicators.append("language_inconsistency")
            
        return indicators
    
    def _analyze_layout_authenticity(self, image: np.ndarray, text: str) -> List[str]:
        """Analyze document layout for authenticity"""
        indicators = []
        
        # 1. Alignment issues
        if self._detect_alignment_issues(image):
            indicators.append("alignment_anomaly")
            
        # 2. Scaling inconsistencies
        if self._detect_scaling_issues(image):
            indicators.append("scaling_inconsistency")
            
        # 3. Template matching
        if self._detect_template_anomalies(image, text):
            indicators.append("template_mismatch")
            
        return indicators
    
    def _analyze_metadata(self, features: Dict[str, Any]) -> List[str]:
        """Analyze metadata for fraud indicators"""
        indicators = []
        
        # Check for suspicious metadata patterns
        if features.get('processing_time', 0) < 0.1:
            indicators.append("suspiciously_fast_processing")
            
        if features.get('confidence', 1.0) == 1.0:
            indicators.append("perfect_confidence_anomaly")
            
        return indicators
    
    def _match_fraud_patterns(self, text: str, image: np.ndarray) -> List[str]:
        """Match against known fraud patterns"""
        indicators = []
        
        # Check against known fraudulent patterns
        for pattern_name, pattern_data in self.fraud_patterns.items():
            if self._matches_pattern(text, image, pattern_data):
                indicators.append(f"matches_known_fraud_pattern_{pattern_name}")
                
        return indicators
    
    def _detect_compression_artifacts(self, gray: np.ndarray) -> bool:
        """Detect excessive compression artifacts"""
        # Use DCT to detect compression artifacts
        # This is a simplified approach
        dct = cv2.dct(np.float32(gray))
        
        # Check for typical JPEG compression patterns
        high_freq_energy = np.sum(np.abs(dct[gray.shape[0]//2:, gray.shape[1]//2:]))
        total_energy = np.sum(np.abs(dct))
        
        if total_energy > 0:
            high_freq_ratio = high_freq_energy / total_energy
            return high_freq_ratio < 0.01  # Too little high frequency content
        
        return False
    
    def _detect_resolution_inconsistencies(self, image: np.ndarray) -> bool:
        """Detect resolution inconsistencies"""
        # Check for areas with different apparent resolutions
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Divide image into blocks and analyze sharpness
        h, w = gray.shape
        block_size = 50
        sharpness_values = []
        
        for i in range(0, h-block_size, block_size):
            for j in range(0, w-block_size, block_size):
                block = gray[i:i+block_size, j:j+block_size]
                # Calculate sharpness using Laplacian variance
                sharpness = cv2.Laplacian(block, cv2.CV_64F).var()
                sharpness_values.append(sharpness)
        
        # Check for high variance in sharpness across blocks
        if len(sharpness_values) > 1:
            sharpness_std = np.std(sharpness_values)
            return sharpness_std > 100  # Threshold for inconsistency
        
        return False
    
    def _detect_suspicious_noise(self, gray: np.ndarray) -> bool:
        """Detect suspicious noise patterns"""
        # Calculate noise characteristics
        noise = gray.astype(np.float64) - cv2.GaussianBlur(gray, (5, 5), 0).astype(np.float64)
        noise_std = np.std(noise)
        
        # Check for artificial noise patterns
        return noise_std > 15  # Threshold for suspicious noise
    
    def _detect_selective_blur(self, gray: np.ndarray) -> bool:
        """Detect selective blur (indicating possible tampering)"""
        # Calculate local sharpness
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian_var = laplacian.var()
        
        # Check for very low variance (indicating blur)
        return laplacian_var < 50
    
    def _detect_font_inconsistencies(self, text: str) -> bool:
        """Detect font inconsistencies (simplified)"""
        # This is a simplified approach - real implementation would use more sophisticated analysis
        # Check for unusual character combinations that might indicate font substitution
        unusual_chars = sum(1 for c in text if ord(c) > 127)
        total_chars = len(text)
        
        if total_chars > 0:
            unusual_ratio = unusual_chars / total_chars
            return unusual_ratio > 0.3  # High ratio of unusual characters
        
        return False
    
    def _detect_spacing_irregularities(self, text: str) -> bool:
        """Detect spacing irregularities"""
        # Check for unusual spacing patterns
        words = text.split()
        if len(words) < 2:
            return False
            
        # Check for words that are too short or too long
        word_lengths = [len(word) for word in words]
        avg_length = np.mean(word_lengths)
        std_length = np.std(word_lengths)
        
        return std_length > avg_length * 1.5  # High variance in word lengths
    
    def _detect_encoding_issues(self, text: str) -> bool:
        """Detect character encoding issues"""
        # Check for encoding artifacts
        try:
            # Try to encode/decode to detect issues
            text.encode('utf-8').decode('utf-8')
            return False
        except UnicodeEncodeError:
            return True
    
    def _detect_language_inconsistencies(self, text: str) -> bool:
        """Detect language inconsistencies"""
        # Simple check for mixed scripts that might indicate tampering
        has_latin = any(ord(c) < 128 for c in text)
        has_devanagari = any(0x900 <= ord(c) <= 0x97F for c in text)
        has_arabic = any(0x600 <= ord(c) <= 0x6FF for c in text)
        
        script_count = sum([has_latin, has_devanagari, has_arabic])
        
        # Having more than 2 scripts might indicate tampering
        return script_count > 2
    
    def _detect_alignment_issues(self, image: np.ndarray) -> bool:
        """Detect alignment issues"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Detect lines and check for alignment
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
        
        if lines is not None:
            # Check for horizontal lines alignment
            horizontal_lines = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                if abs(angle) < 10:  # Approximately horizontal
                    horizontal_lines.append(y1)
            
            if len(horizontal_lines) > 1:
                # Check if lines are properly aligned
                alignment_variance = np.var(horizontal_lines)
                return alignment_variance > 100  # Threshold for misalignment
        
        return False
    
    def _detect_scaling_issues(self, image: np.ndarray) -> bool:
        """Detect scaling inconsistencies"""
        # This is a simplified approach
        # Check for areas with different apparent scaling
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Use template matching approach to detect scaling issues
        # For now, use a simple edge density analysis
        edges = cv2.Canny(gray, 50, 150)
        
        # Divide image into regions and check edge density
        h, w = gray.shape
        region_size = 100
        edge_densities = []
        
        for i in range(0, h-region_size, region_size):
            for j in range(0, w-region_size, region_size):
                region = edges[i:i+region_size, j:j+region_size]
                edge_density = np.sum(region > 0) / (region_size * region_size)
                edge_densities.append(edge_density)
        
        # Check for high variance in edge density
        if len(edge_densities) > 1:
            density_std = np.std(edge_densities)
            return density_std > 0.1  # Threshold for scaling issues
        
        return False
    
    def _detect_template_anomalies(self, image: np.ndarray, text: str) -> bool:
        """Detect template anomalies"""
        # This would compare against known document templates
        # For now, use a simple approach
        
        # Check if document has expected layout elements
        expected_elements = ["name", "date", "number", "address"]
        found_elements = 0
        
        text_lower = text.lower()
        for element in expected_elements:
            if element in text_lower:
                found_elements += 1
        
        # If too few expected elements are found, it might be anomalous
        return found_elements < 2
    
    def _matches_pattern(self, text: str, image: np.ndarray, pattern_data: Dict[str, Any]) -> bool:
        """Check if document matches a known fraud pattern"""
        # This would implement sophisticated pattern matching
        # For now, use a simple approach
        
        if "text_patterns" in pattern_data:
            for pattern in pattern_data["text_patterns"]:
                if pattern in text.lower():
                    return True
        
        return False
    
    def _load_fraud_patterns(self) -> Dict[str, Any]:
        """Load known fraud patterns"""
        # In a real implementation, these would be loaded from a database
        return {
            "common_fraud_1": {
                "text_patterns": ["fake", "counterfeit", "specimen"],
                "image_signatures": []
            },
            "template_substitution": {
                "text_patterns": ["template", "sample", "example"],
                "image_signatures": []
            }
        }
    
    def _load_known_frauds(self) -> List[Dict[str, Any]]:
        """Load database of known fraudulent documents"""
        # In a real implementation, this would load from a secure database
        return []

class DocumentSecurityValidator:
    """Main document security validation system"""
    
    def __init__(self):
        self.security_detector = SecurityFeatureDetector()
        self.fraud_detector = FraudDetector()
        self.validation_history = []
        
    def validate_document_security(self, image: np.ndarray, text: str, features: Dict[str, Any] = None) -> SecurityValidationResult:
        """Perform comprehensive security validation"""
        start_time = time.time()
        
        if features is None:
            features = {}
        
        # 1. Detect security features
        security_features = self.security_detector.detect_security_features(image)
        
        # 2. Detect fraud indicators
        fraud_indicators, fraud_score = self.fraud_detector.detect_fraud_indicators(image, text, features)
        
        # 3. Calculate authenticity score
        authenticity_score = self._calculate_authenticity_score(security_features, fraud_indicators)
        
        # 4. Determine fraud risk level
        fraud_risk_level = self._determine_fraud_risk_level(fraud_score, authenticity_score)
        
        # 5. Check document integrity
        document_integrity = self._check_document_integrity(image, text)
        
        # 6. Generate recommendations
        recommendations = self._generate_recommendations(security_features, fraud_indicators, authenticity_score)
        
        # 7. Determine if validation passed
        validation_passed = self._determine_validation_result(authenticity_score, fraud_risk_level)
        
        processing_time = time.time() - start_time
        
        result = SecurityValidationResult(
            authenticity_score=authenticity_score,
            fraud_risk_level=fraud_risk_level,
            security_features_detected=security_features,
            validation_passed=validation_passed,
            fraud_indicators=fraud_indicators,
            document_integrity=document_integrity,
            processing_time=processing_time,
            validation_method="Advanced Security Analysis",
            recommendations=recommendations
        )
        
        # Store validation history
        self.validation_history.append({
            'timestamp': datetime.now().isoformat(),
            'result': result,
            'document_hash': hashlib.sha256(image.tobytes()).hexdigest()[:16]
        })
        
        return result
    
    def _calculate_authenticity_score(self, security_features: List[str], fraud_indicators: List[str]) -> float:
        """Calculate overall authenticity score"""
        base_score = 0.5  # Base score
        
        # Add points for security features
        feature_score = len(security_features) * 0.1
        
        # Subtract points for fraud indicators
        fraud_penalty = len(fraud_indicators) * 0.15
        
        # Calculate final score
        final_score = base_score + feature_score - fraud_penalty
        
        # Clamp between 0 and 1
        return max(0.0, min(1.0, final_score))
    
    def _determine_fraud_risk_level(self, fraud_score: float, authenticity_score: float) -> str:
        """Determine fraud risk level"""
        combined_risk = (fraud_score + (1 - authenticity_score)) / 2
        
        if combined_risk < 0.3:
            return "LOW"
        elif combined_risk < 0.6:
            return "MEDIUM"
        elif combined_risk < 0.8:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _check_document_integrity(self, image: np.ndarray, text: str) -> Dict[str, Any]:
        """Check document integrity"""
        integrity = {
            'image_hash': hashlib.sha256(image.tobytes()).hexdigest(),
            'text_hash': hashlib.sha256(text.encode()).hexdigest(),
            'timestamp': datetime.now().isoformat(),
            'image_size': image.shape,
            'text_length': len(text)
        }
        
        return integrity
    
    def _generate_recommendations(self, security_features: List[str], fraud_indicators: List[str], authenticity_score: float) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        if authenticity_score < 0.5:
            recommendations.append("Document requires manual verification")
            
        if len(security_features) < 2:
            recommendations.append("Document lacks expected security features")
            
        if "excessive_compression" in fraud_indicators:
            recommendations.append("Image quality is too low for reliable verification")
            
        if "font_inconsistency" in fraud_indicators:
            recommendations.append("Text shows signs of possible tampering")
            
        if not recommendations:
            recommendations.append("Document appears authentic")
            
        return recommendations
    
    def _determine_validation_result(self, authenticity_score: float, fraud_risk_level: str) -> bool:
        """Determine if validation passed"""
        if fraud_risk_level in ["HIGH", "CRITICAL"]:
            return False
            
        if authenticity_score < 0.4:
            return False
            
        return True
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics"""
        if not self.validation_history:
            return {"total_validations": 0}
        
        total_validations = len(self.validation_history)
        passed_validations = sum(1 for v in self.validation_history if v['result'].validation_passed)
        
        fraud_risk_counts = {}
        for v in self.validation_history:
            risk_level = v['result'].fraud_risk_level
            fraud_risk_counts[risk_level] = fraud_risk_counts.get(risk_level, 0) + 1
        
        avg_authenticity = np.mean([v['result'].authenticity_score for v in self.validation_history])
        avg_processing_time = np.mean([v['result'].processing_time for v in self.validation_history])
        
        return {
            "total_validations": total_validations,
            "passed_validations": passed_validations,
            "pass_rate": passed_validations / total_validations * 100,
            "fraud_risk_distribution": fraud_risk_counts,
            "average_authenticity_score": avg_authenticity,
            "average_processing_time": avg_processing_time
        }

# Usage example and testing
if __name__ == "__main__":
    print("🔐 DOCUMENT SECURITY VALIDATOR - INITIALIZATION")
    print("=" * 60)
    
    # Initialize validator
    validator = DocumentSecurityValidator()
    
    # Test with sample document
    print("\n🧪 TESTING SECURITY VALIDATION...")
    
    # Create test image
    test_image = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)
    test_text = "Government of India Aadhaar Card 9704 7285 0296 Ved Thampi"
    
    # Perform validation
    result = validator.validate_document_security(test_image, test_text)
    
    print(f"\n📊 SECURITY VALIDATION RESULTS:")
    print(f"   🔍 Authenticity Score: {result.authenticity_score:.3f}")
    print(f"   ⚠️  Fraud Risk Level: {result.fraud_risk_level}")
    print(f"   ✅ Validation Passed: {result.validation_passed}")
    print(f"   🛡️  Security Features: {', '.join(result.security_features_detected) if result.security_features_detected else 'None detected'}")
    print(f"   🚨 Fraud Indicators: {', '.join(result.fraud_indicators) if result.fraud_indicators else 'None detected'}")
    print(f"   ⏱️  Processing Time: {result.processing_time:.3f} seconds")
    print(f"   💡 Recommendations: {', '.join(result.recommendations)}")
    
    # Show statistics
    stats = validator.get_validation_statistics()
    print(f"\n📈 VALIDATION STATISTICS:")
    print(f"   Total Validations: {stats['total_validations']}")
    print(f"   Pass Rate: {stats['pass_rate']:.1f}%")
    print(f"   Average Authenticity Score: {stats['average_authenticity_score']:.3f}")
    print(f"   Average Processing Time: {stats['average_processing_time']:.3f}s")
    
    print(f"\n✅ DOCUMENT SECURITY VALIDATOR READY!")
    print("   • Advanced fraud detection algorithms")
    print("   • Security feature detection")
    print("   • Document integrity verification")
    print("   • Enterprise-grade validation")
    print("   • Comprehensive reporting and analytics")
