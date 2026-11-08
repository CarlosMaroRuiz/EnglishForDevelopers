"""Application configuration.

Uses pydantic-settings so that values are read from environment variables
and/or a `.env` file at the project root, with sensible defaults.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# Workplace scenarios and their system prompts (domain constants).
# ---------------------------------------------------------------------------
WORK_SCENARIOS = [
    "daily_standup",
    "code_review",
    "technical_interview",
    "debugging_session",
    "project_planning",
    "client_meeting",
    "architecture_discussion",
    "deployment_issue",
]

SCENARIO_PROMPTS = {
    "daily_standup": "You're in a daily standup meeting. Discuss what you worked on yesterday, what you're working on today, and any blockers.",
    "code_review": "You're reviewing a colleague's pull request. Discuss the code quality, suggest improvements, and ask questions.",
    "technical_interview": "You're in a technical interview. Answer questions about your experience, solve coding problems, and ask about the role.",
    "debugging_session": "You're helping debug a production issue. Explain the problem, discuss potential causes, and propose solutions.",
    "project_planning": "You're planning a new feature. Discuss requirements, technical approach, and timeline estimates.",
    "client_meeting": "You're meeting with a client to discuss their software requirements and provide technical recommendations.",
    "architecture_discussion": "You're discussing system architecture with your team. Talk about design patterns, scalability, and best practices.",
    "deployment_issue": "There's a deployment problem in production. Communicate the issue, impact, and resolution steps.",
}


def get_scenario_prompt(scenario: str) -> str:
    return SCENARIO_PROMPTS.get(scenario, "General technical discussion")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    secret_key: str = "dev-secret-key-change-me"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-flash"
    database_path: str = "english_tutor.db"
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
