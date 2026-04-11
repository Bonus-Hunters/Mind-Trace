"""
search.py – Retrieval functions for the RAG pipeline.

Provides vector similarity search, keyword (full-text) search, and hybrid
search that fuses both result lists via Reciprocal Rank Fusion (RRF).
"""

from __future__ import annotations

from typing import Callable, Dict, List

from langchain_core.documents import Document
from sqlalchemy import func, select

from core.database.models import Meeting, MeetingChunk, Note
from core.database.postgresDatabase import PostgresDatabase


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _chunk_to_document(
    chunk: MeetingChunk,
    meeting: Meeting,
    project_name: str,
    score: float,
) -> Document:
    """Convert a MeetingChunk row into a LangChain Document."""
    return Document(
        page_content=chunk.raw_text,
        metadata={
            "source": "meeting",
            "type": "meeting_chunk",
            "project": project_name,
            "title": meeting.title,
            "meeting_id": meeting.id,
            "speaker_names": chunk.speaker_names,
            "date": meeting.date.isoformat() if meeting.date else None,
            "score": score,
        },
    )


def _note_to_document(
    note: Note,
    project_name: str,
    score: float,
) -> Document:
    """Convert a Note row into a LangChain Document."""
    return Document(
        page_content=note.note_text,
        metadata={
            "id": note.id,
            "source": "note",
            "type": note.type,
            "project": project_name,
            "author": note.author,
            "file_name": note.file_name,
            "module": note.module,
            "tags": note.tags,
            "date": note.date.isoformat() if note.date else None,
            "score": score,
        },
    )


def _unique_key(doc: Document) -> str:
    """Return a string key that uniquely identifies a document."""
    meta = doc.metadata
    if meta["source"] == "meeting":
        return f"meeting_chunk:{meta['meeting_id']}:{hash(doc.page_content)}"
    return f"note:{meta.get('file_name')}:{hash(doc.page_content)}"


# ---------------------------------------------------------------------------
# Vector similarity search
# ---------------------------------------------------------------------------


async def retrieve_by_vector(
    query: str,
    project_name: str,
    limit: int,
    embed_query_fn: Callable[[str], List[float]],
) -> List[Document]:
    """Retrieve documents using pgvector cosine-similarity search.

    This searches both ``meeting_chunks`` and ``notes`` tables, merges the
    results, and returns the top-*limit* documents sorted by similarity.
    """
    db = PostgresDatabase()
    session_maker = db.get_session_maker()
    query_embedding = embed_query_fn(query)

    async with session_maker() as session:
        # -- Meeting chunks --------------------------------------------------
        chunk_stmt = (
            select(
                MeetingChunk,
                Meeting,
                MeetingChunk.embedding.cosine_distance(query_embedding).label(
                    "distance"
                ),
            )
            .join(Meeting, MeetingChunk.meeting_id == Meeting.id)
            .where(Meeting.project_name == project_name)
            .order_by("distance")
            .limit(limit)
        )
        chunk_rows = (await session.execute(chunk_stmt)).all()

        # -- Notes ------------------------------------------------------------
        note_stmt = (
            select(
                Note,
                Note.embedding.cosine_distance(query_embedding).label("distance"),
            )
            .where(Note.project_name == project_name)
            .order_by("distance")
            .limit(limit)
        )
        note_rows = (await session.execute(note_stmt)).all()

    docs: List[Document] = []

    for chunk, meeting, distance in chunk_rows:
        docs.append(
            _chunk_to_document(chunk, meeting, project_name, score=1 - distance)
        )
    for note, distance in note_rows:
        docs.append(_note_to_document(note, project_name, score=1 - distance))

    docs.sort(key=lambda d: d.metadata["score"], reverse=True)
    return docs[:limit]


# ---------------------------------------------------------------------------
# Keyword (full-text) search
# ---------------------------------------------------------------------------


