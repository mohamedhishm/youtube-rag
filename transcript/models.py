#TranscriptSegment
#TranscriptChunk
#PipelineError
#TranscriptResult


from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True) # frozen=True makes the dataclass immutable, meaning its attributes cannot be changed after instantiation.
class TranscriptSegment:
    """
    A single transcript segment returned by YouTube.

    The timestamps refer to the original video.
    """

    text: str
    start_seconds: float
    end_seconds: float


@dataclass(frozen=True)
class TranscriptChunk:
    """
    A group of consecutive transcript segments.

    This is the object that will later be sent to the retrieval module.
    """

    chunk_id: str
    text: str
    start_seconds: float
    end_seconds: float


@dataclass(frozen=True)
class PipelineError:
    """
    A predictable error returned by the transcript pipeline.
    """

    code: str
    message: str


@dataclass
class TranscriptResult:
    """
    The final result returned by the transcript pipeline.

    transcript_language represents the selected YouTube transcript track.
    The text itself may contain mixed Arabic and English.
    """

    status: str
    video_id: str | None
    title: str | None
    transcript_language: str | None
    transcript_is_generated: bool | None
    requested_languages: list[str]
    chunks: list[TranscriptChunk]
    error: PipelineError | None

    def to_dict(self) -> dict[str, Any]:
        """Convert the result and nested dataclasses to a dictionary."""

        return asdict(self)
