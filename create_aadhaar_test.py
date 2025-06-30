#!/usr/bin/env python3
"""
Create Aadhaar card image from attachment data
"""

from PIL import Image, ImageDraw, ImageFont
import base64
import io

def create_aadhaar_from_attachment():
    """Create Aadhaar card based on the visible data from the attachment"""
    
    # Create image similar to actual Aadhaar dimensions
    img = Image.new('RGB', (850, 540), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to load system fonts
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 20)
        text_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        number_font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 24)
        small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default() 
        number_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Add Indian flag colors header
    draw.rectangle([(0, 0), (850, 15)], fill='#FF9933')  # Saffron
    draw.rectangle([(0, 15), (850, 30)], fill='white')    # White  
    draw.rectangle([(0, 30), (850, 45)], fill='#138808')  # Green
    
    # Government header
    draw.text((50, 60), "भारत सरकार", fill='black', font=text_font)
    draw.text((50, 80), "Government of India", fill='#000080', font=title_font)
    
    # Based on the attachment information visible:
    # Name: Ved Thampi
    # DOB: 05/09/2000  
    # Gender: Male
    # Aadhaar: 9704 7285 0296
    
    # Add photo placeholder (visible in original)
    draw.rectangle([(50, 120), (150, 220)], outline='black', fill='lightgray')
    draw.text((75, 165), "PHOTO", fill='black', font=text_font)
    
    # Personal details section
    y_pos = 130
    
    # Name
    draw.text((180, y_pos), "नाम / Name", fill='black', font=text_font)
    draw.text((180, y_pos + 20), "Ved Thampi", fill='black', font=number_font)
    y_pos += 60
    
    # Date of Birth  
    draw.text((180, y_pos), "जन्म तिथि / DOB: 05/09/2000", fill='black', font=text_font)
    y_pos += 30
    
    # Gender
    draw.text((180, y_pos), "लिंग / Gender: Male", fill='black', font=text_font)
    y_pos += 40
    
    # Aadhaar number (as visible in attachment)
    draw.text((50, 280), "आधार संख्या / Aadhaar Number:", fill='black', font=text_font)
    draw.text((50, 310), "9704 7285 0296", fill='red', font=number_font)
    
    # Address section
    draw.text((50, 360), "पता / Address:", fill='black', font=text_font)
    draw.text((50, 380), "India", fill='black', font=text_font)
    
    # QR code placeholder (visible in original)
    draw.rectangle([(650, 300), (800, 450)], outline='black', fill='white')
    # Simple QR-like pattern
    for i in range(10):
        for j in range(10):
            if (i + j) % 2 == 0:
                draw.rectangle([
                    (660 + i*13, 310 + j*13), 
                    (670 + i*13, 320 + j*13)
                ], fill='black')
    
    # Bottom signature text
    draw.text((50, 480), "मेरा आधार, मेरी पहचान", fill='#FF9933', font=title_font)
    draw.text((50, 505), "My Aadhaar, My Identity", fill='#FF9933', font=text_font)
    
    return img

if __name__ == "__main__":
    # Create and save the image
    img = create_aadhaar_from_attachment()
    img.save('/Users/vedthampi/CascadeProjects/ocr-document-scanner/aadhaar-card-test.png', 'PNG')
    print("✅ Created Aadhaar test image: aadhaar-card-test.png")
    print("📋 Based on attachment data:")
    print("   • Name: Ved Thampi")
    print("   • DOB: 05/09/2000")
    print("   • Gender: Male") 
    print("   • Aadhaar: 9704 7285 0296")
