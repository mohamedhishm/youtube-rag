import pytest

from transcript.chunker import chunk_segments
from transcript.models import TranscriptSegment


VIDEO_ID = "abcdefghijk"


def test_empty_segments_return_empty_chunks():
    chunks = chunk_segments(
        video_id=VIDEO_ID,
        segments=[],
    )

    assert chunks == []


def test_combines_consecutive_segments_in_one_chunk():
    segments = [
        TranscriptSegment(
            text="Welcome to the course",
            start_seconds=0.0,
            end_seconds=4.0,
        ),
        TranscriptSegment(
            text="Today we will learn about RAG",
            start_seconds=4.0,
            end_seconds=10.5,
        ),
    ]

    chunks = chunk_segments(
        video_id=VIDEO_ID,
        segments=segments,
    )

    assert len(chunks) == 1

    assert chunks[0].chunk_id == (
        "abcdefghijk_chunk_0"
    )

    assert chunks[0].text == (
        "Welcome to the course "
        "Today we will learn about RAG"
    )

    assert chunks[0].start_seconds == 0.0
    assert chunks[0].end_seconds == 10.5


def test_preserves_mixed_arabic_english_text():
    segments = [
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

    chunks = chunk_segments(
        video_id=VIDEO_ID,
        segments=segments,
    )

    assert len(chunks) == 1

    assert chunks[0].text == (
        "النهاردة هنتكلم عن RAG "
        "Retrieval Augmented Generation "
        "بيستخدم semantic search"
    )

    assert chunks[0].start_seconds == 0.0
    assert chunks[0].end_seconds == 12.0


def test_splits_chunks_before_exceeding_word_limit():
    segments = [
        TranscriptSegment(
            text="one two three",
            start_seconds=0.0,
            end_seconds=4.0,
        ),
        TranscriptSegment(
            text="four five",
            start_seconds=4.0,
            end_seconds=8.0,
        ),
        TranscriptSegment(
            text="six seven",
            start_seconds=8.0,
            end_seconds=12.0,
        ),
    ]

    chunks = chunk_segments(
        video_id=VIDEO_ID,
        segments=segments,
        max_words=5,
        max_duration_seconds=60.0,
    )

    assert len(chunks) == 2

    assert chunks[0].text == "one two three four five"
    assert chunks[0].start_seconds == 0.0
    assert chunks[0].end_seconds == 8.0

    assert chunks[1].text == "six seven"
    assert chunks[1].start_seconds == 8.0
    assert chunks[1].end_seconds == 12.0


def test_splits_chunks_before_exceeding_duration_limit():
    segments = [
        TranscriptSegment(
            text="First segment",
            start_seconds=0.0,
            end_seconds=20.0,
        ),
        TranscriptSegment(
            text="Second segment",
            start_seconds=20.0,
            end_seconds=40.0,
        ),
        TranscriptSegment(
            text="Third segment",
            start_seconds=40.0,
            end_seconds=70.0,
        ),
    ]

    chunks = chunk_segments(
        video_id=VIDEO_ID,
        segments=segments,
        max_words=100,
        max_duration_seconds=60.0,
    )

    assert len(chunks) == 2

    assert chunks[0].text == (
        "First segment Second segment"
    )
    assert chunks[0].start_seconds == 0.0
    assert chunks[0].end_seconds == 40.0

    assert chunks[1].text == "Third segment"
    assert chunks[1].start_seconds == 40.0
    assert chunks[1].end_seconds == 70.0


def test_does_not_lose_any_segment_text():
    segments = [
        TranscriptSegment(
            text="first segment",
            start_seconds=0.0,
            end_seconds=4.0,
        ),
        TranscriptSegment(
            text="second segment",
            start_seconds=4.0,
            end_seconds=8.0,
        ),
        TranscriptSegment(
            text="third segment",
            start_seconds=8.0,
            end_seconds=12.0,
        ),
        TranscriptSegment(
            text="fourth segment",
            start_seconds=12.0,
            end_seconds=16.0,
        ),
    ]

    chunks = chunk_segments(
        video_id=VIDEO_ID,
        segments=segments,
        max_words=3,
    )

    combined_output = " ".join(
        chunk.text for chunk in chunks
    )

    expected_output = " ".join(
        segment.text for segment in segments
    )

    assert combined_output == expected_output


def test_ignores_empty_and_noise_only_segments():
    segments = [
        TranscriptSegment(
            text="[Music]",
            start_seconds=0.0,
            end_seconds=3.0,
        ),
        TranscriptSegment(
            text="Welcome to the video",
            start_seconds=3.0,
            end_seconds=8.0,
        ),
        TranscriptSegment(
            text="   ",
            start_seconds=8.0,
            end_seconds=9.0,
        ),
    ]

    chunks = chunk_segments(
        video_id=VIDEO_ID,
        segments=segments,
    )

    assert len(chunks) == 1
    assert chunks[0].text == "Welcome to the video"
    assert chunks[0].start_seconds == 3.0
    assert chunks[0].end_seconds == 8.0


def test_chunk_ids_are_unique_and_ordered():
    segments = [
        TranscriptSegment(
            text="one two",
            start_seconds=0.0,
            end_seconds=5.0,
        ),
        TranscriptSegment(
            text="three four",
            start_seconds=5.0,
            end_seconds=10.0,
        ),
        TranscriptSegment(
            text="five six",
            start_seconds=10.0,
            end_seconds=15.0,
        ),
    ]

    chunks = chunk_segments(
        video_id=VIDEO_ID,
        segments=segments,
        max_words=2,
    )

    chunk_ids = [chunk.chunk_id for chunk in chunks]

    assert chunk_ids == [
        "abcdefghijk_chunk_0",
        "abcdefghijk_chunk_1",
        "abcdefghijk_chunk_2",
    ]


def test_single_segment_can_exceed_preferred_limits():
    segments = [
        TranscriptSegment(
            text="one two three four five six",
            start_seconds=0.0,
            end_seconds=90.0,
        )
    ]

    chunks = chunk_segments(
        video_id=VIDEO_ID,
        segments=segments,
        max_words=3,
        max_duration_seconds=20.0,
    )

    assert len(chunks) == 1
    assert chunks[0].text == (
        "one two three four five six"
    )
    assert chunks[0].start_seconds == 0.0
    assert chunks[0].end_seconds == 90.0


@pytest.mark.parametrize(
    "invalid_max_words",
    [
        0,
        -1,
        1.5,
        True,
    ],
)
def test_rejects_invalid_max_words(invalid_max_words):
    with pytest.raises(ValueError):
        chunk_segments(
            video_id=VIDEO_ID,
            segments=[],
            max_words=invalid_max_words,
        )


@pytest.mark.parametrize(
    "invalid_duration",
    [
        0,
        -1,
        "60",
        True,
    ],
)
def test_rejects_invalid_max_duration(invalid_duration):
    with pytest.raises(ValueError):
        chunk_segments(
            video_id=VIDEO_ID,
            segments=[],
            max_duration_seconds=invalid_duration,
        )


def test_rejects_empty_video_id():
    with pytest.raises(
        ValueError,
        match="video_id must be a non-empty string",
    ):
        chunk_segments(
            video_id="",
            segments=[],
        )


def test_rejects_negative_start_timestamp():
    segments = [
        TranscriptSegment(
            text="Invalid segment",
            start_seconds=-1.0,
            end_seconds=2.0,
        )
    ]

    with pytest.raises(
        ValueError,
        match="start_seconds cannot be negative",
    ):
        chunk_segments(
            video_id=VIDEO_ID,
            segments=segments,
        )


def test_rejects_end_before_start():
    segments = [
        TranscriptSegment(
            text="Invalid segment",
            start_seconds=10.0,
            end_seconds=5.0,
        )
    ]

    with pytest.raises(
        ValueError,
        match="end_seconds cannot be earlier",
    ):
        chunk_segments(
            video_id=VIDEO_ID,
            segments=segments,
        )


def test_rejects_segments_out_of_order():
    segments = [
        TranscriptSegment(
            text="Later segment",
            start_seconds=10.0,
            end_seconds=15.0,
        ),
        TranscriptSegment(
            text="Earlier segment",
            start_seconds=2.0,
            end_seconds=5.0,
        ),
    ]

    with pytest.raises(
        ValueError,
        match="chronological order",
    ):
        chunk_segments(
            video_id=VIDEO_ID,
            segments=segments,
        )