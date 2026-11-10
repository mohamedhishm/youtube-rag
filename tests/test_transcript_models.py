from transcript.models import (
    PipelineError,
    TranscriptChunk,
    TranscriptResult,
    TranscriptSegment,
)


def test_create_transcript_segment():
    segment = TranscriptSegment(
        text="Welcome to the video",
        start_seconds=1.5,
        end_seconds=4.8,
    )

    assert segment.text == "Welcome to the video" 
    assert segment.start_seconds == 1.5
    assert segment.end_seconds == 4.8


def test_segment_preserves_mixed_arabic_english_text():
    segment = TranscriptSegment(
        text="النهاردة هنتكلم عن Retrieval Augmented Generation",
        start_seconds=0.0,
        end_seconds=6.5,
    )

    assert segment.text == (
        "النهاردة هنتكلم عن Retrieval Augmented Generation"
    )


def test_create_transcript_chunk():
    chunk = TranscriptChunk(
        chunk_id="abcdefghijk_chunk_0",
        text="RAG combines retrieval with generation.",
        start_seconds=10.0,
        end_seconds=25.0,
    )

    assert chunk.chunk_id == "abcdefghijk_chunk_0"
    assert chunk.start_seconds == 10.0
    assert chunk.end_seconds == 25.0


def test_success_result_converts_to_dictionary():
    chunk = TranscriptChunk(
        chunk_id="abcdefghijk_chunk_0",
        text="الـ RAG يستخدم retrieval قبل generation",
        start_seconds=10.0,
        end_seconds=20.0,
    )

    result = TranscriptResult(
        status="success",
        video_id="abcdefghijk",
        title="Introduction to RAG",
        transcript_language="ar",
        transcript_is_generated=True,
        requested_languages=["ar", "en"],
        chunks=[chunk],
        error=None,
    )

    output = result.to_dict()

    assert output["status"] == "success"
    assert output["video_id"] == "abcdefghijk"
    assert output["transcript_language"] == "ar"
    assert output["requested_languages"] == ["ar", "en"]
    assert output["error"] is None

    assert output["chunks"] == [
        {
            "chunk_id": "abcdefghijk_chunk_0",
            "text": "الـ RAG يستخدم retrieval قبل generation",
            "start_seconds": 10.0,
            "end_seconds": 20.0,
        }
    ]


def test_failed_result_converts_to_dictionary():
    error = PipelineError(
        code="NO_TRANSCRIPT_FOUND",
        message="No transcript is available for this video.",
    )

    result = TranscriptResult(
        status="failed",
        video_id="abcdefghijk",
        title=None,
        transcript_language=None,
        transcript_is_generated=None,
        requested_languages=["ar", "en"],
        chunks=[],
        error=error,
    )

    output = result.to_dict()

    assert output["status"] == "failed"
    assert output["chunks"] == []
    assert output["error"] == {
        "code": "NO_TRANSCRIPT_FOUND",
        "message": "No transcript is available for this video.",
    }