"""Build the public seed catalog atomically; safe to repeat, never run by the UI."""

# 1. Source paths are repo-relative, including when launched from another folder.
import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import CATALOG_PATH, normalize_identity, validate_chart
from music_agent.session import GENRES, INSTRUMENTS, SKILL_LEVELS


# 2. Validate authored seed metadata before replacing an existing catalog.
def load_seed() -> dict:
    """Verify real song identities, explicit resource types, and attribution."""
    seed = json.loads((ROOT / "data" / "seed_catalog.json").read_text())
    if not seed["attribution"].strip():
        raise ValueError("Attribution is required")
    identifiers = set()
    for song in seed["songs"]:
        if song["id"] in identifiers:
            raise ValueError("Duplicate song ID")
        identifiers.add(song["id"])
        if song["genre"] not in GENRES or song["difficulty"] not in SKILL_LEVELS:
            raise ValueError("Unknown genre or difficulty")
        if not song["instruments"] or not set(song["instruments"]) <= set(INSTRUMENTS):
            raise ValueError("Unknown instruments")
        if not song["attribution"].strip():
            raise ValueError("Song attribution is required")
        validate_chart(song)
        for instrument in song["instruments"]:
            validate_chart({**song, **song.get("arrangements", {}).get(instrument, {})})
    return seed


# 3. Build a fresh DB in a temporary file, then atomically publish on success.
def seed_catalog(output: Path = CATALOG_PATH) -> tuple[int, int]:
    """Rebuild only public music data, with stable song and resource IDs."""
    seed = load_seed()
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".seed-", suffix=".sqlite", dir=output.parent)
    os.close(descriptor)
    temporary_path = Path(temporary)
    chart_count = 0
    try:
        connection = sqlite3.connect(temporary_path)
        try:
            connection.executescript((ROOT / "schema.sql").read_text())
            with connection:
                for song in seed["songs"]:
                    connection.execute(
                        "INSERT INTO songs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (song["id"], song["title"], song["artist"],
                         normalize_identity(song["title"]), normalize_identity(song["artist"]),
                         song["genre"], song["difficulty"], json.dumps(song["instruments"]),
                         song["source_url"], song["release_year"], song["chart_kind"], song.get("origin", "catalog")),
                    )
                    for instrument in song["instruments"]:
                        chart = {**song, **song.get("arrangements", {}).get(instrument, {})}
                        connection.execute(
                            "INSERT INTO chord_charts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (f"{song['id']}-{instrument.lower()}", song["id"], instrument,
                             chart["key"], chart.get("tuning", "E A D G B E (standard)") if instrument == "Guitar" else None,
                             chart["capo"] if instrument == "Guitar" else None,
                             json.dumps(chart["content"]), chart["attribution"], chart.get("resource_url"),
                             chart.get("chord_source_url"), chart.get("reference_note"), chart.get("checked_on"),
                             chart.get("lyrics_license"), chart.get("lyrics_source_url")),
                        )
                        chart_count += 1
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Catalog integrity check failed")
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("Catalog relationship check failed")
        finally:
            connection.close()
        os.replace(temporary_path, output)
    finally:
        temporary_path.unlink(missing_ok=True)
    return len(seed["songs"]), chart_count


# 4. An explicit CLI action owns writes; the app imports read functions only.
def main() -> None:
    """Seed the default catalog or a disposable output for local tests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=CATALOG_PATH)
    arguments = parser.parse_args()
    songs, charts = seed_catalog(arguments.output)
    print(f"Seeded {songs} songs and {charts} arrangements into {arguments.output}")


if __name__ == "__main__":
    main()
