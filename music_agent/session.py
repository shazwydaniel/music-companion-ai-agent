"""Explicit app actions on the current visitor's in-memory Streamlit state."""

# 1. A new session gets new collections; there are no module-level user objects.
from collections.abc import MutableMapping
from datetime import datetime, timezone
from secrets import choice

INSTRUMENTS = ("Guitar", "Piano")
SKILL_LEVELS = ("Beginner", "Intermediate")
GENRES = ("Rock", "Pop", "Jazz", "Indie / Folk", "Electronic", "Classical")
AVATARS = ("cat", "rabbit", "fox")
GENRE_DEMOS = {genre: f"demo-{slug}" for genre, slug in zip(GENRES, ("rock", "pop", "jazz", "folk", "electronic", "classical"))}


def initialize_session(state: MutableMapping) -> None:
    """Initialize per-session data without overwriting values on a rerun."""
    for key, factory in (
        ("profile", lambda: None), ("favorites", dict), ("recent_views", dict),
        ("chat", list), ("active_chart", lambda: None),
        ("editing_profile", lambda: False), ("lookup_result", lambda: None),
        ("avatar", lambda: choice(AVATARS)), ("agent_activity", dict),
        ("transpositions", dict),
        ("greeting_seen", lambda: False),
        ("web_discovery", lambda: None),
    ):
        if key not in state:
            state[key] = factory()


# 2. Draft choices react to the union of selected genres, never to an AI guess.
def song_options_for_genres(songs: list[dict], genres: list[str]) -> list[dict]:
    """Return catalog songs in any selected genre; no selection has no options."""
    selected = set(genres) & set(GENRES)
    return [song for song in songs if song["genre"] in selected]


# 3. Validate the full submitted profile before replacing the current one.
def update_profile(
    state: MutableMapping, nickname: str, instrument: str, skill_level: str,
    genres: list[str], picks: list[str], songs: list[dict],
) -> str | None:
    """Apply a valid profile or return a useful validation message."""
    if not nickname.strip() or len(nickname.strip()) > 40:
        return "Enter a nickname between 1 and 40 characters."
    if instrument not in INSTRUMENTS or skill_level not in SKILL_LEVELS:
        return "Choose a listed instrument and skill level."
    if not genres or not set(genres) <= set(GENRES):
        return "Choose at least one favorite genre."
    if len(picks) != 3 or len(set(picks)) != 3:
        return "Choose exactly three distinct songs."
    if not set(picks) <= {song["id"] for song in songs}:
        return "Choose songs from the current catalog."
    if not set(picks) <= {song["id"] for song in song_options_for_genres(songs, genres)}:
        return "Choose three songs from your selected genres."
    state["profile"] = {
        "nickname": nickname.strip(), "instrument": instrument,
        "skill_level": skill_level, "genres": list(genres), "picks": list(picks),
    }
    state["editing_profile"] = False
    return None


# 4. Opening and saving require validated catalog records supplied by the app.
def open_chart(state: MutableMapping, chart: dict) -> None:
    """Record an explicit chart open once per song, refreshing its timestamp."""
    state["active_chart"] = chart["id"]
    state["recent_views"][chart["song_id"]] = {
        "chart_id": chart["id"], "opened_at": datetime.now(timezone.utc).isoformat(),
    }


def save_song(state: MutableMapping, song_id: str, catalog_ids: set[str]) -> bool:
    """Save a real catalog song once; reruns and repeat saves add no entry."""
    if song_id not in catalog_ids:
        return False
    state["favorites"].setdefault(song_id, datetime.now(timezone.utc).isoformat())
    return True
