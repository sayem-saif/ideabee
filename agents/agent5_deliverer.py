from __future__ import annotations

import json
import os
import re
import zipfile
from pathlib import Path
from typing import Any

from providers import ProviderError, extract_json, openrouter_chat


_STOP_WORDS = {
    "about", "after", "again", "against", "also", "because", "before", "being",
    "between", "could", "every", "from", "have", "into", "more", "most", "much",
    "only", "other", "over", "same", "should", "some", "such", "than", "that",
    "their", "them", "then", "there", "these", "they", "this", "through", "too",
    "under", "very", "what", "when", "where", "which", "while", "with", "within",
    "would", "your",
}


def _content_words(text: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-z0-9]+", text.lower())
        if len(word) > 3 and word not in _STOP_WORDS
    }


def _narrative_matches_profile(master_profile: dict[str, Any], web_html: str) -> bool:
    website_words = _content_words(web_html)
    if not website_words:
        return False


    blueprint = master_profile.get("asset_blueprint", {})
    narrative_parts = [
        master_profile.get("problem", ""),
        master_profile.get("solution", ""),
    ]
    if isinstance(blueprint, dict):
        narrative_parts.extend([
            blueprint.get("problem_story", ""),
            blueprint.get("solution_story", ""),
            blueprint.get("hero_message", ""),
        ])

    for part in narrative_parts:
        profile_words = _content_words(str(part))
        if not profile_words:
            continue
        overlap = profile_words & website_words
        if len(overlap) >= 2 or len(overlap) / max(len(profile_words), 1) >= 0.20:
            return True

    # Check features overlap
    features = master_profile.get("key_features", [])
    for f in features:
        feature_words = _content_words(str(f))
        if feature_words and (feature_words & website_words):
            return True

    return False



def _qa_report(
    master_profile: dict[str, Any],
    website_artifact: dict[str, Any],
    pitch_artifact: dict[str, Any]
) -> tuple[list[str], list[str], float, bool]:
    consistency_logs: list[str] = []
    layout_logs: list[str] = []
    score = 0.0
    passed = True

    startup_name = master_profile.get("startup_name", "")
    problem = master_profile.get("problem", "")
    solution = master_profile.get("solution", "")

    # 1. Consistency Agent Checks
    if startup_name:
        consistency_logs.append("Startup Name exists")
        score += 2.0
    else:
        passed = False

    # Check Website consistency
    web_html = website_artifact.get("html", "")
    if startup_name.lower() in web_html.lower():
        consistency_logs.append("Website contains startup name")
        score += 1.5
    else:
        consistency_logs.append("WARNING: Startup Name missing in Website")
        passed = False

    if _narrative_matches_profile(master_profile, web_html):
        consistency_logs.append("Website aligns with problem/solution narrative")
        score += 1.5
    else:
        consistency_logs.append("WARNING: Website narrative does not match Startup Profile")
        passed = False

    # Check Pitch Deck consistency
    slides = pitch_artifact.get("slides", [])
    deck_text = "".join([slide.get("title", "") + " ".join(slide.get("bullets", [])) for slide in slides]).lower()
    
    if startup_name.lower() in deck_text:
        consistency_logs.append("Pitch Deck contains startup name")
        score += 1.5
    else:
        consistency_logs.append("WARNING: Startup Name missing in Pitch Deck")
        passed = False

    # 2. Layout Validation Agent Checks
    # Verify slide formats and details
    if len(slides) == 12:
        layout_logs.append("Layout check: Pitch deck has exactly 12 slides")
        score += 1.5
    else:
        layout_logs.append("WARNING: Slide count is not 12")
        passed = False

    # Verify no text overflows (long bullet lists or long titles)
    overflow = False
    for slide in slides:
        if len(slide.get("title", "")) > 100 or len(slide.get("bullets", [])) > 10:
            overflow = True
            break
    if not overflow:
        layout_logs.append("Layout check: No text overflow detected on slides")
        score += 1.0
    else:
        layout_logs.append("WARNING: Slide text box overflow detected")
        passed = False

    # Verify files exists on disk
    ppt_file = Path(pitch_artifact.get("pptx", ""))
    pdf_file = Path(pitch_artifact.get("pdf", ""))
    if ppt_file.exists() and pdf_file.exists():
        layout_logs.append("Layout check: PPTX and PDF widescreen exports created")
        score += 1.0
    else:
        layout_logs.append("WARNING: Missing PPTX or PDF widescreen assets")
        passed = False

    return consistency_logs, layout_logs, min(score, 10.0), passed


