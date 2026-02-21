"""
AI module for OCR Document Scanner
Provides AI-powered document classification and analysis
"""

from .document_classifier import DocumentClassifier
from .routes import ai_bp

try:
    from .vision_service import ClaudeVisionService
except ImportError:
    ClaudeVisionService = None

__all__ = ['DocumentClassifier', 'ClaudeVisionService', 'ai_bp']