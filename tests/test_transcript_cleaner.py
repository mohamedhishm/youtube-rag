import pytest

from transcript.cleaner import clean_text


def test_empty_text_returns_empty_string():
    assert clean_text("") == ""


def test_removes_leading_trailing_and_repeated_spaces():
    original = "   RAG    combines   retrieval   and generation.   "

    assert clean_text(original) == (
        "RAG combines retrieval and generation."
    )


def test_replaces_newlines_and_tabs_with_spaces():
    original = (
        "Retrieval\nAugmented\tGeneration\r\n"
        "combines retrieval with generation."
    )

    assert clean_text(original) == (
        "Retrieval Augmented Generation "
        "combines retrieval with generation."
    )


def test_decodes_html_entities():
    original = "RAG uses retrieval &amp; generation."

    assert clean_text(original) == (
        "RAG uses retrieval & generation."
    )


def test_removes_html_formatting_tags():
    original = "<i>RAG</i> uses <b>semantic search</b>."

    assert clean_text(original) == (
        "RAG uses semantic search."
    )


def test_preserves_mixed_arabic_english_text():
    original = (
        "  النهاردة هنتكلم عن\n"
        "Retrieval   Augmented Generation والـ ChromaDB  "
    )

    assert clean_text(original) == (
        "النهاردة هنتكلم عن "
        "Retrieval Augmented Generation والـ ChromaDB"
    )


def test_preserves_arabic_characters_and_diacritics():
    original = "مُقَدِّمَة عن الذكاء الاصطناعي"

    assert clean_text(original) == (
        "مُقَدِّمَة عن الذكاء الاصطناعي"
    )


def test_preserves_numbers_and_punctuation():
    original = "Top-K = 5, similarity: 0.87!"

    assert clean_text(original) == (
        "Top-K = 5, similarity: 0.87!"
    )


@pytest.mark.parametrize(
    "noise_marker",
    [
        "[Music]",
        "[music]",
        "[ MUSIC ]",
        "[Applause]",
        "[Laughter]",
        "[Silence]",
        "[Noise]",
        "[Cheering]",
    ],
)
def test_removes_standalone_noise_markers(noise_marker):
    assert clean_text(noise_marker) == ""


def test_does_not_remove_noise_marker_when_text_is_also_present():
    original = "[Music] Welcome to the RAG course"

    assert clean_text(original) == original


def test_preserves_arabic_caption_description():
    original = "[موسيقى] مقدمة الفيديو"

    assert clean_text(original) == original


@pytest.mark.parametrize(
    "invalid_text",
    [
        None,
        123,
        [],
        {},
    ],
)
def test_rejects_non_string_values(invalid_text):
    with pytest.raises(
        TypeError,
        match="Transcript text must be a string",
    ):
        clean_text(invalid_text)