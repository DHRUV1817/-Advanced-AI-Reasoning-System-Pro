from fastapi import APIRouter, Request
from src.api.schemas import CreateConversationRequest
from src.storage import dao

router = APIRouter()


@router.post("/conversations")
async def create_conversation(req: CreateConversationRequest, request: Request):
    cid = dao.create_conversation(request.app.state.db, title=req.title)
    return {"id": cid, "title": req.title}


@router.get("/conversations")
async def list_conversations(request: Request, limit: int = 100, offset: int = 0):
    rows = dao.list_conversations(request.app.state.db, limit=limit, offset=offset)
    return {"conversations": [dict(r) for r in rows]}
