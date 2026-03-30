## Tech Architecture: Scout Prototype

### The three-agent pipeline

```
User (browser)
    │
    ▼
┌─────────────┐     confirmed      ┌─────────┐     draft recs     ┌────────┐     approved recs
│ Transcriber │ ──── profile ────► │  Scout  │ ────────────────► │ Scorer │ ────────────────► User sees results
│             │                    │         │                   │        │
│ Summarizes  │                    │ Searches│                   │ Checks │
│ call notes  │                    │ grants  │                   │ Scout's│
│ into        │                    │ Ranks   │                   │ work   │
│ profile     │                    │ Writes  │                   │        │
│             │                    │ rationale│                  │ Pass/  │
└─────────────┘                    └─────────┘                   │ Fail   │
                                                                 └────────┘
```

**Transcriber** — Receives call notes from the advisor (pasted into the intake form after or during the 1:1 call). Extracts a structured profile. If critical fields are missing, asks only the specific questions needed. Does not recommend grants.

**Scout** — Receives the confirmed profile. Searches the grant database (pre-filtered to user's state + national). Filters out dealbreakers, geographic mismatches, eligibility failures. Ranks what remains. Produces up to 3 draft recommendations with full rationale, plus up to 2 near-misses (5 total max). Does not present to the user.

**Scorer** — Receives the profile AND Scout's draft recommendations. Runs every recommendation through a checklist: geographic check, eligibility check, dealbreaker check, nuance check, language check, overwhelm check. If all pass → approved, presented to user. If any fail → rejected, Scout tries again.

The user never knows the Scorer exists. They just experience recommendations that are always right.

### The stack

```
Streamlit Web App (Python)
    │
    ├── Fetches 3 prompts from ──► Braintrust (prompt store)
    │   (transcriber-prompt, scout-prompt, scorer-prompt)
    │
    ├── Calls ──► Claude API (console.anthropic.com)
    │                3 separate calls per pipeline run
    │
    ├── Reads ──► grants.json (loaded at startup)
    │
    ├── Logs traces to ──► Braintrust (full pipeline traced)
    │
    └── Stores state in ──► Streamlit session_state
```

### Components

**1. Streamlit app (`app.py`)**
- Intake form: advisor pastes call notes into a structured template (org, location, mission, dealbreakers, etc.)
- One-shot flow: paste notes → click "Find Grants" → pipeline runs → results appear
- Session state holds: pipeline phase (intake / searching / follow_up / searching_with_answers / results / grant_detail / explore / apply), confirmed profile, approved grants, chat history
- Progress bar with single-line snippets: shows pipeline stage (transcriber → filter → scout → scorer → done) and samples short insights from Scout's thinking every few seconds
- Results page: grant cards with rationale + "Apply" and "Learn more" buttons + "See all results" link + follow-up chat
- Learn More page: mock grant detail page showing full grant info from grants.json (funder, description, eligibility, focus areas, geographic scope, etc.)
- Explore All page: mock search results page with all grants and filters (geographic match, grant size)
- Apply page: mock application with profile fields pre-filled by Scout
- No login, no auth, no database

**2. Three Braintrust prompts + one hardcoded prompt**
- `transcriber-prompt-3997` — profile extraction from call notes
- `scout-prompt-7867` — grant search, ranking, rationale writing (uses extended thinking)
- `scorer-prompt-e86a` — quality gate, checklist verification
- Each updated independently in Braintrust UI — no code redeploy
- Fetched at runtime via `braintrust.load_prompt(project="Scout", slug=...)`
- `CHAT_SYSTEM_PROMPT` — hardcoded in `pipeline.py`, powers follow-up chat after results are shown. Not in Braintrust because it's a simple conversational prompt that doesn't need iteration.

**3. Claude API**
- Model: claude-sonnet-4-20250514 for all three agents
- Three calls per pipeline run:
  1. Transcriber: system prompt + call notes → structured profile
  2. Scout: system prompt + confirmed profile + grants.json → draft recommendations (with extended thinking, 15K token budget)
  3. Scorer: system prompt + confirmed profile + draft recommendations → approve/reject
- If Scorer rejects, Scout is called again with feedback (max 2 retries)
- Scout streams thinking tokens; app samples short snippets for the progress display. Scorer streams text tokens (not shown to user, used for verdict parsing only)

**4. Grant data (`data/grants.json`)**
- 125 grants (35 real from GrantWatch + 90 synthetic)
- Loaded at startup, passed to Scout as context
- Not passed to Transcriber or Scorer (they don't need it)

**5. Braintrust tracing + evals**
- Full pipeline traced via `wrap_anthropic`: Transcriber, Scout, Scorer calls all logged
- Eval scorers (not yet built) will run against pipeline output — see spec section 4
- Two types of scorers planned:
  - Rule-based: trap grant avoidance, geographic precision, recommendation count, dealbreaker violations
  - LLM-as-judge: nuance flattening, language mirroring, tone matching, rationale quality
- Production traces from live sessions will feed back into the eval dataset

### Intake flow: v1 (now) vs. v2 (with live transcription)

**v1 — Call notes (what's built)**
```
Advisor has 1:1 call with user
    │
    ▼
Advisor pastes call notes ──► Transcriber extracts profile ──► Scout + Scorer
into intake form                                                pipeline runs
```

The advisor fills in what they heard during the call — org name, mission, dealbreakers, etc. — in whatever format or level of completeness they have. Transcriber synthesizes messy notes into a structured profile. This works now and is the version used for testing and demo.

**v2 — Live transcription (planned)**
```
Advisor has 1:1 call with user
    │
    ├── AssemblyAI (or equivalent) joins call as listener
    │   streams real-time transcript
    │
    ▼
Live transcript ──► Transcriber builds profile ──► Profile shown on
feeds in                in real time                  advisor's screen
continuously                                          for confirmation
    │
    ▼ (advisor confirms profile)
Scout + Scorer pipeline runs
```

In v2, the advisor doesn't paste anything. A transcription service (AssemblyAI, Deepgram, or browser mic + Whisper) listens to the call and streams the transcript to the Transcriber agent in real time. The advisor and user see the structured profile building on screen as they talk — not raw transcription, but the agent's synthesis ("Mission: after-school STEM programs for underserved communities"). The advisor pauses, the user confirms or corrects, and Scout runs.

This is the experience described in the product spec (Section 2, steps 2-6): "the agent connects to the call audio... a clear visual indicator shows when the agent is listening... the agent shows a structured profile building in real time."

**What v2 adds to the stack:**
```
AssemblyAI Real-Time API (or equivalent)
    │
    ├── WebSocket connection from browser
    ├── Streams partial transcripts as user speaks
    ├── Transcriber receives chunks, updates profile incrementally
    └── Profile panel updates live on advisor's screen
```

### File structure

```
scout/
├── docs/
│   ├── build/
│   │   ├── architecture.md            # This file
│   │   ├── model-spec-transcriber.md  # How Transcriber behaves
│   │   ├── model-spec-scout.md        # How Scout behaves
│   │   ├── model-spec-scorer.md       # How Scorer behaves
│   │   └── test-plan.md               # 25 manual test scenarios for testers
│   └── strategy/
│       ├── spec.md                    # Product spec
│       └── playbook.md               # How we operate: eval loop, rollout, CI/CD
│
├── thinking/
│   ├── research.md
│   ├── reflection.md
│   ├── questionnaire.md               # Conversation guide for agents
│   └── working-notes.md
│
├── app/
│   ├── app.py                         # Streamlit app (entry point + UI)
│   ├── pipeline.py                    # All three agents + orchestration
│   └── .env                           # API keys (gitignored)
│
└── data/
    ├── grants.json                    # 125 grants (35 real + 90 synthetic)
    └── synthetic-users.json           # 12 synthetic user profiles
```

### How the pieces connect at runtime

**User flow (what happens when someone uses the app):**
```
Phase 1 — Intake
1. User (advisor) opens Streamlit app
2. Advisor pastes call notes into the intake template
3. Clicks "Find Grants"

Phase 2 — Pipeline (behind the scenes, shown via progress bar + snippets)
4. App fetches transcriber-prompt from Braintrust
5. Transcriber receives call notes, extracts structured profile
6. App fetches scout-prompt, loads grants.json (pre-filtered to user's state + national)
7. Scout receives profile + grants → searches with extended thinking → produces draft recs
8. If Scout has follow-up questions → shown to advisor → answers appended to profile → Scout re-runs with allow_follow_up=False
9. App fetches scorer-prompt
10. Scorer receives profile + Scout's recs → runs checklist
11. If all high confidence → Scorer skipped, results shown directly
12. If medium/low → Scorer reviews. If rejected → Scout retries with feedback (max 2)
13. Full pipeline traced to Braintrust

Phase 3 — Results
14. Approved recommendations displayed with full rationale
15. Each grant has "Apply" and "Learn more" buttons
16. "Learn more" opens a mock grant detail page with full info from grants.json
17. "See all results" opens a mock search page with all grants + geographic/size filters
18. Follow-up chat available — user can ask about grants, adjust criteria
19. "Start new search" resets everything
```

**Eval flow (testing synthetic users):**
```
1. evals.py loads synthetic-users.json
2. For each synthetic user:
   a. build_call_notes() constructs advisor-style notes from the user profile
   b. Transcriber extracts structured profile from call notes
   c. Scout searches and recommends (allow_follow_up=False)
   d. Scorer evaluates (if triggered by Medium confidence)
   e. Tier 1 scorers check pipeline output:
      - Trap Avoidance: did Scout recommend any trap_grants? (0 allowed)
      - Hit Rate: did Scout recommend at least 1 correct_grant?
      - Overwhelm Check: max 3 recommendations + max 2 near-misses (5 total)
   f. Logs scores to Braintrust via braintrust.Eval()
3. Results visible in Braintrust dashboard: per-scorer scores, per-user pass rates
4. Tier 2 scorers (geographic precision, dealbreaker violation, nuance flattening,
   language mirror) — candidates to promote after Tier 1 error analysis
```

### Dependencies

```
# requirements.txt (to be created before deployment)
streamlit
anthropic
braintrust
autoevals
python-dotenv
```

### API keys needed

| Key | Source | Where to get it |
|-----|--------|----------------|
| `ANTHROPIC_API_KEY` | console.anthropic.com | Settings → API Keys |
| `BRAINTRUST_API_KEY` | braintrust.dev | Settings → API Keys |

Both go in `.env` file (gitignored). For Streamlit Cloud, these move to Streamlit secrets management.

### Cost estimate

Three Claude calls per pipeline run (Transcriber + Scout + conditional Scorer). A 4th call happens if the user asks follow-up questions in the chat after results. Scout uses extended thinking (15K token budget).

| Activity | Estimated tokens | Cost (Sonnet) |
|----------|-----------------|---------------|
| 1 demo conversation (full pipeline) | ~40K tokens | ~$0.15 |
| 1 eval run (12 users × full pipeline) | ~480K tokens | ~$1.60 |
| 30 eval iterations | ~14.4M tokens | ~$48 |
| Buffer for prompt testing, debugging | ~3M tokens | ~$10 |
| **Total prototype** | **~18M tokens** | **~$60** |

### Hosting

**Development:** `streamlit run app/app.py`
**Production:** Streamlit Community Cloud (free), connects to GitHub repo, shareable URL

### How we actually built this

| Step | What | Status |
|------|------|--------|
| 1 | Set up accounts (Anthropic, Braintrust) + repo + `.env` | Done |
| 2 | Wrote 3 prompts in Braintrust (transcriber, scout, scorer) | Done |
| 3 | Built `pipeline.py` — all three agents + orchestration in one file | Done |
| 4 | Built `app.py` — Streamlit UI with intake form, progress bar, results page | Done |
| 5 | Added streaming: Scout thinking sampled as progress snippets, Scorer streams for parsing | Done |
| 6 | Added conditional Scorer: high confidence skips Scorer, medium/low triggers quality check | Done |
| 7 | Added follow-up questions: Scout can ask before committing to recommendations | Done |
| 8 | Added follow-up chat: user can ask about grants after results are shown | Done |
| 9 | Added Apply page: mock application with profile fields pre-filled | Done |
| 10 | Polished UI: brand colors, grant card formatting, metadata line breaks | Done |
| 11 | Created test plan: 25 manual scenarios across 12 synthetic users | Done |
| 12 | Wire up Braintrust eval runner (`evals.py`) with Tier 1 scorers (trap avoidance, hit rate, overwhelm check) | Done |
| 13 | Added Learn More page: mock grant detail page with full grant info | Done |
| 14 | Added Explore All page: mock search results with geographic/size filters | Done |
| 15 | Added 25 San Diego County grants for higher ed / student affairs demo (125 total) | Done |
| 16 | Run evals → manual error analysis → decide Tier 2 promotions → update prompts → re-run | Next |
| 17 | Push to GitHub + deploy to Streamlit Cloud | Done |
| 18 | Add live transcription (AssemblyAI or equivalent) for v2 intake flow | Future |
