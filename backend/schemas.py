from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime


class FaqCreate(BaseModel):
    question: str
    answer: str
    tags: Optional[str] = None


class FaqRead(BaseModel):
    id: int
    question: str
    answer: str
    tags: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str


class ChatItem(BaseModel):
    id: int
    question: str
    answer: str
    tags: Optional[str] = None
    score: float


class ChatResponse(BaseModel):
    results: List[ChatItem]
    used: Dict[str, Any]
