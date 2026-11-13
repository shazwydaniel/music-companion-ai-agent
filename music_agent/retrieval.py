"""Lesson-level Gemini embeddings, Chroma cosine retrieval, and a calibrated gate."""

# 1. Parse authored lessons with stable IDs and actual user-visible titles.
import asyncio
from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import threading
from typing import Protocol

from music_agent.errors import error_status

NOTES_PATH = Path(__file__).resolve().parents[1] / "docs" / "MUSIC_KNOWLEDGE_BASE.md"
EMBEDDING_MODEL = "gemini-embedding-001"
DIMENSIONS = 768
METRIC = "cosine"
CALIBRATION_PATH = Path(__file__).resolve().parents[1] / "knowledge" / "retrieval_checks.json"


def load_lessons(path: Path = NOTES_PATH) -> list[dict]:
    """Split level-two headings, retaining source ID, title, topic, and instruments."""
    text = path.read_text(encoding="utf-8")
    lessons, identifiers = [], set()
    for match in re.finditer(r"^## ([^\n]+)\n(.*?)(?=^## |\Z)", text, re.M | re.S):
        title, body = match.group(1).strip(), match.group(2).strip()
        metadata = {}
        for label in ("Source ID", "Topic", "Instruments"):
            value = re.search(rf"\*\*{label}:\*\*\s*([^\n]+)", body)
            if not value:
                raise ValueError("A lesson is missing source metadata")
            metadata[label] = value.group(1).strip().strip("`")
        source_id = metadata["Source ID"]
        if not re.fullmatch(r"[a-z0-9-]+", source_id) or source_id in identifiers:
            raise ValueError("Lesson source IDs must be unique and stable")
        identifiers.add(source_id)
        lessons.append({
            "source_id": source_id, "title": title, "topic": metadata["Topic"],
            "instruments": metadata["Instruments"], "passage": body,
        })
    if not lessons:
        raise ValueError("No authored lessons found")
    return lessons


# 2. A replaceable embedder enables local tests without pretending they are Gemini.
class Embedder(Protocol):
    async def embed(self, texts: list[str], task: str) -> list[list[float]]:
        """Embed documents or transient queries with the same model/dimensions."""
        ...


class GeminiEmbedder:
    """Use the server's explicit Gen AI client; no default embedding download."""

    def __init__(self, client) -> None:
        self.client = client

    async def embed(self, texts: list[str], task: str) -> list[list[float]]:
        """Embed only supplied text; RETRIEVAL_DOCUMENT and RETRIEVAL_QUERY pair."""
        from google.genai import types

        response = await self.client.aio.models.embed_content(
            model=EMBEDDING_MODEL, contents=texts,
            config=types.EmbedContentConfig(task_type=task, output_dimensionality=DIMENSIONS),
        )
        if not response.embeddings or len(response.embeddings) != len(texts):
            raise ValueError("Incomplete embedding response")
        if any(not item.values or len(item.values) != DIMENSIONS for item in response.embeddings):
            raise ValueError("Unexpected embedding dimensions")
        return [unit_vector(item.values) for item in response.embeddings]


def unit_vector(values: list[float]) -> list[float]:
    """Normalize truncated Gemini vectors and reject invalid numeric values."""
    if not values or any(not math.isfinite(value) for value in values):
        raise ValueError("Invalid embedding vector")
    length = math.sqrt(sum(value * value for value in values))
    if length == 0:
        raise ValueError("Zero embedding vector")
    return [value / length for value in values]


# 3. Calibrate on public supported/miss examples before accepting any passages.
class CalibrationError(ValueError):
    """A failed gate is a retrieval error, never an internal knowledge miss."""


