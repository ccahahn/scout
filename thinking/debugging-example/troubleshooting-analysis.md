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

## Why it failed

The `parse_json_output` function searches for JSON by iterating `{` positions **from the last one backwards**. In the fail run, the last `{` was at position 4120 — the start of `elimination_summary`, a nested object inside the main JSON. The parser found that, successfully parsed it, and returned it. But `elimination_summary` has no `grants` key, so the pipeline saw 0 grants and showed the no-match message.

In the pass run, the same backwards search happened to land on an object that either was the outer JSON or contained the grants. Same parsing strategy, different luck.

**The JSON was always there. The parser grabbed the wrong object.**

## Open question: why did the format change?

Both runs produce narrative + JSON (not pure JSON as the prompt requests). This appears to be Scout's normal behavior — the model adds reasoning preamble in both cases. So the format didn't change.

What may have changed: the **length and structure** of the narrative preamble. The fail run's preamble is longer (2301 chars to first `{` vs. 2115 in the pass run), and the nested JSON objects land at different positions. This shifted which object the backwards parser found first.

**The correlation with rate limiting is suspicious but unproven.** 50+ successful runs, then the first failure coincides exactly with API rate pressure from the eval suite. Possible explanations:

1. **Coincidence** — the format varies slightly every run, and this was the first time the variation hit the parser's blind spot
2. **API pressure affects output quality** — rate-limited or recently-throttled requests may produce subtly different outputs (different preamble length, different JSON positioning). Not documented by Anthropic but not ruled out.
3. **Something else entirely** — needs more data points to determine

## Proposed solutions

### Fix 1: Robust parser (addresses the direct cause)
Change `parse_json_output` to find the **largest** valid JSON object in the text instead of the last one. The outer object (with `grants`, `near_misses`, `elimination_summary`) is always the largest. This makes the parser resilient to narrative preamble and nested object positioning.

### Fix 2: Retry on malformed output (defense in depth)
If `parse_json_output` returns a dict with no `grants` key, treat it as a parse failure and retry Scout once. This catches cases where the parser finds valid JSON but the wrong object.

### Fix 3: Prompt reinforcement (addresses root cause)
Strengthen Scout's prompt: "Your text output must be ONLY a JSON object. No narrative, no explanation, no markdown. All reasoning goes in your thinking block." This reduces the frequency of narrative preamble but cannot guarantee it — the model may still produce preamble under certain conditions.

### Fix 4: Concurrency control for evals (prevents the trigger)
Already implemented: `max_concurrency=1` in `evals.py` prevents the eval suite from hammering the API. This reduces the chance of rate-limit-adjacent weirdness but doesn't fix the parser.

### Recommendation
Fix 1 is the most important — it directly solves the parsing failure. Fix 3 is worth trying but won't be 100% reliable. Fix 2 is belt-and-suspenders. Fix 4 is already done.

## Changes made (by this Claude instance)

1. **Logging added to `pipeline.py`** — log statements at every decision point (Scout output length, JSON parse success/failure, Scorer verdict, retry loop). This will show exactly where the pipeline breaks next time. **Kept.**
2. **`parse_json_output` was rewritten then reverted** — the original last-`{`-backwards parser is restored. Fix 1 above is a proposal, not implemented. **A fresh Claude instance should evaluate this independently with both the fail and pass log files before any parser changes are made.**

## Next Claude Instance's Analysis

The parser is the proximate cause. The root cause is deeper.                                                                                               
                                         
  Scout's text output was never pure JSON. Both runs — pass and fail — have narrative preamble before the JSON. The prompt says "no markdown, no text before 
  or after" but the model doesn't comply. And it's not a fluke: it's consistent across 50+ runs. The prompt is asking for something the model reliably
  doesn't do.                                                                                                                                                
                                                            
  So the real question isn't "why did the parser grab the wrong object?" It's: why is the pipeline parsing free-text LLM output as structured data?          
   
  That's an inherently fragile contract. You're asking the model to do two things in one output channel:                                                     
  - Be a consultant (narrative reasoning streamed to the user via thinking)
  - Be a machine (structured JSON parsed by the pipeline)                                                                                                    
                                                            
  The model blurs the line every time — it puts narrative in the text block alongside the JSON, because that's what LLMs do. The backwards-{ parser was a    
  workaround for this, and it worked until the nested elimination_summary object happened to be the last {.                                                  
   
  The fix isn't a better parser. The fix is not parsing free text as JSON.                                                                                   
                                                            
  Claude's API supports tool use, which returns structured JSON in a dedicated tool_use content block — separate from text. Scout could "call a tool" like   
  submit_recommendations with the grants payload. The pipeline parses the tool call (guaranteed valid JSON, guaranteed in a known location), and any
  narrative the model wants to add stays in the text block where it can't break anything.                                                                    
                                                            
  This eliminates the entire category of bug: no preamble problem, no nested-object problem, no parser heuristics. The model's natural tendency to narrate   
  becomes harmless instead of dangerous.

 Tool use is the mechanism that makes your architecture work cleanly:

  1. Scout thinks — extended thinking block, natural language, streamed to user
  2. Scout calls a tool — submit_recommendations(grants=[...], near_misses=[...], elimination_summary={...}) — the tool schema enforces the JSON shape, the
  model fills in values based on its thinking
  3. Pipeline reads the tool call — guaranteed valid JSON, guaranteed in a known content block, no parsing heuristics
  4. Feed to Scorer — deterministic handoff, no ambiguity

  The tool schema is the deterministic function. It constrains the model's output into the exact shape the Scorer expects. Scout still does all the reasoning
   — the schema just forces it to commit to a structure at the end.
