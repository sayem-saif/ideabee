from __future__ import annotations

from typing import Any

DEFAULT_BRAND_IDENTITY = {
    "brand_personality": "Innovative, Professional, Customer-centric",
    "tone": "Confident and Professional",
    "brand_values": ["Innovation", "Transparency", "User Empowerment"],
    "tagline": "Transforming the future, today.",
    "visual_style": "Modern, clean, high-contrast widescreen",
    "primary_color": "#0284c7",
    "secondary_color": "#64748b",
    "typography": "Plus Jakarta Sans & Outfit",
}

DEFAULT_ASSET_BLUEPRINT = {
    "hero_message": "Innovating for a better tomorrow",
    "problem_story": "A significant challenge faces our target users every day.",
    "solution_story": "Our product simplifies operations and unlocks new opportunities.",
    "market_story": "The market is expanding rapidly with a high growth rate.",
    "business_story": "Our tiered pricing model aligns costs directly with user value.",
    "competitive_story": "Differentiation lies in our speed, simplicity, and premium design.",
    "closing_story": "Partner with us to capture early market traction.",
    "call_to_action": "Get Started",
}


def build_master_profile(
    polished_brief: dict[str, Any],
    research_report: dict[str, Any],
    brand_identity: dict[str, Any] | None = None,
    asset_blueprint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = {}
    
    # 1. Basic brief details
    profile["startup_name"] = str(polished_brief.get("startup_name", "IdeaBee"))
    profile["tagline"] = str(polished_brief.get("uvp", "Next-Gen Innovation"))
    profile["industry"] = str(research_report.get("category", "Other"))
    profile["problem"] = str(polished_brief.get("problem", ""))
    profile["solution"] = str(polished_brief.get("solution", ""))
    profile["target_users"] = str(polished_brief.get("target_audience", ""))
    profile["key_features"] = list(polished_brief.get("key_features", []))
    profile["value_proposition"] = str(polished_brief.get("uvp", ""))
    
    # 2. Research & competitor details
    competitors = research_report.get("competitors", [])
    profile["competitors"] = list(competitors) if competitors else ["Competitor analysis unavailable"]
    profile["market_opportunity"] = str(research_report.get("summary", "Market details ready."))
    profile["business_model"] = ", ".join(research_report.get("business_models", [])) if research_report.get("business_models") else "Subscription model"
    
    # 3. Branding
    brand = dict(DEFAULT_BRAND_IDENTITY)
    if brand_identity:
        brand.update(brand_identity)
    profile["brand_identity"] = brand
    
    # 4. Narrative blueprint
    blueprint = dict(DEFAULT_ASSET_BLUEPRINT)
    if asset_blueprint:
        blueprint.update(asset_blueprint)
    profile["asset_blueprint"] = blueprint
    
    # 5. Sourced Research Claims
    claims = []
    # If the researcher returned claims, use them; otherwise compile default claims from report
    raw_claims = research_report.get("research_claims")
    if isinstance(raw_claims, list):
        for claim in raw_claims:
            if isinstance(claim, dict):
                claims.append({
                    "statement": str(claim.get("statement", "")),
                    "source": str(claim.get("source", "Market Research")),
                    "confidence": str(claim.get("confidence", "high")),
                    "used_in_assets": True
                })
    else:
        # Build default claims from tam_sam_som/summary
        tam_sam = research_report.get("tam_sam_som")
        if isinstance(tam_sam, dict):
            for k, v in tam_sam.items():
                if v and "Needs" not in str(v):
                    claims.append({
                        "statement": f"{k.upper()}: {v}",
                        "source": "Market opportunity estimates",
                        "confidence": "high",
                        "used_in_assets": True
                    })
        else:
            claims.append({
                "statement": "Market data unavailable",
                "source": "Research assessment",
                "confidence": "medium",
                "used_in_assets": False
            })
            
    # Filter out low confidence claims
    profile["research_claims"] = [c for c in claims if c["confidence"].lower() != "low"]
    profile["confidence_score"] = "High" if len(profile["research_claims"]) > 1 else "Medium"
    
    # 6. Anti-hallucination details
    profile["team"] = str(polished_brief.get("team", "To Be Determined"))
    profile["financials"] = str(polished_brief.get("financials", "Not Provided"))
    profile["research_summary"] = str(research_report.get("summary", ""))
    
    return profile
