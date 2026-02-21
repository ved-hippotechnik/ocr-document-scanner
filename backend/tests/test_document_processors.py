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
    
    def test_get_processor_by_type(self):
        """Test retrieving processor by document type"""
        processor = processor_registry.get_processor('aadhaar_card')
        assert processor is not None
        assert isinstance(processor, AadhaarProcessor)
    
    def test_classify_document(self):
        """Test document classification"""
        # Mock OCR results for Aadhaar card
        mock_text = "Government of India\nआधार\nAadhaar\n1234 5678 9012\nRAJESH KUMAR"
        
        result = processor_registry.classify_document(mock_text)
        assert result is not None
        assert 'document_type' in result
        assert 'confidence' in result
        assert result['confidence'] > 0


class TestAadhaarProcessor:
    """Test Aadhaar card processor"""
    
    @pytest.fixture
    def processor(self):
        return AadhaarProcessor()
    
    @pytest.fixture
    def sample_aadhaar_text(self):
        return [
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
        ]
    
    def test_aadhaar_detection(self, processor, sample_aadhaar_text):
        """Test Aadhaar card detection"""
        assert processor.detect(sample_aadhaar_text) is True
    
    def test_aadhaar_extraction(self, processor, sample_aadhaar_text, aadhaar_test_data):
        """Test Aadhaar data extraction"""
        with patch.object(processor, '_extract_aadhaar_number') as mock_number, \
             patch.object(processor, '_extract_name') as mock_name, \
             patch.object(processor, '_extract_dob') as mock_dob, \
             patch.object(processor, '_extract_gender') as mock_gender:
            
            mock_number.return_value = aadhaar_test_data['aadhaar_number']
            mock_name.return_value = aadhaar_test_data['name']
            mock_dob.return_value = aadhaar_test_data['dob']
            mock_gender.return_value = aadhaar_test_data['gender']
            
            result = processor.extract_info(sample_aadhaar_text)
            
            assert result['aadhaar_number'] == aadhaar_test_data['aadhaar_number']
            assert result['name'] == aadhaar_test_data['name']
            assert result['dob'] == aadhaar_test_data['dob']
            assert result['gender'] == aadhaar_test_data['gender']
    
    def test_aadhaar_number_validation(self, processor):
        """Test Aadhaar number validation"""
        valid_numbers = [
            "1234 5678 9012",
            "1234-5678-9012",
            "123456789012"
        ]
        
        invalid_numbers = [
            "1234 5678",  # Too short
            "1234 5678 9012 3456",  # Too long
            "abcd efgh ijkl",  # Non-numeric
            ""  # Empty
        ]
        
        for number in valid_numbers:
            assert processor._validate_aadhaar_number(number) is True
        
        for number in invalid_numbers:
            assert processor._validate_aadhaar_number(number) is False
    
    def test_aadhaar_preprocessing(self, processor):
        """Test Aadhaar-specific image preprocessing"""
        # Create mock image
        mock_image = np.zeros((800, 1200, 3), dtype=np.uint8)
        
        with patch('cv2.cvtColor') as mock_cvt, \
             patch('cv2.GaussianBlur') as mock_blur, \
             patch('cv2.threshold') as mock_thresh:
            
            mock_cvt.return_value = mock_image
            mock_blur.return_value = mock_image
            mock_thresh.return_value = (127, mock_image)
            
            processed = processor.preprocess(mock_image)
            
            assert processed is not None
            mock_cvt.assert_called()
            mock_blur.assert_called()


