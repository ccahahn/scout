import json
from datetime import datetime, date
import streamlit as st
from pipeline import run_transcriber, run_pipeline, run_pipeline_with_answers, run_chat_followup, escape_dollars, filter_grants_for_profile, extract_state, profile_dict_to_text, GRANTS


def days_until(deadline_str):
    """Parse a deadline string and return days remaining, or None."""
    if not deadline_str:
        return None
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            d = datetime.strptime(deadline_str.strip(), fmt).date()
            delta = (d - date.today()).days
            return delta if delta >= 0 else None
        except ValueError:
            continue
    return None

st.set_page_config(page_title="Scout by Instrumentl", layout="centered")

# ---- Brand colors ----
PURPLE = "#6B5CE7"
LIGHT_PURPLE = "#7b77c9"
CREAM = "#F8F6F1"
WARM_BORDER = "#D4D2CC"
TEXT_PRIMARY = "#2C2C2A"
TEXT_SUPPORTING = "#A09E96"
TEXT_TERMS = "#6B6A64"
PLACEHOLDER_COLOR = "#C4C2BA"

# ---- Global styles ----
st.markdown(f"""
<style>
/* Warm ivory background */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"],
.main, .block-container, [data-testid="stMainBlockContainer"] {{
    background-color: {CREAM} !important;
    font-size: 14px !important;
    line-height: 1.65 !important;
    color: {TEXT_PRIMARY} !important;
}}
[data-testid="stHeader"] {{
    background-color: {CREAM} !important;
}}

/* Tier 1 — Primary content */
h1, h2, h3, h4 {{
    color: {TEXT_PRIMARY} !important;
    font-size: 18px !important;
    font-weight: 500 !important;
    line-height: 1.4 !important;
}}

/* Body text */
p, li, .stMarkdown {{
    font-size: 14px !important;
    line-height: 1.65 !important;
}}

/* Metadata (amounts, deadlines) */
.stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    line-height: 1.5 !important;
    color: {TEXT_SUPPORTING} !important;
}}

/* Buttons */
.stButton > button {{
    font-size: 14px !important;
    font-weight: 500 !important;
}}

/* Textarea */
.stTextArea textarea {{
    font-size: 14px !important;
    line-height: 1.65 !important;
    background-color: white !important;
    border-radius: 10px !important;
    padding: 18px !important;
    color: {TEXT_PRIMARY} !important;
}}
.stTextArea textarea::placeholder {{
    color: {PLACEHOLDER_COLOR} !important;
    font-style: italic !important;
}}

/* Text inputs */
.stTextInput input,
[data-testid="stChatInput"] textarea {{
    font-size: 14px !important;
    line-height: 1.65 !important;
    background-color: white !important;
    color: {TEXT_PRIMARY} !important;
}}

/* Primary buttons */
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {{
    background-color: {PURPLE} !important;
    border-color: {PURPLE} !important;
    color: white !important;
    border-radius: 7px !important;
}}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {{
    background-color: #5a4dd0 !important;
    border-color: #5a4dd0 !important;
}}

/* Secondary buttons — match primary shape, neutral color */
.stButton > button[kind="secondary"],
.stButton > button[data-testid="stBaseButton-secondary"] {{
    background-color: #EDEAE4 !important;
    border-color: #EDEAE4 !important;
    color: {TEXT_PRIMARY} !important;
    border-radius: 7px !important;
}}
.stButton > button[kind="secondary"]:hover,
.stButton > button[data-testid="stBaseButton-secondary"]:hover {{
    background-color: #E2DFD9 !important;
    border-color: #E2DFD9 !important;
}}

/* Textarea border */
.stTextArea > div,
.stTextArea > div > div,
.stTextArea [data-baseweb="textarea"],
.stTextArea [data-baseweb="base-input"] {{
    border: 0.5px solid {WARM_BORDER} !important;
    border-radius: 10px !important;
}}
.stTextArea textarea:focus,
.stTextArea > div:focus-within,
.stTextArea > div > div:focus-within,
.stTextArea [data-baseweb="textarea"]:focus-within,
.stTextArea [data-baseweb="base-input"]:focus-within {{
    border-color: #b0aea8 !important;
    box-shadow: none !important;
}}
.stTextInput input:focus {{
    border-color: #b0aea8 !important;
    box-shadow: none !important;
}}

/* Text input containers — kill orange focus ring */
.stTextInput > div,
.stTextInput > div > div,
.stTextInput [data-baseweb="input"],
.stTextInput [data-baseweb="base-input"] {{
    border-color: #e0e0e0 !important;
}}
.stTextInput > div:focus-within,
.stTextInput > div > div:focus-within,
.stTextInput [data-baseweb="input"]:focus-within,
.stTextInput [data-baseweb="base-input"]:focus-within {{
    border-color: {PURPLE} !important;
    box-shadow: none !important;
}}

/* Chat input — match textarea styling */
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
.stChatInput > div {{
    border-color: {WARM_BORDER} !important;
    border-radius: 10px !important;
    background-color: white !important;
}}
[data-testid="stChatInput"] textarea {{
    font-size: 14px !important;
    color: {TEXT_PRIMARY} !important;
    background-color: white !important;
}}
[data-testid="stChatInput"] textarea::placeholder {{
    color: {PLACEHOLDER_COLOR} !important;
}}
.stChatInput > div:focus-within,
.stChatInput textarea:focus,
.stChatInput div[data-baseweb]:focus-within,
[data-testid="stChatInput"] > div:focus-within,
[data-testid="stChatInput"] textarea:focus,
[data-testid="stChatInputTextArea"]:focus,
[data-testid="stChatInputTextArea"]:focus-within {{
    border-color: #b0aea8 !important;
    box-shadow: none !important;
    outline: none !important;
}}
/* Chat submit button — purple */
[data-testid="stChatInput"] button,
.stChatInput button {{
    background-color: {PURPLE} !important;
    color: white !important;
}}

/* Toggle — purple instead of orange */
[data-testid="stToggle"] span[data-baseweb="toggle"] > div {{
    background-color: {PURPLE} !important;
}}
[data-testid="stToggle"] span[data-baseweb="toggle"]:focus-within > div {{
    box-shadow: none !important;
}}

/* Selectbox — kill orange focus */
[data-baseweb="select"] > div {{
    border-color: {WARM_BORDER} !important;
}}
[data-baseweb="select"] > div:focus-within,
[data-baseweb="select"]:focus-within > div {{
    border-color: #b0aea8 !important;
    box-shadow: none !important;
}}
[data-baseweb="select"] [data-baseweb="input"]:focus {{
    box-shadow: none !important;
}}

/* Clean focus globally — no browser outlines */
*:focus {{
    outline: none !important;
}}

/* Apply page header */
.apply-header {{
    background: linear-gradient(135deg, {LIGHT_PURPLE} 0%, #9B8FE8 100%);
    padding: 32px 24px;
    border-radius: 8px 8px 0 0;
    margin: -1px;
}}
.apply-header h2 {{
    color: white !important;
    margin: 0 !important;
    font-size: 22px !important;
}}
.apply-header p {{
    color: rgba(255,255,255,0.85);
    margin: 4px 0 0 0;
    font-size: 15px;
}}

/* Pre-filled field styling */
.prefilled {{
    background: #f0eef9;
    border: 1px solid #d4d0e8;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 4px 0 16px 0;
    font-size: 15px;
    color: #262624;
}}
.prefilled-label {{
    font-size: 13px;
    font-weight: 500;
    color: #666;
    margin-bottom: 2px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}}
.prefilled-badge {{
    display: inline-block;
    background: {LIGHT_PURPLE};
    color: white;
    font-size: 11px;
    padding: 2px 6px;
    border-radius: 3px;
    margin-left: 6px;
    vertical-align: middle;
}}

/* Detail page header */
.detail-header {{
    background: linear-gradient(135deg, {PURPLE} 0%, {LIGHT_PURPLE} 100%);
    padding: 32px 24px;
    border-radius: 8px 8px 0 0;
    margin: -1px;
}}
.detail-header h2 {{
    color: white !important;
    margin: 0 !important;
    font-size: 22px !important;
}}
.detail-header p {{
    color: rgba(255,255,255,0.85);
    margin: 4px 0 0 0;
    font-size: 15px;
}}

/* Detail field styling */
.detail-field {{
    margin: 12px 0;
}}
.detail-label {{
    font-size: 13px;
    font-weight: 500;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    margin-bottom: 2px;
}}
.detail-value {{
    font-size: 15px;
    color: #262624;
    line-height: 1.6;
}}

/* Explore tag */
.explore-tag {{
    display: inline-block;
    background: #f0eef9;
    color: {PURPLE};
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 12px;
    margin: 2px 2px 2px 0;
}}



/* Loading / progress display */
.loading-container {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
}}
.loading-spinner {{
    width: 64px;
    height: 64px;
    border: 3px solid {WARM_BORDER};
    border-top-color: {PURPLE};
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 24px;
}}
.progress-count {{
    width: 64px;
    height: 64px;
    border: 3px solid {PURPLE};
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    font-weight: 600;
    color: #262624;
    margin-bottom: 24px;
}}
@keyframes spin {{
    to {{ transform: rotate(360deg); }}
}}
.loading-text {{
    font-size: 20px;
    font-weight: 500;
    color: #262624;
    margin-bottom: 24px;
}}
.step-list {{
    display: flex;
    flex-direction: column;
    gap: 10px;
    min-width: 300px;
}}
.step-row {{
    display: flex;
    align-items: center;
    gap: 10px;
}}
.step-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #ddd;
    flex-shrink: 0;
}}
.step-dot.active {{
    background: {PURPLE};
    animation: pulse 1.5s ease-in-out infinite;
}}
.step-dot.done {{
    background: {PURPLE};
}}
@keyframes pulse {{
    0%, 100% {{ opacity: 0.4; }}
    50% {{ opacity: 1; }}
}}
.step-label {{
    font-size: 15px;
    color: #666;
    flex: 1;
}}
.step-detail {{
    font-size: 14px;
    color: #999;
    text-align: right;
}}
.loading-timer {{
    font-size: 13px;
    color: #ccc;
    margin-top: 16px;
    font-variant-numeric: tabular-nums;
}}
</style>
""", unsafe_allow_html=True)


