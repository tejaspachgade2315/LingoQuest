from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class WordEvaluation(BaseModel):
    index: int
    word: str
    normalized: str
    status: str = "idle"  # idle, current, correct, imperfect, missed
    similarity_score: float = 0.0
    spoken_alternative: Optional[str] = None
    timestamp_ms: Optional[float] = None


class PassageBase(BaseModel):
    title: str
    content: str
    difficulty_level: str = "beginner"
    target_wpm: Optional[int] = 90


class PassageCreate(PassageBase):
    pass


class PassageResponse(PassageBase):
    id: str
    words: List[str]
    total_words: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GameSessionCreate(BaseModel):
    passage_id: str
    user_id: str
    channel: str = "web"  # web, whatsapp, telephony


class GameSessionResponse(BaseModel):
    session_id: str
    passage_id: str
    user_id: str
    channel: str
    status: str = "pending"  # pending, in_progress, completed, failed
    current_word_index: int = 0
    accuracy_score: float = 100.0
    words_read_count: int = 0
    duration_seconds: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class LiveKitTokenRequest(BaseModel):
    roomName: str
    participantName: str
    metadata: Optional[Dict[str, Any]] = None


class LiveKitTokenResponse(BaseModel):
    token: str
    serverUrl: str
    roomName: str
    participantIdentity: str


class WebhookTriggerPayload(BaseModel):
    event_type: str = "call_initiate"  # call_initiate, whatsapp_message
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    passage_id: Optional[str] = "story-1"
    user_id: Optional[str] = "telephony_user"
    metadata: Optional[Dict[str, Any]] = None
