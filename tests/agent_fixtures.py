"""Explicit test doubles: these never represent real Gemini or web evidence."""

# 1. Deterministic vectors exercise real Chroma/gating code without credentials.
import json

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from pydantic import Field

from music_agent.retrieval import CALIBRATION_PATH, load_lessons


class FixtureEmbedder:
    def __init__(self) -> None:
        self.calls = []
        self.lessons = load_lessons()
        self.checks = json.loads(CALIBRATION_PATH.read_text())["checks"]

    async def embed(self, texts, task):
        self.calls.append((list(texts), task))
        vectors = []
        for text in texts:
            slot = 4
            if task == "RETRIEVAL_DOCUMENT":
                slot = next(i for i, lesson in enumerate(self.lessons) if text.startswith(lesson["title"] + "\n"))
            else:
                for check in self.checks:
                    if text == check["query"] and check["source_id"]:
                        slot = next(i for i, lesson in enumerate(self.lessons) if lesson["source_id"] == check["source_id"])
            vectors.append([float(i == slot) for i in range(5)])
        return vectors


# 2. Scripted LLM decisions test ADK plumbing, not real Gemini route accuracy.
class ScriptedModel(BaseLlm):
    # The ADK native Google Search adapter validates this identifier. Responses
    # still come entirely from this explicit test double, with no network call.
    model: str = "gemini-3.6-flash"
    route: str = "music_theory"
    query: str = "What notes are in a C major triad?"
    title: str = "Come As You Are"
    artist: str = "Nirvana"
    web_answer: str = "Fixture web answer [made up](https://unverified.invalid)."
    links: bool = True
    failure_code: int = 0
    delay: float = 0
    compound: bool = False
    math_tool: str = "transpose_chords"
    math_args: dict = Field(default_factory=lambda: {"chords": "C Am F G/B", "from_key": "C major", "to_key": "D major"})
    seen: list = Field(default_factory=list, exclude=True)

    async def generate_content_async(self, llm_request, stream=False):
        import asyncio

        self.seen.append(llm_request.model_copy(deep=True))
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.failure_code:
            error = RuntimeError("private-key-and-prompt-must-not-be-rendered")
            error.code = self.failure_code
            raise error
        tools = set(llm_request.tools_dict)
        contents = llm_request.contents
        last_user = max((
            i for i, content in enumerate(contents)
            if content.role == "user" and any(part.text for part in content.parts or [])
        ), default=0)
        responses = [
            part.function_response for content in contents[last_user:]
            for part in content.parts or [] if part.function_response
        ]
        if "songbook" in tools:
            if any(response.name in {"songbook", "music_theory", "google_search_specialist", "music_math"} for response in responses):
                part = types.Part(text="The specialist result is ready.")
            else:
                part = types.Part(function_call=types.FunctionCall(name=self.route, args={"request": self.query}))
        elif "transpose_chords" in tools:
            part = types.Part(text="Unverified model arithmetic: the answer is 999999.") if responses else types.Part(
                function_call=types.FunctionCall(name=self.math_tool, args=self.math_args)
            )
        elif "get_chord_chart" in tools:
            part = types.Part(text="Here is the stored chart.") if responses else types.Part(
                function_call=types.FunctionCall(name="get_chord_chart", args={"title": self.title, "artist": self.artist})
            )
        elif "search_theory_notes" in tools:
            part = types.Part(text="C major uses C, E, and G. See Major and minor triads.") if responses else types.Part(
                function_call=types.FunctionCall(name="search_theory_notes", args={"query": self.query})
            )
        else:
            metadata = types.GroundingMetadata(grounding_chunks=[
                {"web": {"uri": "https://example.org/music-fixture", "title": "Fixture source (not live)"}},
                {"web": {"uri": "javascript:alert(1)", "title": "Rejected fixture"}},
            ]) if self.links else None
            yield LlmResponse(
                content=types.Content(role="model", parts=[types.Part(text=self.web_answer)]),
                grounding_metadata=metadata,
            )
            return
        parts = [part]
        if self.compound and "songbook" in tools and not responses:
            parts.append(types.Part(function_call=types.FunctionCall(name="music_theory", args={"request": self.query})))
        yield LlmResponse(content=types.Content(role="model", parts=parts))
