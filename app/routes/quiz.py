"""Quiz API endpoints."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["quiz"])


class SubmitQuizRequest(BaseModel):
    answers: dict = Field(default_factory=dict)
    questions: list = Field(default_factory=list)


@router.post("/generate_quiz")
async def generate_quiz(request: Request):
    data = await request.app.state.quiz.generate_personalized_quiz()
    return data


@router.post("/submit_quiz")
def submit_quiz(payload: SubmitQuizRequest, request: Request):
    try:
        return request.app.state.quiz.process_quiz_submission(payload.answers, payload.questions)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
