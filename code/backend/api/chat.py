from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from services.rag import answer_question

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


class SourceRef(BaseModel):
    ref: str
    page: Optional[int] = None
    similarity: float


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    chunks_used: int


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        result = answer_question(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))