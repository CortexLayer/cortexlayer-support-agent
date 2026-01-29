"""LLM answer generation with provider fallback and usage tracking."""

from __future__ import annotations

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
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3,
    )


def _call_openai(prompt: str, model: str, max_tokens: int):
    return openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3,
    )


async def generate_answer(
    prompt: str,
    model_preference: str = "groq",
    max_tokens: int = 500,
) -> Tuple[str, dict]:
    """Generate an answer using LLMs with plan-aware fallback."""
    usage = {
        "model_used": "none",
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
    }

    async def run_groq():
        return await asyncio.to_thread(_call_groq, prompt, max_tokens)

    async def run_openai(model: str):
        return await asyncio.to_thread(_call_openai, prompt, model, max_tokens)

    try:
        if model_preference in {"groq", "groq_with_fallback"}:
            try:
                response = await run_groq()
                usage["model_used"] = settings.GROQ_MODEL
            except Exception as exc:
                if model_preference == "groq":
                    raise
                logger.warning("Groq failed, falling back to OpenAI: %s", exc)
                response = await run_openai(settings.OPENAI_MODEL)
                usage["model_used"] = settings.OPENAI_MODEL

        elif model_preference == "openai_gpt4":
            response = await run_openai(settings.OPENAI_MODEL)
            usage["model_used"] = settings.OPENAI_MODEL

        else:
            response = await run_openai(settings.OPENAI_MODEL)
            usage["model_used"] = settings.OPENAI_MODEL

        usage["input_tokens"] = response.usage.prompt_tokens
        usage["output_tokens"] = response.usage.completion_tokens

        total_tokens = usage["input_tokens"] + usage["output_tokens"]

        if usage["model_used"] == settings.GROQ_MODEL:
            usage["cost_usd"] = total_tokens / 1_000_000 * 0.27
        else:
            usage["cost_usd"] = (usage["input_tokens"] / 1_000_000) * 0.15 + (
                usage["output_tokens"] / 1_000_000
            ) * 0.60

        return response.choices[0].message.content, usage

    except Exception as exc:
        logger.error("LLM generation failed: %s", exc)
        raise RuntimeError("LLM generation failed") from exc
