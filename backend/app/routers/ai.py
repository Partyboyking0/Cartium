from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..ai.chatbot_service import chat_with_assistant
from ..ai.rag import ingest_all_data
from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models import AIChatMessage, User
from ..schemas import AIChatHistoryOut, ChatRequest, ChatResponse, IngestResponse

router = APIRouter(prefix="/api/ai", tags=["ai"])
legacy_router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/history", response_model=AIChatHistoryOut)
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(AIChatMessage).filter(AIChatMessage.user_id == user.id).order_by(AIChatMessage.id.asc()).limit(50).all()
    return {"items": rows}


@router.delete("/history")
def clear_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(AIChatMessage).filter(AIChatMessage.user_id == user.id).delete()
    db.commit()
    return {"status": "cleared"}


@router.get("/health")
def ai_health():
    return {"status": "Cartium AI service is running"}


@router.post("/ingest", response_model=IngestResponse)
def ai_ingest(db: Session = Depends(get_db)):
    counts = ingest_all_data(db)
    return {"message": "Cartium AI knowledge base ingested successfully", "counts": counts}


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = chat_with_assistant(db=db, user=user, message=payload.message, user_id=payload.user_id)
    db.add(AIChatMessage(user_id=user.id, role="user", content=payload.message, model_name="cartium-ai"))
    db.add(AIChatMessage(user_id=user.id, role="assistant", content=result["reply"], model_name="cartium-ai"))
    db.commit()
    return result


legacy_router.add_api_route("/health", ai_health, methods=["GET"])
legacy_router.add_api_route("/ingest", ai_ingest, methods=["POST"], response_model=IngestResponse)
legacy_router.add_api_route("/chat", chat, methods=["POST"], response_model=ChatResponse)
