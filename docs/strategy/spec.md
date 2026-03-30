## 1. What are we prototyping?

An AI prospecting co-pilot ("Scout") for Instrumentl that eliminates the filter-and-scroll workflow entirely. The user talks, the agent understands, and the agent delivers the grant they say yes to. 

**The constraint that no longer exists:**
Instrumentl's current flow assumes the user must learn to navigate the database before they can find a match they say yes to. The onboarding teaches them to fish: set up searches, use filters, narrow results. But that's exactly what creates the overwhelm users report. In a world where AI can reason over 400,000 grants and the user's full context simultaneously, there is no reason 200 results should ever appear. The filtering step, the qualification step, the "don't worry about the number of results" step — none of these need to exist. They are workarounds for a limitation that is no longer real.

This is a prototype of Instrumentl's stated product direction: "AI-powered prospecting co-pilot that delivers personalized, high-quality prospecting strategies" (from their PM job req / Discover Co-pilot initiative, led by Angela Braren, Co-founder & Head of EPD).

**Where the AI magic lives:**
The hard problem isn't "find me grants that match my tags." Instrumentl already does that. The hard problem is that the user can't articulate what they need in the language the system requires. "Fatherhood initiative" doesn't fit in a dropdown. "We're a small org that punches above our weight on environmental justice in underserved communities but we can't handle federal reporting because it's just me" — that's a paragraph of nuance that no filter system captures.

The AI magic is: you talk like a human, and the agent understands like a consultant. The output isn't "here are 200 results, let me show you how to filter." The output is "I reviewed 200+ opportunities. Here's the one to start with, and here's exactly why."

**Abundance + curation, not reduction:**
The user needs to feel the ocean is big AND have someone hand them the right fish. The design isn't "3 instead of 200." It's "here's the one to act on right now — and here's what's behind it: 200+ opportunities we reviewed to get here." If they want more, the agent shows the next tier with rationale for why those are a step below. Each "show me more" is a choice, not a coping mechanism.

**What this prototype demonstrates (to the Instrumentl team):**
- She cares about the customer — the experience is designed around how the best human consultants actually work, not around feature convenience
- She can build with new systems — synthetic users, eval framework, agent learning loop
- She has taste in what's acceptable to demo — one moment, done well, with evidence it works
- She thinks in systems — the eval framework proves quality, not just the happy path

