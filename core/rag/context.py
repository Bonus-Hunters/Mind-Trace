"""
context.py – Utilities for building LLM-ready context from retrieved documents.
"""

from __future__ import annotations

from typing import List

from langchain_core.documents import Document


def build_context(docs: List[Document]) -> str:
    """Format a list of retrieved documents into a single context string.

    Each document is rendered as a labelled block separated by ``---``
    delimiters so the LLM can distinguish between sources.
    """
    blocks: List[str] = []
    for doc in docs:
        meta = doc.metadata
        block = (
            f"Source: {meta.get('source')}\n"
            f"Author: {meta.get('author')}\n"
            f"Date: {meta.get('date')}\n"
            f"\n"
            f"Content:\n"
            f"{doc.page_content}"
        )
        blocks.append(block)
    return "\n---\n".join(blocks)
