# Original demos, Music Math and documentation consolidation

Verified locally on **13 November 2026**, Python **3.12.1**, with the pinned dependencies. Preview: **http://localhost:8504**. No commits, pushes or deployment were performed.

## Delivered

1. **One Markdown folder.** All project Markdown except the root `README.md` is under `docs/`. Eight files were relocated; colliding attribution filenames became `asset-attribution.md` and `catalog-attribution.md`, and the former knowledge README became `knowledge-stores.md`. Relative links, README references and the runtime lesson path were updated. `knowledge/retrieval_checks.json` remains explicit and separate from the Markdown corpus. `scripts/index_knowledge.py` still loads the four original lessons and stable IDs. `INDEX.md` provides the documentation map.
2. **Padded hierarchy.** The floating panel has a 16 px outer inset, inset node cards, padded disclosure content and footer, and bounded scrolling. It now shows five total nodes: coordinator plus Guitar, Piano & Theory, Web Search and Music Math. Actual ADK callbacks and explicitly labeled local Python-tool events drive state; no progress is simulated. Native collapse and the existing drag handle remain.
3. **Six original demos.** Basement Comet (Rock), Pocket-Sized Sunrise (Pop), Lanterns After Closing (Jazz), Maple Postcard (Indie / Folk), Neon Paper Planes (Electronic) and Courtyard Miniature (Classical) each contain eight new lyric lines in verse/refrain sections, with Guitar/Piano accompaniment. They are generated teaching material, clearly marked **Original demo**, with a CC0 dedication to the extent rights apply. Common genre-associated chord patterns are examples, not exclusive genre rules. No third-party lyrics or recorded arrangement was copied. See `original-demos.md` for all new text and credits.
4. **Music Math specialist.** A fourth `AgentTool` delegates to typed `transpose_chords`, `transpose_song`, `calculate_rhythm` and `estimate_practice`. Bounded Python performs the arithmetic. The displayed numeric results come from tool evidence, replacing unsupported model numbers. Inputs, formula and assumptions are available with each result. No arbitrary expression evaluation, write tool or new personal persistence layer exists.
5. **Local controls.** Songbook transposition and the Chat Music calculator work without Gemini. Transposition returns a session display copy, preserves chord quality/slash basses and lyric anchors, accounts for known capo/D-standard offsets, and labels output as concert pitch with standard tuning/no capo. Original key restores the source display. A partial source remains partial. Unsupported tunings fail clearly; switching major/minor requires reharmonization rather than transposition. Rhythm timing uses an explicit beat unit. Practice projections are simple scenarios under a supplied weekly-gain assumption, not individual skill forecasts or guarantees.
6. **Music-only guardrail.** Clear unrelated requests are redirected locally before credentials/model/Search calls. The same gate is installed in ADK before-agent/tool callbacks, together with a music-only semantic coordinator instruction. Existing destructive-catalog refusal remains. Music artists, catalog titles and elliptical follow-ups have representative coverage. The lexical/semantic boundary is not claimed to classify every possible paraphrase perfectly.

The public catalog now has **54 songs / 108 instrument entries**: 48 sourced real songs plus six original demos; each genre has eight real songs and one demo. There are **86 harmonic references**, **ten public-domain accompaniment-study entries**, and **twelve original-demo accompaniment entries**. All nine lyric-bearing works retain reuse metadata; this extension does not copy full contemporary lyrics or published arrangements.

## Automated and live checks

**65 local tests passed.** New tests cover roots/qualities/slash basses, accidentals and multiline input, major/minor rejection, capo/D-standard conversion, lyric-anchor growth, immutable source objects, beat-unit equivalence in compound meter, finite/range checks, fractional-gain rounding, scenario assumptions, generated demo metadata, local UI controls, session transposition, unrelated requests and actual ADK callback refusal. Existing catalog, retrieval, no-key, isolation, rerun and source tests remain passing. Scripted model/vector fixtures are not presented as live Gemini evidence.

Independent real Google checks passed:

| Check | Actual tool evidence |
|---|---|
| `music_math` | Root → Music Math → `transpose_chords`; C Am F G/B from C major to D major produced **D Bm G A/C#**, shift 2 semitones; no Search. |
| `practice_estimate` | Root → Music Math → `estimate_practice`; current 80, target 120, assumed gain 5 BPM/week, 20 minutes/session, five days/week, 100% attendance produced **8 weeks, 40 sessions, 13.3333 practice hours**; no Search. |

Chrome browser checks passed:

- Local practice calculator returned the expected scenario.
- All six original demos opened directly from Catalog with two formatted lyric sections and original-demo attribution.
- Pop demo transposition to D major displayed updated chords; chart, transposition and profile survived Light/Dark changes.
- Both themes at **1440, 1024 and 390 px** had no horizontal overflow or Streamlit exceptions. The panel had five nodes, 16 px outer padding, inset node bounds and viewport-contained scrolling.
- A real Chat transposition highlighted coordinator and Music Math **while their actual callbacks were active**, then showed the correct calculated symbols.
- “What is the capital of France?” returned `out_of_scope`; the local guard did not invoke a model or Search for it.
- A second independent browser context started onboarding without the first visitor's profile. Catalog bytes stayed unchanged through all browser actions.

Artifacts remain outside Git: `/private/tmp/riffin-no-key/v6/evidence.json`, the six `original-transpose-panel-*` screenshots, `live-music_math.png`, `scope-refusal.png`, `/private/tmp/riffin-no-key/v6-browser.log`, `/private/tmp/riffin-v6-tests.log`, `/private/tmp/riffin-v6-live-math.jsonl` and `/private/tmp/riffin-v6-live-practice.jsonl`.

## Commands and file changes

```sh
.venv/bin/python scripts/seed_catalog.py
.venv/bin/python scripts/index_knowledge.py
.venv/bin/python -m unittest discover -s tests
.venv/bin/python scripts/check_agent_integration.py --check music_math
.venv/bin/python scripts/check_agent_integration.py --check practice_estimate
.venv/bin/python -m streamlit run app.py --server.headless=true --server.address=127.0.0.1 --server.port=8504
```

New code: `music_agent/calculations.py`, `music_agent/calculator_ui.py`, `tests/test_calculations.py`. Updated: `app.py`, the agent/Runner/tool/guardrail/activity/session/retrieval/chat modules, `schema.sql`, `db.py`, seeder and live-check scripts, seed JSON/SQLite, styles, existing test expectations/fixtures, README and consolidated documentation. The documentation move mapping is reflected in `INDEX.md` and current README links.

Hosted behavior, clean-checkout installation and publication/history review remain pending under the existing capstone checklist. No new hosted/provider blocker was observed for this phase's two live calculation checks. The unrelated-topic gate has representative tests, not a universal classification guarantee. Existing full contemporary lyric/arrangement clearance requirements remain unchanged.
