from __future__ import annotations

import re
from typing import Any

from tools._shared import domain, terms


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?。！？])\s+|\n+", text)
    return [_clean_text(chunk) for chunk in chunks if _clean_text(chunk)]


def _item_text(item: dict[str, Any]) -> str:
    parts = [item.get("title", ""), item.get("summary", "")]
    return ". ".join(_clean_text(str(part)) for part in parts if _clean_text(str(part)))


def _source(item: dict[str, Any]) -> str:
    src = item.get("source") or domain(item.get("url", ""))
    url = item.get("url") or ""
    return f"[{src}]({url})" if src and url else (src or url)


def _rank_sentences(sentences: list[str], focus: str, limit: int) -> list[str]:
    if not sentences:
        return []

    corpus_terms: dict[str, int] = {}
    for sentence in sentences:
        for term in terms(sentence):
            corpus_terms[term] = corpus_terms.get(term, 0) + 1

    focus_terms = terms(focus)
    scored: list[tuple[float, int, str]] = []
    for index, sentence in enumerate(sentences):
        sentence_terms = terms(sentence)
        if not sentence_terms:
            score = 0.0
        else:
            score = sum(corpus_terms.get(term, 0) for term in sentence_terms) / len(sentence_terms)
            score += 2.0 * len(sentence_terms & focus_terms)
            if 60 <= len(sentence) <= 260:
                score += 0.5
        scored.append((score, index, sentence))

    selected = sorted(scored, key=lambda row: (-row[0], row[1]))[:limit]
    return [sentence for _, _, sentence in sorted(selected, key=lambda row: row[1])]


def summarize(
    text: str = "",
    items: list[dict[str, Any]] | None = None,
    max_sentences: int = 5,
    focus: str = "",
    language: str = "auto",
) -> dict[str, Any]:
    items = items or []
    max_sentences = max(1, min(int(max_sentences or 5), 12))

    if items:
        sentences: list[str] = []
        for item in items:
            item_sentences = _split_sentences(_item_text(item))
            if not item_sentences:
                continue
            source = _source(item)
            first = item_sentences[0]
            sentences.append(f"{first} - {source}" if source else first)
            sentences.extend(item_sentences[1:3])
    else:
        sentences = _split_sentences(text)

    selected = _rank_sentences(sentences, focus=focus, limit=max_sentences)
    bullets = [f"- {sentence}" for sentence in selected]
    summary = "\n".join(bullets)

    return {
        "tool": "summarize",
        "summary": summary,
        "bullets": selected,
        "key_points": selected,
        "item_count": len(items),
        "sentence_count": len(sentences),
        "chars_in": len(text) + sum(len(_item_text(item)) for item in items),
        "language": language,
        "focus": focus,
    }
