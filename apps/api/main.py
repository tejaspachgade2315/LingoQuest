import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.database import connect_to_mongo, close_mongo_connection
from routers import webhooks, session
from services.queue import queue_service

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-7s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("reading-game.api")


import redis.asyncio as aioredis

async def init_redis_defaults():
    try:
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.set("system:status", "online")
        await r.set("app:name", "LingoQuest Kids")
        await r.zadd("zset:leaderboard", {"Pip the Owl": 150, "Leo the Brave": 120, "Luna the Fox": 90})
        await r.hset("story:catalog:story-1", mapping={"title": "The Brave Little Falcon", "level": "Beginner", "lexile": "380L"})
        await r.hset("story:catalog:story-2", mapping={"title": "Echoes of the Deep Forest", "level": "Explorer", "lexile": "420L"})
        await r.hset("story:catalog:story-3", mapping={"title": "Journey to the Obsidian Spire", "level": "Champion", "lexile": "460L"})
        await r.aclose()
        logger.info("[REDIS-INIT] Initialized Redis default catalog and leaderboard.")
    except Exception as e:
        logger.warning(f"[REDIS-INIT-ERR] {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Reading Game API Service...")
    await connect_to_mongo()
    await init_redis_defaults()
    yield
    # Shutdown
    logger.info("Shutting down Reading Game API Service...")
    await close_mongo_connection()
    await queue_service.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Reading Game Ingestion & State Server",
        description="Coordinates WebRTC LiveKit sessions, real-time word evaluation state, and telephony queues.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routers
    app.include_router(webhooks.router, prefix="/api", tags=["Webhooks & LiveKit Tokens"])
    app.include_router(session.router, prefix="/api", tags=["Reading Sessions & Passages"])

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "llm_provider": settings.LLM_PROVIDER,
            "stt_provider": settings.STT_PROVIDER,
            "tts_provider": settings.TTS_PROVIDER,
            "telephony_provider": settings.TELEPHONY_PROVIDER,
        }

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