class TestEmiratesIDProcessor:
    """Test Emirates ID processor"""
    
    @pytest.fixture
    def processor(self):
        return EmiratesIDProcessor()
    
    @pytest.fixture
    def sample_emirates_text(self):
        return [
            "United Arab Emirates",
            "الإمارات العربية المتحدة",
            "Identity Card",
            "784-1990-1234567-8",
            "MOHAMMED AHMED",
            "محمد أحمد",
            "Nationality: ARE",
            "Date of Birth: 01/01/1990",
            "Expiry Date: 01/01/2030"
        ]
    
    def test_emirates_detection(self, processor, sample_emirates_text):
        """Test Emirates ID detection"""
        assert processor.detect(sample_emirates_text) is True
    
    def test_emirates_extraction(self, processor, sample_emirates_text, emirates_id_test_data):
        """Test Emirates ID data extraction"""
        result = processor.extract_info(sample_emirates_text)
        
        assert 'id_number' in result
        assert 'name' in result
        assert 'nationality' in result
        assert 'dob' in result
        assert 'expiry_date' in result
    
    def test_emirates_id_validation(self, processor):
        """Test Emirates ID number validation"""
        valid_ids = [
            "784-1990-1234567-8",
            "784-1985-9876543-2"
        ]
        
        invalid_ids = [
            "123-1990-1234567-8",  # Wrong country code
            "784-1990-123456-8",   # Wrong format
            "784-1990-1234567",    # Missing check digit
        ]
        
        for id_num in valid_ids:
            assert processor._validate_emirates_id(id_num) is True
        
        for id_num in invalid_ids:
            assert processor._validate_emirates_id(id_num) is False


class TestPassportProcessor:
    """Test passport processor"""
    
    @pytest.fixture
    def processor(self):
        return PassportProcessor()
    
    @pytest.fixture
    def sample_passport_text(self):
        return [
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
        ]
    
    def test_passport_detection(self, processor, sample_passport_text):
        """Test passport detection"""
        assert processor.detect(sample_passport_text) is True
    
    def test_passport_extraction(self, processor, sample_passport_text):
        """Test passport data extraction"""
        result = processor.extract_info(sample_passport_text)
        
        assert 'passport_number' in result
        assert 'name' in result
        assert 'nationality' in result
        assert 'dob' in result
        assert 'place_of_birth' in result
    
    def test_passport_number_validation(self, processor):
        """Test passport number validation"""
        valid_numbers = [
            "A1234567",
            "B9876543",
            "Z1111111"
        ]
        
        invalid_numbers = [
            "1234567",     # Missing letter
            "AA1234567",   # Too many letters
            "A123456",     # Too short
            "A12345678"    # Too long
        ]
        
        for number in valid_numbers:
            assert processor._validate_passport_number(number) is True
        
        for number in invalid_numbers:
            assert processor._validate_passport_number(number) is False


class TestDrivingLicenseProcessor:
    """Test driving license processor"""
    
    @pytest.fixture
    def processor(self):
        return DrivingLicenseProcessor()
    
    @pytest.fixture
    def sample_dl_text(self):
        return [
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
        ]
    
    def test_dl_detection(self, processor, sample_dl_text):
        """Test driving license detection"""
        assert processor.detect(sample_dl_text) is True
    
    def test_dl_extraction(self, processor, sample_dl_text):
        """Test driving license data extraction"""
        result = processor.extract_info(sample_dl_text)
        
        assert 'dl_number' in result
        assert 'name' in result
        assert 'dob' in result
        assert 'address' in result
        assert 'validity' in result
    
    def test_dl_number_validation(self, processor):
        """Test DL number validation"""
        valid_numbers = [
            "DL-1420110012345",
            "DL-0520110054321",
            "HR-0619850123456"
        ]
        
        invalid_numbers = [
            "DL-142011001234",   # Too short
            "DL-14201100123456", # Too long
            "142011001234",      # Missing prefix
            "DL142011001234"     # Missing hyphen
        ]
        
        for number in valid_numbers:
            assert processor._validate_dl_number(number) is True
        
        for number in invalid_numbers:
            assert processor._validate_dl_number(number) is False


