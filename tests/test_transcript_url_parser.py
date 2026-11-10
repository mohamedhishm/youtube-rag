import pytest

from transcript.url_parser import extract_video_id


TEST_VIDEO_ID = "dQw4w9WgXcQ"


@pytest.mark.parametrize(
    ("url", "expected_video_id"),
    [
        (
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            TEST_VIDEO_ID,
        ),
        (
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            TEST_VIDEO_ID,
        ),
        (
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            TEST_VIDEO_ID,
        ),
        (
            "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
            TEST_VIDEO_ID,
        ),
        (
            "https://youtu.be/dQw4w9WgXcQ",
            TEST_VIDEO_ID,
        ),
        (
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            TEST_VIDEO_ID,
        ),
        (
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            TEST_VIDEO_ID,
        ),
        (
            "https://www.youtube.com/live/dQw4w9WgXcQ",
            TEST_VIDEO_ID,
        ),
    ],
)
def test_extract_video_id_from_supported_urls(
    url,
    expected_video_id,
):
    assert extract_video_id(url) == expected_video_id


def test_watch_url_with_extra_query_parameters():
    url = (
        "https://www.youtube.com/watch?"
        "v=dQw4w9WgXcQ&list=PL123&index=2"
    )

    assert extract_video_id(url) == TEST_VIDEO_ID


def test_short_url_with_query_parameters():
    url = "https://youtu.be/dQw4w9WgXcQ?t=35"

    assert extract_video_id(url) == TEST_VIDEO_ID


def test_url_surrounded_by_spaces():
    url = "  https://youtu.be/dQw4w9WgXcQ  "

    assert extract_video_id(url) == TEST_VIDEO_ID


@pytest.mark.parametrize(
    "invalid_url",
    [
        "",
        "   ",
        "not-a-url",
        "www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://example.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch",
        "https://www.youtube.com/watch?v=",
        "https://youtu.be/short",
        "https://www.youtube.com/shorts/",
        "ftp://www.youtube.com/watch?v=dQw4w9WgXcQ",
    ],
)
def test_invalid_or_unsupported_urls(invalid_url):
    with pytest.raises(ValueError):
        extract_video_id(invalid_url)


@pytest.mark.parametrize(
    "invalid_value",
    [
        None,
        123,
        [],
        {},
    ],
)
def test_non_string_values(invalid_value):
    with pytest.raises(ValueError):
        extract_video_id(invalid_value)