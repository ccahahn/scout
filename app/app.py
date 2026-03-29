import json
import streamlit as st
from pipeline import run_transcriber, run_pipeline, run_chat_followup, escape_dollars

st.set_page_config(page_title="Scout by Instrumentl", layout="centered")

# ---- Brand colors ----
PURPLE = "#5b56b2"
CORAL = "#f26f63"
LIGHT_PURPLE = "#7b77c9"

# ---- Global styles ----
st.markdown(f"""
<style>
/* Scout title */
h1 {{
    color: {PURPLE} !important;
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
    font-size: 14px;
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
    font-size: 14px;
}}

/* Pre-filled field styling */
.prefilled {{
    background: #f0eef9;
    border: 1px solid #d4d0e8;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 4px 0 16px 0;
    font-size: 14px;
    color: #333;
}}
.prefilled-label {{
    font-size: 12px;
    font-weight: 600;
    color: #666;
    margin-bottom: 2px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}}
.prefilled-badge {{
    display: inline-block;
    background: {LIGHT_PURPLE};
    color: white;
    font-size: 10px;
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
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    border: none;
}}
.apply-btn:hover {{
    background: #e05a4e;
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
    st.session_state.widget_key += 1

def go_back_to_intake():
    st.session_state.phase = "intake"



# ---- Shared CSS for thinking box ----
THINKING_CSS = f"""
<style>
.thinking-scroll {{
    height: 60vh;
    overflow-y: auto;
    display: flex;
    flex-direction: column-reverse;
}}
.thinking-box {{
    background: #f7f7f8;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px;
    font-family: monospace;
    font-size: 13px;
    line-height: 1.6;
    color: #555;
    white-space: pre-wrap;
    word-wrap: break-word;
}}
.thinking-section {{ color: #555; }}
.scorer-section {{ color: #2e7d32; }}
.section-label {{
    display: inline-block;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 16px 0 8px 0;
    padding: 2px 8px;
    border-radius: 4px;
}}
.label-scout {{ background: #e8eaf6; color: #3949ab; }}
.label-scorer {{ background: #e8f5e9; color: #2e7d32; }}
</style>
"""

def make_thinking_ui():
    """Create the thinking box UI elements and return callbacks."""
    st.markdown(THINKING_CSS, unsafe_allow_html=True)
    status_label = st.empty()
    status_label.caption("Reading your notes...")
    thinking_container = st.empty()

    current_thinking = []
    current_scorer = []

    def render_box():
        parts = []
        if current_thinking:
            parts.append('<div class="section-label label-scout">Scout - filtering</div>')
            parts.append(f'<div class="thinking-section">{"".join(current_thinking)}</div>')
        if current_scorer:
            parts.append('<div class="section-label label-scorer">Scorer - quality check</div>')
            parts.append(f'<div class="scorer-section">{"".join(current_scorer)}</div>')
        html = "".join(parts)
        thinking_container.markdown(
            f'<div class="thinking-scroll"><div><div class="thinking-box">{html}</div></div></div>',
            unsafe_allow_html=True,
        )

    def on_thinking(chunk):
        current_thinking.append(chunk)
        render_box()

    def on_scorer(chunk):
        current_scorer.append(chunk)
        render_box()

    def on_status(msg):
        status_label.caption(f"{msg}")

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
                        st.markdown(f"- {q}")
                else:
                    st.markdown(str(questions))
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

                        st.markdown(f"**{title}**")
                        if amount_range:
                            st.markdown(amount_range, unsafe_allow_html=True)
                        if deadline:
                            st.markdown(f"Deadline: {deadline}")
                        st.write("")
                        if rationale:
                            st.markdown(escape_dollars(rationale), unsafe_allow_html=True)
                        if caveats:
                            st.caption(f"Note: {caveats}")
                        st.write("")
                        if st.button("Apply \u2192", key=f"apply_{i}", type="primary"):
                            st.session_state.apply_grant = grant
                            st.session_state.phase = "apply"
                            st.rerun()
                        st.write("")

                elif message:
                    st.markdown(message)

                if near_misses:
                    st.write("---")
                    st.markdown("**Worth keeping an eye on:**")
                    st.write("")
                    for nm in near_misses:
                        st.markdown(f"**{nm.get('title', '')}**")
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
                    st.markdown(msg["content"], unsafe_allow_html=True)

            # Chat input
            if prompt := st.chat_input("Ask about these grants, or tell me what to look for next..."):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
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
            st.caption("Grant prospecting co-pilot (v2)")
            st.write("")
            st.markdown("**Fill in what you know from the call.** Leave blank anything you didn't cover.")
            st.text("""Organization:
Location (city, county, state):
Mission (in their words):
Who they serve:
Team size:
Annual budget:
Grant experience (first-time, some, experienced):
Grant size sweet spot:
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
