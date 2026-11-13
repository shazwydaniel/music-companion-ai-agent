"""Deterministic metadata-based recommendations with inspectable reasons."""

# 1. Difficulty ordering is explicit and shared across ranking comparisons.
LEVELS = {"Beginner": 0, "Intermediate": 1}


# 2. Score only real catalog facts; never infer song properties from a model.
def rank_songs(songs: list[dict], profile: dict, excluded: set[str] | None = None) -> list[dict]:
    """Rank unpicked, unopened songs and attach reasons from their metadata.

    Shared picked artists score 4, genres from picks/profile score 3, a matching
    instrument scores 5, and an appropriate level scores 2. Ties use stable IDs.
    ``excluded`` contains recent song IDs from this visitor's session only.
    """
    picked_ids = set(profile["picks"])
    picks = [song for song in songs if song["id"] in picked_ids]
    artists = {song["artist"] for song in picks}
    genres = set(profile["genres"]) | {song["genre"] for song in picks}
    ranked = []
    for song in songs:
        if song["id"] in picked_ids | (excluded or set()):
            continue
        score, reasons = 0, []
        if song["artist"] in artists:
            score += 4
            reasons.append(f"More from {song['artist']}")
        if song["genre"] in genres:
            score += 3
            reasons.append(f"{song['genre']} matches your tastes")
        if profile["instrument"] in song["instruments"]:
            score += 5
            reasons.append(f"{profile['instrument']} {'practice chords' if song.get('chart_kind') == 'inline' else 'chord reference'}")
        if LEVELS[song["difficulty"]] <= LEVELS[profile["skill_level"]]:
            score += 2
            reasons.append(f"{song['difficulty']} level")
        ranked.append({**song, "score": score, "reason": " · ".join(reasons) or "Explore a different style"})
    return sorted(ranked, key=lambda song: (-song["score"], song["id"]))
