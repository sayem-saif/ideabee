from __future__ import annotations

import os
import zipfile
from pathlib import Path

from providers import ProviderError, extract_json, hf_chat, openrouter_chat


def _render_static_site(polished_idea: dict[str, object], research_report: dict[str, object]) -> tuple[str, str, str]:
    title = str(polished_idea.get("startup_name", "IdeaBee"))
    pitch = str(polished_idea.get("elevator_pitch", ""))
    features = polished_idea.get("key_features", [])
    feature_cards = "".join(f"<li>{feature}</li>" for feature in features)
    summary = str(research_report.get("summary", "Market research ready."))

    html = f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{title}</title>
    <link rel=\"stylesheet\" href=\"styles.css\" />
  </head>
  <body>
    <main class=\"shell\">
      <section class=\"hero\">
        <p class=\"eyebrow\">IdeaBee</p>
        <h1>{title}</h1>
        <p class=\"lead\">{pitch}</p>
        <a class=\"cta\" href=\"#features\">Explore the product</a>
      </section>
      <section id=\"features\" class=\"panel\">
        <h2>Core features</h2>
        <ul>{feature_cards}</ul>
      </section>
      <section class=\"panel\">
        <h2>Research snapshot</h2>
        <p>{summary}</p>
      </section>
    </main>
    <script src=\"script.js\"></script>
  </body>
</html>"""
    css = """*{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,sans-serif;background:radial-gradient(circle at top,#172554,#020617 55%);color:#e2e8f0}.shell{max-width:1100px;margin:0 auto;padding:48px 24px 80px}.hero,.panel{background:rgba(15,23,42,.72);backdrop-filter:blur(18px);border:1px solid rgba(148,163,184,.18);border-radius:24px;box-shadow:0 30px 80px rgba(2,6,23,.35)}.hero{padding:48px}.eyebrow{text-transform:uppercase;letter-spacing:.24em;color:#38bdf8;font-size:.75rem}.hero h1{margin:.25rem 0 1rem;font-size:clamp(2.8rem,6vw,5rem);line-height:.95}.lead{max-width:680px;font-size:1.15rem;color:#cbd5e1}.cta{display:inline-block;margin-top:1.5rem;padding:12px 20px;border-radius:999px;background:linear-gradient(135deg,#38bdf8,#8b5cf6);color:white;text-decoration:none;font-weight:700}.panel{margin-top:24px;padding:28px}.panel h2{margin-top:0}.panel ul{padding-left:20px;display:grid;gap:10px}"""
    js = "document.querySelectorAll('a.cta').forEach((link)=>link.addEventListener('click',()=>console.log('IdeaBee CTA clicked')));"
    return html, css, js


def build_website_artifact(polished_idea: dict[str, object], research_report: dict[str, object], output_dir: str = "outputs") -> dict[str, object]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    index_html = output_path / "index.html"
    styles_css = output_path / "styles.css"
    script_js = output_path / "script.js"
    bundle_zip = output_path / "website_bundle.zip"

    prompt = "Generate JSON with keys html, css, js for a polished startup landing page."
    model = os.getenv("WEBSITE_MODEL", "Qwen/Qwen2.5-Coder-32B-Instruct:nscale")
    html, css, js = _render_static_site(polished_idea, research_report)

    for provider in (
        lambda: hf_chat(model=model, messages=[{"role": "system", "content": prompt}, {"role": "user", "content": f"Idea: {polished_idea}\nResearch: {research_report}"}], temperature=0.3),
        lambda: openrouter_chat(model=model, messages=[{"role": "system", "content": prompt}, {"role": "user", "content": f"Idea: {polished_idea}\nResearch: {research_report}"}], temperature=0.3),
    ):
        try:
            response = provider()
            data = extract_json(response)
            html = str(data.get("html", html))
            css = str(data.get("css", css))
            js = str(data.get("js", js))
            break
        except (ProviderError, ValueError, KeyError, TypeError):
            continue

    index_html.write_text(html, encoding="utf-8")
    styles_css.write_text(css, encoding="utf-8")
    script_js.write_text(js, encoding="utf-8")

    with zipfile.ZipFile(bundle_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(index_html, arcname="index.html")
        archive.write(styles_css, arcname="styles.css")
        archive.write(script_js, arcname="script.js")

    return {
        "status": "generated",
        "files": [str(index_html), str(styles_css), str(script_js)],
        "bundle": str(bundle_zip),
        "idea": polished_idea,
        "research": research_report,
    }
