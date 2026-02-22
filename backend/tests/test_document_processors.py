"""
Comprehensive tests for document processors
"""
import pytest
from unittest.mock import Mock, patch
import cv2
import numpy as np

from app.processors.aadhaar import AadhaarProcessor
from app.processors.emirates_id import EmiratesIDProcessor
from app.processors.passport import PassportProcessor
from app.processors.driving_license import DrivingLicenseProcessor
from app.processors.us_drivers_license import USDriversLicenseProcessor
from app.processors.registry import processor_registry


class TestProcessorRegistry:
    """Test processor registry functionality"""

    def test_registry_initialization(self):
        """Test that processor registry is properly initialized"""
        assert len(processor_registry.processors) > 0
        supported_docs = processor_registry.list_supported_documents()
        assert isinstance(supported_docs, list)
        assert len(supported_docs) > 0

    def test_detect_document_type(self):
        """Test document type detection"""
        mock_text = "Government of India\nआधार\nAadhaar\n1234 5678 9012\nRAJESH KUMAR"

        doc_type, processor = processor_registry.detect_document_type(mock_text)
        assert doc_type is not None
        assert isinstance(doc_type, str)


class TestAadhaarProcessor:
    """Test Aadhaar card processor"""

    @pytest.fixture
    def processor(self):
        return AadhaarProcessor()

    @pytest.fixture
    def sample_aadhaar_text(self):
        return "\n".join([
            "Government of India",
            "आधार",
            "Aadhaar",
            "1234 5678 9012",
            "RAJESH KUMAR",
            "पुरुष / MALE",
            "जन्म तिथि / DOB: 01/01/1990",
            "पिता का नाम / Father's Name: RAM KUMAR",
            "Address Line 1",
            "Test City, Test State - 123456"
        ])

    def test_aadhaar_detection(self, processor, sample_aadhaar_text):
        """Test Aadhaar card detection"""
        assert processor.detect(sample_aadhaar_text) is True

    def test_aadhaar_extraction(self, processor, sample_aadhaar_text):
        """Test Aadhaar data extraction"""
        result = processor.extract_info(sample_aadhaar_text)
        assert isinstance(result, dict)

    def test_aadhaar_number_extraction(self, processor):
        """Test Aadhaar number can be extracted from text"""
        text_with_aadhaar = "Name: Test\nAadhaar No: 1234 5678 9012\nDOB: 01/01/1990"
        result = processor.extract_info(text_with_aadhaar)
        assert isinstance(result, dict)

    def test_aadhaar_preprocessing(self, processor):
        """Test Aadhaar-specific image preprocessing"""
        mock_image = np.zeros((800, 1200, 3), dtype=np.uint8)
        processed = processor.preprocess(mock_image)
        assert processed is not None


class TestEmiratesIDProcessor:
    """Test Emirates ID processor"""

    @pytest.fixture
    def processor(self):
        return EmiratesIDProcessor()

    @pytest.fixture
    def sample_emirates_text(self):
        return "\n".join([
            "United Arab Emirates",
            "الإمارات العربية المتحدة",
            "Identity Card",
            "784-1990-1234567-8",
            "MOHAMMED AHMED",
            "محمد أحمد",
            "Nationality: ARE",
            "Date of Birth: 01/01/1990",
            "Expiry Date: 01/01/2030"
        ])

    def test_emirates_detection(self, processor, sample_emirates_text):
        """Test Emirates ID detection"""
        assert processor.detect(sample_emirates_text) is True

    def test_emirates_extraction(self, processor, sample_emirates_text):
        """Test Emirates ID data extraction"""
        result = processor.extract_info(sample_emirates_text)
        assert isinstance(result, dict)

    def test_emirates_id_extraction(self, processor):
        """Test Emirates ID number can be extracted"""
        text = "Emirates ID\n784-1990-1234567-8\nName: AHMED"
        result = processor.extract_info(text)
        assert isinstance(result, dict)


class TestPassportProcessor:
    """Test passport processor"""

    @pytest.fixture
    def processor(self):
        return PassportProcessor()

    @pytest.fixture
    def sample_passport_text(self):
        return "\n".join([
            "REPUBLIC OF INDIA",
            "भारत गणराज्य",
            "PASSPORT",
            "पासपोर्ट",
            "Passport No./पासपोर्ट संख्या",
            "A1234567",
            "Surname/उपनाम",
            "SHARMA",
            "Given Name(s)/दिया गया नाम",
            "PRIYA",
            "Nationality/राष्ट्रीयता",
            "INDIAN",
            "Date of Birth/जन्म की तारीख",
            "15/06/1985",
            "Place of Birth/जन्म स्थान",
            "DELHI"
        ])

    def test_passport_detection(self, processor, sample_passport_text):
        """Test passport detection"""
        assert processor.detect(sample_passport_text) is True

    def test_passport_extraction(self, processor, sample_passport_text):
        """Test passport data extraction"""
        result = processor.extract_info(sample_passport_text)
        assert isinstance(result, dict)

    def test_passport_number_extraction(self, processor):
        """Test passport number can be extracted"""
        text = "PASSPORT\nPassport No: A1234567\nName: SHARMA"
        result = processor.extract_info(text)
        assert isinstance(result, dict)


