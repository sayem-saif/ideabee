from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.util import Inches, Pt

from providers import ProviderError, extract_json, hf_chat, openrouter_chat


def _render_default_slides(polished_idea: dict[str, object], research_report: dict[str, object]) -> list[dict[str, Any]]:
    return [
        {"title": "Title", "bullets": [str(polished_idea.get("startup_name", "IdeaBee")), str(polished_idea.get("elevator_pitch", ""))], "notes": "Introduce the product and the vision."},
        {"title": "Problem", "bullets": [str(polished_idea.get("problem", ""))], "notes": "Explain the pain."},
        {"title": "Solution", "bullets": [str(polished_idea.get("solution", ""))], "notes": "Show the value."},
        {"title": "Market Opportunity", "bullets": [str(research_report.get("summary", "")), str(research_report.get("feasibility", ""))], "notes": "Position the category."},
        {"title": "Product Demo", "bullets": ["Idea polishing", "Research synthesis", "Website and deck generation"], "notes": "Walk through the workflow."},
        {"title": "Business Model", "bullets": ["Subscription", "Premium exports", "Service add-ons"], "notes": "Describe revenue."},
        {"title": "Traction / Roadmap", "bullets": ["MVP launch", "Quality improvements", "More integrations"], "notes": "Show momentum."},
        {"title": "Competition", "bullets": [", ".join(research_report.get("competitors", [])[:3]) or "Competitive landscape still emerging"], "notes": "Differentiate the product."},
        {"title": "Go-to-Market", "bullets": ["Founders communities", "Product-led growth", "Templates and examples"], "notes": "Explain acquisition."},
        {"title": "Team", "bullets": ["Builder-friendly architecture", "AI-native workflow"], "notes": "Keep concise if founders are not set."},
        {"title": "Financial Projections", "bullets": ["Early revenue from subscriptions", "Upsell deployment and premium services"], "notes": "Keep assumptions clear."},
        {"title": "Ask", "bullets": ["Funding or feedback", "Pilot customers", "Launch support"], "notes": "Close with a clear ask."},
    ]


def _generate_outline(polished_idea: dict[str, object], research_report: dict[str, object]) -> list[dict[str, Any]]:
    prompt = "Return strict JSON with a slide_list array of 12 slides. Each slide needs title, bullets, notes. Bullets should be concise and investor-ready."
    model = os.getenv("PITCH_MODEL", "google/gemma-3-27b-it:featherless-ai")
    fallback = _render_default_slides(polished_idea, research_report)

    for provider in (
        lambda: hf_chat(model=model, messages=[{"role": "system", "content": prompt}, {"role": "user", "content": f"Idea: {polished_idea}\nResearch: {research_report}"}], temperature=0.35),
        lambda: openrouter_chat(model=model, messages=[{"role": "system", "content": prompt}, {"role": "user", "content": f"Idea: {polished_idea}\nResearch: {research_report}"}], temperature=0.35),
    ):
        try:
            response = provider()
            data = extract_json(response)
            slides = data.get("slide_list") or data.get("slides") or data
            if isinstance(slides, list) and len(slides) == 12:
                normalized: list[dict[str, Any]] = []
                for slide in slides:
                    if isinstance(slide, dict):
                        normalized.append(
                            {
                                "title": str(slide.get("title", "Slide")),
                                "bullets": [str(item) for item in slide.get("bullets", [])],
                                "notes": str(slide.get("notes", "")),
                            }
                        )
                if len(normalized) == 12:
                    return normalized
        except (ProviderError, ValueError, KeyError, TypeError):
            continue

    return fallback


def _add_textbox(slide, left: float, top: float, width: float, height: float, text: str, font_size: int, bold: bool = False) -> None:
    textbox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    text_frame = textbox.text_frame
    text_frame.word_wrap = True
    paragraph = text_frame.paragraphs[0]
    paragraph.text = text
    paragraph.font.size = Pt(font_size)
    paragraph.font.bold = bold
    paragraph.font.name = "Aptos"


def _build_pptx(slides: list[dict[str, Any]], output_path: Path, template_path: str | None = None) -> None:
    prs = Presentation(template_path) if template_path and Path(template_path).exists() else Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    layout = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[0]

    for slide_data in slides:
        slide = prs.slides.add_slide(layout)
        _add_textbox(slide, 0.55, 0.35, 12.1, 0.7, slide_data["title"], 26, bold=True)
        body = slide.shapes.add_textbox(Inches(0.7), Inches(1.35), Inches(11.7), Inches(4.9))
        tf = body.text_frame
        tf.word_wrap = True
        tf.clear()
        for index, bullet in enumerate(slide_data.get("bullets", [])):
            paragraph = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
            paragraph.text = bullet
            paragraph.level = 0
            paragraph.font.size = Pt(22)
            paragraph.font.name = "Aptos"
        _add_textbox(slide, 0.7, 6.45, 11.5, 0.35, slide_data.get("notes", ""), 11)

    prs.save(str(output_path))


def _export_pdf_via_soffice(pptx_path: Path, pdf_path: Path) -> bool:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return False
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(pdf_path.parent), str(pptx_path)], check=True, capture_output=True)
    converted = pptx_path.with_suffix(".pdf")
    if converted.exists() and converted != pdf_path:
        converted.replace(pdf_path)
    return pdf_path.exists()


def _export_pdf_fallback(slides: list[dict[str, Any]], pdf_path: Path) -> None:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    width, height = letter
    y = height - 48
    c.setFont("Helvetica-Bold", 18)
    c.drawString(48, y, "IdeaBee Pitch Deck")
    y -= 32
    c.setFont("Helvetica", 11)
    for slide in slides:
        c.setFont("Helvetica-Bold", 13)
        c.drawString(48, y, slide["title"])
        y -= 18
        c.setFont("Helvetica", 10)
        for bullet in slide.get("bullets", []):
            c.drawString(64, y, f"• {bullet}")
            y -= 14
            if y < 72:
                c.showPage()
                y = height - 48
        y -= 10
        if y < 72:
            c.showPage()
            y = height - 48
    c.save()


def build_pitch_deck(polished_idea: dict[str, object], research_report: dict[str, object], output_dir: str = "outputs") -> dict[str, object]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    slides = _generate_outline(polished_idea, research_report)
    slides_json = output_path / "startup_pitch_slides.json"
    pptx_path = output_path / "startup_pitch.pptx"
    pdf_path = output_path / "startup_pitch.pdf"

    slides_json.write_text(json.dumps(slides, indent=2), encoding="utf-8")

    template_path = os.getenv("PITCH_TEMPLATE_PATH", "").strip() or None
    _build_pptx(slides, pptx_path, template_path=template_path)
    if not _export_pdf_via_soffice(pptx_path, pdf_path):
        _export_pdf_fallback(slides, pdf_path)

    return {
        "status": "generated",
        "slides": slides,
        "slides_json": str(slides_json),
        "pptx": str(pptx_path),
        "pdf": str(pdf_path),
        "idea": polished_idea,
        "research": research_report,
    }
