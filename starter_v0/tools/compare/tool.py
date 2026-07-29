from __future__ import annotations

from typing import Any


DEFAULT_CRITERIA = ["relevance", "authority", "freshness", "detail"]


def _text_for(item: dict[str, Any]) -> str:
    return " ".join(str(item.get(key, "")) for key in ("name", "title", "source", "url", "summary", "notes"))


def _score_item(item: dict[str, Any], criteria: list[str]) -> tuple[int, list[str]]:
    text = _text_for(item).lower()
    score = 0
    reasons: list[str] = []

    for criterion in criteria:
        key = criterion.strip().lower()
        if not key:
            continue
        if key in item and item[key]:
            score += 2
            reasons.append(f"has {key}")
        elif key in text:
            score += 1
            reasons.append(f"mentions {key}")

    if item.get("url"):
        score += 1
        reasons.append("has URL")
    if item.get("summary") or item.get("notes"):
        score += 1
        reasons.append("has explanation")

    return score, reasons or ["limited evidence"]


def compare(
    items: list[dict[str, Any]] | None = None,
    criteria: list[str] | None = None,
    question: str = "",
) -> dict[str, Any]:
    items = items or []
    criteria = criteria or DEFAULT_CRITERIA

    compared: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        score, reasons = _score_item(item, criteria)
        compared.append({
            "rank": index,
            "name": item.get("name") or item.get("title") or item.get("url") or f"Item {index}",
            "score": score,
            "reasons": reasons,
            "item": item,
        })

    compared.sort(key=lambda row: row["score"], reverse=True)
    for index, row in enumerate(compared, start=1):
        row["rank"] = index

    return {
        "tool": "compare",
        "question": question,
        "criteria": criteria,
        "item_count": len(items),
        "winner": compared[0]["name"] if compared else None,
        "items": compared,
    }
