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
    # source: Literal["meeting","note","task","all"]
    use_tasks: bool
    use_meetings: bool
    use_notes: bool




rewrite_prompt = PromptTemplate.from_template("""
Rewrite the query into a short, concrete search query.
Rules:
- Output ONE sentence only
- NO explanations
- NO bullet points
- NO meta reasoning
- Preserve entities exactly as written
- Prefer explicit filters like author, date, type when possible

Query: {query}
""")


compression_prompt = PromptTemplate.from_template("""
From the context below, keep ONLY sentences that directly help answer the query.
Do NOT explain.
Do NOT rephrase.
If nothing is relevant, return an empty string.

Context:
{context}

Query:
{query}
""")


rag_prompt = PromptTemplate.from_template("""
You are Mind Trace Assistant.

You must answer strictly using the provided context.
Do not use external knowledge.
If the answer cannot be found in the context, say exactly:
"Not found in project data"
Do not provide any additional explanation when refusing.

Context:
{context}

Question:
{question}

Answer:
""")

