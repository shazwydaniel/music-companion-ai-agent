"""Check authored lesson metadata or build/calibrate its public Gemini index."""

# 1. CLI imports work from the repo root or a different working directory.
import argparse
import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from music_agent.config import resolve_google_api_key
from music_agent.retrieval import load_lessons


# 2. The default check requires no provider; an explicit build uses Google.
async def build() -> None:
    from google import genai
    from google.genai import types
    from streamlit import secrets
    from music_agent.errors import error_status
    from music_agent.retrieval import GeminiEmbedder, TheoryRetriever

    key = resolve_google_api_key(secrets)
    if not key.configured:
        print("PENDING: Google key missing; Gemini embeddings and gate calibration were not run.")
        return
    client = genai.Client(
        api_key=key.api_key, vertexai=False,
        http_options=types.HttpOptions(timeout=15000, retry_options=types.HttpRetryOptions(attempts=1)),
    )
    try:
        async with asyncio.timeout(45):
            index = await TheoryRetriever(GeminiEmbedder(client)).index()
        print(f"PASS: {len(index.lessons)} lessons, cosine gate {index.threshold:.4f}, version {index.version[:12]}")
        print("Index is in process memory; the app builds its own public cache once per version.")
    except Exception as error:
        print(f"PENDING: index build/calibration failed ({error_status(error)}); no successful index claimed.")
    finally:
        await client.aio.aclose()
        client.close()


def main() -> None:
    """Inspect stable lesson sources and optionally test live embedding setup."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true", help="Use the server Google key to embed and calibrate")
    arguments = parser.parse_args()
    for lesson in load_lessons():
        print(f"{lesson['source_id']}: {lesson['title']}")
    if arguments.build:
        asyncio.run(build())


if __name__ == "__main__":
    main()
