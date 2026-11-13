# Genre songbook and welcome refinement · 13 November 2026

Riffin’ now has **48 songs, eight per genre**, and **96 Guitar/Piano entries**. The existing four-lesson vector corpus remains unchanged; the song catalog is a separate read-only knowledge store exposed through the existing Guitar tool. See `docs/knowledge-stores.md` for this distinction.

## Delivered behavior

- Favorite genres immediately update **Three song picks**, before final submission. One selected genre supplies eight options; multiple genres supply their union. With no genre, picks are disabled. Removing a genre clears only incompatible draft picks and displays an explanation. Nickname, instrument and compatible picks survive the rerun. The final validator rejects out-of-genre IDs; Cancel preserves the saved profile.
- The previous form became a bordered container of native controls and a single validation/submit button. This enables dependent inputs while keeping profile, favorites, recent views and chat in Streamlit session state. No account, provider or persistent user store is required.
- Three separate pink, sage and lavender benefit cards remain in one row at the tested desktop, tablet and phone widths. Dark ink stays legible in both themes. A warm serif welcome heading, italic violet supporting line and quieter invitation create a distinct hierarchy.
- The catalog expansion adds Wonderwall, Californication, Sweet Home Alabama, Knockin’ on Heaven’s Door, Hotel California, Riptide, Fast Car, Hallelujah, Faded, Titanium, Levels, One More Time, Clarity, Don’t You Worry Child, Autumn Leaves, Fly Me to the Moon, Blue Bossa, All of Me, Take the “A” Train, Für Elise, Moonlight Sonata, Gymnopédie No. 1, Prelude in C, Turkish March, drivers license, good 4 u, Auld Lang Syne and Greensleeves.

## Stored content and limits

There are **86 source-backed harmonic-reference entries** and **ten public-domain accompaniment-study entries**. These are short researched chord vocabularies, brief harmonic movements, analytical centers or authored accompaniment studies, as each entry explicitly states. They are not complete or artist-certified arrangements. Guitar capo shapes and Piano concert-pitch equivalents differ where needed. The 28 new works and research scope are listed in `docs/chord_research.md`.

Three works contain public-domain lyrics: Amazing Grace (three Newton stanzas), Auld Lang Syne (verse/chorus printed in the 1918 Canadian Soldiers’ Song Book), and Greensleeves (first verse/refrain, spelling modernized from the historical text). Riffin’ supplies simplified accompaniment. Stored lyric entries now retain `lyrics_license` and `lyrics_source_url` in SQLite and seed JSON; validation rejects missing reuse metadata. Instrumental classical works have no fabricated lyrics.

**Not delivered:** complete contemporary lyrics and full published arrangements for every song. Online availability does not supply redistribution permission. Those require rights-cleared content or a licensed provider. No full modern lyrics, paid scores, timing grids or complete third-party arrangements were scraped into the repository. References and lyric studies are labeled by their actual scope.

## Verification

**50 local tests passed on Python 3.12.1**. The four added tests cover all six picker filters/multiple-genre union; compatible-pick pruning, draft-field retention and cancel; lyric reuse metadata; and out-of-genre validation. Existing complete no-key flows, ranking, repeated opens/saves, independent sessions, automatic Search fixtures, parameterized read-only catalog access, provenance and repeatable byte-identical seeding still pass.

Actual Chrome checks verified the three-card row and welcome hierarchy in **Light and Dark at 1440, 1024 and 390 px**, with no horizontal overflow or Streamlit exceptions. An initial browser pass inspected eight song identities for all six single genres. The longer combined dropdown is virtualized, so visible DOM rows are not a reliable full-option count; exact option-set and union assertions use AppTest. The final browser flow uses native search/selection for a real song in each genre and checks the displayed catalog counts.

The browser completed native selection in all six genres, the 16-song Rock/Electronic union, removal of only Rock while preserving two Electronic picks and nickname, completion with a third Electronic pick, and profile editing across a theme change. A harness-only lookup-label mismatch then stopped the script at Catalog; a continuation completed the direct Auld Lang Syne open, stored public-domain lyric display, phone overflow check and selected-song/profile retention across Light/Dark. `completed-flow.json` and `v5-finish.log` record that continuation separately. Catalog bytes stayed unchanged during the user actions. Afterward the explicit seed command synchronized a provenance clarification; a disposable repeat build matched the public seed byte-for-byte, all 96 entries validated, and SQLite integrity passed.

Artifacts are outside Git: `/private/tmp/riffin-no-key/v5/` for screenshots and completed-flow evidence, `/private/tmp/riffin-no-key/v5-browser.log` and `/private/tmp/riffin-no-key/v5-finish.log` for the two browser portions, and `/private/tmp/riffin-v5-tests.log` for tests. No live Google calls were needed for this revision. Previous provider checks and remaining hosted checks are documented separately.

Commands:

```sh
.venv/bin/python scripts/seed_catalog.py
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m streamlit run app.py --server.headless=true --server.address=127.0.0.1 --server.port=8504
```

Current preview: **http://localhost:8504**. Normal startup remains `.venv/bin/python -m streamlit run app.py`.

Files changed: `app.py`, `music_agent/session.py`, `assets/styles.css`, `data/seed_catalog.json`, `data/catalog.sqlite`, `schema.sql`, `db.py`, `scripts/seed_catalog.py`, `docs/chord_research.md`, `docs/catalog-attribution.md`, `docs/knowledge-stores.md`, `tests/test_app_flow.py`, `tests/test_catalog.py`, README, UI guide, specification, checklist and this report. No commits, pushes or deployment.
