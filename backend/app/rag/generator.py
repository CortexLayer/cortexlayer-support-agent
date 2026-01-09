"""LLM answer generation with provider fallback and usage tracking."""

import asyncio
from typing import Tuple

from groq import Groq
from openai import OpenAI

from backend.app.core.config import settings
from backend.app.utils.logger import logger

groq_client = Groq(api_key=settings.GROQ_API_KEY)
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def _call_groq(prompt: str, max_tokens: int):
    return groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3,
    )


def _call_openai(prompt: str, max_tokens: int):
    return openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3,
    )


async def generate_answer(
    prompt: str,
    model_preference: str = "groq",
    max_tokens: int = 500,
) -> Tuple[str, dict]:
    """Generate an answer using LLMs with safe async fallback."""
    usage_stats = {
        "model_used": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
    }

    if model_preference == "groq":
        try:
            response = await asyncio.to_thread(_call_groq, prompt, max_tokens)

            answer = response.choices[0].message.content
            usage_stats["model_used"] = "llama-3.3-70b"
            usage_stats["input_tokens"] = response.usage.prompt_tokens
            usage_stats["output_tokens"] = response.usage.completion_tokens

            input_tokens = usage_stats["input_tokens"]
            output_tokens = usage_stats["output_tokens"]

            usage_stats["cost_usd"] = (input_tokens / 1_000_000) * 0.27 + (
                output_tokens / 1_000_000
            ) * 0.27

            return answer, usage_stats

        except Exception as e:
            logger.warning(f"Groq failed, falling back to OpenAI: {e}")

    try:
        response = await asyncio.to_thread(_call_openai, prompt, max_tokens)

        answer = response.choices[0].message.content
        usage_stats["model_used"] = "gpt-4o-mini"
        usage_stats["input_tokens"] = response.usage.prompt_tokens
        usage_stats["output_tokens"] = response.usage.completion_tokens

        input_tokens = usage_stats["input_tokens"]
        output_tokens = usage_stats["output_tokens"]

        usage_stats["cost_usd"] = (input_tokens / 1_000_000) * 0.15 + (
            output_tokens / 1_000_000
        ) * 0.60

        return answer, usage_stats

    except Exception as e:
        logger.error(f"Both LLM providers failed: {e}")
        raise RuntimeError("LLM generation failed") from e