# ---- Amount formatting helpers ----

def format_amount(val):
    """Format a numeric amount for display with HTML-safe dollar sign."""
    if val is None:
        return None
    if isinstance(val, str):
        cleaned = val.replace('$', '').replace(',', '').strip()
        try:
            val = int(float(cleaned))
        except (ValueError, TypeError):
            return f"&#36;{val}"
    return f"&#36;{val:,}"


def format_amount_range(grant):
    """Format the amount range from a grant dict."""
    amt_min = grant.get("amount_min")
    amt_max = grant.get("amount_max")
    if amt_min is not None and amt_max is not None:
        if amt_min == amt_max:
            return format_amount(amt_max)
        return f"{format_amount(amt_min)} - {format_amount(amt_max)}"
    if amt_max is not None:
        return f"Up to {format_amount(amt_max)}"
    if amt_min is not None:
        return f"From {format_amount(amt_min)}"
    return None


# ---- Session state ----
if "phase" not in st.session_state:
    st.session_state.phase = "intake"
    st.session_state.notes = ""
    st.session_state.profile = None
    st.session_state.profile_dict = None
    st.session_state.editing_profile = False
    st.session_state.editing_field = None
    st.session_state.results = None
    st.session_state.follow_up = None
    st.session_state.follow_up_answers = ""
    st.session_state.scout_context = None
    st.session_state.chat_history = []
    st.session_state.apply_grant = None
    st.session_state.detail_grant = None
    st.session_state.explore_grants = None
    st.session_state.widget_key = 0

