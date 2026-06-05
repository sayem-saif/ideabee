"""Retrieval helpers for IdeaBee."""


def build_knowledge_base(*args, **kwargs):
    from .build_kb import build_knowledge_base as _build_knowledge_base

    return _build_knowledge_base(*args, **kwargs)


def retrieve_context(*args, **kwargs):
    from .retriever import retrieve_context as _retrieve_context

    return _retrieve_context(*args, **kwargs)
