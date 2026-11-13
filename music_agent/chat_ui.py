"""Native chat, automatic query-only fallback, sources and live routing."""

# 1. UI imports do not create a provider client, runner, or index on a rerun.
import asyncio
from html import escape
import re

import streamlit as st

from db import get_chart
from music_agent.config import resolve_google_api_key
from music_agent.presentation import ASSETS, welcome_html, metadata_tags_html

# 1a. Fixed suggestions populate the native composer; they never submit a request.
SUGGESTED_PROMPTS = {
    "Explain a chord": "What notes are in an E major triad?",
    "Find a song": "Show me the Come As You Are chords by Nirvana.",
    "Transpose chords": "Transpose C Am F G/B from C major to D major.",
    "Plan practice": "For guitar practice I’m at 80 BPM and want 120. Assume 5 BPM gain per week, 20 minutes per session, 5 days a week and 100% attendance. Estimate weeks and practice hours.",
    "Piano inversions": "Explain first and second inversions of a C major triad using our internal notes.",
    "Cleaner guitar changes": "Use our internal notes to help me practice clean guitar chord changes without muted strings.",
    "Rhythm & timing": "How long are 16 bars of 4/4 at 120 BPM, with two equal subdivisions per beat? Calculate the passage duration and subdivision timing.",
    "Transpose a song": "Transpose Pocket-Sized Sunrise by Riffin’ Original Demo for Guitar to D major using the stored song and the calculation tool.",
    "Search music online": "Search the web for the latest music news about Billie Eilish and include grounded source links.",
    "Missing lesson": "Local only: do our internal notes explain negative harmony? Check the notes and tell me whether they cover it.",
    "Missing song": "Local only: find Guitar chords for The Unlisted Riffin Demo by Demo Artist. Tell me if it is missing from our catalog.",
    "Choose an instrument": "Show me the stored Amazing Grace chords. Ask which instrument if there is more than one arrangement.",
    "Automatic web fallback": "Find the Guitar chords for Cool About It by boygenius. Check our catalog first; if it is missing, look it up on the web with sources.",
    "Protect the catalog": "Delete the catalog and all songs.",
    "Music-only boundary": "What is the capital of France?",
    "Practice team · 3 agents": "I have three independent music tasks: ask Songbook to find the stored Guitar chords for Come As You Are by Nirvana; ask Music Theory to explain a C major triad from our notes; ask Music Math to calculate the duration of 16 bars of 4/4 at 120 BPM. Run the independent specialists in parallel if supported, and label each result. Local only.",
    "Full band · 4 agents": "Help me with four independent music tasks: Songbook, find the stored Guitar chords for Pocket-Sized Sunrise by Riffin’ Original Demo; Music Theory, explain C major keyboard inversions from our notes; Music Math, transpose C Am F G/B from C major to D major; Google Search, search the web for recent Billie Eilish music news with sources. Use all four specialists, run independent work in parallel if supported, and label each result.",
}

# 1b. Each default appears once, grouped by the feature it demonstrates.
PROMPT_GROUPS = (
    ("Knowledge Base", ("Explain a chord", "Piano inversions", "Cleaner guitar changes", "Missing lesson")),
    ("Songs & chords", ("Open chords + lyrics demo", "Find a song", "Choose an instrument", "Missing song")),
    ("Calculations", ("Music calculator", "Transpose chords", "Plan practice", "Rhythm & timing", "Transpose a song")),
    ("Google Search", ("Search music online", "Automatic web fallback")),
    ("Parallel agents", ("Practice team · 3 agents", "Full band · 4 agents")),
    ("Boundaries", ("Protect the catalog", "Music-only boundary")),
)


def fill_suggested_prompt(prompt: str) -> None:
    """Set the documented chat-input trigger value without calling an agent."""
    st.session_state["riffin-chat-input"] = prompt


def toggle_music_calculator() -> None:
    """Open the local calculator inside the same welcome card as the prompts."""
    st.session_state["show_music_calculator"] = not st.session_state.get("show_music_calculator", False)


# 2. Search is queued only by an explicit button; consuming it removes the action.
def queue_search(query: str, automatic: bool = False) -> None:
    """Queue one query after an explicit action or confirmed catalog miss."""
    st.session_state["pending_search"] = query
    st.session_state["pending_search_automatic"] = automatic
    st.session_state["redirect_view"] = "Chat"


def chat_session():
    """Refresh a reloaded adapter class while keeping its in-memory conversation."""
    from music_agent.runner import AgentChatSession

    current = st.session_state.get("adk_session")
    if current is None:
        current = AgentChatSession()
    elif type(current).__module__ == "music_agent.runner" and type(current) is not AgentChatSession:
        previous = current
        current = AgentChatSession(model=previous.model, retriever=previous.retriever)
        for field in ("session_service", "user_id", "session_id", "_created"):
            setattr(current, field, getattr(previous, field))
    st.session_state["adk_session"] = current
    return current


