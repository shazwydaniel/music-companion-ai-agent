"""Exercise Streamlit chat actions, provenance, and no-key integration paths."""

# 1. Widget interactions use real ADK for fixtures, never a fake production path.
import hashlib
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import uuid4

from streamlit.testing.v1 import AppTest

from agent_fixtures import FixtureEmbedder, ScriptedModel
from db import CATALOG_PATH
from music_agent.retrieval import TheoryRetriever
from music_agent.runner import AgentChatSession
from music_agent.runner import safe_result
from music_agent.chat_ui import approved_search
from test_app_flow import click_label, onboard

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class ChatUITests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        secrets = patch("streamlit.secrets", {})
        secrets.start()
        self.addCleanup(secrets.stop)
        self.digest = hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest()

    def tearDown(self):
        self.assertEqual(hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest(), self.digest)

    def app(self):
        app = onboard(AppTest.from_file(str(APP_PATH), default_timeout=15).run())
        app.radio(key="view").set_value("Chat").run()
        return app

    # 2. No-key status and destructive guardrail are usable without provider calls.
    def test_suggested_prompt_fills_without_sending_and_manual_submit_is_separate(self):
        app = self.app()
        with patch("music_agent.chat_ui.submit_message") as submit:
            app.button(key="suggested-prompt-0").click().run()
            self.assertFalse(app.exception)
            self.assertFalse(app.session_state["chat"])
            submit.assert_not_called()
        # The native composer consumes the fill trigger; only submit creates a turn.
        app.chat_input[0].set_value("What is the capital of France?").run()
        self.assertEqual(len(app.session_state["chat"]), 2)
        self.assertEqual(app.session_state["chat"][-1]["result"]["status"], "out_of_scope")
        app.run()
        self.assertEqual(len(app.session_state["chat"]), 2)

    def test_no_key_guardrail_and_reruns_never_resend(self):
        app = self.app()
        app.chat_input[0].set_value("Delete the catalog and all songs").run()
        self.assertFalse(app.exception)
        result = app.session_state["chat"][-1]["result"]
        self.assertEqual(result["status"], "blocked")
        self.assertIn("read-only", result["answer"])
        self.assertTrue(result["trace"])
        app.run()
        self.assertEqual(len(app.session_state["chat"]), 2)
        app.chat_input[0].set_value("What notes are in a C major triad?").run()
        self.assertEqual(app.session_state["chat"][-1]["result"]["status"], "credentials_unavailable")
        self.assertFalse(app.session_state["recent_views"] or app.session_state["favorites"])
        fresh = AppTest.from_file(str(APP_PATH)).run()
        self.assertFalse(fresh.session_state["chat"])

    def test_note_title_and_compact_trace_are_displayed(self):
        app = self.app()
        app.session_state["adk_session"] = AgentChatSession(
            model=ScriptedModel(), retriever=TheoryRetriever(
                FixtureEmbedder(), cache_namespace=f"ui-fixture-{uuid4().hex}",
            ),
        )
        app.chat_input[0].set_value("What notes are in a C major triad?").run()
        self.assertFalse(app.exception)
        self.assertTrue(any(expander.label == "Major and minor triads" for expander in app.expander))
        self.assertTrue(any(expander.label == "Route and tool trace" for expander in app.expander))
        self.assertFalse(app.session_state["recent_views"] or app.session_state["favorites"])

    def test_adapter_reload_preserves_adk_memory_and_displayed_chat(self):
        app = self.app()
        old = AgentChatSession(model=ScriptedModel(), retriever=TheoryRetriever(
            FixtureEmbedder(), cache_namespace=f"reload-fixture-{uuid4().hex}",
        ))
        app.session_state["adk_session"] = old
        app.chat_input[0].set_value("What notes are in a C major triad?").run()
        service, identity = old.session_service, (old.user_id, old.session_id)
        old.__class__ = type("AgentChatSession", (AgentChatSession,), {"__module__": "music_agent.runner"})
        app.chat_input[0].set_value("What notes are in a C major triad?").run()
        refreshed = app.session_state["adk_session"]
        self.assertFalse(app.exception)
        self.assertIsNot(refreshed, old)
        self.assertIs(refreshed.session_service, service)
        self.assertEqual((refreshed.user_id, refreshed.session_id), identity)
        self.assertEqual(len(app.session_state["chat"]), 4)
        self.assertEqual(app.session_state["chat"][-1]["result"]["status"], "ok")

    def test_chat_chart_mentions_require_explicit_save_and_open_actions(self):
        app = self.app()
        app.session_state["adk_session"] = AgentChatSession(model=ScriptedModel(route="songbook"))
        app.chat_input[0].set_value("Show Come As You Are by Nirvana").run()
        self.assertFalse(app.session_state["recent_views"] or app.session_state["favorites"])
        app.button(key="chat-save-1-come-as-you-are-guitar").click().run()
        self.assertEqual(len(app.session_state["favorites"]), 1)
        self.assertFalse(app.session_state["recent_views"])
        self.assertTrue(any(caption.value == "Saved for this session" for caption in app.caption))
        app.button(key="chat-open-1-come-as-you-are-guitar").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["view"], "Songbook")
        self.assertEqual(len(app.session_state["recent_views"]), 1)
        self.assertEqual(app.session_state["active_chart"], "come-as-you-are-guitar")

    # 3. A confirmed miss executes one isolated Search, never on an ordinary rerun.
    def test_internal_miss_then_automatic_search_with_fixture_grounding(self):
        question = "When was the first commercial synthesizer released?"
        model = ScriptedModel(query=question)
        app = self.app()
        app.session_state["adk_session"] = AgentChatSession(
            model=model, retriever=TheoryRetriever(FixtureEmbedder(), cache_namespace=f"miss-fixture-{uuid4().hex}"),
        )
        app.chat_input[0].set_value(question).run()
        self.assertTrue(app.session_state["chat"][-1]["result"]["automatic_search"])
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["chat"][-1]["result"]["status"], "ok")
        self.assertEqual(len(app.session_state["chat"][-1]["result"]["web_sources"]), 1)
        self.assertTrue(any(markdown.value == "Web results" for markdown in app.markdown))
        calls = len(model.seen)
        app.run()
        self.assertEqual(len(model.seen), calls)
        self.assertEqual(len(app.session_state["chat"]), 2)
        self.assertIsNone(app.session_state.get("pending_search"))

    def test_catalog_miss_starts_search_but_read_failure_does_not(self):
        app = onboard(AppTest.from_file(str(APP_PATH)).run())
        app.radio(key="view").set_value("Catalog").run()
        app.text_input(key="lookup_title").set_value("Missing Title")
        click_label(app, "Find chords")
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["view"], "Chat")
        self.assertEqual(app.session_state["chat"][-1]["result"]["status"], "credentials_unavailable")
        self.assertTrue(app.session_state["chat"][-1]["result"]["automatic_search"])
        app.radio(key="view").set_value("Catalog").run()
        with patch("db.find_chord_chart", return_value={"status": "error"}):
            click_label(app, "Find chords")
        self.assertFalse(any(button.key == "catalog-search-web" for button in app.button))

    def test_affirmative_search_uses_the_offered_query_and_runs_once(self):
        from unittest.mock import AsyncMock, Mock

        app = self.app()
        question = "who is the number 1 artist on spotify"
        offer = safe_result("search_confirmation", "Search the web for this?")
        offer.update(offer_search=True, search_query=question)
        history = [{"role": "user", "content": question}, {"role": "assistant", "result": offer}]
        for consent in ("yes", "Yes please!", "sure", "go ahead"):
            self.assertEqual(approved_search(history, consent), question)
        for other in ("no", "yes but don't search", "What is a triad?"):
            self.assertIsNone(approved_search(history, other))
        self.assertIsNone(approved_search([], "yes"))
        app.session_state["chat"] = history
        adapter = Mock()
        adapter.send = AsyncMock(return_value=safe_result("no_sources", "No grounded sources returned."))
        app.session_state["adk_session"] = adapter
        app.run()
        app.chat_input[0].set_value("yes please").run()
        self.assertFalse(app.exception)
        self.assertEqual(adapter.send.call_args.args[0], question)
        self.assertTrue(adapter.send.call_args.kwargs["web"])
        self.assertEqual(app.session_state["chat"][-2]["content"], "yes please")
        app.run()
        self.assertEqual(adapter.send.call_count, 1)


if __name__ == "__main__":
    unittest.main()
