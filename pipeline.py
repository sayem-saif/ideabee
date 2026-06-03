from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agents import build_pitch_deck, build_website_artifact, finalize_delivery, polish_idea, research_market
from dotenv import load_dotenv

from rag.build_kb import build_knowledge_base

load_dotenv()


@dataclass
class AgentState:
    idea: str
    polished: dict[str, Any] = field(default_factory=dict)
    research: dict[str, Any] = field(default_factory=dict)
    website: dict[str, Any] = field(default_factory=dict)
    pitch: dict[str, Any] = field(default_factory=dict)
    delivery: dict[str, Any] = field(default_factory=dict)


def ensure_directories() -> None:
    for relative_path in ["agents", "rag", "knowledge_base", "templates", "outputs", "prompts"]:
        Path(relative_path).mkdir(parents=True, exist_ok=True)


def run_pipeline(idea: str, output_dir: str | None = None) -> dict[str, Any]:
    ensure_directories()
    output_dir = output_dir or os.getenv("OUTPUT_DIR", "outputs")

    if any(path.suffix.lower() in {".txt", ".md", ".markdown"} for path in Path("knowledge_base").rglob("*")):
        build_knowledge_base(persist_dir=os.getenv("CHROMA_PATH", "knowledge_base/chroma_db"))

    polished = polish_idea(idea)
    research = research_market(polished, output_dir=output_dir)
    website = build_website_artifact(polished, research, output_dir=output_dir)
    pitch = build_pitch_deck(polished, research, output_dir=output_dir)
    delivery = finalize_delivery(polished, research, website, pitch, output_dir=output_dir)

    return {
        "idea": idea,
        "polished": polished,
        "research": research,
        "website": website,
        "pitch": pitch,
        "delivery": delivery,
    }