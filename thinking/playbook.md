## Playbook: Eval-Driven Development for Scout

> **Operating principle:** "How do we protect users while learning" — not "how do we launch."

**Scope note:** **What we build now** (the prototype): the eval loop, the scorers, the Braintrust workflow — everything in Phase 0. **What we'd implement on the job** (at Instrumentl): feature flags, A/B testing, GitHub Actions CI/CD, production cohort analysis. That second layer is documented here to show the thinking, not because we're building it into the prototype. The prototype proves the eval-driven development process works. The org-level infrastructure is the proposal for day one on the job.

This is the operating manual for how Scout improves. Not the what (that's in the spec, section 4) — the how. Every prompt change, every new scorer, every release follows this loop.

This playbook has two parts. **Part 1** is the IC work — the eval loop, the scorers, the calibration, the prompt iteration. This is what an AI PM does every day with their hands on the pipeline. **Part 2** is the org strategy — rollout phases, feature flags, experimentation infrastructure, cohort analysis. This is what a director decides: who sees Scout, when, and under what conditions. Neither part works without the other. The IC process generates the evidence. The org strategy decides what to do with it.

---

## Part 1: AI PM / IC PM — The Development Process

> The daily work of improving Scout. You run the eval loop, build and calibrate scorers, iterate prompts, and gate every change with CI. Everything in this section produces the data that Part 2's rollout decisions depend on.

---

### The loop

```
Observe -> Score -> Diagnose -> Change -> Verify -> Ship
```

1. **Observe** — Run all 12 synthetic users through the full pipeline. Read every output by hand. Annotate what failed and what surprised you.
2. **Score** — Run automated scorers against the same outputs. Compare automated scores to your manual annotations. If they disagree, the scorer is wrong — fix the scorer, not your judgment.
3. **Diagnose** — For each failure, trace it to the responsible agent (Transcriber, Scout, or Scorer). Read the full trace in Braintrust. Identify whether the failure is a prompt issue, a data issue, or a scorer gap.
4. **Change** — Update the prompt in Braintrust (one agent at a time, one change at a time). Or add a new scorer. Never both in the same run.
5. **Verify** — Re-run the same 12 users. Confirm the failure is fixed AND no new regressions appeared.
6. **Ship** — If scores improve or hold, promote the change. If scores regress, revert.

**Rule: never skip Observe.** Automated scorers catch known failures. Manual review catches unknown failures. Both are required.

---

### Scorer build order

Scorers are built in tiers. Each tier must be stable (consistent scores across 3 consecutive runs) before moving to the next.

#### Tier 1 — Deterministic, high-signal (build first)

| Scorer | Type | What it checks | Input | Pass condition |
|--------|------|---------------|-------|----------------|
| Trap Avoidance | Code | No trap grants recommended | `result.grants` vs `user.trap_grants` | Intersection is empty |
| Hit Rate | Code | At least 1 correct grant recommended | `result.grants` vs `user.correct_grants` | Intersection is non-empty |
| Geographic Precision | Code | No wrong-county grants | `result.grants` county vs `user.county` | All grants match user's county or are national/statewide |
| Overwhelm Check | Code | Top recs match user capacity | `len(result.grants)` vs capacity rules | Solo first-timer: 1-2, experienced: up to 3 |

#### Tier 2 — Deterministic but more logic

| Scorer | Type | What it checks | Input | Pass condition |
|--------|------|---------------|-------|----------------|
| Dealbreaker Violation | Code | No dealbreaker violated | `result.grants` metadata vs `user.dealbreakers` | No federal if "no federal", no matching if "no matching", etc. |
| Eligibility Check | Code | User qualifies for every rec | `result.grants` requirements vs `user.years_operating`, `user.org_type` | All requirements met |

#### Tier 3 — LLM-as-judge (build after Tier 1-2 are stable, calibrate first)

| Scorer | Type | What it checks | Calibration required |
|--------|------|---------------|---------------------|
| Rationale Specificity | LLM judge | Rationale is specific to this user, not generic | Yes — see calibration plan below |
| Nuance Preservation | LLM judge | User's specific language not flattened to categories | Yes |
| Inference as Fact | LLM judge | Transcriber doesn't assert unconfirmed info | Yes |
| Language Mirroring | LLM judge | Agent uses user's words, not upgraded jargon | Yes |

#### Tier 4 — Hardest to automate (manual review, automate later)

| Scorer | What it checks | Why manual first |
|--------|---------------|-----------------|
| Energy Following | Agent follows user's excitement, not its own agenda | Requires understanding conversational dynamics |
| Tone Matching | Professional for Rachel, encouraging for Margaret | Subjective, needs many annotated examples |

---

### LLM-as-judge calibration plan

**Before any LLM judge is promoted to the automated eval suite, it must pass calibration.**

#### Step 1: Generate the batch
Run all 12 synthetic users through the full pipeline. Save all outputs (Transcriber profiles, Scout recommendations, Scorer verdicts). This is your calibration dataset.

#### Step 2: Manual scoring (Cecilia)
For each output, score the qualitative criteria by hand using a simple rubric:

| Score | Meaning |
|-------|---------|
| 0 | Clear failure — the unacceptable behavior is present |
| 1 | Pass — the behavior is absent or handled well |

Score each criterion independently per user. Record in a spreadsheet or JSON:

```json
{
  "user_id": "user-01",
  "rationale_specificity": 1,
  "nuance_preservation": 1,
  "inference_as_fact": 0,
  "language_mirroring": 1,
  "notes": "Transcriber inferred Title I without checking"
}
```

This is ~12 users x 4 criteria = 48 judgments. Takes 30-60 minutes. Do it once, carefully.

#### Step 3: Run the LLM judge on the same batch
For each criterion, write a judge prompt. Run it against the same 12 outputs. Record the LLM's scores in the same format.

#### Step 4: Measure agreement
Calculate agreement rate: `(LLM matches human) / total` for each criterion.

| Agreement | Action |
|-----------|--------|
| >= 90% | Promote to automated suite |
| 75-89% | Review disagreements, refine judge prompt, re-run |
| < 75% | Judge is unreliable for this criterion — keep as manual review |

#### Step 5: Document disagreements
For every case where LLM != human, write down why. These are the edge cases that teach you what the judge misunderstands. They become examples in the judge prompt (few-shot) for the next calibration round.

#### Step 6: Re-calibrate periodically
Every 5 prompt iterations, re-run calibration. Judge accuracy can drift as prompts change.

---

### CI/CD: GitHub Actions for eval-on-push

The goal: every prompt change is tested before it goes live. No untested prompts reach the demo.

#### Pipeline

```
Push to main (or PR)
    |
    v
GitHub Action triggers
    |
    |-- 1. Load synthetic users
    |-- 2. Run full pipeline (12 users x Transcriber -> Scout -> Scorer)
    |-- 3. Run Tier 1 + Tier 2 scorers
    |-- 4. Upload scores to Braintrust
    |
    v
Check pass/fail gates
    |
    |-- Trap Avoidance: must be 100% (0 trap grants across all users)
    |-- Hit Rate: must be >= 75% (9/12 users get at least 1 correct grant)
    |-- Geographic Precision: must be 100%
    |-- Overwhelm Check: must be >= 90%
    |
    v
If all gates pass -> merge allowed
If any gate fails -> PR blocked, failure details in PR comment
```

#### Implementation

```yaml
# .github/workflows/eval.yml
name: Eval Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run evals
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          BRAINTRUST_API_KEY: ${{ secrets.BRAINTRUST_API_KEY }}
        run: python evals.py --output results.json

      - name: Check gates
        run: python check_gates.py results.json
```

#### Cost control
- Full eval (12 users x 3 agents) costs ~$1.60 per run
- GitHub Actions runs on push to main and on PRs — expect 3-5 runs per development session
- Budget: ~$8-10/day during active development
- If cost is a concern, run a subset (3 users: Maria, David, Angela — covers the most critical failure modes) on PR, full 12 on merge to main

#### When to run full vs. subset
| Trigger | Users | Why |
|---------|-------|-----|
| PR opened/updated | 3 users (Maria, David, Angela) | Fast feedback, catches obvious regressions |
| Merge to main | All 12 users | Full coverage before any deploy |
| Manual trigger | All 12 users | On-demand after prompt changes in Braintrust |

---

### Prompt change protocol

Prompts live in Braintrust, not in code. This means a prompt change doesn't trigger a code push. The protocol:

1. **Change the prompt in Braintrust UI** (one agent at a time)
2. **Run `python evals.py` locally** — see results immediately
3. **Compare to previous run in Braintrust dashboard** — did scores improve, hold, or regress?
4. **If improved:** update the prompt slug in `pipeline.py` if the slug changed (Braintrust versions prompts). Push to GitHub. CI runs eval. Gates pass. Merge.
5. **If regressed:** revert the prompt in Braintrust. No code change needed.

**Rule: one variable at a time.** Never change a prompt AND a scorer in the same eval run. You won't know which caused the score change.

---

## Part 2: Org / Director Level — Rollout & Experimentation Strategy

> Every decision in this section depends on the eval data from Part 1. The IC PM's scorer pass rates justify moving between phases. The calibration data gives confidence to flip feature flags. The cohort analysis only has clean signal because the IC ran disciplined evals. This section is the steering — Part 1 is the engine.

---

### Rollout strategy

How Scout goes from prototype to production without breaking trust. The core principle: every user who sees Scout output is in a controlled experiment, every experiment has a kill switch, and every interaction generates data we can read in cohort analysis.

---

#### Experimentation infrastructure

**Feature flagging** — A feature flag service (Split.io, LaunchDarkly, Statsig — depends on what Instrumentl already uses or prefers) controls who sees Scout at every stage. Flags are not on/off toggles. They control:

- **Which users see Scout** — assignment by cohort (new users, onboarding stage, org type, advisor)
- **Which version of Scout they see** — prompt version, pipeline variant (e.g., with/without Scorer, different thinking budgets)
- **What fallback they get if Scout fails** — degrade gracefully to the current filter-and-scroll experience, never to an error state

```
Feature flags:

scout_enabled            -- master kill switch. Off = no user sees Scout.
scout_cohort             -- which users are in the experiment (by assignment rules below)
scout_pipeline_variant   -- which pipeline version runs (A/B between prompt versions)
scout_advisor_gate       -- whether advisor screens output before user sees it
scout_surface            -- where Scout appears (sidebar, tab, onboarding flow)
```

**Assignment rules:**
- Users are assigned to cohorts at account creation (or at onboarding stage for existing users). Assignment is sticky — once in a cohort, you stay for the duration of the experiment. No mid-experiment reassignment.
- Assignment is by user ID hash, not random per-session. This ensures consistent experience and clean cohort analysis.
- Advisors are not randomized — they opt in during Phase 1. Randomizing advisors before we know the tool works would risk their trust and their users' trust.

**Kill switches:**
- `scout_enabled = false` immediately removes Scout from all surfaces for all users. The "something went very wrong" lever.
- Per-cohort kill: `scout_cohort` rules can disable Scout for a specific segment (e.g., first-time users) without affecting others.
- Automatic kill trigger: if Trap Avoidance drops below 100% on production traces over any 24-hour window, `scout_enabled` flips to `false` and alerts the team. A dealbreaker violation reaching a real user is a severity-1 incident.

**Behavioral early warning system:**

User signals — editing AI outputs, abandoning conversations, contacting support — are your early warning system. These are the signals that tell you something is wrong before a metric moves.

| Signal | What it means | How to capture | Action |
|--------|--------------|----------------|--------|
| **User edits Scout output** (changes a profile field, rewrites rationale) | Scout got something wrong or close-but-not-right. The edit IS the correction. | Log diffs between Scout's output and what the user/advisor changed. | Each edit becomes a labeled example: Scout said X, correct answer was Y. Feed into eval dataset. High edit rate on a specific field = prompt issue for that field. |
| **User abandons mid-flow** (starts pipeline, never acts on results) | Recommendations weren't compelling, or the experience created friction. | Track funnel: pipeline started -> results shown -> grant saved -> application started. Drop-off points are diagnostic. | Cluster abandonment by user profile (org type, experience, geography). If a segment abandons disproportionately, Scout may have a blind spot for that segment. |
| **User contacts support after Scout interaction** | Scout created confusion, gave a bad recommendation, or the user lost trust. | Tag support tickets that occur within 48 hours of a Scout interaction. Capture: what Scout recommended, what the user's complaint was. | Every support ticket tied to a Scout interaction is a potential new eval criterion. Review weekly. If the same complaint appears 3+ times, it becomes a scorer. |
| **Advisor overrides Scout** (Phase 1-2) | Advisor knows something Scout doesn't. The override is domain knowledge. | Structured advisor log captures what was changed and why. | Overrides are the highest-signal feedback. Each one is either a new trap grant, a new scorer rule, or a domain insight the prompt needs to encode. |

**Automated signal processing:**

These signals shouldn't wait for a human to review them. They should be instrumented with thresholds that trigger alerts and surface insights dynamically.

| Signal | Metric | Threshold | Trigger |
|--------|--------|-----------|---------|
| User edits | Edit rate (% of sessions where user modifies Scout output) | > 20% over rolling 7-day window | Alert: "Edit rate elevated — top edited fields: [X, Y]." Auto-clusters edits by field to show where Scout is consistently wrong. |
| Abandonment | Drop-off rate at each funnel stage | > 40% drop between results shown and grant saved | Alert: "Conversion drop — segment breakdown attached." Auto-segments by org type, experience level, geography to isolate which users are dropping. |
| Support contact | Support ticket rate within 48h of Scout interaction | > 5% of Scout sessions result in a ticket | Alert: "Support ticket rate elevated — common themes: [X, Y]." NLP clustering on ticket text to surface repeated complaints without manual reading. |
| Advisor override | Override rate (% of recommendations advisor changes) | > 30% over rolling 7-day window | Alert: "Override rate elevated — top override reasons: [X, Y]." Structured log auto-categorizes override reasons. |

**Escalation logic:**
- Threshold crossed once -> alert to PM + eval owner with auto-generated breakdown (which segments, which fields, which complaint clusters)
- Threshold crossed for 3 consecutive days -> auto-creates a candidate eval criterion (drafted from the clustered signal data) for human review and promotion to the scorer suite
- Any single session with a dealbreaker violation (detected via production trace scoring) -> immediate alert + kill switch review, no threshold needed

**What this replaces:** Manual weekly review. The system surfaces the insight, clusters the pattern, and drafts the eval criterion. A human still approves promoting it to the scorer suite — but the human isn't doing the detection or the analysis. They're making a judgment call on a pre-digested signal.

**Tooling options:** This can live in the observability layer the team already uses (Datadog, Mixpanel, Amplitude — depends on Instrumentl's stack) with alerts piped to Slack or PagerDuty. The key requirement is that event tracking is granular enough to tie user behavior events (edit, abandon, ticket) back to the specific Scout session and pipeline trace in Braintrust.

---

#### Phase 0: Internal quality bar (prototype, now)

No feature flags yet. Synthetic users only. This is where the eval suite gets built.

**What happens:**
- Build Tier 1-2 scorers, establish baseline scores
- Run the development loop until hard gates pass: Trap Avoidance 100%, Geographic Precision 100%, Hit Rate >= 75%
- Calibrate LLM judges against manual scoring
- Wire up CI/CD so every prompt change is eval-gated

**Exit criteria:** All Tier 1 scorers pass consistently across 3 consecutive runs. Braintrust dashboard shows improvement trajectory from baseline.

#### Phase 1: Advisor-only (no user exposure)

```
scout_enabled = true
scout_cohort = advisor_internal_only
scout_advisor_gate = true (advisor sees output, user does not)
```

3-5 onboarding advisors use Scout during 1:1 calls. They paste call notes, see recommendations, and judge whether they'd share the output. The user never sees Scout.

**What we measure:**
- **Advisor trust rate** — % of recommendations the advisor would share. Target: >= 80%.
- **Advisor override rate** — % of recommendations the advisor modifies before they'd share. Baseline measurement.
- **Failure modes** — every "I wouldn't show this" becomes a new eval criterion with the advisor's reasoning attached.
- **Domain knowledge capture** — structured log: advisor notes why a recommendation is wrong in ways the eval suite doesn't yet catch. These become new trap grants or new scorer logic.

**Feedback instrument:** Post-call advisor log (3 fields: what Scout recommended, would you share it, why/why not). Weekly 15-min sync to review patterns.

**Exit criteria:** Advisor trust rate >= 80% sustained over 2 weeks. Zero dealbreaker violations. At least 3 new domain insights encoded as eval criteria.

#### Phase 2: Controlled user exposure (A/B test)

```
scout_enabled = true
scout_cohort = new_users_post_onboarding, 50/50 split
  Control: standard Instrumentl onboarding (filter-and-scroll)
  Treatment: Scout recommendation during advisor 1:1
scout_advisor_gate = true (advisor still screens first)
scout_pipeline_variant = v1 (current best prompt set)
```

This is the first real experiment. New users are assigned 50/50 at account creation. Treatment group gets Scout during their 1:1 advisor call. Control group gets the current onboarding experience. Advisor still screens Scout output before sharing.

**Primary metric:** Time-to-first-grant-saved — how quickly does the user save a grant to their tracker after onboarding?

**Secondary metrics:**

| Metric | What it tells us | How to measure |
|--------|-----------------|----------------|
| Time-to-Yes | Does Scout reduce decision friction? | Interactions before user commits to a grant |
| Grant save rate | Are Scout's recs actionable? | % of shown recs saved to tracker |
| Application start rate | Does saving convert to action? | % of saved grants where user starts application |
| 7-day activation | Does Scout change early engagement? | % of users who return and take action within 7 days |
| Advisor override rate | Is Scout getting better? | Should trend down from Phase 1 |

**Cohort analysis we need:**
- Treatment vs. control on all metrics above, segmented by: org type, team size, grant experience level, advisor
- Within treatment: per-user funnel (recommendation shown -> saved -> application started -> application submitted)
- Advisor-level: does Scout performance vary by advisor? (Reveals whether the advisor's framing matters more than the recommendation itself)

**Guardrail metrics (if any regress, pause the experiment):**
- NPS / CSAT on onboarding call — Scout must not make the call feel worse
- Support ticket rate in first 14 days — Scout must not create confusion
- Trap Avoidance on production traces — must stay 100%

**Sample size:** Depends on baseline conversion rates (need to understand current time-to-first-grant-saved distribution). Directionally: ~100 users per arm for 80% power on a 15% relative lift in grant save rate. Size properly with the data team before starting.

**Exit criteria:** Statistically significant lift on primary metric (p < 0.05). No guardrail regression. Clean cohort data showing the effect holds across org types and experience levels, not just for one segment.

#### Phase 3: Expanded rollout (ramp)

```
scout_cohort = new_users_post_onboarding, ramped 10% -> 25% -> 50% -> 100%
scout_advisor_gate = false (Scout output shown directly, advisor optional)
scout_surface = [wherever the team decides]
```

Controlled ramp, not a flip. Feature flag ramps exposure: 10% of new users -> watch metrics for 1 week -> 25% -> watch -> 50% -> watch -> 100%. At each step, compare the new cohort's metrics to the prior cohort and to control. If any step regresses, hold at current percentage and diagnose.

**What changes:**
- Advisor gate comes off — Scout presents directly to users. This is the biggest trust boundary crossing.
- Production traces feed the eval suite continuously. Every session is scored by Tier 1-2 scorers automatically.
- New failure modes emerge at scale: ambiguous missions, multi-project orgs, non-English input, edge-case geographies. Each becomes a new eval criterion.
- LLM judges re-calibrate against real advisor/user feedback, not just manual scoring from Phase 0.

**Regression monitoring:**
- Automated: Tier 1-2 scorers run on every production trace. Score drops trigger alerts.
- Weekly: Manual review of a random sample of 20 production traces (the "Observe" step never stops).
- Monthly: Re-run full synthetic user eval to check for prompt drift.

**Prompt A/B testing in production:** Once Scout is live, `scout_pipeline_variant` splits traffic between prompt versions. Each variant's traces flow to Braintrust, scored identically. This closes the loop:

```
Prompt A/B test flow:

Braintrust: new prompt candidate
    |
    v
CI/CD: eval gates pass on synthetic users
    |
    v
Feature flag: scout_pipeline_variant = { A: current (90%), B: candidate (10%) }
    |
    v
Production traces scored for both variants
    |
    v
If B >= A on primary metrics + no guardrail regression -> promote B to 100%
If B < A -> revert flag, candidate goes back for iteration
```

#### Phase 4: The learning flywheel

At scale, every user interaction generates signal:

```
User reacts to recommendation
    |
    |-- Saved -> positive signal (correct_grant candidate)
    |-- Skipped -> weak negative (maybe wrong, maybe later)
    |-- Applied -> strong positive (the real outcome)
    |-- Complained / contacted support -> strong negative (new trap_grant candidate)
    |
    v
Signals feed back into:
    |-- Eval dataset (real sessions replace/supplement synthetic users)
    |-- Scorer calibration (LLM judges validated against real outcomes)
    |-- Prompt iteration (development loop continues, informed by production data)
    |-- Cohort analysis (which segments benefit most -> informs roadmap)
```

The eval suite becomes a knowledge base. The feature flag system enables continuous experimentation. The cohort data tells you not just "does Scout work" but "for whom, under what conditions, and how much." That's the data you need to make roadmap decisions — should Scout expand to multi-project teams? To power users? To the Apply workflow? The cohort analysis answers those with data, not guesses.

---

### Build phases (engineering sequence)

| Build step | Rollout phase | What |
|-----------|---------------|------|
| 1 | Phase 0 | Build Tier 1 scorers, establish baseline |
| 2 | Phase 0 | Prompt iteration loop until hard gates pass |
| 3 | Phase 0 | Build Tier 2 scorers |
| 4 | Phase 0 | LLM judge calibration |
| 5 | Phase 0 | Wire up GitHub Actions CI |
| 6 | Phase 1 | Add advisor feedback logging, integrate feature flag service |
| 7 | Phase 1-2 | Build real-user eval dataset from advisor logs |
| 8 | Phase 2 | Instrument A/B test: assignment, event tracking, cohort tagging |
| 9 | Phase 2-3 | Production trace scoring (automated, continuous) |
| 10 | Phase 3 | Prompt A/B testing via feature flag variants |
| 11 | Phase 3+ | Expand eval dataset from production, re-calibrate judges |

---

### What the Instrumentl team sees

1. **The eval suite is the moat, not the AI** — every production interaction encodes knowledge a competitor can't replicate by copying the code
2. **Controlled experimentation, not "ship and hope"** — every user is in a cohort, every cohort is measured, every experiment has a kill switch
3. **User protection first** — automatic kill triggers on safety metrics, advisor gate before direct exposure, graceful degradation to existing experience
4. **Data-driven expansion** — ramp percentages are informed by metrics at each stage, not by a timeline
5. **Cohort analysis that informs strategy** — not just "does it work" but "for whom, how much, and what should we build next"
6. **The honest kill criterion** — if the 3 thesis-validating scorers (dealbreaker, overwhelm, specificity) fail consistently, the honest answer is the product isn't ready. Knowing that in month 2 is more valuable than discovering it in month 8 after over-investing.
7. **Process a PM can hand to engineering on day one** — feature flags, assignment rules, metrics, exit criteria, kill switches, knowledge ingestion paths. Not a vision doc — an operating plan.
