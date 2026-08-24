import logging
import json
import time
from fastapi import APIRouter, HTTPException, Request, Response
from livekit import api
import redis.asyncio as aioredis
from core.config import settings
from core.database import get_database
from models.schemas import LiveKitTokenRequest, LiveKitTokenResponse, WebhookTriggerPayload
from services.queue import queue_service

logger = logging.getLogger("reading-game.webhooks")
router = APIRouter()


@router.post("/token", response_model=LiveKitTokenResponse)
async def generate_livekit_token(req: LiveKitTokenRequest):
    """
    Creates an authenticated LiveKit participant token with read/write permissions
    for real-time WebRTC audio rooms, and initializes session records in MongoDB & Redis.
    """
    try:
        # Build token using LiveKit Server SDK
        token = api.AccessToken(
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
        )
        token.with_identity(req.participantName).with_name(req.participantName)
        
        # Grant permissions
        grant = api.VideoGrants(
            room_join=True,
            room=req.roomName,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        )
        token.with_grants(grant)

        if req.metadata:
            token.with_metadata(json.dumps(req.metadata))

        jwt_token = token.to_jwt()
        logger.info(f"[TOKEN-MINT] User='{req.participantName}' | Room='{req.roomName}' | Token issued successfully")

        # 1. Persist initial session record to MongoDB
        db = get_database()
        if db is not None:
            try:
                await db["sessions"].update_one(
                    {"session_id": req.roomName},
                    {
                        "$set": {
                            "session_id": req.roomName,
                            "user": req.participantName,
                            "metadata": req.metadata or {},
                            "status": "active",
                            "created_at": time.time(),
                            "accuracy_percentage": 100.0,
                            "points": 0,
                            "streak": 0,
                            "words_completed": 0,
                        }
                    },
                    upsert=True
                )
                logger.info(f"[MONGO-SAVE] Persisted session '{req.roomName}' into MongoDB 'sessions' collection.")
            except Exception as m_err:
                logger.warning(f"[MONGO-SAVE-ERR] Failed persisting to Mongo: {m_err}")

        # 2. Cache initial session state in Redis
        try:
            r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await r.hset(
                f"session:{req.roomName}",
                mapping={
                    "user": req.participantName,
                    "status": "active",
                    "storyId": (req.metadata or {}).get("storyId", "story-1"),
                    "points": "0",
                    "streak": "0",
                    "accuracy": "100.0",
                    "createdAt": str(time.time()),
                    "updatedAt": str(time.time()),
                }
            )
            # Add to set of active sessions
            await r.sadd("active_sessions", req.roomName)
            # Add to real-time events stream
            await r.xadd("stream:reading_events", {
                "event": "session_created",
                "room": req.roomName,
                "user": req.participantName,
            })
            await r.aclose()
            logger.info(f"[REDIS-SAVE] Cached session '{req.roomName}' into Redis.")
        except Exception as r_err:
            logger.warning(f"[REDIS-SAVE-ERR] Failed saving to Redis: {r_err}")

        return LiveKitTokenResponse(
            token=jwt_token,
            serverUrl=settings.NEXT_PUBLIC_LIVEKIT_URL,
            roomName=req.roomName,
            participantIdentity=req.participantName,
        )
    except Exception as e:
        logger.error(f"Error generating LiveKit token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhooks/trigger")
async def handle_outbound_trigger(payload: WebhookTriggerPayload):
    """
    Endpoint triggered by WhatsApp bot or CRM to start an outbound voice reading session.
    Enqueues the trigger to Redis Streams.
    """
    try:
        message_id = await queue_service.publish_session_trigger(
            to_number=payload.to_number,
            story_id=payload.story_id,
            reader_name=payload.reader_name,
            reading_level=payload.reading_level,
        )
        return {
            "status": "queued",
            "message_id": message_id,
            "to_number": payload.to_number,
            "story_id": payload.story_id,
        }
    except Exception as e:
        logger.error(f"Error queuing outbound session trigger: {e}")
        raise HTTPException(status_code=500, detail=str(e))
