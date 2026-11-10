from dataclasses import dataclass

import pytest

from transcript.extractor import (
    EmptyTranscriptError,
    UnsupportedTranscriptLanguageError,
    convert_fetched_transcript,
    language_matches,
    select_transcript,
    validate_preferred_languages,
)


@dataclass
class FakeTranscript:
    language_code: str
    is_generated: bool
    name: str = ""


@dataclass
class FakeSnippet:
    text: str
    start: float
    duration: float


def test_default_languages_are_arabic_then_english():
    assert validate_preferred_languages(None) == [
        "ar",
        "en",
    ]


def test_normalizes_language_codes():
    assert validate_preferred_languages(
        ["AR", "en_US"]
    ) == ["ar", "en-us"]


def test_removes_duplicate_languages():
    assert validate_preferred_languages(
        ["ar", "AR", "en", "en"]
    ) == ["ar", "en"]


def test_rejects_empty_language_list():
    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        validate_preferred_languages([])


def test_rejects_invalid_language_value():
    with pytest.raises(
        ValueError,
        match="non-empty string",
    ):
        validate_preferred_languages(
            ["ar", ""]
        )


@pytest.mark.parametrize(
    ("available", "requested", "expected"),
    [
        ("ar", "ar", True),
        ("AR", "ar", True),
        ("ar-EG", "ar", True),
        ("en-US", "en", True),
        ("en_US", "en", True),
        ("en-US", "en-US", True),
        ("en-US", "en-GB", False),
        ("ar", "en", False),
    ],
)
def test_language_matching(
    available,
    requested,
    expected,
):
    assert language_matches(
        available,
        requested,
    ) is expected


def test_prefers_arabic_generated_over_english_manual():
    transcripts = [
        FakeTranscript(
            language_code="en",
            is_generated=False,
            name="English manual",
        ),
        FakeTranscript(
            language_code="ar",
            is_generated=True,
            name="Arabic generated",
        ),
    ]

    selected = select_transcript(
        transcripts=transcripts,
        preferred_languages=["ar", "en"],
    )

    assert selected.name == "Arabic generated"
    assert selected.language_code == "ar"
    assert selected.is_generated is True


def test_prefers_manual_within_same_language():
    transcripts = [
        FakeTranscript(
            language_code="ar",
            is_generated=True,
            name="Arabic generated",
        ),
        FakeTranscript(
            language_code="ar",
            is_generated=False,
            name="Arabic manual",
        ),
    ]

    selected = select_transcript(
        transcripts=transcripts,
        preferred_languages=["ar", "en"],
    )

    assert selected.name == "Arabic manual"
    assert selected.is_generated is False


def test_uses_english_when_arabic_is_unavailable():
    transcripts = [
        FakeTranscript(
            language_code="en",
            is_generated=True,
            name="English generated",
        )
    ]

    selected = select_transcript(
        transcripts=transcripts,
        preferred_languages=["ar", "en"],
    )

    assert selected.language_code == "en"


def test_base_language_accepts_regional_variant():
    transcripts = [
        FakeTranscript(
            language_code="ar-EG",
            is_generated=False,
            name="Egyptian Arabic manual",
        )
    ]

    selected = select_transcript(
        transcripts=transcripts,
        preferred_languages=["ar", "en"],
    )

    assert selected.language_code == "ar-EG"


def test_raises_error_when_language_is_unsupported():
    transcripts = [
        FakeTranscript(
            language_code="fr",
            is_generated=False,
        ),
        FakeTranscript(
            language_code="de",
            is_generated=True,
        ),
    ]

    with pytest.raises(
        UnsupportedTranscriptLanguageError,
    ) as error_info:
        select_transcript(
            transcripts=transcripts,
            preferred_languages=["ar", "en"],
        )

    error = error_info.value

    assert error.requested_languages == [
        "ar",
        "en",
    ]

    assert error.available_languages == [
        "de",
        "fr",
    ]


def test_raises_error_when_no_tracks_are_available():
    with pytest.raises(
        EmptyTranscriptError,
        match="No transcript tracks",
    ):
        select_transcript(
            transcripts=[],
            preferred_languages=["ar", "en"],
        )


def test_converts_snippets_to_timestamped_segments():
    snippets = [
        FakeSnippet(
            text="Welcome to the course",
            start=2.5,
            duration=4.0,
        ),
        FakeSnippet(
            text="Today we learn RAG",
            start=6.5,
            duration=5.25,
        ),
    ]

    segments = convert_fetched_transcript(snippets)

    assert len(segments) == 2

    assert segments[0].text == (
        "Welcome to the course"
    )
    assert segments[0].start_seconds == 2.5
    assert segments[0].end_seconds == 6.5

    assert segments[1].start_seconds == 6.5
    assert segments[1].end_seconds == 11.75


def test_conversion_preserves_mixed_language_text():
    snippets = [
        FakeSnippet(
            text=(
                "النهاردة هنتكلم عن\n"
                "Retrieval   Augmented Generation"
            ),
            start=0.0,
            duration=7.5,
        )
    ]

    segments = convert_fetched_transcript(snippets)

    assert segments[0].text == (
        "النهاردة هنتكلم عن "
        "Retrieval Augmented Generation"
    )

    assert segments[0].start_seconds == 0.0
    assert segments[0].end_seconds == 7.5


def test_conversion_ignores_noise_only_snippets():
    snippets = [
        FakeSnippet(
            text="[Music]",
            start=0.0,
            duration=3.0,
        ),
        FakeSnippet(
            text="Welcome to the video",
            start=3.0,
            duration=4.0,
        ),
    ]

    segments = convert_fetched_transcript(snippets)

    assert len(segments) == 1
    assert segments[0].text == (
        "Welcome to the video"
    )
    assert segments[0].start_seconds == 3.0
    assert segments[0].end_seconds == 7.0


def test_raises_error_when_all_snippets_are_noise():
    snippets = [
        FakeSnippet(
            text="[Music]",
            start=0.0,
            duration=3.0,
        ),
        FakeSnippet(
            text="   ",
            start=3.0,
            duration=2.0,
        ),
    ]

    with pytest.raises(
        EmptyTranscriptError,
        match="no usable text",
    ):
        convert_fetched_transcript(snippets)


def test_rejects_negative_start_time():
    snippets = [
        FakeSnippet(
            text="Invalid snippet",
            start=-1.0,
            duration=3.0,
        )
    ]

    with pytest.raises(
        ValueError,
        match="negative transcript start",
    ):
        convert_fetched_transcript(snippets)


def test_rejects_negative_duration():
    snippets = [
        FakeSnippet(
            text="Invalid snippet",
            start=5.0,
            duration=-2.0,
        )
    ]

    with pytest.raises(
        ValueError,
        match="negative transcript duration",
    ):
        convert_fetched_transcript(snippets)