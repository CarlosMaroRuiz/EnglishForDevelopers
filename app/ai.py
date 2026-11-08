"""DeepSeek integration via pydantic-ai.

Each task has a dedicated ``Agent`` with a typed ``output_type``. Pydantic AI
validates the model response against the schema automatically, so the manual
JSON parsing (``json.loads`` + markdown fence stripping) from the original
``services/ai_service.py`` is no longer needed.

Notes
-----
* DeepSeek V4 models "think" by default, which makes forced structured output
  unreliable. We disable thinking via ``OpenAIChatModelSettings(thinking=False)``.
* The API key comes from settings and is passed explicitly to ``DeepSeekProvider``.
"""
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.deepseek import DeepSeekProvider

from app.schemas import (
    ConversationAnalysis,
    PersonalReport,
    QuizSet,
    StoryData,
    SuggestedResponse,
)
from config import get_scenario_prompt

# ---------------------------------------------------------------------------
# Instructions (fixed role per agent; variable data goes in the user prompt).
# ---------------------------------------------------------------------------
TUTOR_INSTRUCTIONS = """\
You are an English tutor specialized in helping software developers improve \
their technical English communication in the workplace.

Given the scenario and the user's message:
1. Respond naturally to continue the work conversation.
2. Identify and correct grammar, vocabulary, or communication errors.
3. Suggest better ways to express technical concepts.
4. Introduce new technical vocabulary when appropriate.
5. Provide a short, actionable tip for improvement.
"""

QUIZ_INSTRUCTIONS = """\
You are an English grammar quiz generator for software developers. \
Generate multiple-choice questions that focus on the user's most common \
mistake areas, using realistic technical and workplace communication contexts. \
Each question must include a clear explanation and a grammar category.
"""

STORY_INSTRUCTIONS = """\
You are an expert story creator for English language learning, specialized in \
software development scenarios. Create a concise, engaging, interactive story \
that matches the specifications given in the request. Every step must be either \
a narrative step or a question step that includes both content and a question.
"""

REPORT_INSTRUCTIONS = """\
You are an expert English language analyst for software developers. Analyze the \
provided learning data and produce a comprehensive, specific and constructive \
personal report with a learning path and actionable recommendations.
"""

SUGGESTION_INSTRUCTIONS = """\
You are an English tutor for software developers. The learner is in a workplace \
conversation. Suggest a natural, professional English reply the learner could send \
to keep the conversation going, and provide its Spanish translation. Keep the reply \
concise (1-2 sentences) and realistic for a developer.
"""

# Story length specifications used to build the generation prompt.
STORY_LENGTH_SPECS = {
    "short": {"time": "3-5 minutes", "steps": "1-2 interactive steps", "content_length": "100-200 words", "focus": "Quick, focused practice"},
    "medium": {"time": "5-8 minutes", "steps": "2-3 interactive steps", "content_length": "200-300 words", "focus": "Moderate depth practice"},
    "long": {"time": "8-12 minutes", "steps": "3-4 interactive steps", "content_length": "300-400 words", "focus": "Comprehensive practice"},
}


class AIService:
    def __init__(self, settings):
        self.settings = settings
        self.available = bool(settings.deepseek_api_key)

        if self.available:
            provider = DeepSeekProvider(api_key=settings.deepseek_api_key)
            self.model = OpenAIChatModel(settings.deepseek_model, provider=provider)
        else:
            self.model = None

        self.tutor_agent = self._agent(ConversationAnalysis, TUTOR_INSTRUCTIONS) if self.available else None
        self.quiz_agent = self._agent(QuizSet, QUIZ_INSTRUCTIONS) if self.available else None
        self.story_agent = self._agent(StoryData, STORY_INSTRUCTIONS) if self.available else None
        self.report_agent = self._agent(PersonalReport, REPORT_INSTRUCTIONS) if self.available else None
        self.suggestion_agent = self._agent(SuggestedResponse, SUGGESTION_INSTRUCTIONS) if self.available else None

    def _agent(self, output_type, instructions):
        return Agent(
            self.model,
            output_type=output_type,
            instructions=instructions,
            model_settings=OpenAIChatModelSettings(thinking=False),
        )

    # ------------------------------------------------------------ conversation
    def _tutor_prompt(self, message: str, scenario: str, context: str | None = None) -> str:
        parts = [f"Workplace scenario: {get_scenario_prompt(scenario)}"]
        if context:
            parts.append(f"Current situation: {context}")
        parts.append(f"User message: {message}")
        return "\n\n".join(parts)

    async def analyze_conversation(self, message: str, scenario: str, context: str | None = None):
        """Return a full, validated ``ConversationAnalysis`` (non-streaming)."""
        if not self.available:
            return None
        prompt = self._tutor_prompt(message, scenario, context)
        result = await self.tutor_agent.run(prompt)
        return result.output

    async def stream_conversation(self, message: str, scenario: str, context: str | None = None):
        """Yield partial ``ConversationAnalysis`` snapshots while streaming."""
        prompt = self._tutor_prompt(message, scenario, context)
        async with self.tutor_agent.run_stream(prompt) as run:
            async for snapshot in run.stream_output():
                yield snapshot

    # -------------------------------------------------------------- suggestion
    async def generate_suggestion(self, scenario: str, context: str | None = None):
        """Suggest a natural reply the learner could send (EN + ES)."""
        if not self.available:
            return None
        parts = [f"Workplace scenario: {get_scenario_prompt(scenario)}"]
        if context:
            parts.append(f"The tutor just said: {context}")
        parts.append(
            "Suggest a natural, professional English reply the learner could give, "
            "and its Spanish translation."
        )
        result = await self.suggestion_agent.run("\n\n".join(parts))
        return result.output

    # ------------------------------------------------------------------- quiz
    async def generate_quiz(self, mistake_types, num_questions: int = 5):
        if not self.available:
            return None
        topics = ", ".join(mistake_types) if mistake_types else "general grammar and verb tenses"
        prompt = (
            f"Generate {num_questions} multiple-choice questions focused on these "
            f"user mistake areas: {topics}."
        )
        result = await self.quiz_agent.run(prompt)
        return result.output.questions

    # ------------------------------------------------------------------ story
    def _story_prompt(self, parameters) -> str:
        length = parameters.get("length", "short")
        spec = STORY_LENGTH_SPECS.get(length, STORY_LENGTH_SPECS["short"])
        focus_areas = parameters.get("focus_areas") or ["technical_vocabulary", "communication_skills"]
        return (
            f"Create an interactive story with these specifications:\n"
            f"- Topic: {parameters.get('topic', 'software_development')}\n"
            f"- Scenario: {parameters.get('scenario', 'daily_standup')}\n"
            f"- Difficulty: {parameters.get('difficulty', 'intermediate')}\n"
            f"- Length: {length} ({spec['time']}, {spec['steps']})\n"
            f"- Focus areas: {', '.join(focus_areas)}\n"
            f"Keep the introduction concise ({spec['content_length']}) and make "
            f"every step immediately engaging and actionable."
        )

    async def generate_story(self, parameters):
        if not self.available:
            return None
        prompt = self._story_prompt(parameters)
        result = await self.story_agent.run(prompt)
        return result.output

    # ----------------------------------------------------------------- report
    async def generate_report(self, data_summary: str):
        if not self.available:
            return None
        result = await self.report_agent.run(data_summary)
        return result.output
