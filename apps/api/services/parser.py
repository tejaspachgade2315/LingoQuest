import re
from typing import List, Dict, Any


class DocumentParserService:
    @staticmethod
    def clean_text(text: str) -> str:
        """Removes excessive whitespace and unwanted control characters."""
        text = re.sub(r'[\r\n\t]+', ' ', text)
        text = re.sub(r'\s{2,}', ' ', text)
        return text.strip()

    @staticmethod
    def extract_words(text: str) -> List[str]:
        """Extracts words while preserving hyphenated compounds."""
        raw_words = re.findall(r"\b[\w'-]+\b", text)
        return [w for w in raw_words if w]

    @staticmethod
    def normalize_word(word: str) -> str:
        """Normalizes word for phonetic / fuzzy comparison."""
        return re.sub(r'[^a-zA-Z0-9]', '', word).lower()

    @classmethod
    def parse_passage(cls, title: str, raw_content: str, difficulty: str = "beginner") -> Dict[str, Any]:
        cleaned = cls.clean_text(raw_content)
        words = cls.extract_words(cleaned)
        normalized_words = [cls.normalize_word(w) for w in words]

        # Simple syllable estimation
        total_syllables = sum(cls._estimate_syllables(w) for w in normalized_words)
        reading_level = cls._estimate_reading_level(len(words), total_syllables)

        return {
            "title": title,
            "content": cleaned,
            "words": words,
            "normalized_words": normalized_words,
            "total_words": len(words),
            "estimated_syllables": total_syllables,
            "difficulty_level": difficulty or reading_level,
        }

    @staticmethod
    def _estimate_syllables(word: str) -> int:
        word = word.lower()
        if len(word) <= 3:
            return 1
        count = len(re.findall(r'[aeiouy]+', word))
        if word.endswith('e') and not word.endswith('le') and count > 1:
            count -= 1
        return max(1, count)

    @classmethod
    def _estimate_reading_level(cls, word_count: int, syllable_count: int) -> str:
        if word_count == 0:
            return "beginner"
        avg_syllables = syllable_count / word_count
        if avg_syllables < 1.3 and word_count < 60:
            return "beginner"
        elif avg_syllables < 1.6 and word_count < 120:
            return "intermediate"
        return "advanced"


document_parser = DocumentParserService()