**What this prototype does NOT do:**
- Access Instrumentl's live database (we simulate with representative data)
- Cover the full grant writing workflow (Apply is a separate product)
- Serve power users or multi-project teams
- Test with real users (synthetic users only — but this workflow can and should be repeated with real users to surface failure modes that synthetic profiles can't predict)

**Three-agent architecture:**
The system is a pipeline of three specialized agents, each with one job:
- **Transcriber** — receives conversation transcript from the advisor-user call, extracts a structured profile, asks only for missing critical fields
- **Scout** — searches grants, produces draft recommendations with rationale
- **Scorer** — quality gate that checks Scout's work against the user's profile before anything is shown

The user never knows the Scorer exists. They just experience recommendations that are always right. See `docs/build/architecture.md` for the full technical design and `docs/build/model-spec-*.md` for each agent's behavioral spec.

**Design principle:** React before you generate, mirror before you ask for more. Show value first to earn the right to ask questions.

---

## 2. Who are we solving for — and the experience

A new Instrumentl user getting their first grant recommendation during their 1:1 onboarding call. Not after. Not alone. During the call, with their advisor, in a conversation that feels human — because it is.

**Profile:**
- Solo or 1-2 person grant writing operation
- Just signed up, completed group onboarding (or watched recording)
- About to have their 1:1 with an onboarding advisor
- Needs to get to their first yes — not a maybe, not a save-for-later, but "this is the one, when's the deadline, let's start"
- Has limited capacity — they can't apply to everything, so choosing wrong feels costly

**The onboarding gap this solves:**
Instrumentl offers group onboarding + a 1:1 advisor positioned as a strategy consultant. But advisors operate at scale — they can show users how the tools work, but they can't give deep, personalized grant strategy to every user. So the 1:1 becomes a tool walkthrough, not a qualification session. The user leaves knowing how to filter but not what to pursue. The agent fills this gap: it has the domain reasoning of the best grant consultant and the tool knowledge of the CS team. Neither human has both.

**The experience:**
1. Advisor hops on a call with the user. Screen-shares the scout agent.
2. Advisor says: "I have a tool here that's going to listen to our conversation and build a picture of what you're looking for — you'll see it on my screen as we talk. That way, when you go into Instrumentl on your own later, it'll already know who you are. Is that OK?"
3. User consents. The agent connects to the call audio (like Fireflies/Otter joining a meeting). A clear visual indicator shows when the agent is listening.
4. The advisor has a normal human conversation. "Tell me about your organization and what you're hoping to find." The user talks — rambles, gets excited, mentions dealbreakers casually.
5. On the shared screen, the agent shows a structured profile building in real time. Not raw transcription — synthesis. Mission, focus areas, capacity, dealbreakers, preferences, what they're excited about.
6. The advisor pauses: "Take a look at the screen — does this capture what you're looking for?" The user reads, corrects, confirms. The profile sharpens.
7. The advisor says: "OK, based on all of this, it found one that looks really strong for you." The agent shows a single grant with full rationale — why this funder, why now, why it fits them specifically. "We reviewed 200+ opportunities to get to this one."
8. The user reads it: "Oh wow, that's actually perfect. When's the deadline?" That's the yes.
9. The advisor walks them through next steps — how to track it, how to start. Normal onboarding, but now they're acting on a recommendation, not learning to filter.
10. The call ends. The user opens Instrumentl on their own. **The same scout agent is there.** It already knows them. Their profile is built. They don't start from zero. They don't see 200 unfiltered results. They see: "Welcome back. Here's what I have for you."

**The emotional arc:**
1. User joins call → feels supported ("a real person is helping me")
2. User talks, sees profile build → feels understood ("it gets what I'm actually looking for")
3. Agent recommends → feels confidence ("this is the one, I can see why, let's go")
4. User opens platform alone → feels continuity ("it remembers me, I'm not starting over")

---

## 3. What the best human consultant actually does

This is the bar. The agent should feel like the best grant consultant the user has ever talked to.

1. **They listen for what's behind the words.** The client says "we do after-school programs." The consultant hears "Title I schools, working parents, limited transportation, you probably need funders who don't require a site visit because you're running this out of a church basement." They fill in the context the client doesn't think to say because it's just their life.

2. **They notice what the client gets excited about.** Not what they *say* matters — what makes their voice change. "Oh, and we just started this coding lab thing" — that's where the energy is. A great consultant follows that thread, not the org chart.

3. **They know when to stop asking.** They don't run through a checklist. They ask maybe 3-4 questions, then they say "OK, I think I've got it. Let me tell you what I'm hearing." The client talks for 5 minutes, the consultant synthesizes in 30 seconds, and the client feels *seen*.

4. **They protect the client from themselves.** The client says "we should apply for everything." The consultant says "no. You have capacity for 2 applications this quarter. Let's make them count." They're not a search engine. They're a filter with judgment.

5. **They never make the client feel stupid.** The client doesn't know what an LOI is. The consultant doesn't say "that's a letter of inquiry." They say "some foundations want a short letter first before the full application — kind of like a first date before committing. Have you done any of those?" They meet the client where they are.

6. **They remember everything.** Six months later the client mentions something offhand and the consultant says "wait, that connects to the thing you told me about your board member who used to work at [foundation]. Have you thought about..." The client didn't make that connection. The consultant did, because they held the full picture.

---

## 4. Evals and metrics

### Philosophy: start with 3-5, expand from error analysis

The right way to build evals: build the product, run it, do error analysis on real outputs, then write scorers only for the failure patterns you actually observe. Don't write 19 scorers before the first eval run — let the failures teach you what to measure. This prototype can't follow that advice fully because there are no real users to generate real failures. The synthetic users and trap grants are a deliberate substitute: designed to provoke specific failure modes so the eval suite has something real to catch. But given the choice, I'd run Scout with real users first, catalog what goes wrong, and build scorers from that — not from a checklist written before the first output exists. That's the process I'd follow on the job.

### Tier 1 scorers (implemented)

Three scorers that cover the highest-stakes failure modes — where a bad output wastes the user's most scarce resource (time) or destroys trust.

| Scorer | What it catches | Pass condition |
|--------|----------------|----------------|
| **Trap Avoidance** | Agent recommends a grant that violates a stated dealbreaker or geographic/eligibility mismatch | Zero trap grants in output |
| **Hit Rate** | Agent fails to surface any genuinely good match | At least 1 correct grant recommended |
| **Overwhelm Check** | Agent pushes more grants than the user can act on | Grant count ≤ user capacity (solo: 2, team: 3) |

**Why these three first:**
- Trap avoidance is the most dangerous failure — the user spends weeks on an application they were never eligible for. This is the "never ship this" metric.
- Hit rate is the core promise — if the agent can't find a single good match, the product doesn't work.
- Overwhelm is the pain point Scout exists to solve — if we recreate the 200-result scroll, we've failed.

### Tier 2 scorers (next, based on what Tier 1 reveals)

Candidates to promote once we run Tier 1 and do error analysis. We don't build them until we see which failures actually occur:

- **Geographic Precision** — same-state-wrong-county mismatches (the most common failure mode in testing so far)
- **Dealbreaker Violation** — more granular than trap avoidance: did the agent respect *every* stated dealbreaker, not just the ones encoded as trap grants?
- **Nuance Flattening** (LLM-as-judge) — did the agent flatten "fatherhood initiative" to "family services"?
- **Language Mirror** (LLM-as-judge) — did the rationale use the user's words or upgrade to jargon they didn't use?

### LLM-as-judge (out of scope for prototype)

The Nuance Flattening and Language Mirror scorers require LLM-as-judge — using one model to evaluate another model's output. These are the right scorers for catching the subtle failures that rule-based checks can't: did the agent preserve the user's meaning, not just their keywords? Did it reason about "fatherhood initiative" as a distinct concept, or collapse it into "family services"?

These scorers are out of scope for the prototype because they require calibration to be meaningful. An uncalibrated LLM judge is just another model's opinion. A calibrated one is a validated measurement tool. The difference is: you score a set of outputs manually first, then run the judge on the same outputs, and only ship it when the judge agrees with human judgment on known examples. That calibration process requires real pipeline outputs to score against — and doing it well matters more than doing it fast.

This is the right next step after completing Tier 1 error analysis: identify which subtle failure patterns actually occur, write the judge prompt, calibrate against manual scores, then promote.

### Synthetic users (12 profiles)

Each user is designed to stress-test specific failure modes:

| User | Key test |
|------|----------|
| Maria (Austin, TX) | Jargon mirroring, dealbreaker detection |
| David (RI) | Terse user, doesn't over-ask |
| Patricia (IN) | Extracts signal from rambling |
| James (IN) | Protects from false hope, hidden disqualifiers (2yr org) |
| Sandra (Oakland, CA) | Doesn't flatten nuance, handles pushback |
| Tom (TN) | Navigates contradictions |
| Rachel (CT) | Matches expert pace, doesn't over-explain |
| Angela (Philadelphia) | Fatherhood-initiative test, same-state-wrong-county |
| Margaret (IL) | Builds confidence, never makes client feel stupid |
| Kevin (FL) | Handles skepticism, earns trust through accuracy |
| Lisa (San Marcos, CA) | Cross-category missions, same-state-wrong-city |
| Robert (MN) | Non-western frameworks, resists categorization |

Each user has **correct grants** (what the agent should recommend) and **trap grants** (what looks right but violates a dealbreaker). The traps are where the evals catch failures.

### The eval loop

1. Load synthetic users → build call notes → run full pipeline (Transcriber → Scout → Scorer)
2. Score each run with Tier 1 scorers, log everything to Braintrust
3. Error analysis on failures → decide which Tier 2 scorer to promote next
4. Update prompts → re-run → show improvement

**The demo story:** "I started with 3 scorers that catch the highest-stakes failures. I ran 12 synthetic users through the pipeline, found the patterns that actually break, and promoted new scorers from error analysis. Here's the loop."

---

## 5. Out of scope (and what I'd want to learn)

**Access to Instrumentl's grant database**
We simulate with representative public data. The quality of curation is only as good as the data feeding it — this is the first thing I'd want to understand: how grants are tagged, what metadata exists on funders, and where the gaps are.

**Real customer conversations**
This prototype is built on Capterra reviews, public feedback, and synthesized personas. The obvious next step is talking to customers directly — especially the ones who churned after 3-6 months and the ones who stayed but describe feeling overwhelmed. The gap between those two groups is where the real product insight lives.

**Domain knowledge the team has that the agent doesn't**
Here's a concrete example of why this matters. In testing, one synthetic user (Maria) previously won a $3K grant from a local Rotary club. Scout sometimes recommends the same Rotary club's grant again — framing her prior win as a strength ("they know this model works"). Other times, Scout drops it entirely. Both could be right, but the agent doesn't know because it lacks domain knowledge that the Instrumentl team has: Do local foundations typically fund repeat grantees? Is a prior relationship a signal to lean in or move on? Should the agent weight funder history differently for community foundations vs. federal programs?

This is exactly the kind of knowledge that turns an eval from "did the agent recommend the right grants?" into "did the agent reason about funder relationships the way an expert would?" The team's domain expertise doesn't just inform the product — it becomes eval criteria that makes the agent measurably better. Every question like this that gets answered and encoded into the eval suite is a permanent improvement to recommendation quality.

**Matching and ranking algorithm**
The prototype demonstrates conversation quality and eval rigor, not recommendation engine performance. I'd want to understand how matching works today before proposing anything — what signals it uses, whether it can support weighted criteria (dealbreakers vs. nice-to-haves), and where the bottlenecks are. The scout agent's value depends on what's already been built underneath it.

**Integration with existing product surfaces**
I don't know how the scout would live inside Instrumentl's UI — sidebar, separate tab, notification layer, embedded in the tracker. That depends on where users currently spend their time in the product, which I'd need to learn from the team.

**Post-recommendation workflow**
The prototype stops at curation. It doesn't cover what happens after the user says "yes, I'm interested" — pre-filling applications, pulling funder history, connecting to Apply. Getting the handoff to existing product surfaces right matters, and that requires understanding those surfaces first.

**Geographic precision beyond state level — and a question I can't answer yet**
The prototype already pre-filters grants by state before Scout sees them (user's state + national-scope grants only). That mechanical step is built and working. The unsolved problem is finer-grained: county-level and regional geographic matching. A grant serving "Dallas County, TX" is in the right state but wrong county for a Travis County user. Scout handles this through reasoning, but at scale, geographic scope data is often ambiguous — "Southeast region," "greater metro area," "rural Appalachian communities" — and doesn't map cleanly to county-level filters.

Capterra reviews confirm geographic mismatch is a real pain point. One user wrote: "The only thing missing is I can't filter my funders by state — that is a key search criterion." Another: "I wish it only finds funders that fit ALL of my research parameters instead of ANY."

The question I'd want to explore with the engineering team: how is geographic scope data structured in the real database? Can county/region matching be automated, or is the ambiguity inherent in how funders describe their service areas? The answer determines whether geographic precision is a data problem (clean up the metadata) or a reasoning problem (the AI has to interpret "greater metro area" in context). The prototype treats it as a reasoning problem. At scale, it may need to be both.

**Indexing and pre-filtering at scale**
The geographic question above is a specific case of a broader scaling problem. The prototype does not scale to 400,000 grants. An LLM should never be the one traversing a full database — it's too slow, too expensive, and it's the wrong tool for the job. The right approach is a funnel where existing search infrastructure does the fast, mechanical filtering first and the AI handles judgment and curation on a smaller candidate set. But how that funnel should work depends entirely on what Instrumentl has already built — I'd need to understand the existing search and matching infrastructure before designing around it.

**Scale and edge cases**
Synthetic users let us test a few personas. Real coverage means stress-testing against the full diversity of orgs — tiny rural nonprofits, urban consultants with multiple clients, university research offices. Each has different language, different capacity, different dealbreakers. The evals need to hold across all of them, and getting there requires real user data.

**CI/CD and rollout strategy**
See `docs/strategy/playbook.md` for the full design: CI/CD pipeline, feature flags, A/B testing, controlled ramp, cohort analysis, automated signal processing, and kill switches.

---

## 6. Things to think about — user trust and safety in voice

The advisor-on-a-call experience involves the agent listening to live conversation audio. This requires careful design around consent and user control. These aren't solved in the prototype but matter deeply.

**Consent must be explicit and framed as a benefit.**
By law, the user must consent before the agent listens. The advisor's framing matters: not "this call will be recorded" (surveillance) but "this tool will listen so you don't have to repeat yourself later — is that OK?" If they say no, the advisor runs the call normally and inputs notes after. No degraded experience.

**The user should feel in control throughout, not just at the start.**
Consent at the start is legal. Control throughout is trust. The user should always be able to see when the agent is listening — a clear visual indicator (animation, light, status). Consider whether the user should be able to pause the agent mid-conversation without stopping the call (push-to-talk or toggle model). Some users will find live synthesis magical. Others will self-edit if they know they're being transcribed. The advisor needs to read the room.

**Show synthesis, not transcription.**
The agent should never display raw words on screen. Seeing "we're kind of, I don't know, we do a lot of things" reflected back is embarrassing. Seeing "Mission: after-school STEM programs for underserved communities" reflected back is magical. The difference between "it's recording me" and "it gets me" is whether the user sees their words or the agent's understanding.

**The agent must never speak during the call.**
The advisor is the human in the room. The agent is a silent listener that produces the synthesis view. If the agent starts responding or interrupting, the three-way dynamic gets confusing and the advisor loses control of the conversation.
