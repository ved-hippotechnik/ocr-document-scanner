"""
Language detection and management for multi-language OCR
"""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Map of Tesseract language codes to display names
TESSERACT_LANGUAGES = {
    'eng': 'English',
    'ara': 'Arabic',
    'hin': 'Hindi',
    'fra': 'French',
    'deu': 'German',
    'spa': 'Spanish',
    'por': 'Portuguese',
    'ita': 'Italian',
    'jpn': 'Japanese',
    'kor': 'Korean',
    'chi_sim': 'Chinese (Simplified)',
    'chi_tra': 'Chinese (Traditional)',
    'rus': 'Russian',
    'tha': 'Thai',
    'vie': 'Vietnamese',
    'tur': 'Turkish',
    'pol': 'Polish',
    'nld': 'Dutch',
    'tam': 'Tamil',
    'tel': 'Telugu',
    'kan': 'Kannada',
    'mal': 'Malayalam',
    'ben': 'Bengali',
    'guj': 'Gujarati',
    'mar': 'Marathi',
    'pan': 'Punjabi',
    'urd': 'Urdu',
}

# Cached available languages (populated on first call)
_available_languages_cache = None


def get_available_languages() -> List[str]:
    """Query Tesseract for installed language packs (cached)"""
    global _available_languages_cache
    if _available_languages_cache is not None:
        return _available_languages_cache

    try:
        import pytesseract
        langs = pytesseract.get_languages()
        _available_languages_cache = [l for l in langs if l != 'osd']
        return _available_languages_cache
    except Exception as e:
        logger.warning(f"Could not query Tesseract languages: {e}")
        return ['eng']


def validate_language(lang: str) -> bool:
    """Check if a language code is available in Tesseract"""
    # Handle multi-language strings like 'eng+ara'
    codes = lang.split('+')
    available = get_available_languages()
    return all(code in available for code in codes)


def detect_language(text: str) -> str:
    """Auto-detect the language of *text* and return a Tesseract code.

    Falls back to ``'eng'`` when ``langdetect`` is not installed or
    detection fails.
    """
    if not text or len(text.strip()) < 20:
        return 'eng'

    try:
        from langdetect import detect
    except ImportError:
        logger.debug("langdetect not installed — defaulting to eng")
        return 'eng'

    _lang_map = {
        'en': 'eng', 'hi': 'hin', 'ar': 'ara', 'fr': 'fra',
        'de': 'deu', 'es': 'spa', 'pt': 'por', 'it': 'ita',
        'ja': 'jpn', 'ko': 'kor', 'zh-cn': 'chi_sim',
        'zh-tw': 'chi_tra', 'ru': 'rus', 'th': 'tha',
        'vi': 'vie', 'tr': 'tur', 'pl': 'pol', 'nl': 'nld',
        'ta': 'tam', 'te': 'tel', 'kn': 'kan', 'ml': 'mal',
        'bn': 'ben', 'gu': 'guj', 'mr': 'mar', 'pa': 'pan',
        'ur': 'urd',
    }

    try:
        detected = detect(text)
        tess_code = _lang_map.get(detected, 'eng')
        # Only return if Tesseract actually has this language installed
        if validate_language(tess_code):
            return tess_code
        return 'eng'
    except Exception as exc:
        logger.debug("Language detection failed: %s", exc)
        return 'eng'


def get_languages_info() -> List[Dict[str, str]]:
    """Return available languages with display names"""
    available = get_available_languages()
    return [
        {
            'code': lang,
            'name': TESSERACT_LANGUAGES.get(lang, lang.replace('_', ' ').title())
        }
        for lang in sorted(available)
    ]