def reset_all():
    st.session_state.phase = "intake"
    st.session_state.notes = ""
    st.session_state.profile = None
    st.session_state.profile_dict = None
    st.session_state.editing_profile = False
    st.session_state.editing_field = None
    st.session_state.results = None
    st.session_state.follow_up = None
    st.session_state.follow_up_answers = ""
    st.session_state.scout_context = None
    st.session_state.chat_history = []
    st.session_state.apply_grant = None
    st.session_state.detail_grant = None
    st.session_state.explore_grants = None
    st.session_state.widget_key += 1

def go_back_to_intake():
    st.session_state.phase = "intake"



# ---- Progress UI ----

STEP_LABELS = {
    "reading_profile": "Reading your profile",
    "scanning": "Scanning open grants",
    "scoring": "Scoring for fit",
}

def _build_progress_html(current_step, step_detail=None, grant_count=None, done=False):
    """Build the full progress HTML for a given pipeline state."""
    steps = ["reading_profile", "scanning", "scoring"]

    # Center circle
    if done and grant_count is not None:
        # Animate count from 0 to N via JS
        circle = f'<div class="progress-count" id="grant-counter" data-target="{grant_count}">0</div>'
        headline_id = 'id="done-headline"'
        headline_text = f'Done — <span id="headline-count">{grant_count}</span> grant{"s" if grant_count != 1 else ""} found.'
    else:
        circle = '<div class="loading-spinner"></div>'
        headline_id = ''
        headline_text = "Finding the right grants for you"

    # Step list
    step_rows = ""
    for s in steps:
        label = STEP_LABELS[s]
        past = steps.index(s) < steps.index(current_step) if current_step in steps else False
        active = (s == current_step) and not done
        is_done = done or past

        # Dot color
        if is_done:
            dot_class = "step-dot done"
        elif active:
            dot_class = "step-dot active"
        else:
            dot_class = "step-dot"

        # Right-side detail
        detail = ""
        if s == "scanning" and step_detail:
            detail = f'<span class="step-detail">{step_detail}</span>'

        step_rows += f'<div class="step-row"><span class="{dot_class}"></span><span class="step-label">{label}</span>{detail}</div>'

    return (
        '<div class="loading-container">'
        f'{circle}'
        f'<div class="loading-text" {headline_id}>{headline_text}</div>'
        f'<div class="step-list">{step_rows}</div>'
        '<div class="loading-timer" id="scout-timer"></div>'
        '</div>'
    )


def make_thinking_ui():
    """Create stepped progress display. Returns callbacks for pipeline."""
    progress_el = st.empty()

    # State shared between callbacks
    state = {"current_step": "reading_profile", "detail": None}

    # Render initial state
    progress_el.markdown(
        _build_progress_html("reading_profile"),
        unsafe_allow_html=True,
    )

    # Client-side timer
    st.components.v1.html("""
    <script>
    const el = window.parent.document.getElementById('scout-timer');
    if (el) {
        let seconds = 0;
        const tick = () => {
            seconds++;
            if (seconds < 60) { el.textContent = seconds + 's'; }
            else { el.textContent = Math.floor(seconds/60) + 'm ' + (seconds%60) + 's'; }
        };
        setInterval(tick, 1000);
    }
    </script>
    """, height=0)

    # Placeholder for counter animation script
    counter_el = st.empty()

    def on_step(step, detail=None):
        if step == "done":
            count = int(detail) if detail else 0
            progress_el.markdown(
                _build_progress_html("scoring", state["detail"], grant_count=count, done=True),
                unsafe_allow_html=True,
            )
            # Animate the counter from 0 → N
            if count > 0:
                with counter_el:
                    st.components.v1.html(f"""
                    <script>
                    (function() {{
                        var el = window.parent.document.getElementById('grant-counter');
                        if (!el) return;
                        var target = {count};
                        var current = 0;
                        var s = Math.max(50, Math.floor(600 / target));
                        var timer = setInterval(function() {{
                            current++;
                            el.textContent = current;
                            if (current >= target) clearInterval(timer);
                        }}, s);
                    }})();
                    </script>
                    """, height=0)
        else:
            state["current_step"] = step
            if detail:
                state["detail"] = detail
            progress_el.markdown(
                _build_progress_html(step, state["detail"]),
                unsafe_allow_html=True,
            )

    def on_thinking(chunk):
        pass

    def on_scorer(chunk):
        pass

    def on_status(msg):
        pass

    return on_thinking, on_scorer, on_status, on_step


