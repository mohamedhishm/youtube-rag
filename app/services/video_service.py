
from urllib.parse import parse_qs, urlparse

from fastapi import HTTPException

from app.core.config import settings
from transcript.pipeline import process_youtube_video

from app.schemas.models import (
    TranscriptResult,
    VideoProcessResponse,
    VideoStatus,
    VideoStatusResponse,
)


# Temporary in-memory storage for development.
VIDEO_STORE: dict[str, dict] = {}


# Maps the transcript pipeline's error codes to HTTP status codes.
PIPELINE_ERROR_STATUS = {
    "INVALID_URL": 400,
    "INVALID_VIDEO_ID": 400,
    "INVALID_LANGUAGE_CONFIGURATION": 400,
    "INVALID_CHUNK_CONFIGURATION": 400,
    "NO_TRANSCRIPT_FOUND": 422,
    "TRANSCRIPT_DISABLED": 422,
    "UNSUPPORTED_TRANSCRIPT_LANGUAGE": 422,
    "EMPTY_TRANSCRIPT": 422,
    "AGE_RESTRICTED": 422,
    "VIDEO_UNAVAILABLE": 404,
    "RATE_LIMITED": 429,
    "REQUEST_BLOCKED": 503,
}


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
        return _process_real_video(url)

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


def _process_real_video(url: str) -> VideoProcessResponse:
    """Run Karim's transcript pipeline and store the real chunks."""
    result = process_youtube_video(url=url)

    if result["status"] != "success":
        error = result.get("error") or {}
        code = error.get("code", "TRANSCRIPT_EXTRACTION_FAILED")
        raise HTTPException(
            status_code=PIPELINE_ERROR_STATUS.get(code, 502),
            detail=f"{code}: {error.get('message', 'Processing failed.')}",
        )

    video_id = result["video_id"]
    title = result["title"]

    # Index the chunks for semantic search (Ali's retrieval module).
    # Imported here so MOCK_MODE=true works without chromadb installed.
    try:
        from retrieval.retrieval import RetrievalError, index_chunks

        index_chunks(result)
    except RetrievalError as exc:
        raise HTTPException(status_code=422, detail=f"INDEXING_FAILED: {exc}") from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"INDEXING_FAILED: could not index the transcript ({exc}).",
        ) from exc

    transcript = TranscriptResult(
        video_id=video_id,
        title=title,
        chunks=result["chunks"],
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
        message=(
            f"Processed {len(transcript.chunks)} transcript chunks "
            f"(language: {result['transcript_language']})."
        ),
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
