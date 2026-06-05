from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from pipeline import ensure_directories, run_discovery, run_assets_generation
from agents import build_website_artifact, build_pitch_deck, finalize_delivery, refine_website_artifact
from utils import push_profile_version, validate_and_sanitize
from providers import openrouter_chat, hf_chat, extract_json

load_dotenv()

# Page config
st.set_page_config(page_title="IdeaBee — AI Startup Builder", page_icon="🐝", layout="wide")
ensure_directories()

# Premium Glassmorphism Dark Theme CSS
st.markdown("""
<style>
    /* Hide sidebar and collapse button */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
    
    /* Global Background and Typography */
    .stApp {
        background-color: #0b0f19;
        background-image: 
            radial-gradient(at 10% 20%, rgba(2, 132, 199, 0.08) 0px, transparent 50%),
            radial-gradient(at 90% 80%, rgba(100, 116, 139, 0.08) 0px, transparent 50%);
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
    }
    
    /* Headings */
    h1, h2, h3, h4 {
        font-family: 'Outfit', 'Inter', sans-serif !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
        letter-spacing: -0.02em;
    }
    
    /* Solid color premium buttons (#0284c7) */
    .stButton>button {
        background-color: #0284c7 !important;
        color: #ffffff !important;
        border: 1px solid #0369a1 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 10px 24px !important;
        transition: background-color 0.2s, transform 0.1s, box-shadow 0.2s !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.15) !important;
    }
    .stButton>button:hover {
        background-color: #0369a1 !important;
        border-color: #075985 !important;
        box-shadow: 0 4px 16px rgba(2, 132, 199, 0.3) !important;
        transform: translateY(-1px);
    }
    .stButton>button:active {
        transform: translateY(0px);
    }
    
    /* Solid color download buttons */
    .stDownloadButton>button {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
        transition: background-color 0.2s, transform 0.1s !important;
        width: 100%;
    }
    .stDownloadButton>button:hover {
        background-color: #334155 !important;
        border-color: #475569 !important;
        transform: translateY(-1px);
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(15, 23, 42, 0.65) !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        margin-bottom: 24px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Floating animated logo */
    @keyframes float {
        0% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-8px) rotate(2deg); }
        100% { transform: translateY(0px) rotate(0deg); }
    }
    .logo-container {
        text-align: center;
        margin-bottom: 12px;
        margin-top: 12px;
    }
    .floating-logo {
        display: inline-block;
        font-size: 3.5rem;
        animation: float 5s ease-in-out infinite;
    }
    
    /* Clean log box */
    .log-box {
        background-color: #020617;
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 16px;
        border-radius: 10px;
        color: #38bdf8;
        font-size: 0.95rem;
        text-align: center;
        font-weight: 500;
    }
    
    /* Iframe preview border */
    .preview-frame {
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        overflow: hidden;
    }

    /* Tabs styling overrides */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.4);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.04);
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        border: none;
        padding: 0px 16px;
        transition: all 0.2s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #f8fafc;
        background-color: rgba(255, 255, 255, 0.05);
    }
    .stTabs [aria-selected="true"] {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to clean text outputs (strips quotes, JSON escapes)
def clean_text_output(text: str) -> str:
    if not isinstance(text, str):
        return str(text)
    cleaned = text.strip()
    if cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1]
    elif cleaned.startswith("'") and cleaned.endswith("'"):
        cleaned = cleaned[1:-1]
    cleaned = cleaned.replace("\\n", "\n").replace('\\"', '"')
    return cleaned


def refine_master_profile(master_profile: dict[str, Any], instruction: str) -> dict[str, Any]:
    prompt = (
        "You are a Startup Profile Editor. Your task is to update the Master Startup Profile JSON based on the user's refinement instructions.\n"
        "Return the updated Master Startup Profile as strict JSON matching the original schema.\n"
        "Rules:\n"
        "1. Do not invent details not requested.\n"
        "2. Keep it consistent with the overall brand identity.\n"
        "3. STRICT CONTENT BOUNDARY: Do not include any technical terminology relating to the AI builder, agents, workflows, prompts, ChromaDB, etc.\n"
        "4. If they edit colors, typography, or narrative blueprint elements, update those sub-fields appropriately."
    )
    model = os.getenv("WEBSITE_MODEL", "google/gemma-3-27b-it")
    
    for provider in (
        lambda: openrouter_chat(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Current Profile:\n{json.dumps(master_profile, indent=2)}\n\nInstructions: {instruction}"}
            ],
            temperature=0.2
        ),
        lambda: hf_chat(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Current Profile:\n{json.dumps(master_profile, indent=2)}\n\nInstructions: {instruction}"}
            ],
            temperature=0.2
        )
    ):
        try:
            response = provider()
            data = extract_json(response)
            if isinstance(data, dict) and "startup_name" in data:
                return data
        except Exception:
            continue
    return master_profile


def regenerate_all_assets(master_profile: dict[str, Any], startup_name: str, output_dir: str = "outputs") -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    # Regenerate website, pitch deck, speech notes and package ZIP directly from the profile
    website = build_website_artifact(master_profile, output_dir=output_dir)
    website = validate_and_sanitize(website, startup_name)

    pitch = build_pitch_deck(master_profile, output_dir=output_dir)
    pitch = validate_and_sanitize(pitch, startup_name)

    delivery = finalize_delivery(master_profile, website, pitch, output_dir=output_dir)
    delivery = validate_and_sanitize(delivery, startup_name)

    return website, pitch, delivery


# Initialize Session States
if "polished" not in st.session_state:
    st.session_state.polished = None
if "research" not in st.session_state:
    st.session_state.research = None
if "website" not in st.session_state:
    st.session_state.website = None
if "pitch" not in st.session_state:
    st.session_state.pitch = None
if "delivery" not in st.session_state:
    st.session_state.delivery = None
if "master_profile" not in st.session_state:
    st.session_state.master_profile = None
if "version_history" not in st.session_state:
    st.session_state.version_history = []
if "raw_idea" not in st.session_state:
    st.session_state.raw_idea = ""
if "generation_complete" not in st.session_state:
    st.session_state.generation_complete = False

# App Header
st.markdown("""
<div class="logo-container">
    <span class="floating-logo">🐝</span>
</div>
""", unsafe_allow_html=True)

col_title, col_reset = st.columns([8, 2])
with col_title:
    st.title("IdeaBee")
    st.markdown("<p style='color:#94a3b8; font-size:1.1rem; margin-top:-10px;'>Widescreen AI Startup Builder & Refiner</p>", unsafe_allow_html=True)
with col_reset:
    if st.session_state.polished:
        if st.button("New Startup Idea"):
            st.session_state.polished = None
            st.session_state.research = None
            st.session_state.website = None
            st.session_state.pitch = None
            st.session_state.delivery = None
            st.session_state.master_profile = None
            st.session_state.version_history = []
            st.session_state.raw_idea = ""
            st.session_state.generation_complete = False
            st.rerun()

st.divider()

# ----------------- STAGE 1: STARTUP DISCOVERY -----------------
if not st.session_state.polished:
    st.markdown("### 🔍 Step 1: Tell us about your idea")
    idea = st.text_area(
        "Enter your raw project description, messy thoughts, or startup notes:",
        value="A platform connecting organic coffee growers directly to local coffee shops",
        height=140,
    )

    if st.button("Discover Names & Polish Concept"):
        if idea.strip():
            with st.spinner("Brainstorming suggested startup names..."):
                st.session_state.raw_idea = idea.strip()
                polished = run_discovery(idea.strip())
                st.session_state.polished = polished
                st.rerun()

# ----------------- STAGE 2: NAMING & GENERATION -----------------
elif st.session_state.polished and not st.session_state.generation_complete:
    polished = st.session_state.polished

    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("### Polished Project Brief")
    st.write(f"**Elevator Pitch:** {polished.get('elevator_pitch')}")
    st.write(f"**Core Problem:** {polished.get('problem')}")
    st.write(f"**Proposed Solution:** {polished.get('solution')}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 🏷️ Step 2: Choose your Startup Name")
    suggestions = polished.get("name_suggestions", ["IdeaBee", "FoundryAI", "LaunchPad", "VentureSpark", "BizBuild"])
    name_choice = st.radio("Pick one of our brainstormed name suggestions:", suggestions)
    custom_name = st.text_input("Or enter your own custom startup name:")
    
    final_name = custom_name.strip() if custom_name.strip() else name_choice

    if st.button("Generate Widescreen Launch Package"):
        log_placeholder = st.empty()
        progress_bar = st.progress(0.0)

        # User-friendly milestone updates
        def update_progress(msg: str, progress: float, delay: float = 0.6):
            progress_bar.progress(progress)
            log_placeholder.markdown(f"<div class='log-box'>{msg}</div>", unsafe_allow_html=True)
            time.sleep(delay)

        update_progress("Analyzing Raw Business Idea...", 0.1)
        update_progress("Locking Startup Branding Details...", 0.25)
        update_progress("Synthesizing Competitor & Market Research...", 0.4)
        update_progress("Compiling Unified Narrative Blueprint...", 0.6)
        update_progress("Assembling Master Startup Profile...", 0.75)
        update_progress("Drafting Landing Page & Pitch Slide Assets...", 0.9)

        # Run backend pipeline
        assets = run_assets_generation(polished, final_name)
        
        st.session_state.polished = assets["polished"]
        st.session_state.research = assets["research"]
        st.session_state.website = assets["website"]
        st.session_state.pitch = assets["pitch"]
        st.session_state.delivery = assets["delivery"]
        st.session_state.master_profile = assets["master_profile"]
        
        # Save initial version to history
        st.session_state.version_history = push_profile_version(
            [],
            assets["master_profile"]
        )
        
        update_progress("Finalizing Delivery ZIP & Reports...", 1.0)
        
        st.session_state.generation_complete = True
        st.rerun()

# ----------------- STAGE 3: OUTPUT DASHBOARD (7 TABS) -----------------
elif st.session_state.generation_complete:
    polished = st.session_state.polished
    research = st.session_state.research
    website = st.session_state.website
    pitch = st.session_state.pitch
    delivery = st.session_state.delivery
    master_profile = st.session_state.master_profile

    st.success(f"🚀 Assets successfully generated for **{master_profile.get('startup_name')}**!")

    # Render the 7 Main Tabs
    tab_titles = [
        "1. Idea Submission",
        "2. Startup Profile",
        "3. Market Research",
        "4. Website Preview",
        "5. Pitch Deck Preview",
        "6. Refinement Center",
        "7. Download Center"
    ]
    t1, t2, t3, t4, t5, t6, t7 = st.tabs(tab_titles)

    # --- TAB 1: IDEA SUBMISSION ---
    with t1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Submitted Idea Details")
        st.write(f"**Original Raw Idea:** {st.session_state.raw_idea}")
        st.write(f"**Target Audience / Customer Segment:** {master_profile.get('target_users')}")
        st.write(f"**Industry Category:** {master_profile.get('industry')}")
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Reset & Start New Idea", key="restart_btn"):
            st.session_state.polished = None
            st.session_state.research = None
            st.session_state.website = None
            st.session_state.pitch = None
            st.session_state.delivery = None
            st.session_state.master_profile = None
            st.session_state.version_history = []
            st.session_state.raw_idea = ""
            st.session_state.generation_complete = False
            st.rerun()

    # --- TAB 2: STARTUP PROFILE ---
    with t2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Master Startup Profile")
        
        col_prof_1, col_prof_2 = st.columns(2)
        with col_prof_1:
            st.write(f"**Startup Name:** {master_profile.get('startup_name')}")
            st.write(f"**Tagline:** {master_profile.get('tagline')}")
            st.write(f"**Value Proposition:** {master_profile.get('value_proposition')}")
            st.write(f"**Business Model Type:** {master_profile.get('business_model')}")
        with col_prof_2:
            brand = master_profile.get("brand_identity", {})
            st.write("**Visual Identity & Style:**")
            st.write(f"- Primary Branding Color: `{brand.get('primary_color', '#0284c7')}`")
            st.write(f"- Secondary Branding Color: `{brand.get('secondary_color', '#64748b')}`")
            st.write(f"- Recommended Typography: `{brand.get('typography', 'Plus Jakarta Sans')}`")
            st.write(f"- Visual Tone: `{brand.get('tone', 'Confident')}`")

        st.markdown("#### Narrative Asset Blueprint")
        blueprint = master_profile.get("asset_blueprint", {})
        st.write(f"**Hero Message:** {blueprint.get('hero_message')}")
        st.write(f"**Story Problem:** {blueprint.get('problem_story')}")
        st.write(f"**Story Solution:** {blueprint.get('solution_story')}")
        st.write(f"**Story Market:** {blueprint.get('market_story')}")
        st.write(f"**Story Business:** {blueprint.get('business_story')}")
        st.write(f"**Story Differentiation:** {blueprint.get('competitive_story')}")

        st.markdown("#### Sourced Research Claims")
        claims = master_profile.get("research_claims", [])
        if claims:
            for claim in claims:
                st.info(f"💡 **Claim:** {claim.get('statement')}  \n*Source: {claim.get('source')} | Confidence: {claim.get('confidence')}*")
        else:
            st.info("No high/medium confidence claims sourced.")

        st.markdown("#### 🔒 Context & Anti-Hallucination Guard")
        col_h_1, col_h_2 = st.columns(2)
        with col_h_1:
            team_val = master_profile.get('team', 'To Be Determined')
            if team_val == 'To Be Determined':
                st.warning(f"**Core Team:** {team_val} (Locking placeholders for safety)")
            else:
                st.success(f"**Core Team:** {team_val}")
        with col_h_2:
            financials_val = master_profile.get('financials', 'Not Provided')
            if financials_val == 'Not Provided':
                st.warning(f"**Financial Projections:** {financials_val} (Preventing fabricated statistics)")
            else:
                st.success(f"**Financial Projections:** {financials_val}")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 3: MARKET RESEARCH ---
    with t3:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Market Assessment Details")
        st.write(f"**Research Summary:** {clean_text_output(str(research.get('summary', '')))}")
        
        st.markdown("#### TAM / SAM / SOM Market Sizing")
        st.write(research.get("tam_sam_som"))
        
        st.markdown("#### Competitor Mapping")
        competitors = research.get("competitors", [])
        if competitors and competitors != ["Competitor analysis unavailable"]:
            for comp in competitors:
                st.write(f"- **{comp}**")
        else:
            st.info("⚠️ Competitor analysis unavailable (no competitors provided or verified in research).")

        st.markdown("#### Feasibility & Core Risks")
        st.write(f"**Risks:** {', '.join(research.get('risks', []))}")
        st.write(f"**Technical Feasibility:** {clean_text_output(str(research.get('feasibility', '')))}")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 4: WEBSITE PREVIEW ---
    with t4:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Interactive Website Preview")
        
        html_code = website.get("html", "")
        css_code = website.get("css", "")
        js_code = website.get("js", "")

        compiled_preview = html_code
        if "</head>" in compiled_preview:
            compiled_preview = compiled_preview.replace("</head>", f"<style>\n{css_code}\n</style>\n</head>")
        else:
            compiled_preview = f"<style>\n{css_code}\n</style>\n" + compiled_preview
            
        if "</body>" in compiled_preview:
            compiled_preview = compiled_preview.replace("</body>", f"<script>\n{js_code}\n</script>\n</body>")
        else:
            compiled_preview = compiled_preview + f"\n<script>\n{js_code}\n</script>"

        # Render Live Iframe
        st.components.v1.html(compiled_preview, height=550, scrolling=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 5: PITCH DECK PREVIEW ---
    with t5:
        st.subheader("12 Widescreen Pitch Deck Slides")
        slides = pitch.get("slides", [])
        
        for idx, slide in enumerate(slides):
            with st.container():
                st.markdown(f"<div class='glass-card'>", unsafe_allow_html=True)
                st.markdown(f"### Slide {idx+1}: {slide.get('title')}")
                for bullet in slide.get("bullets", []):
                    st.write(f"- {bullet}")
                if slide.get("notes"):
                    st.markdown(f"<p style='color:#94a3b8;font-style:italic;margin-top:10px;'><b>Presenter Speech Script:</b> {slide.get('notes')}</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 6: REFINEMENT CENTER ---
    with t6:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Refinement Version History")
        
        history_list = st.session_state.version_history
        version_names = [f"Version {i+1}" for i in range(len(history_list))]
        
        if version_names:
            selected_v_name = st.selectbox("Select a previous profile version to restore:", version_names, index=len(version_names)-1)
            selected_index = version_names.index(selected_v_name)
            
            if st.button("Restore Selected Version"):
                st.session_state.master_profile = history_list[selected_index]
                
                # Regenerate all assets on restoration
                with st.spinner("Restoring assets to selected version..."):
                    reg_web, reg_pitch, reg_delivery = regenerate_all_assets(
                        st.session_state.master_profile,
                        master_profile.get("startup_name", "Startup")
                    )
                    st.session_state.website = reg_web
                    st.session_state.pitch = reg_pitch
                    st.session_state.delivery = reg_delivery
                    
                st.success(f"Successfully reverted to {selected_v_name}!")
                time.sleep(1.0)
                st.rerun()
        else:
            st.write("No version history available yet.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Interactive Direct Fields Update")
        st.write("Edit the profile parameters directly and save to trigger asset regeneration:")
        
        # Manual edit form
        with st.form("manual_edit_form"):
            edit_tagline = st.text_input("Branding Tagline / UVP:", value=master_profile.get("tagline", ""))
            edit_problem = st.text_area("Core Problem Statement:", value=master_profile.get("problem", ""), height=80)
            edit_solution = st.text_area("Proposed Solution Statement:", value=master_profile.get("solution", ""), height=80)
            edit_team = st.text_input("Core Team Members (type 'TBD' or list founders):", value=master_profile.get("team", "To Be Determined"))
            edit_financials = st.text_input("Financial Projections (type 'Not Provided' or list metrics):", value=master_profile.get("financials", "Not Provided"))
            
            # Blueprint direct updates
            st.write("**Asset Blueprint Stories:**")
            bp = master_profile.get("asset_blueprint", {})
            edit_hero = st.text_input("Hero Message Copy:", value=bp.get("hero_message", ""))
            edit_prob_story = st.text_area("Problem Story Text:", value=bp.get("problem_story", ""), height=60)
            edit_sol_story = st.text_area("Solution Story Text:", value=bp.get("solution_story", ""), height=60)

            if st.form_submit_button("Save Edits & Regenerate Assets"):
                # Make update
                updated_profile = dict(master_profile)
                updated_profile["tagline"] = edit_tagline
                updated_profile["problem"] = edit_problem
                updated_profile["solution"] = edit_solution
                updated_profile["team"] = edit_team
                updated_profile["financials"] = edit_financials
                
                updated_bp = dict(bp)
                updated_bp["hero_message"] = edit_hero
                updated_bp["problem_story"] = edit_prob_story
                updated_bp["solution_story"] = edit_sol_story
                updated_profile["asset_blueprint"] = updated_bp
                
                st.session_state.master_profile = updated_profile
                
                # Push version
                st.session_state.version_history = push_profile_version(
                    st.session_state.version_history,
                    updated_profile
                )
                
                # Regenerate
                with st.spinner("Regenerating landing page and pitch deck slides..."):
                    reg_web, reg_pitch, reg_delivery = regenerate_all_assets(
                        updated_profile,
                        master_profile.get("startup_name", "Startup")
                    )
                    st.session_state.website = reg_web
                    st.session_state.pitch = reg_pitch
                    st.session_state.delivery = reg_delivery
                    
                st.success("Master profile updated! All assets regenerated.")
                time.sleep(1.0)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Conversational Refinement")
        st.write("Give natural language instructions to update the profile (e.g. 'make primary color emerald green' or 'rewrite solution story to focus on AI scalability'):")
        
        refinement_instr = st.text_input("Enter refinement instructions:", key="refine_input")
        if st.button("Run Refinement"):
            if refinement_instr.strip():
                with st.spinner("Refining master profile context..."):
                    # Update profile via LLM
                    updated_profile = refine_master_profile(master_profile, refinement_instr.strip())
                    st.session_state.master_profile = updated_profile
                    
                    # Push version
                    st.session_state.version_history = push_profile_version(
                        st.session_state.version_history,
                        updated_profile
                    )
                    
                    # Regenerate
                    reg_web, reg_pitch, reg_delivery = regenerate_all_assets(
                        updated_profile,
                        master_profile.get("startup_name", "Startup")
                    )
                    st.session_state.website = reg_web
                    st.session_state.pitch = reg_pitch
                    st.session_state.delivery = reg_delivery
                    
                st.success("Profile refined and all assets regenerated successfully!")
                time.sleep(1.0)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 7: DOWNLOAD CENTER ---
    with t7:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Asset Consistency & Validation Gate")
        
        is_approved = delivery.get("approved", False)
        quality_score = delivery.get("quality_score", 0.0)
        
        st.write(f"**Validation Quality Score:** `{quality_score} / 10.0`")
        
        col_status_1, col_status_2 = st.columns(2)
        with col_status_1:
            if is_approved:
                st.success("🟢 **Approval Status: PASSED**  \nAll sanity validation metrics passed. Assets are ready for download.")
            else:
                st.error("🔴 **Approval Status: PENDING / FAILED**  \nSanity validations failed. Fix layout or consistency errors before downloading.")
        
        st.markdown("#### Consistency Agent Logs:")
        for log in delivery.get("consistency_logs", []):
            if "WARNING" in log:
                st.warning(log)
            else:
                st.info(f"✔️ {log}")
                
        st.markdown("#### Layout Validation Logs:")
        for log in delivery.get("layout_logs", []):
            if "WARNING" in log:
                st.warning(log)
            else:
                st.info(f"✔️ {log}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Deliverables Manifest (manifest.json)")
        st.json(delivery.get("manifest", {}))
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 📥 Download Gated Assets")
        
        # Disabled checks if not approved
        dcol1, dcol2 = st.columns(2)
        with dcol1:
            if Path(delivery["package"]).exists():
                st.download_button(
                    "Download All-in-One ZIP Package",
                    data=Path(delivery["package"]).read_bytes(),
                    file_name="ideabee_delivery.zip",
                    disabled=not is_approved,
                    key="dl_zip"
                )
            if Path(pitch["pptx"]).exists():
                st.download_button(
                    "Download PPTX Slide Deck (Widescreen)",
                    data=Path(pitch["pptx"]).read_bytes(),
                    file_name="startup_pitch.pptx",
                    disabled=not is_approved,
                    key="dl_pptx"
                )
        with dcol2:
            if Path(website["bundle"]).exists():
                st.download_button(
                    "Download Website HTML Bundle",
                    data=Path(website["bundle"]).read_bytes(),
                    file_name="website_bundle.zip",
                    disabled=not is_approved,
                    key="dl_web"
                )
            if Path(pitch["pdf"]).exists():
                st.download_button(
                    "Download PDF Slides Widescreen Deck",
                    data=Path(pitch["pdf"]).read_bytes(),
                    file_name="startup_pitch.pdf",
                    disabled=not is_approved,
                    key="dl_pdf"
                )
        
        if not is_approved:
            st.warning("⚠️ Note: Downloads are disabled. Please modify the profile settings in the Refinement Center to address validation warnings.")