async def retrieve_by_keyword(
    query: str,
    project_name: str,
    limit: int,
) -> List[Document]:
    """Retrieve documents using PostgreSQL full-text search (``ts_rank``).

    Uses ``plainto_tsquery`` so the caller can pass natural-language queries
    without worrying about special tsquery syntax.
    """
    db = PostgresDatabase()
    session_maker = db.get_session_maker()

    ts_query = func.plainto_tsquery("english", query)

    async with session_maker() as session:
        # -- Meeting chunks --------------------------------------------------
        chunk_rank = func.ts_rank(
            func.to_tsvector("english", MeetingChunk.raw_text),
            ts_query,
        ).label("rank")

        chunk_stmt = (
            select(MeetingChunk, Meeting, chunk_rank)
            .join(Meeting, MeetingChunk.meeting_id == Meeting.id)
            .where(Meeting.project_name == project_name)
            .where(
                func.to_tsvector("english", MeetingChunk.raw_text).op("@@")(ts_query)
            )
            .order_by(chunk_rank.desc())
            .limit(limit)
        )
        chunk_rows = (await session.execute(chunk_stmt)).all()

        # -- Notes ------------------------------------------------------------
        note_rank = func.ts_rank(
            func.to_tsvector("english", Note.note_text),
            ts_query,
        ).label("rank")

        note_stmt = (
            select(Note, note_rank)
            .where(Note.project_name == project_name)
            .where(func.to_tsvector("english", Note.note_text).op("@@")(ts_query))
            .order_by(note_rank.desc())
            .limit(limit)
        )
        note_rows = (await session.execute(note_stmt)).all()

    docs: List[Document] = []

    for chunk, meeting, rank in chunk_rows:
        docs.append(_chunk_to_document(chunk, meeting, project_name, score=float(rank)))

    for note, rank in note_rows:
        docs.append(_note_to_document(note, project_name, score=float(rank)))

    docs.sort(key=lambda d: d.metadata["score"], reverse=True)
    return docs[:limit]


# ---------------------------------------------------------------------------
# Hybrid search – Reciprocal Rank Fusion (RRF)
# ---------------------------------------------------------------------------


def _reciprocal_rank_fusion(
    result_lists: List[List[Document]],
    k: int = 60,
) -> List[Document]:
    """Fuse multiple ranked document lists using RRF.

    For each document *d* that appears in any list, compute::

        rrf_score(d) = Σ  1 / (k + rank_i(d))

    where *rank_i(d)* is the 1-based rank of *d* in list *i* (skipped when
    *d* is absent from a list).

    Parameters
    ----------
    result_lists:
        Two or more ranked lists of ``Document`` objects.
    k:
        Smoothing constant (default 60 as per the original RRF paper).

    Returns
    -------
    A single list sorted by descending RRF score.
    """
    rrf_scores: Dict[str, float] = {}
    doc_map: Dict[str, Document] = {}

    for results in result_lists:
        for rank, doc in enumerate(results, start=1):
            key = _unique_key(doc)
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank)
            doc_map[key] = doc  # keep the latest copy

    # Attach the fused score to the document metadata
    for key, doc in doc_map.items():
        doc.metadata["score"] = rrf_scores[key]

    return sorted(doc_map.values(), key=lambda d: d.metadata["score"], reverse=True)


async def retrieve_hybrid(
    query: str,
    project_name: str,
    limit: int,
    embed_query_fn: Callable[[str], List[float]],
    *,
    rrf_k: int = 60,
) -> List[Document]:
    """Hybrid search combining vector similarity and keyword full-text search.

    Both retrieval methods fetch up to *limit* candidates each; the two lists
    are then merged using Reciprocal Rank Fusion before returning the top
    *limit* documents.

    Parameters
    ----------
    query:
        The user's natural-language query.
    project_name:
        Filter results to this project.
    limit:
        Maximum number of documents to return.
    embed_query_fn:
        A callable that maps a query string to its embedding vector.
    rrf_k:
        Smoothing constant for RRF (default 60).
    """
    vector_docs = await retrieve_by_vector(query, project_name, limit, embed_query_fn)

    keyword_docs = await retrieve_by_keyword(query, project_name, limit)

    fused = _reciprocal_rank_fusion([vector_docs, keyword_docs], k=rrf_k)

    return fused[:limit]