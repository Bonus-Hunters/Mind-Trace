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
    *,
    min_similarity: float = 0.3,
    search_notes: bool = True,
    search_meetings: bool = True
) -> List[Document]:
    """Retrieve documents using pgvector cosine-similarity search.

    This searches both ``meeting_chunks`` and ``notes`` tables, merges the
    results, and returns the top-*limit* documents sorted by similarity.
    
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
    min_similarity:
        Minimum similarity score (0-1) to include in results. Default 0.3.
        Lower values = more results but potentially lower quality.
    """
    db = PostgresDatabase()
    session_maker = db.get_session_maker()
    query_embedding = embed_query_fn(query)

    # Fetch more candidates for better fusion with keyword search
    fetch_limit = limit * 3

    async with session_maker() as session:
        chunk_rows = []
        note_rows = []

        # -- Meeting chunks --------------------------------------------------
        if search_meetings:
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
                .limit(fetch_limit)
            )
            chunk_rows = (await session.execute(chunk_stmt)).all()

        # -- Notes ------------------------------------------------------------
        if search_notes:
            note_stmt = (
                select(
                    Note,
                    Note.embedding.cosine_distance(query_embedding).label("distance"),
                )
                .where(Note.project_name == project_name)
                .order_by("distance")
                .limit(fetch_limit)
            )
            note_rows = (await session.execute(note_stmt)).all()

    docs: List[Document] = []

    # Process meeting chunks with similarity threshold
    for chunk, meeting, distance in chunk_rows:
        similarity = 1 - distance
        if similarity >= min_similarity:
            docs.append(
                _chunk_to_document(chunk, meeting, project_name, score=similarity)
            )
    
    # Process notes with similarity threshold
    for note, distance in note_rows:
        similarity = 1 - distance
        if similarity >= min_similarity:
            docs.append(_note_to_document(note, project_name, score=similarity))

    # Sort by score and return top limit
    docs.sort(key=lambda d: d.metadata["score"], reverse=True)
    return docs[:limit]


# ---------------------------------------------------------------------------
# Keyword (full-text) search
# ---------------------------------------------------------------------------


async def retrieve_by_keyword(
    query: str,
    project_name: str,
    limit: int,
    search_notes: bool = True,
    search_meetings: bool = True
) -> List[Document]:
    """Retrieve documents using PostgreSQL full-text search with fuzzy matching fallback.

    Uses ``ts_rank_cd`` (cover density ranking) for better score normalization, plus
    fuzzy trigram matching as a fallback to catch partial/similar matches.
    """
    db = PostgresDatabase()
    session_maker = db.get_session_maker()

    ts_query = func.plainto_tsquery("english", query)
    
    # Fetch more candidates for better fusion in hybrid search
    fetch_limit = limit * 2

    async with session_maker() as session:
        chunk_rows = []
        note_rows = []
        chunk_fuzzy_rows = []
        note_fuzzy_rows = []

        # -- Meeting chunks: Full-text search with cover density ranking ----
        if search_meetings:
            # ts_rank_cd provides normalized scores (0-1 range) better than raw ts_rank
            chunk_rank = func.ts_rank_cd(
                func.to_tsvector("english", MeetingChunk.raw_text),
                ts_query,
                32,  # weights: D=0.1, C=0.2, B=0.4, A=0.8
            ).label("rank")

            chunk_stmt = (
                select(MeetingChunk, Meeting, chunk_rank)
                .join(Meeting, MeetingChunk.meeting_id == Meeting.id)
                .where(Meeting.project_name == project_name)
                .where(
                    func.to_tsvector("english", MeetingChunk.raw_text).op("@@")(ts_query)
                )
                .order_by(chunk_rank.desc())
                .limit(fetch_limit)
            )
            chunk_rows = (await session.execute(chunk_stmt)).all()

        # -- Notes: Full-text search with cover density ranking ----
        if search_notes:
            note_rank = func.ts_rank_cd(
                func.to_tsvector("english", Note.note_text),
                ts_query,
                32,
            ).label("rank")

            note_stmt = (
                select(Note, note_rank)
                .where(Note.project_name == project_name)
                .where(func.to_tsvector("english", Note.note_text).op("@@")(ts_query))
                .order_by(note_rank.desc())
                .limit(fetch_limit)
            )
            note_rows = (await session.execute(note_stmt)).all()

        # -- Fallback: Fuzzy/trigram matching for documents missed by full-text ----
        # Use similarity scores as supplementary retrieval
        if search_meetings:
            chunk_fuzzy_stmt = (
                select(
                    MeetingChunk,
                    Meeting,
                    (func.similarity(MeetingChunk.raw_text, query) * 0.5).label("fuzzy_score"),
                )
                .join(Meeting, MeetingChunk.meeting_id == Meeting.id)
                .where(Meeting.project_name == project_name)
                .where(func.similarity(MeetingChunk.raw_text, query) > 0.1)  # threshold
                .order_by(func.similarity(MeetingChunk.raw_text, query).desc())
                .limit(fetch_limit)
            )
            chunk_fuzzy_rows = (await session.execute(chunk_fuzzy_stmt)).all()

        if search_notes:
            note_fuzzy_stmt = (
                select(
                    Note,
                    (func.similarity(Note.note_text, query) * 0.5).label("fuzzy_score"),
                )
                .where(Note.project_name == project_name)
                .where(func.similarity(Note.note_text, query) > 0.1)
                .order_by(func.similarity(Note.note_text, query).desc())
                .limit(fetch_limit)
            )
            note_fuzzy_rows = (await session.execute(note_fuzzy_stmt)).all()

    docs: List[Document] = []

    # Add full-text ranked results
    for chunk, meeting, rank in chunk_rows:
        docs.append(
            _chunk_to_document(chunk, meeting, project_name, score=float(rank))
        )

    for note, rank in note_rows:
        docs.append(_note_to_document(note, project_name, score=float(rank)))

    # Add fuzzy matches (with lower scores, scaled to 0-1)
    for chunk, meeting, fuzzy_score in chunk_fuzzy_rows:
        # Avoid duplicates
        if not any(d.metadata["meeting_id"] == meeting.id for d in docs):
            docs.append(
                _chunk_to_document(chunk, meeting, project_name, score=float(fuzzy_score))
            )

    for note, fuzzy_score in note_fuzzy_rows:
        # Avoid duplicates
        if not any(d.metadata.get("id") == note.id for d in docs):
            docs.append(_note_to_document(note, project_name, score=float(fuzzy_score)))

    # Sort by score and return top limit
    docs.sort(key=lambda d: d.metadata["score"], reverse=True)
    return docs[:limit]


