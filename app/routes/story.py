"""Story API endpoints (creation, generation, interaction, completion)."""
import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["stories"])


class ManualStoryRequest(BaseModel):
    title: str
    content: str
    scenario: str = "general"
    difficulty: str = "intermediate"


class GenerateStoryRequest(BaseModel):
    topic: str = "software_development"
    difficulty: str = "intermediate"
    scenario: str = "daily_standup"
    length: str = "short"
    focus_areas: list[str] = Field(default_factory=list)


class StoryInteractRequest(BaseModel):
    response: str
    current_step: int = 1


@router.post("/stories/create")
async def create_story(payload: ManualStoryRequest, request: Request):
    service = request.app.state.story
    title = payload.title.strip()
    content = payload.content.strip()

    if not title or not content:
        return JSONResponse(status_code=400, content={"error": "Title and content are required"})
    if len(content) < 50:
        return JSONResponse(status_code=400, content={"error": "Content must be at least 50 characters"})

    story = await asyncio.to_thread(
        service.create_manual_story, title, content, payload.scenario, payload.difficulty
    )
    return {"success": True, "story_id": story["id"]}


@router.post("/stories/generate")
async def generate_story(payload: GenerateStoryRequest, request: Request):
    service = request.app.state.story
    story = await service.generate_ai_story(
        topic=payload.topic,
        difficulty=payload.difficulty,
        scenario=payload.scenario,
        length=payload.length,
        focus_areas=payload.focus_areas,
    )
    if not story or not story.get("id"):
        return JSONResponse(status_code=500, content={"error": "Failed to generate story"})
    return story


@router.post("/api/stories/{story_id}/interact/stream")
async def stream_story_interact(story_id: int, payload: StoryInteractRequest, request: Request):
    response = payload.response.strip()
    if not response:
        return JSONResponse(status_code=400, content={"error": "Response cannot be empty"})

    service = request.app.state.story

    async def event_stream():
        async for event in service.stream_story_interaction(story_id, response, payload.current_step):
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


@router.post("/stories/{story_id}/complete")
def complete_story(story_id: int, request: Request):
    return request.app.state.story.complete_story(story_id)