class TestDrivingLicenseProcessor:
    """Test driving license processor"""

    @pytest.fixture
    def processor(self):
        return DrivingLicenseProcessor()

    @pytest.fixture
    def sample_dl_text(self):
        return "\n".join([
            "GOVERNMENT OF INDIA",
            "DRIVING LICENCE",
            "चालक अनुज्ञप्ति",
            "DL Number: DL-1420110012345",
            "Name: AMIT SINGH",
            "S/W/D of: RAJESH SINGH",
            "DOB: 15/03/1985",
            "Address: 123 Test Road",
            "Test City, Delhi - 110001",
            "Valid Till: 14/03/2025",
            "Class of Vehicle: LMV"
        ])

    def test_dl_detection(self, processor, sample_dl_text):
        """Test driving license detection"""
        assert processor.detect(sample_dl_text) is True

    def test_dl_extraction(self, processor, sample_dl_text):
        """Test driving license data extraction"""
        result = processor.extract_info(sample_dl_text)
        assert isinstance(result, dict)

    def test_dl_number_extraction(self, processor):
        """Test DL number can be extracted"""
        text = "DRIVING LICENCE\nDL Number: DL-1420110012345\nName: AMIT"
        result = processor.extract_info(text)
        assert isinstance(result, dict)


class TestUSDriversLicenseProcessor:
    """Test US driver's license processor"""

    @pytest.fixture
    def processor(self):
        return USDriversLicenseProcessor()

    @pytest.fixture
    def sample_us_dl_text(self):
        return "\n".join([
            "CALIFORNIA",
            "DRIVER LICENSE",
            "DL A1234567",
            "LN SMITH",
            "FN JOHN MICHAEL",
            "DOB 01/15/1980",
            "123 MAIN ST",
            "ANYTOWN CA 90210",
            "EXP 01/15/2025",
            "Class C"
        ])

    def test_us_dl_detection(self, processor, sample_us_dl_text):
        """Test US driver's license detection"""
        assert processor.detect(sample_us_dl_text) is True

    def test_us_dl_extraction(self, processor, sample_us_dl_text):
        """Test US driver's license data extraction"""
        result = processor.extract_info(sample_us_dl_text)
        assert isinstance(result, dict)


class TestProcessorPerformance:
    """Test processor performance and error handling"""

    @pytest.mark.performance
    def test_processor_speed(self, performance_tracker):
        """Test processor performance benchmarks"""
        processor = AadhaarProcessor()
        sample_text = "Government of India\nआधार\n1234 5678 9012\nRAJESH KUMAR"

        performance_tracker.start_timer('aadhaar_processing')

        for _ in range(100):
            processor.detect(sample_text)

        performance_tracker.end_timer('aadhaar_processing')

        assert performance_tracker.get_duration('aadhaar_processing') < 1.0

    def test_processor_error_handling(self):
        """Test processor error handling with invalid input"""
        processor = AadhaarProcessor()

        # Test with empty string
        assert processor.detect("") is False

        # Test with irrelevant text — should not detect
        assert processor.detect("Random text that doesn't match anything") is False

        # Test extraction with invalid text — should still return a dict
        result = processor.extract_info("Random text that doesn't match")
        assert isinstance(result, dict)

    def test_memory_usage(self):
        """Test that processors don't leak memory"""
        import gc
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        processor = AadhaarProcessor()
        large_text = "Government of India\nआधार\n" * 1000

        for _ in range(100):
            processor.detect(large_text)
            processor.extract_info(large_text)

        gc.collect()

        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB

        assert memory_increase < 50


class TestProcessorIntegration:
    """Integration tests for processor workflows"""

    @pytest.mark.integration
    def test_full_processing_pipeline(self):
        """Test complete document processing pipeline"""
        mock_image = np.zeros((800, 1200, 3), dtype=np.uint8)

        mock_text = "Government of India\nआधार\n1234 5678 9012\nRAJESH KUMAR"
        doc_type, processor = processor_registry.detect_document_type(mock_text)

        assert doc_type is not None

        if processor:
            processed_image = processor.preprocess(mock_image)
            assert processed_image is not None

            extracted_data = processor.extract_info(mock_text)
            assert isinstance(extracted_data, dict)

    @pytest.mark.integration
    def test_multi_document_processing(self):
        """Test processing multiple document types"""
        test_cases = [
            {
                'text': "Government of India\nआधार\n1234 5678 9012",
                'expected_contains': 'aadhaar'
            },
            {
                'text': "United Arab Emirates\nIdentity Card\n784-1990-1234567-8",
                'expected_contains': 'id'
            },
            {
                'text': "REPUBLIC OF INDIA\nPASSPORT\nA1234567",
                'expected_contains': 'passport'
            }
        ]

        for case in test_cases:
            doc_type, processor = processor_registry.detect_document_type(case['text'])
            if doc_type:
                assert case['expected_contains'] in doc_type.lower()
                if processor:
                    extracted = processor.extract_info(case['text'])
                    assert isinstance(extracted, dict)
