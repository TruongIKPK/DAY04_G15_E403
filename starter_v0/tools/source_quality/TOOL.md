# source_quality

Scores already retrieved sources or explicit URL items for citation usefulness.

Use this tool when the user asks which sources are reliable, strongest, best to cite, or worth including in a research digest. It does not fetch new pages and should normally run after `lookup`, `fetch`, `papers`, or `social_search`.

Arguments:
- `items`: list of objects with `title`, `url`, `source`, `summary`, and optional `published`.
- `question`: optional research question used for relevance scoring.
- `top_k`: number of strongest sources to return.

Returns:
- ranked items with score and short reasons.
