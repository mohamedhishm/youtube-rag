
from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    description=(
        "Ask questions about YouTube videos "
        "using transcript retrieval and RAG."
    ),
)

app.include_router(router)


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "YouTube Video RAG Assistant API is running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
