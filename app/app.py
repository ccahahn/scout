import json
import streamlit as st
from pipeline import run_transcriber, run_pipeline, run_chat_followup, escape_dollars, filter_grants_for_profile, extract_state, GRANTS

st.set_page_config(page_title="Scout by Instrumentl", layout="centered")

# ---- Brand colors ----
PURPLE = "#5b56b2"
CORAL = "#f26f63"
LIGHT_PURPLE = "#7b77c9"

# ---- Global styles ----
st.markdown(f"""
<style>
/* Base type scale — font loaded via .streamlit/config.toml */
html, body {{
    font-size: 16px !important;
    line-height: 1.6 !important;
    color: #262624 !important;
}}

/* Page title: 28px */
h1 {{
    color: {PURPLE} !important;
    font-size: 28px !important;
    font-weight: 600 !important;
    line-height: 1.3 !important;
}}

/* Section headers: 20px */
h2, h3, h4 {{
    font-size: 20px !important;
    font-weight: 600 !important;
    line-height: 1.4 !important;
}}

/* Body text (paragraphs, list items, markdown): 16px */
p, li, .stMarkdown {{
    font-size: 16px !important;
    line-height: 1.6 !important;
}}

/* Grant titles in results: 18px */
.stMarkdown strong {{
    font-size: 18px;
    font-weight: 600;
}}

/* Metadata (amounts, deadlines): 13px */
.stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    line-height: 1.5 !important;
}}

/* Buttons: 15px */
.stButton > button {{
    font-size: 15px !important;
    font-weight: 500 !important;
}}

/* Text inputs and areas: 16px */
.stTextArea textarea, .stTextInput input,
[data-testid="stChatInput"] textarea {{
    font-size: 16px !important;
    line-height: 1.6 !important;
}}

/* Primary buttons: coral */
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {{
    background-color: {CORAL} !important;
    border-color: {CORAL} !important;
    color: white !important;
}}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {{
    background-color: #e05a4e !important;
    border-color: #e05a4e !important;
}}

/* Subtle focus borders - just slightly darker than default, like Claude.ai */
.stTextArea textarea:focus,
.stTextInput input:focus {{
    border-color: #c0c0c0 !important;
    box-shadow: none !important;
}}
.stTextArea > div,
.stTextArea > div > div,
.stTextArea [data-baseweb="textarea"],
.stTextArea [data-baseweb="base-input"] {{
    border-color: #e0e0e0 !important;
}}
.stTextArea > div:focus-within,
.stTextArea > div > div:focus-within,
.stTextArea [data-baseweb="textarea"]:focus-within,
.stTextArea [data-baseweb="base-input"]:focus-within {{
    border-color: #c0c0c0 !important;
    box-shadow: none !important;
}}

/* Chat input focus - subtle */
.stChatInput > div:focus-within,
.stChatInput textarea:focus,
.stChatInput div[data-baseweb]:focus-within,
[data-testid="stChatInput"] > div:focus-within,
[data-testid="stChatInput"] textarea:focus,
[data-testid="stChatInputTextArea"]:focus,
[data-testid="stChatInputTextArea"]:focus-within {{
    border-color: #c0c0c0 !important;
    box-shadow: none !important;
    outline: none !important;
}}

/* Kill any orange/red focus globally */
*:focus {{
    outline-color: #c0c0c0 !important;
}}
textarea:focus, input:focus {{
    border-color: #c0c0c0 !important;
    box-shadow: none !important;
}}

/* Back link styling */
.back-link {{
    color: {LIGHT_PURPLE};
    text-decoration: none;
    font-size: 15px;
    cursor: pointer;
}}
.back-link:hover {{
    text-decoration: underline;
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

/* Grant card apply button */
.apply-btn {{
    display: inline-block;
    background: {CORAL};
    color: white !important;
    padding: 6px 16px;
    border-radius: 6px;
    text-decoration: none;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    border: none;
}}
.apply-btn:hover {{
    background: #e05a4e;
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

/* Mock banner */
.mock-banner {{
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 13px;
    color: #856404;
    margin-bottom: 16px;
    text-align: center;
}}

/* Explore page grant row */
.explore-grant {{
    padding: 12px 0;
    border-bottom: 1px solid #eee;
}}
.explore-grant:last-child {{
    border-bottom: none;
}}
.explore-tag {{
    display: inline-block;
    background: #f0eef9;
    color: {PURPLE};
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 12px;
    margin: 2px 2px 2px 0;
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
THINKING_CSS = f"""
<style>
.thinking-container {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 32px 0;
}}
.thinking-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: {PURPLE};
    animation: pulse 1.5s ease-in-out infinite;
}}
@keyframes pulse {{
    0%, 100% {{ opacity: 0.3; transform: scale(0.9); }}
    50% {{ opacity: 1; transform: scale(1.1); }}
}}
.thinking-text {{
    font-size: 15px;
    color: #666;
}}
.thinking-timer {{
    font-size: 13px;
    color: #999;
    font-variant-numeric: tabular-nums;
    margin-top: -24px;
}}
</style>
"""


def make_thinking_ui():
    """Create pulsing dot + elapsed timer UI while Scout thinks."""
    st.markdown(THINKING_CSS, unsafe_allow_html=True)
    status_display = st.empty()
    timer_display = st.empty()

    import time
    start_time = [time.time()]
    last_timer_update = [0]

    def _render_status(msg):
        status_display.markdown(
            f'<div class="thinking-container">'
            f'<div class="thinking-dot"></div>'
            f'<span class="thinking-text">{msg}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    def _update_timer():
        elapsed = int(time.time() - start_time[0])
        if elapsed != last_timer_update[0]:
            timer_display.markdown(
                f'<div class="thinking-timer">{elapsed}s</div>',
                unsafe_allow_html=True,
            )
            last_timer_update[0] = elapsed

    _render_status("Finding your best-fit grants so you can spend your time on the work, not the search. Back in two minutes.")

    def on_thinking(chunk):
        _update_timer()

    def on_scorer(chunk):
        _update_timer()

    def on_status(msg):
        # Pipeline status updates just tick the timer, don't replace the main message
        _update_timer()

    return on_thinking, on_scorer, on_status


# =====================================================
# PHASES
# =====================================================

# ---- APPLY (mock application page) ----
if st.session_state.phase == "apply":
    grant = st.session_state.apply_grant
    profile_text = st.session_state.profile or ""

    # Parse profile fields
    def get_field(label):
        for line in profile_text.split("\n"):
            if line.strip().lower().startswith(label.lower()):
                val = line.split(":", 1)[-1].strip() if ":" in line else ""
                return val
        return ""

    org = get_field("organization") or get_field("org")
    location = get_field("location")
    mission = get_field("mission")
    serving = get_field("serving") or get_field("who they serve") or get_field("populations")
    budget = get_field("budget") or get_field("annual budget")
    team = get_field("team") or get_field("team size")

    if st.button("< Back to Results"):
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

    if st.button("< Back to Results"):
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
        if st.button("< Back to Results ", key="detail_back_bottom"):
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
    if st.button("< Back to Results"):
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

# ---- SEARCHING (initial run) ----
elif st.session_state.phase == "searching":
    # Header with back button
    header_col1, header_col2 = st.columns([4, 1])
    with header_col1:
        st.title("Scout")
    with header_col2:
        st.write("")
        if st.button("< Back"):
            go_back_to_intake()
            st.rerun()

    on_thinking, on_scorer, on_status = make_thinking_ui()

    profile = run_transcriber(st.session_state.notes)
    st.session_state.profile = profile

    results = run_pipeline(
        profile,
        thinking_callback=on_thinking,
        scorer_callback=on_scorer,
        status_callback=on_status,
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
        st.title("Scout")
    with header_col2:
        st.write("")
        if st.button("< Back"):
            go_back_to_intake()
            st.rerun()

    on_thinking, on_scorer, on_status = make_thinking_ui()
    on_status("Updating recommendations with your answers...")

    enriched_profile = (
        st.session_state.profile
        + "\n\nFollow-up answers from the user:\n"
        + st.session_state.follow_up_answers
    )

    results = run_pipeline(
        enriched_profile,
        thinking_callback=on_thinking,
        scorer_callback=on_scorer,
        status_callback=on_status,
        allow_follow_up=False,
    )

    st.session_state.results = results
    st.session_state.phase = "results"
    st.rerun()

# All other phases get the standard header
else:
    # ---- HEADER ----
    header_col1, header_col2 = st.columns([4, 1])
    with header_col1:
        st.title("Scout")
    with header_col2:
        st.write("")
        if st.button("Clear chat"):
            reset_all()
            st.rerun()

    page = st.empty()

    # ---- FOLLOW-UP QUESTIONS ----
    if st.session_state.phase == "follow_up":
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

            # "See all results" option above recommendations
            if st.button("See all results \u2192"):
                st.session_state.explore_grants = GRANTS
                st.session_state.phase = "explore"
                st.rerun()

            st.write("")

            grants = st.session_state.results.get("grants", [])
            near_misses = st.session_state.results.get("near_misses", [])
            message = st.session_state.results.get("message")

            with st.container(border=True):
                if grants:
                    st.markdown("Based on everything you shared with me, here's what I found:")
                    st.write("")

                    for i, grant in enumerate(grants):
                        title = grant.get("title", "Untitled Grant")
                        amount_range = format_amount_range(grant)
                        deadline = grant.get("deadline", "")
                        rationale = grant.get("rationale", "")
                        caveats = grant.get("caveats")

                        st.markdown(f"**{escape_dollars(title)}**")
                        if amount_range:
                            st.markdown(amount_range, unsafe_allow_html=True)
                        if deadline:
                            st.markdown(f"Deadline: {escape_dollars(deadline)}")
                        st.write("")
                        if rationale:
                            st.markdown(escape_dollars(rationale), unsafe_allow_html=True)
                        if caveats:
                            st.caption(f"Note: {caveats}")
                        st.write("")
                        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
                        with btn_col1:
                            if st.button("Apply \u2192", key=f"apply_{i}", type="primary"):
                                st.session_state.apply_grant = grant
                                st.session_state.phase = "apply"
                                st.rerun()
                        with btn_col2:
                            if st.button("Learn more", key=f"detail_{i}"):
                                # Find full grant data from grants.json by ID
                                grant_id = grant.get("id")
                                full_grant = next((g for g in GRANTS if g["id"] == grant_id), grant)
                                st.session_state.detail_grant = full_grant
                                st.session_state.phase = "grant_detail"
                                st.rerun()
                        st.write("")

                elif message:
                    st.markdown(escape_dollars(message), unsafe_allow_html=True)

                if near_misses:
                    st.write("---")
                    st.markdown("**Worth keeping an eye on:**")
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
            st.markdown('<p style="font-family: Inter, sans-serif; font-size: 16px; color: #666; margin-top: -8px;">Grant prospecting co-pilot</p>', unsafe_allow_html=True)
            st.write("")
            st.markdown("**Fill in what you know from the call.** Leave blank anything you didn't cover.")
            st.write("")
            st.markdown("""Organization:
Location (city, county, state):
Mission (in their words):
Who they serve:
Team size:
Annual budget:
Grant experience (first-time, some, experienced):
Current grants or funding (if any):
Grant size sweet spot:
How they'd use the funds (staffing, community partner, equipment, etc.):
Renewability (one-time OK, or needs multi-year/renewable):
Spending parameters they care about (indirect costs, FTE, restrictions):
What they're looking for:
What they want to avoid:
How urgently they need this (now, planning ahead, browsing):""")

            notes = st.text_area(
                "Call notes",
                height=300,
                placeholder="Fill in the fields above in any format. Messy is fine, Scout will sort it out.",
                label_visibility="collapsed",
                key=f"notes_{st.session_state.widget_key}",
            )

            if st.button("Find Grants", type="primary"):
                st.session_state.notes = notes
                st.session_state.phase = "searching"
                st.rerun()

            # Auto-focus the text area on page load
            st.components.v1.html("""
            <script>
            const textarea = window.parent.document.querySelector('textarea');
            if (textarea) textarea.focus();
            </script>
            """, height=0)
