
from urllib.parse import parse_qs, urlparse

from fastapi import HTTPException

from app.core.config import settings
from app.schemas.models import (
    TranscriptResult,
    VideoProcessResponse,
    VideoStatus,
    VideoStatusResponse,
)


# Temporary in-memory storage for development.
VIDEO_STORE: dict[str, dict] = {}


def extract_video_id(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    video_id = ""

    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]

    elif host == "youtube.com" or host.endswith(".youtube.com"):
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        else:
            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 2 and parts[0] in {
                "embed", "shorts", "live"
            }:
                video_id = parts[1]

    if not video_id or len(video_id) != 11:
        raise HTTPException(
            status_code=400,
            detail="Invalid or unsupported YouTube URL.",
        )

    return video_id


def process_video(url: str) -> VideoProcessResponse:
    video_id = extract_video_id(url)

    if not settings.mock_mode:
        raise NotImplementedError(
            "Connect the real transcript pipeline before "
            "disabling MOCK_MODE."
        )

    # Temporary sample data. Replace with Karim's pipeline.
    title = "Introduction to RAG (Mock Data)"

    transcript = TranscriptResult(
        video_id=video_id,
        title=title,
        chunks=[
            {
                "chunk_id": f"{video_id}_chunk_0",
                "text": (
                    "Retrieval-Augmented Generation combines "
                    "retrieval with language model generation."
                ),
                "start_seconds": 35.0,
                "end_seconds": 58.0,
            },
            {
                "chunk_id": f"{video_id}_chunk_1",
                "text": (
                    "A retriever finds relevant information "
                    "from a knowledge source before answering."
                ),
                "start_seconds": 59.0,
                "end_seconds": 82.0,
            },
        ],
    )

    VIDEO_STORE[video_id] = {
        "title": title,
        "status": VideoStatus.READY,
        "transcript": transcript,
        "error": None,
    }

    return VideoProcessResponse(
        video_id=video_id,
        title=title,
        status=VideoStatus.READY,
        message="Mock video processed successfully.",
    )


def get_video_status(video_id: str) -> VideoStatusResponse:
    video = VIDEO_STORE.get(video_id)

    if video is None:
        raise HTTPException(
            status_code=404,
            detail="Video not found. Process it first.",
        )

    return VideoStatusResponse(
        video_id=video_id,
        title=video["title"],
        status=video["status"],
        error=video["error"],
    )
