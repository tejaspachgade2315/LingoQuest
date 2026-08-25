import json
import logging
import asyncio
import time
import re
import os
from typing import Optional, List, Dict
import httpx
import redis.asyncio as aioredis
from livekit import rtc
from livekit.agents import (
    JobContext,
    WorkerOptions,
    cli,
    AutoSubscribe,
    voice,
)

from core.config import settings
from fuzzy_matcher import FuzzyReadingMatcher
from adapters.llm.factory import LLMFactory
from adapters.stt.factory import STTFactory
from adapters.tts.factory import TTSFactory
from pedagogy_engine import PedagogyEngine, AIReadingResponse, ComprehensionEvaluation

logger = logging.getLogger("reading-game.voice-agent")

# Universal Story Catalog in sync with Frontend
STORY_CATALOG: Dict[str, Dict[str, str]] = {
    "story-1": {
        "title": "The Brave Little Falcon",
        "sentence": "High above the rocky ridge a young falcon named Pip spread his wings.",
    },
    "story-2": {
        "title": "Echoes of the Deep Forest",
        "sentence": "Twilight painted the tall canopy in shades of violet and emerald.",
    },
    "story-3": {
        "title": "Journey to the Obsidian Spire",
        "sentence": "Turbulent currents crashed against the jagged obsidian cliffs.",
    },
}

# Session States
STATE_READING = "READING_FLOW"
STATE_PHONICS_INTERVENTION = "PHONICS_INTERVENTION"
STATE_COMPREHENSION_CHECK = "COMPREHENSION_CHECK"


def extract_story_id(room_name: str) -> str:
    """Extracts storyId from roomName format 'reading-session-{storyId}-{timestamp}'."""
    match = re.search(r"reading-session-(story-[123])", room_name)
    if match:
        return match.group(1)
    return "story-1"


