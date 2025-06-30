#!/usr/bin/env python3
"""
Open Source Global Document Database Builder
Automatically researches and implements support for documents from multiple countries
"""

import requests
import json
import re
import os
try:
    import yaml
except ImportError:
    print("Installing PyYAML...")
    import subprocess
    subprocess.check_call(["pip", "install", "PyYAML"])
    import yaml
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from PIL import Image, ImageDraw, ImageFont

@dataclass
class DocumentPattern:
    keywords: List[str]
    number_formats: List[str]
    languages: List[str]
    text_indicators: List[str]

@dataclass
class DocumentSpec:
    country: str
    country_code: str
    document_type: str
    official_name: str
    languages: List[str]
    patterns: DocumentPattern
    fields: List[str]
    preprocessing: List[str]

class OpenSourceDocumentBuilder:
    """Build global document support using open source resources"""
    
    def __init__(self):
        self.document_specs = []
        self.initialize_known_documents()
    
    def initialize_known_documents(self):
        """Initialize with current supported documents"""
        # UAE Emirates ID
        self.document_specs.append(DocumentSpec(
            country="United Arab Emirates",
            country_code="ARE",
            document_type="emirates_id",
            official_name="Emirates ID",
            languages=["ar", "en"],
            patterns=DocumentPattern(
                keywords=["emirates id", "بطاقة الهوية", "federal authority"],
                number_formats=[r"784-\d{4}-\d{7}-\d"],
                languages=["arabic", "english"],
                text_indicators=["uae", "united arab emirates", "الإمارات"]
            ),
            fields=["id_number", "name", "nationality", "dob", "gender", "expiry"],
            preprocessing=["clahe", "bilateral_filter", "arabic_ocr"]
        ))
        
        # India Aadhaar
        self.document_specs.append(DocumentSpec(
            country="India",
            country_code="IND",
            document_type="aadhaar_card",
            official_name="Aadhaar Card",
            languages=["hi", "en"],
            patterns=DocumentPattern(
                keywords=["aadhaar", "आधार", "government of india", "भारत सरकार"],
                number_formats=[r"\d{4}\s*\d{4}\s*\d{4}"],
                languages=["hindi", "english"],
                text_indicators=["india", "भारत", "unique identification"]
            ),
            fields=["aadhaar_number", "name", "dob", "gender", "address"],
            preprocessing=["clahe", "denoise", "hindi_ocr"]
        ))
    
    def add_global_documents(self):
        """Add support for documents from many countries using open source data"""
        
        # Major English-speaking countries
        self.add_usa_documents()
        self.add_uk_documents()
        self.add_canada_documents()
        self.add_australia_documents()
        
        # Major European countries
        self.add_germany_documents()
        self.add_france_documents()
        self.add_spain_documents()
        self.add_italy_documents()
        self.add_netherlands_documents()
        
        # Major Asian countries
        self.add_japan_documents()
        self.add_south_korea_documents()
        self.add_singapore_documents()
        self.add_malaysia_documents()
        self.add_thailand_documents()
        
        # Major Latin American countries
        self.add_brazil_documents()
        self.add_mexico_documents()
        self.add_argentina_documents()
        
        # Additional countries
        self.add_south_africa_documents()
        self.add_nigeria_documents()
        self.add_egypt_documents()
        
    def add_usa_documents(self):
        """Add USA document types"""
        # US Driver's License (varies by state)
        self.document_specs.append(DocumentSpec(
            country="United States",
            country_code="USA",
            document_type="drivers_license",
            official_name="Driver's License",
            languages=["en"],
            patterns=DocumentPattern(
                keywords=["driver license", "drivers license", "dl", "motor vehicle"],
                number_formats=[r"[A-Z0-9]{8,15}", r"[A-Z]\d{7,12}"],
                languages=["english"],
                text_indicators=["united states", "state of", "department of motor vehicles"]
            ),
            fields=["license_number", "name", "address", "dob", "class", "expiry"],
            preprocessing=["enhance_contrast", "denoise"]
        ))
        
        # US State ID
        self.document_specs.append(DocumentSpec(
            country="United States",
            country_code="USA",
            document_type="state_id",
            official_name="State ID",
            languages=["en"],
            patterns=DocumentPattern(
                keywords=["identification card", "state id", "identity card"],
                number_formats=[r"[A-Z0-9]{8,15}"],
                languages=["english"],
                text_indicators=["state of", "identification", "not a driver license"]
            ),
            fields=["id_number", "name", "address", "dob", "height", "weight"],
            preprocessing=["enhance_contrast", "denoise"]
        ))
    
    def add_uk_documents(self):
        """Add UK document types"""
        self.document_specs.append(DocumentSpec(
            country="United Kingdom",
            country_code="GBR",
            document_type="driving_licence",
            official_name="UK Driving Licence",
            languages=["en"],
            patterns=DocumentPattern(
                keywords=["driving licence", "dvla", "driver and vehicle licensing agency"],
                number_formats=[r"[A-Z]{5}\d{6}[A-Z]{2}\d[A-Z]{2}"],
                languages=["english"],
                text_indicators=["united kingdom", "great britain", "driving licence"]
            ),
            fields=["licence_number", "name", "address", "dob", "categories", "expiry"],
            preprocessing=["enhance_contrast", "denoise"]
        ))
    
    def add_canada_documents(self):
        """Add Canadian document types"""
        self.document_specs.append(DocumentSpec(
            country="Canada",
            country_code="CAN",
            document_type="drivers_license",
            official_name="Driver's License",
            languages=["en", "fr"],
            patterns=DocumentPattern(
                keywords=["driver's license", "permis de conduire", "licence"],
                number_formats=[r"[A-Z0-9]{8,15}"],
                languages=["english", "french"],
                text_indicators=["canada", "province", "ontario", "quebec", "british columbia"]
            ),
            fields=["license_number", "name", "address", "dob", "class", "expiry"],
            preprocessing=["enhance_contrast", "denoise", "bilingual_ocr"]
        ))
    
    def add_australia_documents(self):
        """Add Australian document types"""
        self.document_specs.append(DocumentSpec(
            country="Australia",
            country_code="AUS",
            document_type="drivers_license",
            official_name="Driver Licence",
            languages=["en"],
            patterns=DocumentPattern(
                keywords=["driver licence", "drivers licence", "transport"],
                number_formats=[r"\d{8,10}", r"[A-Z]\d{7,9}"],
                languages=["english"],
                text_indicators=["australia", "new south wales", "victoria", "queensland"]
            ),
            fields=["licence_number", "name", "address", "dob", "class", "expiry"],
            preprocessing=["enhance_contrast", "denoise"]
        ))
    
    def add_germany_documents(self):
        """Add German document types"""
        self.document_specs.append(DocumentSpec(
            country="Germany",
            country_code="DEU",
            document_type="personalausweis",
            official_name="Personalausweis",
            languages=["de"],
            patterns=DocumentPattern(
                keywords=["personalausweis", "bundesrepublik deutschland", "ausweis"],
                number_formats=[r"[A-Z]\d{8}", r"\d{9}[A-Z]"],
                languages=["german"],
                text_indicators=["deutschland", "germany", "bundesrepublik"]
            ),
            fields=["ausweis_nummer", "name", "geburtstag", "nationalitat", "ablauf"],
            preprocessing=["enhance_contrast", "denoise", "german_ocr"]
        ))
        
        self.document_specs.append(DocumentSpec(
            country="Germany",
            country_code="DEU",
            document_type="fuhrerschein",
            official_name="Führerschein",
            languages=["de"],
            patterns=DocumentPattern(
                keywords=["führerschein", "fahrerlaubnis", "driving licence"],
                number_formats=[r"\d{11}"],
                languages=["german"],
                text_indicators=["deutschland", "führerschein", "klasse"]
            ),
            fields=["nummer", "name", "geburtstag", "klassen", "ablauf"],
            preprocessing=["enhance_contrast", "denoise", "german_ocr"]
        ))
    
    def add_france_documents(self):
        """Add French document types"""
        self.document_specs.append(DocumentSpec(
            country="France",
            country_code="FRA",
            document_type="carte_identite",
            official_name="Carte d'identité",
            languages=["fr"],
            patterns=DocumentPattern(
                keywords=["carte d'identité", "république française", "identité"],
                number_formats=[r"\d{12}"],
                languages=["french"],
                text_indicators=["france", "république française", "carte nationale"]
            ),
            fields=["numero", "nom", "prenom", "naissance", "nationalite"],
            preprocessing=["enhance_contrast", "denoise", "french_ocr"]
        ))
    
    def add_spain_documents(self):
        """Add Spanish document types"""
        self.document_specs.append(DocumentSpec(
            country="Spain",
            country_code="ESP",
            document_type="dni",
            official_name="DNI",
            languages=["es"],
            patterns=DocumentPattern(
                keywords=["documento nacional de identidad", "dni", "españa"],
                number_formats=[r"\d{8}[A-Z]"],
                languages=["spanish"],
                text_indicators=["españa", "spain", "reino de españa"]
            ),
            fields=["dni_numero", "nombre", "apellidos", "nacimiento", "nacionalidad"],
            preprocessing=["enhance_contrast", "denoise", "spanish_ocr"]
        ))
    
    def add_italy_documents(self):
        """Add Italian document types"""
        self.document_specs.append(DocumentSpec(
            country="Italy",
            country_code="ITA",
            document_type="carta_identita",
            official_name="Carta d'identità",
            languages=["it"],
            patterns=DocumentPattern(
                keywords=["carta d'identità", "repubblica italiana", "comune"],
                number_formats=[r"[A-Z]{2}\d{7}"],
                languages=["italian"],
                text_indicators=["italia", "italy", "repubblica italiana"]
            ),
            fields=["numero", "nome", "cognome", "nato", "nazionalità"],
            preprocessing=["enhance_contrast", "denoise", "italian_ocr"]
        ))
    
    def add_netherlands_documents(self):
        """Add Dutch document types"""
        self.document_specs.append(DocumentSpec(
            country="Netherlands",
            country_code="NLD",
            document_type="identiteitskaart",
            official_name="Nederlandse identiteitskaart",
            languages=["nl"],
            patterns=DocumentPattern(
                keywords=["identiteitskaart", "nederland", "koninkrijk"],
                number_formats=[r"[A-Z]{2}[A-Z0-9]{6}"],
                languages=["dutch"],
                text_indicators=["nederland", "netherlands", "koninkrijk"]
            ),
            fields=["bsn", "naam", "geboortedatum", "nationaliteit"],
            preprocessing=["enhance_contrast", "denoise", "dutch_ocr"]
        ))
    
    def add_japan_documents(self):
        """Add Japanese document types"""
        self.document_specs.append(DocumentSpec(
            country="Japan",
            country_code="JPN",
            document_type="mynumber_card",
            official_name="My Number Card",
            languages=["ja", "en"],
            patterns=DocumentPattern(
                keywords=["個人番号カード", "my number", "マイナンバー"],
                number_formats=[r"\d{4}\s\d{4}\s\d{4}"],
                languages=["japanese", "english"],
                text_indicators=["japan", "日本", "個人番号"]
            ),
            fields=["mynumber", "name", "birth_date", "address"],
            preprocessing=["enhance_contrast", "denoise", "japanese_ocr"]
        ))
    
    def add_south_korea_documents(self):
        """Add South Korean document types"""
        self.document_specs.append(DocumentSpec(
            country="South Korea",
            country_code="KOR",
            document_type="resident_card",
            official_name="Resident Registration Card",
            languages=["ko", "en"],
            patterns=DocumentPattern(
                keywords=["주민등록증", "resident registration", "대한민국"],
                number_formats=[r"\d{6}-\d{7}"],
                languages=["korean", "english"],
                text_indicators=["korea", "대한민국", "주민등록"]
            ),
            fields=["registration_number", "name", "address", "issued_date"],
            preprocessing=["enhance_contrast", "denoise", "korean_ocr"]
        ))
    
    def add_singapore_documents(self):
        """Add Singapore document types"""
        self.document_specs.append(DocumentSpec(
            country="Singapore",
            country_code="SGP",
            document_type="nric",
            official_name="NRIC",
            languages=["en"],
            patterns=DocumentPattern(
                keywords=["nric", "national registration identity card", "singapore"],
                number_formats=[r"[STFG]\d{7}[A-Z]"],
                languages=["english"],
                text_indicators=["singapore", "republic of singapore"]
            ),
            fields=["nric_number", "name", "race", "date_of_birth", "country_of_birth"],
            preprocessing=["enhance_contrast", "denoise"]
        ))
    
    def add_malaysia_documents(self):
        """Add Malaysian document types"""
        self.document_specs.append(DocumentSpec(
            country="Malaysia",
            country_code="MYS",
            document_type="mykad",
            official_name="MyKad",
            languages=["ms", "en"],
            patterns=DocumentPattern(
                keywords=["mykad", "malaysia", "kad pengenalan"],
                number_formats=[r"\d{6}-\d{2}-\d{4}"],
                languages=["malay", "english"],
                text_indicators=["malaysia", "kad pengenalan"]
            ),
            fields=["ic_number", "name", "address", "date_of_birth", "religion"],
            preprocessing=["enhance_contrast", "denoise", "malay_ocr"]
        ))
    
    def add_thailand_documents(self):
        """Add Thai document types"""
        self.document_specs.append(DocumentSpec(
            country="Thailand",
            country_code="THA",
            document_type="thai_id",
            official_name="Thai National ID Card",
            languages=["th", "en"],
            patterns=DocumentPattern(
                keywords=["บัตรประชาชน", "national id card", "thailand"],
                number_formats=[r"\d{1}-\d{4}-\d{5}-\d{2}-\d{1}"],
                languages=["thai", "english"],
                text_indicators=["thailand", "ประเทศไทย", "บัตรประชาชน"]
            ),
            fields=["id_number", "name", "last_name", "date_of_birth", "address"],
            preprocessing=["enhance_contrast", "denoise", "thai_ocr"]
        ))
    
    def add_brazil_documents(self):
        """Add Brazilian document types"""
        self.document_specs.append(DocumentSpec(
            country="Brazil",
            country_code="BRA",
            document_type="rg",
            official_name="RG",
            languages=["pt"],
            patterns=DocumentPattern(
                keywords=["registro geral", "rg", "república federativa do brasil"],
                number_formats=[r"\d{1,2}\.\d{3}\.\d{3}-\d{1}"],
                languages=["portuguese"],
                text_indicators=["brasil", "brazil", "república federativa"]
            ),
            fields=["rg_numero", "nome", "filiacao", "nascimento", "naturalidade"],
            preprocessing=["enhance_contrast", "denoise", "portuguese_ocr"]
        ))
    
    def add_mexico_documents(self):
        """Add Mexican document types"""
        self.document_specs.append(DocumentSpec(
            country="Mexico",
            country_code="MEX",
            document_type="ine",
            official_name="INE",
            languages=["es"],
            patterns=DocumentPattern(
                keywords=["instituto nacional electoral", "ine", "méxico"],
                number_formats=[r"\d{13}"],
                languages=["spanish"],
                text_indicators=["méxico", "mexico", "estados unidos mexicanos"]
            ),
            fields=["clave_elector", "nombre", "domicilio", "nacimiento"],
            preprocessing=["enhance_contrast", "denoise", "spanish_ocr"]
        ))
    
    def add_argentina_documents(self):
        """Add Argentine document types"""
        self.document_specs.append(DocumentSpec(
            country="Argentina",
            country_code="ARG",
            document_type="dni",
            official_name="DNI",
            languages=["es"],
            patterns=DocumentPattern(
                keywords=["documento nacional de identidad", "república argentina"],
                number_formats=[r"\d{7,8}"],
                languages=["spanish"],
                text_indicators=["argentina", "república argentina"]
            ),
            fields=["dni_numero", "apellido", "nombre", "nacimiento", "sexo"],
            preprocessing=["enhance_contrast", "denoise", "spanish_ocr"]
        ))
    
    def add_south_africa_documents(self):
        """Add South African document types"""
        self.document_specs.append(DocumentSpec(
            country="South Africa",
            country_code="ZAF",
            document_type="green_id",
            official_name="Green ID Book",
            languages=["en", "af"],
            patterns=DocumentPattern(
                keywords=["identity document", "south africa", "republic"],
                number_formats=[r"\d{13}"],
                languages=["english", "afrikaans"],
                text_indicators=["south africa", "republic of south africa"]
            ),
            fields=["id_number", "surname", "names", "date_of_birth", "sex"],
            preprocessing=["enhance_contrast", "denoise"]
        ))
    
    def add_nigeria_documents(self):
        """Add Nigerian document types"""
        self.document_specs.append(DocumentSpec(
            country="Nigeria",
            country_code="NGA",
            document_type="nin",
            official_name="National Identification Number",
            languages=["en"],
            patterns=DocumentPattern(
                keywords=["national identification number", "nin", "nigeria"],
                number_formats=[r"\d{11}"],
                languages=["english"],
                text_indicators=["nigeria", "federal republic of nigeria"]
            ),
            fields=["nin", "surname", "firstname", "date_of_birth", "gender"],
            preprocessing=["enhance_contrast", "denoise"]
        ))
    
    def add_egypt_documents(self):
        """Add Egyptian document types"""
        self.document_specs.append(DocumentSpec(
            country="Egypt",
            country_code="EGY",
            document_type="national_id",
            official_name="National ID Card",
            languages=["ar", "en"],
            patterns=DocumentPattern(
                keywords=["بطاقة الرقم القومي", "national id", "egypt", "مصر"],
                number_formats=[r"\d{14}"],
                languages=["arabic", "english"],
                text_indicators=["egypt", "مصر", "جمهورية مصر العربية"]
            ),
            fields=["national_id", "name", "birth_date", "governorate"],
            preprocessing=["enhance_contrast", "denoise", "arabic_ocr"]
        ))
    
    def generate_detection_functions(self):
        """Generate detection functions for all document types"""
        functions = []
        
        for spec in self.document_specs:
            func_name = f"detect_{spec.document_type}"
            
            function_code = f'''
def {func_name}(text):
    """Detect {spec.official_name} from {spec.country}"""
    text_lower = text.lower()
    
    # {spec.country} {spec.official_name} patterns
    keywords = {spec.patterns.keywords}
    number_patterns = {spec.patterns.number_formats}
    text_indicators = {spec.patterns.text_indicators}
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2
'''
            functions.append(function_code)
        
        return functions
    
    def generate_preprocessing_functions(self):
        """Generate preprocessing functions for all document types"""
        functions = []
        
        for spec in self.document_specs:
            func_name = f"preprocess_{spec.document_type}"
            
            function_code = f'''
def {func_name}(img):
    """Enhanced preprocessing for {spec.country} {spec.official_name}"""
    processed_images = []
    
    # Base preprocessing
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    processed_images.append(enhanced)
    
    # {spec.country}-specific preprocessing
    preprocessing_steps = {spec.preprocessing}
    
    for step in preprocessing_steps:
        if step == "denoise":
            denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
            processed_images.append(denoised)
        elif step == "enhance_contrast":
            enhanced_contrast = cv2.convertScaleAbs(enhanced, alpha=1.2, beta=10)
            processed_images.append(enhanced_contrast)
        # Add more preprocessing steps as needed
    
    return processed_images
'''
            functions.append(function_code)
        
        return functions
    
    def generate_extraction_functions(self):
        """Generate extraction functions for all document types"""
        functions = []
        
        for spec in self.document_specs:
            func_name = f"enhanced_{spec.document_type}_extraction"
            
            # Create field mapping
            field_mapping = {}
            for field in spec.fields:
                if 'name' in field.lower():
                    field_mapping['full_name'] = field
                elif 'number' in field.lower() or 'id' in field.lower():
                    field_mapping['document_number'] = field
                elif 'birth' in field.lower() or 'dob' in field.lower():
                    field_mapping['date_of_birth'] = field
                elif 'expire' in field.lower() or 'expiry' in field.lower():
                    field_mapping['date_of_expiry'] = field
                elif 'gender' in field.lower() or 'sex' in field.lower():
                    field_mapping['gender'] = field
            
            function_code = f'''
def {func_name}(text_results):
    """Extract specific information from {spec.country} {spec.official_name}"""
    info = {{
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': '{spec.country_code}',
        'gender': None
    }}
    
    combined_text = '\\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = {spec.patterns.number_formats}
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\\s]+([A-Za-z\\s]+?)\\n',
        r'nom[:\\s]+([A-Za-z\\s]+?)\\n',
        r'nombre[:\\s]+([A-Za-z\\s]+?)\\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\\s]*([0-9]{{1,2}}[\\s./-][0-9]{{1,2}}[\\s./-][0-9]{{2,4}})',
        r'([0-9]{{1,2}}[\\s./-][0-9]{{1,2}}[\\s./-][0-9]{{2,4}})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{{1,2}}[\\s./-][0-9]{{1,2}}[\\s./-][0-9]{{2,4}}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\\b(male|female|m|f)\\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info
'''
            functions.append(function_code)
        
        return functions
    
    def export_all_implementations(self):
        """Export all generated functions to files"""
        print("🔧 Generating implementation files...")
        
        # Generate detection functions
        detection_functions = self.generate_detection_functions()
        with open('global_document_detection.py', 'w') as f:
            f.write("# Auto-generated global document detection functions\n")
            f.write("import re\n\n")
            for func in detection_functions:
                f.write(func + "\n")
        
        # Generate preprocessing functions  
        preprocessing_functions = self.generate_preprocessing_functions()
        with open('global_document_preprocessing.py', 'w') as f:
            f.write("# Auto-generated global document preprocessing functions\n")
            f.write("import cv2\nimport numpy as np\n\n")
            for func in preprocessing_functions:
                f.write(func + "\n")
        
        # Generate extraction functions
        extraction_functions = self.generate_extraction_functions()
        with open('global_document_extraction.py', 'w') as f:
            f.write("# Auto-generated global document extraction functions\n")
            f.write("import re\nfrom datetime import datetime\n\n")
            f.write("""
def normalize_date(date_str):
    \"\"\"Normalize date format\"\"\"
    # Add date normalization logic
    return date_str.strip()
\n""")
            for func in extraction_functions:
                f.write(func + "\n")
        
        # Generate country mapping
        country_mapping = {}
        for spec in self.document_specs:
            if spec.country not in country_mapping:
                country_mapping[spec.country] = []
            country_mapping[spec.country].append({
                'type': spec.document_type,
                'name': spec.official_name,
                'languages': spec.languages,
                'patterns': asdict(spec.patterns)
            })
        
        with open('global_document_mapping.yaml', 'w') as f:
            yaml.dump(country_mapping, f, default_flow_style=False)
        
        print(f"✅ Generated support for {len(self.document_specs)} document types")
        print(f"✅ Covering {len(country_mapping)} countries")
        
        return len(self.document_specs), len(country_mapping)

def main():
    """Main function to build global document support"""
    print("🌍 OPEN SOURCE GLOBAL DOCUMENT BUILDER")
    print("=" * 60)
    
    builder = OpenSourceDocumentBuilder()
    
    print("📊 Adding global document support...")
    builder.add_global_documents()
    
    print(f"\n🎯 Document types to be supported:")
    for spec in builder.document_specs:
        print(f"   • {spec.official_name} ({spec.country})")
    
    print(f"\n🔧 Generating implementation files...")
    doc_count, country_count = builder.export_all_implementations()
    
    print(f"\n✅ SUCCESS! Generated support for:")
    print(f"   📄 {doc_count} document types")
    print(f"   🌍 {country_count} countries")
    print(f"   🗂️  Files created:")
    print(f"      • global_document_detection.py")
    print(f"      • global_document_preprocessing.py") 
    print(f"      • global_document_extraction.py")
    print(f"      • global_document_mapping.yaml")
    
    print(f"\n🚀 Next steps:")
    print(f"   1. Review generated functions")
    print(f"   2. Integrate with main routes.py")
    print(f"   3. Test with sample documents")
    print(f"   4. Add language-specific OCR models")

if __name__ == "__main__":
    main()
