## Backlog — parked ideas, alternative user journeys, future directions

These are ideas and explorations from the design process that are out of scope for the prototype but worth returning to.

---

### Alternative user journeys (not building these)

**Experience B — "React, don't generate" (cold-start onboarding for new users)**
Show 3-4 real grants, ask "would you look into this or skip?" Follow-up: "what made you say no?" After a few rounds, agent mirrors what it learned. Best cold-start solution for new users. Park for v2 — we scoped to the first-grant user deliberately.

**Experience D — "Just talk to me" (voice-first input)**
Voice-first. User talks like they would to a colleague. Agent listens, then synthesizes. Right long-term vision, wrong prototype scope. Conversation design needs to work in text first. Shared office problem. Mention as future direction.

---

### Product ideas (not building these)

**Grant-Win Activation Trigger (Rank #4)**
Scout appears when user marks a grant as awarded — peak confidence, peak trust. "Congrats. Based on what made this one work, here are 2 more." Inspired by Cecilia's Ember experience (foundation lady said "find another PTA" at peak moment). Brilliant product insight about timing and psychology, but it's a product/timing decision, not an AI demo. A rule-based system could trigger on a status change. Belongs as a design recommendation in a presentation, not the prototype centerpiece.

**React-Then-Ask Onboarding / WHOOP pattern (Rank #5)**
Show value before asking questions. Observe first, then ask contextual questions tied to something the user can already see. Strong UX pattern from WHOOP's calibration phase. Best for new users, we scoped to first-grant users.

**Voice-First Input (Rank #6)**
Users talk naturally instead of typing. Captures nuance, energy, things people say when not filling out a form. Right instinct but conversation design needs to work in text first. Solve what the agent says before choosing the modality.

**Daily Scout / Proactive Monitoring (Rank #7)**
Agent monitors new grant postings daily, surfaces opportunities on a rhythm the user sets. The "scouting" part of the original vision. Valuable in production, but requires real data pipeline and database. Can't meaningfully prototype without their infrastructure. Mention as the vision, don't build it.

**Delight-to-Referral Loop (Rank #8)**
At peak delight (grant win or great recommendation), prompt user to invite a colleague. Cecilia's prior company: referral ask at peak delight was a goldmine. Growth insight, not a prototype feature. Include in presentation as evidence of full business loop thinking.

---

### Saved design questions

- **Trigger to delight loop**: The best moment to ask for deeper engagement is at peak delight. At Cecilia's previous company, this was a goldmine for referrals. Where is the equivalent moment in the scout flow? Hypothesis: the scout's recommendation leads to a grant win → that's when you ask "want to invite a colleague to try this?"
- **How does Instrumentl capture the award moment today?** Great question to ask the team. They have post-award management features (task assignment, reminders, spend-down tracking), so a status change exists.
- **Voice input**: Do we include in v1 prototype? The target user may not be comfortable with chat, but also may be in a shared office. Park for now — focus on the conversation design first, modality second.
- **Option 1 — AI assists CS**: The agent sits behind the CS person during onboarding. The user says something about their org, the agent whispers to the CS person with domain-expert suggestions. The human stays in the loop, the trust stays with the human, the AI adds the domain knowledge. Different product surface than the scout, but related.

---

### Metrics we'd track in production but can't demo

- D7/D30 retention after first scout interaction
- Submission velocity change (does 2/month go to 3/month?)
- Second-bite rate: does the user come back and ask the scout for more?
- Referral trigger: does the win → scout → win loop become the moment users refer colleagues?

---

### Research references

**WHOOP product metrics:**
- 50%+ daily usage 18+ months post-purchase
- 85% annual renewal target
- 4-day calibration phase → Strain Coach on Day 5, Sleep Coach on Day 7 (time-to-insight framework)
- WHOOP Coach (GPT-4) = "search engine for your body"
- 10% lift in cross-sell conversions within 6 weeks of AI Decisioning

**AI consumer app benchmarks:**
- Noom: 43.6% D30 engagement, 77.8% 4+ week retention, engagement directly predicts outcomes
- Calm/Headspace: 8-16% 30-day retention, monetize retained users effectively
- Stickiness ratio (DAU/MAU) is primary health metric
- Task completion rate benchmark for AI agents: 75-80%

**Recommendation system metrics (Evidently AI framework):**
- Precision@K, Recall@K, Hit Rate@K for relevance
- MRR, MAP, NDCG for ranking quality
- Diversity, Novelty, Serendipity for discovery/trust

## Original eval thinking — 19 unacceptable behaviors (archived)

This was the original eval design before we converged on Hamel's "start with 3-5 most critical" approach. Preserved here for reference — these are real failure modes we identified and may promote to scorers later as error analysis reveals which ones actually fire.

The 3 scorers we shipped in `evals.py` (trap avoidance, hit rate, overwhelm check) came from narrowing this list to what matters most for the prototype. The rest lives here, not in the spec.

### Original unacceptables (19 across 4 categories)

#### Trust breakers
- Agent dismisses or ignores a stated criterion without compassionately prompting ("Are you sure? Here's why I ask...")
- Agent flattens nuance into generic tags — e.g., treating "fatherhood initiative" as "family services" or "animal welfare" as "environment"
- Agent presents a grant that violates a stated dealbreaker (e.g., federal reporting when user said no federal)
- Agent makes client feel they lost the ability to talk to a human (they love Instrumentl's customer support and would feel a loss if they think the human has been replaced)

#### Overwhelm recreators
- Agent pushes more top recommendations than the user's capacity warrants — a solo first-timer should see 1-2, an experienced grant writer might see 3. The number of top picks should match what the user can realistically act on, based on team size, budget, and experience. Additional strong-fit grants belong in the bench ("worth keeping an eye on"), not the top picks.
- Agent delivers a list without rationale — just names and deadlines, no "why this matters to you"
- Agent pings/nudges when user has indicated they're in a quiet phase

#### Comprehension failures
- Agent asks the user to re-explain something it should already know from their history
- Agent gives a generic summary that could apply to any nonprofit ("you care about making an impact")
- Second interaction feels identical to the first — no evidence of learning

#### White glove violations
- Agent infers and states as fact without checking. "So you work with Title I schools" — but they don't. The agent inferred and presented it as truth instead of asking.
- Agent follows its own agenda instead of the client's energy. Client gets excited about the coding lab, agent pivots back to "tell me more about your after-school programs."
- Agent asks more than it needs to. Five questions is an interview. Three is a conversation.
- Agent overwhelms with its own knowledge. "There are 47 foundations in your area that fund education" — the client didn't ask for a number.
- Agent uses jargon the client didn't use first. If the client didn't say "LOI," the agent doesn't say "LOI."
- Agent gives a recommendation without showing its reasoning.
- Agent treats all criteria as equal weight. Must distinguish between dealbreakers and nice-to-haves.
- Agent doesn't know when to stop. The consultant reads the client's capacity and gives them only what they can act on.

### Original per-agent eval matrices

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
- Did the number of top recommendations match the user's capacity? (Overwhelm Check)

**Scorer evals:**
- Did the Scorer catch geographic mismatches Scout missed? (Scorer Catch Rate)
- Did the Scorer catch eligibility failures Scout missed? (Scorer Catch Rate)
- Did the Scorer catch dealbreaker violations Scout missed? (Scorer Catch Rate)
- Did the Scorer let through a bad recommendation? (Scorer Miss Rate — should be 0)

**Retry loop evals:**
- When the Scorer rejected, did Scout improve on the retry? (Retry Improvement Rate)
- Did Scout's retry address the specific feedback from the Scorer? (Feedback Incorporation)
- After max retries, if still rejected, did the user see a clean no-match message? (Graceful Failure)

### Original metrics (6)

| Metric | What it proves |
|--------|---------------|
| **Time-to-Yes** | How many interactions before the user commits to pursuing a specific grant. Goal is 1. |
| **Time-to-First-Value** | How quickly does the agent say something the user didn't explicitly state but is true about them? |
| **Hit Rate@3** | Of the grants surfaced, did at least 1 make the user say "yes"? |
| **Precision@3** | Of the grants surfaced, how many were genuinely relevant? |
| **Trap Avoidance** | Agent never recommends a grant that violates a stated dealbreaker or geographic mismatch. |
| **Overwhelm Index** | Top recommendations match user's capacity. No unexplained lists. |

---

## Product Ideas — Ranked

Ranking criteria:
- **WHY**: Demonstrate to Instrumentl's EPD team that Cecilia cares about the customer, can build with new systems, has good taste, and thinks in systems
- **WHAT**: The customer's core pain is overwhelm and the gap between how they think about their needs and how the system requires them to express those needs

| Rank | Idea | What it is | Why this rank |
|------|------|-----------|---------------|
| **1** | **The Conversation Engine** | Agent takes messy, unstructured human input and builds a richer profile than any filter system could. Demo moment: the agent mirrors back what it understood and the user thinks "how did you get that from what I said?" | This IS the AI magic. The thing no filter-based system can do. Directly solves the core pain. Strongest demo of taste because the evals are the product. Buildable without their database. |
| **2** | **Eval Framework + Synthetic Users** | Testable system that runs synthetic user conversations through the agent and checks for 19 unacceptable behaviors — wrong inferences stated as fact, jargon the client didn't use, flattening nuance into tags, etc. | Proves #1 works. Anyone can build a chatbot that sounds good in a cherry-picked demo. The framework that catches failures separates PM thinking from prompt engineering. Shows Angela's team "I know how to ship this safely." |
| **3** | **White Glove Standard** | Documented spec of what the best human grant consultant actually does — follows energy not checklists, synthesizes in 30 seconds, protects client from overcommitting, mirrors language, remembers everything. Becomes the rubric for the agent. | The design artifact that makes #1 and #2 credible. Every eval traces back to "this is how the best human does it." Customer empathy grounded in real behavior, not assumptions. |
| **4** | **Grant-Win Activation Trigger** | Scout appears when user marks a grant as awarded — peak confidence, peak trust. "Congrats. Based on what made this one work, here are 2 more. We've already started." Inspired by Cecilia's Ember experience (foundation lady said "find another PTA" at peak moment). | Brilliant product insight about timing and psychology. But it's a product/timing decision, not an AI demo. A rule-based system could trigger on a status change. Belongs as a design recommendation, not the prototype centerpiece. |
| **5** | **React-Then-Ask Onboarding (WHOOP pattern)** | Show 3-4 real grants, ask "would you look into this or skip?" Follow-up: "what made you say no?" After a few rounds, agent mirrors what it learned. | Strong UX pattern, solves cold-start for new users. But we scoped to returning users to avoid cold start. Great v2 idea for new user onboarding. |
| **6** | **Voice-First Input** | Users talk naturally instead of typing. Captures nuance, energy, things people say when not filling out a form. | Right instinct — voice captures what typing flattens. But conversation design needs to work in text first. Solve what the agent says before choosing the modality. |
| **7** | **Daily Scout / Proactive Monitoring** | Agent monitors new grant postings daily, surfaces opportunities on a rhythm the user sets. | The "scouting" part of the original vision. Valuable in production, but requires real data pipeline and database. Can't meaningfully prototype. Mention as the vision, don't build it. |
| **8** | **Delight-to-Referral Loop** | At peak delight (grant win or great recommendation), prompt user to invite a colleague. Cecilia's prior company: referral ask at peak delight was a goldmine. | Growth insight, not a prototype feature. Include in presentation as evidence of full business loop thinking. |

**Build order:** #3 (write the standard) → #1 (build the conversation) → #2 (build the evals) → show #4 and #8 as design recommendations

---

## Experiences for the Solo Grant Writer — Ranked

These are the distinct interaction flows we designed for the returning solo grant writer persona.

Ranking criteria: same as above — WHY (demonstrate PM value) + WHAT (most valuable to the customer)

| Rank | Experience | The flow | Why this rank |
|------|-----------|----------|---------------|
| **1** | **E — The Consultant Conversation** | Agent asks 3 questions max, follows the client's energy, mirrors language, infers context without stating as fact, distinguishes dealbreakers from preferences. Delivers 2-3 curated grants with full rationale: why this one, why now, what's the move. Knows when to stop. | The only one where the AI magic is in the quality of the interaction itself, not a trigger or data trick. Every moment maps to a white glove behavior, every failure maps to a testable eval. Strongest proof of taste, customer empathy, and systems thinking. Buildable without their database. |
| **2** | **A — "I already know you, let me prove it"** | Agent opens with what it already knows from user history — searches, tracked grants, skipped grants. "Here's what I understand about you. Did I get that right?" User corrects or confirms. Agent sharpens. | Strongest opening moment. If synthetic profile feels real, this + E is the full demo: A is the first 10 seconds, E is the next 3 minutes. Risk: synthetic data feeling hollow. |
| **3** | **C — "Congrats, here's what's next"** | User marks grant as awarded. Scout: "Congratulations. Based on what made this a fit, here are 2 more. Want to look now, or reminder in 3 weeks?" | Best product insight about where in the journey the scout lives. Include as a design recommendation slide, not a built prototype. Shows full lifecycle thinking. |
| **4** | **B — "React, don't generate"** | Show 3-4 grants, ask skip or pursue, follow up on why. After a few rounds, mirror: "So you care about X, won't bother under Y, federal is a dealbreaker. Right?" | Best cold-start solution for new users. Park for v2. Mention to show you've thought about the new user problem but scoped it out deliberately. |
| **5** | **D — "Just talk to me"** | Voice-first. User talks like they would to a colleague. Agent listens, then synthesizes: "Here's what I'm hearing — correct me." | Right long-term vision, wrong prototype scope. Conversation design needs to work in text first. Shared office problem. Mention as future direction. |

**Recommendation:** Build E, open with a taste of A (if synthetic profile is strong), present C as a slide. Demo = AI understanding + eval rigor + product vision.