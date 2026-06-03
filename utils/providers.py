from __future__ import annotations

import os
from typing import Optional

try:
    from huggingface_hub import InferenceClient
except Exception:
    InferenceClient = None


def hf_client() -> Optional[object]:
    token = os.getenv("HF_TOKEN") or os.getenv("HF_TOKEN")
    if not token or InferenceClient is None:
        return None
    return InferenceClient(api_key=token)


def has_openrouter() -> bool:
    return bool(os.getenv("OPENROUTER_API_KEY"))


def openrouter_headers() -> dict:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        return {}
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def has_tavily() -> bool:
    return bool(os.getenv("TAVILY_API_KEY"))


def available_providers() -> dict:
    return {
        "hf": bool(os.getenv("HF_TOKEN")) and InferenceClient is not None,
        "openrouter": has_openrouter(),
        "tavily": has_tavily(),
    }
