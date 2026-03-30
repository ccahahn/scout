"""
Pipeline: Orchestrates Transcriber → Scout → Scorer
"""
import os
import re
import json
import anthropic
from braintrust import init_logger, wrap_anthropic

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("scout.pipeline")

try:
    import streamlit as st
    api_key = st.secrets.get("ANTHROPIC_API_KEY")
    bt_key = st.secrets.get("BRAINTRUST_API_KEY")
    if bt_key:
        os.environ["BRAINTRUST_API_KEY"] = bt_key
except Exception:
    api_key = None

if not api_key:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")

# Initialize Braintrust-wrapped Anthropic client
client = wrap_anthropic(
    anthropic.Anthropic(api_key=api_key)
)
logger = init_logger(project="Scout")

MODEL = "claude-sonnet-4-20250514"
MAX_SCORER_RETRIES = 2

# Tool schema for Scout — forces structured output via tool use
# Tool schema for Transcriber — forces structured profile output
TRANSCRIBER_TOOL = {
    "name": "submit_profile",
    "description": "Submit the structured user profile extracted from the call notes.",
    "input_schema": {
        "type": "object",
        "properties": {
            "organization": {"type": "string", "description": "Organization name"},
            "location": {"type": "string", "description": "City, county, and state"},
            "mission": {"type": "string", "description": "What the org does, in the user's own language"},
            "who_they_serve": {"type": "string", "description": "Populations or communities served"},
            "budget": {"type": "string", "description": "Annual budget or size indicator"},
            "grant_experience": {"type": "string", "description": "First-time, some, experienced — plus any specifics"},
            "sweet_spot": {"type": "string", "description": "Ideal grant size range"},
            "dealbreakers": {"type": "string", "description": "What they want to avoid or can't handle"},
            "urgency": {"type": "string", "description": "How urgently they need to apply"},
            "org_type": {"type": "string", "description": "Organization type. Default to '501(c)(3) nonprofit' unless the user explicitly says otherwise (e.g. fiscal sponsor, government, individual)."},
            "fund_use": {"type": "string", "description": "How they'd use the funds — staffing, equipment, community partner, etc."},
            "renewability": {"type": "string", "description": "One-time OK, or needs multi-year/renewable funding"},
            "looking_for": {"type": "string", "description": "What they're specifically looking for in a grant"},
        },
        "required": ["organization", "location", "mission"],
    },
}

# Tool schema for Scout — forces structured output via tool use
SCOUT_TOOL = {
    "name": "submit_recommendations",
    "description": "Submit your grant recommendations, near-misses, follow-up questions, and elimination summary after completing your analysis.",
    "input_schema": {
        "type": "object",
        "properties": {
            "grants": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "amount_min": {"type": ["number", "null"]},
                        "amount_max": {"type": ["number", "null"]},
                        "deadline": {"type": "string"},
                        "rationale": {"type": "string"},
                        "caveats": {"type": ["string", "null"]},
                        "confidence": {"type": "string", "enum": ["High", "Medium"]},
                        "funder": {"type": "string", "description": "Name of the funding organization"},
                        "fit_tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Short fit-reason tags, e.g. 'location match', 'mission match', 'budget fit', 'simple application'",
                        },
                    },
                    "required": ["id", "title", "rationale", "confidence"],
                },
            },
            "near_misses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "what_aligns": {"type": "string"},
                        "the_issue": {"type": "string"},
                        "the_play": {"type": "string"},
                    },
                    "required": ["id", "title", "what_aligns", "the_issue", "the_play"],
                },
            },
            "follow_up_questions": {
                "type": "array",
                "items": {"type": "string"},
            },
            "elimination_summary": {
                "type": "object",
                "properties": {
                    "total_reviewed": {"type": "integer"},
                    "eliminated_geographic": {"type": "integer"},
                    "eliminated_dealbreaker": {"type": "integer"},
                    "eliminated_eligibility": {"type": "integer"},
                    "recommended": {"type": "integer"},
                },
            },
        },
        "required": ["grants", "near_misses", "follow_up_questions", "elimination_summary"],
    },
}

# Braintrust prompt slugs
TRANSCRIBER_SLUG = "transcriber-prompt-3997"
SCOUT_SLUG = "scout-prompt-7867"
SCORER_SLUG = "scorer-prompt-e86a"


