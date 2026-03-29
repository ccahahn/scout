## Reflection: What I learned from reading 35 real grants

This file documents the patterns, pain points, and insights that emerged from compiling real grant data from GrantWatch. These learnings directly informed the questionnaire the scout agent uses and the eval criteria it's measured against.

---

### 1. The fields that matter most for matching aren't always the obvious ones

**Geographic scope is the first filter, but it's more nuanced than state-level.**
Almost every grant is hyper-local. Not "California" — "San Marcos, California." Not "New York" — "Broome County, New York." Not "Indiana" — "eight counties in southern Indiana." The scout agent must understand the user's service area at the county or city level, not just their state. A user who says "we're in the Bay Area" could qualify for Sunnyvale neighborhood grants, Oakland arts grants, or San Marcos community grants — all in different counties with different eligibility.

**Funder type determines the application experience more than the focus area.**
Federal pass-through grants (like CDBG or ESG) require matching funds, compliance with HUD regulations, mandatory public hearings, and reimbursement-based payment. Private foundation grants are simpler — online application, no match, faster turnaround. A solo grant writer who says "I can't handle complicated reporting" is really saying "no federal." But they might not know that's what they mean. The agent needs to translate that.

**Eligible applicant requirements vary wildly and are often disqualifying.**
Some grants require 2+ years of operating history. Some require 3+ years of specific program experience (like the Nevada school garden grant). Some require minimum 12 months prior experience. Some require pre-existing SFSP approval. Some won't fund organizations with budgets over $2M. Some prioritize organizations with budgets under $950K. The agent must capture the user's org age, budget size, and any specialized credentials early — these are hard disqualifiers, not soft preferences.

---

### 2. The amount range tells you what kind of nonprofit the grant is designed for

**Micro grants ($500-$2,500):** Designed for very small community organizations. Low administrative burden. The Rhode Island Foundation grant ($800-$2,500) explicitly prioritizes organizations "without access to other funding sources." These are for orgs where $1,500 is meaningful.

**Small grants ($2,000-$15,000):** The sweet spot for solo grant writers at small nonprofits. Most common in our dataset. Usually one-page to three-page applications. Often quarterly deadlines. The Rotary Club ($2,000), Arts for Oakland Kids ($5,000), Ellison Foundation ($1,000-$10,000).

**Mid-range grants ($15,000-$50,000):** Require more detailed proposals, budgets, sometimes LOIs. The United Way of Greater Austin ($50K), Being for Others ($40K), Philadelphia Foundation ($10K-$50K). These often have two-stage application processes.

**Large grants ($100K+):** Complex applications, federal compliance, matching requirements, mandatory workshops. The CDBG ($2.3M total), Oakland Violence Prevention ($39M over 3 years). These are not for solo grant writers.

**Key insight for the questionnaire:** Asking "what's your typical grant size?" or "what's the biggest grant you've managed?" immediately tells the agent what tier of complexity the user can handle. A user who's only ever applied for $5K grants should not be shown a $2.3M CDBG opportunity, even if the focus area matches perfectly.

---

### 3. Application type is a proxy for capacity

**Full application (most common):** Online portal, fill out fields, submit. Most manageable.

**LOI first, then full application:** Two-stage process. The Kott Memorial Trust and United Way of Austin both use this. It's actually friendlier for small orgs — you write a short letter first, and only do the full application if invited. The agent should explain this benefit.

**Pre-contact required:** The Hoyt Foundation requires a phone call one month before and an in-person meeting with the CEO before submitting. The Main Street Community Foundation requires a preliminary discussion one week before. These are not just bureaucratic hurdles — they're relationship-building steps. The agent should frame them as opportunities, not obstacles.

**Written/paper submission:** The Rotary Club of Pensacola uses manual written submissions. Rare but exists. Some users might prefer this simplicity.

**RFP (Request for Proposals):** The Oakland Violence Prevention uses a formal RFP with pre-proposal meetings, iSupplier registration, and complex narrative requirements. This is a different world from a $2,000 Rotary grant.

**Key insight for the questionnaire:** Don't ask "what application type do you prefer?" Nobody knows. Ask "have you written a grant application before? What was that like?" The answer tells you everything — if they describe filling out a Google Form, they're at the micro/small tier. If they describe writing a 20-page narrative with logic models, they can handle an RFP.

---

### 4. Focus areas are fuzzy — the same work fits multiple categories

The Being for Others Foundation has EIGHT priority pillars. The Legacy Foundation has FOUR focus areas with sub-categories. The J.W. Couch Foundation has THREE programs with multiple sub-themes each.

A nonprofit that runs after-school coding for underserved kids could fit under:
- Education (academic enrichment)
- Youth development (youth services)
- STEM (technology education)
- Community development (workforce readiness)
- Equity (serving underrepresented populations)
- Digital wellbeing (the J.W. Couch wellness category)

