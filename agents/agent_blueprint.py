from __future__ import annotations

import os
import json
from providers import ProviderError, extract_json, openrouter_chat, hf_chat
from utils.profile import DEFAULT_ASSET_BLUEPRINT

def generate_asset_blueprint(
    polished_idea: dict[str, object],
    research_report: dict[str, object],
    brand_identity: dict[str, object]
) -> dict[str, object]:
    prompt = (
        "You are a Business Narrative Designer. Create a unified, consistent storyline for this startup.\n"
        "Generate strict JSON with keys: hero_message, problem_story, solution_story, market_story, business_story, competitive_story, closing_story, call_to_action.\n"
        "The stories should read like professional copy. Do not invent fake statistics or fake numbers.\n"
        "STRICT CONTENT BOUNDARY: Do not include any technical terminology relating to the AI builder, agents, workflows, prompts, ChromaDB, etc.\n"
        "startup details:\n"
        f"Name: {polished_idea.get('startup_name')}\n"
        f"Idea: {polished_idea}\n"
        f"Brand Identity: {brand_identity}\n"
        f"Research: {research_report}\n"
    )

    model = os.getenv("DELIVERER_MODEL", "google/gemma-3-27b-it")
    fallback = dict(DEFAULT_ASSET_BLUEPRINT)

    for provider in (
        lambda: openrouter_chat(model=model, messages=[{"role": "system", "content": prompt}], temperature=0.35),
        lambda: hf_chat(model=model, messages=[{"role": "system", "content": prompt}], temperature=0.35),
    ):
        try:
            response = provider()
            data = extract_json(response)
            if isinstance(data, dict):
                return data
        except Exception:
            continue

    return fallback
