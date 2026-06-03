# Implementation Plan - IdeaBee AI Startup Builder

This implementation plan outlines the steps to build **IdeaBee**, an AI-powered startup builder system with 5 cooperative agents orchestrated via LangGraph, featuring RAG-based market validation and a Streamlit UI, based on the `IdeaBee_Project_Blueprint.pdf` document.

## User Review Required

> [!IMPORTANT]
> **API Keys & Model Configuration**
> - The blueprint recommends OpenRouter (`google/gemma-3-27b-it` and `deepseek/deepseek-r1`) and Tavily (web search).
> - We will create a `.env.example` file. You will need to copy it to `.env` and fill in your OpenRouter / OpenAI / Tavily keys to run the agents.
> - If you prefer using OpenAI/Groq keys directly instead of OpenRouter, we can configure `ChatOpenAI` or `ChatGroq` accordingly.

> [!WARNING]
> **PDF Export Dependency (LibreOffice)**
> - Converting `.pptx` slides to `.pdf` requires LibreOffice CLI. If LibreOffice is not installed on your Windows machine, we will configure a fallback to skip PDF conversion (retaining the PPTX deck) or use `reportlab` to build a simple PDF report.

---

## Proposed Changes

We will construct the project following the folder structure detailed in Section 8 of the blueprint:

```
ideabee/ (workspace root)
├── main.py (LangGraph workflow entry point)
├── app.py (Streamlit UI)
├── requirements.txt (All Python dependencies)
├── .env.example (Environment variables template)
├── agents/
│   ├── __init__.py
│   ├── agent1_polisher.py
│   ├── agent2_researcher.py
│   ├── agent3_website.py
│   ├── agent4_pitch.py
│   └── agent5_deliverer.py
├── rag/
│   ├── __init__.py
│   ├── build_kb.py
│   └── retriever.py
├── knowledge_base/
│   └── (Sample startup materials / guidelines)
├── templates/
│   └── (Base pptx template)
├── outputs/
│   └── (Output directory for zip files, decks, scripts)
└── prompts/
    ├── polisher.txt
    ├── researcher.txt
    ├── website.txt
    ├── pitch.txt
    └── deliverer.txt
```

### 1. Project Initialization & Dependencies
#### [NEW] [requirements.txt](file:///c:/Users/SS/Desktop/ideabee/requirements.txt)
- Defines dependencies: `langgraph`, `langchain`, `langchain-openai`, `langchain-community`, `chromadb`, `sentence-transformers`, `tavily-python`, `python-pptx`, `reportlab`, `pillow`, `streamlit`, `python-dotenv`, `beautifulsoup4`, `requests`, `aiohttp`.

#### [NEW] [env.example](file:///c:/Users/SS/Desktop/ideabee/.env.example)
- Sample environment file showing keys required:
  - `OPENROUTER_API_KEY`
  - `TAVILY_API_KEY`

---

### 2. Knowledge Base & RAG Pipeline
#### [NEW] [build_kb.py](file:///c:/Users/SS/Desktop/ideabee/rag/build_kb.py)
- Utility to load startup documentation, YC reports, and market research from `knowledge_base/` directory, chunk them using `RecursiveCharacterTextSplitter`, embed using HuggingFace local `all-MiniLM-L6-v2` (or OpenAI embeddings), and store them in a local Chroma vector database.

#### [NEW] [retriever.py](file:///c:/Users/SS/Desktop/ideabee/rag/retriever.py)
- Interface to query the vector store for context matching the startup type.

---

### 3. Agent Implementations
We will separate prompt templates into the `prompts/` folder to maintain modularity.

#### [NEW] [agent1_polisher.py](file:///c:/Users/SS/Desktop/ideabee/agents/agent1_polisher.py)
- Polishes messy user idea into a clean JSON structure: `startup_name`, `elevator_pitch`, `problem`, `solution`, `target_audience`, `key_features`, `uvp`, `suggested_tech_stack`.

#### [NEW] [agent2_researcher.py](file:///c:/Users/SS/Desktop/ideabee/agents/agent2_researcher.py)
- Conducts RAG search from the knowledge base and web search via Tavily/DuckDuckGo.
- Formulates a market validation report containing TAM/SAM/SOM, direct competitors, technical feasibility, business models, and risks.

#### [NEW] [agent3_website.py](file:///c:/Users/SS/Desktop/ideabee/agents/agent3_website.py)
- Instructs the LLM to generate code for: `index.html`, `styles.css`, and `script.js`.
- Writes them to disk inside `outputs/` and zips them. Includes support for Vercel CLI deployment command generation.

#### [NEW] [agent4_pitch.py](file:///c:/Users/SS/Desktop/ideabee/agents/agent4_pitch.py)
- Formulates the slide structure (12 standard investor slides).
- Uses `python-pptx` to programmatically build the slide deck, reading from a presentation template in `templates/` or building it with curated layout designs.

#### [NEW] [agent5_deliverer.py](file:///c:/Users/SS/Desktop/ideabee/agents/agent5_deliverer.py)
- Performs final QA check, issues quality score, and writes a timed 5-minute presentation script.

---

### 4. Orchestration & UI
#### [NEW] [main.py](file:///c:/Users/SS/Desktop/ideabee/main.py)
- LangGraph orchestration defining the nodes (`polish`, `research`, `build_website`, `build_pitch`, `deliver`), shared `AgentState`, and edges (sequential processing transitioning into a parallel split for website and pitch, then merging at delivery).

#### [NEW] [app.py](file:///c:/Users/SS/Desktop/ideabee/app.py)
- Interactive Streamlit dashboard showing state generation, allowing download of the output ZIP package, PPTX deck, and pitch script.

---

## Verification Plan

### Automated Tests
- Run validation checks on LangGraph state updates.
- Test isolated agent calls using mock inputs to verify JSON parsing.

### Manual Verification
1. Run the system using Python CLI: `python main.py`
2. Start the Streamlit app: `streamlit run app.py` and test with a mockup idea (e.g., "An app that matches students for study sessions").
3. Inspect generated files in the `outputs/` folder (HTML site, PPTX presentation, pitch speech text).
