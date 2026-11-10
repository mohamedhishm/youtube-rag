import re
from urllib.parse import parse_qs, urlparse


VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")

SUPPORTED_YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
}

SHORT_YOUTUBE_HOSTS = {
    "youtu.be",
    "www.youtu.be",
}


def extract_video_id(url: str) -> str:
    """
    Extract and validate a YouTube video ID from a supported URL.

    Supported examples:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/live/VIDEO_ID

    Raises:
        ValueError: If the URL is empty, invalid, or unsupported.
    """

    if not isinstance(url, str) or not url.strip():
        raise ValueError("YouTube URL is required.")

    normalized_url = url.strip()
    parsed_url = urlparse(normalized_url)

    if parsed_url.scheme.lower() not in {"http", "https"}:
        raise ValueError(
            "YouTube URL must start with http:// or https://."
        )

    hostname = (parsed_url.hostname or "").lower()
    video_id = ""

    if hostname in SHORT_YOUTUBE_HOSTS:
        path_parts = parsed_url.path.strip("/").split("/")

        if path_parts and path_parts[0]:
            video_id = path_parts[0]

    elif hostname in SUPPORTED_YOUTUBE_HOSTS:
        normalized_path = parsed_url.path.rstrip("/")

        if normalized_path == "/watch":
            video_id = parse_qs(parsed_url.query).get("v", [""])[0]

        elif normalized_path.startswith(
            ("/shorts/", "/embed/", "/live/")
        ):
            path_parts = normalized_path.strip("/").split("/")

            if len(path_parts) >= 2:
                video_id = path_parts[1]

    if not VIDEO_ID_PATTERN.fullmatch(video_id):
        raise ValueError("Invalid or unsupported YouTube URL.")

    return video_id