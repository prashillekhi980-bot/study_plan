"""Note summariser — the proposal's optional Phase 6 feature: "Summarize
class notes ... using simple NLP or the OpenAI API."

Two tiers, exactly as the proposal frames it ("This feature can start off
with a set of predefined rules"):

1. A simple, offline, rule-based extractive summarizer (word-frequency
   sentence scoring — classic Luhn-style NLP) that always works, needs no
   API key, and sends nothing anywhere. This is the default.
2. If OPENAI_API_KEY is configured AND the student has explicitly
   consented for this specific request, an OpenAI call is used instead
   for a higher-quality summary. Per the proposal's ethics section, this
   is opt-in per request, not a silent default — the core app (including
   this feature's basic form) never depends on the external API.
"""
import re
from collections import Counter

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be",
    "been", "being", "in", "on", "at", "to", "for", "of", "with", "by",
    "from", "as", "it", "its", "this", "that", "these", "those", "i", "we",
    "you", "he", "she", "they", "them", "his", "her", "their", "our", "your",
    "not", "no", "so", "if", "then", "than", "there", "here", "which", "who",
    "what", "when", "where", "why", "how", "will", "would", "can", "could",
    "should", "have", "has", "had", "do", "does", "did", "also", "into",
}


def _split_sentences(text):
    text = text.strip()
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def extractive_summarize(text, max_sentences=3):
    """Offline, rule-based summary: score each sentence by the frequency
    of its (non-stopword) words across the whole text, then return the
    top-scoring sentences in their original order. No external calls."""
    sentences = _split_sentences(text)
    if len(sentences) <= max_sentences:
        return text.strip()

    words = re.findall(r"[a-zA-Z']+", text.lower())
    freqs = Counter(w for w in words if w not in STOPWORDS and len(w) > 2)

    scored = []
    for i, sentence in enumerate(sentences):
        sentence_words = re.findall(r"[a-zA-Z']+", sentence.lower())
        score = sum(freqs.get(w, 0) for w in sentence_words)
        scored.append((score, i, sentence))

    top = sorted(scored, key=lambda x: x[0], reverse=True)[:max_sentences]
    top_in_order = [s for _, _, s in sorted(top, key=lambda x: x[1])]
    return " ".join(top_in_order)


def openai_summarize(text, api_key):
    """Higher-quality summary via the OpenAI API. Only called when the key
    is configured and the student has consented for this request. Returns
    None (falls back to the offline summarizer) on any error, so a bad key
    or network issue never breaks the feature."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Summarize the student's study notes in 2-3 concise sentences."},
                {"role": "user", "content": text},
            ],
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None


def summarize(text, api_key=None, consent=False):
    """Entry point used by routes. Returns (summary_text, method) where
    method is 'openai' or 'offline', so the UI can be transparent about
    which one produced the result."""
    if api_key and consent:
        result = openai_summarize(text, api_key)
        if result:
            return result, "openai"

    return extractive_summarize(text), "offline"
