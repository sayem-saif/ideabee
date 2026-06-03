from __future__ import annotations

import json
import os
import re
from typing import Any

import requests
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TAVILY_URL = "https://api.tavily.com/search"


class ProviderError(RuntimeError):
    pass


def extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, re.DOTALL)
    if fenced:
        cleaned = fenced.group(1)
    else:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def openrouter_chat(model: str, messages: list[dict[str, Any]], temperature: float = 0.4) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise ProviderError("OPENROUTER_API_KEY is missing")

    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "IdeaBee",
        },
        json={"model": model, "messages": messages, "temperature": temperature},
        timeout=180,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def hf_chat(model: str, messages: list[dict[str, Any]], temperature: float = 0.4) -> str:
    api_key = os.getenv("HF_TOKEN", "").strip()
    if not api_key:
        raise ProviderError("HF_TOKEN is missing")

    client = InferenceClient(api_key=api_key)
    completion = client.chat.completions.create(model=model, messages=messages, temperature=temperature)
    message = completion.choices[0].message
    content = getattr(message, "content", None)
    return str(content if content is not None else message).strip()


def web_search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
    if tavily_key:
        response = requests.post(
            TAVILY_URL,
            json={
                "api_key": tavily_key,
                "query": query,
                "search_depth": "advanced",
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        return [
            {"title": str(result.get("title", "")), "url": str(result.get("url", "")), "content": str(result.get("content", ""))}
            for result in results[:max_results]
        ]

    response = requests.get(
        "https://html.duckduckgo.com/html/",
        params={"q": query},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=60,
    )
    response.raise_for_status()

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(response.text, "html.parser")
    results: list[dict[str, str]] = []
    for anchor in soup.select("a.result__a")[:max_results]:
        results.append({"title": anchor.get_text(" ", strip=True), "url": anchor.get("href", ""), "content": ""})
    return results
