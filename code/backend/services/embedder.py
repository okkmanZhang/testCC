import os
from typing import List, Dict
from openai import AzureOpenAI
from sqlalchemy import text
from models.database import SessionLocal
from dotenv import load_dotenv

load_dotenv()

AWARD_ID = "MA000004"


def get_azure_client() -> AzureOpenAI:
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )


def embed_and_store(chunks: List[Dict]) -> int:
    """Batch embed chunks using Azure OpenAI and store in award_chunks table."""
    client = get_azure_client()
    embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
    db = SessionLocal()
    stored = 0

    try:
        batch_size = 16
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [c["chunk_text"] for c in batch]
            texts = [t[:6000] if len(t) > 6000 else t for t in texts]

            response = client.embeddings.create(
                model=embedding_deployment,
                input=texts
            )

            for j, item in enumerate(response.data):
                chunk = batch[j]
                embedding_str = "[" + ",".join(str(x) for x in item.embedding) + "]"

                db.execute(text("""
                    INSERT INTO award_chunks
                        (award_id, chunk_text, embedding, section, clause, page_num, metadata)
                    VALUES
                        (:award_id, :chunk_text,
                        CAST(:embedding AS vector),
                        :section, :clause, :page_num,
                        CAST(:metadata AS jsonb))
                """), {
                    "award_id": AWARD_ID,
                    "chunk_text": chunk["chunk_text"],
                    "embedding": embedding_str,
                    "section": chunk.get("section"),
                    "clause": chunk.get("clause"),
                    "page_num": chunk.get("page_num"),
                    "metadata": "{}"
                })
                stored += 1

            db.commit()
            print(f"  Stored batch {i // batch_size + 1} ({stored}/{len(chunks)})")

    finally:
        db.close()

    return stored