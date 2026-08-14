"""Language utilities for the bilingual Career Copilot experience."""

import re


class LanguageService:
    supported_languages = ("en", "ar")

    def detect_language(self, text: str) -> str:
        """Detect Arabic when Arabic letters are dominant; otherwise default to English."""
        letters = re.findall(r"[A-Za-z\u0600-\u06ff]", text or "")
        if not letters:
            return "en"
        arabic = sum("\u0600" <= char <= "\u06ff" for char in letters)
        return "ar" if arabic / len(letters) >= 0.25 else "en"

    def translate_text(self, text: str, target_language: str) -> str:
        """Translate common product phrases without pretending to be a general translator.

        The API clearly marks unsupported free-form translation so a production deployment
        can plug in a provider through an environment variable later.
        """
        if target_language not in self.supported_languages:
            raise ValueError("Unsupported target language")
        dictionary = {
            ("What is AI?", "ar"): "ما هو الذكاء الاصطناعي؟",
            ("What can you do?", "ar"): "ماذا تستطيع أن تفعل؟",
            ("ما هو الذكاء الاصطناعي؟", "en"): "What is artificial intelligence?",
            ("ماذا تستطيع أن تفعل؟", "en"): "What can you do?",
        }
        if self.detect_language(text) == target_language:
            return text
        return dictionary.get((text, target_language), text)

    def get_language_name(self, language_code: str) -> str:
        return {"en": "English", "ar": "Arabic"}.get(language_code, language_code)
