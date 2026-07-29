from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err


def web_search(query: str = "", topic: str = "general", timeframe: str | None = "week", max_results: int = 5) -> dict[str, Any]:
    try:
        key = os.getenv("TAVILY_API_KEY")
        if not key:
            raise RuntimeError("Missing TAVILY_API_KEY env var")
        
        cleaned_query = (query or "").strip()
        if not cleaned_query:
            cleaned_query = "tin tức mới nhất" if topic == "news" else "tin tức"

        body: dict[str, Any] = {"query": cleaned_query, "topic": topic, "max_results": int(max_results or 5), "search_depth": "basic"}
        if timeframe:
            body["time_range"] = timeframe
        response = requests.post(
            "https://api.tavily.com/search",
            json=body,
            headers={"Authorization": f"Bearer {key}"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        items = [{
            "title": item.get("title"),
            "url": item.get("url"),
            "source": domain(item.get("url", "")),
            "summary": item.get("content"),
            "score": item.get("score"),
        } for item in data.get("results", [])]
        return {"tool": "web_search", "query": cleaned_query, "topic": topic, "timeframe": timeframe, "items": items}
    except Exception as exc:
        return err("web_search", exc)

