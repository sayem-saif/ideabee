from __future__ import annotations

import os
import zipfile
from pathlib import Path
from typing import Any

from providers import ProviderError, extract_json, hf_chat, openrouter_chat


def _render_static_site(master_profile: dict[str, Any]) -> tuple[str, str, str]:
    title = str(master_profile.get("startup_name", "the company"))
    tagline = str(master_profile.get("tagline", ""))
    
    brand = master_profile.get("brand_identity", {})
    primary = str(brand.get("primary_color", "#0284c7"))
    secondary = str(brand.get("secondary_color", "#64748b"))
    font = brand.get("typography", "Plus Jakarta Sans")
    if isinstance(font, dict):
        font = font.get("primary") or font.get("header") or font.get("body") or list(font.values())[0]
    font = str(font)


    blueprint = master_profile.get("asset_blueprint", {})
    hero_msg = str(blueprint.get("hero_message", "Innovation Simplified"))
    prob_story = str(blueprint.get("problem_story", ""))
    sol_story = str(blueprint.get("solution_story", ""))
    comp_story = str(blueprint.get("competitive_story", ""))
    cta_text = str(blueprint.get("call_to_action", "Get Started"))

    features = master_profile.get("key_features", [])
    feature_cards = "".join(
        f"<div class=\"card\"><h3>{f}</h3><p>Key capability designed to support your operational goals.</p></div>"
        for f in features
    )
    
    # Testimonials policy: only if provided by user in idea
    testimonials_html = ""
    raw_idea = str(master_profile.get("raw_idea", "")).lower()
    if "testimonial" in raw_idea or "happy customer" in raw_idea:
        testimonials_html = """
      <section id="testimonials" class="panel fade-in">
        <h2>What Our Customers Say</h2>
        <div class="testimonial-box">
          <p class="quote">"This solution transformed our business workflow from day one."</p>
          <p class="author">— Early Pilot Partner</p>
        </div>
      </section>
        """

    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title} — {tagline}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <header class="navbar">
      <div class="logo">{title}</div>
      <nav>
        <a href="#about">About</a>
        <a href="#features">Features</a>
        <a href="#benefits">Benefits</a>
        <a href="#contact" class="cta-nav">{cta_text}</a>
      </nav>
    </header>
    <main class="shell">
      <section class="hero fade-in">
        <p class="eyebrow">{title}</p>
        <h1>{hero_msg}</h1>
        <p class="lead">{tagline}</p>
        <div class="hero-actions">
          <a class="cta" href="#features">Explore Features</a>
          <a class="cta-secondary" href="#benefits">Learn More</a>
        </div>
      </section>

      <section id="about" class="grid-2 fade-in">
        <div class="panel">
          <h2>The Problem</h2>
          <p>{prob_story}</p>
        </div>
        <div class="panel highlight">
          <h2>Our Solution</h2>
          <p>{sol_story}</p>
        </div>
      </section>

      <section id="features" class="features-section fade-in">
        <h2>Key Capabilities</h2>
        <div class="features-grid">
          {feature_cards}
        </div>
      </section>

      <section id="benefits" class="panel fade-in">
        <h2>Why Choose Us</h2>
        <p>{comp_story}</p>
      </section>

      {testimonials_html}

      <section id="contact" class="panel cta-box fade-in">
        <h2>Ready to work with {title}?</h2>
        <p>Subscribe to stay updated on our journey and early pilot programs.</p>
        <form class="subscribe-form" onsubmit="return false;">
          <input type="email" placeholder="Enter your email" required />
          <button type="submit" class="cta">{cta_text}</button>
        </form>
      </section>
    </main>
    <footer class="footer">
      <p>&copy; 2026 {title}. All rights reserved.</p>
    </footer>
    <script src="script.js"></script>
  </body>
</html>"""

    css = f"""* {{ box-sizing: border-box; scroll-behavior: smooth; }}
