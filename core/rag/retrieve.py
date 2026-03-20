"""
retrieve.py – Backward-compatible re-exports.

All implementation has moved to dedicated modules:

- ``core.rag.search``   — retrieval functions (vector, keyword, hybrid)
- ``core.rag.context``  — context-building utilities
- ``core.rag.pipeline`` — high-level query orchestration
"""

# Re-export the original public names so existing callers keep working.
from core.rag.search import retrieve_by_vector as retrieve_context  # noqa: F401
from core.rag.search import retrieve_hybrid  # noqa: F401
from core.rag.context import build_context  # noqa: F401
from core.rag.pipeline import mind_trace_query  # noqa: F401