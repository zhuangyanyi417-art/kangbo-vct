from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["chat"])

chat_service = ChatService()


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


@router.post("", response_model=ChatResponse)
async def ask_question(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    answer = await chat_service.answer(req.question, db)
    return ChatResponse(answer=answer)
