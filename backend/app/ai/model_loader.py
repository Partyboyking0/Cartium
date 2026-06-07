from __future__ import annotations

import requests

from ..core.config import settings

HF_CHAT_COMPLETIONS_URL = "https://router.huggingface.co/v1/chat/completions"


def _messages_from_input(messages_or_prompt: str | list[dict[str, str]]) -> list[dict[str, str]]:
    if isinstance(messages_or_prompt, list):
        return messages_or_prompt
    return [{"role": "user", "content": messages_or_prompt}]


def _prompt_from_input(messages_or_prompt: str | list[dict[str, str]]) -> str:
    if isinstance(messages_or_prompt, str):
        return messages_or_prompt
    lines = []
    for item in messages_or_prompt:
        role = item.get("role", "user").title()
        content = item.get("content", "")
        lines.append(f"{role}: {content}")
    lines.append("Assistant:")
    return "\n".join(lines)


def _clean_reply(text: str) -> str:
    leaked_markers = [
        "### SYSTEM",
        "### PRIVATE FACTS",
        "### INSTRUCTIONS",
        "### USER QUESTION",
        "### FINAL CUSTOMER ANSWER",
        "Cartium context:",
        "Cartium retrieved context:",
        "User personalization:",
        "Backend action result:",
        "User question:",
        "Customer-facing answer rules:",
    ]
    cleaned_text = text.strip()
    for marker in leaked_markers:
        index = cleaned_text.find(marker)
        if index > 0:
            cleaned_text = cleaned_text[:index].strip()
        elif index == 0:
            cleaned_text = ""

    lines = [line.strip() for line in cleaned_text.splitlines() if line.strip()]
    cleaned: list[str] = []
    seen_counts: dict[str, int] = {}
    for line in lines:
        if any(line.startswith(marker) for marker in leaked_markers):
            break
        key = line.lower().rstrip(" .!?,;:")
        seen_counts[key] = seen_counts.get(key, 0) + 1
        if seen_counts[key] > 1:
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def _extract_reply(data: dict) -> str:
    choices = data.get("choices") or []
    if choices:
        first = choices[0]
        if isinstance(first.get("message"), dict):
            return _clean_reply(first["message"].get("content") or "")
        if first.get("text"):
            return _clean_reply(str(first["text"]))
    if isinstance(data.get("generated_text"), str):
        return _clean_reply(data["generated_text"])
    raise RuntimeError(f"Unexpected Hugging Face API response: {data}")


def generate_response(messages_or_prompt: str | list[dict[str, str]]) -> str:
    """Generate with Hugging Face hosted API.

    Supports both OpenAI-compatible chat-completions endpoints and provider
    completions endpoints such as /v1/completions. No local torch/transformers
    model is loaded.
    """
    if not settings.huggingface_api_key:
        raise RuntimeError("HUGGINGFACE_API_KEY is not set in backend/.env")

    url = settings.huggingface_chat_url or HF_CHAT_COMPLETIONS_URL
    clean_url = url.rstrip("/")
    if clean_url.endswith("/completions") and not clean_url.endswith("/chat/completions"):
        payload = {
            "model": settings.ai_model_name,
            "prompt": _prompt_from_input(messages_or_prompt),
            "max_tokens": settings.max_new_tokens,
            "temperature": settings.temperature,
            "top_p": settings.top_p,
            "stream": False,
            "stop": ["\nUser:", "\nAssistant:", "\n###", "\nCartium context:", "\nUser personalization:", "\nBackend action result:", "\nUser question:", "<|end|>"],
        }
    else:
        payload = {
            "model": settings.ai_model_name,
            "messages": _messages_from_input(messages_or_prompt),
            "max_tokens": settings.max_new_tokens,
            "temperature": settings.temperature,
            "top_p": settings.top_p,
            "stream": False,
        }

    headers = {
        "Authorization": f"Bearer {settings.huggingface_api_key}",
        "Content-Type": "application/json",
    }
    response = requests.post(url, headers=headers, json=payload, timeout=settings.huggingface_timeout_seconds)
    if response.status_code >= 400:
        raise RuntimeError(f"Hugging Face API error {response.status_code}: {response.text[:500]}")
    return _extract_reply(response.json())
