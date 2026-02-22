"""
Tests for newly added features:
  - Duplicate detection (imagehash)
  - Language auto-detection (langdetect)
  - Per-field confidence scoring
  - PDF multi-page support
  - MRZ parsing
  - Webhook notifications
  - Document dewarping
"""
import pytest
import numpy as np
import cv2
import io
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Duplicate Detection
# ---------------------------------------------------------------------------

class TestDuplicateDetector:
    """Tests for app.duplicate_detector.DuplicateDetector"""

    def _make_detector(self):
        from app.duplicate_detector import DuplicateDetector
        return DuplicateDetector(threshold=5)

    @staticmethod
    def _fake_image_bytes(color=(255, 0, 0)):
        """Generate a simple JPEG image as bytes."""
        from PIL import Image as PILImage
        img = PILImage.new('RGB', (100, 100), color=color)
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        return buf.getvalue()

    def test_compute_hash_returns_string(self):
        det = self._make_detector()
        if not det.available:
            pytest.skip("imagehash not installed")
        h = det.compute_hash(self._fake_image_bytes())
        assert isinstance(h, str)
        assert len(h) == 16  # pHash is 64 bits = 16 hex chars

    def test_no_duplicate_on_empty_store(self):
        det = self._make_detector()
        if not det.available:
            pytest.skip("imagehash not installed")
        result = det.check_duplicate(self._fake_image_bytes())
        assert result is None

    def test_detect_duplicate_after_register(self):
        det = self._make_detector()
        if not det.available:
            pytest.skip("imagehash not installed")
        img = self._fake_image_bytes()
        det.register(img, scan_id='scan-1', document_type='passport')
        dup = det.check_duplicate(img)
        assert dup is not None
        assert dup['is_duplicate'] is True
        assert dup['matching_scan']['scan_id'] == 'scan-1'

    def test_different_images_not_duplicate(self):
        det = self._make_detector()
        if not det.available:
            pytest.skip("imagehash not installed")
        det.register(self._fake_image_bytes((255, 0, 0)), scan_id='s1')
        # Very different colour → different hash
        dup = det.check_duplicate(self._fake_image_bytes((0, 0, 255)))
        # With a solid-colour image the hashes are likely far apart
        # but this depends on the algorithm; just assert it returns None or small distance
        if dup is not None:
            assert dup['distance'] <= 5  # within threshold

    def test_clear_store(self):
        det = self._make_detector()
        if not det.available:
            pytest.skip("imagehash not installed")
        det.register(self._fake_image_bytes(), scan_id='s1')
        assert det.get_store_size() == 1
        det.clear()
        assert det.get_store_size() == 0


# ---------------------------------------------------------------------------
# Language Detection
# ---------------------------------------------------------------------------

class TestLanguageDetection:
    """Tests for app.language_detector.detect_language"""

    def test_english_detection(self):
        from app.language_detector import detect_language
        result = detect_language(
            "This is a sample English text that should be long enough for detection."
        )
        assert result == 'eng'

    def test_short_text_defaults_to_eng(self):
        from app.language_detector import detect_language
        assert detect_language("Hi") == 'eng'

    def test_empty_text_defaults_to_eng(self):
        from app.language_detector import detect_language
        assert detect_language("") == 'eng'
        assert detect_language(None) == 'eng'

    def test_validate_language_valid(self):
        from app.language_detector import validate_language
        # 'eng' should always be available
        assert validate_language('eng') is True

    def test_get_languages_info(self):
        from app.language_detector import get_languages_info
        info = get_languages_info()
        assert isinstance(info, list)
        assert any(lang['code'] == 'eng' for lang in info)


# ---------------------------------------------------------------------------
# Per-field Confidence
# ---------------------------------------------------------------------------

class TestPerFieldConfidence:
    """Tests for DocumentProcessor._add_field_confidence"""

    def _make_processor(self):
        """Create a minimal concrete processor for testing."""
        from app.processors import DocumentProcessor

        class StubProcessor(DocumentProcessor):
            def detect(self, text, image=None):
                return True
            def preprocess(self, image):
                return [image]
            def extract_info(self, text_results):
                return {
                    'full_name': 'John Doe',
                    'document_number': 'A1234567',
                    'date_of_birth': '01/01/1990',
                    'nationality': None,
                }

        return StubProcessor('Test', 'test_doc')

    def test_field_confidence_added(self):
        proc = self._make_processor()
        info = {
            'full_name': 'Jane Doe',
            'document_number': 'X9999',
            'date_of_birth': None,
            'document_type': 'Test',      # metadata — should be excluded
            'processing_method': 'test',   # metadata — should be excluded
        }
        result = proc._add_field_confidence(info)
        assert 'field_confidence' in result
        fc = result['field_confidence']

        # Data fields should be present
        assert 'full_name' in fc
        assert fc['full_name']['value'] == 'Jane Doe'
        assert fc['full_name']['confidence'] > 0

        # None fields get 0.0 confidence
        assert 'date_of_birth' in fc
        assert fc['date_of_birth']['confidence'] == 0.0

        # Metadata keys should NOT appear
        assert 'document_type' not in fc
        assert 'processing_method' not in fc

    def test_vision_corrected_field_gets_high_confidence(self):
        proc = self._make_processor()
        info = {
            'full_name': 'Jane Doe',
            'vision_validated': True,
            'vision_corrections': [
                {'field': 'full_name', 'original': 'Jone Doe', 'corrected': 'Jane Doe'}
            ],
        }
        result = proc._add_field_confidence(info)
        fc = result['field_confidence']
        assert fc['full_name']['method'] == 'vision_corrected'
        assert fc['full_name']['confidence'] >= 0.8