def load_grants():
    """Load grant database from JSON file."""
    grants_path = os.path.join(os.path.dirname(__file__), "..", "data", "grants.json")
    with open(grants_path, "r") as f:
        return json.load(f)


_prompt_cache = {}
_prompt_cache_time = {}
PROMPT_CACHE_TTL = 300  # 5 minutes


def load_braintrust_prompt(slug):
    """Fetch a prompt from Braintrust by slug, cached for 5 minutes."""
    import time
    now = time.time()
    if slug in _prompt_cache and (now - _prompt_cache_time.get(slug, 0)) < PROMPT_CACHE_TTL:
        return _prompt_cache[slug]
    from braintrust import load_prompt as bt_load_prompt
    prompt = bt_load_prompt(project="Scout", slug=slug)
    _prompt_cache[slug] = prompt
    _prompt_cache_time[slug] = now
    return prompt


GRANTS = load_grants()

# US state abbreviations for extraction
US_STATES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN",
    "mississippi": "MS", "missouri": "MO", "montana": "MT", "nebraska": "NE",
    "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
    "new mexico": "NM", "new york": "NY", "north carolina": "NC",
    "north dakota": "ND", "ohio": "OH", "oklahoma": "OK", "oregon": "OR",
    "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
}
STATE_ABBREVS = {v: v for v in US_STATES.values()}


def extract_state(profile_text):
    """Extract US state abbreviation from profile text."""
    text_lower = profile_text.lower()
    # Check for abbreviation in Location line first
    for line in profile_text.split("\n"):
        if line.strip().lower().startswith("location"):
            # Look for 2-letter state abbreviation
            abbrev_match = re.search(r'\b([A-Z]{2})\b', line)
            if abbrev_match and abbrev_match.group(1) in STATE_ABBREVS:
                return abbrev_match.group(1)
            # Look for full state name
            for name, abbrev in US_STATES.items():
                if name in line.lower():
                    return abbrev
    # Fallback: search full text for state names
    for name, abbrev in US_STATES.items():
        if name in text_lower:
            return abbrev
    return None


def filter_grants_for_profile(grants, profile_text):
    """
    Pre-filter grants by state before sending to Scout.
    Keeps: grants in the user's state + national-scope grants.
    Removes: grants in other states (obvious geographic mismatches).
    Scout still handles county-level matching and all judgment calls.
    """
    state = extract_state(profile_text)
    if not state:
        return grants  # Can't determine state, send all grants

    filtered = [
        g for g in grants
        if g.get("state") == state or g.get("state") == "national"
    ]
    return filtered


def profile_dict_to_text(profile):
    """Convert a structured profile dict to text for Scout/Scorer."""
    lines = []
    field_labels = {
        "organization": "Organization",
        "org_type": "Organization type",
        "location": "Location",
        "mission": "Mission",
        "who_they_serve": "Who they serve",
        "budget": "Budget",
        "grant_experience": "Grant experience",
        "sweet_spot": "Sweet spot",
        "fund_use": "How they'd use the funds",
        "renewability": "Renewability",
        "looking_for": "Looking for",
        "dealbreakers": "Dealbreakers",
        "urgency": "Urgency",
    }
    for key, label in field_labels.items():
        val = profile.get(key, "")
        if val:
            lines.append(f"{label}: {val}")
    return "\n".join(lines)


def run_transcriber(conversation_text):
    """
    Transcriber: Takes freeform conversation text, returns structured profile dict.
    Uses tool use to guarantee structured JSON output with all 9 profile fields.
    """
    prompt = load_braintrust_prompt(TRANSCRIBER_SLUG)
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        tools=[TRANSCRIBER_TOOL],
        system=prompt.build()["messages"][0]["content"],
        messages=[
            {
                "role": "user",
                "content": f"Here is the conversation transcript:\n\n{conversation_text}",
            }
        ],
    )
    # Extract structured profile from tool call
    for block in response.content:
        if block.type == "tool_use":
            return block.input
    # Fallback: try to parse text output as JSON
    for block in response.content:
        if block.type == "text" and block.text:
            try:
                return parse_json_output(block.text)
            except ValueError:
                pass
    # Last resort: return the text as-is wrapped in a dict
    log.warning("Transcriber did not call tool — returning raw text")
    text = response.content[0].text if response.content else ""
    return {"organization": "", "location": "", "mission": text, "who_they_serve": "", "budget": "", "grant_experience": "", "sweet_spot": "", "fund_use": "", "renewability": "", "looking_for": "", "dealbreakers": "", "urgency": ""}


