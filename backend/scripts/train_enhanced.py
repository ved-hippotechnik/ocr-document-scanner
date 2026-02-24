#!/usr/bin/env python3
"""
Enhanced training script that generates realistic synthetic document images
and trains both classifiers (DocumentClassifier + MLDocumentClassifier).
"""
import sys
import os
import io
import random
import logging
import string
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Synthetic document image generators
# ---------------------------------------------------------------------------

def _random_name():
    first = random.choice(['Amit', 'Priya', 'Raj', 'Sunita', 'Vikram', 'Kavitha',
                           'Ahmed', 'Fatima', 'John', 'Sarah', 'Wei', 'Mei'])
    last = random.choice(['Sharma', 'Patel', 'Kumar', 'Singh', 'Al Mansouri',
                          'Smith', 'Johnson', 'Williams', 'Zhang', 'Lee'])
    return f"{first} {last}"

def _random_date():
    d, m, y = random.randint(1, 28), random.randint(1, 12), random.randint(1960, 2005)
    return f"{d:02d}/{m:02d}/{y}"

def _random_digits(n):
    return ''.join(random.choices(string.digits, k=n))

def _draw_text(draw, pos, text, fill=(0, 0, 0), size=16):
    """Draw text using PIL default font."""
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except (IOError, OSError):
        font = ImageFont.load_default()
    draw.text(pos, text, fill=fill, font=font)


def _make_document_base(w=600, h=400, bg_color=(255, 255, 255)):
    """Create a base document image with a border."""
    img = Image.new('RGB', (w, h), bg_color)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(10, 10), (w - 10, h - 10)], outline=(0, 0, 0), width=2)
    return img, draw


def generate_aadhaar(idx):
    bg = random.choice([(255, 255, 255), (245, 245, 240), (255, 250, 245)])
    img, draw = _make_document_base(600, 400, bg)
    draw.rectangle([(20, 20), (580, 70)], fill=(255, 100, 0))
    _draw_text(draw, (30, 25), "Government of India", fill=(255, 255, 255), size=18)
    _draw_text(draw, (30, 48), "Unique Identification Authority of India", fill=(255, 255, 255), size=12)
    _draw_text(draw, (30, 80), "Aadhaar", size=22)
    name = _random_name()
    aadhaar_no = f"{_random_digits(4)} {_random_digits(4)} {_random_digits(4)}"
    _draw_text(draw, (30, 120), f"Name: {name}", size=14)
    _draw_text(draw, (30, 150), f"DOB: {_random_date()}", size=14)
    _draw_text(draw, (30, 180), f"Gender: {random.choice(['Male', 'Female'])}", size=14)
    _draw_text(draw, (30, 220), f"Aadhaar Number:", size=14)
    _draw_text(draw, (30, 245), aadhaar_no, size=20)
    # Photo placeholder
    draw.rectangle([(420, 90), (560, 250)], outline=(100, 100, 100), fill=(200, 200, 200))
    _draw_text(draw, (450, 160), "PHOTO", fill=(150, 150, 150), size=12)
    # QR placeholder
    draw.rectangle([(30, 300), (120, 380)], fill=(50, 50, 50))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=random.randint(70, 95))
    return buf.getvalue()


def generate_emirates_id(idx):
    bg = random.choice([(255, 255, 255), (240, 245, 255)])
    img, draw = _make_document_base(600, 380, bg)
    draw.rectangle([(20, 20), (580, 65)], fill=(0, 100, 0))
    _draw_text(draw, (30, 25), "United Arab Emirates", fill=(255, 255, 255), size=16)
    _draw_text(draw, (30, 45), "Identity Card", fill=(255, 255, 255), size=12)
    name = _random_name()
    id_no = f"784-{_random_digits(4)}-{_random_digits(7)}-{_random_digits(1)}"
    _draw_text(draw, (30, 80), f"Name: {name}", size=14)
    _draw_text(draw, (30, 110), f"ID Number: {id_no}", size=14)
    _draw_text(draw, (30, 140), f"Nationality: {random.choice(['UAE', 'IND', 'PAK', 'PHL'])}", size=14)
    _draw_text(draw, (30, 170), f"Date of Birth: {_random_date()}", size=14)
    _draw_text(draw, (30, 200), f"Expiry Date: {random.randint(1, 28):02d}/{random.randint(1, 12):02d}/{random.randint(2026, 2035)}", size=14)
    draw.rectangle([(430, 75), (560, 220)], outline=(100, 100, 100), fill=(200, 200, 200))
    _draw_text(draw, (460, 140), "PHOTO", fill=(150, 150, 150), size=12)
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=random.randint(70, 95))
    return buf.getvalue()


