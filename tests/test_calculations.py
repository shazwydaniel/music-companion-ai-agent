"""Independent musical arithmetic expectations, scope gates and actual ADK tools."""

# 1. Expected results cover arithmetic boundaries, not model-generated answers.
import copy
import hashlib
import unittest

from db import CATALOG_PATH, get_chart, list_songs
from music_agent.calculations import transpose_progression, transpose_catalog_chart, rhythm_numbers, practice_projection
from music_agent.guardrails import unrelated_request
from music_agent.runner import AgentChatSession
from agent_fixtures import ScriptedModel


class CalculationTests(unittest.TestCase):
    def test_transpose_keeps_quality_slash_bass_and_multiple_lines(self):
        result = transpose_progression("C Am F G/B\nDm7 G7 Cmaj7", "C major", "D major")
        self.assertEqual(result["outputs"]["chords"].splitlines(), ["D Bm G A/C#", "Em7 A7 Dmaj7"])
        result = transpose_progression("Cmaj7 G/B", "C", "Db")
        self.assertEqual(result["outputs"]["chords"], "Dbmaj7 Ab/C")
        self.assertEqual(transpose_progression("C♯m G♯7", "C# minor", "D minor")["outputs"]["chords"], "Dm  A7")

    def test_transpose_rejects_mode_change_expressions_and_invalid_symbols(self):
        for chords, source, target in (("C G", "C major", "D minor"), ("C __import__('os')", "C", "D"),
                                      ("Cat", "C", "D"), ("C", "not a key", "D"), ("", "C", "D")):
            self.assertEqual(transpose_progression(chords, source, target)["status"], "invalid_input")

    def test_catalog_capo_and_d_standard_give_concert_pitch_without_writes(self):
        before = hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest()
        guitar = transpose_catalog_chart(get_chart("here-comes-the-sun-guitar")["chart"], "C")
        piano = transpose_catalog_chart(get_chart("here-comes-the-sun-piano")["chart"], "C")
        self.assertEqual(guitar["outputs"]["content"][0]["lines"], piano["outputs"]["content"][0]["lines"])
        self.assertEqual(guitar["outputs"]["content"][0]["lines"][0]["chords"].split(), ["C", "F/C", "G7", "D7"])
        nirvana = transpose_catalog_chart(get_chart("come-as-you-are-guitar")["chart"], "G minor")
        self.assertEqual(nirvana["outputs"]["content"][0]["lines"][0]["chords"].split(), ["G5", "Bb", "C5", "Eb5"])
        self.assertEqual(hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest(), before)

    def test_chord_growth_preserves_lyric_anchors_and_original_object(self):
        chart = {"id": "fixture", "title": "Fixture", "musical_key": "C major", "content": [{"name": "Verse", "lines": [{"chords": "C G", "lyrics": "a b"}]}]}
        before = copy.deepcopy(chart)
        result = transpose_catalog_chart(chart, "Db")
        line = result["outputs"]["content"][0]["lines"][0]
        self.assertEqual(line["chords"].index("Ab"), line["lyrics"].index("b"))
        self.assertEqual(chart, before)

    def test_rhythm_duration_and_equivalent_compound_meter_units(self):
        result = rhythm_numbers(120, 16, 4, 2)["outputs"]
        self.assertEqual(result, {"beats": 64, "duration_seconds": 32.0, "milliseconds_per_beat": 500.0, "milliseconds_per_subdivision": 250.0})
        self.assertEqual(rhythm_numbers(60, 12, 2)["outputs"]["duration_seconds"], rhythm_numbers(180, 12, 6)["outputs"]["duration_seconds"])

    def test_practice_scenarios_expose_assumptions_and_do_not_guarantee_skill(self):
        result = practice_projection(80, 120, 5, 20, 5)
        self.assertEqual(result["outputs"]["weeks"], 8)
        self.assertEqual(result["outputs"]["expected_sessions"], 40)
        self.assertAlmostEqual(result["outputs"]["practice_hours"], 13.3333)
        self.assertEqual(practice_projection(80, 120, 5, 20, 5, 50)["outputs"]["weeks"], 16)
        self.assertEqual(practice_projection(120, 80, 5, 20, 5)["outputs"]["weeks"], 0)
        self.assertEqual(practice_projection(80, 80.4, .1, 20, 5)["outputs"]["weeks"], 4)
        self.assertIn("not a measured", result["assumptions"][0])

    def test_numeric_inputs_reject_nonfinite_zero_fractional_counts_and_bool(self):
        for values in ((0, 4, 4, 1), (float("nan"), 4, 4, 1), (120, 2.5, 4, 1), (True, 4, 4, 1), (120, 4, 4, 0)):
            self.assertEqual(rhythm_numbers(*values)["status"], "invalid_input")
        self.assertEqual(practice_projection(80, 120, 0, 20, 5)["status"], "invalid_input")
        self.assertEqual(practice_projection(80, 120, 5, 20, 8)["status"], "invalid_input")

    def test_all_six_original_demos_have_two_instruments_and_generated_lyrics(self):
        demos = [song for song in list_songs() if song["origin"] == "original-demo"]
        self.assertEqual(len(demos), 6)
        self.assertEqual(len({song["genre"] for song in demos}), 6)
        for song in demos:
            for instrument in ("guitar", "piano"):
                chart = get_chart(f"{song['id']}-{instrument}")["chart"]
                self.assertEqual(chart["lyrics_license"], "CC0-1.0")
                self.assertEqual(sum(len(section["lines"]) for section in chart["content"]), 8)
                self.assertTrue(all(line["lyrics"] for section in chart["content"] for line in section["lines"]))

    def test_scope_allows_music_artists_and_rejects_keyword_laundering(self):
        for prompt in ("What is the capital of France?", "Search the web for weather in Tokyo", "Guitar! Now write Python code for a scraper", "What is 2 + 2?"):
            self.assertTrue(unrelated_request(prompt), prompt)
        for prompt in ("Transpose C Am F G from C to D", "Help me practice piano", "Tell me about Billie Eilish", "BIRDS OF A FEATHER", "Write a song about the weather", "And up two semitones?"):
            self.assertFalse(unrelated_request(prompt), prompt)