def parse_json_output(text):
    """
    Extract a JSON object from LLM text output.
    Handles ```json code fences, raw JSON, and JSON preceded by reasoning text.
    Tries from the last { backwards to find the main JSON object.
    """
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    positions = [i for i, c in enumerate(text) if c == '{']
    for start in reversed(positions):
        depth = 0
        for i in range(start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
    raise ValueError(f"No valid JSON found in output: {text[:300]}")


def escape_dollars(text):
    """Escape dollar signs to prevent Streamlit LaTeX rendering."""
    return text.replace('$', '&#36;')


def run_scout(profile_text, grants=None, thinking_callback=None, raw_notes=None):
    """
    Scout: Takes confirmed profile, searches grants, returns structured dict.
    Uses tool use to guarantee valid JSON output — no free-text parsing.
    If thinking_callback is provided, streams extended thinking tokens to it.
    Grants are pre-filtered by state before being passed in.
    raw_notes: original freeform advisor notes — gives Scout extra context beyond the structured profile.
    """
    if grants is None:
        grants = GRANTS
    # Strip to matching-relevant fields — detail page loads full data from grants.json
    SCOUT_FIELDS = {"id", "title", "funder", "amount_min", "amount_max", "deadline",
                    "geographic_scope", "state", "eligible_applicants", "focus_areas",
                    "federal", "description"}
    slim_grants = [{k: g[k] for k in SCOUT_FIELDS if k in g} for g in grants]
    grants_text = json.dumps(slim_grants, indent=2)
    prompt = load_braintrust_prompt(SCOUT_SLUG)

    user_content = f"Here is the confirmed user profile:\n\n{profile_text}\n\nHere is the grant database:\n\n{grants_text}"

    api_params = dict(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "enabled", "budget_tokens": 8000},
        tools=[SCOUT_TOOL],
        system=prompt.build()["messages"][0]["content"],
        messages=[
            {
                "role": "user",
                "content": user_content,
            }
        ],
    )

    if thinking_callback:
        tool_json = ""
        fallback_text = ""
        thinking_text = ""
        with client.messages.stream(**api_params) as stream:
            for event in stream:
                if event.type == "content_block_delta":
                    delta_type = getattr(event.delta, "type", None)
                    if delta_type == "thinking_delta":
                        thinking_callback(event.delta.thinking)
                        thinking_text += event.delta.thinking
                    elif delta_type == "input_json_delta":
                        tool_json += event.delta.partial_json
                    elif delta_type == "text_delta":
                        fallback_text += event.delta.text
        if tool_json:
            return json.loads(tool_json)
        # Model didn't call the tool — try to recover from thinking
        log.warning("Scout did not call tool — attempting recovery")
        if thinking_text:
            return _recover_from_thinking(thinking_text, api_params)
        if fallback_text:
            return parse_json_output(fallback_text)
        return {"grants": [], "near_misses": [], "follow_up_questions": [], "elimination_summary": {}}
    else:
        response = client.messages.create(**api_params)
        for block in response.content:
            if block.type == "tool_use":
                return block.input
        # Model didn't call the tool — fall back to text parsing
        log.warning("Scout did not call tool — falling back to text parsing")
        for block in response.content:
            if block.type == "text" and block.text:
                return parse_json_output(block.text)
        return {"grants": [], "near_misses": [], "follow_up_questions": [], "elimination_summary": {}}


def _recover_from_thinking(thinking_text, original_params):
    """
    Scout analyzed grants but didn't call the tool.
    Feed the thinking back and ask it to just call submit_recommendations.
    Cheap call — no grant database, no extended thinking, just the tool call.
    """
    log.info("Attempting tool recovery from thinking (%d chars)", len(thinking_text))
    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        tools=[SCOUT_TOOL],
        system=original_params["system"],
        messages=[
            original_params["messages"][0],  # original user message with profile + grants
            {"role": "assistant", "content": f"Here is my analysis:\n\n{thinking_text}\n\nLet me now submit my recommendations."},
            {"role": "user", "content": "Please call submit_recommendations now based on your analysis above."},
        ],
    )
    for block in response.content:
        if block.type == "tool_use":
            log.info("Tool recovery succeeded")
            return block.input
    log.error("Tool recovery failed — no tool call in response")
    # Last resort: try parsing text
    for block in response.content:
        if block.type == "text" and block.text:
            try:
                return parse_json_output(block.text)
            except ValueError:
                pass
    return {"grants": [], "near_misses": [], "follow_up_questions": [], "elimination_summary": {}}


