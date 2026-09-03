# ADR-001: WebRTC LiveKit Audio & Data Channel Architecture

## Status
Accepted

## Context
Traditional speech-evaluating education software requires the student to record an entire sentence, compress it into an audio file (e.g. MP3/WAV), upload it over HTTP POST, and wait for a server batch response. This introduces a 2000ms - 4000ms delay, destroying any illusion of a responsive game controller.

## Decision
We chose **LiveKit WebRTC** infrastructure for continuous bidirectional audio streaming and peer-to-peer data channels:
1. **Opus Audio Streaming**: Continuous UDP streaming with sub-50ms network buffering.
2. **Integrated Data Channels**: Low-overhead JSON packet dispatching (`room.local_participant.publish_data`) over SCTP/WebRTC directly to the student's browser.
3. **Decoupled Python Worker Agent**: The server-side Python voice worker acts as a WebRTC participant in the room, consuming the audio track in real time and publishing word-by-word telemetry.

## Consequences
- **Pros**: End-to-end evaluation roundtrip reduced to ~280ms. Eliminates HTTP upload overhead and file storage requirements for live gameplay.
- **Cons**: Requires continuous WebRTC connection and LiveKit cloud or self-hosted server deployment.