# =====================================================
# PHASES
# =====================================================

# ---- APPLY (mock application page) ----
if st.session_state.phase == "apply":
    grant = st.session_state.apply_grant
    profile = st.session_state.profile_dict or {}

    org = profile.get("organization", "")
    location = profile.get("location", "")
    mission = profile.get("mission", "")
    serving = profile.get("who_they_serve", "")
    budget = profile.get("budget", "")
    team = ""  # not in structured profile

    if st.button("\u2190 Back to Results"):
        st.session_state.phase = "results"
        st.rerun()

    st.write("")

    # Build subtitle from structured grant data
    amount_range = format_amount_range(grant)
    deadline = grant.get("deadline", "")
    subtitle_parts = []
    if amount_range:
        subtitle_parts.append(amount_range)
    if deadline:
        subtitle_parts.append(f"Deadline: {deadline}")
    subtitle = " | ".join(subtitle_parts)

    st.markdown(f"""
    <div class="apply-header">
        <h2>Application: {grant.get("title", "")}</h2>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### About your organization")
        st.write("")

        def prefilled_field(label, value):
            badge = '<span class="prefilled-badge">Pre-filled by Scout</span>' if value else ''
            st.markdown(f'<div class="prefilled-label">{label}{badge}</div>', unsafe_allow_html=True)
            if value:
                st.markdown(f'<div class="prefilled">{value}</div>', unsafe_allow_html=True)
            else:
                st.text_input(label, label_visibility="collapsed", key=f"apply_{label}")

        prefilled_field("Organization name", org)
        prefilled_field("Mission and description", mission)
        prefilled_field("Populations served", serving)
        prefilled_field("Location", location)
        prefilled_field("Annual budget", budget)
        prefilled_field("Team size", team)

        st.write("")
        st.markdown("#### Project details")
        st.write("")
        st.text_area("Describe the project this grant would fund", height=120,
                     placeholder="Scout can help you draft this based on your conversation...",
                     key="apply_project")

        st.write("")
        st.markdown("#### Budget")
        st.write("")
        st.text_area("Proposed budget breakdown", height=100,
                     placeholder="How would you allocate the funds?",
                     key="apply_budget")

        st.write("")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.button("Submit Application", type="primary")
        with col2:
            st.button("Save Draft")

# ---- GRANT DETAIL (mock Instrumentl grant page) ----
elif st.session_state.phase == "grant_detail":
    grant = st.session_state.detail_grant

    if st.button("\u2190 Back to Results"):
        st.session_state.phase = "results"
        st.rerun()

    st.write("")


    # Header
    amount_range = format_amount_range(grant)
    deadline = grant.get("deadline", "")
    subtitle_parts = []
    if amount_range:
        subtitle_parts.append(amount_range)
    if deadline:
        subtitle_parts.append(f"Deadline: {deadline}")
    subtitle = " | ".join(subtitle_parts)

    st.markdown(f"""
    <div class="detail-header">
        <h2>{grant.get("title", "")}</h2>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        def detail_field(label, value):
            if value:
                st.markdown(f'<div class="detail-field"><div class="detail-label">{label}</div><div class="detail-value">{value}</div></div>', unsafe_allow_html=True)

        detail_field("Funder", grant.get("funder", ""))
        detail_field("Funder type", (grant.get("funder_type") or "").replace("_", " ").title())
        detail_field("Description", grant.get("description", ""))
        detail_field("Geographic scope", grant.get("geographic_scope", ""))

        # Eligible applicants
        eligible = grant.get("eligible_applicants", [])
        if eligible:
            detail_field("Eligible applicants", ", ".join(eligible))

        # Focus areas as tags
        focus = grant.get("focus_areas", [])
        if focus:
            tags_html = " ".join(f'<span class="explore-tag">{f}</span>' for f in focus)
            st.markdown(f'<div class="detail-field"><div class="detail-label">Focus areas</div><div>{tags_html}</div></div>', unsafe_allow_html=True)

        detail_field("Application type", (grant.get("application_type") or "").replace("_", " ").title())

        # Matching funds
        if grant.get("requires_match"):
            detail_field("Matching funds", "Required")
        elif grant.get("match_strengthens"):
            detail_field("Matching funds", "Not required, but strengthens application")

        detail_field("Federal", "Yes" if grant.get("federal") else "No")

        # Total funding pool
        total = grant.get("total_funding")
        if total:
            detail_field("Total funding available", f"&#36;{total:,}")

        # New fields from user feedback
        if grant.get("renewable") is not None:
            renewable_text = "Yes" if grant["renewable"] else "No"
            duration = grant.get("grant_duration")
            if duration:
                renewable_text += f" ({duration.replace('_', ' ')})"
            detail_field("Renewable", renewable_text)

        if grant.get("funds_staffing") is not None:
            detail_field("Can fund staffing/FTE", "Yes" if grant["funds_staffing"] else "No")

        if grant.get("allows_indirect_costs") is not None:
            idc_text = "Yes" if grant["allows_indirect_costs"] else "No"
            rate = grant.get("indirect_cost_rate")
            if rate:
                idc_text += f" — {rate}"
            detail_field("Indirect costs", idc_text)

        if grant.get("reporting_requirements"):
            detail_field("Reporting requirements", grant["reporting_requirements"])

    st.write("")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("\u2190 Back to Results", key="detail_back_bottom"):
            st.session_state.phase = "results"
            st.rerun()
    with col2:
        # Find matching grant for Apply
        if st.button("Apply \u2192", type="primary", key="detail_apply"):
            st.session_state.apply_grant = grant
            st.session_state.phase = "apply"
            st.rerun()

# ---- EXPLORE ALL (mock Instrumentl search page) ----
elif st.session_state.phase == "explore":
    if st.button("\u2190 Back to Results"):
        st.session_state.phase = "results"
        st.rerun()

    st.write("")

    st.title("Search")

    all_grants = st.session_state.explore_grants or []

    # Filters
    with st.container(border=True):
        st.markdown("**Filters**")
        filter_cols = st.columns(2)
        with filter_cols[0]:
            geo_filter = st.toggle("Geographic match", value=True, help="Show only grants matching your location")
        with filter_cols[1]:
            size_filter = st.selectbox("Grant size", options=["Any size", "Under $10K", "$10K - $50K", "$50K+"])

    # Apply filters
    filtered = all_grants
    if geo_filter and st.session_state.profile:
        user_state = extract_state(st.session_state.profile)
        if user_state:
            filtered = [g for g in filtered if g.get("state") == user_state or g.get("state") == "national"]

    if size_filter == "Under $10K":
        filtered = [g for g in filtered if (g.get("amount_max") or float("inf")) < 10000]
    elif size_filter == "$10K - $50K":
        filtered = [g for g in filtered if (g.get("amount_min") or 0) >= 10000 and (g.get("amount_max") or 0) <= 50000]
    elif size_filter == "$50K+":
        filtered = [g for g in filtered if (g.get("amount_min") or g.get("amount_max") or 0) >= 50000]

    st.caption(f"Showing {len(filtered)} of {len(all_grants)} opportunities")
    st.write("")

    # Grant list
    for g in filtered:
        with st.container(border=True):
            title = g.get("title", "Untitled")
            funder = g.get("funder", "")
            amount_range = format_amount_range(g)
            deadline = g.get("deadline", "")
            geo = g.get("geographic_scope", "")
            focus = g.get("focus_areas", [])

            st.markdown(f"**{escape_dollars(title)}**")
            meta_parts = []
            if funder:
                meta_parts.append(escape_dollars(funder))
            if amount_range:
                meta_parts.append(amount_range)
            if deadline:
                meta_parts.append(f"Deadline: {escape_dollars(deadline)}")
            if meta_parts:
                st.markdown(" | ".join(meta_parts), unsafe_allow_html=True)
            if geo:
                st.caption(f"Geographic scope: {geo}")
            if focus:
                tags_html = " ".join(f'<span class="explore-tag">{f}</span>' for f in focus[:5])
                st.markdown(tags_html, unsafe_allow_html=True)

# ---- EXTRACTING (transcriber runs with simple loading screen) ----
elif st.session_state.phase == "extracting":
    # Header
    header_col1, header_col2 = st.columns([4, 1])
    with header_col1:
        st.markdown(f'<span style="font-family: Georgia, serif; font-size: 28px; font-weight: 600; color: {PURPLE};">Scout</span> <span style="font-size: 16px; color: #999;">grant prospecting co-pilot</span>', unsafe_allow_html=True)
    with header_col2:
        st.write("")
        if st.button("Clear"):
            reset_all()
            st.rerun()

    # Simple centered spinner while transcriber runs
    st.markdown(
        '<div class="loading-container">'
        '<div class="loading-spinner"></div>'
        '<div class="loading-text">Getting to know you</div>'
        '<div class="loading-timer" id="scout-timer"></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.components.v1.html("""
    <script>
    const el = window.parent.document.getElementById('scout-timer');
    if (el) {
        let seconds = 0;
        const tick = () => { seconds++; el.textContent = seconds < 60 ? seconds + 's' : Math.floor(seconds/60) + 'm ' + (seconds%60) + 's'; };
        setInterval(tick, 1000);
    }
    </script>
    """, height=0)

    profile_dict = run_transcriber(st.session_state.notes)
    st.session_state.profile_dict = profile_dict
    st.session_state.profile = profile_dict_to_text(profile_dict)
    st.session_state.phase = "confirm_profile"
    st.rerun()

# ---- SEARCHING (scout + scorer with stepped progress) ----
elif st.session_state.phase == "searching":
    # Header
    header_col1, header_col2 = st.columns([4, 1])
    with header_col1:
        st.markdown(f'<span style="font-family: Georgia, serif; font-size: 28px; font-weight: 600; color: {PURPLE};">Scout</span> <span style="font-size: 16px; color: #999;">grant prospecting co-pilot</span>', unsafe_allow_html=True)
    with header_col2:
        pass

    on_thinking, on_scorer, on_status, on_step = make_thinking_ui()

    results = run_pipeline(
        st.session_state.profile,
        raw_notes=st.session_state.notes,
        thinking_callback=on_thinking,
        scorer_callback=on_scorer,
        status_callback=on_status,
        step_callback=on_step,
    )

    if results.get("needs_follow_up"):
        st.session_state.follow_up = results["follow_up_questions"]
        st.session_state.scout_context = results["scout_output"]
        st.session_state.phase = "follow_up"
    else:
        st.session_state.results = results
        st.session_state.phase = "results"
    st.rerun()

# ---- SEARCHING AFTER FOLLOW-UP ----
elif st.session_state.phase == "searching_with_answers":
    header_col1, header_col2 = st.columns([4, 1])
    with header_col1:
        st.markdown(f'<span style="font-family: Georgia, serif; font-size: 28px; font-weight: 600; color: {PURPLE};">Scout</span> <span style="font-size: 16px; color: #999;">grant prospecting co-pilot</span>', unsafe_allow_html=True)
    with header_col2:
        st.write("")
        if st.button("\u2190 Back"):
            go_back_to_intake()
            st.rerun()

    on_thinking, on_scorer, on_status, on_step = make_thinking_ui()

    results = run_pipeline_with_answers(
        profile_text=st.session_state.profile,
        previous_scout_output=st.session_state.scout_context,
        follow_up_answers=st.session_state.follow_up_answers,
        scorer_callback=on_scorer,
        step_callback=on_step,
    )

    st.session_state.results = results
    st.session_state.phase = "results"
    st.rerun()

# All other phases get the standard header
else:
    # ---- HEADER ----
    header_col1, header_col2 = st.columns([4, 1])
    with header_col1:
        st.markdown(f'<span style="font-family: Georgia, serif; font-size: 28px; font-weight: 600; color: {PURPLE};">Scout</span> <span style="font-size: 16px; color: #999;">grant prospecting co-pilot</span>', unsafe_allow_html=True)
    with header_col2:
        st.write("")
        if st.session_state.phase == "results":
            if st.button("\u2190 Back"):
                st.session_state.phase = "confirm_profile"
                st.rerun()
        else:
            if st.button("Clear"):
                reset_all()
                st.rerun()

    page = st.empty()

    # ---- PROFILE CONFIRMATION ----
    if st.session_state.phase == "confirm_profile":
        FIELD_HINTS = {
            "organization": "What's the organization called?",
            "location": "City, county, state?",
            "mission": "What do they do?",
            "who_they_serve": "Who do they serve?",
            "budget": "Roughly how large is the org?",
            "grant_experience": "First-time or experienced?",
            "looking_for": "What kind of grants are they after?",
            "sweet_spot": "What grant size range works?",
            "fund_use": "How would they spend it?",
            "renewability": "One-time OK, or need multi-year?",
            "dealbreakers": "Anything they want to avoid?",
            "urgency": "How soon do they need this?",
        }
        EMPTY_PATTERNS = {"", "not mentioned", "not discussed", "not specified", "unknown", "n/a", "none", "not provided"}
        field_labels = [
            ("organization", "Organization"),
            ("location", "Location"),
            ("mission", "Mission"),
            ("who_they_serve", "Who they serve"),
            ("budget", "Budget"),
            ("grant_experience", "Grant experience"),
            ("looking_for", "Looking for"),
            ("sweet_spot", "Sweet spot"),
            ("fund_use", "Fund use"),
            ("renewability", "Renewability"),
            ("dealbreakers", "Dealbreakers"),
            ("urgency", "Urgency"),
        ]

        with page.container():
            st.write("")
            st.markdown(f'<p style="font-size: 12px; color: {TEXT_SUPPORTING}; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 2px;">Extracted Profile</p>', unsafe_allow_html=True)
            st.markdown(f'<p style="font-size: 22px; font-weight: 500; color: {TEXT_PRIMARY}; margin: 0;">Here\'s what I understood.</p>', unsafe_allow_html=True)
            st.markdown(f'<p style="font-size: 15px; font-weight: 400; color: {TEXT_SUPPORTING}; margin: 4px 0 20px 0;">Anything to correct before I search?</p>', unsafe_allow_html=True)

            profile = st.session_state.profile_dict or {}

            if st.session_state.editing_profile:
                # Edit mode — all fields as text inputs
                with st.container(border=True):
                    edited = {}
                    for key, label in field_labels:
                        edited[key] = st.text_input(label, value=profile.get(key, ""), key=f"edit_{key}")
                    st.write("")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Save and find grants", type="primary"):
                            st.session_state.profile_dict = edited
                            st.session_state.profile = profile_dict_to_text(edited)
                            st.session_state.editing_profile = False
                            st.session_state.phase = "searching"
                            st.rerun()
                    with col2:
                        if st.button("Cancel"):
                            st.session_state.editing_profile = False
                            st.rerun()
            else:
                # Read-only card with flex rows
                rows_html = ""
                for idx, (key, label) in enumerate(field_labels):
                    val = profile.get(key, "")
                    is_empty = not val or val.strip().lower() in EMPTY_PATTERNS
                    border = "" if idx == len(field_labels) - 1 else "border-bottom: 0.5px solid #E8E6E0;"

                    if is_empty:
                        hint = FIELD_HINTS.get(key, "")
                        val_html = f'<span style="font-style: italic; color: {PLACEHOLDER_COLOR}; font-size: 14px;">Didn\'t come up — {hint}</span>'
                    else:
                        val_html = f'<span style="color: {TEXT_PRIMARY}; font-size: 14px; line-height: 1.5;">{escape_dollars(val)}</span>'

                    rows_html += (
                        f'<div style="display: flex; align-items: flex-start; padding: 16px 20px; {border}">'
                        f'<div style="width: 140px; flex-shrink: 0; font-size: 13px; color: {TEXT_SUPPORTING};">{label}</div>'
                        f'<div style="flex: 1;">{val_html}</div>'
                        f'</div>'
                    )

                st.markdown(
                    f'<div style="background: white; border: 0.5px solid #D4D2CC; border-radius: 12px; overflow: hidden;">'
                    f'{rows_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                st.write("")
                col1, col2, col3 = st.columns([1, 1, 4])
                with col1:
                    if st.button("Find grants", type="primary"):
                        st.session_state.phase = "searching"
                        st.rerun()
                with col2:
                    if st.button("Edit"):
                        st.session_state.editing_profile = True
                        st.rerun()

    # ---- FOLLOW-UP QUESTIONS ----
    elif st.session_state.phase == "follow_up":
        with page.container():
            st.write("")
            st.markdown("**Scout has a couple of questions before finalizing your recommendations:**")
            st.write("")
            with st.container(border=True):
                questions = st.session_state.follow_up
                if isinstance(questions, list):
                    for q in questions:
                        st.markdown(f"- {escape_dollars(q)}", unsafe_allow_html=True)
                else:
                    st.markdown(escape_dollars(str(questions)), unsafe_allow_html=True)
            st.write("")
            answers = st.text_area(
                "Your answers",
                height=150,
                placeholder="Answer however feels natural - short is fine.",
                key=f"followup_{st.session_state.widget_key}",
            )
            if st.button("Continue search", type="primary"):
                st.session_state.follow_up_answers = answers
                st.session_state.phase = "searching_with_answers"
                st.rerun()

    # ---- RESULTS + CHAT ----
    elif st.session_state.phase == "results":
        with page.container():
            st.write("")

            grants = st.session_state.results.get("grants", [])
            near_misses = st.session_state.results.get("near_misses", [])
            elimination = st.session_state.results.get("elimination_summary", {})
            message = st.session_state.results.get("message")

            if grants:
                # Header
                st.markdown("## Here's what I found.")
                total_reviewed = elimination.get("total_reviewed", "200+")
                col_context, col_explore = st.columns([3, 1])
                with col_context:
                    st.markdown(f'<p style="font-size: 14px; color: {TEXT_SUPPORTING};">{len(grants)} grant{"s" if len(grants) != 1 else ""} from {total_reviewed} reviewed &middot; sorted by fit</p>', unsafe_allow_html=True)
                with col_explore:
                    if st.button("See all results \u2192", key="see_all"):
                        st.session_state.explore_grants = GRANTS
                        st.session_state.phase = "explore"
                        st.rerun()

                # Purple accent line
                st.markdown(f'<hr style="border: none; height: 2px; background: {PURPLE}; margin: 8px 0 24px 0;">', unsafe_allow_html=True)

                for i, grant in enumerate(grants):
                    title = grant.get("title", "Untitled Grant")
                    amount_range = format_amount_range(grant)
                    deadline = grant.get("deadline", "")
                    rationale = grant.get("rationale", "")
                    caveats = grant.get("caveats")
                    funder = grant.get("funder", "")
                    fit_tags = grant.get("fit_tags", [])
                    days_left = days_until(deadline)

                    # Look up funder from grants.json if not in Scout output
                    if not funder:
                        grant_id = grant.get("id")
                        full = next((g for g in GRANTS if g["id"] == grant_id), None)
                        if full:
                            funder = full.get("funder", "")

                    is_top = (i == 0)
                    num = f"{i + 1:02d}"

                    # Section number + top match label
                    if is_top:
                        st.markdown(f'<p style="font-size: 14px; color: {PURPLE}; margin-bottom: 4px;"><strong>{num}</strong> &middot; TOP MATCH</p>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<p style="font-size: 14px; color: {TEXT_SUPPORTING}; margin-bottom: 4px;"><strong>{num}</strong></p>', unsafe_allow_html=True)

                    # Grant name + funder
                    st.markdown(f"### {escape_dollars(title)}")
                    if funder:
                        st.markdown(f'<p style="font-size: 13px; color: {TEXT_SUPPORTING}; margin-top: -8px;">{escape_dollars(funder)}</p>', unsafe_allow_html=True)

                    # Metrics row
                    met1, met2, met3 = st.columns(3)
                    with met1:
                        st.caption("Amount")
                        if amount_range:
                            st.markdown(f"**{amount_range}**", unsafe_allow_html=True)
                    with met2:
                        st.caption("Deadline")
                        if deadline:
                            st.markdown(f"**{escape_dollars(deadline)}**")
                    with met3:
                        st.caption("Time left")
                        if days_left is not None:
                            if days_left < 30:
                                dl_color = "#A32D2D"
                            elif days_left < 90:
                                dl_color = "#BA7517"
                            else:
                                dl_color = TEXT_PRIMARY
                            st.markdown(f'<p style="font-weight: 500; color: {dl_color};">{days_left} days</p>', unsafe_allow_html=True)

                    # Why this fits
                    st.markdown(f'<p style="font-size: 13px; color: {TEXT_SUPPORTING}; margin: 12px 0 4px 0;">Why this fits</p>', unsafe_allow_html=True)
                    if rationale:
                        st.write(escape_dollars(rationale))
                    if caveats:
                        st.caption(f"Note: {caveats}")

                    # Match tags — plain text with dot separators
                    if fit_tags:
                        st.markdown(
                            f'<p style="font-size: 13px; color: {TEXT_SUPPORTING};">'
                            + ' &middot; '.join(escape_dollars(t) for t in fit_tags)
                            + '</p>',
                            unsafe_allow_html=True,
                        )

                    # Buttons
                    btn1, btn2, btn3 = st.columns([1, 1, 3])
                    with btn1:
                        if st.button("Apply \u2192", key=f"apply_{i}", type="primary"):
                            st.session_state.apply_grant = grant
                            st.session_state.phase = "apply"
                            st.rerun()
                    with btn2:
                        if st.button("Learn more", key=f"detail_{i}"):
                            grant_id = grant.get("id")
                            full_grant = next((g for g in GRANTS if g["id"] == grant_id), grant)
                            st.session_state.detail_grant = full_grant
                            st.session_state.phase = "grant_detail"
                            st.rerun()

                    # Divider between grants (not after last)
                    if i < len(grants) - 1:
                        st.divider()

            elif message:
                st.markdown(escape_dollars(message), unsafe_allow_html=True)

            if near_misses:
                st.divider()
                st.markdown(f'<p style="font-size: 14px; color: {TEXT_SUPPORTING};"><strong>Worth keeping an eye on</strong></p>', unsafe_allow_html=True)
                st.write("")
                for nm in near_misses:
                    st.markdown(f"**{escape_dollars(nm.get('title', ''))}**")
                    if nm.get("what_aligns"):
                        st.markdown(f"*What aligns:* {escape_dollars(nm['what_aligns'])}", unsafe_allow_html=True)
                    if nm.get("the_issue"):
                        st.markdown(f"*The gap:* {escape_dollars(nm['the_issue'])}", unsafe_allow_html=True)
                    if nm.get("the_play"):
                        st.markdown(f"*Next move:* {escape_dollars(nm['the_play'])}", unsafe_allow_html=True)
                    st.write("")

            # Chat history
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(escape_dollars(msg["content"]), unsafe_allow_html=True)

            # Chat input
            if prompt := st.chat_input("Ask about these grants, or tell me what to look for next..."):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(escape_dollars(prompt))
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = run_chat_followup(
                            profile=st.session_state.results["profile"],
                            scout_output=st.session_state.results["scout_output"],
                            grants=st.session_state.results.get("grants", []),
                            chat_history=st.session_state.chat_history,
                        )
                    st.markdown(response, unsafe_allow_html=True)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()

            st.write("")
            if st.button("Start new search"):
                reset_all()
                st.rerun()

    # ---- INTAKE ----
    else:
        with page.container():
            st.write("")
            st.markdown(f'<p style="font-size: 18px; font-weight: 500; color: {TEXT_PRIMARY}; margin: 0;">Paste the call transcript or notes.</p>', unsafe_allow_html=True)
            st.markdown(f'<p style="font-size: 14px; font-weight: 400; color: {TEXT_SUPPORTING}; margin: 6px 0 24px 0;">Messy is fine — Scout will pull out what matters.</p>', unsafe_allow_html=True)

            notes = st.text_area(
                "Call notes",
                height=200,
                placeholder='e.g. "We\'re Raices del Valle, a small after-school tutoring program in south Austin. We serve first-generation Latino students in Travis County. Our budget is around $180K. We\'ve gotten a few small grants before — one from the local Rotary club — but nothing federal. We need something in the $2K–$10K range, and we can\'t handle complex reporting because it\'s basically just me and one volunteer."',
                label_visibility="collapsed",
                key=f"notes_{st.session_state.widget_key}",
            )

            # Gentle hint for what to include
            terms = ["organization", "location", "mission", "who they serve", "budget", "grant experience", "looking for", "grant size", "fund use", "renewability", "dealbreakers", "urgency"]
            st.markdown(
                f'<div style="margin-top: 20px;">'
                f'<p style="font-size: 13px; color: {TEXT_SUPPORTING}; font-weight: 400; margin: 0 0 4px 0;">Helpful to cover:</p>'
                f'<p style="font-size: 14px; color: {TEXT_TERMS}; font-weight: 500; line-height: 1.65; margin: 0;">'
                + ' \u00b7 '.join(terms)
                + '</p></div>',
                unsafe_allow_html=True,
            )

            st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
            if st.button("Find grants", type="primary"):
                st.session_state.notes = notes
                st.session_state.phase = "extracting"
                st.rerun()

            # Auto-focus the text area on page load
            st.components.v1.html("""
            <script>
            const textarea = window.parent.document.querySelector('textarea');
            if (textarea) textarea.focus();
            </script>
            """, height=0)
