"""Grounded, session-only song discovery outside the read-only catalog."""

# 1. Build one bounded public-music query from validated playing preferences.
import json
import re

from db import normalize_identity
from music_agent.session import GENRES, INSTRUMENTS, SKILL_LEVELS


def discovery_signature(profile: dict) -> tuple:
    """Identify when the current session's recommendation inputs changed."""
    return (profile["instrument"], profile["skill_level"],
            tuple(profile["genres"]), tuple(profile["picks"]))


def discovery_query(profile: dict, songs: list[dict]) -> str:
    """Ask for similar public songs without a nickname, history, or full profile.

    Args:
        profile: This session's validated instrument, level, genres, and picks.
        songs: Read-only public catalog metadata used to name selected examples.

    Returns:
        A bounded query containing only music preferences and public song names.
    """
    instrument = profile["instrument"] if profile["instrument"] in INSTRUMENTS else "Guitar"
    level = profile["skill_level"] if profile["skill_level"] in SKILL_LEVELS else "Beginner"
    genres = ", ".join(genre for genre in profile["genres"] if genre in GENRES)
    by_id = {song["id"]: song for song in songs}
    examples = [f"{by_id[song_id]['title']} by {by_id[song_id]['artist']}" for song_id in profile["picks"] if song_id in by_id]
    suffix = (
        ' Return JSON only: {"songs":[{"title":"...","artist":"...","why":"..."}]}. '
        "Put no URLs in the JSON; Google grounding supplies links separately. "
        "No lyrics or full charts. Suggest a level fit, not verified arrangement difficulty."
    )
    while True:
        examples_text = "; ".join(examples) or "the selected genres"
        query = (f"For You discovery: Search the web for 4 real songs similar to {examples_text}. "
                 f"Suit a {level} {instrument} learner who likes {genres}. Exclude the examples." + suffix)
        if len(query) <= 490 or not examples:
            return query[:490]
        examples.pop()


# 2. Parse model suggestions conservatively; only grounding metadata can supply links.
def _json_songs(answer: str) -> list:
    decoder = json.JSONDecoder()
    for match in re.finditer(r"[\[{]", answer[:8000]):
        try:
            value, _ = decoder.raw_decode(answer[match.start():])
        except (ValueError, TypeError):
            continue
        if isinstance(value, dict) and isinstance(value.get("songs"), list):
            return value["songs"]
        if isinstance(value, list):
            return value
    return []


def _plain(value: object, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    value = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"https?://\S+|[<>\x00-\x1f]", " ", value)
    return " ".join(value.split())[:limit].strip()


def parse_discoveries(answer: str, sources: list[dict], songs: list[dict]) -> list[dict]:
    """Keep distinct non-catalog songs and accept links only from grounding.

    Args:
        answer: Specialist-generated JSON or text; untrusted until parsed.
        sources: HTTP(S) links already extracted from grounding metadata.
        songs: Local catalog used to exclude stored titles.

    Returns:
        Up to four bounded display cards only when grounding exists. Source
        links are displayed separately; this does not certify difficulty.
    """
    if not sources:
        return []
    catalog_titles = {normalize_identity(song["title"]) for song in songs}
    seen = set()
    items = []
    for row in _json_songs(answer):
        if not isinstance(row, dict):
            continue
        title = _plain(row.get("title"), 80)
        artist = _plain(row.get("artist"), 80)
        identity = normalize_identity(title)
        if not title or not artist or identity in catalog_titles or identity in seen:
            continue
        why = _plain(row.get("why"), 180) or "A new song to explore based on your music tastes."
        items.append({"title": title, "artist": artist, "why": why})
        seen.add(identity)
        if len(items) == 4:
            break
    return items


# 3. Invoke only the existing Google Search specialist in a fresh ADK session.
async def search_new_songs(profile: dict, songs: list[dict], api_key: str | None,
                           *, model=None, on_activity=None) -> dict:
    """Return validated web ideas and actual grounded sources, without writes.

    Args:
        profile: Validated playing preferences; nickname is never used.
        songs: Public catalog metadata, read-only.
        api_key: Server-only Google key, or None for the offline state.
        model: Optional explicit scripted model for local tests.
        on_activity: Optional session-owned live agent observer.

    Returns:
        A status, bounded cards, grounded source links, trace, and safe answer.
    """
    if not api_key and model is None:
        return {"status": "credentials_unavailable", "items": [], "sources": [], "answer": ""}
    from music_agent.runner import AgentChatSession

    query = discovery_query(profile, songs)
    result = await AgentChatSession(model=model).send(query, api_key, web=True, on_activity=on_activity)
    sources = result["web_sources"]
    items = parse_discoveries(result["answer"], sources, songs) if result["status"] == "ok" else []
    return {"status": "ok" if items else "unstructured" if result["status"] == "ok" else result["status"],
            "items": items, "sources": sources, "answer": result["answer"],
            "trace": result["trace"], "usage": result["usage"]}
