
from groq import Groq
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.models import (
    QuestionResponse,
    RetrievedChunk,
    VideoStatus,
)
from app.services.video_service import VIDEO_STORE


def generate_answer(question: str, sources: list[RetrievedChunk]) -> str:
    if not settings.groq_api_key:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY is not configured.",
        )

    context = "\n\n".join(
        (
            f"Source {i} "
            f"(timestamp {chunk.start_seconds:.1f}-"
            f"{chunk.end_seconds:.1f} seconds):\n"
            f"{chunk.text}"
        )
        for i, chunk in enumerate(sources, start=1)
    )

    client = Groq(api_key=settings.groq_api_key)

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a YouTube video assistant. "
                        "Answer using only the provided transcript "
                        "context. If the context does not contain "
                        "the answer, clearly say that you could not "
                        "find the answer in the available transcript. "
                        "Do not invent facts or timestamps. "
                        "Answer clearly and concisely."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Transcript context:\n{context}\n\n"
                        f"Question: {question}"
                    ),
                },
            ],
            max_completion_tokens=800,
            include_reasoning=False,
        )

        answer = response.choices[0].message.content

        if not answer or not answer.strip():
            raise HTTPException(
                status_code=502,
                detail="The language model returned an empty answer.",
            )

        return answer.strip()

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Failed to generate an answer using the language model.",
        ) from exc


def answer_question(
    video_id: str,
    question: str,
    top_k: int = 5,
) -> QuestionResponse:
    video = VIDEO_STORE.get(video_id)

    if video is None:
        raise HTTPException(
            status_code=404,
            detail="Video not found. Process it first.",
        )

    if video["status"] != VideoStatus.READY:
        raise HTTPException(
            status_code=409,
            detail="Video is not ready for questions.",
        )

    transcript = video["transcript"]

    # Temporary retrieval: select the first chunks.
    # Replace this with Ali's semantic retriever during integration.
    selected_chunks = transcript.chunks[:top_k]

    sources = [
        RetrievedChunk(
            chunk_id=chunk.chunk_id,
            text=chunk.text,
            start_seconds=chunk.start_seconds,
            end_seconds=chunk.end_seconds,
            score=None,
        )
        for chunk in selected_chunks
    ]

    if not sources:
        answer = "No transcript context is available for this video."
    elif settings.use_llm:
        answer = generate_answer(question, sources)
    else:
        answer = (
            "Mock answer: the transcript chunks are available, "
            "but real language-model generation is disabled."
        )

    return QuestionResponse(
        video_id=video_id,
        answer=answer,
        sources=sources,
    )
