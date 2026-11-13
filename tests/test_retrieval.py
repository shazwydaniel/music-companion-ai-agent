"""Test lesson parsing, real Chroma indexing, and gated fixture-vector retrieval."""

# 1. Fixture vectors are explicitly isolated from the production Gemini cache.
import json
from pathlib import Path
import tempfile
import unittest
from uuid import uuid4

from agent_fixtures import FixtureEmbedder
from music_agent.retrieval import (
    CalibrationError, TheoryRetriever, calibrate_gate, load_lessons, unit_vector,
)


class RetrievalTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.embedder = FixtureEmbedder()
        self.retriever = TheoryRetriever(self.embedder, cache_namespace=f"fixture-{uuid4().hex}")

    # 2. Stable source metadata comes from the authored heading, not model prose.
    def test_parse_all_lessons_and_reject_missing_or_duplicate_source_metadata(self):
        lessons = load_lessons()
        self.assertEqual(len(lessons), 4)
        self.assertEqual(lessons[0]["title"], "Major and minor triads")
        self.assertEqual(lessons[0]["source_id"], "major-minor-triads")
        self.assertIn("Guitar", lessons[0]["instruments"])
        self.assertIn("C major uses C, E, and G", lessons[0]["passage"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notes.md"
            path.write_text("## No metadata\nBody")
            with self.assertRaises(ValueError):
                load_lessons(path)
            path.write_text(("## Lesson\n**Source ID:** `duplicate`\n**Topic:** Chords\n**Instruments:** Piano\nBody\n") * 2)
            with self.assertRaises(ValueError):
                load_lessons(path)

    async def test_real_chroma_index_hits_misses_and_transient_queries(self):
        supported = await self.retriever.search("What notes are in a C major triad?")
        self.assertEqual(supported["status"], "found")
        self.assertEqual(supported["passages"][0]["title"], "Major and minor triads")
        self.assertEqual(supported["passages"][0]["source_id"], "major-minor-triads")
        missing = await self.retriever.search("When was the first commercial synthesizer released?")
        self.assertEqual(missing, {"status": "no_results", "passages": []})
        index = await self.retriever.index()
        self.assertEqual(index.collection.count(), 4)
        stored = index.collection.get(include=["documents", "metadatas"])
        self.assertNotIn("synthesizer", json.dumps(stored))
        self.assertTrue(all("source_id" in metadata for metadata in stored["metadatas"]))
        doc_calls = [call for call in self.embedder.calls if call[1] == "RETRIEVAL_DOCUMENT"]
        self.assertEqual(len(doc_calls), 1)
        self.assertAlmostEqual(index.threshold, 0.5)
        self.assertIs(index, await self.retriever.index())

    # 3. A bad embedding/calibration never becomes a no_results coverage claim.
    async def test_unavailable_embedding_and_failed_gate_are_errors(self):
        class BrokenEmbedder:
            async def embed(self, texts, task):
                raise TimeoutError("sensitive provider request")

        retriever = TheoryRetriever(BrokenEmbedder(), cache_namespace=f"broken-{uuid4().hex}")
        result = await retriever.search("triads")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["code"], "timeout")

        class BadGateEmbedder:
            async def embed(self, texts, task):
                return [[1.0, 0.0] for _ in texts]

        bad = TheoryRetriever(BadGateEmbedder(), cache_namespace=f"bad-{uuid4().hex}")
        self.assertEqual((await bad.search("triads"))["code"], "calibration_error")

    def test_invalid_vectors_are_rejected(self):
        self.assertEqual(unit_vector([3.0, 4.0]), [0.6, 0.8])
        for values in ([], [0.0, 0.0], [float("nan"), 1.0], [float("inf")]):
            with self.assertRaises(ValueError):
                unit_vector(values)


if __name__ == "__main__":
    unittest.main()
