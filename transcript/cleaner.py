import html
import re


# Remove these only when the entire segment is a caption noise marker.
NOISE_PATTERN = re.compile(
    r"^\[\s*"
    r"(music|applause|laughter|silence|noise|cheering)" #[Music] Welcome to the course Our first version keeps it unchanged rather than risking deletion of useful content:
    r"\s*\]$",
    re.IGNORECASE,
)

# Matches HTML tags such as <i>, </i>, <b>, and <font>.
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")

# Matches repeated whitespace, including spaces, tabs, and new lines.
WHITESPACE_PATTERN = re.compile(r"\s+")

SPACE_BEFORE_PUNCTUATION_PATTERN = re.compile(r"\s+([,.;:!?])") # Matches whitespace before punctuation marks such as commas, periods, semicolons, colons, exclamation marks, and question marks.


def clean_text(text: str) -> str:
    """
    Clean obvious transcript formatting problems without changing meaning.

    The function:
    - Converts HTML entities such as &amp; into their characters.
    - Removes HTML formatting tags.
    - Converts repeated whitespace and new lines into one space.
    - Removes standalone caption noise markers such as [Music].
    - Preserves Arabic, English, numbers, and punctuation.

    Args:
        text: The original text of one transcript segment.

    Returns:
        The conservatively cleaned text.

    Raises:
        TypeError: If text is not a string.
    """

    if not isinstance(text, str):
        raise TypeError("Transcript text must be a string.")

    if not text:
        return ""

    cleaned = html.unescape(text)
    cleaned = HTML_TAG_PATTERN.sub(" ", cleaned)
    cleaned = WHITESPACE_PATTERN.sub(" ", cleaned).strip()
    cleaned = SPACE_BEFORE_PUNCTUATION_PATTERN.sub(r"\1", cleaned)

    if NOISE_PATTERN.fullmatch(cleaned):
        return ""

    return cleaned