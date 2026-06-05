from __future__ import annotations

import os
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agents import (
    build_pitch_deck,
    build_website_artifact,
    finalize_delivery,
    polish_idea,
    research_market,
    generate_brand_identity,
    generate_asset_blueprint,
)
from utils.profile import build_master_profile
from utils import validate_and_sanitize
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AgentState:
    idea: str
    polished: dict[str, Any] = field(default_factory=dict)
    research: dict[str, Any] = field(default_factory=dict)
    website: dict[str, Any] = field(default_factory=dict)
    pitch: dict[str, Any] = field(default_factory=dict)
    delivery: dict[str, Any] = field(default_factory=dict)
    master_profile: dict[str, Any] = field(default_factory=dict)


def ensure_directories() -> None:
    for relative_path in ["agents", "rag", "knowledge_base", "templates", "outputs", "prompts"]:
        Path(relative_path).mkdir(parents=True, exist_ok=True)


def run_discovery(idea: str) -> dict[str, Any]:
    ensure_directories()
    polished = polish_idea(idea)
    return polished


def run_assets_generation(polished: dict[str, Any], startup_name: str, output_dir: str | None = None) -> dict[str, Any]:
    ensure_directories()
    output_dir = output_dir or os.getenv("OUTPUT_DIR", "outputs")

    # 1. Override and sanitize polished brief first
    polished = dict(polished)
    polished["startup_name"] = startup_name
    polished = validate_and_sanitize(polished, startup_name)

    # 2. Build RAG KB if we have documents
    if any(path.suffix.lower() in {".txt", ".md", ".markdown"} for path in Path("knowledge_base").rglob("*")):
        try:
            from rag.build_kb import build_knowledge_base
            build_knowledge_base(persist_dir=os.getenv("CHROMA_PATH", "knowledge_base/chroma_db"))
        except Exception:
            pass

    # 3. Research Market
    research = research_market(polished, output_dir=output_dir)
    research = validate_and_sanitize(research, startup_name)

    # 4. Generate Brand Identity
    brand = generate_brand_identity(polished, research)
    brand = validate_and_sanitize(brand, startup_name)

    # 5. Generate Asset Blueprint
    blueprint = generate_asset_blueprint(polished, research, brand)
    blueprint = validate_and_sanitize(blueprint, startup_name)

    # 6. Build Master Startup Profile
    master_profile = build_master_profile(polished, research, brand, blueprint)
    master_profile = validate_and_sanitize(master_profile, startup_name)

    # 7. Generate Website Artifact
    website = build_website_artifact(master_profile, output_dir=output_dir)
    website = validate_and_sanitize(website, startup_name)

    # 8. Generate Pitch Deck
    pitch = build_pitch_deck(master_profile, output_dir=output_dir)
    pitch = validate_and_sanitize(pitch, startup_name)

    # 9. Sanitize all generated text files on disk
    output_path = Path(output_dir)
    for path in output_path.rglob("*"):
        if path.is_file() and path.suffix in {".html", ".css", ".js", ".json", ".txt"}:
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                sanitized_content = validate_and_sanitize(content, startup_name)
                if sanitized_content != content:
                    path.write_text(sanitized_content, encoding="utf-8")
            except Exception:
                pass

    # Re-zip the website bundle with sanitized contents
    bundle_zip = output_path / "website_bundle.zip"
    try:
        with zipfile.ZipFile(bundle_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for fname in ["index.html", "styles.css", "script.js"]:
                fpath = output_path / fname
                if fpath.exists():
                    archive.write(fpath, arcname=fname)
    except Exception:
        pass

    # 10. Finalize delivery package with fully sanitized deliverables
    delivery = finalize_delivery(master_profile, website, pitch, output_dir=output_dir)
    delivery = validate_and_sanitize(delivery, startup_name)

    return {
        "polished": polished,
        "research": research,
        "website": website,
        "pitch": pitch,
        "delivery": delivery,
        "master_profile": master_profile,
    }


def run_pipeline(idea: str, output_dir: str | None = None) -> dict[str, Any]:
    polished = run_discovery(idea)
    suggestions = polished.get("name_suggestions", [])
    selected_name = suggestions[0] if suggestions else str(polished.get("startup_name", "IdeaBee"))
    assets = run_assets_generation(polished, selected_name, output_dir=output_dir)

    return {
        "idea": idea,
        "polished": assets["polished"],
        "research": assets["research"],
        "website": assets["website"],
        "pitch": assets["pitch"],
        "delivery": assets["delivery"],
        "master_profile": assets["master_profile"],
    }