def run_scout_with_answers(profile_text, previous_scout_output, follow_up_answers):
    """
    Lightweight Scout call: takes the original Scout analysis + user's follow-up answers
    and produces final recommendations. No grant database, no extended thinking.
    Much faster than a full re-run (~5-10s vs ~60s).
    """
    log.info("Running Scout follow-up with answers (lightweight)")
    prompt = load_braintrust_prompt(SCOUT_SLUG)

    response = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        tools=[SCOUT_TOOL],
        system=prompt.build()["messages"][0]["content"],
        messages=[
            {
                "role": "user",
                "content": f"Here is the confirmed user profile:\n\n{profile_text}",
            },
            {
                "role": "assistant",
                "content": f"I analyzed the grants and had some follow-up questions. Here is my initial analysis:\n\n{previous_scout_output}",
            },
            {
                "role": "user",
                "content": f"Here are the answers to your follow-up questions:\n\n{follow_up_answers}\n\nPlease finalize your recommendations based on this additional information. Call submit_recommendations with your final picks.",
            },
        ],
    )
    for block in response.content:
        if block.type == "tool_use":
            return block.input
    # Fallback
    for block in response.content:
        if block.type == "text" and block.text:
            try:
                return parse_json_output(block.text)
            except ValueError:
                pass
    return {"grants": [], "near_misses": [], "follow_up_questions": [], "elimination_summary": {}}


def run_scorer(profile_text, scout_output, scorer_callback=None):
    """
    Scorer: Takes profile + Scout's recommendations, returns reasoning text + JSON verdict.
    If scorer_callback is provided, streams text tokens to it.
    """
    prompt = load_braintrust_prompt(SCORER_SLUG)

    if scorer_callback:
        result_text = ""
        with client.messages.stream(
            model=MODEL,
            max_tokens=4096,
            system=prompt.build()["messages"][0]["content"],
            messages=[
                {
                    "role": "user",
                    "content": f"Here is the confirmed user profile:\n\n{profile_text}\n\nHere are Scout's draft recommendations:\n\n{scout_output}",
                }
            ],
        ) as stream:
            for event in stream:
                if event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        result_text += event.delta.text
                        scorer_callback(event.delta.text)
        return result_text
    else:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=prompt.build()["messages"][0]["content"],
            messages=[
                {
                    "role": "user",
                    "content": f"Here is the confirmed user profile:\n\n{profile_text}\n\nHere are Scout's draft recommendations:\n\n{scout_output}",
                }
            ],
        )
        return response.content[0].text


NO_MATCH_MESSAGE = """I reviewed the available opportunities against your profile and couldn't find a strong match right now.

That's useful information. It means the right grant for you likely isn't in this database yet, not that it doesn't exist. A few next steps worth considering:

- Check with your onboarding advisor about additional sources
- Look at local community foundations in your area directly
- Check back as new opportunities are added

This isn't a dead end. It's a starting point."""


