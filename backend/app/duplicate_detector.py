"""
Duplicate document detection using perceptual hashing (pHash).

Compares incoming document images against previously scanned documents
to flag potential duplicates before processing.
"""
import io
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

try:
    import imagehash
    from PIL import Image
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False
    logger.warning("imagehash not installed — duplicate detection disabled")


class DuplicateDetector:
    """Detect duplicate document uploads using perceptual image hashing."""

    def __init__(self, threshold: int = 5):
        """
        Args:
            threshold: Maximum Hamming distance to consider two images
                       as duplicates.  Lower = stricter matching.
        """
        self.threshold = threshold
        # In-memory store: {hash_str: {scan_id, timestamp, document_type}}
        self._hash_store: Dict[str, Dict] = {}

    @property
    def available(self) -> bool:
        return IMAGEHASH_AVAILABLE

    def compute_hash(self, image_data: bytes) -> Optional[str]:
        """Compute a perceptual hash for raw image bytes."""
        if not IMAGEHASH_AVAILABLE:
            return None
        try:
            img = Image.open(io.BytesIO(image_data))
            phash = imagehash.phash(img)
            return str(phash)
        except Exception as exc:
            logger.warning("Failed to compute image hash: %s", exc)
            return None

    def check_duplicate(self, image_data: bytes) -> Optional[Dict]:
        """Check whether *image_data* matches a previously stored hash.

        Returns metadata of the matching scan if a duplicate is found,
        otherwise ``None``.
        """
        if not IMAGEHASH_AVAILABLE:
            return None

        current_hash = self.compute_hash(image_data)
        if current_hash is None:
            return None

        current = imagehash.hex_to_hash(current_hash)

        for stored_hex, meta in self._hash_store.items():
            stored = imagehash.hex_to_hash(stored_hex)
            distance = current - stored
            if distance <= self.threshold:
                return {
                    'is_duplicate': True,
                    'distance': distance,
                    'matching_scan': meta,
                }

        return None

    def register(self, image_data: bytes, scan_id: str,
                 document_type: str = '', timestamp: str = '') -> Optional[str]:
        """Store the hash of a newly processed document.

        Returns the hex hash string, or ``None`` on failure.
        """
        h = self.compute_hash(image_data)
        if h is None:
            return None
        self._hash_store[h] = {
            'scan_id': scan_id,
            'document_type': document_type,
            'timestamp': timestamp,
        }
        return h

    def get_store_size(self) -> int:
        return len(self._hash_store)

    def clear(self) -> None:
        self._hash_store.clear()
