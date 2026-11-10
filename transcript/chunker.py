from transcript.cleaner import clean_text
from transcript.models import TranscriptChunk, TranscriptSegment


def chunk_segments(
    video_id: str,
    segments: list[TranscriptSegment],
    max_words: int = 120,
    max_duration_seconds: float = 60.0,
) -> list[TranscriptChunk]:
    """
    Combine consecutive transcript segments into timestamped chunks.

    A chunk is closed before adding a new segment when adding that segment
    would exceed either the maximum word count or maximum duration.

    The function preserves:
    - Segment order.
    - Original Arabic-English text.
    - Start time of the first segment in each chunk.
    - End time of the last segment in each chunk.

    Args:
        video_id:
            The YouTube video ID used to generate unique chunk IDs.

        segments:
            Ordered transcript segments from the selected transcript track.

        max_words:
            Maximum preferred number of words in one chunk.

        max_duration_seconds:
            Maximum preferred duration of one chunk in seconds.

    Returns:
        A list of timestamped TranscriptChunk objects.

    Raises:
        ValueError:
            If video_id is empty, limits are invalid, or segment timestamps
            are invalid or out of chronological order.
    """

    if not isinstance(video_id, str) or not video_id.strip():
        raise ValueError("video_id must be a non-empty string.")

    if isinstance(max_words, bool) or not isinstance(max_words, int):
        raise ValueError("max_words must be an integer.")

    if max_words <= 0:
        raise ValueError("max_words must be greater than zero.")

    if isinstance(max_duration_seconds, bool) or not isinstance(
        max_duration_seconds,
        (int, float),
    ):
        raise ValueError(
            "max_duration_seconds must be a number."
        )

    if max_duration_seconds <= 0:
        raise ValueError(
            "max_duration_seconds must be greater than zero."
        )

    if not isinstance(segments, list):
        raise TypeError("segments must be a list.")

    chunks: list[TranscriptChunk] = []

    current_texts: list[str] = []
    current_word_count = 0
    current_start: float | None = None
    current_end: float | None = None

    previous_segment_start: float | None = None

    def close_current_chunk() -> None:
        """
        Store the current chunk, then reset the temporary state.
        """

        nonlocal current_texts
        nonlocal current_word_count
        nonlocal current_start
        nonlocal current_end

        if not current_texts:
            return

        if current_start is None or current_end is None:
            raise RuntimeError(
                "Chunk timestamps were not initialized correctly."
            )

        chunk_index = len(chunks)

        chunks.append(
            TranscriptChunk(
                chunk_id=f"{video_id}_chunk_{chunk_index}",
                text=" ".join(current_texts),
                start_seconds=round(current_start, 3),
                end_seconds=round(current_end, 3),
            )
        )

        current_texts = []
        current_word_count = 0
        current_start = None
        current_end = None

    for segment in segments:
        if not isinstance(segment, TranscriptSegment):
            raise TypeError(
                "Every item in segments must be a TranscriptSegment."
            )

        if segment.start_seconds < 0:
            raise ValueError(
                "Segment start_seconds cannot be negative."
            )

        if segment.end_seconds < segment.start_seconds:
            raise ValueError(
                "Segment end_seconds cannot be earlier than start_seconds."
            )

        if (
            previous_segment_start is not None
            and segment.start_seconds < previous_segment_start
        ):
            raise ValueError(
                "Transcript segments must be in chronological order."
            )

        previous_segment_start = segment.start_seconds

        cleaned_text = clean_text(segment.text)

        if not cleaned_text:
            continue

        segment_word_count = len(cleaned_text.split())

        if current_start is None:
            current_start = segment.start_seconds

        proposed_word_count = (
            current_word_count + segment_word_count
        )

        proposed_duration = (
            segment.end_seconds - current_start
        )

        exceeds_limit = bool(current_texts) and (
            proposed_word_count > max_words
            or proposed_duration > max_duration_seconds
        )

        if exceeds_limit:
            close_current_chunk()
            current_start = segment.start_seconds

        current_texts.append(cleaned_text)
        current_word_count += segment_word_count
        current_end = segment.end_seconds

    close_current_chunk()

    return chunks