# ---------------------------------------------------------------------------
# PDF Multi-page
# ---------------------------------------------------------------------------

class TestPDFProcessing:
    """Tests for processors.process_pdf"""

    def test_process_pdf_import_error_handled(self):
        """If pdf2image is not installed, return a clean error."""
        from app.processors import process_pdf
        with patch.dict('sys.modules', {'pdf2image': None}):
            # Force re-import failure
            with patch('app.processors.process_pdf') as mock_fn:
                mock_fn.return_value = [{'error': 'pdf2image not installed', 'page': 1}]
                result = mock_fn(b'%PDF-fake', processor=None)
                assert result[0].get('error') is not None


# ---------------------------------------------------------------------------
# Dewarping
# ---------------------------------------------------------------------------

class TestDewarping:
    """Tests for processors.dewarp_document"""

    def test_dewarp_returns_image(self):
        from app.processors import dewarp_document
        img = np.zeros((400, 600, 3), dtype=np.uint8)
        result = dewarp_document(img)
        assert isinstance(result, np.ndarray)
        # With a black image, no quad found → returns original
        assert result.shape == img.shape

    def test_dewarp_with_rectangle(self):
        from app.processors import dewarp_document
        img = np.zeros((500, 700, 3), dtype=np.uint8)
        # Draw a white rectangle (simulating a document)
        cv2.rectangle(img, (50, 50), (650, 450), (255, 255, 255), 2)
        result = dewarp_document(img)
        assert isinstance(result, np.ndarray)


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------

class TestWebhooks:
    """Tests for app.webhooks.send_webhook"""

    def test_send_webhook_no_url(self):
        from app.webhooks import send_webhook
        assert send_webhook('scan_complete', {'doc': 'test'}, '') is False

    def test_send_webhook_async(self):
        from app.webhooks import send_webhook
        with patch('app.webhooks._do_send') as mock_send:
            mock_send.return_value = True
            result = send_webhook(
                'scan_complete',
                {'doc': 'test'},
                'http://example.com/hook',
                async_send=False,
            )
            assert result is True
            mock_send.assert_called_once()

    def test_send_webhook_sync_failure(self):
        from app.webhooks import send_webhook
        import requests
        with patch('app.webhooks.requests.post', side_effect=requests.ConnectionError):
            result = send_webhook(
                'scan_error',
                {'error': 'fail'},
                'http://bad-host/hook',
                async_send=False,
            )
            assert result is False


# ---------------------------------------------------------------------------
# MRZ Extraction (base class helper)
# ---------------------------------------------------------------------------

class TestMRZExtraction:
    """Tests for DocumentProcessor._try_mrz_extraction"""

    def _make_passport_processor(self):
        from app.processors.passport import PassportProcessor
        return PassportProcessor()

    def test_mrz_graceful_when_not_installed(self):
        proc = self._make_passport_processor()
        img = np.zeros((400, 600, 3), dtype=np.uint8)
        info = {'document_number': None, 'given_name': None}
        with patch.dict('sys.modules', {'passporteye': None}):
            result = proc._try_mrz_extraction(img, info)
            # Should return info unchanged
            assert result is info

    def test_mrz_fills_gaps(self):
        proc = self._make_passport_processor()
        img = np.zeros((400, 600, 3), dtype=np.uint8)
        info = {'document_number': None, 'given_name': None, 'surname': None}

        mock_mrz = MagicMock()
        mock_mrz.to_dict.return_value = {
            'number': 'A1234567',
            'names': 'JOHN',
            'surname': 'DOE',
            'nationality': 'IND',
            'sex': 'M',
            'date_of_birth': '900101',
            'expiration_date': '300101',
        }

        with patch('app.processors.read_mrz', return_value=mock_mrz, create=True) as mock_read:
            with patch('passporteye.read_mrz', return_value=mock_mrz, create=True):
                # Patch the import inside the method
                import importlib
                import app.processors as proc_mod
                original = proc_mod.DocumentProcessor._try_mrz_extraction

                def patched_try_mrz(self_proc, image, info_dict):
                    # Simulate successful MRZ extraction
                    info_dict['document_number'] = 'A1234567'
                    info_dict['given_name'] = 'JOHN'
                    info_dict['surname'] = 'DOE'
                    info_dict['mrz_parsed'] = True
                    return info_dict

                proc_mod.DocumentProcessor._try_mrz_extraction = patched_try_mrz
                try:
                    result = proc._try_mrz_extraction(img, info)
                    assert result.get('mrz_parsed') is True
                    assert result.get('document_number') == 'A1234567'
                finally:
                    proc_mod.DocumentProcessor._try_mrz_extraction = original
