from fastapi import FastAPI
from api.chat import router as chat_router

app = FastAPI(title="Payroll Compliance API")

app.include_router(chat_router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok"}