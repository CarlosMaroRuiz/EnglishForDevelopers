"""Conversation (chat) business logic."""
import asyncio

from app.schemas import ConversationAnalysis
from app.services.fallback import fallback_analysis

_FALLBACK_SUGGESTIONS = {
    "daily_standup": {
        "suggestion_en": "Yesterday I worked on the login page. Today I'll finish the password reset, and I'm not blocked.",
        "suggestion_es": "Ayer trabajé en la página de inicio de sesión. Hoy terminaré el restablecimiento de contraseña y no tengo bloqueos.",
    },
    "code_review": {
        "suggestion_en": "The logic looks good overall. I'd suggest renaming this variable for clarity and adding a test for the edge case.",
        "suggestion_es": "La lógica se ve bien en general. Sugeriría renombrar esta variable para mayor claridad y añadir una prueba para el caso límite.",
    },
    "technical_interview": {
        "suggestion_en": "In my last role I built a REST API with Python and FastAPI. I focused on clean architecture and testing.",
        "suggestion_es": "En mi último puesto construí una API REST con Python y FastAPI. Me centré en una arquitectura limpia y en las pruebas.",
    },
    "debugging_session": {
        "suggestion_en": "I think the issue is in the authentication flow. Let me check the logs and reproduce it locally.",
        "suggestion_es": "Creo que el problema está en el flujo de autenticación. Déjame revisar los registros y reproducirlo en local.",
    },
}


class ConversationService:
    def __init__(self, db, ai):
        self.db = db
        self.ai = ai

    def _persist(self, message: str, analysis: ConversationAnalysis, scenario: str):
        self.db.save_conversation(
            message,
            analysis.conversation_response,
            [c.model_dump() for c in analysis.corrections],
            scenario,
        )
        if analysis.new_vocabulary:
            self.db.save_vocabulary([v.model_dump() for v in analysis.new_vocabulary])

    async def stream_conversation(self, message: str, scenario: str):
        """Stream the tutor's response and yield SSE event dicts."""
        analysis: ConversationAnalysis | None = None

        if self.ai.available:
            try:
                async for snapshot in self.ai.stream_conversation(message, scenario):
                    analysis = snapshot
                    yield {"type": "delta", "text": snapshot.conversation_response or ""}
            except Exception as exc:  # noqa: BLE001 - keep the endpoint resilient
                print(f"Conversation streaming error: {exc}")
                analysis = None

        if analysis is None or not analysis.conversation_response:
            analysis = fallback_analysis(message, scenario)

        await asyncio.to_thread(self._persist, message, analysis, scenario)
        yield {"type": "done", "analysis": analysis.model_dump()}

    async def generate_suggestion(self, scenario: str, context: str | None = None):
        """Return an AI-suggested reply with its Spanish translation."""
        if self.ai.available:
            try:
                suggestion = await self.ai.generate_suggestion(scenario, context)
                if suggestion:
                    return {
                        "suggestion_en": suggestion.suggestion_en,
                        "suggestion_es": suggestion.suggestion_es,
                    }
            except Exception as exc:  # noqa: BLE001
                print(f"Suggestion generation error: {exc}")
        return _FALLBACK_SUGGESTIONS.get(scenario, _FALLBACK_SUGGESTIONS["daily_standup"])
