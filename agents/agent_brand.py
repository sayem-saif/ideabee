from __future__ import annotations

import os
import json
from providers import ProviderError, extract_json, openrouter_chat, hf_chat
from utils.profile import DEFAULT_BRAND_IDENTITY

def generate_brand_identity(polished_idea: dict[str, object], research_report: dict[str, object]) -> dict[str, object]:
    prompt = (
        "You are a Brand Identity Strategist. Create a consistent branding identity for this startup.\n"
        "Generate strict JSON with keys: brand_personality, tone, brand_values (an array of 3 strings), tagline, visual_style, primary_color (a HEX code), secondary_color (a HEX code), typography, messaging_style.\n"
        "Colors must match the startup's domain (e.g. warm brown/gold for coffee, clean blue for SaaS, pastel green for organic cosmetics). Do not use generic grey/black.\n"
        "STRICT CONTENT BOUNDARY: Do not include any platform reference or platform terminology.\n"
        "startup details:\n"
        f"Name: {polished_idea.get('startup_name')}\n"
        f"Idea: {polished_idea}\n"
        f"Research Summary: {research_report.get('summary')}\n"
    )

    model = os.getenv("DELIVERER_MODEL", "google/gemma-3-27b-it")
    fallback = dict(DEFAULT_BRAND_IDENTITY)

    # Dynamic fallback adjustments based on industry/category
    category = str(research_report.get("category", "Other")).lower()
    if "cosmetic" in category or "organic" in category:
        fallback["primary_color"] = "#059669" # green
        fallback["secondary_color"] = "#10b981"
    elif "coffee" in category or "food" in category:
        fallback["primary_color"] = "#854d0e" # brown
        fallback["secondary_color"] = "#b45309"

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
