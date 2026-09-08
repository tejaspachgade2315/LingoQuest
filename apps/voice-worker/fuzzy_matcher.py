import re
import time
import Levenshtein
from typing import List, Dict, Any, Optional, Tuple


class FuzzyReadingMatcher:
    """
    Word-level reading evaluation algorithm.
    Compares real-time streaming STT transcript tokens against the target passage words,
    using Levenshtein distance, acoustic/phonetic heuristics, and child-friendly tolerance.
    Includes gentle, non-intrusive sound-out hints that coach the reader without ever
    prematurely skipping words or interrupting their reading flow.
    """

    def __init__(self, target_words: List[str]):
        self.target_words = target_words
        self.normalized_targets = [self._normalize(w) for w in target_words]
        self.current_index = 0
        self.evaluated_words: Dict[int, Dict[str, Any]] = {}
        self.last_advance_time: float = time.time()
        self.consecutive_streak: int = 0
        self.highest_streak: int = 0
        self.total_points: int = 0
        self.hesitation_tier: int = 0  # 0: none, 1: soundout, 2: gentle nudge

    @property
    def words(self) -> List[str]:
        """Alias for target_words for backward-compatibility."""
        return self.target_words

    @property
    def words_correct_count(self) -> int:
        """Counts how many words have been evaluated as correct in the current sentence."""
        return sum(1 for e in self.evaluated_words.values() if e.get("status") == "correct")

    @staticmethod
    def _normalize(word: str) -> str:
        """Strip punctuation and lowercase."""
        return re.sub(r'[^a-zA-Z0-9]', '', word).lower()

    @staticmethod
    def sound_out_word(word: str) -> str:
        """
        Creates a phonetically spaced representation for TTS sound-out.
        e.g. 'falcon' -> 'f, a, l, c, o, n. falcon!'
        """
        cleaned = re.sub(r'[^a-zA-Z]', '', word).lower()
        if not cleaned:
            return word
        if len(cleaned) <= 6:
            spaced = ", ".join(list(cleaned))
            return f"{spaced}. {cleaned}!"
        else:
            chunks = [cleaned[i:i+3] for i in range(0, len(cleaned), 3)]
            spaced = ", ".join(chunks)
            return f"{spaced}. {cleaned}!"

    @staticmethod
    def _phonetic_key(word: str) -> str:
        """
        Lightweight Soundex-inspired phonetic reduction key for speech matching.
        """
        w = re.sub(r'[^a-zA-Z]', '', word).upper()
        if not w:
            return ""
        first = w[0]
        mapping = {
            'B': '1', 'F': '1', 'P': '1', 'V': '1',
            'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
            'D': '3', 'T': '3',
            'L': '4',
            'M': '5', 'N': '5',
            'R': '6',
        }
        res = [first]
        prev = mapping.get(first, '0')
        for char in w[1:]:
            code = mapping.get(char, '0')
            if code != '0' and code != prev:
                res.append(code)
            prev = code
        return "".join(res[:4]).ljust(4, '0')

    def reset_hesitation_timer(self) -> None:
        """Resets the hesitation clock after the tutor delivers a hint or prompt."""
        self.last_advance_time = time.time()

    def check_hesitation(self, timeout_seconds: float = 7.0) -> Optional[Dict[str, Any]]:
        """
        Gentle hesitation detection that assists without taking control away from the child:
        - Tier 1 (7.0s pause): Sound out the word phonetically to coach them.
        - Tier 2 (18.0s pause): Friendly encouragement nudge ("Take your time! Say: ...").
        NEVER skips or advances the word automatically on a timer. The student remains in control.
        """
        if self.current_index >= len(self.target_words):
            return None

        elapsed = time.time() - self.last_advance_time
        current_word = self.target_words[self.current_index]

        if elapsed >= 18.0 and self.hesitation_tier < 2:
            self.hesitation_tier = 2
            return {
                "type": "reprompt",
                "wordIndex": self.current_index,
                "word": current_word,
                "hintText": f"Take your time! Say: {current_word}, or click Skip to move on!",
            }
        elif elapsed >= timeout_seconds and self.hesitation_tier < 1:
            self.hesitation_tier = 1
            sounded_out = self.sound_out_word(current_word)
            return {
                "type": "soundout",
                "wordIndex": self.current_index,
                "word": current_word,
                "soundedOut": sounded_out,
                "hintText": f"Sound it out: {sounded_out}",
            }
        return None

    def evaluate_spoken_phrase(self, spoken_text: str) -> List[Dict[str, Any]]:
        """
        Processes streaming speech tokens and sequentially matches upcoming target words.
        Only advances when the child actually speaks a matching pronunciation
        (as correct or imperfect). Never advances on silence or non-matching chatter.
        """
        spoken_tokens = [self._normalize(w) for w in spoken_text.split() if self._normalize(w)]
        if not spoken_tokens:
            return []

        results = []

        # Progressively match targets from current_index forward
        while self.current_index < len(self.target_words):
            target = self.normalized_targets[self.current_index]
            target_raw = self.target_words[self.current_index]

            best_sim = 0.0
            best_token = ""
            best_status = "missed"

            for token in spoken_tokens:
                sim, status = self._score_word(token, target)
                if sim > best_sim:
                    best_sim = sim
                    best_token = token
                    best_status = status

            # If target word is recognized as correct or imperfect, record & advance
            if best_status in ("correct", "imperfect"):
                evaluation = {
                    "index": self.current_index,
                    "word": target_raw,
                    "normalized": target,
                    "status": best_status,
                    "similarityScore": round(best_sim, 2),
                    "spokenAlternative": best_token,
                }
                self.evaluated_words[self.current_index] = evaluation
                results.append(evaluation)

                if best_status == "correct":
                    self.consecutive_streak += 1
                    self.highest_streak = max(self.highest_streak, self.consecutive_streak)
                    self.total_points += 10 + (self.consecutive_streak * 2)
                else:
                    self.consecutive_streak = 0
                    self.total_points += 5

                self.current_index += 1
                self.last_advance_time = time.time()
                self.hesitation_tier = 0
            else:
                # Target word has not been spoken; wait patiently for child to speak it
                break

        return results

    def skip_current_word(self) -> Optional[Dict[str, Any]]:
        """Explicitly marks the current word as skipped/missed and advances (triggered by user button)."""
        if self.current_index < len(self.target_words):
            idx = self.current_index
            target_raw = self.target_words[idx]
            target_norm = self.normalized_targets[idx]
            missed_word = {
                "index": idx,
                "word": target_raw,
                "normalized": target_norm,
                "status": "missed",
                "similarityScore": 0.0,
                "spokenAlternative": "(skipped)",
            }
            self.evaluated_words[idx] = missed_word
            self.consecutive_streak = 0
            self.current_index += 1
            self.last_advance_time = time.time()
            self.hesitation_tier = 0
            return missed_word
        return None

    def _score_word(self, spoken: str, target: str) -> Tuple[float, str]:
        """
        Calculates similarity with child-friendly phonetic and edit distance tolerance.
        """
        if not spoken or not target:
            return 0.0, "missed"

        if spoken == target:
            return 1.0, "correct"

        lev_ratio = Levenshtein.ratio(spoken, target)
        dist = Levenshtein.distance(spoken, target)

        # Initial letter match bonus (children typically nail the starting consonant)
        initial_match = spoken[0] == target[0]
        initial_bonus = 0.12 if initial_match else 0.0

        # Phonetic matching bonus
        same_phonetic = self._phonetic_key(spoken) == self._phonetic_key(target)
        phonetic_bonus = 0.15 if same_phonetic else 0.0

        # Soft-G / Suffix pattern: 'ridge' sounds like /rɪdʒ/, often heard as 'read', 'ragic', 'rich'
        soft_g_match = target.endswith(('dge', 'ge')) and spoken.endswith(('d', 'ch', 'c', 'g', 'sh', 'ic', 'tch'))

        combined_score = min(1.0, lev_ratio + phonetic_bonus + initial_bonus)

        # Lenient evaluation rules for young learners:
        # 1. Exact or single edit off -> correct
        if combined_score >= 0.78 or dist <= 1:
            status = "correct"
        # 2. Plausible attempt (edit distance <= 2 with same initial letter, soft-g, or phonetic)
        elif (
            combined_score >= 0.48
            or (initial_match and dist <= 2)
            or (initial_match and soft_g_match and len(spoken) >= 3)
            or (same_phonetic and len(spoken) >= 3)
        ):
            status = "imperfect"
        else:
            status = "missed"

        return combined_score, status

    def set_new_sentence(self, new_words: List[str]) -> None:
        """Sets a dynamically generated sentence from the LLM Dungeon Master."""
        self.target_words = new_words
        self.normalized_targets = [self._normalize(w) for w in new_words]
        self.current_index = 0
        self.evaluated_words.clear()
        self.last_advance_time = time.time()
        self.hesitation_tier = 0

    def is_sentence_completed(self) -> bool:
        return self.current_index >= len(self.target_words)

    def get_session_metrics(self, elapsed_seconds: float = 1.0) -> Dict[str, Any]:
        total = len(self.target_words)
        correct = sum(1 for e in self.evaluated_words.values() if e.get("status") == "correct")
        imperfect = sum(1 for e in self.evaluated_words.values() if e.get("status") == "imperfect")
        missed = sum(1 for e in self.evaluated_words.values() if e.get("status") == "missed")

        evaluated_count = len(self.evaluated_words)
        accuracy = ((correct + imperfect * 0.7) / max(1, evaluated_count)) * 100

        minutes = max(0.01, elapsed_seconds / 60.0)
        wpm = (correct + imperfect) / minutes

        return {
            "totalWords": total,
            "correctWords": correct,
            "imperfectWords": imperfect,
            "missedWords": missed,
            "accuracyPercentage": round(accuracy, 1),
            "wpm": round(wpm, 1),
            "readingDurationSeconds": round(elapsed_seconds, 1),
            "streak": self.consecutive_streak,
            "highestStreak": self.highest_streak,
            "points": self.total_points,
        }