**Key insight for the questionnaire:** Don't ask users to pick a category. Let them describe their work, then the agent maps it to the right categories. This is exactly the "fatherhood initiative doesn't fit in a dropdown" problem from the spec. The agent's job is to understand that "we teach kids to code after school in underserved neighborhoods" maps to education + youth + equity + STEM + community development — and then find grants that match ANY of those intersections.

---

### 5. Deadlines create urgency tiers that matter for recommendations

**Quarterly rolling deadlines:** The San Marcos Community Foundation, South Cumberland Fund, Steuben County REMC all have quarterly cycles. No urgency — if you miss one, apply next quarter.

**Biannual deadlines:** The SEMAC Arts Council, Hoyt Foundation, Andersen Foundation. More structure. Miss it and you wait 6 months.

**Annual deadlines:** One shot per year. Miss it and you wait 12 months. These are the ones worth flagging urgently.

**Key insight for the questionnaire:** Ask "are you looking for something to apply to right now, or are you planning ahead?" This determines whether the agent shows grants with deadlines in 3 weeks (urgent) or 3 months (plannable). A user in "browsing mode" doesn't need to see a grant due in 5 days — that just creates anxiety.

---

### 6. The hidden disqualifiers that no one thinks to mention

From the grant data, these are real requirements that a user wouldn't think to bring up but are absolutely disqualifying:

- **Must have operated for X years** (Nevada: 2 years school garden experience; Initiative Foundation: 3 years continuous programming; Orlando ESG: 2 years in business; Utica CDBG: 12 months)
- **Budget cap** (Initiative Foundation: under $2M; Philadelphia Foundation: priority under $950K)
- **Must be in specific counties/cities** (almost all grants — not state-level)
- **Cannot have received funding recently** (Main Street: not 2+ consecutive years; Hoyt: two-year wait; Toledo Rotary: two-year wait)
- **Mandatory pre-application meetings or calls** (Orlando ESG: mandatory workshop; Hoyt: in-person meeting; Main Street: staff discussion)
- **Must serve specific populations** (United Way Austin: low-income; Utica CDBG: low/moderate-income)
- **Specific certifications required** (Nebraska SFSP: must be SFSP-approved sponsor)
- **Matching fund requirements** (Orlando ESG: 100% dollar-for-dollar match)

**Key insight for the questionnaire:** The agent should proactively ask about these before recommending. "How long has your organization been operating?" "Have you received grants from community foundations before?" "Do you have matching funds available?" These save the user from falling in love with a grant they can't apply for.

---

### 7. What makes a grant "perfect" for someone isn't just fit — it's feasibility

A perfect match isn't just "your mission aligns with their focus area." It's the intersection of:
1. **Mission fit** — your work matches what they fund
2. **Geographic fit** — you serve the area they care about
3. **Capacity fit** — you can handle the application complexity and reporting
4. **Size fit** — the award amount is meaningful to you but not beyond what you can manage
5. **Timeline fit** — you have enough time to apply well
6. **Eligibility fit** — you meet all the hard requirements (org age, budget, certifications)
7. **Relationship fit** — the funder's style matches how you work (hands-off vs. engaged, simple vs. complex)

The last one — relationship fit — is the one no filter system captures. Some funders want to meet you before you apply (Hoyt Foundation). Some want you at quarterly community gatherings (Middlesex United Way). Some just want a Google Form (Youth Board Grant). A solo grant writer who's introverted and overwhelmed would thrive with the Google Form funder and dread the quarterly gathering requirement. The agent needs to know this.

---

## Debugging tidbits

Lessons from debugging this prototype — the kind of thing that's hard to Google because the fix depends on understanding *why* something works, not just *what* to type.

---

### 8. Streamlit stale DOM: don't replace old content during a long operation — make it not exist

**The bug:** During the searching phase, the intake form appeared grayed out below the thinking/status box. The pipeline takes several seconds to run, and the whole time the old form sat there looking broken.

**Why it happens:** When Streamlit reruns the script, the browser keeps showing the previous render's DOM (grayed out, reduced opacity) until the new render completes. If the new render includes a long-running call (`run_pipeline()`), the old DOM lingers for the entire duration. This is just how Streamlit works — it's not a bug, it's the framework showing "stale" content while the script executes.

**What didn't work:** Wrapping everything in a single `st.empty()` container and rendering both phases inside `page.container()`. The idea was that writing new content to the container would replace the old content. But it doesn't — Streamlit has to *finish executing* the container's contents before it can swap the DOM. So while the pipeline ran inside the new `page.container()`, the browser was still showing the old `page.container()` (the intake form) as stale content.

**What worked:** Put the intake/results UI inside `page = st.empty()`, but render the searching UI *directly to the page root*, leaving `page` unwritten. An unwritten `st.empty()` renders as nothing — so the intake form is immediately gone from the DOM the moment the rerun starts. The status widget renders cleanly as the only element on screen.

**The principle:** Don't try to *replace* content during a long operation. Make the old content *not exist* by leaving its container empty. The distinction matters because replacement requires execution to complete, but absence is immediate.
