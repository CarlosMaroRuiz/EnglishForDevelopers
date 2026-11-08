"""Test DeepSeek connectivity and structured output via pydantic-ai.

Run with::

    python test.py

This verifies the API key, the DeepSeek provider, and that typed structured
output is returned and validated correctly.
"""
import asyncio
import sys

from pydantic import BaseModel

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.deepseek import DeepSeekProvider

from config import get_settings


class Greeting(BaseModel):
    response: str
    suggestions: list[str]


async def main() -> int:
    settings = get_settings()

    if not settings.deepseek_api_key:
        print("❌ DEEPSEEK_API_KEY not found. Create a .env file with your key.")
        return 1

    print(f"✅ API key found: {settings.deepseek_api_key[:10]}...{settings.deepseek_api_key[-4:]}")
    print(f"   Model: {settings.deepseek_model}")

    provider = DeepSeekProvider(api_key=settings.deepseek_api_key)
    model = OpenAIChatModel(settings.deepseek_model, provider=provider)
    agent = Agent(
        model,
        output_type=Greeting,
        instructions=(
            "You are an English tutor for developers. Respond with a short greeting "
            "and one suggestion to improve technical English."
        ),
        model_settings=OpenAIChatModelSettings(thinking=False),
    )

    try:
        result = await agent.run("Hello! I want to improve my technical English.")
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Test failed: {exc}")
        return 1

    print("✅ Structured output received and validated:")
    print(f"   response: {result.output.response}")
    print(f"   suggestions: {result.output.suggestions}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
