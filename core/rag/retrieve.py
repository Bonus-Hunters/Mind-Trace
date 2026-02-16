from typing import List
from langchain_core.output_parsers import StrOutputParser
from core.rag.prompts import *
from core.rag.models import LLM_MODEL, EMBED_MODEL
from core.database.postgresDatabase import PostgresDatabase
from langchain_core.documents import Document
from langchain_core.output_parsers import PydanticOutputParser
from sqlalchemy import select
from core.database.models import Meeting, MeetingChunk, Note
from core.rag.llm_factory import get_llm, get_embeddings
from core.rag.llm_config import LLMConfig

async def retrieve_context(query: str, project_name: str, limit: int,embed_query_fn) -> List[Document]:
    """Retrieve context from PostgreSQL database using vector similarity search on both MeetingChunks and Notes"""
    db = PostgresDatabase()
    session_maker = db.get_session_maker()
    
    query_embedding = embed_query_fn(query)
    
    async with session_maker() as session:
        # 1. Search Meeting Chunks
        # We join with Meeting to filter by project and get meeting metadata
        chunk_stmt = (
            select(
                MeetingChunk,
                Meeting,
                MeetingChunk.embedding.cosine_distance(query_embedding).label("distance")
            )
            .join(Meeting, MeetingChunk.meeting_id == Meeting.id)
            .where(Meeting.project_name == project_name)
            .order_by("distance")
            .limit(limit)
        )
        
        chunk_results = await session.execute(chunk_stmt)
        chunk_rows = chunk_results.all() # list of (MeetingChunk, Meeting, distance)

        # 2. Search Notes
        note_stmt = (
            select(
                Note,
                Note.embedding.cosine_distance(query_embedding).label("distance")
            )
            .where(Note.project_name == project_name)
            .order_by("distance")
            .limit(limit)
        )

        note_results = await session.execute(note_stmt)
        note_rows = note_results.all() # list of (Note, distance)

    # Combine and format results
    docs = []

    # Process chunks
    for chunk, meeting, distance in chunk_rows:
        # Distance is 0 to 2 (cosine distance), similarity = 1 - distance
        # But we really just care about relative ranking usually. 
        # For now let's keep the distance or convert to a score if needed.
        # Let's perform a cutoff if distance is too high (low similarity) if desired, 
        # but for now we just take the top K.
        
        docs.append(
            Document(
                page_content=chunk.text_content,
                metadata={
                    "source": "meeting",
                    "type": "meeting_chunk",
                    "project": project_name,
                    "title": meeting.title,
                    "meeting_id": meeting.id,
                    "speaker_names": chunk.speaker_names,
                    "date": meeting.date.isoformat() if meeting.date else None,
                    "score": 1 - distance # Convert distance to similarity score
                }
            )
        )

    # Process notes
    for note, distance in note_rows:
        docs.append(
            Document(
                page_content=note.note_text,
                metadata={
                    "source": "note",
                    "type": note.type,
                    "project": project_name,
                    "author": note.author,
                    "file_name": note.file_name,
                    "module": note.module,
                    "tags": note.tags,
                    "date": note.date.isoformat() if note.date else None,
                    "score": 1 - distance
                }
            )
        )

    # Sort combined results by score (descending)
    docs.sort(key=lambda x: x.metadata["score"], reverse=True)

    # Return top K from the combined list
    return docs[:limit]


# def compress_context(docs, query):
#     if not docs:
#         return ""
    
#     # Format context with source information
#     formatted_docs = []
#     for d in docs:
#         source_info = f"[Source: {d.metadata.get('source', 'unknown')} - {d.metadata.get('type', 'unknown')}]"
#         if d.metadata.get('source') == 'meeting':
#             source_info += f" (Meeting: {d.metadata.get('title')})"
#         elif d.metadata.get('source') == 'note':
#             source_info += f" (Author: {d.metadata.get('author')})"
            
#         formatted_docs.append(f"{source_info}\n{d.page_content}")

#     raw_context = "\n\n---\n\n".join(formatted_docs)
#     return compress_chain.invoke({"context": raw_context, "query": query})




def build_context(docs):
    blocks = []
    for d in docs:
        blocks.append(
            f"""Source: {d.metadata.get('source')}
            Author: {d.metadata.get('author')}
            Date: {d.metadata.get('date')}

            Content:
            {d.page_content}
            """
        )
    return "\n---\n".join(blocks)

async def mind_trace_query(
    query: str,
    project: str,
    llm_config: LLMConfig,
    embed_config: LLMConfig
):
    llm = get_llm(llm_config)
    embeddings = get_embeddings(embed_config)

    parser = PydanticOutputParser(pydantic_object=IntentOutput)

    intent_chain = intent_prompt | llm | parser
    rewrite_chain = rewrite_prompt | llm | StrOutputParser()
    rag_chain = rag_prompt | llm | StrOutputParser()
    compress_chain = (compression_prompt | llm | StrOutputParser())

    def rewrite_query(query):
        return rewrite_chain.invoke({"query": query})

    def embed_query(query):
        return embeddings.embed_query(query)
    rewritten = rewrite_query(query)
    print(rewritten)

    docs = await retrieve_context(
        query,
        project,
        limit=8,
        embed_query_fn=embed_query
    )
    print(docs)
    final_context = build_context(docs)
    print(final_context)
    return rag_chain.invoke({"context": final_context, "question": query})


if __name__ == "__main__":
    import asyncio

    async def main():
        """Main entry point for testing manager logic."""
        llm_cfg = LLMConfig(
            provider="ollama",
            model= LLM_MODEL,
            temperature=0.8
        )

        embed_cfg = LLMConfig(
            provider="ollama",
            model=EMBED_MODEL
        )

        print(await mind_trace_query(
            "what is the note written by Test Author? can you also comment on the note?",
            "Test Project",
            llm_cfg,
            embed_cfg
            ))

    asyncio.run(main())