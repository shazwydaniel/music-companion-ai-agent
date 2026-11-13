"""Bounded, deterministic music arithmetic; no eval, provider or catalog writes."""

# 1. Pitch classes and key parsing preserve chord quality, rather than reharmonize.
import math
import re
from decimal import Decimal, ROUND_CEILING

SHARPS = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
FLATS = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")
PITCH = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
KEY = re.compile(r"^([A-G](?:#|b)?)(?:\s*(major|minor|maj|min|m))?$", re.I)
CHORD = re.compile(r"^([A-G](?:#|b)?)((?:(?:maj|min|dim|aug|sus|add|omit|no|m|M)|[0-9+#b°ø()\-])*)(?:/([A-G](?:#|b)?))?$")


def pitch(note: str) -> int:
    """Convert a validated note to a twelve-tone equal-temperament pitch class."""
    return (PITCH[note[0].upper()] + note.count("#") - note.count("b")) % 12


def parse_key(value: str) -> tuple[str, str | None]:
    """Accept a tonic and optional major/minor mode, never arbitrary expressions."""
    if not isinstance(value, str) or len(value) > 30:
        raise ValueError("Use a key such as C, F# minor or Bb major.")
    match = KEY.fullmatch(value.strip().replace("♯", "#").replace("♭", "b"))
    if not match:
        raise ValueError("Use a key such as C, F# minor or Bb major.")
    note, mode = match.groups()
    return note[0].upper() + note[1:].lower(), ("minor" if mode.lower() in {"m", "min", "minor"} else "major") if mode else None


def _number(value: float, name: str, low: float, high: float) -> float:
    """Reject bools, non-finite numbers and unrealistic/unbounded input sizes."""
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{name} must be a finite number between {low:g} and {high:g}.")
    return value


def _whole(value: int, name: str, low: int, high: int) -> int:
    _number(value, name, low, high)
    if int(value) != value:
        raise ValueError(f"{name} must be a whole number.")
    return int(value)


def _failure(error: ValueError) -> dict:
    return {"status": "invalid_input", "message": str(error)}


def _palette(tonic: str, mode: str | None) -> tuple[str, ...]:
    """Prefer common flat spellings for flat-side major and minor keys."""
    flat_side = tonic in ({"D", "G", "C", "F", "Bb", "Eb", "Ab"} if mode == "minor" else {"F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb"})
    return FLATS if "b" in tonic or flat_side else SHARPS


# 2. Transpose roots/slash basses; render at original lyric columns where they fit.
def _chord(value: str, shift: int, names: tuple[str, ...]) -> str:
    if value in {"|", "||", "||:", ":||", "%", "N.C.", "NC"}:
        return value
    match = CHORD.fullmatch(value)
    if not match:
        raise ValueError(f"Unsupported chord symbol: {value[:30]}. Use chord names separated by spaces.")
    root, quality, bass = match.groups()
    return names[(pitch(root) + shift) % 12] + quality + ("/" + names[(pitch(bass) + shift) % 12] if bass else "")


def _line(line: dict, shift: int, names: tuple[str, ...]) -> dict:
    original = line["chords"].replace("♯", "#").replace("♭", "b")
    if len(original) > 2000:
        raise ValueError("Keep each chord line under 2000 characters.")
    output, lyrics, extra = "", line.get("lyrics"), 0
    # If a longer accidental collides, insert matching space into the lyric line.
    for token in re.finditer(r"\S+", original):
        chord = _chord(token.group(), shift, names)
        column = token.start() + extra
        if output and len(output) >= column:
            added = len(output) + 1 - column
            if lyrics is not None:
                lyrics = lyrics[:column] + " " * added + lyrics[column:]
            extra += added
            column += added
        output = output.ljust(column) + chord
    return {"chords": output, **({"lyrics": lyrics} if lyrics is not None else {})}


def transpose_progression(chords: str, from_key: str, to_key: str) -> dict:
    """Transpose written chord symbols, preserving qualities and slash basses."""
    try:
        source, source_mode = parse_key(from_key)
        target, target_mode = parse_key(to_key)
        if source_mode and target_mode and source_mode != target_mode:
            raise ValueError("Transposition preserves major/minor quality. Changing mode needs reharmonization.")
        if not isinstance(chords, str) or not chords.strip():
            raise ValueError("Enter at least one chord.")
        shift = (pitch(target) - pitch(source)) % 12
        names = _palette(target, target_mode or source_mode)
        if len(chords) > 10000:
            raise ValueError("Keep the progression under 10000 characters.")
        changed = "\n".join(_line({"chords": line}, shift, names)["chords"] for line in chords.splitlines())
        return {"status": "found", "kind": "transpose", "summary": f"{from_key} → {to_key}: {changed}",
                "inputs": {"chords": chords, "from_key": from_key, "to_key": to_key},
                "outputs": {"chords": changed, "semitones_up": shift},
                "formula": "(target pitch class − source pitch class) mod 12; shift each root and slash bass equally.",
                "assumptions": ["Chord qualities are preserved; enharmonic spelling uses a consistent sharp/flat palette."]}
    except ValueError as error:
        return _failure(error)


