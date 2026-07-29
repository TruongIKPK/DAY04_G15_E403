# Day 04 Lab v2 Report - Research Agent

## Team

- Team: G15 E403
- Members: Tran Duy Truong, Nguyen Khanh Toan, Ho Van Thi, Bui Dang Quoc An, Nguyen Quang Huy, Le Nguyen Phi Truong
- Provider/model: OpenRouter `openai/gpt-4o-mini` recommended. Tool smoke tests use Tavily, Firecrawl, and RapidAPI keys from runtime env.

# PHAN A - Gioi thieu agent

## A1. Agent nay lam duoc gi

Research Agent helps collect and triage evidence from web search, social posts, specific URLs, internal policy docs, and scholarly papers. It can ask for missing information, enforce confirmation before sending to Telegram, format retrieved items, and rank citation-quality sources.

Two updated support tools improve the final research output:

- Summarization / `format`: turns retrieved items into a readable digest, bullet list, sectioned report, social thread, or Vietnamese daily AI brief. It should be used after retrieval tools such as `lookup`, `fetch`, or `social_search`, because its input is the already collected `items`.
- `compare`: compares already-known sources, tools, papers, products, or options by criteria. It should be used when the user asks to compare, rank, choose, or decide which option is better, and the options are already available in context.

Link dung thu:

- Local UI: `streamlit run app.py` from `starter_v0`, then open `http://localhost:8501`.
- Public tunnel can be added with Cloudflare Tunnel during demo if another team needs remote access.

## A2. Tool agent co

| Tool | Lam duoc gi | Tool moi nhom them? |
|---|---|---|
| clarify | Ask for missing info or yes/no confirmation before sensitive actions | No |
| compare | Compare or rank already-known options by criteria such as relevance, authority, freshness, and detail | Yes |
| timeline | Get recent posts from a specific account/handle | No |
| social_search | Search social posts by topic, Latest or Top | No |
| lookup | Search web/general news with timeframe routing | No |
| fetch | Read a specific URL | No |
| format / summarization | Summarize retrieved items into brief, sections, bullets, thread, or `daily_ai_vn` digest | No |
| source_quality | Rank retrieved sources for citation usefulness | Yes |
| research_brief | Build a research plan or briefing outline before retrieval | Yes |
| policy | Search internal company policy markdown | No |
| papers | Search scholarly papers | No |
| paper_text | Extract text from arXiv paper ID/URL | No |
| send | Send text to Telegram after confirmation | No |

## A3. Cau hoi mau de thu

1. `Tin AI hom nay tren web co gi noi bat?`
2. `Lay 5 tweet moi nhat cua Sam Altman`
3. `Moi nguoi dang noi gi ve GPT-5 tren Twitter, lay cac bai top`
4. `Doc va tom tat URL nay: https://openai.com/research/`
5. `Trong cac source da co, chon nguon dang tin nhat de cite ve AI agent evaluation`
6. `So sanh cac nguon nay theo authority, freshness va detail`

## A4. Kich ban demo da rehearse

| Scenario | Tool trace can thay | Cai thien version | Fallback |
|---|---|---|---|
| Daily AI news | `lookup(query=AI, topic=news, timeframe=day)` | Prompt maps "hom nay" to `day` | `runs/*base*.json` after provider run |
| Specific article summary | `fetch(url=...)` | Tool description says URL means fetch, not lookup | UI transcript |
| Missing tweet account | `clarify(response_type=text)` | Guardrail prevents guessing a famous account | Group eval G03 |
| Send boundary | `clarify(response_type=yes_no)` | Prompt forbids `send` before confirmation | Base eval R12 / group G05 |
| Citation ranking | `source_quality(items=..., question=...)` | Team-added tool separates ranking from search | Direct smoke test |
| Summarization output | `format(items=..., template=brief/sections/bullets/thread/daily_ai_vn)` | Summary step is separated from retrieval so the agent does not invent items | UI transcript |
| Comparison output | `compare(items=..., criteria=...)` | Team-added tool ranks known options instead of doing unsupported comparison from memory | Direct smoke test |

# PHAN B - Chi tiet / bang chung

## B1. Version evidence

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | Original starter prompt/tools | Baseline likely over-guesses and sends without confirmation | case_accuracy | pending provider key | pending provider key | pending |
| v1 | Rewrote system prompt with routing and safety rules | Clear boundaries reduce wrong tool and wrong boundary failures | case_accuracy | pending provider key | pending provider key | pending |
| v2 | Rewrote tool declarations with argument conventions | Better schemas/descriptions improve argument accuracy | argument_accuracy | pending provider key | pending provider key | pending |
| v3 | Added `source_quality`, group eval, and UI | Covers mandatory team tool and demo evidence | group_case_accuracy | pending provider key | pending provider key | pending |

