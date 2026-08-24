import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from core.config import settings

logger = logging.getLogger("reading-game.database")

DEFAULT_PASSAGES = [
    {
        "story_id": "story-1",
        "title": "The Brave Little Falcon",
        "level": "Beginner",
        "lexile": "380L",
        "text": "High above the rocky ridge a young falcon named Pip spread his wings.",
        "words": ["High", "above", "the", "rocky", "ridge", "a", "young", "falcon", "named", "Pip", "spread", "his", "wings."],
    },
    {
        "story_id": "story-2",
        "title": "Echoes of the Deep Forest",
        "level": "Explorer",
        "lexile": "420L",
        "text": "Twilight painted the tall canopy in shades of violet and emerald.",
        "words": ["Twilight", "painted", "the", "tall", "canopy", "in", "shades", "of", "violet", "and", "emerald."],
    },
    {
        "story_id": "story-3",
        "title": "Journey to the Obsidian Spire",
        "level": "Champion",
        "lexile": "460L",
        "text": "Turbulent currents crashed against the jagged obsidian cliffs.",
        "words": ["Turbulent", "currents", "crashed", "against", "the", "jagged", "obsidian", "cliffs."],
    },
]


class Database:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


db_instance = Database()


async def connect_to_mongo() -> None:
    try:
        logger.info(f"Connecting to MongoDB at {settings.MONGO_URI}...")
        db_instance.client = AsyncIOMotorClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=5000,
        )
        db_instance.db = db_instance.client[settings.MONGO_DB_NAME]
        logger.info("Successfully connected to MongoDB.")

        # Seed initial passages if empty
        await seed_initial_passages()
    except Exception as e:
        logger.warning(f"Failed to connect to MongoDB: {e}. Running in disconnected fallback mode.")


async def seed_initial_passages() -> None:
    if db_instance.db is not None:
        try:
            count = await db_instance.db["passages"].count_documents({})
            if count == 0:
                await db_instance.db["passages"].insert_many(DEFAULT_PASSAGES)
                logger.info("[MONGO-SEED] Seeded 3 default story passages into 'passages' collection.")
        except Exception as err:
            logger.warning(f"[MONGO-SEED-ERR] Could not seed passages: {err}")


async def close_mongo_connection() -> None:
    if db_instance.client:
        logger.info("Closing MongoDB connection...")
        db_instance.client.close()
        logger.info("MongoDB connection closed.")


def get_database() -> Optional[AsyncIOMotorDatabase]:
    return db_instance.db
