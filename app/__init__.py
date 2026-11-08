"""Application factory.

Wires configuration, persistence, the AI layer and the service layer together,
then mounts static files and registers all routers.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import get_settings

from .ai import AIService
from .db import DatabaseService
from .services.analytics import AnalyticsService
from .services.conversation import ConversationService
from .services.quiz import QuizService
from .services.report import ReportService
from .services.story import StoryService


def create_app() -> FastAPI:
    settings = get_settings()

    db = DatabaseService(settings.database_path)
    ai = AIService(settings)

    app = FastAPI(title="English Tutor for Developers")

    app.state.settings = settings
    app.state.db = db
    app.state.ai = ai
    app.state.conversation = ConversationService(db, ai)
    app.state.quiz = QuizService(db, ai)
    app.state.story = StoryService(db, ai)
    app.state.report = ReportService(db, ai)
    app.state.analytics = AnalyticsService(db)

    static_dir = Path(__file__).resolve().parent.parent / "static"
    static_dir.mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    from .routes import chat, pages, quiz as quiz_routes, story as story_routes

    app.include_router(pages.router)
    app.include_router(chat.router)
    app.include_router(quiz_routes.router)
    app.include_router(story_routes.router)

    return app
