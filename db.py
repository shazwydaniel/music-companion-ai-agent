"""Fixed, parameterized reads of Riffin's public SQLite seed catalog."""

# 1. Paths resolve from source, independently of the current working directory.
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
from urllib.parse import urlparse
from typing import Iterator

from music_agent.security import is_sql_mutation

CATALOG_PATH = Path(__file__).resolve().parent / "data" / "catalog.sqlite"


def normalize_identity(value: str) -> str:
    """Normalize case and whitespace without treating user text as SQL."""
    return " ".join(value.casefold().split())


# 2. Every runtime connection is read-only; neither a miss nor a write creates a DB.
@contextmanager
def read_catalog(path: Path = CATALOG_PATH) -> Iterator[sqlite3.Connection]:
    """Open a short-lived read-only connection to the public catalog."""
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    try:
        yield connection
    finally:
        connection.close()


def execute_catalog_read(connection: sqlite3.Connection, sql: str, parameters: tuple = ()) -> sqlite3.Cursor:
    """Permit only one AST-verified SELECT with separately bound values."""
    if is_sql_mutation(sql):
        raise ValueError("Catalog queries must be a single read-only SELECT")
    return connection.execute(sql, parameters)


def _song(row: sqlite3.Row) -> dict:
    """Decode public metadata; no user state enters this service."""
    result = dict(row)
    result["instruments"] = json.loads(result["instruments"])
    return result


# 3. Public browsing uses a fixed query and deterministic ordering.
def list_songs(path: Path = CATALOG_PATH) -> list[dict]:
    """Return the seed songs in a stable title, artist, and ID order."""
    with read_catalog(path) as connection:
        rows = execute_catalog_read(connection,
            "SELECT id, title, artist, genre, difficulty, instruments, source_url, release_year, chart_kind, origin FROM songs "
            "ORDER BY normalized_title, normalized_artist, id"
        ).fetchall()
    return [_song(row) for row in rows]


# 4. Validate catalog identity at the read boundary before rendering or actions.
def get_chart(chart_id: str, path: Path = CATALOG_PATH) -> dict:
    """Read one chart by ID, distinguishing missing content from lookup errors."""
    try:
        with read_catalog(path) as connection:
            row = execute_catalog_read(connection,
                "SELECT c.*, s.title, s.artist, s.genre, s.difficulty, s.source_url, s.release_year, s.chart_kind, s.origin "
                "FROM chord_charts c JOIN songs s ON s.id = c.song_id WHERE c.id = ?",
                (chart_id,),
            ).fetchone()
        if row is None:
            return {"status": "not_found"}
        chart = dict(row)
        chart["content"] = json.loads(chart["content"])
        validate_chart(chart)
        if not chart["attribution"].strip():
            raise ValueError("Chart has no attribution")
        return {"status": "found", "chart": chart}
    except (sqlite3.Error, ValueError, TypeError, KeyError):
        # A retrieval failure never masquerades as a confirmed catalog miss.
        return {"status": "error", "message": "The catalog chart could not be read."}


def validate_content(content: object) -> None:
    """Reject malformed chart sections before they reach the aligned renderer."""
    if not isinstance(content, list) or not content:
        raise ValueError("Expected named chart sections")
    for section in content:
        if not isinstance(section, dict) or not isinstance(section.get("name"), str):
            raise ValueError("Expected a section name")
        lines = section.get("lines")
        if not isinstance(lines, list) or not lines:
            raise ValueError("Expected chart lines")
        for line in lines:
            if not isinstance(line, dict) or not isinstance(line.get("chords"), str):
                raise ValueError("Expected a chord line")
            if "lyrics" in line and not isinstance(line["lyrics"], str):
                raise ValueError("Expected optional lyric text")


def validate_chart(chart: dict) -> None:
    """Keep licensed resource links distinct from stored practice charts."""
    if chart["chart_kind"] in {"inline", "reference"}:
        validate_content(chart["content"])
        if any("lyrics" in line for section in chart["content"] for line in section["lines"]):
            lyric_source = urlparse(chart.get("lyrics_source_url") or "")
            if chart.get("lyrics_license") not in {"public-domain", "licensed", "CC0-1.0"} or lyric_source.scheme != "https" or not lyric_source.netloc:
                raise ValueError("Stored lyrics need explicit reuse status and a source")
        if chart["chart_kind"] == "reference":
            if any("lyrics" in line for section in chart["content"] for line in section["lines"]):
                raise ValueError("Contemporary references contain harmonic facts, not copied lyrics")
            source = urlparse(chart.get("chord_source_url") or "")
            if source.scheme != "https" or not source.netloc or not chart.get("reference_note"):
                raise ValueError("A chord reference needs a source and scope note")
    elif chart["chart_kind"] == "external":
        if chart["content"] != []:
            raise ValueError("External resources cannot contain copied charts")
        url = urlparse(chart.get("resource_url") or "")
        if url.scheme != "https" or url.netloc not in {"www.musicnotes.com", "www.davebrubeck.com"}:
            raise ValueError("Expected an approved chart resource")
    else:
        raise ValueError("Unknown chart kind")
    source = urlparse(chart["source_url"])
    if source.scheme != "https" or not source.netloc:
        raise ValueError("Expected a metadata source")


# 5. Title/artist lookup has a bounded ambiguity response and optional instrument.
def find_chord_chart(
    title: str, artist: str = "", instrument: str = "", path: Path = CATALOG_PATH
) -> dict:
    """Look up a stored arrangement; user strings are always bound parameters.

    Returns:
        found with a validated chart; ambiguous with bounded song/arrangement
        choices; not_found for a confirmed miss; error for a retrieval failure.
    """
    try:
        with read_catalog(path) as connection:
            rows = execute_catalog_read(connection,
                "SELECT c.id AS chart_id, s.id AS song_id, s.title, s.artist, c.instrument "
                "FROM songs s JOIN chord_charts c ON c.song_id = s.id "
                "WHERE s.normalized_title = ? "
                "AND (? = '' OR s.normalized_artist = ?) "
                "AND (? = '' OR c.instrument = ?) "
                "ORDER BY s.normalized_artist, s.id, c.instrument LIMIT 20",
                (normalize_identity(title), normalize_identity(artist),
                 normalize_identity(artist), instrument, instrument),
            ).fetchall()
        if not rows:
            return {"status": "not_found"}
        if len(rows) > 1:
            return {"status": "ambiguous", "choices": [dict(row) for row in rows]}
        return get_chart(rows[0]["chart_id"], path)
    except sqlite3.Error:
        return {"status": "error", "message": "The catalog lookup is unavailable."}
