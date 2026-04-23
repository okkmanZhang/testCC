from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.chat import router as chat_router
from api.rate import router as rate_router

app = FastAPI(title="Payroll Compliance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api/v1")
app.include_router(rate_router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok"}