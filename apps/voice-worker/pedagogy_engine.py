"""
Pedagogical Engine for Dynamic Difficulty Adjustment (DDA),
Phonics Interventions, and Conversational Story Comprehension.

Aligns with the Varsity Tutors (Nerdy) 1-on-1 reading specialist model:
- WCPM (Words Correct Per Minute) & Accuracy evaluation
- Lexile scaffolding: Independent (>=95%), Instructional (90-94%), Frustrational (<90%)
- Targeted phonics rule interventions
- Open-ended plot comprehension checks
"""

import json
import logging
import re
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

logger = logging.getLogger("voice-worker.pedagogy")


class AIReadingResponse(BaseModel):
    next_story_text: str = Field(
        description="The next 1-2 sentences of the narrative, strictly adhering to the target Lexile complexity."
    )
    adjusted_lexile: str = Field(
        default="400L",
        description="The new Lexile level (e.g., '350L', '420L') adjusted based on student accuracy."
    )
    reading_level: str = Field(
        default="Instructional",
        description="One of: 'Independent', 'Instructional', 'Frustrational'."
    )
    avatar_intervention: Optional[str] = Field(
        default=None,
        description="Short encouraging phonics rule script if accuracy < 90% or child struggled with a phonetic pattern."
    )
    comprehension_question: Optional[str] = Field(
        default=None,
        description="Open-ended conversational plot question. Triggered when sentences_since_last_check >= 3."
    )
    target_vocabulary: List[str] = Field(
        default_factory=list,
        description="2-3 sight words or phonetic target words introduced in next_story_text."
    )
    scene_visual_prompt: Optional[str] = Field(
        default=None,
        description="A vivid scene description for generative UI backdrops."
    )


class ComprehensionEvaluation(BaseModel):
    score: int = Field(
        default=5,
        description="1 to 5 stars comprehension score."
    )
    passed: bool = Field(
        default=True,
        description="True if student understood the plot/inference."
    )
    tutor_feedback: str = Field(
        default="Spot on, superstar! You understand this story like a true detective!",
        description="Warm, spoken feedback from Sparky to the child."
    )
    bonus_xp: int = Field(
        default=100,
        description="Bonus XP points awarded (50 to 100 XP)."
    )
    child_answer: Optional[str] = None


