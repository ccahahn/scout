# Scout No-Results Bug: Troubleshooting Analysis

## What happened

Maria's scenario — which had passed 50+ consecutive times — returned the no-match message for the first time. Scout's thinking streamed normally. Scout found the right grants. But the results never rendered.

## Timeline

1. We ran `evals.py` with all 12 synthetic users concurrently against the Anthropic API
2. 5 of 12 users hit 429 rate limit errors (8K output tokens/minute ceiling)
3. Immediately after, Maria was run manually in the Streamlit app
4. Maria's run returned the no-match fallback despite Scout finding 3 correct grants

## What the logs show

**Fail run vs. pass run comparison:**

| | Fail run | Pass run |
|---|---------|---------|
| completion_tokens | 4,467 | 4,214 |
| thinking block | 8,071 chars | 7,156 chars |
| text block | 4,272 chars | 3,716 chars |
| Text starts with JSON? | No — narrative preamble | No — narrative preamble |
| JSON found in text? | Yes, at position 2301 | Yes, at position 2115 |
| Grants in JSON | 3 (SYN-001, SYN-002, SYN-003) | 2 (SYN-001, SYN-002) |

Key finding: **both runs have the same format.** Both have narrative text before the JSON. Both have valid JSON with grants embedded in the text. Neither hit a token ceiling.

## Root cause

**Proximate cause:** The `parse_json_output` function searches for JSON by iterating `{` positions from the last one backwards. In the fail run, the last `{` was `elimination_summary` (a nested object). The parser grabbed it, found valid JSON, but it had no `grants` key — so the pipeline saw 0 grants and showed the no-match fallback.

**Root cause:** Parsing free-text LLM output as structured data is inherently fragile. Scout's text output was never pure JSON — both pass and fail runs have narrative preamble before the JSON, despite the prompt requesting "no text before or after." This is consistent behavior across 50+ runs. The prompt asks for something the model reliably doesn't do.

The backwards-`{` parser was a heuristic that worked until it didn't. A better parser (find the largest JSON object) would fix this specific bug but not the category.

## Solutions considered

| Solution | What it does | Why we chose or rejected it |
|----------|-------------|----------------------------|
| **Smarter parser** — find largest JSON object | Fixes this specific bug (largest object is always the outer one with `grants`) | Rejected. Still parsing free text as structured data. Fixes the symptom, not the root cause. The next model variation produces a different failure. |
| **Prompt reinforcement** — "output ONLY JSON" | Reduces narrative preamble frequency | Rejected. Can't guarantee compliance — the model produced preamble on 50+ consecutive runs despite the instruction. |
| **Blind retry** — if 0 grants, re-run Scout | Catches delivery failures by starting over | Rejected. Wasteful — throws away Scout's analysis and re-runs the full pipeline. Slow and expensive for a problem in delivery, not reasoning. |
| **Tool use** — `submit_recommendations` tool | Structured JSON in a dedicated `tool_use` content block. No parsing needed. | **Chosen.** Eliminates the entire category of parsing bugs. Narrative in text block becomes harmless. |
| **Smart recovery from thinking** — feed thinking back, ask Scout to call the tool | If tool call fails, reuse the analysis Scout already did | **Chosen (fallback).** The failure is in delivery, not reasoning. Recovery is cheap — no grant database re-analysis, just "commit what you found." |
| **Concurrency control** — `max_concurrency=1` | Prevents eval suite from overwhelming the API | **Chosen (for evals).** Doesn't fix the parser but prevents the trigger condition. |

## What was implemented

### Primary: Tool use for Scout output
Scout now outputs via `submit_recommendations` tool call instead of raw JSON in text. The tool schema enforces the exact structure the pipeline needs. Pipeline reads the `tool_use` content block — guaranteed valid JSON, no heuristics.

**API constraint discovered:** `tool_choice: {"type": "tool"}` (which forces the model to call a specific tool) is incompatible with extended thinking. The API rejects the combination with a 400 error. Braintrust's `wrap_anthropic` silently caught this error and fell back to a call without tools — which is why the first test after implementation still failed. Fix: removed `tool_choice`, tools are provided without forcing. The prompt instructs Scout to call the tool, and it does reliably.

### Fallback chain
1. **Tool call** → parse `tool_use` content block (primary path)
2. **Smart recovery** → if no tool call, feed thinking back to Scout in a cheap follow-up call: "you already found matches, call the tool now" (no re-analysis, no grant database)
3. **Text parsing** → if recovery fails, fall back to the old `parse_json_output` parser (last resort)
4. **Empty result** → no-match message

### Supporting changes
- `max_concurrency=1` in `evals.py` — sequential eval runs to respect rate limits
- Logging at every pipeline decision point
- Thinking text accumulated during streaming for potential recovery use

## 5 failed eval runs (separate issue)

The 5 eval failures that triggered this investigation were **not** caused by the parsing bug. All 5 hit 429 rate limit errors (8K output tokens/minute) at the Transcriber stage — before Scout even ran. The eval suite ran 12 users concurrently, exhausting the rate limit. Extended thinking tokens count toward the output token rate limit, so Scout's 15K thinking budget alone could exceed the 8K ceiling. Upgrading to Tier 2 (90K OTPM) and running with `max_concurrency=1` resolves this.
