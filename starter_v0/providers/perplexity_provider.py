from __future__ import annotations

import json
import os
from typing import Any

from providers.base import ModelResponse, ToolCall
from providers.openai_provider import OpenAIProvider


class SearchResult:
    def __init__(self, title: str, url: str, snippet: str = "") -> None:
        self.title = title
        self.url = url
        self.snippet = snippet


class SearchResponse:
    def __init__(self, results: list[SearchResult]) -> None:
        self.results = results


class SearchAPI:
    def __init__(self, client: Perplexity) -> None:
        self.client = client

    def create(self, query: str, model: str | None = None) -> SearchResponse:
        messages = [
            {
                "role": "system",
                "content": "Return search results in JSON format with key 'results': list of objects with 'title', 'url', and 'snippet'.",
            },
            {"role": "user", "content": query},
        ]
        resp = self.client.provider.complete(messages, model=model)
        results: list[SearchResult] = []
        if resp.text:
            try:
                data = json.loads(resp.text)
                if isinstance(data, dict) and "results" in data:
                    for item in data["results"]:
                        results.append(
                            SearchResult(
                                title=item.get("title", ""),
                                url=item.get("url", ""),
                                snippet=item.get("snippet", ""),
                            )
                        )
            except Exception:
                pass
        if not results and resp.text:
            results.append(SearchResult(title=query, url="", snippet=resp.text))
        return SearchResponse(results=results)


class Perplexity:
    """Perplexity Client SDK interface matching standard SDK usage."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if api_key:
            os.environ["PERPLEXITY_API_KEY"] = api_key
        self.provider = PerplexityProvider()
        self.search = SearchAPI(self)


class PerplexityProvider(OpenAIProvider):
    """Perplexity API provider with support for Perplexity models (default: sonar)."""

    def __init__(
        self,
        *,
        api_key_env: str = "PERPLEXITY_API_KEY",
        base_url: str | None = None,
        default_model: str = "openai/gpt-5-mini",
    ) -> None:
        super().__init__(
            api_key_env=api_key_env,
            base_url=base_url or os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai"),
            default_model=os.getenv("MODEL_AI", default_model),
        )

    def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        selected_model = model or self.default_model
        # Map non-Perplexity model names (like openai/gpt-5-mini) to valid Perplexity API model "sonar"
        valid_perplexity_models = {
            "sonar",
            "sonar-pro",
            "sonar-reasoning",
            "sonar-reasoning-pro",
            "sonar-deep-research",
            "llama-3.1-sonar-small-128k-online",
            "llama-3.1-sonar-large-128k-online",
            "llama-3.1-8b-instruct",
            "llama-3.1-70b-instruct",
        }
        is_perplexity_api = "perplexity.ai" in (self.base_url or "")
        if is_perplexity_api and selected_model not in valid_perplexity_models:
            selected_model = "sonar"

        # Perplexity API does not support OpenAI-style tool/function calling parameters
        effective_tools = None if is_perplexity_api else tools
        effective_tool_choice = None if is_perplexity_api else tool_choice

        return super().complete(
            messages,
            effective_tools,
            model=selected_model,
            temperature=temperature,
            tool_choice=effective_tool_choice,
        )