def generate_passport(idx):
    bg = random.choice([(240, 240, 255), (245, 245, 255)])
    img, draw = _make_document_base(600, 420, bg)
    draw.rectangle([(20, 20), (580, 75)], fill=(0, 0, 128))
    _draw_text(draw, (200, 25), "PASSPORT", fill=(255, 215, 0), size=22)
    _draw_text(draw, (180, 50), "Republic of India", fill=(255, 255, 255), size=14)
    name = _random_name()
    passport_no = f"{random.choice(string.ascii_uppercase)}{_random_digits(7)}"
    _draw_text(draw, (30, 90), f"Type: P", size=12)
    _draw_text(draw, (30, 110), f"Country Code: IND", size=12)
    _draw_text(draw, (30, 135), f"Passport No: {passport_no}", size=14)
    _draw_text(draw, (30, 165), f"Surname: {name.split()[-1].upper()}", size=14)
    _draw_text(draw, (30, 190), f"Given Name: {name.split()[0].upper()}", size=14)
    _draw_text(draw, (30, 220), f"Nationality: INDIAN", size=14)
    _draw_text(draw, (30, 250), f"Date of Birth: {_random_date()}", size=14)
    _draw_text(draw, (30, 280), f"Sex: {random.choice(['M', 'F'])}", size=14)
    _draw_text(draw, (30, 310), f"Place of Birth: {random.choice(['MUMBAI', 'DELHI', 'CHENNAI', 'KOLKATA'])}", size=14)
    draw.rectangle([(430, 85), (565, 250)], outline=(100, 100, 100), fill=(200, 200, 200))
    # MRZ lines
    mrz = f"P<IND{''.join(name.split()).upper():<39}"[:44]
    _draw_text(draw, (30, 360), mrz, size=10)
    _draw_text(draw, (30, 380), f"{passport_no}<{'<' * 30}", size=10)
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=random.randint(70, 95))
    return buf.getvalue()


def generate_driving_license(idx):
    bg = random.choice([(255, 255, 255), (255, 250, 240)])
    img, draw = _make_document_base(600, 380, bg)
    draw.rectangle([(20, 20), (580, 65)], fill=(139, 0, 0))
    _draw_text(draw, (120, 28), "DRIVING LICENCE", fill=(255, 255, 255), size=20)
    name = _random_name()
    dl_no = f"{random.choice(['DL', 'MH', 'KA', 'TN'])}{_random_digits(2)} {_random_digits(11)}"
    _draw_text(draw, (30, 80), f"DL No: {dl_no}", size=14)
    _draw_text(draw, (30, 110), f"Name: {name}", size=14)
    _draw_text(draw, (30, 140), f"S/D/W of: {_random_name()}", size=14)
    _draw_text(draw, (30, 170), f"DOB: {_random_date()}", size=14)
    _draw_text(draw, (30, 200), f"Blood Group: {random.choice(['A+', 'B+', 'O+', 'AB+'])}", size=14)
    _draw_text(draw, (30, 230), f"Address: {random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad'])}", size=14)
    _draw_text(draw, (30, 260), f"Validity (Transport): {_random_date()}", size=14)
    draw.rectangle([(430, 75), (560, 220)], outline=(100, 100, 100), fill=(200, 200, 200))
    _draw_text(draw, (30, 300), "State Motor Vehicles Department", size=11)
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=random.randint(70, 95))
    return buf.getvalue()


def generate_us_drivers_license(idx):
    bg = random.choice([(240, 248, 255), (255, 255, 255)])
    img, draw = _make_document_base(600, 380, bg)
    state = random.choice(['CALIFORNIA', 'NEW YORK', 'TEXAS', 'FLORIDA'])
    draw.rectangle([(20, 20), (580, 65)], fill=(0, 51, 102))
    _draw_text(draw, (30, 25), f"STATE OF {state}", fill=(255, 255, 255), size=16)
    _draw_text(draw, (30, 48), "DRIVER LICENSE", fill=(255, 215, 0), size=14)
    name = _random_name()
    dl_no = f"{random.choice(string.ascii_uppercase)}{_random_digits(7)}"
    _draw_text(draw, (30, 80), f"DL {dl_no}", size=16)
    _draw_text(draw, (30, 110), f"LN {name.split()[-1].upper()}", size=14)
    _draw_text(draw, (30, 135), f"FN {name.split()[0].upper()}", size=14)
    _draw_text(draw, (30, 165), f"DOB {_random_date()}", size=14)
    _draw_text(draw, (30, 195), f"EXP {random.randint(1, 28):02d}/{random.randint(1, 12):02d}/{random.randint(2026, 2035)}", size=14)
    _draw_text(draw, (30, 225), f"SEX {random.choice(['M', 'F'])}  HGT {random.randint(5, 6)}-{random.randint(0, 11):02d}", size=14)
    _draw_text(draw, (30, 255), f"EYES {random.choice(['BLU', 'BRN', 'GRN', 'HAZ'])}", size=14)
    draw.rectangle([(430, 75), (560, 230)], outline=(100, 100, 100), fill=(200, 200, 200))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=random.randint(70, 95))
    return buf.getvalue()


