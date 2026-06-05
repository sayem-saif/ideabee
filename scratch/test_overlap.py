import json
import re
from pathlib import Path

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

def test():
    debug_path = Path("outputs/debug_consistency.json")
    if not debug_path.exists():
        print("Debug file not found")
        return
        
    data = json.loads(debug_path.read_text(encoding="utf-8"))
    profile = data.get("master_profile", {})
    web_html = data.get("web_html", "")
    
    print("=== Master Profile Keys ===")
    print(list(profile.keys()))
    
    print("\n=== Narrative Parts & Overlaps ===")
    website_words = _content_words(web_html)
    
    blueprint = profile.get("asset_blueprint", {})
    narrative_parts = {
        "problem": profile.get("problem", ""),
        "solution": profile.get("solution", ""),
        "problem_story": blueprint.get("problem_story", ""),
        "solution_story": blueprint.get("solution_story", ""),
        "hero_message": blueprint.get("hero_message", ""),
    }
    
    for name, part in narrative_parts.items():
        words = _content_words(str(part))
        overlap = words & website_words
        ratio = len(overlap) / max(len(words), 1)
        passed = len(overlap) >= 3 or ratio >= 0.35
        print(f"[{name}] words count: {len(words)}, overlap count: {len(overlap)}, ratio: {ratio:.3f}, passed: {passed}")
        if not passed:
            print(f"  Part text: {part}")
            print(f"  Part words: {words}")

if __name__ == "__main__":
    test()
