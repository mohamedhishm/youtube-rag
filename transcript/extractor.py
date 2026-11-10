from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from youtube_transcript_api import YouTubeTranscriptApi

from transcript.cleaner import clean_text
from transcript.models import TranscriptSegment


DEFAULT_LANGUAGES = ["ar", "en"]


class UnsupportedTranscriptLanguageError(Exception):
    """
    Raised when the video has transcript tracks, but none match
    the requested languages.
    """

    def __init__(
        self,
        requested_languages: list[str],
        available_languages: list[str],
    ) -> None:
        self.requested_languages = requested_languages
        self.available_languages = available_languages

        message = (
            "None of the requested transcript languages are available. "
            f"Requested: {requested_languages}. "
            f"Available: {available_languages}."
        )

        super().__init__(message)


class EmptyTranscriptError(Exception):
    """
    Raised when a transcript is fetched but has no usable text.
    """


def normalize_language_code(language_code: str) -> str:
    """
    Normalize a language code for comparison.

    Examples:
        ar    -> ar
        AR    -> ar
        en-US -> en-us
        en_US -> en-us
    """

    return language_code.strip().lower().replace("_", "-")


def language_matches(
    available_language: str,
    requested_language: str,
) -> bool:
    """
    Check whether an available transcript language matches a request.

    Exact codes match:
        en-US matches en-US

    A base-language request also accepts a regional variant:
        en matches en-US
        ar matches ar-EG

    A regional request does not silently accept every variant:
        en-GB does not automatically match en-US
    """

    available = normalize_language_code(available_language)
    requested = normalize_language_code(requested_language)

    if available == requested:
        return True

    if "-" not in requested:
        return available.split("-", maxsplit=1)[0] == requested

    return False


def validate_preferred_languages(
    preferred_languages: list[str] | None,
) -> list[str]:
    """
    Validate and normalize the requested language priority list.
    """

    if preferred_languages is None:
        return DEFAULT_LANGUAGES.copy()

    if not isinstance(preferred_languages, list):
        raise TypeError(
            "preferred_languages must be a list of language codes."
        )

    if not preferred_languages:
        raise ValueError(
            "preferred_languages cannot be empty."
        )

    normalized_languages: list[str] = []

    for language_code in preferred_languages:
        if (
            not isinstance(language_code, str)
            or not language_code.strip()
        ):
            raise ValueError(
                "Every preferred language must be a non-empty string."
            )

        normalized_code = normalize_language_code(language_code)

        if normalized_code not in normalized_languages:
            normalized_languages.append(normalized_code)

    return normalized_languages


def get_available_language_codes(
    transcripts: Iterable[Any],
) -> list[str]:
    """
    Return unique available transcript language codes.
    """

    language_codes = {
        normalize_language_code(transcript.language_code)
        for transcript in transcripts
    }

    return sorted(language_codes)


def select_transcript(
    transcripts: Iterable[Any],
    preferred_languages: list[str] | None = None,
) -> Any:
    """
    Select one transcript using a predictable policy.

    Priority:
    1. Order of preferred_languages.
    2. Manually created transcript.
    3. Automatically generated transcript.

    For ["ar", "en"], the order is:
    - Arabic manual
    - Arabic generated
    - English manual
    - English generated
    """

    languages = validate_preferred_languages(
        preferred_languages
    )

    available_transcripts = list(transcripts)

    if not available_transcripts:
        raise EmptyTranscriptError(
            "No transcript tracks are available for this video."
        )

    for requested_language in languages:
        matching_transcripts = [
            transcript
            for transcript in available_transcripts
            if language_matches(
                transcript.language_code,
                requested_language,
            )
        ]

        manual_transcripts = [
            transcript
            for transcript in matching_transcripts
            if not transcript.is_generated
        ]

        if manual_transcripts:
            return manual_transcripts[0]

        generated_transcripts = [
            transcript
            for transcript in matching_transcripts
            if transcript.is_generated
        ]

        if generated_transcripts:
            return generated_transcripts[0]

    available_languages = get_available_language_codes(
        available_transcripts
    )

    raise UnsupportedTranscriptLanguageError(
        requested_languages=languages,
        available_languages=available_languages,
    )


def convert_fetched_transcript(
    fetched_transcript: Iterable[Any],
) -> list[TranscriptSegment]:
    """
    Convert fetched YouTube snippets into internal transcript segments.

    Noise-only or empty snippets are ignored. Arabic-English mixed text
    is preserved by clean_text().
    """

    segments: list[TranscriptSegment] = []

    for snippet in fetched_transcript:
        text = clean_text(snippet.text)

        if not text:
            continue

        start_seconds = float(snippet.start)
        duration_seconds = float(snippet.duration)

        if start_seconds < 0:
            raise ValueError(
                "YouTube returned a negative transcript start time."
            )

        if duration_seconds < 0:
            raise ValueError(
                "YouTube returned a negative transcript duration."
            )

        end_seconds = start_seconds + duration_seconds

        segments.append(
            TranscriptSegment(
                text=text,
                start_seconds=round(start_seconds, 3),
                end_seconds=round(end_seconds, 3),
            )
        )

    if not segments:
        raise EmptyTranscriptError(
            "The transcript was retrieved but contained no usable text."
        )

    return segments


def fetch_transcript(
    video_id: str,
    preferred_languages: list[str] | None = None,
) -> tuple[list[TranscriptSegment], str, bool]:
    """
    Retrieve and convert one selected transcript track.

    Returns:
        A tuple containing:
        - timestamped transcript segments
        - selected transcript language code
        - whether the selected transcript is auto-generated
    """

    if not isinstance(video_id, str) or not video_id.strip():
        raise ValueError(
            "video_id must be a non-empty string."
        )

    languages = validate_preferred_languages(
        preferred_languages
    )

    api = YouTubeTranscriptApi()
    transcript_list = api.list(video_id.strip())

    selected_transcript = select_transcript(
        transcripts=transcript_list,
        preferred_languages=languages,
    )

    fetched_transcript = selected_transcript.fetch()

    segments = convert_fetched_transcript(
        fetched_transcript
    )

    return (
        segments,
        normalize_language_code(
            selected_transcript.language_code
        ),
        bool(selected_transcript.is_generated),
    )