"""
pipeline.py – High-level RAG query orchestration.
"""

from __future__ import annotations

from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser

from backend.core.rag.context import build_context
from backend.core.rag.llm_config import LLMConfig
from backend.core.rag.llm_factory import get_embeddings, get_llm
from backend.core.rag.models import EMBED_MODEL, LLM_MODEL
from backend.core.rag.prompts import IntentOutput, intent_prompt, rag_prompt, rewrite_prompt
from backend.core.rag.search import retrieve_by_vector, retrieve_hybrid


from typing import AsyncGenerator


async def mind_trace_query(
    query: str,
    project: str,
    llm_config: LLMConfig,
    embed_config: LLMConfig,
) -> AsyncGenerator[str, None]:
    """Run the full Mind-Trace RAG pipeline for a user query.

    Steps
    -----
    1. Rewrite the query for better retrieval.
    2. Embed & retrieve relevant documents via vector search.
    3. Build a context string and invoke the LLM with the RAG prompt.
    """
    llm = get_llm(llm_config)
    embeddings = get_embeddings(embed_config)

    # Build chains
    rewrite_chain = rewrite_prompt | llm | StrOutputParser()
    rag_chain = rag_prompt | llm | StrOutputParser()

    # 1. Rewrite
    # rewritten = rewrite_chain.invoke({"query": query})
    # print(rewritten)

    # 2. Retrieve
    embed_query_fn = embeddings.embed_query

    docs = await retrieve_hybrid(
        query,
        project,
        limit=8,
        embed_query_fn=embed_query_fn,
    )
    print(" ----- retrieval passed -")
    # docs = await retrieve_by_vector(
    #     query,
    #     project,
    #     limit=8,
    #     embed_query_fn=embed_query_fn,
    # )
    print(docs)

    # 3. Generate
    final_context = build_context(docs)
    print(final_context)
    
    # Stream the response
    for chunk in rag_chain.stream({"context": final_context, "question": query}):
        yield chunk


# ---------------------------------------------------------------------------
# Quick manual test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        """Entry point for testing the RAG pipeline."""
        llm_cfg = LLMConfig(
            provider="ollama",
            model=LLM_MODEL,
            temperature=0.8,
        )
        embed_cfg = LLMConfig(
            provider="ollama",
            model=EMBED_MODEL,
        )

        print("Streaming response:")
        async for chunk in mind_trace_query(
            "how is javascript engine holding on",
            "Mozilla Issues",
            llm_cfg,
            embed_cfg,
        ):
            print(chunk, end="", flush=True)
        print()

    asyncio.run(main())
