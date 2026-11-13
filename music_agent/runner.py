"""Session-isolated ADK Runner integration, bounded calls, and evidence handling."""

# 1. Imports and safe response contracts never serialize provider exceptions.
import asyncio
import re
from time import perf_counter
from uuid import uuid4

from google.adk.agents.run_config import RunConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google import genai
from google.genai import types

from db import get_chart
from music_agent.agent import build_agents
from music_agent.errors import MESSAGES, error_status
from music_agent.guardrails import (
    REFUSAL, SCOPE_REFUSAL, INJECTION_REFUSAL, clean_search_query, destructive_catalog_request, forbids_web_search, requests_web_search, unrelated_request,
)
from music_agent.security import mask_pii, prompt_injection_request
from music_agent.observability import summarize_usage
from music_agent.retrieval import GeminiEmbedder, TheoryRetriever
from music_agent.session import INSTRUMENTS, SKILL_LEVELS
from music_agent.turn import CURRENT_TURN, TurnEvidence

APP_NAME = "music_agent"
TURN_TIMEOUT = 45


def safe_result(status: str, answer: str, trace: list[dict] | None = None) -> dict:
    """Build a display result with explicit provenance slots and no false sources."""
    return {
        "status": status, "answer": answer, "trace": trace or [],
        "internal_sources": [], "web_sources": [], "charts": [], "calculations": [],
        "offer_search": False, "search_query": "",
        "automatic_search": False, "local_status": "",
        "usage": summarize_usage([]),
    }


def with_usage(result: dict, evidence: TurnEvidence) -> dict:
    """Attach native token counts and paid-tier estimate to one display turn."""
    result["usage"] = summarize_usage(evidence.usage)
    return result


# 2. Result handling trusts tool evidence, not a model's prose labels or IDs.
def resolve_evidence(text: str, evidence: TurnEvidence, web: bool) -> dict:
    """Enforce source-backed outcomes and distinguish a genuine miss from error."""
    if web:
        if not evidence.web_sources:
            return safe_result("no_sources", MESSAGES["no_sources"], evidence.trace)
        # Only metadata-derived links are clickable in the separate Web results UI.
        text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
        text = re.sub(r"https?://\S+", "", text)
        result = safe_result("ok", text.strip() or "See the grounded sources below.", evidence.trace)
        result["web_sources"] = evidence.web_sources
        return result
    if not evidence.results:
        question = (
            text if text.strip().endswith("?")
            else "Which song or music learning topic would you like help with?"
        )
        result = safe_result("clarification", question, evidence.trace)
        # A permission question is a Search proposal, never a confirmed KB miss.
        if requests_web_search(question):
            result["status"] = "search_confirmation"
            result["offer_search"] = True
            result["search_query"] = clean_search_query(evidence.prompt)
        return result
    errors = [item for item in evidence.results if item["status"] == "error"]
    if errors:
        code = errors[-1].get("code", "error")
        return safe_result(code, MESSAGES.get(code, MESSAGES["error"]), evidence.trace)
    result = safe_result("ok", text or "Here is the catalog or internal-note result.", evidence.trace)
    unresolved_ambiguity = False
    selected_choice = None
    for item in evidence.results:
        if item["tool"] in {"transpose_chords", "transpose_song", "calculate_rhythm", "estimate_practice"} and item["status"] == "found":
            result["calculations"].append({key: item[key] for key in ("kind", "summary", "inputs", "outputs", "formula", "assumptions")})
        if item["tool"] == "search_theory_notes" and item["status"] == "found":
            for passage in item["passages"]:
                if passage["source_id"] not in {source["source_id"] for source in result["internal_sources"]}:
                    result["internal_sources"].append(passage)
        if item["tool"] == "get_chord_chart":
            choices = item.get("choices", [])
            if item["status"] == "ambiguous":
                explicit = [choice for choice in choices
                            if choice["artist"].casefold() in evidence.prompt.casefold()
                            and re.search(r"\b" + re.escape(choice["instrument"]) + r"\b", evidence.prompt, re.I)]
                if len(explicit) == 1:
                    selected_choice = explicit[0]
                    choices = explicit
                else:
                    unresolved_ambiguity = True
            ids = [item["chart"]["id"]] if item["status"] == "found" else [
                choice["chart_id"] for choice in choices
            ]
            for chart_id in ids:
                checked = get_chart(chart_id)
                if checked["status"] == "found" and chart_id not in {chart["id"] for chart in result["charts"]}:
                    result["charts"].append({
                        key: checked["chart"][key]
                        for key in ("id", "song_id", "title", "artist", "instrument", "attribution")
                    })
    if result["calculations"]:
        # Tool values are authoritative; do not display invented model arithmetic.
        result["answer"] = "\n\n".join(item["summary"] for item in result["calculations"])
    invalid = [item for item in evidence.results if item["status"] == "invalid_input"]
    if invalid:
        result["status"] = "invalid_input"
        result["answer"] = invalid[-1]["message"]
        return result
    misses = [item for item in evidence.results if item["status"] in ("not_found", "no_results")]
    if misses:
        if result["charts"] or result["internal_sources"] or result["calculations"]:
            result["status"] = "partial"
            result["answer"] += "\nPart of this question has no matching local source."
        else:
            result["status"] = "no_results"
            result["answer"] = (
                "No matching chords in the local catalog."
                if misses[-1]["tool"] == "get_chord_chart"
                else "The internal music notes do not cover this question."
            )
        result["offer_search"] = True
        result["search_query"] = clean_search_query(evidence.prompt)
    elif unresolved_ambiguity:
        result["status"] = "ambiguous"
        result["answer"] = "More than one chart matches. Choose an artist and arrangement below."
    elif selected_choice:
        result["answer"] = f"I found the {selected_choice['instrument']} chords for {selected_choice['title']} by {selected_choice['artist']}. Open Chords below to view the source and scope."
    return result