async def reading_agent_entrypoint(ctx: JobContext):
    """
    LiveKit Voice Agent entrypoint.
    Acts as an interactive, encouraging AI Reading Tutor ('Sparky')
    for young learners (ages 7+).
    """
    room_name = ctx.room.name
    logger.info(f"Starting reading agent session for room: {room_name}")

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Determine selected story from room identifier
    story_id = extract_story_id(room_name)
    selected_story = STORY_CATALOG.get(story_id, STORY_CATALOG["story-1"])
    initial_sentence_str = selected_story["sentence"]
    initial_words = initial_sentence_str.split()

    logger.info(f"[STORY-LOAD] Room='{room_name}' -> Selected='{story_id}' ({selected_story['title']})")

    # Initialize modular adapters
    stt_adapter = STTFactory.get_adapter()
    tts_adapter = TTSFactory.get_adapter()
    llm_adapter = LLMFactory.get_adapter()

    livekit_stt = stt_adapter.get_livekit_stt()
    livekit_tts = tts_adapter.get_livekit_tts()

    matcher = FuzzyReadingMatcher(initial_words)
    start_time = time.time()
    story_sentences_history = [initial_sentence_str]

    # Pedagogical Session Tracking
    current_state = STATE_READING
    sentences_read_count = 0
    sentences_since_last_check = 0
    current_lexile = "380L"
    struggled_words_history: List[str] = []
    active_comprehension_q: Optional[str] = None
    pending_next_story_text: Optional[str] = None

    # Redis Connection for persistence
    redis_conn = None
    try:
        redis_conn = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception as r_init_err:
        logger.warning(f"Could not connect to Redis: {r_init_err}")

    async def persist_game_state(
        metrics: dict,
        dda_metrics: Optional[dict] = None,
        latest_word: Optional[dict] = None,
        event_name: str = "progress",
    ):
        """Asynchronously persists real-time gameplay metrics into Redis and MongoDB."""
        try:
            # 1. Update Redis Cache, Stream & Leaderboard
            if redis_conn:
                mapping = {
                    "room": ctx.room.name,
                    "accuracy": str(metrics.get("accuracyPercentage", 100)),
                    "points": str(metrics.get("points", 0)),
                    "streak": str(metrics.get("streak", 0)),
                    "wpm": str(metrics.get("wpm", 0)),
                    "lexile": str(current_lexile),
                    "readingLevel": str(dda_metrics.get("readingLevel") if dda_metrics else "Instructional"),
                    "updatedAt": str(time.time()),
                }
                if latest_word:
                    mapping["lastWord"] = str(latest_word.get("word", ""))
                    mapping["lastStatus"] = str(latest_word.get("status", ""))

                await redis_conn.hset(f"session:{ctx.room.name}", mapping=mapping)

                stream_payload = {
                    "room": ctx.room.name,
                    "event": event_name,
                    "accuracy": str(metrics.get("accuracyPercentage", 100)),
                    "points": str(metrics.get("points", 0)),
                    "streak": str(metrics.get("streak", 0)),
                }
                if latest_word:
                    stream_payload["word"] = str(latest_word.get("word", ""))
                    stream_payload["status"] = str(latest_word.get("status", ""))
                await redis_conn.xadd("stream:reading_events", stream_payload)

                participant_name = (ctx.room.name.split("-")[-2]) if "-" in ctx.room.name else "Hero Reader"
                await redis_conn.zadd("zset:leaderboard", {participant_name: float(metrics.get("points", 0))})

            # 2. Update MongoDB via API PATCH
            api_url = os.environ.get("API_URL", "http://api:8000")
            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.patch(
                    f"{api_url}/api/sessions/{ctx.room.name}",
                    json={
                        "accuracy_score": metrics.get("accuracyPercentage", 100),
                        "points": metrics.get("points", 0),
                        "streak": metrics.get("streak", 0),
                        "wpm": metrics.get("wpm", 0),
                        "current_lexile": current_lexile,
                        "status": "in_progress",
                    },
                )
        except Exception as p_err:
            logger.debug(f"[PERSIST-ERR] Non-blocking state persist exception: {p_err}")

    is_tutor_speaking = False

    async def safe_say(text: str):
        """Safely speaks text over WebRTC track with echo suppression and status check."""
        nonlocal is_tutor_speaking
        try:
            if session and ctx.room.isconnected():
                is_tutor_speaking = True
                await session.say(text)
        except Exception as err:
            logger.warning(f"[TTS-SAY-ERR] Failed speaking '{text[:30]}...': {err}")
        finally:
            await asyncio.sleep(0.5)
            is_tutor_speaking = False

    async def broadcast_data_packet(packet: dict):
        """Sends real-time JSON packets to all connected clients over LiveKit Data Channel."""
        try:
            payload = json.dumps(packet).encode("utf-8")
            await ctx.room.local_participant.publish_data(payload, reliable=True)
            logger.info(f"[DATA-CHANNEL-TX] Type='{packet.get('type')}' | Room='{ctx.room.name}'")
        except Exception as e:
            logger.error(f"[DATA-CHANNEL-ERR] Error publishing data packet: {e}")

    # Initialize LiveKit Voice Agent & Session
    agent = voice.Agent(
        instructions=(
            "You are Sparky, a warm, patient, and joyful AI reading tutor for an 8-year-old child. "
            "You speak with an encouraging, friendly voice, celebrate effort, and make reading fun."
        ),
    )
    session = voice.AgentSession(
        stt=livekit_stt,
        tts=livekit_tts,
    )

    # Background task for detecting hesitations with gentle, patient assistance
    async def hesitation_watcher():
        while ctx.room.isconnected():
            await asyncio.sleep(0.5)
            if current_state == STATE_READING and not is_tutor_speaking:
                hint = matcher.check_hesitation(timeout_seconds=4.0)
                if hint:
                    hint_type = hint.get("type", "soundout")
                    word = hint["word"]
                    word_idx = hint["wordIndex"]

                    if hint_type == "soundout":
                        struggled_words_history.append(word)
                        logger.info(
                            f"[HESITATION-HINT] Word='{word}' (Idx={word_idx}) "
                            f"| Paused >4.0s | Soundout='{hint['soundedOut']}'"
                        )
                        await broadcast_data_packet({
                            "type": "hint_soundout",
                            "sessionId": ctx.room.name,
                            "currentWordIndex": word_idx,
                            "word": word,
                            "soundedOut": hint["soundedOut"],
                            "feedbackText": f"Let's sound it out: {word} ({hint['soundedOut']})",
                        })
                        await safe_say(
                            f"Let's sound this one out together: {hint['soundedOut']}. You try: {word}!"
                        )

                    elif hint_type == "reprompt":
                        logger.info(f"[HESITATION-NUDGE] Re-prompting for Word='{word}' (Idx={word_idx})")
                        await broadcast_data_packet({
                            "type": "hint_soundout",
                            "sessionId": ctx.room.name,
                            "currentWordIndex": word_idx,
                            "word": word,
                            "soundedOut": word,
                            "feedbackText": f"Take your time! Say: {word}!",
                        })
                        await safe_say(f"Take your time, superstar! Say: {word}, or click Skip to move on!")

    @session.on("user_input_transcribed")
    def on_user_speech(ev):
        """
        Triggered when streaming STT yields recognized text segment from the child's microphone.
        """
        nonlocal current_state, sentences_since_last_check, pending_next_story_text
        if is_tutor_speaking:
            logger.debug("Ignoring speech while tutor is speaking (echo suppression)")
            return

        msg = getattr(ev, "transcript", "")
        if not msg or not msg.strip():
            return

        child_speech = msg.strip()

        # MODE 1: COMPREHENSION CHECKPOINT (Child answers plot question conversationally)
        if current_state == STATE_COMPREHENSION_CHECK and active_comprehension_q:
            logger.info(f"[COMPREHENSION-ANSWER] Child said: \"{child_speech}\"")
            asyncio.create_task(handle_comprehension_answer(child_speech))
            return

        # MODE 2: READING FLOW (Student reading story words aloud)
        if current_state == STATE_READING:
            logger.info(f"[SPEECH-STT] Recognized child reading: \"{child_speech}\"")
            elapsed = max(1.0, time.time() - start_time)
            results = matcher.evaluate_spoken_phrase(child_speech)

            # Broadcast what Sparky heard to frontend so user has immediate live visual proof
            asyncio.create_task(
                broadcast_data_packet({
                    "type": "speech_transcribed_live",
                    "sessionId": ctx.room.name,
                    "heardSpeech": child_speech,
                })
            )

            if results:
                latest_eval = results[-1]
                metrics = matcher.get_session_metrics(elapsed)

                if latest_eval.get("status") in ("imperfect", "missed"):
                    struggled_words_history.append(latest_eval.get("word", ""))

                logger.info(
                    f"[WORD-EVAL] Target='{latest_eval.get('word')}' "
                    f"| Heard='{latest_eval.get('spokenAlternative')}' "
                    f"| Status={latest_eval.get('status')} "
                    f"| Score={latest_eval.get('similarityScore', 1.0):.2f} "
                    f"| Accuracy={metrics.get('accuracyPercentage')}% "
                    f"| Streak={metrics.get('streak', 0)}x"
                )

                asyncio.create_task(
                    broadcast_data_packet({
                        "type": "word_highlight",
                        "sessionId": ctx.room.name,
                        "currentWordIndex": matcher.current_index,
                        "evaluatedWord": latest_eval,
                        "metrics": metrics,
                        "heardSpeech": child_speech,
                        "feedbackText": f"Great reading! Streak: {metrics.get('streak', 0)}x | Score: {metrics.get('points', 0)} Stars!",
                    })
                )

                # Persist live progress into Redis & MongoDB
                asyncio.create_task(
                    persist_game_state(metrics, latest_word=latest_eval, event_name="word_evaluated")
                )

                # Check if current sentence is fully read
                if matcher.is_sentence_completed():
                    asyncio.create_task(handle_sentence_completion(metrics))

    async def handle_sentence_completion(metrics: dict):
        """
        Pedagogical DDA Trigger: When a sentence is completed by the child.
        """
        nonlocal current_state, sentences_read_count, sentences_since_last_check, current_lexile
        nonlocal active_comprehension_q, pending_next_story_text

        sentences_read_count += 1
        sentences_since_last_check += 1
        elapsed = max(1.0, time.time() - start_time)
        accuracy = metrics.get("accuracyPercentage", 100)
        wcpm = PedagogyEngine.calculate_wcpm(matcher.words_correct_count, elapsed)

        telemetry = {
            "wcpm": wcpm,
            "accuracy_percentage": accuracy,
            "struggling_words": list(set(struggled_words_history))[-5:],
            "current_lexile": current_lexile,
            "sentences_read": sentences_read_count,
        }

        logger.info(
            f"[SENTENCE-COMPLETE] SentencesRead={sentences_read_count} | WCPM={wcpm} | "
            f"Accuracy={accuracy}% | Struggled={telemetry['struggling_words']}"
        )

        # Immediate warm celebration
        praise = (
            "Woohoo! High five, superstar! You read that entire sentence like a champion!"
            if accuracy >= 85
            else "Awesome effort! You are getting stronger with every single word!"
        )
        await safe_say(praise)

        # Execute Pedagogical DDA Scaffolding Engine
        step: AIReadingResponse = await PedagogyEngine.generate_scaffolded_step(
            llm_adapter=llm_adapter,
            story_history=story_sentences_history,
            telemetry=telemetry,
            sentences_since_check=sentences_since_last_check,
        )

        logger.info(
            f"[DDA-EVAL] ReadingLevel={step.reading_level} | NewLexile={step.adjusted_lexile} | "
            f"PhonicsIntervention={bool(step.avatar_intervention)} | CompQ={bool(step.comprehension_question)}"
        )

        current_lexile = step.adjusted_lexile
        pending_next_story_text = step.next_story_text

        # DDA Metrics packet for frontend HUD
        dda_metrics = {
            "wcpm": wcpm,
            "accuracyPercentage": accuracy,
            "currentLexile": current_lexile,
            "targetVocabulary": step.target_vocabulary,
            "readingLevel": step.reading_level,
            "strugglingWords": telemetry["struggling_words"],
            "sentencesRead": sentences_read_count,
        }

        # Persist DDA sentence completion to Redis and MongoDB
        asyncio.create_task(
            persist_game_state(metrics, dda_metrics=dda_metrics, event_name="sentence_completed")
        )

        # 1. Active Phonics Rule Intervention (if student struggled with a pattern)
        if step.avatar_intervention:
            current_state = STATE_PHONICS_INTERVENTION
            logger.info(f"[PHONICS-INTERVENTION] Speaking rule: \"{step.avatar_intervention}\"")
            await broadcast_data_packet({
                "type": "phonics_rule_intervention",
                "sessionId": ctx.room.name,
                "phonicsRule": step.avatar_intervention,
                "feedbackText": step.avatar_intervention,
                "ddaMetrics": dda_metrics,
            })
            await safe_say(step.avatar_intervention)
            current_state = STATE_READING

        # 2. Comprehension Checkpoint (Triggered every 3 sentences)
        if step.comprehension_question:
            current_state = STATE_COMPREHENSION_CHECK
            active_comprehension_q = step.comprehension_question
            sentences_since_last_check = 0

            logger.info(f"[COMPREHENSION-PROMPT] Asking question: \"{active_comprehension_q}\"")

            await broadcast_data_packet({
                "type": "comprehension_question_prompt",
                "sessionId": ctx.room.name,
                "comprehensionQuestion": {
                    "id": f"cq-{sentences_read_count}",
                    "question": active_comprehension_q,
                    "targetConcept": "Plot Recall & Inference",
                    "storyContext": " ".join(story_sentences_history[-2:]),
                },
                "ddaMetrics": dda_metrics,
                "feedbackText": f"Question time! {active_comprehension_q}",
            })

            await safe_say(f"Quick detective question: {active_comprehension_q}")
            return

        # 3. Seamless Story Progression (Standard Loop)
        await advance_to_next_sentence(step.next_story_text, dda_metrics)

    async def handle_comprehension_answer(child_answer: str):
        """Evaluates child's natural spoken explanation of the story plot."""
        nonlocal current_state, active_comprehension_q, pending_next_story_text

        story_context = " ".join(story_sentences_history[-2:])
        question = active_comprehension_q or "What happened in the story?"

        # Evaluate answer via LLM
        eval_result: ComprehensionEvaluation = await PedagogyEngine.evaluate_comprehension(
            llm_adapter=llm_adapter,
            story_context=story_context,
            question=question,
            child_answer=child_answer,
        )

        logger.info(
            f"[COMPREHENSION-SCORED] Score={eval_result.score}/5 | Passed={eval_result.passed} | "
            f"BonusXP=+{eval_result.bonus_xp} | Feedback=\"{eval_result.tutor_feedback}\""
        )

        # Broadcast score & bonus to frontend
        await broadcast_data_packet({
            "type": "comprehension_eval_result",
            "sessionId": ctx.room.name,
            "comprehensionEval": eval_result.dict(),
            "feedbackText": eval_result.tutor_feedback,
        })

        # Persist comprehension evaluation to Redis and MongoDB
        metrics = matcher.get_session_metrics(time.time() - start_time)
        metrics["points"] = (metrics.get("points", 0)) + eval_result.bonus_xp
        asyncio.create_task(
            persist_game_state(metrics, event_name="comprehension_scored")
        )

        # Speak warm celebration feedback
        await safe_say(eval_result.tutor_feedback)

        # Brief pause for celebration display before resuming story quest
        await asyncio.sleep(2.5)

        # Resume reading flow with next sentence
        current_state = STATE_READING
        active_comprehension_q = None
        next_text = pending_next_story_text or "The intrepid adventurer marched forward into the enchanted realm."
        await advance_to_next_sentence(next_text)

    async def advance_to_next_sentence(next_sentence: str, dda_metrics: Optional[dict] = None):
        """Advances story to next sentence and re-arms word matcher."""
        nonlocal story_sentences_history

        next_sentence = next_sentence.replace('"', '').replace('\n', ' ').strip()
        story_sentences_history.append(next_sentence)
        new_words = next_sentence.split()

        logger.info(f"[DUNGEON-MASTER-ADVANCE] Next sentence: \"{next_sentence}\"")
        matcher.set_new_sentence(new_words)

        await broadcast_data_packet({
            "type": "story_advanced",
            "sessionId": ctx.room.name,
            "sentence": next_sentence,
            "words": new_words,
            "currentWordIndex": 0,
            "feedbackText": "The story advances! Read the next sentence aloud!",
            "metrics": matcher.get_session_metrics(time.time() - start_time),
            "ddaMetrics": dda_metrics,
        })

    # Listen for client data channel requests
    @ctx.room.on("data_received")
    def on_data_received(data_packet: rtc.DataPacket):
        nonlocal current_state
        try:
            payload = json.loads(data_packet.data.decode("utf-8"))
            req_type = payload.get("type")

            if req_type == "request_soundout":
                curr_word = matcher.words[matcher.current_index] if matcher.current_index < len(matcher.words) else ""
                if curr_word:
                    sounded = matcher.sound_out_word(curr_word)
                    logger.info(f"[USER-SOUNDOUT] Manual soundout requested for '{curr_word}' -> '{sounded}'")
                    asyncio.create_task(broadcast_data_packet({
                        "type": "hint_soundout",
                        "sessionId": ctx.room.name,
                        "currentWordIndex": matcher.current_index,
                        "word": curr_word,
                        "soundedOut": sounded,
                        "feedbackText": f"Let's sound it out: {curr_word} ({sounded})",
                    }))
                    asyncio.create_task(safe_say(f"Here is how you say it: {sounded}. You try: {curr_word}!"))

            elif req_type == "skip_word":
                missed = matcher.skip_current_word()
                if missed:
                    logger.info(f"[USER-SKIP-WORD] Skipped word='{missed['word']}' (NewIdx={matcher.current_index})")
                    metrics = matcher.get_session_metrics(time.time() - start_time)
                    asyncio.create_task(broadcast_data_packet({
                        "type": "word_highlight",
                        "sessionId": ctx.room.name,
                        "currentWordIndex": matcher.current_index,
                        "evaluatedWord": missed,
                        "metrics": metrics,
                    }))
                    if matcher.is_sentence_completed():
                        asyncio.create_task(handle_sentence_completion(metrics))

            elif req_type == "skip_comprehension":
                logger.info("[USER-SKIP-COMPREHENSION] Client skipped comprehension checkpoint.")
                if current_state == STATE_COMPREHENSION_CHECK:
                    current_state = STATE_READING
                    next_text = pending_next_story_text or "The courageous traveler continued down the winding trail."
                    asyncio.create_task(advance_to_next_sentence(next_text))

        except Exception as e:
            logger.error(f"Error handling client data packet: {e}")

    # Start session in room
    await session.start(agent, room=ctx.room)

    # Initial broadcast and warm AI Tutor greeting
    await asyncio.sleep(0.5)
    await broadcast_data_packet({
        "type": "story_advanced",
        "sessionId": ctx.room.name,
        "sentence": initial_sentence_str,
        "words": initial_words,
        "currentWordIndex": 0,
        "feedbackText": f"Hi there! Read the glowing word out loud: '{initial_words[0]}'",
        "metrics": matcher.get_session_metrics(0.1),
        "ddaMetrics": {
            "wcpm": 0,
            "accuracyPercentage": 100,
            "currentLexile": current_lexile,
            "readingLevel": "Instructional",
            "strugglingWords": [],
            "sentencesRead": 0,
        },
    })

    # AI Tutor speaks warm welcome
    welcome_greeting = f"Hi there, little reader! I'm Sparky, your reading buddy! Read the glowing word out loud whenever you are ready!"
    await safe_say(welcome_greeting)

    # Arm hesitation watcher only after greeting finishes speaking
    matcher.last_advance_time = time.time()
    hesitation_task = asyncio.create_task(hesitation_watcher())

    while ctx.room.isconnected():
        await asyncio.sleep(1)

    hesitation_task.cancel()
    if redis_conn:
        await redis_conn.aclose()


def run_agent():
    """Runs the LiveKit agent worker loop."""
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=reading_agent_entrypoint,
            ws_url=settings.effective_livekit_url,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
        )
    )
