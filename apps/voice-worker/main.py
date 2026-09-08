import sys
import os
import json
import asyncio
import logging
import redis.asyncio as aioredis
from typing import Optional

# Pre-register LiveKit plugins on the main thread during module load
try:
    from livekit.plugins import deepgram
except ImportError:
    deepgram = None

try:
    from livekit.plugins import cartesia
except ImportError:
    cartesia = None

try:
    from livekit.plugins import openai
except ImportError:
    openai = None

try:
    from livekit.plugins import google
except ImportError:
    google = None

from core.config import settings
from adapters.telephony.factory import TelephonyFactory
from agent import reading_agent_entrypoint
from livekit.agents import WorkerOptions, JobProcess, cli

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-7s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("voice-worker.main")


def prewarm(proc: JobProcess):
    """Pre-register plugins on the main thread of newly initialized worker processes."""
    try:
        from livekit.plugins import deepgram
    except ImportError:
        pass
    try:
        from livekit.plugins import cartesia
    except ImportError:
        pass


async def run_redis_consumer():
    """
    Background worker listening to Redis Stream 'stream:reading_sessions'
    for telephony outbound call triggers.
    """
    logger.info(f"Connecting to Redis Stream at {settings.REDIS_URL}...")
    try:
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        stream_name = settings.STREAM_NAME
        group_name = settings.CONSUMER_GROUP
        consumer_name = settings.CONSUMER_NAME

        # Create consumer group if not already present
        try:
            await r.xgroup_create(stream_name, group_name, id="0", mkstream=True)
            logger.info(f"Created consumer group '{group_name}' for stream '{stream_name}'")
        except Exception:
            pass  # Group already exists

        telephony_adapter = TelephonyFactory.get_adapter()

        logger.info(f"Consumer '{consumer_name}' started reading from '{stream_name}'...")
        while True:
            try:
                # Read new entries
                streams = await r.xreadgroup(
                    group_name,
                    consumer_name,
                    {stream_name: ">"},
                    count=1,
                    block=3000,
                )
                if not streams:
                    await asyncio.sleep(0.5)
                    continue

                for _, messages in streams:
                    for message_id, fields in messages:
                        event = fields.get("event")
                        payload_raw = fields.get("payload", "{}")
                        payload = json.loads(payload_raw)
                        logger.info(f"Processing Redis event: {event} | ID: {message_id}")

                        if event == "initiate_telephony_call":
                            to_num = payload.get("to_number", "")
                            room_name = f"telephony-room-{message_id}"
                            await telephony_adapter.dial_outbound(to_num, room_name, payload)

                        # Acknowledge message in Redis stream
                        await r.xack(stream_name, group_name, message_id)

            except Exception as e:
                logger.error(f"Error in Redis consumer loop: {e}")
                await asyncio.sleep(2)

    except Exception as e:
        logger.warning(f"Redis not available for consumer: {e}. Running in standalone mode.")


def main():
    """
    Main entrypoint. Can be run with LiveKit CLI commands:
    python main.py start
    python main.py dev
    """
    logger.info(f"Starting Voice Worker with providers: LLM={settings.LLM_PROVIDER}, STT={settings.STT_PROVIDER}, TTS={settings.TTS_PROVIDER}, Telephony={settings.TELEPHONY_PROVIDER}")

    # Start background Redis consumer in async loop if starting agent
    worker_options = WorkerOptions(
        entrypoint_fnc=reading_agent_entrypoint,
        prewarm_fnc=prewarm,
        ws_url=settings.effective_livekit_url,
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET,
    )
    cli.run_app(worker_options)


if __name__ == "__main__":
    main()
