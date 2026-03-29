## Eval Plan: How we measure Scout

The model can have a great conversation. Cecilia's job is making sure it has the *right* conversation. The evals are the product.

---

### Unacceptables

These are failures the agent must never commit. Each maps to a real user pain point from Capterra feedback, the white glove consultant standard, or patterns discovered in the grant data.

#### Trust breakers
- [ ] Agent dismisses or ignores a stated criterion without compassionately prompting ("Are you sure? Here's why I ask...")
- [ ] Agent flattens nuance into generic tags — e.g., treating "fatherhood initiative" as "family services" or "animal welfare" as "environment"
- [ ] Agent presents a grant that violates a stated dealbreaker (e.g., federal reporting when user said no federal)
- [ ] Agent makes client feel they lost the ability to talk to a human (they love Instrumentl's customer support and would feel a loss if they think the human has been replaced)

#### Overwhelm recreators
- [ ] Agent surfaces more than 5 opportunities in a single interaction without user asking for more
- [ ] Agent delivers a list without rationale — just names and deadlines, no "why this matters to you"
- [ ] Agent pings/nudges when user has indicated they're in a quiet phase

#### Comprehension failures
- [ ] Agent asks the user to re-explain something it should already know from their history
- [ ] Agent gives a generic summary that could apply to any nonprofit ("you care about making an impact")
- [ ] Second interaction feels identical to the first — no evidence of learning

#### White glove violations
- [ ] **Agent infers and states as fact without checking.** "So you work with Title I schools" — but they don't. The agent inferred and presented it as truth instead of asking. This is the worst one because it destroys the "you understand me" moment. It becomes "you think you understand me and you're wrong."
- [ ] **Agent follows its own agenda instead of the client's energy.** Client gets excited about the coding lab, agent pivots back to "tell me more about your after-school programs" because that's the "main" program. The consultant follows the energy. The agent follows the prompt.
- [ ] **Agent asks more than it needs to.** Five questions is an interview. Three is a conversation. The agent should synthesize from minimal input. If it keeps asking, the client feels like they're filling out a form with extra steps.
- [ ] **Agent overwhelms with its own knowledge.** "There are 47 foundations in your area that fund education" — the client didn't ask for a number. They asked for help. Showing off the database is the opposite of white glove.
- [ ] **Agent uses jargon the client didn't use first.** If the client didn't say "LOI," the agent doesn't say "LOI." If the client said "grant letter," the agent says "grant letter." Mirroring language is how trust works.
- [ ] **Agent gives a recommendation without showing its reasoning.** "You should apply for the Johnson Foundation grant" — why? The consultant always says why. "Because they funded two orgs like yours last year, their check size matches what you need, and the deadline gives you enough time." No black boxes.
- [ ] **Agent treats all criteria as equal weight.** The client said "ideally local, definitely no federal, and we prefer under $50K." "Definitely no federal" is a hard constraint. "Ideally local" is a preference. "Prefer under $50K" is flexible. The agent must distinguish between dealbreakers and nice-to-haves — and if unsure, ask: "when you say ideally local, would you consider a regional funder if everything else was perfect?"
- [ ] **Agent doesn't know when to stop.** The consultant says "I think these 2 are your best bet right now" and stops. The agent wants to be helpful and keeps going — "also here's a third, and a fourth, and by the way have you considered..." That's overwhelm in a friendly voice.

**[Cecilia to add]**: more eval criteria as we build

---

### Metrics

| Metric | What it proves |
|--------|---------------|
| **Time-to-Yes** | How many interactions before the user commits to pursuing a specific grant. Goal is 1. |
| **Time-to-First-Value** | How quickly does the agent say something the user didn't explicitly state but is true about them? |
| **Hit Rate@3** | Of the grants surfaced, did at least 1 make the user say "yes"? |
| **Precision@3** | Of the grants surfaced, how many were genuinely relevant? |
| **Trap Avoidance** | Agent never recommends a grant that violates a stated dealbreaker or geographic mismatch. |
| **Overwhelm Index** | User never sees >5 items, never gets an unexplained list. Binary pass/fail. |

---

### Synthetic users (12 profiles in `data/synthetic_users.json`)

Each user is designed to stress-test specific failure modes:

| User | Key test | Communication style |
|------|----------|-------------------|
| Maria (Austin, TX) | Jargon mirroring, dealbreaker detection | Warm, fast-talking, Spanglish |
| David (RI) | Terse user, doesn't over-ask | Minimal, efficient |
| Patricia (IN) | Extracts signal from rambling | Verbose, tells backstories |
| James (IN) | Protects from false hope, hidden disqualifiers (2yr org) | Nervous, non-standard language |
| Sandra (Oakland, CA) | Doesn't flatten nuance, handles pushback | Confident, direct, will challenge |
| Tom (TN) | Navigates contradictions | Laconic, dry humor |
| Rachel (CT) | Matches expert pace, doesn't over-explain | Professional grant writer |
| Angela (Philadelphia) | Fatherhood-initiative test, same-state-wrong-county | Passionate, frustrated by miscategorization |
| Margaret (IL) | Builds confidence, never makes client feel stupid | Apologetic, self-deprecating |
| Kevin (FL) | Handles skepticism, earns trust through accuracy | Skeptical, needs convincing |
| Lisa (San Marcos, CA) | Cross-category missions, same-state-wrong-city | Enthusiastic, jumps between topics |
| Robert (MN) | Non-western frameworks, resists categorization | Thoughtful, measured, long pauses |

Each user has **correct grants** (what the agent should recommend) and **trap grants** (what looks right but violates a dealbreaker — geographic mismatch, eligibility mismatch, population mismatch). The traps are where the evals catch failures.

---

### How evals map to the three-agent pipeline

Each agent is evaluated separately AND as part of the full pipeline:

**Transcriber evals:**
- Did it mirror the user's language? (Language Mirror)
- Did it state an inference as fact? (Inference Check)
- Did it ask more than 3 direct questions? (Question Count)
- Did it flatten nuance into generic categories? (Nuance Check)
- Did it follow the user's energy or redirect to its own agenda? (Energy Check)
- Did it produce a complete, accurate profile? (Profile Completeness)

**Scout evals:**
- Did it recommend correct_grants? (Hit Rate)
- Did it recommend any trap_grants? (Trap Avoidance)
- Did it recommend a grant outside the user's geography? (Geographic Precision)
- Did it recommend a grant the user is ineligible for? (Eligibility Check)
- Did it include rationale for each recommendation? (Rationale Check)
- Did it recommend more than 2 grants? (Overwhelm Check)

**Scorer evals:**
- Did the Scorer catch geographic mismatches Scout missed? (Scorer Catch Rate)
- Did the Scorer catch eligibility failures Scout missed? (Scorer Catch Rate)
- Did the Scorer catch dealbreaker violations Scout missed? (Scorer Catch Rate)
- Did the Scorer let through a bad recommendation? (Scorer Miss Rate — this should be 0)

**Retry loop evals:**
- When the Scorer rejected, did Scout improve on the retry? (Retry Improvement Rate)
- Did Scout's retry address the specific feedback from the Scorer? (Feedback Incorporation)
- After max retries, if still rejected, did the user see a clean no-match message instead of internal rejection output? (Graceful Failure)

**Pipeline evals (end to end):**
- Time-to-Yes: how many interactions before the user gets a recommendation they'd pursue?
- Final recommendations shown to user: were they all genuinely good? (End-to-End Precision)

### How evals run (Braintrust)

See `architecture.md` for the full technical implementation. The loop:

1. Load synthetic users from `data/synthetic_users.json`
2. For each user, run the full pipeline: Transcriber → Scout → Scorer
3. Score each agent independently AND the full pipeline output
4. Catch new failures not yet in the eval suite
5. Add those as new scorers
6. Re-run, show improvement

**The demo story:** "I built synthetic users, ran them through a three-agent pipeline, watched each agent fail in different ways, added those failures to my eval suite, and improved each agent's prompt. Here's the loop."

Out of scope but should happen next: repeat with real users.
