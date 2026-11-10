from unittest.mock import patch

import pytest

from transcript.extractor import (
    EmptyTranscriptError,
    UnsupportedTranscriptLanguageError,
)
from transcript.models import TranscriptSegment
from transcript.pipeline import (
    classify_extraction_error,
    process_youtube_video,
)


VALID_URL = (
    "https://www.youtube.com/watch?v=abcdefghijk"
)

VIDEO_ID = "abcdefghijk"


def fake_mixed_segments():
    return [
        TranscriptSegment(
            text="النهاردة هنتكلم عن RAG",
            start_seconds=0.0,
            end_seconds=5.0,
        ),
        TranscriptSegment(
            text=(
                "Retrieval Augmented Generation "
                "بيستخدم semantic search"
            ),
            start_seconds=5.0,
            end_seconds=12.0,
        ),
    ]


@patch("transcript.pipeline.fetch_transcript")
def test_successful_pipeline_returns_fixed_contract(
    mock_fetch_transcript,
):
    mock_fetch_transcript.return_value = (
        fake_mixed_segments(),
        "ar",
        True,
    )

    result = process_youtube_video(
        url=VALID_URL,
        preferred_languages=["ar", "en"],
    )

    assert result["status"] == "success"
    assert result["video_id"] == VIDEO_ID
    assert result["title"] is None

    assert result["transcript_language"] == "ar"
    assert result["transcript_is_generated"] is True

    assert result["requested_languages"] == [
        "ar",
        "en",
    ]

    assert result["error"] is None
    assert len(result["chunks"]) == 1

    chunk = result["chunks"][0]

    assert chunk["chunk_id"] == (
        "abcdefghijk_chunk_0"
    )

    assert chunk["text"] == (
        "النهاردة هنتكلم عن RAG "
        "Retrieval Augmented Generation "
        "بيستخدم semantic search"
    )

    assert chunk["start_seconds"] == 0.0
    assert chunk["end_seconds"] == 12.0


@patch("transcript.pipeline.fetch_transcript")
def test_pipeline_passes_language_priority_to_extractor(
    mock_fetch_transcript,
):
    mock_fetch_transcript.return_value = (
        fake_mixed_segments(),
        "en",
        False,
    )

    process_youtube_video(
        url=VALID_URL,
        preferred_languages=["en", "ar"],
    )

    mock_fetch_transcript.assert_called_once_with(
        video_id=VIDEO_ID,
        preferred_languages=["en", "ar"],
    )


@patch("transcript.pipeline.fetch_transcript")
def test_default_languages_are_arabic_then_english(
    mock_fetch_transcript,
):
    mock_fetch_transcript.return_value = (
        fake_mixed_segments(),
        "ar",
        True,
    )

    result = process_youtube_video(
        url=VALID_URL,
    )

    assert result["requested_languages"] == [
        "ar",
        "en",
    ]

    mock_fetch_transcript.assert_called_once_with(
        video_id=VIDEO_ID,
        preferred_languages=["ar", "en"],
    )


def test_invalid_url_returns_fixed_failure_contract():
    result = process_youtube_video(
        url="https://example.com/video",
        preferred_languages=["ar", "en"],
    )

    assert result["status"] == "failed"
    assert result["video_id"] is None
    assert result["chunks"] == []

    assert result["error"]["code"] == "INVALID_URL"
    assert result["error"]["message"]


@pytest.mark.parametrize(
    "invalid_languages",
    [
        [],
        ["ar", ""],
        "ar",
    ],
)
def test_invalid_language_configuration(
    invalid_languages,
):
    result = process_youtube_video(
        url=VALID_URL,
        preferred_languages=invalid_languages,
    )

    assert result["status"] == "failed"

    assert result["error"]["code"] == (
        "INVALID_LANGUAGE_CONFIGURATION"
    )

    assert result["chunks"] == []


@patch("transcript.pipeline.fetch_transcript")
def test_unsupported_language_returns_clear_error(
    mock_fetch_transcript,
):
    mock_fetch_transcript.side_effect = (
        UnsupportedTranscriptLanguageError(
            requested_languages=["ar", "en"],
            available_languages=["fr"],
        )
    )

    result = process_youtube_video(
        url=VALID_URL,
        preferred_languages=["ar", "en"],
    )

    assert result["status"] == "failed"
    assert result["video_id"] == VIDEO_ID
    assert result["chunks"] == []

    assert result["error"]["code"] == (
        "UNSUPPORTED_TRANSCRIPT_LANGUAGE"
    )

    assert "Available" in result["error"]["message"]


@patch("transcript.pipeline.fetch_transcript")
def test_empty_transcript_returns_clear_error(
    mock_fetch_transcript,
):
    mock_fetch_transcript.side_effect = (
        EmptyTranscriptError(
            "The transcript contained no usable text."
        )
    )

    result = process_youtube_video(
        url=VALID_URL,
    )

    assert result["status"] == "failed"
    assert result["video_id"] == VIDEO_ID
    assert result["chunks"] == []

    assert result["error"]["code"] == (
        "EMPTY_TRANSCRIPT"
    )


@patch("transcript.pipeline.fetch_transcript")
def test_invalid_chunk_configuration_is_not_invalid_url(
    mock_fetch_transcript,
):
    mock_fetch_transcript.return_value = (
        fake_mixed_segments(),
        "ar",
        True,
    )

    result = process_youtube_video(
        url=VALID_URL,
        max_words=0,
    )

    assert result["status"] == "failed"

    assert result["error"]["code"] == (
        "INVALID_CHUNK_CONFIGURATION"
    )


@patch("transcript.pipeline.fetch_transcript")
def test_pipeline_creates_more_than_one_chunk(
    mock_fetch_transcript,
):
    mock_fetch_transcript.return_value = (
        [
            TranscriptSegment(
                text="one two",
                start_seconds=0.0,
                end_seconds=4.0,
            ),
            TranscriptSegment(
                text="three four",
                start_seconds=4.0,
                end_seconds=8.0,
            ),
            TranscriptSegment(
                text="five six",
                start_seconds=8.0,
                end_seconds=12.0,
            ),
        ],
        "en",
        False,
    )

    result = process_youtube_video(
        url=VALID_URL,
        max_words=2,
    )

    assert result["status"] == "success"

    assert [
        chunk["chunk_id"]
        for chunk in result["chunks"]
    ] == [
        "abcdefghijk_chunk_0",
        "abcdefghijk_chunk_1",
        "abcdefghijk_chunk_2",
    ]


class TranscriptsDisabled(Exception):
    pass


class VideoUnavailable(Exception):
    pass


class RequestBlocked(Exception):
    pass


@pytest.mark.parametrize(
    ("error", "expected_code"),
    [
        (
            TranscriptsDisabled("Disabled"),
            "TRANSCRIPT_DISABLED",
        ),
        (
            VideoUnavailable("Unavailable"),
            "VIDEO_UNAVAILABLE",
        ),
        (
            RequestBlocked("Blocked"),
            "REQUEST_BLOCKED",
        ),
        (
            RuntimeError("HTTP 429"),
            "RATE_LIMITED",
        ),
        (
            RuntimeError("Unknown error"),
            "TRANSCRIPT_EXTRACTION_FAILED",
        ),
    ],
)
def test_classify_extraction_errors(
    error,
    expected_code,
):
    assert classify_extraction_error(error) == (
        expected_code
    )