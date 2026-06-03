# IdeaBee

Local scaffold for IdeaBee — an AI startup builder.

Quick start

1. Create and activate a Python virtualenv:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```bash
pip install -r requirements.txt
pip install huggingface-hub sentence-transformers chromadb python-pptx reportlab
```

3. Copy `.env.example` to `.env` and fill your keys.

4. Run the pipeline:

```bash
python run_pipeline.py "Your startup idea here"
```

5. Start the UI:

```bash
streamlit run app.py
```

Security

- `.gitignore` excludes `.env` and common virtualenv folders. Do not commit secrets.
- Run `python security_scan.py` to locate obvious secret patterns.
- If keys were exposed, rotate them immediately.

Next steps

- Wire advanced RAG and provider options (already scaffolded).
- Replace or supply a `PITCH_TEMPLATE_PATH` for prettier slides.
# IdeaBee

IdeaBee is an AI startup builder that turns a rough idea into:

- a polished startup brief
- a research report
- a static launch website
- a 12-slide pitch deck in PPTX and PDF
- a delivery ZIP with everything packaged together

## Run

```bash
python main.py "Your startup idea here"
```

```bash
streamlit run app.py
```

## Setup

1. Copy `.env.example` to `.env`.
2. Fill in your API keys.
3. Put any reference docs in `knowledge_base/`.

## Outputs

Generated files land in `outputs/`.