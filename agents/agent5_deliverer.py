from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

from providers import ProviderError, extract_json, openrouter_chat


def _qa_report(website_artifact: dict[str, object], pitch_artifact: dict[str, object]) -> tuple[list[str], float]:
    checks: list[str] = []
    score = 0.0

    website_files = [Path(path) for path in website_artifact.get("files", [])]
    if website_files and all(path.exists() for path in website_files):
        checks.append("Website files exist")
        score += 2.5

    index_file = next((path for path in website_files if path.name == "index.html"), None)
    if index_file and "<html" in index_file.read_text(encoding="utf-8", errors="ignore").lower():
        checks.append("Website HTML looks valid")
        score += 2.5

    slides = pitch_artifact.get("slides", [])
    if isinstance(slides, list) and len(slides) == 12:
        checks.append("Pitch deck has 12 slides")
        score += 3.0

    if pitch_artifact.get("pptx") and Path(str(pitch_artifact["pptx"])).exists():
        checks.append("PPTX exists")
        score += 1.0

    if pitch_artifact.get("pdf") and Path(str(pitch_artifact["pdf"])).exists():
        checks.append("PDF exists")
        score += 1.0

    return checks, min(score, 10.0)


def _write_script(polished_idea: dict[str, object], research_report: dict[str, object], pitch_artifact: dict[str, object], website_artifact: dict[str, object], output_path: Path) -> str:
    prompt = "Write a 5-minute founder pitch script with timed sections and 3 likely investor Q&A pairs. Return strict JSON with keys: script, q_and_a."
    model = os.getenv("DELIVERER_MODEL", "google/gemma-3-27b-it")

    fallback_script = (
        f"Opening: {polished_idea.get('elevator_pitch', '')}\n\n"
        f"Problem: {polished_idea.get('problem', '')}\n\n"
        f"Solution: {polished_idea.get('solution', '')}\n\n"
        f"Market: {research_report.get('summary', '')}\n\n"
        f"Business Model: {', '.join(research_report.get('business_models', []))}\n\n"
        f"Ask: Use the deck and product to secure pilots and early customers."
    )

    try:
        response = openrouter_chat(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps({"idea": polished_idea, "research": research_report, "pitch": pitch_artifact, "website": website_artifact})},
            ],
            temperature=0.35,
        )
        data = extract_json(response)
        script = str(data.get("script", fallback_script))
        q_and_a = data.get("q_and_a", [])
    except (ProviderError, ValueError, KeyError, TypeError):
        script = fallback_script
        q_and_a = [
            {"question": "Why now?", "answer": "The AI stack now makes end-to-end startup generation practical."},
            {"question": "What differentiates you?", "answer": "A single flow that produces research, a website, and a pitch deck."},
            {"question": "How do you monetize?", "answer": "Subscriptions plus premium exports and services."},
        ]

    script_text = ["# IdeaBee 5-Minute Pitch", "", script, "", "## Q&A Prep"]
    for item in q_and_a:
        script_text.append(f"- Q: {item.get('question', '')}")
        script_text.append(f"  A: {item.get('answer', '')}")

    output_path.write_text("\n".join(script_text), encoding="utf-8")
    return str(output_path)


def finalize_delivery(
    polished_idea: dict[str, object],
    research_report: dict[str, object],
    website_artifact: dict[str, object],
    pitch_artifact: dict[str, object],
    output_dir: str = "outputs",
) -> dict[str, object]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    checks, quality_score = _qa_report(website_artifact, pitch_artifact)
    script_path = output_path / "presentation_script.txt"
    script = _write_script(polished_idea, research_report, pitch_artifact, website_artifact, script_path)

    summary_file = output_path / "delivery_summary.json"
    summary_file.write_text(json.dumps({"checks": checks, "quality_score": quality_score}, indent=2), encoding="utf-8")

    package_path = output_path / "ideabee_delivery.zip"
    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in website_artifact.get("files", []):
            path = Path(str(file_path))
            if path.exists():
                archive.write(path, arcname=path.name)
        for key in ("bundle", "pptx", "pdf", "slides_json"):
            value = pitch_artifact.get(key)
            if value and Path(str(value)).exists():
                path = Path(str(value))
                archive.write(path, arcname=path.name)
        archive.write(script_path, arcname=script_path.name)
        archive.write(summary_file, arcname=summary_file.name)

    return {
        "status": "generated",
        "quality_score": quality_score,
        "checks": checks,
        "script": script,
        "script_path": str(script_path),
        "package": str(package_path),
        "polished": polished_idea,
        "research": research_report,
        "website": website_artifact,
        "pitch": pitch_artifact,
    }
