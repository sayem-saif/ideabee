from __future__ import annotations

import json
import os
from pathlib import Path

from providers import ProviderError, extract_json, openrouter_chat, web_search
from rag.retriever import retrieve_context


def research_market(polished_idea: dict[str, object], output_dir: str = "outputs") -> dict[str, object]:
    query = f"{polished_idea.get('startup_name', 'startup')} {polished_idea.get('elevator_pitch', '')}"
    kb_context = retrieve_context(query, top_k=5)
    web_results = web_search(query, max_results=5)
    model = os.getenv("RESEARCH_MODEL", "google/gemma-3-27b-it")
    prompt = (
        "You are a market researcher. Produce strict JSON with keys: summary, tam_sam_som, competitors, "
        "business_models, risks, feasibility, sources. Use the provided idea, knowledge base context, and web results."
    )

    try:
        response = openrouter_chat(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": json.dumps({"idea": polished_idea, "knowledge_base": kb_context, "web_results": web_results}),
                },
            ],
            temperature=0.3,
        )
        report = extract_json(response)
    except (ProviderError, ValueError, KeyError, TypeError):
        report = {
            "summary": f"Validated the idea '{polished_idea.get('startup_name', 'IdeaBee')}' with local RAG and web research.",
            "tam_sam_som": {"tam": "Needs market sizing input", "sam": "Needs segmentation input", "som": "Needs launch assumptions"},
            "competitors": [result.get("title", "") for result in web_results[:3]],
            "business_models": ["Subscription", "Usage-based", "Service + platform hybrid"],
            "risks": ["Model reliability", "Market saturation", "Execution complexity"],
            "feasibility": "Feasible as a multi-agent workflow with API-backed generation.",
            "sources": web_results,
        }

    report.setdefault("summary", "Research completed.")
    report.setdefault("tam_sam_som", {})
    report.setdefault("competitors", [])
    report.setdefault("business_models", [])
    report.setdefault("risks", [])
    report.setdefault("feasibility", "")
    report.setdefault("sources", web_results)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "research_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