def _write_script(master_profile: dict[str, Any], output_path: Path) -> dict[str, str]:
    prompt = (
        "You are the Pitch Speech Agent. Generate 3 synchronized versions of the pitch script for the startup:\n"
        f"Startup Name: {master_profile.get('startup_name')}\n"
        f"Brief Description: {master_profile.get('tagline')}\n"
        f"Narrative Blueprint: {master_profile.get('asset_blueprint')}\n\n"
        "Generate strict JSON with keys: pitch_60s (a 60-second elevator pitch), pitch_3m (a 3-minute business pitch), pitch_5m (a 5-minute detailed investor pitch), and q_and_a (an array of 3 investor Q&A pairs).\n"
        "STRICT CONTENT BOUNDARY: Do not include any platform reference or technical AI pipeline details. No fake metrics."
    )
    model = os.getenv("DELIVERER_MODEL", "google/gemma-3-27b-it")

    fallback_60 = f"Hello. We are building {master_profile.get('startup_name')}. Tagline: {master_profile.get('tagline')}. We solve: {master_profile.get('problem')}"
    fallback_3m = f"Hello investors. {master_profile.get('startup_name')} solves the following problem: {master_profile.get('problem')}. Our solution: {master_profile.get('solution')}. Target market opportunity: {master_profile.get('market_opportunity')}"
    fallback_5m = f"Hello board members. Today we present {master_profile.get('startup_name')}. We address: {master_profile.get('problem')}. Our visual identity aligns with our values. Key features include: {', '.join(master_profile.get('key_features', []))}"

    try:
        response = openrouter_chat(
            model=model,
            messages=[{"role": "system", "content": prompt}],
            temperature=0.35,
        )
        data = extract_json(response)
        pitch_60s = str(data.get("pitch_60s", fallback_60))
        pitch_3m = str(data.get("pitch_3m", fallback_3m))
        pitch_5m = str(data.get("pitch_5m", fallback_5m))
        q_and_a = data.get("q_and_a", [])
    except Exception:
        pitch_60s = fallback_60
        pitch_3m = fallback_3m
        pitch_5m = fallback_5m
        q_and_a = [
            {"question": "What is the market entry strategy?", "answer": "Focusing on direct user outreach and community partnerships."},
            {"question": "How do you scale operations?", "answer": "By leveraging automation and building reusable system modules."},
            {"question": "What is the biggest operational risk?", "answer": "Customer acquisition cost, which we mitigate via organic content marketing."}
        ]

    startup_name = str(master_profile.get("startup_name", "Startup"))
    script_text = [
        f"# {startup_name} Presentation Speech Scripts",
        "",
        "## 1. 60-Second Pitch",
        pitch_60s,
        "",
        "## 2. 3-Minute Business Pitch",
        pitch_3m,
        "",
        "## 3. 5-Minute Investor Pitch",
        pitch_5m,
        "",
        "## 4. Q&A Prep Notes"
    ]
    for item in q_and_a:
        script_text.append(f"- Q: {item.get('question', '')}")
        script_text.append(f"  A: {item.get('answer', '')}")

    output_path.write_text("\n".join(script_text), encoding="utf-8")
    return {
        "pitch_60s": pitch_60s,
        "pitch_3m": pitch_3m,
        "pitch_5m": pitch_5m,
        "script_path": str(output_path),
    }


def finalize_delivery(
    master_profile: dict[str, Any],
    website_artifact: dict[str, Any],
    pitch_artifact: dict[str, Any],
    output_dir: str = "outputs",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    consistency_logs, layout_logs, quality_score, approved = _qa_report(
        master_profile, website_artifact, pitch_artifact
    )

    script_path = output_path / "presentation_script.txt"
    speech = _write_script(master_profile, script_path)

    # Deliverables Manifest
    manifest_file = output_path / "manifest.json"
    manifest = {
        "startup_name": str(master_profile.get("startup_name", "Startup")),
        "generated_files": [
            "index.html",
            "styles.css",
            "script.js",
            "startup_pitch.pptx",
            "startup_pitch.pdf",
            "presentation_script.txt"
        ],
        "generation_date": "2026-06-05",
        "version": "1.0",
        "validation_status": "passed" if approved else "failed",
        "quality_score": quality_score
    }
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Zip packaging
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
        archive.write(manifest_file, arcname=manifest_file.name)

    return {
        "status": "generated",
        "quality_score": quality_score,
        "consistency_logs": consistency_logs,
        "layout_logs": layout_logs,
        "approved": approved,
        "script": speech["pitch_5m"],
        "script_60s": speech["pitch_60s"],
        "script_3m": speech["pitch_3m"],
        "script_path": str(script_path),
        "package": str(package_path),
        "manifest": manifest,
    }
