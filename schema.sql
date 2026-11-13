-- 1. Public catalog only: no profile, chat, activity, or credential tables.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS songs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    normalized_artist TEXT NOT NULL,
    genre TEXT NOT NULL,
    difficulty TEXT NOT NULL CHECK (difficulty IN ('Beginner', 'Intermediate')),
    instruments TEXT NOT NULL CHECK (json_valid(instruments)),
    source_url TEXT NOT NULL,
    release_year INTEGER,
    chart_kind TEXT NOT NULL CHECK (chart_kind IN ('inline', 'reference', 'external')),
    origin TEXT NOT NULL DEFAULT 'catalog' CHECK (origin IN ('catalog', 'original-demo')),
    UNIQUE (normalized_title, normalized_artist)
);

-- 2. Structured arrangements retain their source and instrument metadata.
CREATE TABLE IF NOT EXISTS chord_charts (
    id TEXT PRIMARY KEY,
    song_id TEXT NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    instrument TEXT NOT NULL CHECK (instrument IN ('Guitar', 'Piano')),
    musical_key TEXT,
    tuning TEXT,
    capo INTEGER CHECK (capo IS NULL OR capo BETWEEN 0 AND 12),
    content TEXT NOT NULL CHECK (json_valid(content)),
    attribution TEXT NOT NULL,
    resource_url TEXT,
    chord_source_url TEXT,
    reference_note TEXT,
    checked_on TEXT,
    lyrics_license TEXT CHECK (lyrics_license IS NULL OR lyrics_license IN ('public-domain', 'licensed', 'CC0-1.0')),
    lyrics_source_url TEXT,
    UNIQUE (song_id, instrument)
);

-- 3. Exact normalized identities make title ambiguity explicit.
CREATE INDEX IF NOT EXISTS songs_title_lookup ON songs(normalized_title, normalized_artist);
