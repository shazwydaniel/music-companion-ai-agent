"""Typed read-only catalog and internal retrieval tools used by ADK specialists."""

# 1. Typed tools — agents use the same read-only catalog boundary as the UI.
from db import find_chord_chart
from music_agent.playing_notes import playing_note
from music_agent.turn import CURRENT_TURN


def _record(name: str, identity: tuple, result: dict) -> dict:
    """Keep source evidence private and reuse identical calls within one turn."""
    evidence = CURRENT_TURN.get()
    if evidence:
        evidence.results.append({"tool": name, **result})
        evidence.cache[(name, *identity)] = result
    return result


def get_chord_chart(title: str, artist: str = "", instrument: str = "") -> dict:
    """Find a stored chord chart, asking for clarification when choices remain.

    Args:
        title: Song title, matched without case or whitespace differences.
        artist: Optional catalog artist label to disambiguate the title.
        instrument: Optional exact arrangement instrument, Guitar or Piano.

    Returns:
        A structured found, not_found, ambiguous, or error result. A hit includes
        its validated chart ID and attribution; choices include instrument names.
    """
    evidence = CURRENT_TURN.get()
    key = ("get_chord_chart", title, artist, instrument)
    if evidence and key in evidence.cache:
        return evidence.cache[key]
    result = find_chord_chart(title, artist, instrument)
    if result["status"] == "found":
        chart = result["chart"]
        result = {**result, "chart": {**chart, "playing_note": playing_note(chart["instrument"])}}
    return _record("get_chord_chart", (title, artist, instrument), result)


# 2. A relevance miss is distinct from unavailable credentials/index failures.
async def search_theory_notes(query: str) -> dict:
    """Retrieve relevant authored music lessons and their actual citation titles.

    Args:
        query: Proposed focused question. During an app turn, retrieval is bound
            to the current submitted question so earlier chat topics cannot be
            substituted by the model. Standalone calls use this argument.

    Returns:
        found with bounded authored passages and stable source metadata;
        no_results only after a working calibrated index rejects all passages;
        error with a safe code when embeddings/indexing/retrieval is unavailable.
    """
    evidence = CURRENT_TURN.get()
    if evidence:
        query = evidence.prompt
    cache_key = ("search_theory_notes", query)
    if evidence and cache_key in evidence.cache:
        return evidence.cache[cache_key]
    owned_client = None
    try:
        if evidence and evidence.retriever:
            retriever = evidence.retriever
        else:
            from google import genai
            from google.genai import types
            from music_agent.config import resolve_google_api_key
            from music_agent.retrieval import GeminiEmbedder, TheoryRetriever

            key = resolve_google_api_key()
            if not key.configured:
                return _record("search_theory_notes", (query,), {
                    "status": "error", "code": "credentials_unavailable", "passages": [],
                })
            owned_client = genai.Client(
                api_key=key.api_key, vertexai=False,
                http_options=types.HttpOptions(timeout=15000, retry_options=types.HttpRetryOptions(attempts=1)),
            )
            retriever = TheoryRetriever(GeminiEmbedder(owned_client))
        result = await retriever.search(query)
        return _record("search_theory_notes", (query,), result)
    finally:
        if owned_client:
            await owned_client.aio.aclose()
            owned_client.close()


# 3. Music arithmetic uses deterministic functions; model prose is not the evidence.
def transpose_chords(chords: str, from_key: str, to_key: str) -> dict:
    """Transpose a supplied progression, keeping chord quality and slash basses.

    Args:
        chords: Space-separated chord symbols, such as C Am F G/B.
        from_key: Starting tonic and optional major/minor mode.
        to_key: Target tonic in the same mode; reharmonization is not transposition.

    Returns:
        found with exact chord symbols, interval, inputs and formula; invalid_input
        with guidance for unsupported symbols or incompatible modes.
    """
    from music_agent.calculations import transpose_progression

    return _record("transpose_chords", (chords, from_key, to_key), transpose_progression(chords, from_key, to_key))


def transpose_song(title: str, target_key: str, artist: str = "", instrument: str = "Guitar") -> dict:
    """Transpose stored song material using a read-only, instrument-specific lookup.

    Args:
        title: Exact catalog title. Ask which song when it is missing or unclear.
        target_key: Desired sounding tonic and optional mode.
        artist: Optional artist label to resolve a duplicate title.
        instrument: Guitar or Piano; use the learner's choice or ask.

    Returns:
        found with a transposed display copy, assumptions and source chart ID;
        not_found/ambiguous/error for lookup outcomes; invalid_input for bad keys.
        It never writes the catalog or saves/opens a personal song.
    """
    from music_agent.calculations import transpose_catalog_chart
    from music_agent.session import INSTRUMENTS

    if instrument not in INSTRUMENTS:
        result = {"status": "invalid_input", "message": "Choose Guitar or Piano."}
    else:
        lookup = find_chord_chart(title, artist, instrument)
        result = transpose_catalog_chart(lookup["chart"], target_key) if lookup["status"] == "found" else lookup
    return _record("transpose_song", (title, target_key, artist, instrument), result)


def calculate_rhythm(bpm: float, bars: int, beats_per_bar: int, subdivision: int = 1) -> dict:
    """Calculate exact beat timing and passage duration at a fixed tempo.

    Args:
        bpm: Tempo in the explicitly chosen beat unit, between 1 and 400.
        bars: Number of measures, including any repeats the learner wants counted.
        beats_per_bar: Counted beats per measure in the same unit as BPM.
        subdivision: Equal divisions per counted beat, such as 2 for eighths at quarter-note BPM.

    Returns:
        found with beat count, duration and subdivision milliseconds plus formula;
        invalid_input for non-finite, fractional-count or out-of-range inputs.
    """
    from music_agent.calculations import rhythm_numbers

    return _record("calculate_rhythm", (bpm, bars, beats_per_bar, subdivision),
                   rhythm_numbers(bpm, bars, beats_per_bar, subdivision))


def estimate_practice(current_bpm: float, target_bpm: float, bpm_gain_per_week: float,
                      minutes_per_day: float, days_per_week: int, adherence_percent: float = 100) -> dict:
    """Project a music-practice scenario using a user-supplied improvement assumption.

    Args:
        current_bpm: Tempo the learner can currently play cleanly.
        target_bpm: Desired clean playing tempo.
        bpm_gain_per_week: Assumed weekly improvement at full attendance; ask if missing.
        minutes_per_day: Planned minutes in each practice session.
        days_per_week: Planned weekly practice days, from 1 to 7.
        adherence_percent: Expected attendance percentage, from 1 to 100.

    Returns:
        found with scenario weeks, expected sessions/hours, inputs and formula;
        invalid_input for impossible values. This is not a measured skill forecast
        or a promise that the learner will achieve a tempo by a particular date.
    """
    from music_agent.calculations import practice_projection

    return _record("estimate_practice", (current_bpm, target_bpm, bpm_gain_per_week, minutes_per_day, days_per_week, adherence_percent),
                   practice_projection(current_bpm, target_bpm, bpm_gain_per_week, minutes_per_day, days_per_week, adherence_percent))
