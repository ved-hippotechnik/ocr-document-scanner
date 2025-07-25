#!/usr/bin/env python3
"""
Training script for the AI document classifier
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Tuple

# Add the parent directory to sys.path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai.document_classifier import DocumentClassifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_training_data(data_dir: str) -> List[Tuple[bytes, str]]:
    """
    Load training data from directory structure
    
    Expected structure:
    data_dir/
    ├── aadhaar/
    │   ├── image1.jpg
    │   ├── image2.jpg
    │   └── ...
    ├── emirates_id/
    │   ├── image1.jpg
    │   └── ...
    └── ...
    """
    training_data = []
    data_path = Path(data_dir)
    
    if not data_path.exists():
        logger.error(f"Training data directory not found: {data_dir}")
        return training_data
    
    for doc_type_dir in data_path.iterdir():
        if not doc_type_dir.is_dir():
            continue
            
        document_type = doc_type_dir.name
        logger.info(f"Loading {document_type} samples...")
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        
        for image_file in doc_type_dir.iterdir():
            if image_file.suffix.lower() in image_extensions:
                try:
                    with open(image_file, 'rb') as f:
                        image_data = f.read()
                    
                    training_data.append((image_data, document_type))
                    
                except Exception as e:
                    logger.error(f"Error loading {image_file}: {e}")
        
        logger.info(f"Loaded {len([t for t in training_data if t[1] == document_type])} {document_type} samples")
    
    logger.info(f"Total training samples: {len(training_data)}")
    return training_data

def create_synthetic_data() -> List[Tuple[bytes, str]]:
    """
    Create synthetic training data for testing
    This is a placeholder - in production, use real document images
    """
    import numpy as np
    from PIL import Image
    import io
    
    training_data = []
    document_types = ['aadhaar', 'emirates_id', 'passport', 'driving_license', 'us_drivers_license']
    
    for doc_type in document_types:
        for i in range(20):  # 20 samples per type
            # Create a random image
            img_array = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)
            
            # Add some basic patterns to differentiate document types
            if doc_type == 'aadhaar':
                img_array[50:100, 50:200] = [255, 0, 0]  # Red rectangle
            elif doc_type == 'emirates_id':
                img_array[100:150, 100:250] = [0, 255, 0]  # Green rectangle
            elif doc_type == 'passport':
                img_array[200:250, 200:350] = [0, 0, 255]  # Blue rectangle
            elif doc_type == 'driving_license':
                img_array[150:200, 150:300] = [255, 255, 0]  # Yellow rectangle
            elif doc_type == 'us_drivers_license':
                img_array[300:350, 300:450] = [255, 0, 255]  # Magenta rectangle
            
            # Convert to PIL Image
            img = Image.fromarray(img_array, 'RGB')
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes = img_bytes.getvalue()
            
            training_data.append((img_bytes, doc_type))
    
    logger.info(f"Created {len(training_data)} synthetic training samples")
    return training_data

def main():
    """Main training function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train AI document classifier')
    parser.add_argument('--data-dir', type=str, help='Directory containing training data')
    parser.add_argument('--synthetic', action='store_true', help='Use synthetic data for testing')
    parser.add_argument('--model-path', type=str, default='models/document_classifier.pkl', 
                       help='Path to save trained model')
    
    args = parser.parse_args()
    
    # Load training data
    if args.synthetic:
        logger.info("Using synthetic training data")
        training_data = create_synthetic_data()
    elif args.data_dir:
        logger.info(f"Loading training data from: {args.data_dir}")
        training_data = load_training_data(args.data_dir)
    else:
        logger.error("Either --data-dir or --synthetic must be specified")
        sys.exit(1)
    
    if len(training_data) < 10:
        logger.error("Insufficient training data. Need at least 10 samples.")
        sys.exit(1)
    
    # Initialize classifier
    classifier = DocumentClassifier(model_path=args.model_path)
    
    # Train the model
    logger.info("Starting model training...")
    result = classifier.train_model(training_data)
    
    if result['success']:
        logger.info("Training completed successfully!")
        logger.info(f"Training accuracy: {result['train_accuracy']:.3f}")
        logger.info(f"Test accuracy: {result['test_accuracy']:.3f}")
        logger.info(f"Model saved to: {args.model_path}")
    else:
        logger.error(f"Training failed: {result['error']}")
        sys.exit(1)

if __name__ == '__main__':
    main()