def transpose_catalog_chart(chart: dict, target_key: str) -> dict:
    """Return a concert-pitch display copy, accounting for known capo/D tuning."""
    try:
        raw_key = chart.get("musical_key") or chart.get("key") or ""
        match = re.match(r"([A-G][#b]?)(?:\s+(major|minor))?", raw_key)
        if not match:
            raise ValueError("The catalog has no unambiguous starting tonic for this entry.")
        source, source_mode = match.groups()
        target, target_mode = parse_key(target_key)
        if source_mode and target_mode and source_mode != target_mode:
            raise ValueError("Transposition preserves major/minor quality. Changing mode needs reharmonization.")
        tuning = chart.get("tuning") or ""
        tuning_shift = -2 if tuning.startswith("D G C F A D") else 0
        if tuning and tuning != "E A D G B E (standard)" and not tuning_shift:
            raise ValueError("This tuning needs a verified pitch mapping before automatic transposition.")
        capo = chart.get("capo") or 0
        shift = (pitch(target) - pitch(source) + capo + tuning_shift) % 12
        names = _palette(target, target_mode or source_mode)
        content = [{"name": section["name"], "lines": [_line(line, shift, names) for line in section["lines"]]}
                   for section in chart["content"]]
        if not content:
            raise ValueError("This entry has no stored chord material to transpose.")
        return {"status": "found", "kind": "transpose_song", "summary": f"{chart['title']} transposed to {target_key} (concert pitch).",
                "inputs": {"chart_id": chart["id"], "from_key": raw_key, "target_key": target_key},
                "outputs": {"content": content, "target_key": target + (" " + (target_mode or source_mode) if target_mode or source_mode else ""),
                            "capo": 0, "tuning": "standard", "semitones_up": shift},
                "formula": "Written-chord shift = target tonic − sounding tonic + source capo + known tuning offset (mod 12).",
                "assumptions": ["Output chord names are concert pitch: use standard tuning with no capo.",
                                "Original source scope still applies; a partial reference remains partial.",
                                "This changes chord pitch, not melody notation or major/minor mode."]}
    except ValueError as error:
        return _failure(error)


# 3. Rhythm arithmetic uses an explicitly chosen beat unit, not an assumed meter.
def rhythm_numbers(bpm: float, bars: int, beats_per_bar: int, subdivision: int = 1) -> dict:
    """Calculate beat/subdivision timing and duration for a fixed-tempo passage."""
    try:
        _number(bpm, "BPM", 1, 400)
        bars = _whole(bars, "Bars", 1, 10000)
        beats_per_bar = _whole(beats_per_bar, "Beats per bar", 1, 16)
        subdivision = _whole(subdivision, "Subdivisions per beat", 1, 16)
        beats = bars * beats_per_bar
        seconds = beats * 60 / bpm
        return {"status": "found", "kind": "rhythm", "summary": f"{bars} bars × {beats_per_bar} beats at {bpm:g} BPM take {seconds:.2f} seconds ({beats} beats).",
                "inputs": {"bpm": bpm, "bars": bars, "beats_per_bar": beats_per_bar, "subdivision": subdivision},
                "outputs": {"beats": beats, "duration_seconds": round(seconds, 4), "milliseconds_per_beat": round(60000 / bpm, 4),
                            "milliseconds_per_subdivision": round(60000 / bpm / subdivision, 4)},
                "formula": "seconds = bars × beats per bar × 60 / BPM; subdivision ms = 60000 / BPM / subdivisions.",
                "assumptions": ["Tempo is constant, with no pauses or repeats beyond the entered bars.",
                                "BPM and beats per bar must use the same beat unit; for 6/8, enter 2 if BPM counts dotted quarters, or 6 if it counts eighth notes."]}
    except ValueError as error:
        return _failure(error)


# 4. Progress projection is a transparent scenario, not a learned skill forecast.
def practice_projection(current_bpm: float, target_bpm: float, bpm_gain_per_week: float,
                        minutes_per_day: float, days_per_week: int, adherence_percent: float = 100) -> dict:
    """Estimate a timeline under the learner's explicit linear-improvement assumption."""
    try:
        _number(current_bpm, "Current BPM", 1, 400)
        _number(target_bpm, "Target BPM", 1, 400)
        _number(bpm_gain_per_week, "Assumed BPM gain per week", .1, 60)
        _number(minutes_per_day, "Minutes per session", 1, 240)
        days_per_week = _whole(days_per_week, "Practice days per week", 1, 7)
        _number(adherence_percent, "Adherence percent", 1, 100)
        decimal_gain = Decimal(str(bpm_gain_per_week)) * Decimal(str(adherence_percent)) / 100
        gap = max(Decimal(0), Decimal(str(target_bpm)) - Decimal(str(current_bpm)))
        weeks = int((gap / decimal_gain).to_integral_value(rounding=ROUND_CEILING))
        gain = float(decimal_gain)
        if weeks > 5200:
            raise ValueError("This scenario exceeds 100 years. Use a nearer goal or revisit the assumptions.")
        sessions = weeks * days_per_week * adherence_percent / 100
        hours = sessions * minutes_per_day / 60
        return {"status": "found", "kind": "practice_estimate", "summary": f"Scenario estimate: {weeks} weeks, about {sessions:.1f} completed sessions and {hours:.2f} practice hours.",
                "inputs": {"current_bpm": current_bpm, "target_bpm": target_bpm, "bpm_gain_per_week": bpm_gain_per_week,
                           "minutes_per_day": minutes_per_day, "days_per_week": days_per_week, "adherence_percent": adherence_percent},
                "outputs": {"weeks": weeks, "expected_sessions": round(sessions, 2), "practice_hours": round(hours, 4), "effective_bpm_gain_per_week": round(gain, 4)},
                "formula": "weeks = ceil(max(0, target − current) / (assumed weekly gain × adherence / 100)); hours = weeks × days × adherence / 100 × minutes / 60.",
                "assumptions": ["The weekly gain is your scenario assumption, not a measured or guaranteed learning rate.",
                                "This simple model assumes improvement scales linearly with attendance; it does not predict an individual's ability.",
                                "An already-reached target needs zero additional weeks in this scenario."]}
    except ValueError as error:
        return _failure(error)
