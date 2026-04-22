from code.backend.models.database import engine

try:
    with engine.connect() as connection:
        print("✅ 成功连接到 Docker 中的 PostgreSQL！")
except Exception as e:
    print(f"❌ 连接失败: {e}")