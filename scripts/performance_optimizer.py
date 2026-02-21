#!/usr/bin/env python3
"""
Performance Optimization Engine for OCR Document Scanner
Provides intelligent preprocessing selection and parallel processing capabilities
"""

import cv2
import numpy as np
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Optional, Any
import pytesseract
from dataclasses import dataclass

@dataclass
class ProcessingResult:
    """Structure to hold OCR processing results"""
    text: str
    confidence: float
    processing_time: float
    method: str
    config: str

class IntelligentPreprocessor:
    """Intelligent preprocessing with automatic parameter selection"""
    
    def __init__(self):
        self.preprocessing_cache = {}
        
    def analyze_image_characteristics(self, image: np.ndarray) -> Dict[str, float]:
        """Analyze image to determine optimal preprocessing strategy"""
        
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Calculate image metrics
        height, width = gray.shape
        total_pixels = height * width
        
        # Brightness analysis
        brightness = np.mean(gray)
        
        # Contrast analysis
        contrast = np.std(gray)
        
        # Blur detection using Laplacian variance
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Noise estimation
        noise_level = self.estimate_noise(gray)
        
        # Resolution assessment
        resolution_score = min(width, height) / 1000.0  # Normalized resolution score
        
        # Edge density (text complexity indicator)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / total_pixels
        
        return {
            'brightness': brightness,
            'contrast': contrast,
            'blur_score': blur_score,
            'noise_level': noise_level,
            'resolution_score': resolution_score,
            'edge_density': edge_density,
            'width': width,
            'height': height
        }
    
    def estimate_noise(self, image: np.ndarray) -> float:
        """Estimate noise level in image"""
        # Use a high-pass filter to estimate noise
        kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
        filtered = cv2.filter2D(image, -1, kernel)
        return np.std(filtered) / 255.0
    
    def select_optimal_preprocessing(self, characteristics: Dict[str, float]) -> List[str]:
        """Select optimal preprocessing steps based on image characteristics"""
        
        steps = []
        
        # Always start with basic enhancement
        steps.append('basic_enhancement')
        
        # Low resolution - add upscaling
        if characteristics['resolution_score'] < 0.8:
            steps.append('intelligent_upscale')
        
        # High noise - add denoising
        if characteristics['noise_level'] > 0.1:
            steps.append('advanced_denoise')
        
        # Low contrast - add contrast enhancement
        if characteristics['contrast'] < 30:
            steps.append('adaptive_contrast')
        
        # Poor lighting - add lighting correction
        if characteristics['brightness'] < 80 or characteristics['brightness'] > 180:
            steps.append('lighting_correction')
        
        # Blurry image - add sharpening
        if characteristics['blur_score'] < 100:
            steps.append('text_sharpening')
        
        # High edge density - might need morphological operations
        if characteristics['edge_density'] > 0.1:
            steps.append('morphological_cleanup')
        
        return steps
    
    def apply_preprocessing_pipeline(self, image: np.ndarray, steps: List[str]) -> List[np.ndarray]:
        """Apply selected preprocessing steps"""
        
        processed_images = []
        current_image = image.copy()
        
        for step in steps:
            if step == 'basic_enhancement':
                current_image = self.basic_enhancement(current_image)
            elif step == 'intelligent_upscale':
                current_image = self.intelligent_upscale(current_image)
            elif step == 'advanced_denoise':
                current_image = self.advanced_denoise(current_image)
            elif step == 'adaptive_contrast':
                current_image = self.adaptive_contrast(current_image)
            elif step == 'lighting_correction':
                current_image = self.lighting_correction(current_image)
            elif step == 'text_sharpening':
                current_image = self.text_sharpening(current_image)
            elif step == 'morphological_cleanup':
                current_image = self.morphological_cleanup(current_image)
            
            processed_images.append(current_image.copy())
        
        return processed_images
    
    def basic_enhancement(self, image: np.ndarray) -> np.ndarray:
        """Basic image enhancement"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # CLAHE enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        return enhanced
    
    def intelligent_upscale(self, image: np.ndarray) -> np.ndarray:
        """Intelligent upscaling using interpolation"""
        height, width = image.shape[:2]
        
        # Calculate optimal scale factor
        target_width = max(1920, width)
        target_height = max(1200, height)
        
        scale_x = target_width / width
        scale_y = target_height / height
        scale = min(scale_x, scale_y, 3.0)  # Limit maximum scale
        
        if scale > 1.1:  # Only upscale if significant improvement
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # Use INTER_CUBIC for better quality
            upscaled = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            return upscaled
        
        return image
    
    def advanced_denoise(self, image: np.ndarray) -> np.ndarray:
        """Advanced noise reduction"""
        if len(image.shape) == 3:
            # Color image
            denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        else:
            # Grayscale image
            denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
        
        return denoised
    
    def adaptive_contrast(self, image: np.ndarray) -> np.ndarray:
        """Adaptive contrast enhancement"""
        if len(image.shape) == 3:
            # Convert to LAB and enhance L channel
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            lab[:,:,0] = clahe.apply(lab[:,:,0])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            # Grayscale
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)
        
        return enhanced
    
    def lighting_correction(self, image: np.ndarray) -> np.ndarray:
        """Correct lighting issues"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Create illumination correction
        kernel_size = max(gray.shape) // 20
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        background = cv2.medianBlur(gray, kernel_size)
        corrected = cv2.divide(gray, background, scale=255)
        
        return corrected
    
    def text_sharpening(self, image: np.ndarray) -> np.ndarray:
        """Specialized sharpening for text"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Unsharp mask
        gaussian = cv2.GaussianBlur(gray, (0, 0), 2.0)
        sharpened = cv2.addWeighted(gray, 1.5, gaussian, -0.5, 0)
        
        return sharpened
    
    def morphological_cleanup(self, image: np.ndarray) -> np.ndarray:
        """Morphological operations for text cleanup"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Binary threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return cleaned

