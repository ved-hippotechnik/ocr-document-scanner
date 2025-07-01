"""
Initialize and register all document processors
"""
from .emirates_id import EmiratesIDProcessor
from .aadhaar import AadhaarProcessor
from .driving_license import DrivingLicenseProcessor
from .passport import PassportProcessor
from .us_drivers_license import USDriversLicenseProcessor
from . import processor_registry

# Register all processors
def initialize_processors():
    """Initialize and register all document processors"""
    
    # Register all available processors
    processor_registry.register(EmiratesIDProcessor())
    processor_registry.register(AadhaarProcessor())
    processor_registry.register(DrivingLicenseProcessor())
    processor_registry.register(PassportProcessor())
    processor_registry.register(USDriversLicenseProcessor())
    
    # Future processors can be added here:
    # processor_registry.register(UKDrivingLicenceProcessor())
    # processor_registry.register(PassportUSProcessor())
    # processor_registry.register(IDCardProcessor())
    
    print(f"✅ Registered {len(processor_registry.processors)} document processors")

# Initialize processors when module is imported
initialize_processors()
