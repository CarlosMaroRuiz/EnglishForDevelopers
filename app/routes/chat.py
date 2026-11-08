"""Chat API endpoints (SSE streaming)."""
import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    scenario: str = "daily_standup"


@router.post("/stream")
async def stream_chat(payload: ChatRequest, request: Request):
    message = payload.message.strip()
    if not message:
        return JSONResponse(status_code=400, content={"error": "Message cannot be empty"})

    service = request.app.state.conversation

    async def event_stream():
        async for event in service.stream_conversation(message, payload.scenario):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


class SuggestRequest(BaseModel):
    scenario: str = "daily_standup"
    context: str = ""


@router.post("/suggest")
async def suggest_reply(payload: SuggestRequest, request: Request):
    service = request.app.state.conversation
    return await service.generate_suggestion(payload.scenario, payload.context or None)
