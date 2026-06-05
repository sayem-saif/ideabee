from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

if os.getenv("HF_TOKEN") and not os.getenv("HUGGINGFACE_HUB_TOKEN"):
    os.environ["HUGGINGFACE_HUB_TOKEN"] = os.getenv("HF_TOKEN", "")


def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    normalized = "\n".join(line.strip() for line in text.splitlines()).strip()
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        if end < len(normalized):
            separator = normalized.rfind("\n\n", start, end)
            if separator == -1:
                separator = normalized.rfind(". ", start, end)
            if separator == -1:
                separator = normalized.rfind(" ", start, end)
            if separator > start + chunk_size // 2:
                end = separator + 1
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = max(end - overlap, end)
    return chunks


def _iter_documents(source_dir: Path) -> Iterable[Path]:
    for path in source_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".txt", ".md", ".markdown"}:
            yield path


def build_knowledge_base(source_dir: str = "knowledge_base", persist_dir: str = "knowledge_base/chroma_db") -> dict[str, object]:
    source_path = Path(source_dir)
    source_path.mkdir(parents=True, exist_ok=True)
    Path(persist_dir).mkdir(parents=True, exist_ok=True)

    embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model)
    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection(name="ideabee", embedding_function=embedding_function)

    documents = [str(path) for path in _iter_documents(source_path)]
    records: list[str] = []
    metadatas: list[dict[str, str]] = []
    ids: list[str] = []
    for index, document_path in enumerate(documents):
        content = Path(document_path).read_text(encoding="utf-8", errors="ignore")
        for chunk_index, chunk in enumerate(_chunk_text(content)):
            ids.append(f"{index}-{chunk_index}")
            records.append(chunk)
            metadatas.append({"source": document_path, "chunk_index": str(chunk_index)})

    if records:
        collection.upsert(ids=ids, documents=records, metadatas=metadatas)

    return {
        "status": "generated",
        "documents": documents,
        "persist_dir": persist_dir,
        "chunks": len(records),
        "note": "ChromaDB built with local sentence-transformer embeddings.",
    }
