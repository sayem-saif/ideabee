# IdeaBee

IdeaBee is an AI startup builder that turns a rough idea into:

- a polished startup brief
- a research report
- a static launch website
- a 12-slide pitch deck in PPTX and PDF
- a delivery ZIP with everything packaged together

## Quick Start

1. Create and activate a virtualenv.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```bash
pip install -r requirements.txt
pip install huggingface-hub sentence-transformers chromadb python-pptx reportlab
```

3. Copy `.env.example` to `.env` and fill API keys.

4. Run pipeline.

```bash
python run_pipeline.py "Your startup idea here"
```

5. Start Streamlit UI.

```bash
streamlit run app.py
```

## Setup Notes

1. Put reference docs in `knowledge_base/` for local RAG context.
2. Generated outputs are written to `outputs/`.

## Security

- `.gitignore` excludes `.env` and virtualenv folders.
- Run `python security_scan.py` to find obvious secret patterns.
- Rotate keys immediately if they were exposed.
