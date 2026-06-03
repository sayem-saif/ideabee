from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from pipeline import ensure_directories, run_pipeline

load_dotenv()

st.set_page_config(page_title="IdeaBee", page_icon="🐝", layout="wide")
ensure_directories()

st.title("IdeaBee")
st.write("AI startup builder that turns rough ideas into a launch package.")

with st.sidebar:
    st.header("Configuration")
    st.code(
        "\n".join(
            [
                f"OPENROUTER_API_KEY={'set' if os.getenv('OPENROUTER_API_KEY') else 'missing'}",
                f"HF_TOKEN={'set' if os.getenv('HF_TOKEN') else 'missing'}",
                f"TAVILY_API_KEY={'set' if os.getenv('TAVILY_API_KEY') else 'missing'}",
            ]
        )
    )
    st.caption("The app will fall back to local defaults if a provider call fails.")

idea = st.text_area(
    "Startup idea",
    value=os.getenv("IDEABEE_SAMPLE_IDEA", "An AI startup builder that turns rough ideas into validated ventures."),
    height=140,
)

if st.button("Generate launch package", type="primary"):
    with st.spinner("Building IdeaBee outputs..."):
        result = run_pipeline(idea)
    tabs = st.tabs(["Polished", "Research", "Website", "Pitch", "Delivery"])
    with tabs[0]:
        st.json(result["polished"])
    with tabs[1]:
        st.json(result["research"])
    with tabs[2]:
        st.json(result["website"])
    with tabs[3]:
        st.json(result["pitch"])
    with tabs[4]:
        st.json(result["delivery"])

    st.success(f"Quality score: {result['delivery'].get('quality_score', 0)}/10")
    st.download_button("Download delivery ZIP", data=Path(result["delivery"]["package"]).read_bytes(), file_name="ideabee_delivery.zip")
    st.download_button("Download PPTX", data=Path(result["pitch"]["pptx"]).read_bytes(), file_name="startup_pitch.pptx")
    st.download_button("Download PDF", data=Path(result["pitch"]["pdf"]).read_bytes(), file_name="startup_pitch.pdf")
    st.download_button("Download website ZIP", data=Path(result["website"]["bundle"]).read_bytes(), file_name="website_bundle.zip")

st.divider()
st.subheader("Next steps")
st.markdown(
    """
- Edit the idea prompt and run the app again.
- Add local knowledge base files under `knowledge_base/`.
- Replace the default pitch template with a branded `.pptx` if you want a custom look.
"""
)

outputs_dir = Path("outputs")
if outputs_dir.exists():
    st.caption(f"Outputs directory: {outputs_dir.resolve()}")
