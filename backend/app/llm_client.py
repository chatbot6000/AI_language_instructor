"""
OpenAI-compatible chat client.

Talks to Ollama (/v1), OpenRouter, or any chat-completions endpoint.
If the call fails or no usable config exists, returns a graceful stub reply
so the M1 vertical slice still demos without a live LLM.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

# Patient beginner Spanish tutor — M1 hardcoded prompt (persona UI is M4)
SPANISH_SYSTEM_PROMPT = """You are EVANGELINE, a patient conversational Spanish tutor for absolute beginners (Pre-A1).

Rules:
- Keep Spanish simple: greetings, numbers, colors, common nouns, short phrases.
- Prefer short turns. Mix a little Spanish with brief English scaffolding when helpful.
- Always keep chat text clear and readable (never hide what you say).
- Encourage the learner; if they struggle, simplify further.
- Do not claim to be Pimsleur or any commercial brand.
- Reply in plain text only (no JSON, no markdown fences).
"""


@dataclass
class LlmResult:
    text: str
    mocked: bool
    error: str | None = None


def _stub_spanish_reply(user_message: str) -> str:
    """Deterministic fallback when LLM is unavailable."""
    lower = user_message.strip().lower()
    if any(g in lower for g in ("hola", "hello", "hi")):
        return (
            "(demo mode — no LLM connected) ¡Hola! Soy EVANGELINE. "
            "Let's practice Spanish. Try saying: Me llamo …"
        )
    if any(w in lower for w in ("gracias", "thank")):
        return "(demo mode) ¡De nada! Want to try colors? Rojo, azul, verde."
    return (
        "(demo mode — configure AI settings to talk to a real model) "
        f"I heard: “{user_message[:120]}”. "
        "Try a simple phrase like “Hola” or “¿Cómo estás?”."
    )


async def chat_completion(
    *,
    base_url: str,
    model: str,
    api_key: str,
    temperature: float,
    messages: list[dict[str, str]],
    timeout: float = 60.0,
) -> LlmResult:
    """
    POST /chat/completions against an OpenAI-compatible base URL.

    base_url should look like http://127.0.0.1:11434/v1 (no trailing slash required).
    """
    root = (base_url or "").rstrip("/")
    if not root or not model:
        return LlmResult(text=_stub_spanish_reply(_last_user(messages)), mocked=True, error="missing config")

    url = f"{root}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=headers, content=json.dumps(body))
            resp.raise_for_status()
            data = resp.json()
            text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            if not text:
                return LlmResult(
                    text=_stub_spanish_reply(_last_user(messages)),
                    mocked=True,
                    error="empty model response",
                )
            return LlmResult(text=text, mocked=False)
    except Exception as exc:  # noqa: BLE001 — intentional broad catch for stub fallback
        return LlmResult(
            text=_stub_spanish_reply(_last_user(messages)),
            mocked=True,
            error=str(exc),
        )


def _last_user(messages: list[dict[str, str]]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


def build_spanish_messages(history: list[dict[str, str]], user_text: str) -> list[dict[str, str]]:
    """Assemble system + prior turns + new user message for the LLM."""
    out: list[dict[str, str]] = [{"role": "system", "content": SPANISH_SYSTEM_PROMPT}]
    # Cap history so prompts stay small in M1
    for turn in history[-20:]:
        out.append({"role": turn["role"], "content": turn["content"]})
    out.append({"role": "user", "content": user_text})
    return out
