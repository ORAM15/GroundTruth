"""Deterministic provider doubles for evaluation ONLY.

These classes exist so the GT-5 golden evaluation can run end-to-end with
no API key and produce reproducible numbers. They are evaluation doubles,
exactly like the fakes in the test suites:

* :class:`BagOfWordsEmbeddingProvider` is a lexical bag-of-words embedding
  (stopword-filtered, with a naive plural stemmer). It is NOT a semantic
  embedding: it measures whether the pipeline's gate, ranking and wiring
  behave correctly when similarity is driven by shared vocabulary. It says
  nothing about how Gemini embeddings will score the same texts.
* :class:`TopEvidenceGenerationProvider` is a *scripted compliant model*:
  it answers by quoting the top-ranked evidence block from the prompt and
  citing it, which is the behaviour the production prompt asks a real
  model for. It never refuses on content grounds and never paraphrases, so
  "answered" in an evaluation run means "the retrieval gate passed and the
  returned citations verified" — not "a real model judged this answerable".

Neither class is referenced by the API application or any production code
path; the harness injects them through the same FastAPI dependency
overrides the tests use. Production runs use the Gemini providers.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

_TOKEN = re.compile(r"[a-z0-9]+")

STOPWORDS = frozenset(
    {
        "a", "about", "after", "all", "am", "an", "and", "any", "are", "as",
        "at", "be", "been", "before", "being", "by", "did", "do", "does",
        "during", "each", "every", "for", "from", "had", "has", "have", "he",
        "her", "here", "him", "his", "how", "i", "if", "in", "into", "is",
        "it", "its", "me", "my", "no", "not", "of", "on", "or", "our", "over",
        "per", "she", "so", "than", "that", "the", "their", "them", "then",
        "there", "these", "they", "this", "those", "to", "under", "us", "was",
        "we", "were", "what", "when", "where", "which", "who", "whom", "with",
        "you", "your",
    }
)


def tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokens, stopwords removed, with a naive
    plural stem (trailing ``s`` stripped for tokens longer than 3 chars
    that do not end in ``ss``) applied consistently to every text."""
    tokens = []
    for token in _TOKEN.findall(text.lower()):
        if token in STOPWORDS:
            continue
        if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
            token = token[:-1]
        tokens.append(token)
    return tokens


class BagOfWordsEmbeddingProvider:
    """Bag-of-words vectors over a fixed vocabulary built from the corpus
    and the case questions, so cosine similarity is fully deterministic
    and driven only by shared content words."""

    provider_name = "evaluation-double"
    model_name = "bow-eval-v1"

    def __init__(self, vocabulary_texts: Sequence[str]) -> None:
        vocabulary: set[str] = set()
        for text in vocabulary_texts:
            vocabulary.update(tokenize(text))
        self._vocabulary = sorted(vocabulary)

    @property
    def vocabulary(self) -> list[str]:
        return list(self._vocabulary)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            counts: dict[str, float] = {}
            for token in tokenize(text):
                counts[token] = counts.get(token, 0.0) + 1.0
            vectors.append([counts.get(word, 0.0) for word in self._vocabulary])
        return vectors


_EVIDENCE_BLOCK = re.compile(r'<evidence id="([^"]+)">\n(.*?)\n</evidence>', re.DOTALL)


class TopEvidenceGenerationProvider:
    """Scripted compliant-model double: answers by quoting the top-ranked
    evidence block in the prompt and citing its chunk id — the behaviour
    the production prompt instructs a real model to follow."""

    provider_name = "evaluation-double"
    model_name = "scripted-top-evidence-v1"

    def __init__(self) -> None:
        self.calls = 0
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.calls += 1
        self.prompts.append(prompt)
        match = _EVIDENCE_BLOCK.search(prompt)
        if match is None:
            return "The evidence does not answer the question."
        chunk_id, text = match.group(1), match.group(2).strip()
        return f"Based on the evidence: {text} [{chunk_id}]"
