from __future__ import annotations

import os

import chromadb

from rag.build_kb import SentenceTransformerEmbeddingFunction


def retrieve_context(query: str, top_k: int = 5) -> list[str]:
    persist_dir = os.getenv("CHROMA_PATH", "knowledge_base/chroma_db")
    embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    embedding_function = SentenceTransformerEmbeddingFunction(embedding_model)
    client = chromadb.PersistentClient(path=persist_dir)

    try:
        collection = client.get_collection(name="ideabee", embedding_function=embedding_function)
    except Exception:
        return []

    results = collection.query(query_texts=[query], n_results=top_k)
    documents = results.get("documents", [[]])
    if not documents:
        return []
    return [str(document) for document in documents[0] if document]
