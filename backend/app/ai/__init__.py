"""
AI module for OCR Document Scanner
Provides AI-powered document classification and analysis
"""

from .document_classifier import DocumentClassifier
from .routes import ai_bp

__all__ = ['DocumentClassifier', 'ai_bp']