def run_pipeline(profile_text, raw_notes=None, thinking_callback=None, scorer_callback=None, status_callback=None, step_callback=None, allow_follow_up=True):
    """
    Full pipeline: Scout → [follow-up?] → Scorer (with retries).
    Profile is already confirmed by the advisor/client.
    raw_notes: original freeform text from the advisor — passed to Scout for extra context.

    Returns a dict with:
      - "needs_follow_up": True if Scout has questions for the user
      - "follow_up_questions": list of question strings (if needs_follow_up)
      - "grants": list of grant dicts (title, amount_min, amount_max, deadline, rationale, etc.)
      - "near_misses": list of near-miss dicts
      - "elimination_summary": dict with filtering stats
      - "message": fallback text for no-match case
    """
    def update_status(msg):
        if status_callback:
            status_callback(msg)

    def update_step(step, detail=None):
        if step_callback:
            step_callback(step, detail)

    # Step 0: Pre-filter grants by state (mechanical, fast)
    update_step("reading_profile")
    filtered_grants = filter_grants_for_profile(GRANTS, profile_text)
    update_step("scanning", f"{len(filtered_grants)} reviewed")

    # Step 1: Scout searches and recommends (returns structured dict via tool use)
    scout_data = run_scout(profile_text, grants=filtered_grants, thinking_callback=thinking_callback, raw_notes=raw_notes)
    scout_output = json.dumps(scout_data, indent=2)  # string form for Scorer and chat context
    log.info("Scout returned %d grants, %d near_misses", len(scout_data.get("grants", [])), len(scout_data.get("near_misses", [])))
    update_step("scoring")

    # Step 1b: Check if Scout has follow-up questions
    follow_up = scout_data.get("follow_up_questions", [])
    if follow_up and allow_follow_up:
        update_status("Scout has a few questions before finalizing...")
        return {
            "needs_follow_up": True,
            "follow_up_questions": follow_up,
            "scout_output": scout_output,
            "profile": profile_text,
        }

    grants = scout_data.get("grants", [])
    near_misses = scout_data.get("near_misses", [])
    elimination = scout_data.get("elimination_summary", {})

    # No grants found
    if not grants:
        log.warning("Scout returned 0 grants — showing no-match message")
        update_step("done", "0")
        return {
            "needs_follow_up": False,
            "profile": profile_text,
            "scout_output": scout_output,
            "grants": [],
            "near_misses": near_misses,
            "elimination_summary": elimination,
            "message": NO_MATCH_MESSAGE,
            "retries": 0,
            "approved": False,
            "scorer_skipped": True,
        }

    # Step 2: Conditional Scorer — only if Scout has Medium/Low confidence
    all_high = all(
        g.get("confidence", "").lower() == "high" for g in grants
    )

    if all_high:
        log.info("All grants High confidence — skipping Scorer, presenting %d grants", len(grants))
        update_step("done", str(len(grants)))
        return {
            "needs_follow_up": False,
            "profile": profile_text,
            "scout_output": scout_output,
            "scorer_output": None,
            "grants": grants,
            "near_misses": near_misses,
            "elimination_summary": elimination,
            "retries": 0,
            "approved": True,
            "scorer_skipped": True,
        }

    # Medium/Low confidence — Scorer reviews
    log.info("Medium/Low confidence detected — running Scorer on %d grants", len(grants))
    update_status("Running quality checks on recommendations...")
    scorer_output = run_scorer(profile_text, scout_output, scorer_callback=scorer_callback)
    log.info("Scorer verdict: %s", "REJECTED" if "REJECTED" in scorer_output.upper() else "APPROVED")

    def is_rejected(output):
        try:
            data = parse_json_output(output)
            return data.get("status", "").upper() == "REJECTED"
        except ValueError:
            return "REJECTED" in output.upper()

    # Retry loop if Scorer rejects
    retries = 0
    retry_messages = [
        "Almost there — double-checking the fit...",
        "Not quite right yet — trying a different angle...",
    ]
    while is_rejected(scorer_output) and retries < MAX_SCORER_RETRIES:
        # Try to extract what failed from Scorer output
        retry_reason = ""
        try:
            scorer_data_check = parse_json_output(scorer_output)
            failed = scorer_data_check.get("failed_checks", [])
            if failed:
                retry_reason = f" ({failed[0][:60]})"
        except ValueError:
            pass

        retries += 1
        log.info("Scorer rejected — retry %d of %d%s", retries, MAX_SCORER_RETRIES, retry_reason)
        update_status(retry_messages[retries - 1] if retries <= len(retry_messages) else "Scout is refining...")
        scout_data = run_scout(
            f"{profile_text}\n\nPrevious recommendation was rejected by quality check:\n{scorer_output}\n\nPlease try again with this feedback.",
            grants=filtered_grants,
        )
        scout_output = json.dumps(scout_data, indent=2)
        grants = scout_data.get("grants", [])
        near_misses = scout_data.get("near_misses", [])
        elimination = scout_data.get("elimination_summary", {})
        update_status("Re-checking quality...")
        scorer_output = run_scorer(profile_text, scout_output)

    # Final check: still rejected after retries?
    if is_rejected(scorer_output):
        log.error("Scorer still REJECTED after %d retries — showing no-match message", retries)
        update_step("done", "0")
        return {
            "needs_follow_up": False,
            "profile": profile_text,
            "scout_output": scout_output,
            "scorer_output": scorer_output,
            "grants": [],
            "near_misses": [],
            "message": NO_MATCH_MESSAGE,
            "retries": retries,
            "approved": False,
            "scorer_skipped": False,
        }

    # Scorer approved — use Scorer's grants if available (may have added caveats)
    try:
        scorer_data = parse_json_output(scorer_output)
        if scorer_data.get("grants"):
            grants = scorer_data["grants"]
    except ValueError:
        pass

    update_step("done", str(len(grants)))
    return {
        "needs_follow_up": False,
        "profile": profile_text,
        "scout_output": scout_output,
        "scorer_output": scorer_output,
        "grants": grants,
        "near_misses": near_misses,
        "elimination_summary": elimination,
        "retries": retries,
        "approved": True,
        "scorer_skipped": False,
    }


