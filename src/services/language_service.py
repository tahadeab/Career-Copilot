"""
Language Service - Language detection and translation
"""

import logging

logger = logging.getLogger(__name__)


class LanguageService:
    """Service for language detection and translation."""
    
    def __init__(self):
        self.supported_languages = ['en', 'ar']
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of the given text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Language code ('en' or 'ar')
        """
        # Simple heuristic based on Arabic character detection
        arabic_chars = set('ابتثجحخدذرزسشصضطظعغفقكلمنهويآأإةؤئ')
        
        # Count Arabic characters
        arabic_count = sum(1 for char in text if char in arabic_chars)
        
        # If more than 30% Arabic characters, consider it Arabic
        if len(text) > 0 and (arabic_count / len(text)) > 0.3:
            return 'ar'
        
        return 'en'
    
    def translate_text(self, text: str, target_language: str) -> str:
        """
        Translate text to the target language.
        For now, returns a placeholder message.
        
        Args:
            text: The text to translate
            target_language: Target language code
            
        Returns:
            Translated text (or placeholder)
        """
        logger.info(f"Translation requested: {text[:50]}... to {target_language}")
        
        # Placeholder translations
        if target_language == 'ar':
            return "[ترجمة] " + text
        else:
            return "[Translation] " + text
    
    def get_language_name(self, language_code: str) -> str:
        """Get the full name of a language from its code."""
        names = {
            'en': 'English',
            'ar': 'العربية'
        }
        return names.get(language_code, language_code)
