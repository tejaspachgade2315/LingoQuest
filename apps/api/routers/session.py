import uuid
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from models.schemas import (
    PassageCreate,
    PassageResponse,
    GameSessionCreate,
    GameSessionResponse,
)
from core.database import get_database
from services.parser import document_parser

logger = logging.getLogger("reading-game.session")
router = APIRouter()

# Default in-memory seed passages for immediate development
MOCK_PASSAGES = {
    "story-1": {
        "id": "story-1",
        "title": "The Brave Little Falcon",
        "content": "High above the rocky ridge a young falcon named Pip spread his wings for the very first time. The crisp morning breeze lifted him gently as he looked toward the horizon with courage.",
        "difficulty_level": "beginner",
        "target_wpm": 80,
        "words": "High above the rocky ridge a young falcon named Pip spread his wings for the very first time. The crisp morning breeze lifted him gently as he looked toward the horizon with courage.".split(" "),
        "total_words": 31,
    },
    "story-2": {
        "id": "story-2",
        "title": "Echoes of the Deep Forest",
        "content": "As twilight painted the canopy in shades of violet the ancient oak trees whispered secrets to the wind. Curious creatures emerged from their shelters to welcome the gentle night.",
        "difficulty_level": "intermediate",
        "target_wpm": 100,
        "words": "As twilight painted the canopy in shades of violet the ancient oak trees whispered secrets to the wind. Curious creatures emerged from their shelters to welcome the gentle night.".split(" "),
        "total_words": 28,
    },
}


@router.get("/passages", response_model=List[PassageResponse])
async def list_passages():
    db = get_database()
    if db is not None:
        try:
            cursor = db["passages"].find()
            passages = await cursor.to_list(length=100)
            if passages:
                return [PassageResponse(**p) for p in passages]
        except Exception as e:
            logger.warning(f"Failed to read from Mongo, using fallback passages: {e}")

    return [
        PassageResponse(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            difficulty_level=data["difficulty_level"],
            target_wpm=data["target_wpm"],
            words=data["words"],
            total_words=data["total_words"],
        )
        for data in MOCK_PASSAGES.values()
    ]


@router.post("/passages", response_model=PassageResponse)
async def create_passage(req: PassageCreate):
    parsed = document_parser.parse_passage(
        title=req.title,
        raw_content=req.content,
        difficulty=req.difficulty_level,
    )
    passage_id = f"passage-{uuid.uuid4().hex[:8]}"
    doc = {
        "id": passage_id,
        "title": parsed["title"],
        "content": parsed["content"],
        "difficulty_level": parsed["difficulty_level"],
        "target_wpm": req.target_wpm,
        "words": parsed["words"],
        "total_words": parsed["total_words"],
        "created_at": datetime.utcnow(),
    }

    db = get_database()
    if db is not None:
        await db["passages"].insert_one(doc)

    return PassageResponse(**doc)


@router.post("/sessions", response_model=GameSessionResponse)
async def create_session(req: GameSessionCreate):
    session_id = f"sess-{uuid.uuid4().hex[:10]}"
    doc = {
        "session_id": session_id,
        "passage_id": req.passage_id,
        "user_id": req.user_id,
        "channel": req.channel,
        "status": "in_progress",
        "current_word_index": 0,
        "accuracy_score": 100.0,
        "words_read_count": 0,
        "duration_seconds": 0.0,
        "created_at": datetime.utcnow(),
    }

    db = get_database()
    if db is not None:
        await db["sessions"].insert_one(doc)

    return GameSessionResponse(**doc)


@router.get("/sessions/{session_id}", response_model=GameSessionResponse)
async def get_session(session_id: str):
    db = get_database()
    if db is not None:
        doc = await db["sessions"].find_one({"session_id": session_id})
        if doc:
            return GameSessionResponse(**doc)

    raise HTTPException(status_code=404, detail="Session not found")


@router.patch("/sessions/{session_id}")
async def update_session_progress(session_id: str, payload: dict):
    """Updates live session metrics, evaluations, and DDA state in MongoDB."""
    db = get_database()
    if db is not None:
        payload["updated_at"] = datetime.utcnow()
        await db["sessions"].update_one(
            {"session_id": session_id},
            {"$set": payload},
            upsert=True,
        )
        return {"status": "updated", "session_id": session_id}
    return {"status": "noop"}