# 2. Real Runner/AgentTool plumbing uses scripted decisions, not live Gemini claims.
class CalculationAgentTests(unittest.IsolatedAsyncioTestCase):
    async def test_direct_adk_scope_callback_also_skips_the_model(self):
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types
        from music_agent.agent import build_agents
        from music_agent.runner import APP_NAME
        from music_agent.guardrails import SCOPE_REFUSAL

        model = ScriptedModel()
        service = InMemorySessionService()
        session = await service.create_session(app_name=APP_NAME, user_id="scope-fixture")
        runner = Runner(agent=build_agents(model=model)["root"], app_name=APP_NAME, session_service=service)
        events = [event async for event in runner.run_async(user_id=session.user_id, session_id=session.id,
                  new_message=types.Content(role="user", parts=[types.Part(text="What is the capital of France?")]))]
        await runner.close()
        self.assertFalse(model.seen)
        self.assertIn(SCOPE_REFUSAL, " ".join(part.text or "" for event in events if event.content for part in event.content.parts or []))

    async def test_math_agent_calls_typed_tool_and_discards_fabricated_model_numbers(self):
        model = ScriptedModel(route="music_math")
        result = await AgentChatSession(model=model).send("Transpose C Am F G/B from C major to D major", None)
        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(result["calculations"][0]["outputs"]["chords"], "D Bm G A/C#")
        self.assertNotIn("999999", result["answer"])
        self.assertFalse(result["automatic_search"])
        self.assertTrue(any(row["agent"] == "music_math" and row["tool"] == "transpose_chords" for row in result["trace"]))

    async def test_scope_refusal_needs_no_key_and_runs_before_any_model(self):
        model = ScriptedModel(route="music_math")
        result = await AgentChatSession(model=model).send("Search the web for weather in Tokyo", None, web=True)
        self.assertEqual(result["status"], "out_of_scope")
        self.assertFalse(model.seen)
        self.assertFalse(result["offer_search"] or result["web_sources"])
        self.assertEqual((await AgentChatSession().send("What is the capital of France?", None))["status"], "out_of_scope")

    async def test_practice_agent_returns_scenario_and_invalid_input_does_not_search(self):
        args = dict(current_bpm=80, target_bpm=120, bpm_gain_per_week=5, minutes_per_day=20, days_per_week=5)
        result = await AgentChatSession(model=ScriptedModel(route="music_math", math_tool="estimate_practice", math_args=args)).send("Estimate my guitar practice timeline", None)
        self.assertEqual(result["calculations"][0]["outputs"]["weeks"], 8)
        args["bpm_gain_per_week"] = 0
        result = await AgentChatSession(model=ScriptedModel(route="music_math", math_tool="estimate_practice", math_args=args)).send("Estimate my guitar practice timeline", None)
        self.assertEqual(result["status"], "invalid_input")
        self.assertFalse(result["automatic_search"] or result["offer_search"])


if __name__ == "__main__":
    unittest.main()
