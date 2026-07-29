# compare

Compares already-known sources, tools, papers, products, or options using explicit criteria.

Use this tool when the user asks to compare options that are already in context, such as "compare these sources", "which tool is better", or "rank these papers". It does not fetch new information. If the options are not known yet, use retrieval tools first.

Arguments:
- `items`: list of objects. Useful fields include `name`, `title`, `url`, `source`, `summary`, `notes`, or criterion-specific fields.
- `criteria`: list of criteria to compare by. Defaults to relevance, authority, freshness, and detail.
- `question`: optional user question that frames the comparison.

Returns:
- ranked items;
- simple scores;
- reasons for each rank;
- a winner when at least one item is provided.