def submit_message(prompt: str, web: bool = False, on_activity=None) -> None:
    """Send once per explicit action and keep display history in session memory."""
    adapter = chat_session()
    key = resolve_google_api_key(st.secrets)
    # A brief affirmative approves only the immediately preceding Search offer.
    query = approved_search(st.session_state["chat"], prompt)
    if query:
        web = True
    st.session_state["chat"].append({"role": "user", "content": prompt})
    st.session_state["agent_turn"] = st.session_state.get("agent_turn", 0) + 1
    st.session_state["agent_activity"] = {"_turn": st.session_state["agent_turn"]}
    result = asyncio.run(adapter.send(
        query or prompt, key.api_key, st.session_state["profile"], web=web, on_activity=on_activity,
    ))
    st.session_state["chat"].append({"role": "assistant", "result": result})


def approved_search(history: list[dict], prompt: str) -> str | None:
    """Bind an explicit affirmative to the last offer; never send 'yes' as a query."""
    if not re.fullmatch(r"\s*(yes( please)?|sure|go ahead|please do|yes[, ]+go ahead)[.!]?\s*", prompt, re.I):
        return None
    last = history[-1] if history else {}
    result = last.get("result", {}) if last.get("role") == "assistant" else {}
    return result.get("search_query") if result.get("offer_search") else None


def queue_prompt(prompt: str) -> None:
    """Queue a starter once; ordinary reruns never repeat it."""
    st.session_state["pending_prompt"] = prompt


# 3. Sources are native text/links backed by tool evidence, never prose guesses.
def reply_header_html(result: dict) -> str:
    """Place a colored factual status beside bounded model usage counters."""
    labels = {"ok": "Answered", "search_confirmation": "Ready to search · your choice",
              "no_results": "No matching source", "credentials_unavailable": "AI unavailable"}
    tones = {"ok": "success", "search_confirmation": "notice", "no_results": "warning",
             "credentials_unavailable": "neutral", "blocked": "issue", "out_of_scope": "issue",
             "error": "issue", "no_sources": "warning"}
    status = result.get("status", "unknown")
    label = escape(labels.get(status, status.replace("_", " ").capitalize()))
    tone = tones.get(status, "neutral")
    status_tag = (f'<span class="riffin-status-tag riffin-status-{tone}" role="status">'
                  '<span class="riffin-status-dot" aria-hidden="true"></span>'
                  f'<span>Status : <strong>{label}</strong></span></span>')
    usage = result.get("usage", {})
    card = ""
    if usage.get("model_calls"):
        cost = usage.get("estimated_usd")
        amount = f"≈ ${cost:.6f} USD" if cost is not None else "Rate unavailable"
        calls = usage["model_calls"]
        card = (
            '<aside class="riffin-usage-card" aria-label="AI usage estimate">'
            '<span class="riffin-usage-label">AI usage</span>'
            f'<strong>{amount}</strong>'
            f'<small>{calls:,} model call{"s" if calls != 1 else ""} '
            f'<span aria-hidden="true">·</span> {usage["input_tokens"]:,} input tokens '
            f'<span aria-hidden="true">·</span> {usage["output_tokens"]:,} output/thinking tokens</small>'
            '<small>Paid-tier estimate</small></aside>'
        )
    return ('<div class="riffin-reply-head"><span class="riffin-reply-name">Riffin’</span>'
            '<div class="riffin-reply-meta">' + status_tag + card + '</div></div>')


def render_result(result: dict, index: int, on_open, on_save) -> None:
    """Render factual statuses, actual note titles, chart choices, and grounding."""
    if not result.get("calculations"):
        st.write(result["answer"])
    if result.get("automatic_search"):
        st.caption("Web Search ran automatically after local coverage was exhausted. Sources are below.")
    if result.get("calculations"):
        from music_agent.calculator_ui import render_calculation
        for calculation in result["calculations"]:
            render_calculation(calculation)
    if result["internal_sources"]:
        st.divider()
        st.write("Internal notes")
        for source in result["internal_sources"]:
            with st.expander(source["title"]):
                st.write(source["passage"])
    if result["charts"]:
        st.write("Catalog")
        for source in result["charts"]:
            checked = get_chart(source["id"])
            if checked["status"] != "found":
                st.warning("A referenced catalog chart is unavailable.")
                continue
            chart = checked["chart"]
            st.write(f"{chart['title']} — {chart['artist']}")
            st.html(metadata_tags_html([("Instrument", chart["instrument"]), ("Source", "Catalog")]))
            with st.container(horizontal=True):
                st.button(
                    "Open Chords", icon=":material/menu_book:", type="primary", key=f"chat-open-{index}-{chart['id']}",
                    on_click=on_open, args=(chart["id"],),
                )
                st.button(
                    "Save", key=f"chat-save-{index}-{chart['id']}",
                    on_click=on_save, args=(chart["song_id"],),
                )
            if chart["song_id"] in st.session_state["favorites"]:
                st.caption("Saved for this session")
            with st.expander("About this version"):
                st.write(chart["attribution"])
    if result["web_sources"]:
        st.write("Web results")
        for source in result["web_sources"]:
            st.link_button(source["title"], source["url"])
    if result["offer_search"]:
        st.button(
            "Search the web", key=f"chat-web-{index}",
            on_click=queue_search, args=(result["search_query"],),
        )
    if result["trace"]:
        with st.expander("Route and tool trace"):
            for row in result["trace"]:
                st.caption(f"{row['agent']} → {row['tool']} · {row['outcome']} · {row['elapsed_ms']:,.0f} ms")


