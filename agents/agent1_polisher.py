from __future__ import annotations

import os

from providers import ProviderError, extract_json, openrouter_chat


DEFAULT_POLISHED_IDEA = {
    "startup_name": "IdeaBee",
    "elevator_pitch": "An AI startup builder that turns rough ideas into launch-ready ventures.",
    "problem": "Founders spend too much time turning messy notes into a coherent startup plan.",
    "solution": "A multi-agent workflow that refines the idea, validates the market, builds a website, and produces a pitch deck.",
    "target_audience": "Founders, indie hackers, and small startup teams.",
    "key_features": ["Idea normalization", "Market validation", "Website generation", "Pitch deck generation"],
    "uvp": "Converts a raw concept into a polished launch package in one flow.",
    "suggested_tech_stack": ["Python", "LangGraph", "Streamlit", "ChromaDB", "python-pptx"],
}


def polish_idea(raw_idea: str) -> dict[str, object]:
    cleaned_idea = raw_idea.strip()
    model = os.getenv("POLISHER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    prompt = (
        "Turn the user's raw startup idea into strict JSON with keys: startup_name, elevator_pitch, problem, solution, "
        "target_audience, key_features, uvp, suggested_tech_stack. Keep it concise and startup-focused."
    )

    try:
        response = openrouter_chat(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": cleaned_idea},
            ],
            temperature=0.2,
        )
        data = extract_json(response)
    except (ProviderError, ValueError, KeyError, TypeError):
        data = dict(DEFAULT_POLISHED_IDEA)
        data["elevator_pitch"] = cleaned_idea or DEFAULT_POLISHED_IDEA["elevator_pitch"]

    data.setdefault("startup_name", "IdeaBee")
    data.setdefault("elevator_pitch", cleaned_idea or DEFAULT_POLISHED_IDEA["elevator_pitch"])
    data.setdefault("problem", DEFAULT_POLISHED_IDEA["problem"])
    data.setdefault("solution", DEFAULT_POLISHED_IDEA["solution"])
    data.setdefault("target_audience", DEFAULT_POLISHED_IDEA["target_audience"])
    data.setdefault("key_features", DEFAULT_POLISHED_IDEA["key_features"])
    data.setdefault("uvp", DEFAULT_POLISHED_IDEA["uvp"])
    data.setdefault("suggested_tech_stack", DEFAULT_POLISHED_IDEA["suggested_tech_stack"])
    data["raw_idea"] = cleaned_idea
    return data
