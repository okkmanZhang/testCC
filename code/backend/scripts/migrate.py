# scripts/migrate.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        # 启用 pgvector 扩展
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS award_chunks (
                id          SERIAL PRIMARY KEY,
                award_id    TEXT NOT NULL,
                chunk_text  TEXT NOT NULL,
                embedding   vector(1536),
                section     TEXT,
                clause      TEXT,
                page_num    INT,
                metadata    JSONB,
                created_at  TIMESTAMPTZ DEFAULT now()
            )
        """))

        # 向量相似度索引（数据量大后生效，现在先建着）
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS award_chunks_embedding_idx
            ON award_chunks
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """))

        # 全文搜索索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS award_chunks_fts_idx
            ON award_chunks
            USING gin(to_tsvector('english', chunk_text))
        """))

        conn.commit()
        print("✅ Migration complete")

if __name__ == "__main__":
    migrate()