
from fastapi import APIRouter, HTTPException, status

from app.schemas.models import (
    QuestionRequest,
    QuestionResponse,
    VideoProcessRequest,
    VideoProcessResponse,
    VideoStatusResponse,
)
from app.services.rag_service import answer_question
from app.services.video_service import (
    get_video_status,
    process_video,
)

router = APIRouter(prefix="/api", tags=["YouTube RAG"])


@router.post(
    "/videos/process",
    response_model=VideoProcessResponse,
    status_code=status.HTTP_200_OK,
)
def process_video_endpoint(
    request: VideoProcessRequest,
) -> VideoProcessResponse:
    try:
        return process_video(str(request.url))
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=501,
            detail=str(exc),
        ) from exc


@router.get(
    "/videos/{video_id}/status",
    response_model=VideoStatusResponse,
)
def video_status_endpoint(
    video_id: str,
) -> VideoStatusResponse:
    return get_video_status(video_id)


@router.post(
    "/videos/{video_id}/questions",
    response_model=QuestionResponse,
)
def question_endpoint(
    video_id: str,
    request: QuestionRequest,
) -> QuestionResponse:
    return answer_question(
        video_id=video_id,
        question=request.question,
        top_k=request.top_k,
    )
