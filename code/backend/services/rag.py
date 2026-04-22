import os
from typing import List, Dict
from openai import AzureOpenAI
from sqlalchemy import text
from models.database import SessionLocal
from dotenv import load_dotenv

load_dotenv()

AWARD_ID = "MA000004"

SYSTEM_PROMPT = """You are an Australian Fair Work compliance assistant specialising in the 
General Retail Industry Award 2020 [MA000004].

Your job is to answer payroll questions accurately using ONLY the Award clauses provided in the context.

Rules:
- Always cite the specific clause or schedule number (e.g. "clause 18.1", "Schedule B.3")
- If calculating pay, show the step-by-step breakdown
- If the context does not contain enough information to answer, say so clearly
- Never guess or use knowledge outside the provided context
- Amounts are in AUD
"""

REWRITE_PROMPT = """Convert the user's payroll question into 3 short search queries 
to find relevant clauses in the General Retail Industry Award 2020.

Return ONLY a JSON array of 3 strings, no explanation.
Example: ["junior rates percentage age", "saturday penalty rate retail", "16 year old minimum wage"]
"""


def get_azure_client() -> AzureOpenAI:
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )


def rewrite_query(question: str) -> List[str]:
    """Rewrite user question into multiple search queries for better retrieval."""
    client = get_azure_client()
    chat_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    try:
        response = client.chat.completions.create(
            model=chat_deployment,
            messages=[
                {"role": "system", "content": REWRITE_PROMPT},
                {"role": "user", "content": question}
            ],
            temperature=0,
            max_tokens=100,
            response_format={"type": "json_object"}
        )
        import json
        content = response.choices[0].message.content
        parsed = json.loads(content)
        # handle both {"queries": [...]} and direct array wrapped in object
        if isinstance(parsed, list):
            return parsed
        return list(parsed.values())[0]
    except Exception:
        # fallback to original question if rewrite fails
        return [question]


def retrieve_chunks(queries: List[str], top_k: int = 4) -> List[Dict]:
    """Retrieve chunks for multiple queries, deduplicated by id."""
    client = get_azure_client()
    embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
    db = SessionLocal()
    seen_texts = set()
    all_chunks = []

    try:
        for query in queries:
            resp = client.embeddings.create(model=embedding_deployment, input=query)
            embedding_str = "[" + ",".join(str(x) for x in resp.data[0].embedding) + "]"

            rows = db.execute(text("""
                SELECT
                    chunk_text,
                    section,
                    clause,
                    page_num,
                    1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
                FROM award_chunks
                WHERE award_id = :award_id
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
            """), {
                "embedding": embedding_str,
                "award_id": AWARD_ID,
                "top_k": top_k
            }).fetchall()

            for row in rows:
                # deduplicate by first 100 chars of text
                key = row.chunk_text[:100]
                if key not in seen_texts:
                    seen_texts.add(key)
                    all_chunks.append({
                        "chunk_text": row.chunk_text,
                        "section": row.section,
                        "clause": row.clause,
                        "page_num": row.page_num,
                        "similarity": float(row.similarity)
                    })

        # sort by similarity descending
        all_chunks.sort(key=lambda x: x["similarity"], reverse=True)
        return all_chunks[:8]  # return top 8 unique chunks across all queries

    finally:
        db.close()


def build_context(chunks: List[Dict]) -> str:
    """Format retrieved chunks into a context block for the LLM."""
    parts = []
    for i, chunk in enumerate(chunks):
        label = chunk.get("section") or chunk.get("clause") or f"page {chunk.get('page_num')}"
        parts.append(f"[Source {i+1} — {label}]\n{chunk['chunk_text']}")
    return "\n\n---\n\n".join(parts)


def answer_question(question: str) -> Dict:
    """
    Full RAG pipeline:
    1. Rewrite query into multiple search queries
    2. Retrieve relevant chunks for each query
    3. Build context
    4. Generate answer with LLM
    """
    client = get_azure_client()
    chat_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    # Step 1: rewrite
    queries = rewrite_query(question)
    print(f"Rewritten queries: {queries}")

    # Step 2: retrieve
    chunks = retrieve_chunks(queries)
    print(f"Retrieved {len(chunks)} unique chunks")

    # Step 3: build context
    context = build_context(chunks)

    # Step 4: generate
    user_message = f"""Use the following Award clauses to answer the question.

AWARD CONTEXT:
{context}

QUESTION:
{question}
"""

    response = client.chat.completions.create(
        model=chat_deployment,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        temperature=0,
        max_tokens=800
    )

    answer = response.choices[0].message.content

    sources = []
    for chunk in chunks:
        ref = chunk.get("section") or chunk.get("clause") or f"page {chunk.get('page_num')}"
        sources.append({
            "ref": ref,
            "page": chunk.get("page_num"),
            "similarity": round(chunk["similarity"], 3)
        })

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(chunks)
    }