class ParallelOCRProcessor:
    """Parallel OCR processing for improved performance"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.ocr_configs = [
            '--oem 3 --psm 6',  # Uniform block of text
            '--oem 3 --psm 8',  # Single word
            '--oem 3 --psm 7',  # Single text line
            '--oem 3 --psm 11', # Sparse text
            '--oem 3 --psm 12', # Sparse text with OSD
            '--oem 3 --psm 13'  # Raw line with character
        ]
    
    def process_image_parallel(self, images: List[np.ndarray], language: str = 'eng') -> List[ProcessingResult]:
        """Process multiple images in parallel with different configurations"""
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all OCR tasks
            future_to_config = {}
            
            for i, image in enumerate(images):
                for j, config in enumerate(self.ocr_configs):
                    future = executor.submit(self._ocr_single_image, image, config, language, f"img_{i}_config_{j}")
                    future_to_config[future] = (i, j, config)
            
            # Collect results
            for future in as_completed(future_to_config):
                img_idx, config_idx, config = future_to_config[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"OCR failed for image {img_idx} with config {config}: {e}")
        
        return results
    
    def _ocr_single_image(self, image: np.ndarray, config: str, language: str, method: str) -> Optional[ProcessingResult]:
        """Process a single image with OCR"""
        
        start_time = time.time()
        
        try:
            # Run OCR
            text = pytesseract.image_to_string(image, lang=language, config=config)
            
            # Get confidence data
            data = pytesseract.image_to_data(image, lang=language, config=config, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                text=text.strip(),
                confidence=avg_confidence,
                processing_time=processing_time,
                method=method,
                config=config
            )
            
        except Exception as e:
            print(f"OCR error: {e}")
            return None
    
    def select_best_result(self, results: List[ProcessingResult]) -> ProcessingResult:
        """Select the best OCR result based on confidence and text quality"""
        
        if not results:
            return ProcessingResult("", 0, 0, "none", "none")
        
        # Score results based on multiple factors
        scored_results = []
        
        for result in results:
            score = 0
            
            # Confidence weight (40%)
            score += result.confidence * 0.4
            
            # Text length weight (20%) - longer text usually better
            text_length_score = min(len(result.text), 100) / 100 * 20
            score += text_length_score
            
            # Character diversity weight (20%) - more diverse text better
            unique_chars = len(set(result.text.lower()))
            diversity_score = min(unique_chars, 20) / 20 * 20
            score += diversity_score
            
            # Processing time weight (20%) - faster is better (inverted)
            time_score = max(0, 20 - result.processing_time) / 20 * 20
            score += time_score
            
            scored_results.append((score, result))
        
        # Return the highest scoring result
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return scored_results[0][1]

class PerformanceOptimizer:
    """Main performance optimization coordinator"""
    
    def __init__(self):
        self.preprocessor = IntelligentPreprocessor()
        self.ocr_processor = ParallelOCRProcessor()
        self.processing_cache = {}
    
    def process_document_optimized(self, image: np.ndarray, language: str = 'eng', document_type: str = 'auto') -> Dict[str, Any]:
        """
        Process document with full optimization pipeline
        """
        start_time = time.time()
        
        # Generate cache key
        cache_key = self._generate_cache_key(image, language, document_type)
        
        # Check cache first
        if cache_key in self.processing_cache:
            cached_result = self.processing_cache[cache_key].copy()
            cached_result['cache_hit'] = True
            return cached_result
        
        # Analyze image characteristics
        characteristics = self.preprocessor.analyze_image_characteristics(image)
        
        # Select optimal preprocessing
        preprocessing_steps = self.preprocessor.select_optimal_preprocessing(characteristics)
        
        # Apply preprocessing
        processed_images = self.preprocessor.apply_preprocessing_pipeline(image, preprocessing_steps)
        
        # Parallel OCR processing
        ocr_results = self.ocr_processor.process_image_parallel(processed_images, language)
        
        # Select best result
        best_result = self.ocr_processor.select_best_result(ocr_results)
        
        total_time = time.time() - start_time
        
        # Prepare final result
        result = {
            'text': best_result.text,
            'confidence': best_result.confidence,
            'processing_time': total_time,
            'best_method': best_result.method,
            'best_config': best_result.config,
            'preprocessing_steps': preprocessing_steps,
            'image_characteristics': characteristics,
            'total_ocr_attempts': len(ocr_results),
            'cache_hit': False
        }
        
        # Cache result
        self.processing_cache[cache_key] = result.copy()
        
        return result
    
    def _generate_cache_key(self, image: np.ndarray, language: str, document_type: str) -> str:
        """Generate cache key for image"""
        # Use image hash + parameters
        image_hash = hash(image.tobytes())
        return f"{image_hash}_{language}_{document_type}"
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'cache_size': len(self.processing_cache),
            'cache_hit_rate': self._calculate_cache_hit_rate(),
            'average_processing_time': self._calculate_avg_processing_time(),
            'preprocessing_usage': self._get_preprocessing_usage_stats()
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if not self.processing_cache:
            return 0.0
        
        cache_hits = sum(1 for result in self.processing_cache.values() if result.get('cache_hit', False))
        return cache_hits / len(self.processing_cache) * 100
    
    def _calculate_avg_processing_time(self) -> float:
        """Calculate average processing time"""
        if not self.processing_cache:
            return 0.0
        
        times = [result['processing_time'] for result in self.processing_cache.values()]
        return sum(times) / len(times)
    
    def _get_preprocessing_usage_stats(self) -> Dict[str, int]:
        """Get preprocessing step usage statistics"""
        step_counts = {}
        
        for result in self.processing_cache.values():
            for step in result.get('preprocessing_steps', []):
                step_counts[step] = step_counts.get(step, 0) + 1
        
        return step_counts

# Example usage and testing
if __name__ == "__main__":
    optimizer = PerformanceOptimizer()
    
    print("🚀 PERFORMANCE OPTIMIZATION ENGINE")
    print("=" * 50)
    print("Features:")
    print("• Intelligent preprocessing selection based on image analysis")
    print("• Parallel OCR processing with multiple configurations")
    print("• Advanced caching for repeated processing")
    print("• Performance monitoring and statistics")
    print("• Adaptive image enhancement")
    print("• Optimized memory usage")
    
    # Test with a sample image (would need actual image in real use)
    print("\n✅ Performance Optimization Engine ready for integration!")
