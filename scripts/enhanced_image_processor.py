#!/usr/bin/env python3
"""
Enhanced Image Processing Module for OCR Document Scanner
Provides advanced image enhancement, scaling, and optimization capabilities
"""

import cv2
import numpy as np
import math
import io
import base64
from typing import List, Tuple, Dict, Optional

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL/Pillow not available. Some features will be limited.")

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    print("Warning: qrcode library not available. QR code generation will be disabled.")

class EnhancedImageProcessor:
    """Advanced image processing for optimal OCR results"""
    
    def __init__(self):
        self.target_dpi = 300  # Optimal DPI for OCR
        self.min_resolution = (1920, 1200)  # Minimum resolution for good OCR
        self.max_resolution = (4800, 3000)  # Maximum to prevent memory issues
        
    def enhance_image_quality(self, image: np.ndarray) -> np.ndarray:
        """
        Comprehensive image enhancement for optimal OCR
        """
        # Convert to PIL for advanced operations
        if len(image.shape) == 3:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            pil_image = Image.fromarray(image)
        
        # 1. Intelligent upscaling if needed
        current_size = pil_image.size
        if current_size[0] < self.min_resolution[0] or current_size[1] < self.min_resolution[1]:
            pil_image = self.intelligent_upscale(pil_image)
        
        # 2. Advanced noise reduction
        pil_image = self.advanced_denoise(pil_image)
        
        # 3. Adaptive contrast enhancement
        pil_image = self.adaptive_contrast_enhancement(pil_image)
        
        # 4. Shadow and lighting correction
        pil_image = self.shadow_correction(pil_image)
        
        # 5. Text sharpening
        pil_image = self.text_sharpening(pil_image)
        
        # Convert back to OpenCV format
        if len(image.shape) == 3:
            return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        else:
            return np.array(pil_image.convert('L'))
    
    def intelligent_upscale(self, image: Image.Image) -> Image.Image:
        """
        Intelligent upscaling using Lanczos algorithm with sharpening
        """
        current_size = image.size
        target_size = self.calculate_optimal_size(current_size)
        
        # Use Lanczos for high-quality upscaling
        try:
            upscaled = image.resize(target_size, Image.Resampling.LANCZOS)
        except AttributeError:
            # Fallback for older PIL versions
            upscaled = image.resize(target_size, Image.LANCZOS)
        
        # Apply unsharp mask after upscaling
        enhancer = ImageEnhance.Sharpness(upscaled)
        upscaled = enhancer.enhance(1.2)
        
        return upscaled
    
    def calculate_optimal_size(self, current_size: Tuple[int, int]) -> Tuple[int, int]:
        """Calculate optimal size for OCR processing"""
        width, height = current_size
        aspect_ratio = width / height
        
        # Target minimum resolution while maintaining aspect ratio
        if width < self.min_resolution[0]:
            new_width = self.min_resolution[0]
            new_height = int(new_width / aspect_ratio)
        elif height < self.min_resolution[1]:
            new_height = self.min_resolution[1]
            new_width = int(new_height * aspect_ratio)
        else:
            return current_size
        
        # Ensure we don't exceed maximum resolution
        if new_width > self.max_resolution[0]:
            new_width = self.max_resolution[0]
            new_height = int(new_width / aspect_ratio)
        if new_height > self.max_resolution[1]:
            new_height = self.max_resolution[1]
            new_width = int(new_height * aspect_ratio)
        
        return (new_width, new_height)
    
    def advanced_denoise(self, image: Image.Image) -> Image.Image:
        """
        Advanced noise reduction using multiple techniques
        """
        # Convert to numpy for OpenCV operations
        img_array = np.array(image)
        
        if len(img_array.shape) == 3:
            # Color image - convert to BGR for OpenCV
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Non-local means denoising for color images
            denoised = cv2.fastNlMeansDenoisingColored(img_cv, None, 10, 10, 7, 21)
            
            # Convert back to RGB
            denoised_rgb = cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB)
            return Image.fromarray(denoised_rgb)
        else:
            # Grayscale image
            denoised = cv2.fastNlMeansDenoising(img_array, None, 10, 7, 21)
            return Image.fromarray(denoised)
    
    def adaptive_contrast_enhancement(self, image: Image.Image) -> Image.Image:
        """
        Adaptive contrast enhancement based on image analysis
        """
        # Convert to grayscale for analysis
        gray = image.convert('L')
        histogram = gray.histogram()
        
        # Calculate image statistics
        pixels = sum(histogram)
        mean_brightness = sum(i * histogram[i] for i in range(256)) / pixels
        
        # Adaptive contrast based on brightness
        if mean_brightness < 80:  # Dark image
            contrast_factor = 1.4
            brightness_factor = 1.2
        elif mean_brightness > 180:  # Bright image
            contrast_factor = 1.2
            brightness_factor = 0.9
        else:  # Normal image
            contrast_factor = 1.3
            brightness_factor = 1.0
        
        # Apply enhancements
        enhancer = ImageEnhance.Contrast(image)
        enhanced = enhancer.enhance(contrast_factor)
        
        enhancer = ImageEnhance.Brightness(enhanced)
        enhanced = enhancer.enhance(brightness_factor)
        
        return enhanced
    
    def shadow_correction(self, image: Image.Image) -> Image.Image:
        """
        Correct shadows and uneven lighting
        """
        # Convert to numpy array
        img_array = np.array(image)
        
        if len(img_array.shape) == 3:
            # Convert to LAB color space
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            lab[:,:,0] = clahe.apply(lab[:,:,0])
            
            # Convert back to RGB
            corrected = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            corrected_rgb = cv2.cvtColor(corrected, cv2.COLOR_BGR2RGB)
            
            return Image.fromarray(corrected_rgb)
        else:
            # Grayscale - apply CLAHE directly
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            corrected = clahe.apply(img_array)
            return Image.fromarray(corrected)
    
    def text_sharpening(self, image: Image.Image) -> Image.Image:
        """
        Specialized sharpening for text clarity
        """
        # Convert to OpenCV format
        img_array = np.array(image)
        
        if len(img_array.shape) == 3:
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        else:
            gray = img_array
        
        # Custom kernel for text sharpening
        kernel = np.array([[-0.5, -1, -0.5],
                          [-1, 7, -1],
                          [-0.5, -1, -0.5]])
        
        sharpened = cv2.filter2D(gray, -1, kernel)
        
        # Convert back to original format
        if len(img_array.shape) == 3:
            # Convert back to color
            sharpened_bgr = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)
            sharpened_rgb = cv2.cvtColor(sharpened_bgr, cv2.COLOR_BGR2RGB)
            return Image.fromarray(sharpened_rgb)
        else:
            return Image.fromarray(sharpened)
    
    def correct_perspective(self, image: np.ndarray) -> np.ndarray:
        """
        Automatic perspective correction for documents
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find the largest rectangular contour (likely the document)
        for contour in sorted(contours, key=cv2.contourArea, reverse=True):
            # Approximate contour
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # If we have 4 points, we found our document
            if len(approx) == 4:
                # Get corner points
                corners = approx.reshape(4, 2).astype(np.float32)
                
                # Order points: top-left, top-right, bottom-right, bottom-left
                corners = self.order_points(corners)
                
                # Calculate dimensions
                width = int(max(
                    np.linalg.norm(corners[1] - corners[0]),
                    np.linalg.norm(corners[2] - corners[3])
                ))
                height = int(max(
                    np.linalg.norm(corners[3] - corners[0]),
                    np.linalg.norm(corners[2] - corners[1])
                ))
                
                # Define destination points
                dst = np.array([
                    [0, 0],
                    [width - 1, 0],
                    [width - 1, height - 1],
                    [0, height - 1]
                ], dtype=np.float32)
                
                # Get perspective transform matrix
                matrix = cv2.getPerspectiveTransform(corners, dst)
                
                # Apply perspective correction
                corrected = cv2.warpPerspective(image, matrix, (width, height))
                return corrected
        
        # If no document found, return original image
        return image
    
    def order_points(self, points: np.ndarray) -> np.ndarray:
        """Order points in clockwise order starting from top-left"""
        rect = np.zeros((4, 2), dtype=np.float32)
        
        # Top-left point has smallest sum
        s = points.sum(axis=1)
        rect[0] = points[np.argmin(s)]
        
        # Bottom-right point has largest sum
        rect[2] = points[np.argmax(s)]
        
        # Top-right point has smallest difference
        diff = np.diff(points, axis=1)
        rect[1] = points[np.argmin(diff)]
        
        # Bottom-left point has largest difference
        rect[3] = points[np.argmax(diff)]
        
        return rect

class ProfessionalTestImageGenerator:
    """Generate professional-quality test images for document testing"""
    
    def __init__(self):
        self.base_resolution = (2400, 1500)  # High resolution for crisp text
        self.dpi = 300
        
    def create_professional_aadhaar(self) -> Image.Image:
        """Create a professional Aadhaar card with realistic features"""
        
        # Create high-resolution image
        img = Image.new('RGB', self.base_resolution, color='white')
        draw = ImageDraw.Draw(img)
        
        # Load fonts with fallbacks
        fonts = self.load_professional_fonts()
        
        # Add Indian tricolor header (proportional)
        header_height = 60
        draw.rectangle([(0, 0), (self.base_resolution[0], header_height//3)], fill='#FF9933')  # Saffron
        draw.rectangle([(0, header_height//3), (self.base_resolution[0], 2*header_height//3)], fill='white')
        draw.rectangle([(0, 2*header_height//3), (self.base_resolution[0], header_height)], fill='#138808')  # Green
        
        # Add Ashoka Chakra (simplified representation)
        chakra_center = (self.base_resolution[0]//2, header_height//2)
        chakra_radius = 15
        draw.ellipse([
            (chakra_center[0] - chakra_radius, chakra_center[1] - chakra_radius),
            (chakra_center[0] + chakra_radius, chakra_center[1] + chakra_radius)
        ], outline='#000080', width=2)
        
        # Add radial lines (simplified Ashoka Chakra)
        for i in range(24):
            angle = i * 2 * math.pi / 24
            x1 = chakra_center[0] + (chakra_radius - 5) * math.cos(angle)
            y1 = chakra_center[1] + (chakra_radius - 5) * math.sin(angle)
            x2 = chakra_center[0] + (chakra_radius - 2) * math.cos(angle)
            y2 = chakra_center[1] + (chakra_radius - 2) * math.sin(angle)
            draw.line([(x1, y1), (x2, y2)], fill='#000080', width=1)
        
        # Government header
        y_pos = header_height + 40
        draw.text((120, y_pos), "भारत सरकार", fill='black', font=fonts['hindi'])
        draw.text((120, y_pos + 50), "Government of India", fill='black', font=fonts['title'])
        draw.text((120, y_pos + 100), "Unique Identification Authority of India", fill='#0066CC', font=fonts['subtitle'])
        
        # UIDAI logo placeholder (more realistic)
        logo_box = [(120, y_pos + 150), (250, y_pos + 220)]
        draw.rectangle(logo_box, outline='#FF9933', width=3)
        draw.text((125, y_pos + 170), "आधार", fill='#FF9933', font=fonts['logo'])
        draw.text((125, y_pos + 195), "UIDAI", fill='#FF9933', font=fonts['text'])
        
        # Main content with better spacing
        content_y = y_pos + 280
        
        # Aadhaar number (highlighted)
        draw.rectangle([(120, content_y - 10), (800, content_y + 60)], fill='#FFF8DC', outline='#DDD', width=1)
        draw.text((140, content_y), "आधार संख्या / Aadhaar Number:", fill='black', font=fonts['label'])
        draw.text((140, content_y + 35), "9704 7285 0296", fill='#CC0000', font=fonts['number'])
        
        content_y += 120
        
        # Personal details
        details = [
            ("नाम / Name:", "Ved Thampi"),
            ("जन्म तिथि / Date of Birth:", "05/09/2000"),
            ("लिंग / Gender:", "पुरुष / Male"),
            ("पिता का नाम / Father's Name:", "Rajesh Thampi")
        ]
        
        for label, value in details:
            draw.text((120, content_y), label, fill='black', font=fonts['label'])
            draw.text((500, content_y), value, fill='black', font=fonts['text'])
            content_y += 60
        
        # Address section
        content_y += 20
        draw.text((120, content_y), "पता / Address:", fill='black', font=fonts['label'])
        draw.text((120, content_y + 45), "123 Main Street, Trivandrum,", fill='black', font=fonts['text'])
        draw.text((120, content_y + 85), "Kerala - 695001, India", fill='black', font=fonts['text'])
        
        # Generate functional QR code
        qr_img = self.generate_qr_code("aadhaar:9704728502965:Ved Thampi:05/09/2000")
        qr_size = (300, 300)
        # Handle PIL compatibility issue - fallback for older PIL versions
        try:
            qr_img = qr_img.resize(qr_size, Image.Resampling.NEAREST)
        except AttributeError:
            # Fallback for older PIL versions
            qr_img = qr_img.resize(qr_size, Image.NEAREST)
        
        # Paste QR code
        qr_position = (self.base_resolution[0] - 400, content_y - 200)
        img.paste(qr_img, qr_position)
        
        # Photo placeholder (more realistic)
        photo_box = [(self.base_resolution[0] - 400, content_y + 120), (self.base_resolution[0] - 120, content_y + 350)]
        draw.rectangle(photo_box, fill='#F0F0F0', outline='#333', width=2)
        # Add photo corners
        corner_size = 20
        for corner in [(photo_box[0][0], photo_box[0][1]), (photo_box[1][0]-corner_size, photo_box[0][1]),
                      (photo_box[0][0], photo_box[1][1]-corner_size), (photo_box[1][0]-corner_size, photo_box[1][1]-corner_size)]:
            draw.rectangle([corner, (corner[0]+corner_size, corner[1]+corner_size)], fill='#888')
        
        draw.text((photo_box[0][0]+80, photo_box[0][1]+110), "PHOTO", fill='#666', font=fonts['text'])
        
        # Bottom signature area
        bottom_y = self.base_resolution[1] - 120
        draw.text((120, bottom_y), "मेरा आधार, मेरी पहचान", fill='#FF9933', font=fonts['hindi'])
        draw.text((120, bottom_y + 40), "My Aadhaar, My Identity", fill='#FF9933', font=fonts['subtitle'])
        
        # Add security features simulation
        self.add_security_features(img, draw)
        
        return img
    
    def load_professional_fonts(self) -> Dict[str, ImageFont.ImageFont]:
        """Load professional fonts with fallbacks"""
        fonts = {}
        
        font_paths = [
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        ]
        
        try:
            # Try to load system fonts
            for font_path in font_paths:
                try:
                    fonts['title'] = ImageFont.truetype(font_path, 48)
                    fonts['subtitle'] = ImageFont.truetype(font_path, 32)
                    fonts['label'] = ImageFont.truetype(font_path, 28)
                    fonts['text'] = ImageFont.truetype(font_path, 26)
                    fonts['number'] = ImageFont.truetype(font_path, 36)
                    fonts['hindi'] = ImageFont.truetype(font_path, 24)
                    fonts['logo'] = ImageFont.truetype(font_path, 20)
                    break
                except:
                    continue
        except:
            pass
        
        # Fallback to default font
        for key in ['title', 'subtitle', 'label', 'text', 'number', 'hindi', 'logo']:
            if key not in fonts:
                fonts[key] = ImageFont.load_default()
        
        return fonts
    
    def generate_qr_code(self, data: str) -> Image.Image:
        """Generate a functional QR code"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        return qr.make_image(fill_color="black", back_color="white")
    
    def add_security_features(self, img: Image.Image, draw: ImageDraw.Draw):
        """Add simulated security features"""
        width, height = img.size
        
        # Add subtle watermark pattern
        for x in range(0, width, 200):
            for y in range(0, height, 200):
                draw.text((x, y), "आधार", fill=(220, 220, 220), font=ImageFont.load_default())
        
        # Add border with pattern
        border_width = 8
        for i in range(border_width):
            color_intensity = 200 + i * 5
            draw.rectangle([(i, i), (width-i-1, height-i-1)], 
                         outline=(color_intensity, color_intensity, color_intensity), width=1)

# Usage example and testing functions
if __name__ == "__main__":
    # Initialize processors
    enhancer = EnhancedImageProcessor()
    generator = ProfessionalTestImageGenerator()
    
    print("Creating professional Aadhaar test image...")
    professional_aadhaar = generator.create_professional_aadhaar()
    professional_aadhaar.save('/Users/vedthampi/CascadeProjects/ocr-document-scanner/professional_aadhaar_test.png', 
                             dpi=(300, 300), quality=95)
    print("✅ Professional Aadhaar image saved as 'professional_aadhaar_test.png'")
    
    print("\n🎨 ENHANCED IMAGE PROCESSOR FEATURES:")
    print("• Intelligent upscaling for low-resolution images")
    print("• Advanced noise reduction using non-local means")
    print("• Adaptive contrast enhancement based on image analysis")
    print("• Shadow and lighting correction with CLAHE")
    print("• Specialized text sharpening")
    print("• Automatic perspective correction")
    print("• Professional test image generation with functional QR codes")
