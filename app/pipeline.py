"""
Pipeline: Orchestrates Transcriber → Scout → Scorer
"""
import os
import re
import json
import anthropic
from braintrust import init_logger, wrap_anthropic

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

# Braintrust prompt slugs
TRANSCRIBER_SLUG = "transcriber-prompt-3997"
SCOUT_SLUG = "scout-prompt-7867"
SCORER_SLUG = "scorer-prompt-e86a"


def load_grants():
    """Load grant database from JSON file."""
    grants_path = os.path.join(os.path.dirname(__file__), "..", "data", "grants.json")
    with open(grants_path, "r") as f:
        return json.load(f)


def load_braintrust_prompt(slug):
    """Fetch a prompt from Braintrust by slug."""
    from braintrust import load_prompt as bt_load_prompt
    prompt = bt_load_prompt(project="Scout", slug=slug)
    return prompt


GRANTS = load_grants()
GRANTS_TEXT = json.dumps(GRANTS, indent=2)


def run_transcriber(conversation_text):
    """
    Transcriber: Takes conversation text, returns structured profile.
    May return follow-up questions if critical fields are missing.
    """
    prompt = load_braintrust_prompt(TRANSCRIBER_SLUG)
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=prompt.build()["messages"][0]["content"],
        messages=[
            {
                "role": "user",
                "content": f"Here is the conversation transcript:\n\n{conversation_text}",
            }
        ],
    )
    return response.content[0].text


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


def run_scout(profile_text, thinking_callback=None):
    """
    Scout: Takes confirmed profile, searches grants, returns raw text (JSON).
    If thinking_callback is provided, streams extended thinking tokens to it.
    """
    prompt = load_braintrust_prompt(SCOUT_SLUG)

    if thinking_callback:
        result_text = ""
        with client.messages.stream(
            model=MODEL,
            max_tokens=16000,
            thinking={
                "type": "enabled",
                "budget_tokens": 15000,
            },
            system=prompt.build()["messages"][0]["content"],
            messages=[
                {
                    "role": "user",
                    "content": f"Here is the confirmed user profile:\n\n{profile_text}\n\nHere is the grant database:\n\n{GRANTS_TEXT}",
                }
            ],
        ) as stream:
            for event in stream:
                if event.type == "content_block_delta":
                    if event.delta.type == "thinking_delta":
                        thinking_callback(event.delta.thinking)
                    elif event.delta.type == "text_delta":
                        result_text += event.delta.text
        return result_text
    else:
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            thinking={
                "type": "enabled",
                "budget_tokens": 15000,
            },
            system=prompt.build()["messages"][0]["content"],
            messages=[
                {
                    "role": "user",
                    "content": f"Here is the confirmed user profile:\n\n{profile_text}\n\nHere is the grant database:\n\n{GRANTS_TEXT}",
                }
            ],
        )
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""


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


def run_pipeline(profile_text, thinking_callback=None, scorer_callback=None, status_callback=None, allow_follow_up=True):
    """
    Full pipeline: Scout → [follow-up?] → Scorer (with retries).
    Profile is already confirmed by the advisor/client.

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

    # Step 1: Scout searches and recommends
    update_status("Filtering through 200 grants...")
    scout_output = run_scout(profile_text, thinking_callback=thinking_callback)

    # Parse Scout's JSON output
    try:
        scout_data = parse_json_output(scout_output)
    except ValueError:
        return {
            "needs_follow_up": False,
            "profile": profile_text,
            "scout_output": scout_output,
            "grants": [],
            "near_misses": [],
            "message": NO_MATCH_MESSAGE,
            "retries": 0,
            "approved": False,
            "scorer_skipped": False,
        }

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
        update_status("High confidence - presenting results...")
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
    update_status("Running quality checks on recommendations...")
    scorer_output = run_scorer(profile_text, scout_output, scorer_callback=scorer_callback)

    def is_rejected(output):
        try:
            data = parse_json_output(output)
            return data.get("status", "").upper() == "REJECTED"
        except ValueError:
            return "REJECTED" in output.upper()

    # Retry loop if Scorer rejects
    retries = 0
    while is_rejected(scorer_output) and retries < MAX_SCORER_RETRIES:
        retries += 1
        update_status(f"Refining recommendations (attempt {retries + 1})...")
        scout_output = run_scout(
            f"{profile_text}\n\nPrevious recommendation was rejected by quality check:\n{scorer_output}\n\nPlease try again with this feedback."
        )
        try:
            scout_data = parse_json_output(scout_output)
            grants = scout_data.get("grants", [])
            near_misses = scout_data.get("near_misses", [])
            elimination = scout_data.get("elimination_summary", {})
        except ValueError:
            pass
        update_status("Re-checking quality...")
        scorer_output = run_scorer(profile_text, scout_output)

    # Final check: still rejected after retries?
    if is_rejected(scorer_output):
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
