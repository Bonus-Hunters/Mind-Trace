from langchain_core.output_parsers import StrOutputParser,JsonOutputParser
from prompts import *
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from models import LLM_MODEL, EMBED_MODEL
from core.database.postgresDatabase import PostgresDatabase
from core.database.repos import TaskRepository, MeetingRepository, MeetingChunkRepository
from langchain_core.documents import Document
import numpy as np
from langchain_core.output_parsers import PydanticOutputParser

llm = OllamaLLM(model=LLM_MODEL, temperature=0)
embeddings = OllamaEmbeddings(model=EMBED_MODEL)

parser = PydanticOutputParser(pydantic_object=IntentOutput)

intent_chain = intent_prompt | llm | parser

def classify_query(query: str) -> IntentOutput:
    return intent_chain.invoke({"query": query})

rewrite_chain = rewrite_prompt | llm | StrOutputParser()

def rewrite_query(query: str):
    return rewrite_chain.invoke({"query": query})

def cosine_similarity(query_embedding,chunk_embedding):
    return np.dot(query_embedding, chunk_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
            )

async def retrieve_context(query: str, project: str, source: str = "both"):
    """Retrieve context from PostgreSQL database using vector similarity search"""
    db = PostgresDatabase()
    session_maker = db.get_session_maker()
    meeting_repo = MeetingRepository(session_maker)
    
    # Get query embedding
    query_embedding = embeddings.embed_query(query)
    query_embedding = np.array(query_embedding)
    
    # Retrieve all meetings for the project
    async with session_maker() as session:
        from sqlalchemy import select
        from core.database.models import Meeting, MeetingChunk,Note
        
        # Query meetings by project
        stmt = select(Meeting).where(Meeting.project_name == project)
        result = await session.execute(stmt)
        meetings = result.scalars().all()
    
    # Collect all chunks from meetings
    all_chunks = []
    for meeting in meetings:
        chunks = await meeting_repo.get_all_chunks(meeting.id)
        if chunks:
            all_chunks.extend(chunks)
    
    # Calculate similarity scores and sort
    chunk_similarities = []
    for chunk in all_chunks:
        if chunk.embedding:
            chunk_embedding = np.array(chunk.embedding)
            # Cosine similarity
            similarity = cosine_similarity(query_embedding,chunk_embedding)
            chunk_similarities.append((chunk, similarity))
    
    # Sort by similarity and get top k
    chunk_similarities.sort(key=lambda x: x[1], reverse=True)
    top_chunks = [chunk for chunk, _ in chunk_similarities[:8]]
    
    # Convert to Document objects for compatibility with downstream functions
    docs = [
        Document(
            page_content=chunk.text_content,
            metadata={
                "project": project,
                "speaker_names": chunk.speaker_names,
                "meeting_id": chunk.meeting_id
            }
        )
        for chunk in top_chunks
    ]
    
    return docs

async def get_tasks_for_user(user_id: str, project_name: str):
    """Fetch tasks for a specific user in a project from PostgreSQL database"""
    db = PostgresDatabase()
    session_maker = db.get_session_maker()
    task_repo = TaskRepository(session_maker)
    
    # Get all tasks for the project and filter by owner/assignee
    tasks = await task_repo.get_by_project_and_assignee(project_name, user_id)
    return tasks


compress_chain = (
    compression_prompt
    | llm
    | StrOutputParser()
)

def compress_context(docs, query):
    raw_context = "\n\n".join(d.page_content for d in docs)
    return compress_chain.invoke({
        "context": raw_context,
        "query": query
    })

rag_chain = (
    rag_prompt
    | llm
    | StrOutputParser()
)

def answer_question(context, question):
    return rag_chain.invoke({
        "context": context,
        "question": question
    })

async def mind_trace_query(
    query: str,
    project: str,
    user_id: str
):
    """Main query function that uses PostgreSQL database for task retrieval and context"""
    intent = classify_query(query)
    rewritten = rewrite_query(query)
    # if "task" in intent.lower():
    #     tasks = await get_tasks_for_user(user_id, project)
    #     if tasks:
    #         return tasks
    match intent.intent:
        case "task":
            tasks = await get_tasks_for_user(user_id,project)
            if tasks:
                return tasks
        case "summary":
            pass
        case "fact":
            pass


    docs = await retrieve_context(
        rewritten,
        project,
        source=intent.source
    )

    compressed = compress_context(docs, rewritten)

    return answer_question(compressed, query)
