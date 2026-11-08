"""HTML page routes (server-rendered templates)."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.templating import templates
from config import WORK_SCENARIOS

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"scenarios": WORK_SCENARIOS})


@router.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request, scenario: str = "daily_standup"):
    return templates.TemplateResponse(request, "chat.html", {"scenario": scenario})


@router.get("/speak", response_class=HTMLResponse)
def speak_page(request: Request):
    return templates.TemplateResponse(request, "speak.html", {})


@router.get("/quiz", response_class=HTMLResponse)
def quiz_page(request: Request):
    return templates.TemplateResponse(request, "quiz.html", {})


@router.get("/report", response_class=HTMLResponse)
async def report_page(request: Request):
    data = await request.app.state.report.generate_personal_report()
    return templates.TemplateResponse(
        request, "report.html", {"report": data["report"], "analytics": data["analytics"]}
    )


@router.get("/analytics", response_class=HTMLResponse)
def analytics_page(request: Request):
    data = request.app.state.analytics.get_analytics_data()
    return templates.TemplateResponse(
        request, "analytics.html", {"analytics": data["analytics"], "recommendations": data["recommendations"]}
    )


@router.get("/vocabulary", response_class=HTMLResponse)
def vocabulary_page(request: Request):
    vocabulary = request.app.state.analytics.get_vocabulary_data()
    return templates.TemplateResponse(request, "vocabulary.html", {"vocabulary": vocabulary})


@router.get("/history", response_class=HTMLResponse)
def history_page(request: Request):
    conversations = request.app.state.analytics.get_conversation_history()
    return templates.TemplateResponse(request, "history.html", {"conversations": conversations})


@router.get("/stories", response_class=HTMLResponse)
def stories_list(request: Request):
    stories = request.app.state.story.get_stories_list()
    user_progress = request.app.state.story.get_user_story_progress()
    return templates.TemplateResponse(
        request, "stories/list.html", {"stories": stories, "user_progress": user_progress}
    )


@router.get("/stories/create", response_class=HTMLResponse)
def create_story_page(request: Request):
    return templates.TemplateResponse(request, "stories/create.html", {})


@router.get("/stories/{story_id}", response_class=HTMLResponse)
def story_detail(request: Request, story_id: int):
    story = request.app.state.story.get_story_by_id(story_id)
    if not story:
        return templates.TemplateResponse(request, "stories/not_found.html", {}, status_code=404)

    user_progress = request.app.state.story.get_story_progress(story_id)
    interactions = request.app.state.story.get_story_interactions(story_id)
    return templates.TemplateResponse(
        request,
        "stories/detail.html",
        {"story": story, "user_progress": user_progress, "interactions": interactions},
    )
