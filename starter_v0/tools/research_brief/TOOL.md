# research_brief

Builds a lightweight research plan before retrieval.

Use this tool when the user asks for a research plan, briefing outline, demo plan, or what questions should guide a digest. It does not call external APIs and does not replace evidence-gathering tools such as `lookup`, `fetch`, `papers`, or `social_search`.

Arguments:
- `topic`: the topic to investigate.
- `audience`: who the brief is for.
- `focus`: the kind of evidence or output needed.
- `max_questions`: number of guiding questions to generate.

Returns:
- guiding research questions;
- suggested tool order;
- intended deliverable.
