# ADR-002: Word-Level Phonetic Fuzzy Matching Algorithm

## Status
Accepted

## Context
Children often speak with high pitch, non-standard cadence, slight regional accents, or background noise. Exact literal string matching between the ASR transcript and target text causes false negatives (e.g. child says "c-a-v-e" and ASR transcribes "caves" or "gave").

## Decision
We implemented a multi-stage fuzzy evaluation engine (`FuzzyReadingMatcher`) combining:
1. **Punctuation Normalization**: Strips quotation marks, periods, commas, and normalizes casing.
2. **Levenshtein Distance Ratio**: Computes edit distance similarity ($0.0 \dots 1.0$).
3. **Soundex Phonetic Reduction**: Maps consonant sound groups (e.g. B/F/P/V, C/G/J/K/S). If the spoken token shares phonetic sound patterns with the target word, a phonetic bonus (+0.15) is applied.
4. **Scoring Thresholds**:
   - $\ge 0.82$: Marked as `correct` (green glow, advances word, increments streak).
   - $0.60 \dots 0.81$: Marked as `imperfect` (amber highlight, advances word, half points).
   - $< 0.60$: Evaluates 1-word lookahead (checks if child skipped the word). If lookahead matches, marks skipped word as `missed` without crashing the game loop.

## Consequences
- **Pros**: Resilient against imperfect ASR transcriptions for young children while maintaining educational rigor.
- **Cons**: Extremely accented edge-cases might require customized phoneme dictionaries for non-English native learners.
