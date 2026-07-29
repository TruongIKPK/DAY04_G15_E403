---
name: summarize
track: core
kind: local_formatter
requires_env: []
inputs: [text, items, max_sentences, focus, language]
outputs: [summary, bullets, key_points, item_count, sentence_count, chars_in]
side_effect: false
---
# summarize

Summarizes text that the Agent already has. It does not fetch new data and does
not call an external LLM.

Use this tool when the user asks for a concise summary, key points, TL;DR, or a
short synthesis of content returned by other tools such as `lookup`, `fetch`,
`papers`, or `paper_text`.

Inputs:

- `text`: raw text to summarize.
- `items`: optional list of collected items with `title`, `summary`, `url`, and
  `source` fields.
- `max_sentences`: maximum number of bullet points to return, from 1 to 12.
- `focus`: optional topic or question to prioritize while summarizing.
- `language`: optional language hint. The implementation is extractive and keeps
  the original language of the input.

Output:

- `summary`: markdown bullet list.
- `bullets` / `key_points`: selected summary sentences as plain strings.
- `item_count`, `sentence_count`, `chars_in`: metadata for Agent reasoning.
