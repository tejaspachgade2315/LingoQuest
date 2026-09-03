# ADR-005: Dynamic Difficulty Adjustment (DDA) & Conversational Story Comprehension

## Context & The "Nerdy" Hackathon Problem Statement

Traditional reading apps test comprehension via multiple-choice quizzes after silent reading. This approach fails to evaluate:
1. **Reading Fluency**: The speed (WCPM), accuracy, and cadence of reading out loud.
2. **Interactive Comprehension**: The student's ability to explain the plot, infer character motivations, and use vocabulary conversationally.
3. **Active Scaffolding**: Adjusting reading difficulty dynamically rather than following a static, repetitive text tree.

Nerdy (Varsity Tutors) pairs human tutors with AI superpowers. To mirror a live 1-on-1 reading specialist session, our AI companion (**Sparky**) must:
- Dynamically scale Lexile levels using established educational frameworks (**Independent $\ge 95\%$**, **Instructional $90-94\%$**, **Frustrational $< 90\%$**).
- Actively intervene with targeted phonics rules when struggling with phonetic patterns (e.g. silent 'k' in *knight*).
- Conduct periodic open-ended voice comprehension checkpoints.

---

## Architectural Decision

We implemented a unified Pedagogical Engine (`apps/voice-worker/pedagogy_engine.py`) integrated directly with the LiveKit WebRTC agent loop:

### 1. Telemetry Ingestion & Lexile Classification

When a student finishes reading a sentence, the system computes:
- **WCPM (Words Correct Per Minute)**: $\text{round}\left(\frac{\text{Words Correct}}{\text{Duration Seconds}} \times 60\right)$
- **Accuracy Percentage**: $\frac{\text{Correct Words}}{\text{Total Words}} \times 100$
- **Struggled Words**: Tracked via Levenshtein & Soundex phonetics.

```python
def classify_reading_level(accuracy_pct: float) -> str:
    if accuracy_pct >= 95.0:
        return "Independent"   # Elevate Lexile (+40L), introduce Tier-2 vocabulary
    elif accuracy_pct >= 90.0:
        return "Instructional" # The sweet spot: maintain Lexile, target key phonics
    else:
        return "Frustrational" # Drop Lexile (-40L), shorten sentences, trigger phonics rule
```

### 2. Pydantic Structured Pedagogical Generation

The LLM (Google Gemini 2.5 Flash / Groq) generates responses strictly bound to `AIReadingResponse`:
```python
class AIReadingResponse(BaseModel):
    next_story_text: str
    adjusted_lexile: str
    reading_level: str
    avatar_intervention: Optional[str]
    comprehension_question: Optional[str]
    target_vocabulary: List[str]
    scene_visual_prompt: Optional[str]
```

### 3. State Machine & Conversational Checkpoint Loop

The voice worker operates a 3-state machine:
1. `READING_FLOW`: Streaming speech-to-text forced alignment (<280ms latency).
2. `PHONICS_INTERVENTION`: Sparky pauses reading text and speaks the targeted phonics rule aloud via Cartesia TTS.
3. `COMPREHENSION_CHECK`:
   - Canvas dims into the **Story Detective Hub**.
   - Sparky speaks an open-ended question: *"Why do you think the dragon was guarding the silver chest?"*
   - Streaming STT captures the child's natural spoken voice response.
   - LLM evaluates conceptual understanding on a 1-5 Star scale with bonus XP.
   - Sparky speaks encouraging feedback, and resumes the quest!

---

## Consequences & Benefits

- **Pedagogical Alignment**: Meets actual literacy intervention standards used by reading specialists and educators.
- **True Multimodal Experience**: Switches seamlessly between high-speed forced alignment (<280ms) and natural conversational dialogue.
- **Zero Disengagement**: The student is never stuck on static passages; the narrative adapts directly to their fluency and comprehension skills.