# ---------------------------------------------------------------------------
# Hybrid search – Reciprocal Rank Fusion (RRF)
# ---------------------------------------------------------------------------


def _reciprocal_rank_fusion(
    result_lists: List[List[Document]],
    weights: List[float] | None = None,
    k: int = 60,
) -> List[Document]:
    """Fuse multiple ranked document lists using weighted RRF.

    For each document *d* that appears in any list, compute::

        rrf_score(d) = Σ  weight_i / (k + rank_i(d))

    where *rank_i(d)* is the 1-based rank of *d* in list *i* (skipped when
    *d* is absent from a list), and *weight_i* is the weight for list *i*.

    Parameters
    ----------
    result_lists:
        Two or more ranked lists of ``Document`` objects.
    weights:
        Optional list of weights for each result list. If None, defaults to
        equal weights (1.0 for each list). Must have the same length as
        result_lists. Weights are normalized to sum to 1.0.
    k:
        Smoothing constant (default 60 as per the original RRF paper).

    Returns
    -------
    A single list sorted by descending RRF score.
    """
    if weights is None:
        weights = [1.0] * len(result_lists)
    
    # Normalize weights to sum to 1.0
    total_weight = sum(weights)
    weights = [w / total_weight for w in weights]
    
    rrf_scores: Dict[str, float] = {}
    doc_map: Dict[str, Document] = {}

    for results, weight in zip(result_lists, weights):
        for rank, doc in enumerate(results, start=1):
            key = _unique_key(doc)
            rrf_scores[key] = rrf_scores.get(key, 0.0) + weight / (k + rank)
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
    vector_weight: float = 1,
    keyword_weight: float = 1,
    min_similarity: float = 0.3,
    min_fused_score: float = 0.0,
    rrf_k: int = 60,
    search_notes: bool = True,
    search_meetings: bool = True
) -> List[Document]:
    """Hybrid search combining vector similarity and keyword full-text search.

    Both retrieval methods fetch candidates; the two lists are then merged using
    weighted Reciprocal Rank Fusion before returning the top *limit* documents.

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
    vector_weight:
        Weight for dense/vector search results (default 0.6). Higher values
        prioritize semantic similarity.
    keyword_weight:
        Weight for keyword/full-text search results (default 0.4). Higher values
        prioritize exact term matches.
    min_similarity:
        Minimum similarity threshold for vector search results (default 0.3).
        Filters out vector search hits below this score. Range: 0.0-1.0.
    min_fused_score:
        Minimum fused RRF score to include in results (default 0.0).
        Raises quality floor but may reduce recall. Typical range: 0.0-0.01.
    rrf_k:
        Smoothing constant for RRF (default 60). Lower values (20-40) emphasize
        top ranks; higher values (80-100) treat ranks more equally.
    """
    vector_docs = await retrieve_by_vector(
        query, project_name, limit, embed_query_fn, min_similarity=min_similarity,
          search_notes= search_notes, search_meetings= search_meetings
    )

    keyword_docs = await retrieve_by_keyword(
        query, project_name, limit,
        search_notes= search_notes,
        search_meetings= search_meetings
        )

    fused = _reciprocal_rank_fusion(
        [vector_docs, keyword_docs],
        weights=[vector_weight, keyword_weight],
        k=rrf_k,
    )

    # Filter by minimum fused score if threshold is set
    if min_fused_score > 0.0:
        fused = [doc for doc in fused if doc.metadata["score"] >= min_fused_score]

    return fused[:limit]