"""
Training data pipeline for the AI document classifier.

Collects labelled samples from scan history (database) and uses
the processor registry's detect() as a ground-truth labelling oracle
for unlabelled images.
"""

import logging
import os
import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TrainingDataGenerator:
    """Generates and manages training data for the document classifier."""

    def __init__(self, upload_dir: str = 'uploads'):
        self.upload_dir = upload_dir

    # ------------------------------------------------------------------
    # Ground-truth labelling via processor registry
    # ------------------------------------------------------------------

    def label_image_with_processors(self, image_data: bytes) -> Optional[str]:
        """Use processor registry to label a single image."""
        try:
            from ..processors import processor_registry
            import pytesseract

            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is None:
                return None

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            text = pytesseract.image_to_string(gray)

            _, processor = processor_registry.detect_document_type(text, image)
            if processor:
                return processor.document_type
            return None
        except Exception as e:
            logger.warning(f"Processor labelling failed: {e}")
            return None

    # ------------------------------------------------------------------
    # Collect from database scan history
    # ------------------------------------------------------------------

    def collect_from_scan_history(self, min_confidence: str = 'medium') -> List[Tuple[bytes, str]]:
        """
        Gather labelled samples from the ScanHistory table.
        Each row has document_type and optionally a stored image path.
        """
        try:
            from ..database import db, ScanHistory
            confidence_levels = {'high': 3, 'medium': 2, 'low': 1}
            min_level = confidence_levels.get(min_confidence, 2)

            records = ScanHistory.query.filter(
                ScanHistory.document_type.isnot(None),
                ScanHistory.document_type != 'unknown',
                ScanHistory.document_type != 'other',
            ).all()

            samples: List[Tuple[bytes, str]] = []
            for record in records:
                # Skip low-confidence records
                record_level = confidence_levels.get(
                    getattr(record, 'confidence', 'medium'), 2
                )
                if record_level < min_level:
                    continue

                image_path = getattr(record, 'image_path', None)
                if image_path and os.path.exists(image_path):
                    with open(image_path, 'rb') as f:
                        samples.append((f.read(), record.document_type))

            logger.info(f"Collected {len(samples)} samples from scan history")
            return samples

        except Exception as e:
            logger.warning(f"Could not collect from scan history: {e}")
            return []

    # ------------------------------------------------------------------
    # Simple image augmentation
    # ------------------------------------------------------------------

    @staticmethod
    def augment_image(image_data: bytes, num_augmented: int = 3) -> List[bytes]:
        """
        Generate augmented copies of an image via rotation, brightness and noise.
        Returns a list of raw JPEG bytes.
        """
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            return []

        augmented: List[bytes] = []
        h, w = image.shape[:2]

        for i in range(num_augmented):
            aug = image.copy()

            # Slight rotation (-5 to +5 degrees)
            angle = np.random.uniform(-5, 5)
            M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
            aug = cv2.warpAffine(aug, M, (w, h), borderMode=cv2.BORDER_REPLICATE)

            # Brightness jitter
            beta = np.random.randint(-20, 20)
            aug = cv2.convertScaleAbs(aug, alpha=1.0, beta=beta)

            # Optional Gaussian noise
            if i % 2 == 0:
                noise = np.random.normal(0, 5, aug.shape).astype(np.uint8)
                aug = cv2.add(aug, noise)

            _, buf = cv2.imencode('.jpg', aug)
            augmented.append(buf.tobytes())

        return augmented

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------

    def build_training_set(self, augment: bool = True) -> List[Tuple[bytes, str]]:
        """
        Build a complete training set by combining scan history data
        and optional augmentation.
        """
        samples = self.collect_from_scan_history()

        if augment and samples:
            augmented_samples = []
            for image_data, label in samples:
                augmented_samples.append((image_data, label))
                for aug_image in self.augment_image(image_data, num_augmented=2):
                    augmented_samples.append((aug_image, label))
            logger.info(
                f"Augmented {len(samples)} samples to {len(augmented_samples)}"
            )
            return augmented_samples

        return samples

    def get_training_stats(self) -> Dict:
        """Return statistics about available training data."""
        samples = self.collect_from_scan_history()
        label_counts: Dict[str, int] = {}
        for _, label in samples:
            label_counts[label] = label_counts.get(label, 0) + 1

        return {
            'total_samples': len(samples),
            'label_distribution': label_counts,
            'unique_labels': len(label_counts),
            'timestamp': datetime.now().isoformat(),
        }
