from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)


@app.get("/")
def root():
    return {
        "message": "YouTube Video RAG Assistant API is running"
    }