def run_pipeline_with_answers(profile_text, previous_scout_output, follow_up_answers, scorer_callback=None, step_callback=None):
    """
    Lightweight pipeline for follow-up answers. Skips Transcriber and grant filtering.
    Just re-runs Scout (without extended thinking) and conditional Scorer.
    """
    def update_step(step, detail=None):
        if step_callback:
            step_callback(step, detail)

    update_step("scoring")

    scout_data = run_scout_with_answers(profile_text, previous_scout_output, follow_up_answers)
    scout_output = json.dumps(scout_data, indent=2)
    log.info("Scout follow-up returned %d grants", len(scout_data.get("grants", [])))

    grants = scout_data.get("grants", [])
    near_misses = scout_data.get("near_misses", [])
    elimination = scout_data.get("elimination_summary", {})

    if not grants:
        update_step("done", "0")
        return {
            "needs_follow_up": False,
            "profile": profile_text,
            "scout_output": scout_output,
            "grants": [],
            "near_misses": near_misses,
            "elimination_summary": elimination,
            "message": NO_MATCH_MESSAGE,
            "retries": 0,
            "approved": False,
            "scorer_skipped": True,
        }

    # Conditional Scorer
    all_high = all(g.get("confidence", "").lower() == "high" for g in grants)
    if all_high:
        update_step("done", str(len(grants)))
        return {
            "needs_follow_up": False,
            "profile": profile_text,
            "scout_output": scout_output,
            "scorer_output": None,
            "grants": grants,
            "near_misses": near_misses,
            "elimination_summary": elimination,
            "retries": 0,
            "approved": True,
            "scorer_skipped": True,
        }

    scorer_output = run_scorer(profile_text, scout_output, scorer_callback=scorer_callback)
    update_step("done", str(len(grants)))

    return {
        "needs_follow_up": False,
        "profile": profile_text,
        "scout_output": scout_output,
        "scorer_output": scorer_output,
        "grants": grants,
        "near_misses": near_misses,
        "elimination_summary": elimination,
        "retries": 0,
        "approved": True,
        "scorer_skipped": False,
    }


CHAT_SYSTEM_PROMPT = """You are Scout, a grant prospecting co-pilot. The user has just received grant recommendations and is now asking follow-up questions.

You have full context: their profile, the grants you searched, and the recommendations they saw. Answer their questions directly — about specific grants, why you picked or didn't pick something, deadlines, application processes, or what to look for next.

Be conversational, specific, and honest. Use their language. If they ask about a grant you eliminated, explain why honestly. If they want to adjust criteria, note what changed.

Keep responses concise — 2-4 sentences for simple questions, a short paragraph for complex ones."""


def run_chat_followup(profile, scout_output, grants, chat_history):
    """
    Handle follow-up chat after results are shown.
    Has full context of the profile, scout's work, and the grants shown.
    """
    grants_context = json.dumps(grants, indent=2)
    messages = [
        {
            "role": "user",
            "content": f"Context — User profile:\n{profile}\n\nScout's full analysis:\n{scout_output}\n\nGrants shown to user:\n{grants_context}",
        },
        {"role": "assistant", "content": "I have the full context. Ready for questions."},
    ]
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=CHAT_SYSTEM_PROMPT,
        messages=messages,
    )
    return escape_dollars(response.content[0].text)