class TestUSDriversLicenseProcessor:
    """Test US driver's license processor"""
    
    @pytest.fixture
    def processor(self):
        return USDriversLicenseProcessor()
    
    @pytest.fixture
    def sample_us_dl_text(self):
        return [
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
        ]
    
    def test_us_dl_detection(self, processor, sample_us_dl_text):
        """Test US driver's license detection"""
        assert processor.detect(sample_us_dl_text) is True
    
    def test_us_dl_extraction(self, processor, sample_us_dl_text):
        """Test US driver's license data extraction"""
        result = processor.extract_info(sample_us_dl_text)
        
        assert 'dl_number' in result
        assert 'name' in result
        assert 'dob' in result
        assert 'address' in result
        assert 'state' in result
        assert 'expiry_date' in result


class TestProcessorPerformance:
    """Test processor performance and error handling"""
    
    @pytest.mark.performance
    def test_processor_speed(self, performance_tracker):
        """Test processor performance benchmarks"""
        processor = AadhaarProcessor()
        sample_text = ["Government of India", "आधार", "1234 5678 9012", "RAJESH KUMAR"]
        
        performance_tracker.start_timer('aadhaar_processing')
        
        # Run detection multiple times
        for _ in range(100):
            processor.detect(sample_text)
        
        performance_tracker.end_timer('aadhaar_processing')
        
        # Should complete 100 detections in under 1 second
        assert performance_tracker.get_duration('aadhaar_processing') < 1.0
    
    def test_processor_error_handling(self):
        """Test processor error handling with invalid input"""
        processor = AadhaarProcessor()
        
        # Test with None input
        assert processor.detect(None) is False
        
        # Test with empty list
        assert processor.detect([]) is False
        
        # Test with invalid text
        result = processor.extract_info(["Random text that doesn't match"])
        assert isinstance(result, dict)
        
        # Should handle malformed data gracefully
        malformed_text = [""] * 100  # 100 empty strings
        assert processor.detect(malformed_text) is False
    
    def test_memory_usage(self):
        """Test that processors don't leak memory"""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        processor = AadhaarProcessor()
        large_text = ["Government of India", "आधार"] * 1000
        
        # Process large amounts of text
        for _ in range(100):
            processor.detect(large_text)
            processor.extract_info(large_text)
        
        # Force garbage collection
        gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50


class TestProcessorIntegration:
    """Integration tests for processor workflows"""
    
    @pytest.mark.integration
    def test_full_processing_pipeline(self, mock_ocr_system):
        """Test complete document processing pipeline"""
        # Mock image
        mock_image = np.zeros((800, 1200, 3), dtype=np.uint8)
        
        # Test classification
        mock_text = ["Government of India", "आधार", "1234 5678 9012", "RAJESH KUMAR"]
        result = processor_registry.classify_document(mock_text)
        
        assert result is not None
        assert result['document_type'] in processor_registry.processors
        
        # Test processing
        processor = processor_registry.get_processor(result['document_type'])
        assert processor is not None
        
        # Test preprocessing
        processed_image = processor.preprocess(mock_image)
        assert processed_image is not None
        
        # Test extraction
        extracted_data = processor.extract_info(mock_text)
        assert isinstance(extracted_data, dict)
    
    @pytest.mark.integration
    def test_multi_document_processing(self):
        """Test processing multiple document types"""
        test_cases = [
            {
                'text': ["Government of India", "आधार", "1234 5678 9012"],
                'expected_type': 'aadhaar_card'
            },
            {
                'text': ["United Arab Emirates", "Identity Card", "784-1990-1234567-8"],
                'expected_type': 'emirates_id'
            },
            {
                'text': ["REPUBLIC OF INDIA", "PASSPORT", "A1234567"],
                'expected_type': 'passport'
            }
        ]
        
        for case in test_cases:
            result = processor_registry.classify_document(case['text'])
            assert result['document_type'] == case['expected_type']
            
            processor = processor_registry.get_processor(result['document_type'])
            extracted = processor.extract_info(case['text'])
            assert isinstance(extracted, dict)
            assert len(extracted) > 0