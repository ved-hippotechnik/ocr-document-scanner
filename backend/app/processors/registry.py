"""
Initialize and register all document processors
"""
from .emirates_id import EmiratesIDProcessor
from .aadhaar import AadhaarProcessor
from .driving_license import DrivingLicenseProcessor
from .passport import PassportProcessor
from .us_drivers_license import USDriversLicenseProcessor
from .us_green_card import USGreenCardProcessor
from .uk_passport import UKPassportProcessor
from .canadian_passport import CanadianPassportProcessor
from .australian_passport import AustralianPassportProcessor
from .german_passport import GermanPassportProcessor
from . import processor_registry

# Register all processors
def initialize_processors():
    """Initialize and register all document processors"""
    
    # Register specific processors first (higher priority)
    processor_registry.register(EmiratesIDProcessor())
    processor_registry.register(AadhaarProcessor())
    processor_registry.register(DrivingLicenseProcessor())
    processor_registry.register(USGreenCardProcessor())  # Green Card before Drivers License
    processor_registry.register(USDriversLicenseProcessor())
    
    # Country-specific passport processors (register before generic passport)
    processor_registry.register(UKPassportProcessor())
    processor_registry.register(CanadianPassportProcessor())
    processor_registry.register(AustralianPassportProcessor())
    processor_registry.register(GermanPassportProcessor())
    
    # Generic passport processor (fallback for other passports)
    processor_registry.register(PassportProcessor())
    
    # Future processors can be added here:
    # processor_registry.register(FrenchPassportProcessor())
    # processor_registry.register(ItalianPassportProcessor())
    # processor_registry.register(SpanishPassportProcessor())
    # processor_registry.register(JapanesePassportProcessor())
    # processor_registry.register(ChinesePassportProcessor())
    # processor_registry.register(ItalianPassportProcessor())
    # processor_registry.register(SpanishPassportProcessor())
    # processor_registry.register(JapanesePassportProcessor())
    # processor_registry.register(ChinesePassportProcessor())
    
    print(f"✅ Registered {len(processor_registry.processors)} document processors")

# Initialize processors when module is imported
initialize_processors()
