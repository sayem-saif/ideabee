from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from agents.agent1_polisher import polish_idea
from agents.agent2_researcher import research_market
from agents.agent3_website import build_website_artifact
from agents.agent4_pitch import build_pitch_deck
from agents.agent5_deliverer import finalize_delivery
from rag.retriever import retrieve_context
from rag.build_kb import build_knowledge_base
from utils import providers


@dataclass
class AgentState:
    idea: str
    polished: dict[str, Any] = field(default_factory=dict)
    research: dict[str, Any] = field(default_factory=dict)
    website: dict[str, Any] = field(default_factory=dict)
    pitch: dict[str, Any] = field(default_factory=dict)
    delivery: dict[str, Any] = field(default_factory=dict)


def ensure_directories() -> None:
    for relative_path in ["agents", "rag", "knowledge_base", "templates", "outputs", "prompts", "utils"]:
        Path(relative_path).mkdir(parents=True, exist_ok=True)


def run_pipeline(idea: str) -> AgentState:
    ensure_directories()
    print("Building knowledge base (placeholder)...")
    kb = build_knowledge_base()

    print("Polishing idea...")
    polished = polish_idea(idea)

    print("Retrieving context from KB...")
    context = retrieve_context(idea)

    print("Running research agent...")
    research = research_market(polished, context="\n".join(context))

    print("Building website artifact...")
    website = build_website_artifact(polished, output_dir=os.getenv("OUTPUT_DIR", "outputs"))

    print("Building pitch deck outline...")
    pitch = build_pitch_deck(polished, output_dir=os.getenv("OUTPUT_DIR", "outputs"))

    print("Finalizing delivery...")
    delivery = finalize_delivery(polished, research, website, pitch, output_dir=os.getenv("OUTPUT_DIR", "outputs"))

    state = AgentState(idea=idea)
    state.polished = polished
    state.research = research
    state.website = website
    state.pitch = pitch
    state.delivery = delivery

    print("Pipeline complete. Artifacts written to:", os.path.abspath(os.getenv("OUTPUT_DIR", "outputs")))
    return state


if __name__ == "__main__":
    sample_idea = os.getenv("IDEABEE_SAMPLE_IDEA", "An AI startup builder that turns rough ideas into validated ventures.")
    if len(sys.argv) > 1:
        idea = " ".join(sys.argv[1:])
    else:
        idea = sample_idea
    run_pipeline(idea)
