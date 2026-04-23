# scripts/test_query.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from openai import AzureOpenAI
from sqlalchemy import text
from models.database import SessionLocal


def get_azure_client() -> AzureOpenAI:
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )


def search(query: str, top_k: int = 5):
    client = get_azure_client()
    embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")

    resp = client.embeddings.create(
        model=embedding_deployment,
        input=query
    )
    embedding_str = "[" + ",".join(str(x) for x in resp.data[0].embedding) + "]"

    db = SessionLocal()
    try:
        results = db.execute(text("""
            SELECT
                chunk_text,
                section,
                clause,
                page_num,
                1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM award_chunks
            WHERE award_id = 'MA000004'
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
        """), {"embedding": embedding_str, "top_k": top_k}).fetchall()

        print(f"\nQuery: {query}\n")
        print("=" * 60)
        for i, row in enumerate(results):
            print(f"\n[{i+1}] similarity={row.similarity:.3f}  clause={row.clause}  section={row.section}  page={row.page_num}")
            print(row.chunk_text[:300] + "..." if len(row.chunk_text) > 300 else row.chunk_text)
            print("-" * 40)

    finally:
        db.close()


if __name__ == "__main__":
    queries = [
        "Schedule B junior rates percentage age",
        "saturday penalty rate retail employee",
        "16 year old junior employee rate"
    ]
    for q in queries:
        search(q, top_k=3)
        print("\n")

# Add this temporarily to scripts/test_query.py bottom
if __name__ == "__main__":
    search("under 16 years of age junior rate percentage", top_k=5)        

# Add to scripts/test_query.py temporarily
if __name__ == "__main__":
    search("Table 4 minimum rates clause 17.1 adult retail employee level 3", top_k=3)    

# update test_query.py bottom temporarily
if __name__ == "__main__":
    search("overtime hours threshold full-time 38 hours per week clause 26", top_k=3)    