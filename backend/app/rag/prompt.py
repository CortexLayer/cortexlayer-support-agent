"""Prompts for controlling hallucinations and fallback behavior."""

from typing import Dict, List


def build_rag_prompt(query: str, context_chunks: List[Dict]) -> str:
    """Build prompt for RAG with retrieved context."""
    context_text = ""
    for i, chunk in enumerate(context_chunks):
        doc_name = chunk.get("metadata", {}).get("filename", "unknown")
        chunk_id = chunk.get("metadata", {}).get("chunk_index", i)
        text = chunk.get("text", "")

        context_text += f"\n[Document: {doc_name}, Chunk: {chunk_id}]\n" f"{text}\n"

    prompt = f"""You are a helpful customer support assistant.
Answer the user's question using ONLY the information provided
in the context below.

CONTEXT:
{context_text}

RULES:
1. Only use information from the context above
2. If the answer is not in the context, say
   "I don't have information about that in my knowledge base."
3. Include citations in format [doc: filename#chunk_number]
4. Be concise and accurate
5. If multiple sources support your answer, cite all relevant ones

USER QUESTION:
{query}

ANSWER:"""

    return prompt


def build_fallback_prompt(query: str) -> str:
    """Prompt when no relevant context is found."""
    return f"""You are a customer support assistant.
The user asked: "{query}"

Unfortunately, I don't have specific information about that
in my current knowledge base.

Please provide a helpful response that:
1. Acknowledges the question
2. Explains you don't have that specific information
3. Suggests they contact support directly for detailed help

Keep it professional and empathetic."""
