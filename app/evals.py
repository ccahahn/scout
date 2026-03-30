"""
Evals: Runs 12 synthetic users through the pipeline and scores with Braintrust.

Tier 1 scorers:
  1. Trap Avoidance — no trap grants recommended
  2. Hit Rate — at least 1 correct grant recommended
  3. Overwhelm Check — grant count matches user capacity
"""
import os
import json
import sys

from braintrust import Eval, Score

# Add parent dir so we can import pipeline
sys.path.insert(0, os.path.dirname(__file__))
from pipeline import run_transcriber, run_pipeline


def load_synthetic_users():
    """Load all 12 synthetic users from JSON."""
    path = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic-users.json")
    with open(path, "r") as f:
        return json.load(f)


def build_call_notes(user):
    """
    Construct call notes from a synthetic user profile,
    simulating what an advisor would paste after a 1:1 call.
    """
    # Get the "what they say first" field (varies by user)
    says_first = (
        user.get("what_she_says_first")
        or user.get("what_he_says_first")
        or user.get("mission", "")
    )

    populations = ", ".join(user.get("populations_served", []))
    dealbreakers = ", ".join(user.get("dealbreakers", []))
    preferences = ", ".join(user.get("preferences", []))

    current_funding = user.get("current_funding", "not discussed")
    fund_use = user.get("fund_use", "not discussed")
    renewability = user.get("renewability_preference", "not discussed")
    spending = user.get("spending_parameters", "not discussed")

    notes = f"""Organization: {user["org_name"]}
Location: {user["location"]} ({user["county"]})
Mission: {says_first}
Who they serve: {populations}
Team size: {user["team_size"]}
Annual budget: ${user["annual_budget"]:,}
Years operating: {user["years_operating"]}
Grant experience: {user["grant_experience"]}
Current grants or funding: {current_funding}
How they'd use the funds: {fund_use}
Renewability: {renewability}
Spending parameters: {spending}
Looking for: {preferences}
Avoid: {dealbreakers}
Mode: {user["browsing_mode"].replace("_", " ")}"""

    return notes


def get_recommended_ids(output):
    """Extract grant IDs from pipeline output."""
    grants = output.get("grants", [])
    return {g.get("id") for g in grants if g.get("id")}


def max_grants_for_user(user):
    """
    Max top recommendations: 3 for everyone.
    Users compare and choose — 3 gives options without overwhelm.
    Near-misses ("worth considering") add 0-2 more, capped at 5 total.
    """
    return 3


# ---------------------------------------------------------------------------
# Scorers
# ---------------------------------------------------------------------------

def trap_avoidance(output, expected):
    """Score 1.0 if no trap grants were recommended, 0.0 if any were."""
    recommended = get_recommended_ids(output)
    traps = set(expected.get("trap_grants", []))
    found_traps = recommended & traps

    return Score(
        name="trap_avoidance",
        score=0.0 if found_traps else 1.0,
        metadata={
            "trap_grants_found": sorted(found_traps),
            "recommended_ids": sorted(recommended),
        },
    )


def hit_rate(output, expected):
    """Score 1.0 if at least 1 correct grant was recommended, 0.0 if none."""
    recommended = get_recommended_ids(output)
    correct = set(expected.get("correct_grants", []))
    hits = recommended & correct

    return Score(
        name="hit_rate",
        score=1.0 if hits else 0.0,
        metadata={
            "correct_grants_found": sorted(hits),
            "correct_grants_expected": sorted(correct),
            "recommended_ids": sorted(recommended),
        },
    )


def overwhelm_check(output, expected):
    """Score 1.0 if grant count is within limits, 0.0 if over.
    Max 3 top recommendations. Max 2 near-misses. Max 5 total."""
    grants = output.get("grants", [])
    near_misses = output.get("near_misses", [])
    grant_count = len(grants)
    near_miss_count = len(near_misses)
    total = grant_count + near_miss_count

    max_grants = 3
    max_near_misses = 2
    max_total = 5

    passed = grant_count <= max_grants and near_miss_count <= max_near_misses and total <= max_total

    return Score(
        name="overwhelm_check",
        score=1.0 if passed else 0.0,
        metadata={
            "grant_count": grant_count,
            "near_miss_count": near_miss_count,
            "total": total,
            "max_grants": max_grants,
            "max_near_misses": max_near_misses,
            "max_total": max_total,
        },
    )


# ---------------------------------------------------------------------------
# Task function
# ---------------------------------------------------------------------------

def run_eval_task(input, hooks=None):
    """
    Run a single synthetic user through the full pipeline.
    Input is the call notes string. Returns the pipeline result dict.
    """
    # Step 1: Transcriber extracts profile from call notes
    profile = run_transcriber(input)

    # Step 2: Pipeline runs Scout (+ conditional Scorer) on the profile
    # No streaming callbacks — evals run headless
    result = run_pipeline(profile, allow_follow_up=False)

    return result


# ---------------------------------------------------------------------------
# Dataset + Eval
# ---------------------------------------------------------------------------

def build_dataset():
    """Build Braintrust dataset from synthetic users."""
    users = load_synthetic_users()
    dataset = []
    for user in users:
        dataset.append({
            "input": build_call_notes(user),
            "expected": user,
            "metadata": {
                "user_id": user["id"],
                "user_name": user["name"],
            },
        })
    return dataset


if __name__ == "__main__":
    Eval(
        name="Scout",
        data=build_dataset,
        task=run_eval_task,
        scores=[trap_avoidance, hit_rate, overwhelm_check],
        max_concurrency=1,  # Rate limit: 8K output tokens/min on current tier
    )
