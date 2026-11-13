"""Read-only policy, consented query-only Search, and redacted ADK callbacks."""

# 1. Guardrails — reject obvious catalog writes without needing a provider.
import re
import sqlite3
from time import perf_counter
from urllib.parse import urlparse

from google.genai import types

from music_agent.turn import CURRENT_TURN
from music_agent.errors import MESSAGES, error_status
from music_agent.security import mask_pii, prompt_injection_request
from music_agent.observability import usage_from_response

REFUSAL = "I can't delete or modify the catalog. It is read-only. You can open charts and save songs for this session."
SCOPE_REFUSAL = MESSAGES["out_of_scope"]
INJECTION_REFUSAL = "I can help with music, but I can't follow instructions to override my safeguards or reveal private configuration."
REGISTERED = {
    "riffin_coordinator": {"songbook", "music_theory", "google_search_specialist", "music_math"},
    "songbook": {"get_chord_chart"}, "music_theory": {"search_theory_notes"},
    "google_search_specialist": {"google_search"},
    "music_math": {"transpose_chords", "transpose_song", "calculate_rhythm", "estimate_practice"},
}


def unrelated_request(prompt: str) -> bool:
    """Reject clear unrelated intent locally; leave short music follow-ups usable.

    This lexical gate complements the coordinator's semantic scope instruction.
    It is a product boundary, not a claim to perfectly classify every paraphrase.
    """
    creative = re.search(r"\b(write|compose|create)\b.{0,35}\b(song|lyrics|melody)\b", prompt, re.I)
    unrelated = re.search(r"\b(weather|capital of|stock prices?|crypto|bitcoin|tax return|election|president|football scores?|recipe|cook pasta|debug|python code|javascript code|sql injection|solve my homework)\b", prompt, re.I)
    if unrelated and not creative:
        return True
    music = re.search(r"\b(music|songs?|chords?|charts?|guitar|piano|keyboard|triads?|inversions?|scales?|transpose|transposition|bpm|tempo|rhythm|beats?|bars?|metronome|practice|practicing|practise|synthesizers?|synthesiser|artist|album|spotify|singer|lyrics|melody|harmony|jazz|rock|pop|folk|classical|electronic|semitones?|capo|tuning|riff|strum|concert|singing|drums?|violin|bass|sheet music|midi|arpeggio)\b", prompt, re.I)
    if music:
        return False
    from db import list_songs, normalize_identity
    try:
        songs = list_songs()
        if normalize_identity(prompt) in {normalize_identity(song["title"]) for song in songs}:
            return False
        if any(len(song["artist"]) >= 5 and re.search(r"\b" + re.escape(song["artist"]) + r"\b", prompt, re.I) for song in songs):
            return False
    except (OSError, ValueError, sqlite3.Error):
        pass
    if re.match(r"^\s*(and |what about |how about |can you explain |please clarify )", prompt, re.I):
        return False
    # Courtesy and elliptical follow-ups carry no unrelated factual request.
    return not bool(re.fullmatch(r"\s*(hi|hello|hey|thanks|thank you|yes( please)?|no|sure|go ahead|please do|why|how so|explain (that|more)|what about (that|this)|tell me more)[.!? ]*", prompt, re.I))


def destructive_catalog_request(prompt: str) -> bool:
    """Match destructive catalog intent without blocking ordinary music advice."""
    action = re.search(
        r"\b(delete|drop|erase|wipe|truncate|destroy|remove|overwrite|update|insert|alter)\b", prompt, re.I,
    )
    target = re.search(r"\b(catalog|database|sqlite|tables?|all songs|songs table|chord_charts)\b", prompt, re.I)
    return bool(action and target)


def requests_web_search(prompt: str) -> bool:
    """Require an explicit web/online/Google request, rather than a bare 'search'."""
    if forbids_web_search(prompt):
        return False
    return bool(re.search(
        r"\b(search|look|find|check|browse)\b.{0,60}\b(web|online|internet)\b|"
        r"\b(web search|google search|search google|google this|google it)\b|"
        r"^\s*(please\s+)?google\b|\b(can|could|would)\s+you\s+(please\s+)?google\b",
        prompt, re.I | re.S,
    ))


def forbids_web_search(prompt: str) -> bool:
    """An explicit local-only instruction overrides the app's automatic fallback."""
    return bool(re.search(
        r"\b(do not|don't|never|without)\b.{0,35}\b(search|brows\w*|google|web|online)\b|"
        r"\b(local|internal|offline|catalog|notes)[ -]only\b|\bonly (use|search) (the )?(local|internal|catalog|notes)\b",
        prompt, re.I,
    ))


def clean_search_query(prompt: str) -> str:
    """Use the user-approved question only, with no appended profile or history."""
    query = re.sub(
        r"^\s*(please\s+)?(search\s+(the\s+)?(web|internet|online)|search google|google search)\s*[:,-]?\s*",
        "", prompt, flags=re.I,
    )
    return " ".join(re.sub(r"[\x00-\x1f<>]", " ", query).split())[:500]


def current_prompt(context) -> str:
    """Read only the current invocation for the callback and ADK Dev UI guard."""
    evidence = CURRENT_TURN.get()
    if evidence:
        return evidence.prompt
    content = context.user_content
    return " ".join(part.text for part in (content.parts or []) if part.text) if content else ""