## B2. Failure analysis

Provider eval has not been completed in this workspace because no model provider key was provided. Expected high-risk failures from the starter were fixed in artifacts:

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R10/R11 | missing_info | starter would guess | Missing handle/URL should not be guessed | `system_prompt.md` now requires `clarify` |
| R12/G05 | wrong_boundary | starter would send | Telegram send needs confirmation | prompt + `send` declaration require yes/no confirmation |
| R03/R06 | wrong_arg_value | timeframe may be vague | today/week mapping unclear | prompt + `lookup` declaration define timeframe mapping |
| G04 | wrong_tool | no team ranking tool existed | Mandatory new tool missing | added `source_quality` |

## B3. Team eval cases

`data/eval_group.json` contains exactly 10 team-authored phase B cases:

| Case ID | What It Tests | Expected |
|---|---|---|
| G01 | Today AI news with max result limit | `lookup` |
| G02 | Exact URL reading | `fetch` |
| G03 | Missing social account | `clarify` |
| G04 | Source reliability ranking | `source_quality` |
| G05 | Telegram confirmation boundary | `clarify yes_no` |
| GM01 | Multi-turn topic replacement with timeframe carryover | `lookup` |
| GM02 | Multi-turn handle and limit correction | `timeline` |
| GM03 | Multi-turn URL supplied after clarification | `fetch` |
| GM04 | Multi-turn social Top sorting | `social_search` |
| GM05 | Multi-turn internal citation policy | `policy` |

## B4. Live chat evidence

UI transcript files are saved to `transcripts/*.transcript.json` after each Streamlit turn. CLI transcripts are saved by `python chat.py --provider openrouter --version v3` when a provider key is available.

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: team tool | `tools/source_quality/tool.py`, `tools/source_quality/TOOL.md` | Local ranking of candidate sources | Does not fetch pages; must use retrieved/provided items |
| Team tool: compare | `tools/compare/tool.py`, `tools/compare/TOOL.md`, `artifacts/tools.yaml` | Compares already-known options with `items`, `criteria`, and optional `question`; returns ranked items, scores, reasons, and winner | Does not fetch new evidence; if options are missing, retrieval should happen first |
| Summarization tool | `tools/format/tool.py`, `tools/format/TOOL.md`, `artifacts/tools.yaml` | Converts retrieved `items` into `brief`, `sections`, `bullets`, `thread`, or `daily_ai_vn` markdown output with optional `headline` | Should run after retrieval; empty or low-quality input items produce weak summaries |
| Extra team tool | `tools/research_brief/tool.py`, `tools/research_brief/TOOL.md` | Builds research questions and a suggested tool order | Planning only; evidence still needs retrieval |
| Core tools | `tools/lookup`, `tools/fetch`, `tools/timeline`, `tools/social_search` | API-backed retrieval when env keys are present | API quota/network errors are surfaced in tool results |
| UI | `app.py` | Displays request, response, artifact version, and tool trace | Does not display secrets |

### B5.1 Summarization (`format`)

The summarization capability is implemented through the `format` tool declaration in `artifacts/tools.yaml`. It accepts an `items` array where each item can contain `title`, `url`, `source`, `summary`, and `section`. The `template` argument controls the output shape:

- `brief`: short digest with a headline and up to five compact bullets.
- `sections`: grouped markdown report by section.
- `bullets`: direct bullet list for all retrieved items.
- `thread`: numbered social-thread style output.
- `daily_ai_vn`: Vietnamese daily AI news digest grouped by section.

This tool should not be used as the first retrieval step. The expected flow is retrieval first, for example `lookup` or `fetch`, then `format` to summarize the returned items.

### B5.2 Compare (`compare`)

The `compare` tool compares already-known options from context. Its required input is `items`; each item can include fields such as `name`, `title`, `url`, `source`, `summary`, or `notes`. The optional `criteria` array defaults to `relevance`, `authority`, `freshness`, and `detail`, and the optional `question` frames the comparison.

The output includes ranked items, simple scores, reasons for each ranking, and a `winner` when at least one item is available. The guardrail is that `compare` does not fetch new information; if the user asks to compare sources that have not been collected yet, the agent should retrieve them first and only then call `compare`.

## B6. Reflection

- `system_prompt.md` fixes behavior: when to clarify, when not to use tools, send confirmation, multi-turn carryover.
- `tools.yaml` fixes interface clarity: tool names, descriptions, schemas, argument defaults, and routing hints.
- Provider errors and API tool errors need manual review because routing can pass even when external data retrieval fails.
- Next improvement: run v0-v3 with a real provider key, parse run logs into CSV, then replace pending metrics with measured results.