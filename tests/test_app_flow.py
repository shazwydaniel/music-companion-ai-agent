"""Run the actual Streamlit flow with no Google key and isolated sessions."""

# 1. Shared helpers operate widgets; they do not bypass the profile form.
import hashlib
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from db import CATALOG_PATH, list_songs

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
PICKS = ["amazing-grace", "ode-to-joy", "get-lucky"]


def click_label(app: AppTest, label: str) -> AppTest:
    """Click one uniquely labelled action in the current screen."""
    return next(button for button in app.button if button.label == label).click().run()


def onboard(app: AppTest, nickname: str = "Flow Learner") -> AppTest:
    """Submit all required guest profile fields through the native form."""
    app.text_input(key="profile_nickname").set_value(nickname)
    app.selectbox(key="profile_instrument").set_value("Guitar")
    app.selectbox(key="profile_skill").set_value("Beginner")
    app.multiselect(key="profile_genres").set_value(["Rock", "Indie / Folk", "Classical", "Electronic"]).run()
    app.multiselect(key="profile_picks").set_value(PICKS)
    return click_label(app, "Start Exploring")


# 2. A full flow must not write user data or even change the public SQLite bytes.
class AppFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.secrets = patch("streamlit.secrets", {})
        self.secrets.start()
        self.addCleanup(self.secrets.stop)
        self.catalog_hash = hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest()

    def tearDown(self) -> None:
        self.assertEqual(hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest(), self.catalog_hash)

    def test_complete_flow_repeated_actions_and_empty_feed(self) -> None:
        app = AppTest.from_file(str(APP_PATH)).run()
        self.assertEqual(app.header[0].value, "Let’s find your groove")
        self.assertEqual({widget.label for widget in app.text_input}, {"Nickname"})
        onboard(app)
        self.assertFalse(app.exception)
        self.assertEqual(app.header[0].value, "For You")
        self.assertEqual(app.radio(key="view").value, "For You")
        app.radio(key="view").set_value("For You").run()
        self.assertEqual(app.header[0].value, "For You")
        self.assertTrue(any("AI offline" in m.value for m in app.markdown))
        featured = next(button for button in app.button if (button.key or "").startswith("open-featured-"))
        song_id = featured.key.removeprefix("open-featured-")
        featured.click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["active_chart"], f"{song_id}-guitar")
        opened = app.session_state["recent_views"][song_id]["opened_at"]
        app.run()
        self.assertEqual(app.session_state["recent_views"][song_id]["opened_at"], opened)
        app.button(key="save-active-chart").click().run()
        app.button(key="save-active-chart").click().run()
        self.assertEqual(len(app.session_state["favorites"]), 1)
        app.button(key="reopen-active-chart").click().run()
        self.assertEqual(len(app.session_state["recent_views"]), 1)
        self.assertNotEqual(app.session_state["recent_views"][song_id]["opened_at"], opened)
        app.radio(key="view").set_value("Library").run()
        self.assertFalse(app.exception)
        self.assertEqual({heading.value for heading in app.subheader}, {"Recently Opened", "Saved Songs"})
        # All other suggestions opened: verify the rendered useful empty state.
        app.session_state["recent_views"] = {song["id"]: {"chart_id": f"{song['id']}-{song['instruments'][0].lower()}", "opened_at": "2026-11-12T00:00:00+00:00"} for song in list_songs()}
        app.radio(key="view").set_value("For You").run()
        self.assertIn("You have explored every suggestion", app.info[0].value)

    def test_lookup_ambiguous_missing_found_and_instrumental_chart(self) -> None:
        app = onboard(AppTest.from_file(str(APP_PATH)).run())
        app.radio(key="view").set_value("Catalog").run()
        app.text_input(key="lookup_title").set_value("Amazing Grace")
        click_label(app, "Find chords")
        self.assertEqual(app.session_state["lookup_result"]["status"], "ambiguous")
        self.assertEqual(len(app.session_state["lookup_result"]["choices"]), 2)
        self.assertFalse(app.session_state["recent_views"])
        app.text_input(key="lookup_title").set_value("Missing Title")
        click_label(app, "Find chords")
        self.assertEqual(app.session_state["view"], "Chat")
        self.assertEqual(app.session_state["chat"][-1]["result"]["status"], "credentials_unavailable")
        app.radio(key="view").set_value("Catalog").run()
        app.text_input(key="lookup_title").set_value("Amazing Grace")
        app.text_input(key="lookup_artist").set_value("John Newton / Traditional")
        app.selectbox(key="lookup_instrument").set_value("Piano")
        click_label(app, "Find chords")
        self.assertEqual(app.session_state["lookup_result"]["status"], "found")
        app.button(key="lookup-open-amazing-grace-piano").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["active_chart"], "amazing-grace-piano")
        self.assertTrue(any("CHORDS & LYRICS" in caption.value for caption in app.caption))
        app.radio(key="view").set_value("Catalog").run()
        app.button(key="open-catalog-amazing-grace").click().run()
        self.assertEqual(app.session_state["active_chart"], "amazing-grace-guitar")

    def test_form_validation_editing_and_feed_refresh(self) -> None:
        app = AppTest.from_file(str(APP_PATH)).run()
        click_label(app, "Start Exploring")
        self.assertIn("nickname", app.error[0].value)
        app.text_input(key="profile_nickname").set_value("Editor")
        app.multiselect(key="profile_genres").set_value(["Indie / Folk", "Classical"]).run()
        app.multiselect(key="profile_picks").set_value(PICKS[:2])
        click_label(app, "Start Exploring")
        self.assertIn("three distinct", app.error[0].value)
        onboard(app, "Editor")
        app.radio(key="view").set_value("For You").run()
        click_label(app, "Edit profile")
        app.multiselect(key="profile_genres").set_value(["Rock", "Pop"]).run()
        app.multiselect(key="profile_picks").set_value(["come-as-you-are", "birds-of-a-feather", "here-comes-the-sun"])
        click_label(app, "Save My Vibe")
        self.assertFalse(app.exception)
        self.assertEqual(app.header[0].value, "For You")
        self.assertFalse(any(button.key == "open-featured-come-as-you-are" for button in app.button))
        self.assertEqual(app.session_state["profile"]["genres"], ["Rock", "Pop"])
        self.assertTrue(any((button.key or "").startswith("open-featured-") for button in app.button))

    # Genre controls must react before submitting the full guest profile.
    def test_each_genre_filters_the_picker_and_multiple_genres_form_a_union(self) -> None:
        app = AppTest.from_file(str(APP_PATH)).run()
        self.assertTrue(app.multiselect(key="profile_picks").disabled)
        self.assertFalse(app.multiselect(key="profile_picks").options)
        songs = list_songs()
        for genre in ("Rock", "Pop", "Jazz", "Indie / Folk", "Electronic", "Classical"):
            app.multiselect(key="profile_genres").set_value([genre]).run()
            expected = {f"{song['title']} — {song['artist']}" for song in songs if song['genre'] == genre}
            self.assertEqual(set(app.multiselect(key="profile_picks").options), expected)
            self.assertEqual(len(expected), 9)
            self.assertFalse(app.multiselect(key="profile_picks").disabled)
        app.multiselect(key="profile_genres").set_value(["Jazz", "Electronic"]).run()
        self.assertEqual(len(app.multiselect(key="profile_picks").options), 18)
        self.assertFalse(app.exception)

    def test_genre_changes_preserve_compatible_picks_and_other_draft_fields(self) -> None:
        app = AppTest.from_file(str(APP_PATH)).run()
        app.text_input(key="profile_nickname").set_value("Genre Learner").run()
        app.selectbox(key="profile_instrument").set_value("Piano").run()
        app.multiselect(key="profile_genres").set_value(["Rock", "Electronic"]).run()
        app.multiselect(key="profile_picks").set_value(["come-as-you-are", "get-lucky", "wake-me-up"]).run()
        app.multiselect(key="profile_genres").set_value(["Electronic"]).run()
        self.assertEqual(app.multiselect(key="profile_picks").value, ["get-lucky", "wake-me-up"])
        self.assertEqual(app.text_input(key="profile_nickname").value, "Genre Learner")
        self.assertEqual(app.selectbox(key="profile_instrument").value, "Piano")
        click_label(app, "Start Exploring")
        self.assertIsNone(app.session_state["profile"])
        self.assertIn("three distinct", app.error[0].value)
        app.multiselect(key="profile_picks").set_value(["get-lucky", "wake-me-up", "faded"]).run()
        click_label(app, "Start Exploring")
        self.assertEqual(app.session_state["profile"]["picks"], ["get-lucky", "wake-me-up", "faded"])
        click_label(app, "Edit profile")
        app.multiselect(key="profile_genres").set_value([]).run()
        self.assertTrue(app.multiselect(key="profile_picks").disabled)
        self.assertFalse(app.multiselect(key="profile_picks").value)
        click_label(app, "Cancel")
        self.assertEqual(app.session_state["profile"]["genres"], ["Electronic"])
        self.assertEqual(len(app.session_state["profile"]["picks"]), 3)

    def test_original_demo_and_transposition_stay_local_and_preserve_lyrics(self) -> None:
        app = onboard(AppTest.from_file(str(APP_PATH)).run())
        app.radio(key="view").set_value("Catalog").run()
        app.button(key="demo-open-demo-pop").click().run()
        self.assertEqual(app.session_state["active_chart"], "demo-pop-guitar")
        app.selectbox(key="transpose-target-demo-pop-guitar").set_value("D").run()
        app.button(key="transpose-song-demo-pop-guitar").click().run()
        changed = app.session_state["transpositions"]["demo-pop-guitar"]
        self.assertEqual(changed["outputs"]["target_key"], "D major")
        self.assertEqual(changed["outputs"]["content"][0]["lines"][0]["chords"].split(), ["D", "Bm"])
        self.assertIn("sun upon my sleeve", changed["outputs"]["content"][0]["lines"][0]["lyrics"])
        app.run()
        self.assertEqual(app.session_state["transpositions"]["demo-pop-guitar"], changed)
        app.button(key="reset-transpose-demo-pop-guitar").click().run()
        self.assertFalse(app.session_state["transpositions"])
        self.assertFalse(app.exception)

    def test_no_key_practice_calculator_and_unrelated_chat_guard(self) -> None:
        app = onboard(AppTest.from_file(str(APP_PATH)).run())
        app.radio(key="view").set_value("Chat").run()
        app.button(key="chat-calculator-toggle").click().run()
        app.selectbox(key="music-calculation-kind").set_value("Practice scenario").run()
        click_label(app, "Calculate")
        self.assertEqual(app.session_state["last_music_calculation"]["outputs"]["weeks"], 8)
        self.assertFalse(app.exception)
        app.chat_input[0].set_value("What is the capital of France?").run()
        self.assertEqual(app.session_state["chat"][-1]["result"]["status"], "out_of_scope")
        self.assertFalse(app.session_state["chat"][-1]["result"]["web_sources"])

    # 3. AppTest creates separate Streamlit sessions, not copied state mappings.
    def test_two_sessions_never_share_profile_activity_or_chat(self) -> None:
        first = onboard(AppTest.from_file(str(APP_PATH)).run(), "First Visitor")
        first.radio(key="view").set_value("For You").run()
        next(button for button in first.button if (button.key or "").startswith("open-featured-")).click().run()
        first.button(key="save-active-chart").click().run()
        first.session_state["chat"].append({"role": "user", "content": "private session sentinel"})
        first.run()
        second = AppTest.from_file(str(APP_PATH)).run()
        self.assertEqual(second.header[0].value, "Let’s find your groove")
        self.assertIsNone(second.session_state["profile"])
        for key in ("favorites", "recent_views", "chat"):
            self.assertFalse(second.session_state[key])
        onboard(second, "Second Visitor")
        self.assertEqual(first.session_state["profile"]["nickname"], "First Visitor")
        self.assertEqual(second.session_state["profile"]["nickname"], "Second Visitor")
        self.assertFalse(second.session_state["favorites"] or second.session_state["recent_views"] or second.session_state["chat"])
        self.assertEqual(len(first.session_state["favorites"]), 1)
        self.assertEqual(len(first.session_state["chat"]), 1)


if __name__ == "__main__":
    unittest.main()