# 2. Agent callbacks record routing without user IDs, prompts, or full results.
def before_agent(callback_context):
    """Refuse destructive requests before any model call and start route timing."""
    evidence = CURRENT_TURN.get()
    if evidence:
        evidence.started[(callback_context.agent_name, "agent")] = perf_counter()
        evidence.announce(callback_context.agent_name, "agent", "running")
    if prompt_injection_request(current_prompt(callback_context)):
        if evidence:
            evidence.record(callback_context.agent_name, "input_guardrail", "blocked", perf_counter())
        return types.Content(role="model", parts=[types.Part(text=INJECTION_REFUSAL)])
    if destructive_catalog_request(current_prompt(callback_context)):
        if evidence:
            evidence.record(callback_context.agent_name, "guardrail", "blocked", perf_counter())
        return types.Content(role="model", parts=[types.Part(text=REFUSAL)])
    if unrelated_request(current_prompt(callback_context)):
        if evidence:
            evidence.failure_code = "out_of_scope"
            evidence.record(callback_context.agent_name, "scope_guardrail", "out_of_scope", perf_counter())
        return types.Content(role="model", parts=[types.Part(text=SCOPE_REFUSAL)])
    return None


def after_agent(callback_context):
    """Finish the route entry; outcome labels describe execution, not correctness."""
    evidence = CURRENT_TURN.get()
    if evidence:
        start = evidence.started.pop((callback_context.agent_name, "agent"), perf_counter())
        evidence.record(callback_context.agent_name, "agent", "completed", start)
    return None


# 3. Tool callbacks enforce the registry and explicit web authorization.
def before_tool(tool, args, tool_context):
    """Validate tool permissions and replace Search arguments with approved text."""
    evidence = CURRENT_TURN.get()
    agent = tool_context.agent_name
    if unrelated_request(current_prompt(tool_context)):
        return {"status": "blocked", "message": SCOPE_REFUSAL}
    if evidence:
        evidence.started[(agent, tool.name)] = perf_counter()
        evidence.announce(agent, tool.name, "running")
    if tool.name not in REGISTERED.get(agent, set()):
        return {"status": "blocked", "message": "This tool is not registered for this agent."}
    if tool.name == "google_search_specialist":
        prompt = current_prompt(tool_context)
        allowed = evidence.allow_web if evidence else requests_web_search(prompt)
        if not allowed:
            if evidence:
                evidence.record(agent, tool.name, "blocked", perf_counter())
            return {"status": "blocked", "message": "Search needs an explicit music request or a confirmed-miss fallback handled by the app."}
        # Ignore a model-supplied request that could include copied conversation.
        args.clear()
        args["request"] = evidence.search_query if evidence else clean_search_query(prompt)
    return None


def after_tool(tool, args, tool_context, tool_response):
    """Expose only a controlled status and elapsed time in the demo trace."""
    evidence = CURRENT_TURN.get()
    if evidence:
        agent = tool_context.agent_name
        start = evidence.started.pop((agent, tool.name), perf_counter())
        status = tool_response.get("status", "completed") if isinstance(tool_response, dict) else "completed"
        allowed = {"found", "not_found", "ambiguous", "error", "no_results", "blocked", "completed", "invalid_input"}
        evidence.record(agent, tool.name, status if status in allowed else "completed", start)
    return None


# 4. Grounding is evidence from Gemini metadata, never model-written URLs.
def grounding_sources(metadata) -> list[dict]:
    """Extract bounded usable HTTP(S) links from returned grounding chunks."""
    sources = []
    for chunk in getattr(metadata, "grounding_chunks", None) or []:
        web = getattr(chunk, "web", None)
        url = getattr(web, "uri", "") if web else ""
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https") and parsed.netloc and url not in {item["url"] for item in sources}:
            sources.append({"url": url, "title": getattr(web, "title", "") or parsed.netloc})
        if len(sources) >= 8:
            break
    return sources


def before_model(callback_context, llm_request):
    """Search sees one approved query, regardless of coordinator history/state."""
    evidence = CURRENT_TURN.get()
    if evidence:
        evidence.started[(callback_context.agent_name, "model")] = perf_counter()
        evidence.announce(callback_context.agent_name, "model", "running")
    for content in llm_request.contents or []:
        if content.role == "user":
            for part in content.parts or []:
                if part.text:
                    part.text = mask_pii(part.text)
    if callback_context.agent_name == "google_search_specialist" and evidence:
        llm_request.contents = [types.Content(role="user", parts=[types.Part(text=evidence.search_query)])]
        evidence.started[(callback_context.agent_name, "google_search")] = perf_counter()
    return None


def on_model_error(callback_context, llm_request, error):
    """Consume provider exceptions before ADK can log raw exception details."""
    from google.adk.models.llm_response import LlmResponse

    code = error_status(error)
    evidence = CURRENT_TURN.get()
    if evidence:
        evidence.failure_code = code
        start = evidence.started.pop((callback_context.agent_name, "model"), perf_counter())
        evidence.record(callback_context.agent_name, "model", code, start)
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=MESSAGES[code])]))


def after_model(callback_context, llm_response):
    """Capture native Search grounding even inside nested AgentTool execution."""
    evidence = CURRENT_TURN.get()
    if evidence and not llm_response.partial:
        entry = usage_from_response(llm_response, callback_context.agent_name)
        if entry:
            evidence.usage.append(entry)
    if callback_context.agent_name == "google_search_specialist" and evidence and not llm_response.partial:
        sources = grounding_sources(llm_response.grounding_metadata)
        for source in sources:
            if source not in evidence.web_sources:
                evidence.web_sources.append(source)
        start = evidence.started.pop((callback_context.agent_name, "google_search"), perf_counter())
        evidence.record(callback_context.agent_name, "google_search", "grounded" if sources else "not_observed", start)
    return None
