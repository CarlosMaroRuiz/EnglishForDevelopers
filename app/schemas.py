"""Pydantic models describing the structured outputs produced by the AI agents.

These replace the fragile "respond with JSON only" prompts used previously:
pydantic-ai validates the model output against these schemas automatically.
"""
from pydantic import BaseModel, Field


class Correction(BaseModel):
    """A single grammar/vocabulary/style correction."""

    original: str = ""
    corrected: str = ""
    type: str = "grammar"
    explanation: str = ""


class VocabularyItem(BaseModel):
    """A new technical term suggested to the user."""

    word: str
    definition: str = ""
    example: str = ""


class ConversationAnalysis(BaseModel):
    """The tutor's analysis of a user message."""

    conversation_response: str
    corrections: list[Correction] = Field(default_factory=list)
    new_vocabulary: list[VocabularyItem] = Field(default_factory=list)
    suggestions: str = ""


class SuggestedResponse(BaseModel):
    """An AI-suggested reply the learner could send, with a Spanish translation."""

    suggestion_en: str
    suggestion_es: str


class QuizQuestion(BaseModel):
    """A single multiple-choice grammar question."""

    question: str
    option_a: str
    option_b: str
    option_c: str
    correct_answer: str
    explanation: str
    category: str = "general"


class QuizSet(BaseModel):
    """A set of generated quiz questions."""

    questions: list[QuizQuestion] = Field(default_factory=list)


class StoryStep(BaseModel):
    """A single interactive step inside a story."""

    step_number: int = 1
    type: str = "question"
    content: str
    question: str | None = None
    expected_response_type: str = "open"
    learning_focus: str = "communication_skills"


class StoryData(BaseModel):
    """An AI-generated interactive story."""

    title: str
    description: str = ""
    content: str
    learning_objectives: list[str] = Field(default_factory=list)
    estimated_time: int = 10
    steps: list[StoryStep] = Field(default_factory=list)


class PersonalReport(BaseModel):
    """A comprehensive AI analysis report of the user's progress."""

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    grammar_mastered: list[str] = Field(default_factory=list)
    grammar_needs_work: list[str] = Field(default_factory=list)
    focus_areas: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    overall_assessment: str = ""
    learning_path: list[str] = Field(default_factory=list)
    personality_insights: list[str] = Field(default_factory=list)
