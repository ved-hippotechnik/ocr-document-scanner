#!/usr/bin/env python3
"""
Test script to verify that the new passport processors are working correctly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.processors.registry import processor_registry
import numpy as np

def test_passport_processors():
    """Test that all passport processors are registered and can detect documents"""
    
    print("=== Testing Passport Processors ===")
    print(f"Total processors registered: {len(processor_registry.processors)}")
    
    # List all registered processors
    print("\nRegistered processors:")
    for i, processor in enumerate(processor_registry.processors):
        print(f"{i+1}. {processor.__class__.__name__} - {processor.get_display_name()} ({processor.get_country_code()})")
    
    # Test sample texts for different passport types
    test_cases = [
        {
            'text': 'P<GBRGBR123456789<<<<<<<<<<<<<<<<<<<<<<<<<<<\n90/01/01M30/12/31GBR<<<<<<<<<<<1234567890<<<<<\nSMITH<<JOHN<DAVID<<<<<<<<<<<<<<<<<<<<<<<<<<\nUNITED KINGDOM OF GREAT BRITAIN AND NORTHERN IRELAND\nPASSPORT\nNationality BRITISH\nDate of birth 01 JAN 1990\nDate of issue 01 JAN 2020\nDate of expiry 31 DEC 2030',
            'expected': 'UK Passport'
        },
        {
            'text': 'CANADA\nPASSPORT\nPASSEPORT\nGovernment of Canada\nGouvernement du Canada\nJohn Smith\nDate of birth 01 JAN 1990\nNationality CANADIAN\nPassport No AB123456\nDate of issue 01 JAN 2020\nDate of expiry 31 DEC 2030',
            'expected': 'Canadian Passport'
        },
        {
            'text': 'AUSTRALIA\nPASSPORT\nCommonwealth of Australia\nSurname SMITH\nGiven names JOHN DAVID\nNationality AUSTRALIAN\nPassport No A12345678\nDate of birth 01 JAN 1990\nDate of issue 01 JAN 2020\nDate of expiry 31 DEC 2030',
            'expected': 'Australian Passport'
        },
        {
            'text': 'BUNDESREPUBLIK DEUTSCHLAND\nDEUTSCHER REISEPASS\nSurname MÜLLER\nGiven names HANS PETER\nNationality DEUTSCH\nPassport No C12345678\nDate of birth 01 JAN 1990\nDate of issue 01 JAN 2020\nDate of expiry 31 DEC 2030',
            'expected': 'German Passport'
        },
        {
            'text': 'UNITED STATES OF AMERICA\nU.S. CITIZENSHIP AND IMMIGRATION SERVICES\nPERMANENT RESIDENT CARD\nSmith John David\nA123456789\nCard Number ABC1234567890\nResident Since 01/01/2020\nCard Expires 01/01/2030',
            'expected': 'US Green Card'
        }
    ]
    
    print("\n=== Testing Document Detection ===")
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest {i+1}: {test_case['expected']}")
        print(f"Sample text: {test_case['text'][:100]}...")
        
        # Test detection
        doc_display_name, processor = processor_registry.detect_document_type(test_case['text'])
        
        if processor:
            print(f"✅ Detected: {doc_display_name}")
            print(f"   Processor: {processor.__class__.__name__}")
            print(f"   Country: {processor.country}")
            print(f"   Expected: {test_case['expected']}")
            
            # Test if detection matches expectation
            if doc_display_name == test_case['expected']:
                print("   ✅ Detection CORRECT")
            else:
                print(f"   ⚠️  Detection MISMATCH - Expected: {test_case['expected']}")
        else:
            print(f"❌ No processor detected for {test_case['expected']}")
    
    # Test processing with dummy image
    print("\n=== Testing Document Processing ===")
    dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)  # Black image
    
    uk_processor = None
    for processor in processor_registry.processors:
        if processor.__class__.__name__ == 'UKPassportProcessor':
            uk_processor = processor
            break
    
    if uk_processor:
        print(f"\nTesting {uk_processor.__class__.__name__} processing...")
        try:
            result = uk_processor.process(dummy_image, [test_cases[0]['text']])
            print(f"✅ Processing successful")
            print(f"   Document type: {result.get('document_type')}")
            print(f"   Confidence: {result.get('confidence')}")
            print(f"   Processor: {result.get('processor')}")
            print(f"   Keys extracted: {list(result.keys())}")
        except Exception as e:
            print(f"❌ Processing failed: {e}")
    
    # Test supported document types endpoint data
    print("\n=== Testing Supported Document Types ===")
    supported_docs = processor_registry.list_supported_documents()
    print(f"Total supported document types: {len(supported_docs)}")
    
    passport_types = [doc for doc in supported_docs if 'passport' in doc['document_type'].lower()]
    print(f"Passport types: {len(passport_types)}")
    
    for doc in passport_types:
        print(f"  - {doc['display_name']} ({doc['country_code']})")

if __name__ == "__main__":
    test_passport_processors()
