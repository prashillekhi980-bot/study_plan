"""Note summariser (app/notes/summarizer.py): offline extractive
summary, and the consent-gated OpenAI upgrade path. The OpenAI call
itself is monkeypatched so this suite never makes a real network call
or needs a real API key.
"""
import app.notes.summarizer as summarizer_module
from app.notes.summarizer import extractive_summarize, summarize


SHORT_TEXT = "Joins combine rows. Inner joins need a match. Outer joins keep unmatched rows."

LONG_TEXT = (
    "Database indexes speed up lookups by avoiding full table scans. "
    "A primary key index is created automatically on most databases. "
    "Composite indexes cover multiple columns and help multi-column filters. "
    "Indexes slow down writes because every insert must update the index too. "
    "Choosing the right columns to index requires knowing the query patterns. "
    "Over-indexing wastes disk space and can hurt write performance significantly."
)


def test_extractive_summarize_returns_short_text_unchanged():
    assert extractive_summarize(SHORT_TEXT, max_sentences=3) == SHORT_TEXT.strip()


def test_extractive_summarize_truncates_long_text():
    result = extractive_summarize(LONG_TEXT, max_sentences=3)
    assert result != LONG_TEXT
    # Should keep only 3 of the 6 sentences (split on '. ').
    assert result.count(".") <= 3


def test_extractive_summarize_handles_empty_text():
    assert extractive_summarize("", max_sentences=3) == ""


def test_summarize_defaults_to_offline_with_no_api_key():
    summary, method = summarize(SHORT_TEXT, api_key=None, consent=True)
    assert method == "offline"
    assert summary == SHORT_TEXT.strip()


def test_summarize_stays_offline_without_consent_even_with_key():
    summary, method = summarize(SHORT_TEXT, api_key="fake-key-123", consent=False)
    assert method == "offline"


def test_summarize_uses_openai_only_with_key_and_consent(monkeypatch):
    monkeypatch.setattr(
        summarizer_module, "openai_summarize",
        lambda text, api_key: "AI-generated summary."
    )
    summary, method = summarize(SHORT_TEXT, api_key="fake-key-123", consent=True)
    assert method == "openai"
    assert summary == "AI-generated summary."


def test_summarize_falls_back_to_offline_if_openai_call_fails(monkeypatch):
    monkeypatch.setattr(
        summarizer_module, "openai_summarize",
        lambda text, api_key: None  # simulates a bad key / network error
    )
    summary, method = summarize(SHORT_TEXT, api_key="fake-key-123", consent=True)
    assert method == "offline"


def test_openai_summarize_returns_none_on_exception(monkeypatch):
    """The real function must never raise — a bad key or network error
    should degrade to the offline path, not crash the request."""
    import app.notes.summarizer as mod

    class ExplodingClient:
        def __init__(self, api_key):
            raise RuntimeError("network unreachable")

    monkeypatch.setattr(mod, "OpenAI", ExplodingClient, raising=False)
    # Patch the import site used inside the function (it imports locally).
    import sys
    fake_openai_module = type(sys)("openai")
    fake_openai_module.OpenAI = ExplodingClient
    monkeypatch.setitem(sys.modules, "openai", fake_openai_module)

    result = mod.openai_summarize(SHORT_TEXT, api_key="fake-key")
    assert result is None
