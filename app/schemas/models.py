
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class VideoStatus(str, Enum):
    PROCESSING = "Processing"
    READY = "Ready"
    FAILED = "Failed"


class VideoProcessRequest(BaseModel):
    url: HttpUrl


class VideoProcessResponse(BaseModel):
    video_id: str
    title: str | None = None
    status: VideoStatus
    message: str


class VideoStatusResponse(BaseModel):
    video_id: str
    title: str | None = None
    status: VideoStatus
    error: str | None = None


class TranscriptChunk(BaseModel):
    chunk_id: str
    text: str
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(ge=0)


class TranscriptResult(BaseModel):
    video_id: str
    title: str | None = None
    chunks: list[TranscriptChunk]


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievedChunk(TranscriptChunk):
    score: float | None = None


class QuestionResponse(BaseModel):
    video_id: str
    answer: str
    sources: list[RetrievedChunk]
