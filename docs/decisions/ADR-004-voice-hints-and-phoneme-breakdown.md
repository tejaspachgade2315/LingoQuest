# ADR-004: Hesitation Detection & Expressive TTS Phonetic Sound-Out

## Status
Accepted

## Context
When a young reader struggles with a word, sitting in complete silence induces anxiety and stalls the gameplay. Human teachers intervene after 3 to 4 seconds by sounding out difficult phonemes (e.g. "k - n - i - g - h - t. knight!").

## Decision
We implemented an active hesitation watcher in the Voice Worker:
1. **Silence / Hesitation Timer**: If the reader has not advanced past the current target word for $> 3.0$ seconds:
2. **Phonetic Decomposition**: The target word is decomposed into segmented sounds (e.g. "k - n - i - g - h - t" or syllables).
3. **Low-Latency Voice Synthesis**: Cartesia Sonic English (<100ms TTFB) is invoked to speak a gentle hint: `"Try this word: k - n - i - g - h - t. knight!"`
4. **Visual Cue Card**: A phoneme guidance card is broadcast to the web client via the LiveKit data channel, displaying the sounded-out letters directly above the highlighted word.

## Consequences
- **Pros**: Emulates human tutoring pedagogy, prevents frustration, and maintains game flow.
- **Cons**: Requires suppression mechanisms so the tutor voice does not feed back into the STT recognizer (handled by LiveKit echo cancellation and agent speech state flags).
