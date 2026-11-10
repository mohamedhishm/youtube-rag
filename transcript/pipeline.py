from __future__ import annotations

from typing import Any

from transcript.chunker import chunk_segments
from transcript.extractor import (
    EmptyTranscriptError,
    UnsupportedTranscriptLanguageError,
    fetch_transcript,
    validate_preferred_languages,
)
from transcript.models import (
    PipelineError,
    TranscriptResult,
)
from transcript.url_parser import extract_video_id


def classify_extraction_error(error: Exception) -> str:
    """
    Convert extraction exceptions into stable API error codes.

    Some errors come from youtube-transcript-api. Class-name matching keeps
    this layer independent from small exception import changes between
    library versions.
    """

    error_name = type(error).__name__.lower()
    error_message = str(error).lower()

    if isinstance(error, UnsupportedTranscriptLanguageError):
        return "UNSUPPORTED_TRANSCRIPT_LANGUAGE"

    if isinstance(error, EmptyTranscriptError):
        return "EMPTY_TRANSCRIPT"

    if "transcriptsdisabled" in error_name:
        return "TRANSCRIPT_DISABLED"

    if "notranscriptfound" in error_name:
        return "NO_TRANSCRIPT_FOUND"

    if "videounavailable" in error_name:
        return "VIDEO_UNAVAILABLE"

    if "invalidvideoid" in error_name:
        return "INVALID_VIDEO_ID"

    if "age" in error_name and "restricted" in error_name:
        return "AGE_RESTRICTED"

    if "requestblocked" in error_name or "ipblocked" in error_name:
        return "REQUEST_BLOCKED"

    if (
        "429" in error_message
        or "too many requests" in error_message
    ):
        return "RATE_LIMITED"

    return "TRANSCRIPT_EXTRACTION_FAILED"


def failed_result(
    *,
    video_id: str | None,
    requested_languages: list[str],
    error_code: str,
    error_message: str,
) -> dict[str, Any]:
    """
    Build a failure result using the same stable contract every time.
    """

    result = TranscriptResult(
        status="failed",
        video_id=video_id,
        title=None,
        transcript_language=None,
        transcript_is_generated=None,
        requested_languages=requested_languages,
        chunks=[],
        error=PipelineError(
            code=error_code,
            message=error_message,
        ),
    )

    return result.to_dict()


def process_youtube_video(
    url: str,
    preferred_languages: list[str] | None = None,
    max_words: int = 120,
    max_duration_seconds: float = 60.0,
) -> dict[str, Any]:
    """
    Process a YouTube URL into timestamped transcript chunks.

    Processing stages:
    1. Validate requested languages.
    2. Extract and validate the YouTube video ID.
    3. Retrieve one transcript track using the language policy.
    4. Convert the transcript into timestamped segments.
    5. Combine consecutive segments into timestamped chunks.
    6. Return a stable dictionary for Backend and Retrieval integration.

    Mixed Arabic-English text is preserved. No translation, embeddings,
    retrieval, or LLM work is performed here.
    """

    video_id: str | None = None

    try:
        requested_languages = validate_preferred_languages(
            preferred_languages
        )
    except (TypeError, ValueError) as error:
        return failed_result(
            video_id=None,
            requested_languages=[],
            error_code="INVALID_LANGUAGE_CONFIGURATION",
            error_message=str(error),
        )

    try:
        video_id = extract_video_id(url)
    except (TypeError, ValueError) as error:
        return failed_result(
            video_id=None,
            requested_languages=requested_languages,
            error_code="INVALID_URL",
            error_message=str(error),
        )

    try:
        segments, transcript_language, is_generated = (
            fetch_transcript(
                video_id=video_id,
                preferred_languages=requested_languages,
            )
        )
    except Exception as error:
        return failed_result(
            video_id=video_id,
            requested_languages=requested_languages,
            error_code=classify_extraction_error(error),
            error_message=str(error),
        )

    try:
        chunks = chunk_segments(
            video_id=video_id,
            segments=segments,
            max_words=max_words,
            max_duration_seconds=max_duration_seconds,
        )
    except (TypeError, ValueError) as error:
        return failed_result(
            video_id=video_id,
            requested_languages=requested_languages,
            error_code="INVALID_CHUNK_CONFIGURATION",
            error_message=str(error),
        )
    except Exception as error:
        return failed_result(
            video_id=video_id,
            requested_languages=requested_languages,
            error_code="CHUNKING_FAILED",
            error_message=str(error),
        )

    if not chunks:
        return failed_result(
            video_id=video_id,
            requested_languages=requested_languages,
            error_code="EMPTY_TRANSCRIPT",
            error_message=(
                "The transcript produced no usable chunks."
            ),
        )

    result = TranscriptResult(
        status="success",
        video_id=video_id,
        title=None,
        transcript_language=transcript_language,
        transcript_is_generated=is_generated,
        requested_languages=requested_languages,
        chunks=chunks,
        error=None,
    )

    return result.to_dict()