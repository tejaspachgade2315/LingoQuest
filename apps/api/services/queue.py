import logging
import json
import redis.asyncio as aioredis
from typing import Dict, Any, Optional
from core.config import settings

logger = logging.getLogger("reading-game.queue")


class RedisQueueService:
    def __init__(self, redis_url: str = settings.REDIS_URL):
        self.redis_url = redis_url
        self._client: Optional[aioredis.Redis] = None
        self.stream_name = "stream:reading_sessions"

    async def get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def dispatch_session_event(self, event_name: str, payload: Dict[str, Any]) -> str:
        """
        Dispatches an event to the Redis Stream via XADD.
        """
        client = await self.get_client()
        message_data = {
            "event": event_name,
            "payload": json.dumps(payload),
        }
        try:
            entry_id = await client.xadd(self.stream_name, message_data)
            logger.info(f"Dispatched event {event_name} to stream {self.stream_name} with ID {entry_id}")
            return entry_id
        except Exception as e:
            logger.error(f"Failed to publish to Redis stream {self.stream_name}: {e}")
            raise e

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None


queue_service = RedisQueueService()
