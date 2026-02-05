from typing import Literal
from langchain_core.prompts import PromptTemplate

intent_prompt = PromptTemplate.from_template("""
Classify the user query.

{format_instructions}

Query: {query}
""")

from pydantic import BaseModel

class IntentOutput(BaseModel):
    intent: Literal["retrieve","discuss"]
    source: Literal["meeting","note","task","all"]
    # needs_tasks: bool




rewrite_prompt = PromptTemplate.from_template("""
Rewrite the query to maximize semantic retrieval.
Do NOT answer it.

Query: {query}
""")


compression_prompt = PromptTemplate.from_template("""
Extract only parts relevant to the query.

Context:
{context}

Query:
{query}
""")


rag_prompt = PromptTemplate.from_template("""
You are Mind Trace Assistant.
Answer ONLY from the context.
If not found, say "Not found in project data".

Context:
{context}

Question:
{question}

Answer with sources if possible.
""")
