"""Exercise public catalog permissions, provenance, ranking, and session actions."""

# 1. Tests use disposable databases; the approved catalog remains unchanged.
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from db import find_chord_chart, get_chart, list_songs, read_catalog, validate_chart
from music_agent.presentation import chart_section_html, metadata_tags_html, profile_pills_html
from music_agent.recommendations import rank_songs
from music_agent.session import initialize_session, open_chart, save_song, update_profile
from scripts.seed_catalog import seed_catalog


class CatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "catalog.sqlite"
        seed_catalog(self.path)

    # 2. Repeated initialization preserves the same logical and physical data.
    def test_repeatable_seed_has_only_public_tables_and_provenance(self) -> None:
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.assertEqual(seed_catalog(self.path), (54, 108))
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), before)
        with read_catalog(self.path) as connection:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertEqual(tables, {"songs", "chord_charts"})
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertFalse(connection.execute("PRAGMA foreign_key_check").fetchall())
        for song in list_songs(self.path):
            for instrument in song["instruments"]:
                result = get_chart(f"{song['id']}-{instrument.lower()}", self.path)
                self.assertEqual(result["status"], "found")
                self.assertTrue(result["chart"]["attribution"])
                self.assertTrue(result["chart"]["source_url"].startswith("https://"))
                if result["chart"]["chart_kind"] == "external":
                    self.assertEqual(result["chart"]["content"], [])
                    self.assertTrue(result["chart"]["resource_url"].startswith("https://www.musicnotes.com/"))
                else:
                    self.assertTrue(result["chart"]["content"])

    def test_runtime_connection_refuses_writes_and_unknown_path_is_not_created(self) -> None:
        with read_catalog(self.path) as connection:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("DELETE FROM songs")
        missing = self.path.parent / "missing.sqlite"
        self.assertEqual(find_chord_chart("Amazing Grace", path=missing)["status"], "error")
        self.assertFalse(missing.exists())
        self.assertEqual(len(list_songs(self.path)), 54)

    # 3. Exact title identity and arrangement ambiguity remain distinct from errors.
    def test_normalized_hit_ambiguity_and_instrument_choices(self) -> None:
        result = find_chord_chart("  cOME    As You Are ", " NIRVANA ", instrument="Guitar", path=self.path)
        self.assertEqual(result["status"], "found")
        self.assertEqual(result["chart"]["id"], "come-as-you-are-guitar")
        ambiguous = find_chord_chart("Amazing Grace", path=self.path)
        self.assertEqual(ambiguous["status"], "ambiguous")
        self.assertEqual({choice["instrument"] for choice in ambiguous["choices"]}, {"Guitar", "Piano"})
        self.assertEqual(find_chord_chart("Amazing Grace", path=self.path)["status"], "ambiguous")
        self.assertEqual(find_chord_chart("Amazing Grace", instrument="Piano", path=self.path)["status"], "found")

    def test_miss_sql_injection_invalid_id_and_corrupt_chart(self) -> None:
        for title in ("Unknown Song", "' OR 1=1 --", "Amazing Grace'; DROP TABLE songs; --"):
            self.assertEqual(find_chord_chart(title, path=self.path)["status"], "not_found")
        self.assertEqual(get_chart("not-a-chart", self.path)["status"], "not_found")
        with sqlite3.connect(self.path) as connection:
            connection.execute("UPDATE chord_charts SET content = ? WHERE id = ?", ('{"invalid": true}', 'amazing-grace-guitar'))
        self.assertEqual(get_chart("amazing-grace-guitar", self.path)["status"], "error")
        with sqlite3.connect(self.path) as connection:
            connection.execute("UPDATE chord_charts SET attribution = '' WHERE id = 'come-as-you-are-guitar'")
        self.assertEqual(get_chart("come-as-you-are-guitar", self.path)["status"], "error")

    def test_chord_rendering_preserves_spaces_lyrics_and_escapes(self) -> None:
        section = {"name": '<script>section</script>', "lines": [{"chords": "C       G", "lyrics": "<img src=x>   sing"}]}
        html = chart_section_html(section)
        self.assertIn("C       G", html)
        self.assertIn("&lt;img src=x&gt;   sing", html)
        self.assertNotIn("<script>", html)
        self.assertIn('tabindex="0"', html)
        tags = metadata_tags_html([("Key", "<script>C</script>"), ("Capo", 0), ("Missing", None)])
        self.assertIn("Key :", tags)
        self.assertIn("&lt;script&gt;C&lt;/script&gt;", tags)
        self.assertIn("<strong>0</strong>", tags)
        self.assertNotIn("Missing", tags)
        pills = profile_pills_html({"nickname": "<img src=x>", "instrument": "Guitar", "skill_level": "Beginner"})
        self.assertIn("You :", pills)
        self.assertIn("&lt;img src=x&gt;", pills)
        self.assertNotIn("<img src=x>", pills)
        instrumental = get_chart("canon-in-d-guitar", self.path)["chart"]
        self.assertNotIn("lyrics", instrumental["content"][0]["lines"][0])

    def test_stored_lyrics_need_reuse_metadata_and_only_three_works_have_them(self) -> None:
        lyric_works = set()
        for song in list_songs(self.path):
            for instrument in song["instruments"]:
                chart = get_chart(f"{song['id']}-{instrument.lower()}", self.path)["chart"]
                if any("lyrics" in line for section in chart["content"] for line in section["lines"]):
                    lyric_works.add(song["id"])
                    self.assertEqual(chart["lyrics_license"], "CC0-1.0" if chart["origin"] == "original-demo" else "public-domain")
                    self.assertTrue(chart["lyrics_source_url"].startswith("https://"))
                    with self.assertRaises(ValueError):
                        validate_chart({**chart, "lyrics_license": None})
        self.assertEqual(lyric_works, {"amazing-grace", "auld-lang-syne", "greensleeves", "demo-rock", "demo-pop", "demo-jazz", "demo-folk", "demo-electronic", "demo-classical"})

    def test_profile_cannot_submit_out_of_genre_song_ids(self) -> None:
        state = {}
        initialize_session(state)
        error = update_profile(state, "Learner", "Guitar", "Beginner", ["Electronic"],
                               ["get-lucky", "wake-me-up", "come-as-you-are"], list_songs(self.path))
        self.assertIn("selected genres", error)
        self.assertIsNone(state["profile"])


