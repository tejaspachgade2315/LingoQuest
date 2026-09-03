# ADR-003: Generative Dungeon Master Storytelling

## Status
Accepted

## Context
Static reading passages become repetitive and fail to adapt to varying reading levels within the same grade. When children encounter passages that are too difficult, they disengage; when too easy, they get bored.

## Decision
We implemented a dynamic storytelling loop where an LLM (Google Gemini 2.5 Flash via GCP Vertex AI, or Groq) acts as a real-time Dungeon Master:
1. **Sentence Completion Trigger**: Upon completing sentence $N$, the agent evaluates the child's accuracy score and hesitation frequency.
2. **Pedagogical Prompt Constraints**:
   - Word count constraint: strictly 10 to 16 words.
   - Adaptive difficulty: If accuracy $\ge 85\%$, introduce richer descriptive vocabulary. If $< 70\%$, utilize high-frequency sight words.
   - Narrative coherence: Keeps rolling context of the last 3 sentences.
3. **Dynamic Canvas Replacement**: The generated sentence replaces the active canvas in the Next.js frontend, updating words and resetting word indices seamlessly.

## Consequences
- **Pros**: Endless replayability, personalized difficulty scaling, and high immersion.
- **Cons**: Requires LLM latency to remain under 800ms between sentences (achieved via Gemini 2.5 Flash / Groq Llama 3).
