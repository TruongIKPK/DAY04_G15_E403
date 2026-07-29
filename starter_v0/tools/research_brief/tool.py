from __future__ import annotations

from typing import Any


def build_research_brief(
    topic: str = "",
    audience: str = "class demo",
    focus: str = "news and evidence",
    max_questions: int = 5,
) -> dict[str, Any]:
    clean_topic = topic.strip() or "the requested topic"
    clean_audience = audience.strip() or "class demo"
    clean_focus = focus.strip() or "news and evidence"
    count = max(1, min(int(max_questions or 5), 8))

    base_questions = [
        f"What changed recently about {clean_topic}?",
        f"Which sources are strongest for {clean_topic}?",
        f"What claims about {clean_topic} need verification?",
        f"What are the risks, tradeoffs, or open questions around {clean_topic}?",
        f"What concise takeaway should be shown to {clean_audience}?",
        f"Which social reactions are useful signal rather than noise for {clean_topic}?",
        f"What follow-up URL or paper should be read next for {clean_topic}?",
        f"What evidence would change the current conclusion about {clean_topic}?",
    ]

    return {
        "tool": "research_brief",
        "topic": clean_topic,
        "audience": clean_audience,
        "focus": clean_focus,
        "questions": base_questions[:count],
        "suggested_tool_order": ["lookup", "fetch", "source_quality", "format"],
        "deliverable": f"A concise {clean_focus} brief about {clean_topic} for {clean_audience}.",
    }
