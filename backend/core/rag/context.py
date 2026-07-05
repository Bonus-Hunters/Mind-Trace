"""
context.py – Utilities for building LLM-ready context from retrieved documents.
"""

from __future__ import annotations

import re
from typing import List

from langchain_core.documents import Document


def build_context(docs: List[Document]) -> str:
    """Format retrieved documents into a context block that can be cited by ID."""
    blocks: List[str] = []
    for index, doc in enumerate(docs, start=1):
        meta = doc.metadata or {}
        block = [f"[DOC {index}]", f"Source: {meta.get('source', 'unknown')}"]

        if meta.get("project") is not None:
            block.append(f"Project: {meta.get('project')}")
        if meta.get("title") is not None:
            block.append(f"Title: {meta.get('title')}")
        if meta.get("author") is not None:
            block.append(f"Author: {meta.get('author')}")
        if meta.get("file_name") is not None:
            block.append(f"File: {meta.get('file_name')}")
        if meta.get("function_name") is not None:
            block.append(f"Function: {meta.get('function_name')}")
        if meta.get("line_number") is not None:
            block.append(f"Line: {meta.get('line_number')}")
        if meta.get("date") is not None:
            block.append(f"Date: {meta.get('date')}")

        block.append("")
        block.append("Content:")
        block.append(doc.page_content or "")
        blocks.append("\n".join(block))

    return "\n---\n".join(blocks)


def decorate_answer_with_references(answer: str, docs: List[Document]) -> str:
    """Append referenced notes for the documents cited by the model."""
    cited_ids = set(re.findall(r"\bDOC\s*(\d+)\b", answer, flags=re.IGNORECASE))
    if not cited_ids:
        return answer

    referenced_notes: List[str] = []
    for doc_id in sorted(int(item) for item in cited_ids):
        if doc_id < 1 or doc_id > len(docs):
            continue

        doc = docs[doc_id - 1]
        meta = doc.metadata or {}
        if meta.get("source") != "note":
            continue

        note_lines = [f"- {meta.get('file_name') or 'unknown'}"]
        if meta.get("function_name"):
            note_lines.append(f"  Function: {meta.get('function_name')}")
        if meta.get("line_number") is not None:
            note_lines.append(f"  Line: {meta.get('line_number')}")

        if len(note_lines) > 1:
            referenced_notes.extend(note_lines)

    if not referenced_notes:
        return answer

    reference_block = ["", "Referenced Notes"] + referenced_notes
    return answer.rstrip() + "\n".join(reference_block)