class PedagogyEngine:
    """Orchestrates educational literacy rules and LLM generation."""

    @staticmethod
    def calculate_wcpm(words_correct: int, duration_seconds: float) -> int:
        """Calculates Words Correct Per Minute (WCPM)."""
        duration = max(duration_seconds, 1.0)
        return int(round((words_correct / duration) * 60))

    @staticmethod
    def classify_reading_level(accuracy_pct: float) -> str:
        """Classifies literacy mastery into established pedagogical tiers."""
        if accuracy_pct >= 95.0:
            return "Independent"
        elif accuracy_pct >= 90.0:
            return "Instructional"
        else:
            return "Frustrational"

    @classmethod
    async def generate_scaffolded_step(
        cls,
        llm_adapter,
        story_history: List[str],
        telemetry: Dict[str, Any],
        sentences_since_check: int,
    ) -> AIReadingResponse:
        """
        Generates the next story step using DDA and structured pedagogical guidance.
        """
        accuracy = telemetry.get("accuracy_percentage", 100)
        reading_level = cls.classify_reading_level(accuracy)
        struggled_words = telemetry.get("struggling_words", [])
        current_lexile = telemetry.get("current_lexile", "400L")

        system_instruction = (
            "You are an expert AI Reading Specialist and Interactive Storyteller (named Sparky) for a 7-9 year old child. "
            "You dynamically scaffold reading difficulty and story adventure based on student telemetry.\n\n"
            "Pedagogical Rules:\n"
            "1. DYNAMIC DIFFICULTY ADJUSTMENT (DDA):\n"
            "   - If Accuracy >= 95% (Independent): Elevate Lexile (+40L). Introduce rich adventure adjectives or a compound sentence.\n"
            "   - If Accuracy is 90%-94% (Instructional): Maintain current Lexile. Target engaging 8-12 word sentence.\n"
            "   - If Accuracy < 90% (Frustrational): Lower Lexile (-40L). Use short, high-frequency sight words and decodable phonics.\n\n"
            "2. PHONICS COPILOT INTERVENTION:\n"
            f"   - Struggled Words: {struggled_words}\n"
            "   - If the student struggled with tricky words (e.g., silent 'k' in 'knight', 'igh' in 'night', or vowel digraphs like 'boat'), "
            "write a friendly 1-sentence `avatar_intervention` explaining the rule.\n"
            "   - Example: \"Did you know that when 'k' and 'n' start a word together, the 'k' is silent? Say it with me: knight!\"\n\n"
            "3. COMPREHENSION CHECKPOINT:\n"
            f"   - Sentences since last check: {sentences_since_check}\n"
            "   - If sentences_since_last_check >= 3, generate an open-ended `comprehension_question` testing plot recall or inference. "
            "Keep it fun and friendly (e.g., 'Why do you think Pip the falcon wanted to spread his wings?').\n\n"
            "Output MUST be valid JSON conforming exactly to this structure:\n"
            "{\n"
            '  "next_story_text": "The sentence to read.",\n'
            '  "adjusted_lexile": "420L",\n'
            f'  "reading_level": "{reading_level}",\n'
            '  "avatar_intervention": null,\n'
            '  "comprehension_question": null,\n'
            '  "target_vocabulary": ["falcon", "wings"],\n'
            '  "scene_visual_prompt": "Golden sunrise above a rocky mountain cliff with a flying falcon."\n'
            "}"
        )

        prompt = (
            f"Story Context so far: {' -> '.join(story_history[-3:])}\n"
            f"Student Telemetry: Accuracy={accuracy}%, Level={reading_level}, WCPM={telemetry.get('wcpm', 0)}, "
            f"CurrentLexile={current_lexile}, StruggledWords={struggled_words}, SentencesSinceCheck={sentences_since_check}.\n"
            "Generate next scaffolded reading step as JSON:"
        )

        try:
            raw_response = await llm_adapter.generate_response(prompt, system_instruction=system_instruction)
            logger.info(f"[PEDAGOGY-LLM-RAW] {raw_response[:180]}...")

            # Clean markdown JSON wraps if present
            cleaned = re.sub(r"^```json\s*", "", raw_response.strip(), flags=re.IGNORECASE)
            cleaned = re.sub(r"```$", "", cleaned.strip()).strip()

            data = json.loads(cleaned)
            return AIReadingResponse(**data)
        except Exception as e:
            logger.warning(f"[PEDAGOGY-FALLBACK] Failed parsing structured response ({e}). Using resilient fallback.")
            return cls._fallback_response(accuracy, reading_level, sentences_since_check)

    @classmethod
    async def evaluate_comprehension(
        cls,
        llm_adapter,
        story_context: str,
        question: str,
        child_answer: str,
    ) -> ComprehensionEvaluation:
        """
        Evaluates the child's natural voice answer for plot recall, inference, and vocabulary understanding.
        """
        system_instruction = (
            "You are Sparky, an encouraging AI Reading Specialist for an 8-year-old child. "
            "You evaluate children's spoken answers to story comprehension questions.\n\n"
            "Evaluation Guidelines:\n"
            "1. Children use simple, spoken language. Be warm, generous, and validating.\n"
            "2. Score 5: Understood the plot and provided thoughtful explanation or inference.\n"
            "3. Score 4: Understood the key idea with simple wording.\n"
            "4. Score 3: Partially understood; give gentle guidance.\n"
            "5. Passed is true if Score >= 3.\n"
            "6. 'tutor_feedback' MUST be a warm 1-2 sentence spoken script celebrating their answer.\n\n"
            "Output JSON format:\n"
            "{\n"
            '  "score": 5,\n'
            '  "passed": true,\n'
            '  "tutor_feedback": "Spot on, detective! You knew exactly why the dragon was friendly!",\n'
            '  "bonus_xp": 100\n'
            "}"
        )

        prompt = (
            f"Story context: {story_context}\n"
            f"Question asked to child: {question}\n"
            f"Child's spoken voice answer: \"{child_answer}\"\n"
            "Evaluate comprehension as JSON:"
        )

        try:
            raw = await llm_adapter.generate_response(prompt, system_instruction=system_instruction)
            cleaned = re.sub(r"^```json\s*", "", raw.strip(), flags=re.IGNORECASE)
            cleaned = re.sub(r"```$", "", cleaned.strip()).strip()
            data = json.loads(cleaned)
            data["child_answer"] = child_answer
            return ComprehensionEvaluation(**data)
        except Exception as e:
            logger.warning(f"[COMPREHENSION-EVAL-FALLBACK] LLM eval failed ({e}).")
            return ComprehensionEvaluation(
                score=5,
                passed=True,
                tutor_feedback="High five, reading detective! That was a wonderful observation!",
                bonus_xp=100,
                child_answer=child_answer,
            )

    @staticmethod
    def _fallback_response(accuracy: float, level: str, sentences_since_check: int) -> AIReadingResponse:
        """Resilient fallback if LLM JSON generation encounters unexpected format."""
        should_ask_q = sentences_since_check >= 3
        return AIReadingResponse(
            next_story_text="A friendly baby dragon smiled and revealed a shining golden key.",
            adjusted_lexile="410L" if accuracy >= 90 else "360L",
            reading_level=level,
            avatar_intervention="Great effort! Remember to take your time on long words." if accuracy < 90 else None,
            comprehension_question="What do you think this golden key might open?" if should_ask_q else None,
            target_vocabulary=["dragon", "golden", "key"],
            scene_visual_prompt="A cheerful small green dragon sitting near a glowing stone doorway.",
        )
