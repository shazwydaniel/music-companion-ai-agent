"""Web discovery uses grounded results and one search per session profile."""

# 1. Scripted ADK responses never contact Google or stand in for live evidence.
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from agent_fixtures import ScriptedModel
from db import list_songs
from music_agent.discovery import discovery_query, parse_discoveries, search_new_songs

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
PROFILE = {"nickname": "Private Learner", "instrument": "Guitar", "skill_level": "Beginner",
           "genres": ["Rock", "Pop"], "picks": ["come-as-you-are", "birds-of-a-feather", "here-comes-the-sun"]}


class DiscoveryTests(unittest.IsolatedAsyncioTestCase):
    def test_query_and_parser_keep_preferences_bounded_and_catalog_out(self):
        songs = list_songs()
        query = discovery_query(PROFILE, songs)
        self.assertLessEqual(len(query), 490)
        for phrase in ("Rock", "Pop", "Beginner", "Guitar", "Come As You Are"):
            self.assertIn(phrase, query)
        self.assertNotIn("Private Learner", query)
        answer = json.dumps({"songs": [
            {"title": "Come As You Are", "artist": "Nirvana", "why": "Already stored"},
            {"title": "New Song", "artist": "New Artist", "why": "A simple practice idea"},
            {"title": "New Song", "artist": "New Artist", "why": "Duplicate"},
            {"title": "Another Song", "artist": "Other Artist", "why": "See https://unverified.invalid"},
        ]})
        sources = [{"url": "https://example.org/music-fixture", "title": "Fixture source"}]
        self.assertEqual(parse_discoveries(answer, [], songs), [])
        found = parse_discoveries(answer, sources, songs)
        self.assertEqual([item["title"] for item in found], ["New Song", "Another Song"])
        self.assertNotIn("unverified.invalid", found[1]["why"])

    async def test_search_specialist_receives_only_query_and_actual_sources(self):
        songs = list_songs()
        model = ScriptedModel(web_answer=json.dumps({"songs": [
            {"title": "New Song", "artist": "New Artist", "why": "Good for chord changes"},
        ]}))
        result = await search_new_songs(PROFILE, songs, None, model=model)
        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(result["items"][0]["title"], "New Song")
        self.assertEqual(result["sources"], [{"url": "https://example.org/music-fixture", "title": "Fixture source (not live)"}])
        requests = [request for request in model.seen if any(tool.google_search is not None for tool in request.config.tools or [])]
        self.assertEqual(len(requests), 1)
        self.assertEqual([part.text for part in requests[0].contents[0].parts], [discovery_query(PROFILE, songs)])
        self.assertNotIn("Private Learner", requests[0].model_dump_json(exclude_none=True))
        offline = await search_new_songs(PROFILE, songs, None)
        self.assertEqual(offline["status"], "credentials_unavailable")


# 2. Two AppTest sessions prove the web result is never shared or resubmitted on reruns.
class DiscoveryAppTests(unittest.TestCase):
    def test_for_you_caches_search_and_separates_sessions(self):
        calls = []

        async def fake_search(profile, songs, api_key, *, on_activity=None):
            calls.append((profile["skill_level"], tuple(profile["genres"])))
            return {"status": "ok", "items": [{"title": "Web Song", "artist": "Web Artist", "why": "Fits your practice goal"}],
                    "sources": [{"url": "https://example.org/music-fixture", "title": "Fixture source"}],
                    "answer": "", "trace": [], "usage": {}}

        with patch.dict(os.environ, {}, clear=True), patch("streamlit.secrets", {"GOOGLE_API_KEY": "fixture-key"}), \
                patch("music_agent.discovery.search_new_songs", new=fake_search):
            first = self._onboard()
            self.assertEqual(len(calls), 1)
            self.assertEqual(first.session_state["web_discovery"]["result"]["items"][0]["title"], "Web Song")
            featured = next(button for button in first.button if (button.key or "").startswith("open-featured-"))
            featured_song = next(song for song in list_songs() if song["id"] == featured.key.removeprefix("open-featured-"))
            self.assertIn(featured_song["genre"], ("Rock", "Pop"))
            self.assertEqual(featured_song["difficulty"], "Beginner")
            first.run()
            self.assertEqual(len(calls), 1)
            second = self._onboard()
            self.assertEqual(len(calls), 2)
            self.assertIsNot(first.session_state["web_discovery"], second.session_state["web_discovery"])
            next(button for button in first.button if button.label == "Edit profile").click().run()
            first.selectbox(key="profile_skill").set_value("Intermediate")
            next(button for button in first.button if button.label == "Save My Vibe").click().run()
            self.assertEqual(len(calls), 3)
            self.assertEqual(calls[-1][0], "Intermediate")

    @staticmethod
    def _onboard():
        app = AppTest.from_file(str(APP_PATH)).run()
        app.text_input(key="profile_nickname").set_value("Private Learner")
        app.selectbox(key="profile_instrument").set_value("Guitar")
        app.selectbox(key="profile_skill").set_value("Beginner")
        app.multiselect(key="profile_genres").set_value(["Rock", "Pop"]).run()
        app.multiselect(key="profile_picks").set_value(PROFILE["picks"])
        next(button for button in app.button if button.label == "Start Exploring").click().run()
        if app.exception:
            raise AssertionError(app.exception)
        return app
