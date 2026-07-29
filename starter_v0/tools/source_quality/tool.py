from __future__ import annotations

from typing import Any

from tools._shared import domain, terms


AUTHORITY_WEIGHTS = {
    "openai.com": 3,
    "anthropic.com": 3,
    "deepmind.google": 3,
    "googleblog.com": 2,
    "microsoft.com": 2,
    "arxiv.org": 3,
    "nature.com": 3,
    "science.org": 3,
    "acm.org": 2,
    "ieee.org": 2,
    "gov": 2,
    "edu": 2,
}


def _authority_score(source_domain: str) -> int:
    for marker, weight in AUTHORITY_WEIGHTS.items():
        if marker in source_domain:
            return weight
    if source_domain:
        return 1
    return 0


def score_sources(
    items: list[dict[str, Any]] | None = None,
    question: str = "",
    top_k: int = 3,
) -> dict[str, Any]:
    items = items or []
    query_terms = terms(question)
    scored: list[dict[str, Any]] = []

    for item in items:
        url = item.get("url") or ""
        source_domain = item.get("source") or domain(url)
        text = " ".join(str(item.get(key, "")) for key in ("title", "summary", "source", "url"))
        item_terms = terms(text)
        overlap = len(query_terms & item_terms) if query_terms else 0
        authority = _authority_score(source_domain)
        has_summary = 1 if item.get("summary") else 0
        has_date = 1 if item.get("published") or item.get("date") else 0
        score = authority * 3 + overlap * 2 + has_summary + has_date
        reasons = []
        if authority >= 2:
            reasons.append("authoritative domain")
        elif authority == 1:
            reasons.append("identifiable source")
        if overlap:
            reasons.append(f"{overlap} query term match(es)")
        if has_summary:
            reasons.append("has extractable summary")
        if has_date:
            reasons.append("has freshness signal")
        scored.append({
            "title": item.get("title") or url or "Untitled source",
            "url": url,
            "source": source_domain,
            "score": score,
            "reasons": reasons or ["limited citation evidence"],
        })

    scored.sort(key=lambda item: item["score"], reverse=True)
    return {
        "tool": "source_quality",
        "question": question,
        "item_count": len(items),
        "top_k": int(top_k or 3),
        "items": scored[: int(top_k or 3)],
    }