body {{ margin: 0; font-family: '{font}', sans-serif; background: #090d16; background-image: radial-gradient(circle at top, #1e1b4b, #090d16 60%); color: #f8fafc; line-height: 1.6; }}
h1, h2, h3, .logo {{ font-family: 'Outfit', sans-serif; font-weight: 700; }}
.navbar {{ display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; padding: 24px; position: sticky; top: 0; backdrop-filter: blur(12px); z-index: 100; }}
.logo {{ font-size: 1.5rem; color: {primary}; background: linear-gradient(135deg, {primary}, {secondary}); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
nav a {{ color: #cbd5e1; text-decoration: none; margin-left: 24px; font-weight: 600; font-size: 0.95rem; transition: color 0.2s; }}
nav a:hover {{ color: {primary}; }}
.cta-nav {{ background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.4); padding: 8px 16px; border-radius: 99px; }}
.cta-nav:hover {{ background: rgba(56, 189, 248, 0.25); color: #fff; }}
.shell {{ max-width: 1200px; margin: 0 auto; padding: 48px 24px 80px; display: grid; gap: 48px; }}
.hero {{ text-align: center; padding: 80px 24px; background: rgba(15, 23, 42, 0.55); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 32px; backdrop-filter: blur(24px); box-shadow: 0 40px 100px rgba(0,0,0,0.4); }}
.eyebrow {{ text-transform: uppercase; letter-spacing: 0.2em; color: {secondary}; font-weight: 600; font-size: 0.85rem; margin-bottom: 16px; }}
.hero h1 {{ font-size: clamp(2.5rem, 6vw, 4.5rem); margin: 0 0 24px; line-height: 1.1; color: #fff; }}
.lead {{ max-width: 760px; margin: 0 auto 32px; font-size: 1.25rem; color: #94a3b8; }}
.hero-actions {{ display: flex; gap: 16px; justify-content: center; }}
.cta, .cta-secondary {{ display: inline-block; padding: 14px 28px; border-radius: 99px; text-decoration: none; font-weight: 700; transition: transform 0.2s, box-shadow 0.2s; border: none; cursor: pointer; }}
.cta {{ background: {primary}; color: #fff; box-shadow: 0 8px 20px rgba(2,132,199,0.25); }}
.cta:hover {{ transform: translateY(-2px); box-shadow: 0 12px 28px rgba(2,132,199,0.4); }}
.cta-secondary {{ background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #fff; }}
.cta-secondary:hover {{ background: rgba(255,255,255,0.1); transform: translateY(-2px); }}
.grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
@media(max-width: 768px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
.panel {{ background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 24px; padding: 36px; backdrop-filter: blur(12px); }}
.panel.highlight {{ border-color: {primary}; background-image: linear-gradient(135deg, rgba(2, 132, 199, 0.05), transparent); }}
.panel h2 {{ margin: 0 0 16px; font-size: 1.75rem; color: #fff; }}
.features-section {{ text-align: center; }}
.features-section h2 {{ font-size: 2.25rem; margin-bottom: 32px; color: #fff; }}
.features-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; }}
.card {{ background: rgba(15, 23, 42, 0.45); border: 1px solid rgba(255, 255, 255, 0.04); border-radius: 20px; padding: 28px; text-align: left; transition: transform 0.2s, border-color 0.2s; }}
.card:hover {{ transform: translateY(-4px); border-color: {primary}; }}
.card h3 {{ margin: 0 0 12px; color: {primary}; font-size: 1.25rem; }}
.card p {{ margin: 0; color: #94a3b8; font-size: 0.95rem; }}
.comp-list {{ padding-left: 20px; margin: 0; display: grid; gap: 12px; color: #cbd5e1; }}
.metric {{ margin-top: 24px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.08); display: flex; justify-content: space-between; }}
.metric .label {{ color: #94a3b8; }}
.metric .val {{ color: {secondary}; font-weight: 700; }}
.cta-box {{ text-align: center; max-width: 800px; margin: 0 auto; }}
.subscribe-form {{ display: flex; gap: 12px; max-width: 500px; margin: 24px auto 0; }}
.subscribe-form input {{ flex: 1; padding: 14px 20px; border-radius: 99px; border: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.2); color: #fff; font-size: 1rem; outline: none; }}
.subscribe-form input:focus {{ border-color: {primary}; }}
@media(max-width: 500px) {{ .subscribe-form {{ flex-direction: column; }} .subscribe-form button {{ width: 100%; }} }}
.footer {{ text-align: center; padding: 48px 24px; color: #64748b; font-size: 0.9rem; border-top: 1px solid rgba(255,255,255,0.03); margin-top: 80px; }}
.fade-in {{ animation: fadeInUp 0.8s ease forwards; }}
.testimonial-box {{ border-left: 4px solid {primary}; padding-left: 20px; margin: 20px 0; }}
.quote {{ font-style: italic; font-size: 1.15rem; color: #cbd5e1; }}
.author {{ font-weight: 600; color: {secondary}; }}
@keyframes fadeInUp {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}"""

    js = """document.querySelectorAll('.subscribe-form').forEach(form => {
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const input = form.querySelector('input');
    if (input && input.value) {
      alert('Thanks for subscribing! We will notify you at: ' + input.value);
      input.value = '';
    }
  });
});"""

    return html, css, js


def build_website_artifact(master_profile: dict[str, Any], output_dir: str = "outputs") -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    index_html = output_path / "index.html"
    styles_css = output_path / "styles.css"
    script_js = output_path / "script.js"
    bundle_zip = output_path / "website_bundle.zip"

    prompt = (
        "You are an expert full-stack developer (Website Generator Agent). Generate website content strictly from the Master Startup Profile, Brand Identity, and Asset Blueprint.\n"
        "Generate strict JSON with keys: html, css, js. The CSS must utilize the primary and secondary branding colors dynamically.\n"
        "Ensure all features, tags, problem, and solution stories match the blueprint narrative exactly.\n"
        "STRICT CONTENT BOUNDARY: Do not include any technical terminology relating to AI builder, agents, workflows, or platform names (e.g. 'IdeaBee', 'agents').\n"
        f"Master Profile Context: {master_profile}\n"
    )
    
    model = os.getenv("WEBSITE_MODEL", "Qwen/Qwen2.5-Coder-32B-Instruct:nscale")
    html, css, js = _render_static_site(master_profile)

    for provider in (
        lambda: hf_chat(model=model, messages=[{"role": "system", "content": prompt}], temperature=0.3),
        lambda: openrouter_chat(model=model, messages=[{"role": "system", "content": prompt}], temperature=0.3),
    ):
        try:
            response = provider()
            data = extract_json(response)
            html = str(data.get("html", html))
            css = str(data.get("css", css))
            js = str(data.get("js", js))
            break
        except Exception:
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
        "html": html,
        "css": css,
        "js": js,
        "master_profile": master_profile,
    }


def refine_website_artifact(
    master_profile: dict[str, Any],
    current_html: str,
    current_css: str,
    current_js: str,
    refinement_prompt: str,
    output_dir: str = "outputs"
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    index_html = output_path / "index.html"
    styles_css = output_path / "styles.css"
    script_js = output_path / "script.js"
    bundle_zip = output_path / "website_bundle.zip"

    system_prompt = (
        "You are an expert website developer. You have generated a website with the following files:\n"
        f"HTML:\n{current_html}\n\n"
        f"CSS:\n{current_css}\n\n"
        f"JS:\n{current_js}\n\n"
        "Your task is to refine this website based on the user's specific request. Maintain the responsive visual design "
        "and brand colors. Do not strip out the startup features or narrative blueprint details.\n"
        "Here is the master startup context:\n"
        f"Master Profile: {master_profile}\n\n"
        "Return strict JSON with keys: html, css, js. Include the entire updated code for each key.\n"
        "STRICT CONTENT BOUNDARY: Do not include any technical terminology relating to AI builder, agents, workflows, or platform names."
    )

    model = os.getenv("WEBSITE_MODEL", "Qwen/Qwen2.5-Coder-32B-Instruct:nscale")
    html, css, js = current_html, current_css, current_js

    if "red" in refinement_prompt.lower() or "emerald" in refinement_prompt.lower() or "green" in refinement_prompt.lower():
        color = "#ef4444" if "red" in refinement_prompt.lower() else "#10b981"
        css = current_css.replace("#38bdf8", color).replace("#8b5cf6", color)

    for provider in (
        lambda: hf_chat(model=model, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": refinement_prompt}], temperature=0.35),
        lambda: openrouter_chat(model=model, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": refinement_prompt}], temperature=0.35),
    ):
        try:
            response = provider()
            data = extract_json(response)
            html = str(data.get("html", html))
            css = str(data.get("css", css))
            js = str(data.get("js", js))
            break
        except Exception:
            continue

    index_html.write_text(html, encoding="utf-8")
    styles_css.write_text(css, encoding="utf-8")
    script_js.write_text(js, encoding="utf-8")

    with zipfile.ZipFile(bundle_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(index_html, arcname="index.html")
        archive.write(styles_css, arcname="styles.css")
        archive.write(script_js, arcname="script.js")

    return {
        "status": "refined",
        "files": [str(index_html), str(styles_css), str(script_js)],
        "bundle": str(bundle_zip),
        "html": html,
        "css": css,
        "js": js,
        "master_profile": master_profile,
    }
