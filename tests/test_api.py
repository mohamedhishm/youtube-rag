
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_process_video():
    response = client.post(
        "/api/videos/process",
        json={
            "url": "https://www.youtube.com/watch?v=abcdefghijk"
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["video_id"] == "abcdefghijk"
    assert data["status"] == "Ready"


def test_video_status():
    client.post(
        "/api/videos/process",
        json={
            "url": "https://youtu.be/abcdefghijk"
        },
    )

    response = client.get(
        "/api/videos/abcdefghijk/status"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Ready"


def test_question_returns_timestamps():
    client.post(
        "/api/videos/process",
        json={
            "url": "https://youtu.be/abcdefghijk"
        },
    )

    response = client.post(
        "/api/videos/abcdefghijk/questions",
        json={
            "question": "What is RAG?",
            "top_k": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["video_id"] == "abcdefghijk"
    assert len(data["sources"]) == 1

    source = data["sources"][0]
    assert source["chunk_id"] == "abcdefghijk_chunk_0"
    assert source["start_seconds"] == 35.0
    assert source["end_seconds"] == 58.0


def test_invalid_youtube_url():
    response = client.post(
        "/api/videos/process",
        json={"url": "https://example.com/video"},
    )

    assert response.status_code == 400


def test_question_before_processing():
    response = client.post(
        "/api/videos/zzzzzzzzzzz/questions",
        json={"question": "What is RAG?"},
    )

    assert response.status_code == 404