# 4. Ranking and state checks use real catalog metadata and independent mappings.
class SessionAndRankingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.songs = list_songs()
        self.state = {}
        initialize_session(self.state)
        self.assertIsNone(update_profile(self.state, "Learner", "Guitar", "Beginner", ["Rock", "Indie / Folk", "Classical", "Electronic"], ["amazing-grace", "ode-to-joy", "get-lucky"], self.songs))

    def test_rank_excludes_picks_and_opens_with_stable_metadata_reasons(self) -> None:
        ranked = rank_songs(self.songs, self.state["profile"])
        canon = next(song for song in ranked if song["id"] == "canon-in-d")
        self.assertEqual(canon["score"], 10)
        self.assertIn("Classical matches your tastes", canon["reason"])
        self.assertIn("Guitar practice chords", canon["reason"])
        self.assertGreaterEqual(ranked[0]["score"], canon["score"])
        self.assertFalse(set(self.state["profile"]["picks"]) & {song["id"] for song in ranked})
        self.assertEqual(ranked, rank_songs(list(reversed(self.songs)), self.state["profile"]))
        self.assertNotIn("come-as-you-are", {song["id"] for song in rank_songs(self.songs, self.state["profile"], {"come-as-you-are"})})
        self.assertEqual(rank_songs(self.songs, self.state["profile"], {song["id"] for song in self.songs}), [])

    def test_researched_references_have_scope_dates_and_instrument_transpositions(self) -> None:
        kinds = []
        for song in self.songs:
            for instrument in song["instruments"]:
                chart = get_chart(f"{song['id']}-{instrument.lower()}")["chart"]
                kinds.append(chart["chart_kind"])
                if chart["chart_kind"] == "reference":
                    self.assertTrue(chart["chord_source_url"].startswith("https://"))
                    self.assertEqual(chart["checked_on"], "2026-11-13")
                    self.assertTrue(chart["reference_note"])
                    self.assertFalse(any("lyrics" in line for section in chart["content"] for line in section["lines"]))
        self.assertEqual(kinds.count("reference"), 86)
        self.assertEqual(kinds.count("inline"), 22)
        guitar = get_chart("here-comes-the-sun-guitar")["chart"]
        piano = get_chart("here-comes-the-sun-piano")["chart"]
        self.assertEqual(guitar["capo"], 7)
        self.assertIsNone(piano["capo"])
        self.assertNotEqual(guitar["content"], piano["content"])
        self.assertEqual(len(get_chart("amazing-grace-guitar")["chart"]["content"]), 3)

    def test_profile_validation_and_changed_picks_update_ranking(self) -> None:
        old = dict(self.state["profile"])
        for picks in (["amazing-grace"] * 3, ["amazing-grace", "ode-to-joy"], ["bad", "amazing-grace", "ode-to-joy"]):
            self.assertIsNotNone(update_profile(self.state, "Learner", "Guitar", "Beginner", ["Rock"], picks, self.songs))
            self.assertEqual(self.state["profile"], old)
        self.assertIsNotNone(update_profile(self.state, " ", "Guitar", "Beginner", ["Rock"], old["picks"], self.songs))
        self.assertIsNotNone(update_profile(self.state, "Learner", "Guitar", "Beginner", [], old["picks"], self.songs))
        self.assertIsNone(update_profile(self.state, "Learner", "Piano", "Intermediate", ["Rock", "Pop"], ["come-as-you-are", "birds-of-a-feather", "here-comes-the-sun"], self.songs))
        ranked = rank_songs(self.songs, self.state["profile"])
        self.assertNotIn("come-as-you-are", {song["id"] for song in ranked})
        self.assertIn("amazing-grace", {song["id"] for song in ranked})

    def test_repeat_actions_rerun_and_independent_session(self) -> None:
        chart = get_chart("amazing-grace-guitar")["chart"]
        open_chart(self.state, chart)
        first = self.state["recent_views"]["amazing-grace"]["opened_at"]
        open_chart(self.state, chart)
        self.assertGreaterEqual(self.state["recent_views"]["amazing-grace"]["opened_at"], first)
        self.assertEqual(len(self.state["recent_views"]), 1)
        ids = {song["id"] for song in self.songs}
        self.assertTrue(save_song(self.state, "amazing-grace", ids))
        saved_time = self.state["favorites"]["amazing-grace"]
        save_song(self.state, "amazing-grace", ids)
        self.assertEqual(self.state["favorites"], {"amazing-grace": saved_time})
        self.assertFalse(save_song(self.state, "invalid", ids))
        self.state["chat"].append({"role": "user", "content": "session sentinel"})
        snapshot = json.dumps(self.state)
        initialize_session(self.state)
        self.assertEqual(json.dumps(self.state), snapshot)
        fresh = {}
        initialize_session(fresh)
        self.assertIsNone(fresh["profile"])
        self.assertFalse(fresh["favorites"] or fresh["recent_views"] or fresh["chat"])


if __name__ == "__main__":
    unittest.main()