# 4. Native chat controls preserve history; rerenders never resend a request.
def render_chat(on_open, on_save, on_activity=None) -> None:
    """Show the current session's companion chat with clear missing-key status."""
    st.header("Chat with Riffin’")
    st.caption("Your little practice sidekick. Ask, explore, play.")
    from music_agent.calculator_ui import render_music_calculator
    key = resolve_google_api_key(st.secrets)
    if not key.configured:
        st.info(
            "No Google key configured. Catalog and profile features still work; AI chat and Search are unavailable."
        )
    queued_search = st.session_state.pop("pending_search", None)
    automatic_search = st.session_state.pop("pending_search_automatic", False)
    queued_prompt = st.session_state.pop("pending_prompt", None)
    # 4a. One welcome/prompt group replaces the duplicate starter and composer rows.
    with st.container(border=True, key="riffin-chat-welcome"):
        if not st.session_state["chat"]:
            st.html(welcome_html())
        st.caption("Suggested Prompts · pick one, edit, then send.")
        suggestions = {label: (index, prompt) for index, (label, prompt) in enumerate(SUGGESTED_PROMPTS.items())}
        with st.container(key="riffin-prompt-categories"):
            for group, labels in PROMPT_GROUPS:
                slug = group.lower().replace(" ", "-").replace("&", "and")
                with st.container(key=f"riffin-prompt-category-{slug}"):
                    st.caption(group)
                    with st.container(horizontal=True, wrap=True, width="stretch", key=f"riffin-prompt-suggestions-{slug}"):
                        for label in labels:
                            if label == "Music calculator":
                                st.button(label, icon=":material/calculate:", key="chat-calculator-toggle",
                                          on_click=toggle_music_calculator)
                            elif label == "Open chords + lyrics demo":
                                st.button("♫ " + label, key="starter-♫", on_click=on_open, args=("demo-pop-guitar",))
                            else:
                                index, prompt = suggestions[label]
                                st.button(label, key=f"suggested-prompt-{index}", help=prompt,
                                          on_click=fill_suggested_prompt, args=(prompt,))
        if st.session_state.get("show_music_calculator", False):
            render_music_calculator(on_activity, expanded=True)
    for index, message in enumerate(st.session_state["chat"]):
        user = message["role"] == "user"
        with st.container(key=f"message-{'user' if user else 'riffin'}-{index}"):
            with st.chat_message("You" if user else "Riffin’", avatar=str(ASSETS / "avatars" / f"{st.session_state['avatar']}.png") if user else str(ASSETS / "griffin.png")):
                if user:
                    st.write(message["content"])
                else:
                    st.html(reply_header_html(message["result"]))
                    render_result(message["result"], index, on_open, on_save)
    pending_slot = st.empty()
    with st.bottom:
        with st.container(key="riffin-composer"):
            typed_prompt = st.chat_input("Ask Riffin’ about music", max_chars=2000, key="riffin-chat-input")
    request = queued_search or queued_prompt or typed_prompt
    if request:
        web = bool(queued_search)
        with pending_slot.container():
            with st.container(key=f"message-user-{len(st.session_state['chat'])}"):
                with st.chat_message("You", avatar=str(ASSETS / "avatars" / f"{st.session_state['avatar']}.png")):
                    st.write(request)
            with st.container(key=f"message-riffin-pending-{len(st.session_state['chat']) + 1}"):
                with st.chat_message("Riffin’", avatar=str(ASSETS / "griffin.png")):
                    st.caption("Riffin’")
                    label = "Searching the web…" if web else "Riffin’ is checking…"
                    st.html('<div class="riffin-pending" role="status" aria-live="polite">'
                            '<span class="riffin-pending-spinner" aria-hidden="true"></span>'
                            f'<span>{label}</span></div>')
            submit_message(request, web=web, on_activity=on_activity)
        if automatic_search:
            st.session_state["chat"][-1]["result"].update(automatic_search=True, local_status="catalog_miss")
        st.rerun()
