"""Run separate live chat, grounded Search, and notes checks only with a key."""

# 1. Safe CLI setup — print statuses and counts, never credentials or prompts.
import asyncio
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from music_agent.config import resolve_google_api_key


# 2. Each provider check is independent; one failure does not claim another passed.
async def main(only: str | None = None) -> None:
    from streamlit import secrets
    from music_agent.runner import AgentChatSession

    key = resolve_google_api_key(secrets)
    checks = [
        ("gemini_reply", "Show the Come As You Are chart by Nirvana.", False),
        ("grounded_search", "Search the web: When was the first commercial synthesizer released?", True),
        ("notes_retrieval", "What notes are in a C major triad?", False),
        ("public_fact_search_offer", "who is the number 1 artist on spotify", False),
        ("spotify_grounded_search", "Who is the number 1 artist on Spotify by monthly listeners today?", True),
        ("search_agenttool", "Search the web: What is Billie Eilish's HIT ME HARD AND SOFT album release date?", False),
        ("internal_miss", "When was the first commercial synthesizer released?", False),
        ("music_math", "Transpose C Am F G/B from C major to D major. Use the calculation tool.", False),
        ("practice_estimate", "For guitar practice I play cleanly at 80 BPM and want 120 BPM. Assume a gain of 5 BPM per week, 20 minutes per session, 5 days per week and 100% attendance. Estimate weeks and hours using the tool.", False),
    ]
    for name, prompt, web in checks:
        if only and name != only:
            continue
        if not key.configured:
            print(json.dumps({"check": name, "status": "pending", "reason": "Google key missing"}))
            continue
        result = await AgentChatSession().send(prompt, key.api_key, web=web)
        print(json.dumps({
            "check": name, "status": result["status"],
            "charts": len(result["charts"]), "notes": len(result["internal_sources"]),
            "grounded_links": len(result["web_sources"]), "trace": result["trace"],
            "offer_search": result["offer_search"],
            "automatic_search": result["automatic_search"], "local_status": result["local_status"],
            "calculations": [{"kind": item["kind"], "outputs": {key: value for key, value in item["outputs"].items() if key != "content"}}
                             for item in result.get("calculations", [])],
        }))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", help="Run one named check from the source list")
    arguments = parser.parse_args()
    asyncio.run(main(arguments.check))