# Augmentation
def augment_image(image_bytes, count=3):
    """Create augmented versions of an image."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        return []
    h, w = image.shape[:2]
    augmented = []
    for _ in range(count):
        aug = image.copy()
        # Rotation
        angle = random.uniform(-5, 5)
        M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        aug = cv2.warpAffine(aug, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        # Brightness
        aug = cv2.convertScaleAbs(aug, alpha=random.uniform(0.85, 1.15), beta=random.randint(-15, 15))
        # Gaussian noise
        if random.random() > 0.5:
            noise = np.random.normal(0, 3, aug.shape).astype(np.int16)
            aug = np.clip(aug.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        # JPEG quality variation
        quality = random.randint(60, 95)
        _, buf = cv2.imencode('.jpg', aug, [cv2.IMWRITE_JPEG_QUALITY, quality])
        augmented.append(buf.tobytes())
    return augmented


GENERATORS = {
    'aadhaar': generate_aadhaar,
    'emirates_id': generate_emirates_id,
    'passport': generate_passport,
    'driving_license': generate_driving_license,
    'us_drivers_license': generate_us_drivers_license,
}


def generate_training_set(samples_per_class=40, augment_count=3):
    """Generate a full synthetic training set with augmentation."""
    data = []
    for doc_type, gen_fn in GENERATORS.items():
        for i in range(samples_per_class):
            img_bytes = gen_fn(i)
            data.append((img_bytes, doc_type))
            for aug_bytes in augment_image(img_bytes, augment_count):
                data.append((aug_bytes, doc_type))
    random.shuffle(data)
    logger.info(f"Generated {len(data)} training samples ({samples_per_class} base + {augment_count} augmented per class)")
    return data


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.chdir(Path(__file__).parent.parent)

    logger.info("=" * 60)
    logger.info("Enhanced ML Classifier Training")
    logger.info("=" * 60)

    # 1. Generate training data
    training_data = generate_training_set(samples_per_class=50, augment_count=4)
    logger.info(f"Total samples: {len(training_data)}")

    # Count per class
    from collections import Counter
    counts = Counter(label for _, label in training_data)
    for label, count in sorted(counts.items()):
        logger.info(f"  {label}: {count} samples")

    # 2. Train main DocumentClassifier
    logger.info("\n--- Training DocumentClassifier (image features) ---")
    from app.ai.document_classifier import DocumentClassifier
    classifier = DocumentClassifier()
    result = classifier.train_model(training_data)
    if result['success']:
        logger.info(f"DocumentClassifier trained: train_acc={result['train_accuracy']:.3f}, test_acc={result['test_accuracy']:.3f}")
    else:
        logger.error(f"DocumentClassifier training failed: {result.get('error')}")

    # 3. Train MLDocumentClassifier (text + image ensemble)
    logger.info("\n--- Training MLDocumentClassifier (text+image ensemble) ---")
    from app.ml_document_classifier import MLDocumentClassifier, MLTrainingDataGenerator
    ml_gen = MLTrainingDataGenerator()
    ml_data = ml_gen.generate_synthetic_training_data(900)
    ml_classifier = MLDocumentClassifier()
    ml_result = ml_classifier.train_classifier(ml_data)
    if ml_result.get('success'):
        logger.info(f"MLDocumentClassifier trained: accuracy={ml_result['accuracy']:.3f}, time={ml_result['training_time']:.2f}s")
    else:
        logger.error(f"MLDocumentClassifier training failed: {ml_result.get('error')}")

    # 4. Verify saved models
    logger.info("\n--- Verifying saved models ---")
    model_files = ['models/document_classifier.pkl', 'models/feature_scaler.pkl', 'models/ml_classifier.pkl']
    for mf in model_files:
        if os.path.exists(mf):
            size_kb = os.path.getsize(mf) / 1024
            logger.info(f"  {mf}: {size_kb:.1f} KB")
        else:
            logger.warning(f"  {mf}: NOT FOUND")

    # 5. Quick inference test
    logger.info("\n--- Quick inference test ---")
    test_classifier = DocumentClassifier()
    for doc_type, gen_fn in GENERATORS.items():
        test_img = gen_fn(999)
        result = test_classifier.classify_document(test_img)
        predicted = result.get('document_type', 'unknown')
        conf = result.get('confidence', 0)
        match = "OK" if predicted == doc_type else f"MISMATCH (got {predicted})"
        logger.info(f"  {doc_type}: predicted={predicted} conf={conf:.2f} [{match}]")

    logger.info("\nTraining complete!")


if __name__ == '__main__':
    main()
