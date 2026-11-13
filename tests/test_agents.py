"""Exercise real ADK AgentTools/Runner with explicitly scripted model responses."""

# 1. Tests never contact Gemini or claim that fixture URLs are live results.
import asyncio
import hashlib
import json
import unittest
from unittest.mock import patch
from uuid import uuid4

from google.adk.agents.run_config import RunConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import AgentTool, google_search
from google.genai import types

from agent_fixtures import FixtureEmbedder, ScriptedModel
from db import CATALOG_PATH, get_chart
from music_agent import root_agent
from music_agent.agent import build_agents
from music_agent.errors import error_status
from music_agent.guardrails import REFUSAL, destructive_catalog_request, requests_web_search
from music_agent.retrieval import TheoryRetriever
from music_agent.runner import APP_NAME, AgentChatSession, resolve_evidence
from music_agent.turn import TurnEvidence
from music_agent.tools import get_chord_chart, search_theory_notes


class AgentIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def retriever(self):
        return TheoryRetriever(FixtureEmbedder(), cache_namespace=f"agent-fixture-{uuid4().hex}")

    # 2. Real ADK definitions expose only the intended specialist/tool registry.
    def test_exported_lab5_agent_graph_and_docstrings(self):
        self.assertEqual(root_agent.name, "riffin_coordinator")
        self.assertTrue(all(isinstance(tool, AgentTool) for tool in root_agent.tools))
        self.assertEqual([tool.name for tool in root_agent.tools], ["songbook", "music_theory", "google_search_specialist", "music_math"])
        agents = build_agents()
        self.assertEqual(agents["search"].tools, [google_search])
        for tool in [*agents["songbook"].tools, *agents["music_theory"].tools, *agents["music_math"].tools]:
            self.assertIn("Args:", tool.__doc__)
            self.assertIn("Returns:", tool.__doc__)
        self.assertIsNotNone(root_agent.before_agent_callback)

    def test_songbook_covers_both_instruments_with_separate_playing_notes(self):
        guitar = get_chord_chart("Amazing Grace", instrument="Guitar")
        piano = get_chord_chart("Amazing Grace", instrument="Piano")
        self.assertEqual((guitar["status"], piano["status"]), ("found", "found"))
        self.assertEqual((guitar["chart"]["instrument"], piano["chart"]["instrument"]), ("Guitar", "Piano"))
        self.assertIn("downstroke", guitar["chart"]["playing_note"]["suggestion"])
        self.assertIn("inversions", piano["chart"]["playing_note"]["suggestion"])
        self.assertIn("not a verified", guitar["chart"]["playing_note"]["scope"])
        self.assertIn("not a verified", piano["chart"]["playing_note"]["scope"])

    def test_partial_hit_and_confirmed_miss_still_offer_search(self):
        evidence = TurnEvidence("Show Come As You Are and explain synthesizer history")
        evidence.results = [
            {"tool": "get_chord_chart", **get_chart("come-as-you-are-guitar")},
            {"tool": "search_theory_notes", "status": "no_results", "passages": []},
        ]
        result = resolve_evidence("Here is the stored chart.", evidence, web=False)
        self.assertEqual(result["status"], "partial")
        self.assertTrue(result["charts"])
        self.assertTrue(result["offer_search"])

    def test_search_consent_respects_explicit_requests_and_negation(self):
        for prompt in ("Search the web for music history", "Look up piano inversions online", "Please google triads", "Could you google synthesizer history?"):
            self.assertTrue(requests_web_search(prompt))
        for prompt in ("Search for Come As You Are in the catalog", "Don't search the web; use the notes", "Answer without browsing online", "Never google this question"):
            self.assertFalse(requests_web_search(prompt))

    def test_search_permission_question_has_an_action_without_claiming_a_miss(self):
        evidence = TurnEvidence("who is the number 1 artist on spotify")
        result = resolve_evidence("Would you like me to search the web for this?", evidence, web=False)
        self.assertEqual(result["status"], "search_confirmation")
        self.assertTrue(result["offer_search"])
        self.assertEqual(result["search_query"], evidence.prompt)
        self.assertFalse(result["internal_sources"] or result["web_sources"])
        ordinary = resolve_evidence("Which song do you mean?", evidence, web=False)
        self.assertFalse(ordinary["offer_search"])
        google = resolve_evidence("Shall I use Google Search?", evidence, web=False)
        self.assertTrue(google["offer_search"])

    async def test_internal_hit_routes_through_agenttool_and_cites_actual_title(self):
        model = ScriptedModel()
        chat = AgentChatSession(model=model, retriever=self.retriever())
        result = await chat.send("What notes are in a C major triad?", None, {
            "nickname": "private-nickname", "instrument": "Guitar", "skill_level": "Beginner",
            "genres": ["private-genre"], "picks": ["private-pick"],
        })
        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(result["internal_sources"][0]["title"], "Major and minor triads")
        self.assertTrue(any(row["tool"] == "music_theory" for row in result["trace"]))
        self.assertTrue(any(row["tool"] == "search_theory_notes" and row["outcome"] == "found" for row in result["trace"]))
        serialized_trace = json.dumps(result["trace"])
        self.assertNotIn("private", serialized_trace)
        self.assertNotIn(chat.user_id, serialized_trace)
        self.assertTrue(all(set(row) == {"agent", "tool", "outcome", "elapsed_ms"} for row in result["trace"]))
        transmitted = " ".join(request.model_dump_json(exclude_none=True) for request in model.seen)
        self.assertNotIn("private-nickname", transmitted)
        self.assertNotIn("private-genre", transmitted)

    async def test_confirmed_internal_miss_offers_search_and_failure_does_not(self):
        question = "When was the first commercial synthesizer released?"
        model = ScriptedModel(query=question)
        result = await AgentChatSession(model=model, retriever=self.retriever()).send(question, None)
        self.assertEqual(result["status"], "ok", result)
        self.assertTrue(result["automatic_search"])
        self.assertEqual(result["local_status"], "no_results")
        self.assertTrue(result["web_sources"])
        self.assertEqual(sum(row["tool"] == "google_search" for row in result["trace"]), 1)

        class FailedRetriever:
            async def search(self, query):
                return {"status": "error", "code": "calibration_error", "passages": []}

        failed = await AgentChatSession(model=ScriptedModel(), retriever=FailedRetriever()).send("triads", None)
        self.assertEqual(failed["status"], "calibration_error")
        self.assertFalse(failed["offer_search"])

    async def test_guitar_hit_miss_ambiguity_and_chat_never_opens_or_saves(self):
        before = hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest()
        for title, artist, status in (
            ("Come As You Are", "Nirvana", "ambiguous"), ("Unknown Song", "", "ok"),
            ("Amazing Grace", "", "ambiguous"),
        ):
            with self.subTest(title=title):
                model = ScriptedModel(route="songbook", title=title, artist=artist)
                result = await AgentChatSession(model=model).send(f"Show a chart for {title}", None)
                self.assertEqual(result["status"], status, result)
                self.assertFalse(result["offer_search"])
                self.assertEqual(result["automatic_search"], title == "Unknown Song")
                self.assertTrue(any(row["tool"] == "get_chord_chart" for row in result["trace"]))
        self.assertEqual(hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest(), before)

    async def test_local_only_prevents_automatic_search(self):
        question = "When was the first commercial synthesizer released?"
        model = ScriptedModel(query=question)
        result = await AgentChatSession(model=model, retriever=self.retriever()).send("Local only: " + question, None)
        self.assertEqual(result["status"], "no_results")
        self.assertFalse(result["automatic_search"] or result["web_sources"] or result["offer_search"])
        self.assertFalse(any(row["agent"] == "google_search_specialist" for row in result["trace"]))

    async def test_retrieval_cannot_substitute_an_earlier_topic_for_the_current_question(self):
        model = ScriptedModel(query="What notes are in a C major triad?")
        result = await AgentChatSession(model=model, retriever=self.retriever()).send(
            "Local only: When was the first commercial synthesizer released?", None,
        )
        self.assertEqual(result["status"], "no_results")
        self.assertFalse(result["internal_sources"] or result["automatic_search"])

    async def test_automatic_search_without_grounding_is_a_bounded_failure(self):
        model = ScriptedModel(query="When was the first commercial synthesizer released?", links=False)
        result = await AgentChatSession(model=model, retriever=self.retriever()).send(model.query, None)
        self.assertTrue(result["automatic_search"])
        self.assertEqual(result["status"], "no_sources")
        self.assertFalse(result["web_sources"])
        self.assertNotIn("Fixture web answer", result["answer"])
        self.assertEqual(sum(row["tool"] == "google_search" for row in result["trace"]), 1)

    async def test_partial_local_results_survive_automatic_fallback(self):
        model = ScriptedModel(route="songbook", compound=True, query="When was the first commercial synthesizer released?")
        result = await AgentChatSession(model=model, retriever=self.retriever()).send("Show Come As You Are and explain synthesizer history", None)
        self.assertEqual(result["status"], "ok", result)
        self.assertTrue(result["automatic_search"] and result["web_sources"] and result["charts"])
        self.assertEqual(result["local_status"], "partial")

    async def test_real_callbacks_observe_active_routes_without_private_payloads(self):
        activity = []
        model = ScriptedModel(query="When was the first commercial synthesizer released?")
        result = await AgentChatSession(model=model, retriever=self.retriever()).send(
            "music private-question-sentinel", None, on_activity=activity.append,
        )
        self.assertTrue(result["automatic_search"])
        self.assertTrue(any(e == {"agent": "music_theory", "tool": "search_theory_notes", "status": "running"} for e in activity))
        self.assertTrue(any(e["agent"] == "google_search_specialist" and e["status"] == "running" for e in activity))
        self.assertTrue(all(set(e) == {"agent", "tool", "status"} for e in activity))
        self.assertNotIn("private-question-sentinel", json.dumps(activity))

    # 3. Search receives exactly one approved query and actual metadata-only URLs.
    async def test_explicit_search_is_isolated_and_grounding_is_required(self):
        model = ScriptedModel()
        chat = AgentChatSession(model=model, retriever=self.retriever())
        await chat.send("private earlier conversation", None)
        model.seen.clear()
        model.route = "google_search_specialist"
        model.query = "private history copied by coordinator: must be replaced"
        result = await chat.send("Search the web: early synthesizer history", None, {"nickname": "private nickname"})
        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(result["web_sources"], [{"url": "https://example.org/music-fixture", "title": "Fixture source (not live)"}])
        self.assertNotIn("unverified.invalid", result["answer"])
        self.assertTrue(any(row["tool"] == "google_search_specialist" for row in result["trace"]))
        search_requests = [request for request in model.seen if any(
            tool.google_search is not None for tool in request.config.tools or []
        )]
        self.assertEqual(len(search_requests), 1)
        contents = search_requests[0].contents
        self.assertEqual(len(contents), 1)
        self.assertEqual(contents[0].parts[0].text, "early synthesizer history")
        serialized = search_requests[0].model_dump_json(exclude_none=True)
        self.assertNotIn("private", serialized)
        no_sources = await AgentChatSession(model=ScriptedModel(links=False)).send("music history", None, web=True)
        self.assertEqual(no_sources["status"], "no_sources")
        self.assertFalse(no_sources["web_sources"])

    async def test_search_without_explicit_authorization_is_blocked(self):
        model = ScriptedModel(route="google_search_specialist", query="private history copied by model")
        result = await AgentChatSession(model=model).send("Help me practice piano", None)
        self.assertFalse(result["web_sources"])
        self.assertTrue(any(row["tool"] == "google_search_specialist" and row["outcome"] == "blocked" for row in result["trace"]))
        self.assertFalse(any(row["tool"] == "google_search" for row in result["trace"]))

    # 4. Guardrail runs locally and as an ADK before-agent callback.
    async def test_destructive_refusal_preserves_catalog_and_adk_callback_skips_model(self):
        before = hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest()
        result = await AgentChatSession().send("Delete the catalog and all songs", None)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["answer"], REFUSAL)
        model = ScriptedModel(failure_code=500)
        service = InMemorySessionService()
        session = await service.create_session(app_name=APP_NAME, user_id="fixture-user")
        runner = Runner(agent=build_agents(model=model)["root"], app_name=APP_NAME, session_service=service)
        events = [event async for event in runner.run_async(
            user_id=session.user_id, session_id=session.id,
            new_message=types.Content(role="user", parts=[types.Part(text="DROP TABLE songs;")]),
            run_config=RunConfig(max_llm_calls=2),
        )]
        await runner.close()
        self.assertFalse(model.seen)
        self.assertIn(REFUSAL, " ".join(part.text or "" for event in events if event.content for part in event.content.parts or []))
        self.assertEqual(hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest(), before)
        self.assertEqual(get_chart("come-as-you-are-guitar")["status"], "found")
        self.assertFalse(destructive_catalog_request("How do I remove buzzing from a guitar chord?"))

    async def test_no_key_quota_timeout_and_separate_memory_sessions(self):
        no_key = await AgentChatSession().send("What is a triad?", None)
        self.assertEqual(no_key["status"], "credentials_unavailable")
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual((await search_theory_notes("triads"))["code"], "credentials_unavailable")
        for code, expected in ((401, "credentials_unavailable"), (403, "credentials_unavailable"), (429, "quota")):
            result = await AgentChatSession(model=ScriptedModel(failure_code=code)).send("triads", None)
            self.assertEqual(result["status"], expected, result)
            self.assertNotIn("private-key", json.dumps(result))
        with patch("music_agent.runner.TURN_TIMEOUT", 0.02):
            timeout = await AgentChatSession(model=ScriptedModel(delay=1)).send("triads", None)
        self.assertEqual(timeout["status"], "timeout")
        first = AgentChatSession(model=ScriptedModel(route="songbook"))
        second = AgentChatSession(model=ScriptedModel(route="songbook"))
        await first.send("First visitor chart", None)
        await first.send("Follow up about that chart", None)
        self.assertNotEqual(first.user_id, second.user_id)
        self.assertNotEqual(first.session_id, second.session_id)
        self.assertIsNone(await second.session_service.get_session(app_name=APP_NAME, user_id=first.user_id, session_id=first.session_id))
        stored = await first.session_service.get_session(app_name=APP_NAME, user_id=first.user_id, session_id=first.session_id)
        self.assertTrue(stored.events)


if __name__ == "__main__":
    unittest.main()