def calibrate_gate(collection, checks: list[dict], vectors: list[list[float]]) -> float:
    """Require correct positive sources and separation from negative examples."""
    positive, negative = [], []
    for check, vector in zip(checks, vectors, strict=True):
        result = collection.query(query_embeddings=[vector], n_results=1, include=["distances"])
        score = 1 - result["distances"][0][0]
        if check["source_id"] is None:
            negative.append(score)
        else:
            if result["ids"][0][0] != check["source_id"]:
                raise CalibrationError("A supported example retrieved the wrong lesson")
            positive.append(score)
    if not positive or not negative or min(positive) <= max(negative) + 0.02:
        raise CalibrationError("Supported and unsupported examples do not separate")
    return (min(positive) + max(negative)) / 2


@dataclass
class LessonIndex:
    """Cache public lesson vectors and gate only, never prompts or credentials."""

    collection: object
    threshold: float
    version: str
    lessons: dict[str, dict]


_INDEXES: dict[str, LessonIndex] = {}
_BUILD_LOCK = threading.Lock()


# 4. Build once per corpus/model/calibration version; query vectors stay transient.
class TheoryRetriever:
    def __init__(self, embedder: Embedder, cache_namespace: str = "gemini") -> None:
        self.embedder = embedder
        self.cache_namespace = cache_namespace

    async def index(self) -> LessonIndex:
        """Build a Chroma index of authored lessons with an empirically set gate."""
        lessons = load_lessons()
        checks = json.loads(CALIBRATION_PATH.read_text())["checks"]
        material = json.dumps([lessons, checks, EMBEDDING_MODEL, DIMENSIONS, METRIC, self.cache_namespace])
        version = sha256(material.encode()).hexdigest()
        if version in _INDEXES:
            return _INDEXES[version]
        # A threading lock works across Streamlit's separate invocation loops.
        while not _BUILD_LOCK.acquire(blocking=False):
            await asyncio.sleep(0.05)
        collection = None
        client = None
        try:
            if version in _INDEXES:
                return _INDEXES[version]
            import chromadb
            from chromadb.config import Settings

            client = chromadb.EphemeralClient(Settings(anonymized_telemetry=False))
            # No default embedding function, persistent client, or query insertion.
            collection = client.create_collection(
                name=f"riffin-{version[:32]}", embedding_function=None,
                configuration={"hnsw": {"space": METRIC}},
            )
            documents = [f"{lesson['title']}\n{lesson['passage']}" for lesson in lessons]
            embeddings = await self.embedder.embed(documents, "RETRIEVAL_DOCUMENT")
            collection.add(
                ids=[lesson["source_id"] for lesson in lessons], documents=documents,
                embeddings=embeddings,
                metadatas=[
                    {key: lesson[key] for key in ("source_id", "title", "topic", "instruments")}
                    for lesson in lessons
                ],
            )
            calibration_vectors = await self.embedder.embed([check["query"] for check in checks], "RETRIEVAL_QUERY")
            threshold = calibrate_gate(collection, checks, calibration_vectors)
            index = LessonIndex(collection, threshold, version, {lesson["source_id"]: lesson for lesson in lessons})
            _INDEXES[version] = index
            return index
        except BaseException:
            if collection is not None and client is not None:
                client.delete_collection(collection.name)
            raise
        finally:
            _BUILD_LOCK.release()

    async def search(self, query: str) -> dict:
        """Return bounded relevant authored passages, a confirmed miss, or error."""
        try:
            index = await self.index()
            vector = (await self.embedder.embed([query[:1000]], "RETRIEVAL_QUERY"))[0]
            matches = index.collection.query(
                query_embeddings=[vector], n_results=min(2, len(index.lessons)), include=["distances"],
            )
            passages = []
            for source_id, distance in zip(matches["ids"][0], matches["distances"][0], strict=True):
                if 1 - distance >= index.threshold:
                    lesson = index.lessons[source_id]
                    passages.append({**lesson, "passage": lesson["passage"][:1800]})
            return {"status": "found" if passages else "no_results", "passages": passages}
        except CalibrationError:
            return {"status": "error", "code": "calibration_error", "passages": []}
        except Exception as error:
            return {"status": "error", "code": error_status(error), "passages": []}
