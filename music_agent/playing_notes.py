"""Instrument-specific practice ideas, kept separate from catalog provenance."""

# 1. Chord symbols describe harmony; the playing motion depends on the instrument.
def playing_note(instrument: str) -> dict[str, str] | None:
    """Return a general, clearly labeled accompaniment idea for a chart.

    Args:
        instrument: Validated catalog instrument, Guitar or Piano.

    Returns:
        A title, suggestion, and scope note; None for unknown instruments.
        Suggestions are teaching ideas, not sourced recording transcriptions.
    """
    if instrument == "Guitar":
        return {
            "title": "Guitar playing idea",
            "suggestion": "Start with one downstroke at each chord change. Then try gentle down and up strokes or picked notes to fit the song’s pulse; check the listed tuning and capo before playing.",
            "scope": "A Riffin’ practice suggestion, not a verified strumming pattern or fingering from the recording.",
        }
    if instrument == "Piano":
        return {
            "title": "Piano playing idea",
            "suggestion": "Play chord roots with your left hand and chord tones with your right. Try nearby inversions to keep common notes and move smoothly between chords.",
            "scope": "A Riffin’ practice suggestion, not a verified piano voicing or performance transcription.",
        }
    return None
