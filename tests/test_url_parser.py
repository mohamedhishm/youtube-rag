import pytest

from transcript.url_parser import extract_video_id


@pytest.mark.parametrize(
    "url, expected_video_id",
    [
        (
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "dQw4w9WgXcQ",
        ),
        (
            "https://youtu.be/dQw4w9WgXcQ",
            "dQw4w9WgXcQ",
        ),
        (
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "dQw4w9WgXcQ",
        ),
        (
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "dQw4w9WgXcQ",
        ),
        (
            "https://www.youtube.com/live/dQw4w9WgXcQ",
            "dQw4w9WgXcQ",
        ),
    ],
)
def test_extract_video_id(url, expected_video_id):
    assert extract_video_id(url) == expected_video_id


@pytest.mark.parametrize(
    "invalid_url",
    [
        "",
        "hello",
        "https://example.com/video",
        "https://www.youtube.com/watch",
        "https://youtu.be/invalid",
    ],
)
def test_invalid_youtube_url(invalid_url):
    with pytest.raises(ValueError):
        extract_video_id(invalid_url)