# 3. Separate in-memory sessions — never cache this object across visitors.
class AgentChatSession:
    """Own one visitor's ADK memory and opaque IDs, without retaining a key."""

    def __init__(self, model=None, retriever=None) -> None:
        self.user_id = uuid4().hex
        self.session_id = uuid4().hex
        self.session_service = InMemorySessionService()
        self.model = model
        self.retriever = retriever
        self._created = False

    async def send(
        self, prompt: str, api_key: str | None, profile: dict | None = None, web: bool = False,
        *, auto_search: bool = True, on_activity=None,
    ) -> dict:
        """Run one explicit request, with no automatic retry or persistence.

        Args:
            prompt: Current user question; bounded to 2000 characters.
            api_key: Server-resolved Google key; never put in ADK/session state.
            profile: Only allowlisted instrument and skill level are sent to root.
            web: True to invoke Search directly in a fresh query-only session.
            auto_search: Follow confirmed misses with one isolated Web Search.
                Explicit local-only user instructions always take precedence.
            on_activity: Session-owned observer of real agent/tool callbacks.

        Returns:
            A safe status, answer, actual sources/chart choices, compact trace,
            and whether an automatic query-only fallback was actually attempted.
        """
        started = perf_counter()
        prompt = prompt.strip()[:2000]
        if not prompt:
            return safe_result("clarification", "Ask a song chart or music learning question.")
        if prompt_injection_request(prompt):
            evidence = TurnEvidence("", on_activity=on_activity)
            evidence.record("riffin_coordinator", "input_guardrail", "blocked", started)
            return safe_result("blocked", INJECTION_REFUSAL, evidence.trace)
        prompt = mask_pii(prompt)
        if destructive_catalog_request(prompt):
            evidence = TurnEvidence(prompt, on_activity=on_activity)
            evidence.record("riffin_coordinator", "guardrail", "blocked", started)
            return safe_result("blocked", REFUSAL, evidence.trace)
        if unrelated_request(prompt):
            evidence = TurnEvidence(prompt, on_activity=on_activity)
            evidence.record("riffin_coordinator", "scope_guardrail", "out_of_scope", started)
            return safe_result("out_of_scope", SCOPE_REFUSAL, evidence.trace)
        if not api_key and self.model is None:
            return safe_result("credentials_unavailable", MESSAGES["credentials_unavailable"])
        explicit_search = requests_web_search(prompt)
        evidence = TurnEvidence(prompt, allow_web=web or explicit_search,
                                search_query=clean_search_query(prompt), on_activity=on_activity)
        token = CURRENT_TURN.set(evidence)
        client = None
        runners = []
        fallback_started = False
        local_result = None
        try:
            async with asyncio.timeout(TURN_TIMEOUT):
                if self.model is None:
                    client = genai.Client(
                        api_key=api_key, vertexai=False,
                        http_options=types.HttpOptions(
                            timeout=15000, retry_options=types.HttpRetryOptions(attempts=1),
                        ),
                    )
                evidence.retriever = self.retriever or TheoryRetriever(GeminiEmbedder(client))
                agents = build_agents(model=self.model, client=client)
                if web:
                    # No profile, chat transcript, earlier ADK events, or shared state.
                    service = InMemorySessionService()
                    session = await service.create_session(app_name=APP_NAME, user_id=uuid4().hex)
                    agent, user_id, session_id = agents["search"], session.user_id, session.id
                    message_text, state_delta = evidence.search_query, None
                else:
                    service = self.session_service
                    if not self._created:
                        await service.create_session(
                            app_name=APP_NAME, user_id=self.user_id, session_id=self.session_id,
                        )
                        self._created = True
                    agent, user_id, session_id = agents["root"], self.user_id, self.session_id
                    supplied = profile or {}
                    state_delta = {}
                    for key, allowed in (("instrument", INSTRUMENTS), ("skill_level", SKILL_LEVELS)):
                        if supplied.get(key) in allowed:
                            state_delta[key] = supplied[key]
                    message_text = prompt
                runner = Runner(agent=agent, app_name=APP_NAME, session_service=service)
                runners.append(runner)
                # 4. Event handling — only final non-thought model text is displayed.
                answer = await consume_events(runner, user_id, session_id, message_text, state_delta, evidence)
                if evidence.failure_code:
                    return with_usage(safe_result(evidence.failure_code, MESSAGES[evidence.failure_code], evidence.trace), evidence)
                searched = web or any(row["agent"] == "google_search_specialist" for row in evidence.trace)
                result = resolve_evidence(answer, evidence, searched)
                # 5. One automatic fallback per submitted turn; errors/ambiguity never trigger it.
                if (auto_search and not searched and not forbids_web_search(prompt)
                        and result["offer_search"] and result["status"] in {"no_results", "partial", "search_confirmation"}):
                    fallback_started = True
                    local_result = result
                    evidence.allow_web = True
                    evidence.announce("google_search_specialist", "automatic_fallback", "running")
                    fresh_service = InMemorySessionService()
                    fresh = await fresh_service.create_session(app_name=APP_NAME, user_id=uuid4().hex)
                    search_runner = Runner(agent=agents["search"], app_name=APP_NAME, session_service=fresh_service)
                    runners.append(search_runner)
                    searched_answer = await consume_events(
                        search_runner, fresh.user_id, fresh.id, evidence.search_query, None, evidence,
                    )
                    code = evidence.failure_code
                    fallback = safe_result(code, MESSAGES[code], evidence.trace) if code else resolve_evidence(searched_answer, evidence, True)
                    fallback.update(automatic_search=True, local_status=result["status"],
                                    internal_sources=result["internal_sources"], charts=result["charts"], calculations=result["calculations"])
                    if result["status"] == "partial":
                        fallback["answer"] = answer + "\n\nWeb lookup:\n" + fallback["answer"]
                    return with_usage(fallback, evidence)
                if forbids_web_search(prompt):
                    result["offer_search"] = False
                    result["search_query"] = ""
                    if result["status"] == "no_results":
                        result["answer"] = "No relevant local source was found. Kept this request local as you asked."
                    elif result["status"] in {"partial", "search_confirmation"}:
                        result["answer"] += "\nKept this request local as you asked."
                return with_usage(result, evidence)
        except Exception as error:
            code = error_status(error)
            evidence.record("google_search_specialist" if web or fallback_started else "riffin_coordinator", "request", code, started)
            failure = safe_result(code, MESSAGES[code], evidence.trace)
            if fallback_started:
                failure.update(automatic_search=True, local_status=local_result["status"],
                               charts=local_result["charts"], internal_sources=local_result["internal_sources"], calculations=local_result["calculations"])
            return with_usage(failure, evidence)
        finally:
            try:
                for runner in reversed(runners):
                    await runner.close()
                if client:
                    await client.aio.aclose()
                    client.close()
            finally:
                CURRENT_TURN.reset(token)


# 6. A shared event consumer handles both root routing and the isolated fallback.
async def consume_events(runner, user_id, session_id, message, state_delta, evidence) -> str:
    """Consume real ADK events, without publishing thoughts or tool arguments."""
    answer = ""
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=message)]),
        state_delta=state_delta, run_config=RunConfig(max_llm_calls=8),
    ):
        if event.error_code or event.error_message:
            evidence.failure_code = evidence.failure_code or "error"
            break
        if event.is_final_response() and event.content:
            answer = "\n".join(p.text for p in event.content.parts or [] if p.text and not p.thought)
    return answer
