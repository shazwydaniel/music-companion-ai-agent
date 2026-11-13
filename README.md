# Riffin’

Riffin’ is a music companion for beginner and intermediate musicians, built for an AI Engineering capstone. The working display name is **Riffin’**; the repository and importable package keep their existing technical names.

**A bandmate in your browser.** A one-time session greeting introduces Riffin’ in a modal over the onboarding page; three pastel cards introduce song discovery, sourced chord references and AI music/practice help. A fixed brand bar shares the top toolbar area; pink, sage and lavender pills identify your nickname, instrument and level. Earlier interface checks are recorded in [current verification](docs/interface-v8-verification.md). All Markdown is under [docs/](docs/INDEX.md) except this README.

## Current phase

Riffin’ is a runnable local capstone: four ADK specialists route music requests, a read-only SQLite catalog and four authored lessons supply local facts, and Streamlit presents recommendations, chords and chat. Input guards mask common personal identifiers and block clear prompt-injection, unrelated and destructive requests. SQLite reads use an AST mutation check, `mode=ro` and `PRAGMA query_only`. Model callbacks record token counts and a paid-tier cost estimate without logging prompts. Four public golden cases passed a separate live Gemini judge on 13 November 2026; the [submission benchmark report](docs/EVALUATION_BENCHMARK_REPORT.md) includes the assistant and judge spend.

**Capstone limits:** MCP discovery is deliberately omitted, so that rubric item is unmet. The current implementation has not been pushed or deployed by this work; hosted behavior is unverified. You control commits, pushes and Streamlit Community Cloud deployment.

Latest updates: **For You** limits local cards to the selected genres, instrument and playing level, then uses the Google Search specialist for session-cached suggestions outside the catalog when a server key is present. **Chat** shows a colored status tag beside its AI usage card. The saved browser report below predates these two changes; local automated tests cover their behavior, while the final visual layout remains to be checked in a browser. One live discovery call returned two new songs and four grounding links; a later call returned no grounding, which the app reports while preserving local picks.

The main workspace is **Let’s find your groove → For You**, with icon navigation to **Browse Songs**, **Saved & Recent**, **Chords & Lyrics** and **Chat**. Chat has its own peach accent and a faint divider; the other views use a compact tab rail, distinct from profile pills. A compact sticky brand header, a licensed griffin mascot and genre border stickers give Riffin its music identity. A fresh session starts with the **Start Playing** greeting, then asks for a nickname, Guitar or Piano, Beginner or Intermediate level, favorite genres, and exactly three distinct song picks. Edit profile changes the recommendations immediately. Onboarding, local catalog recommendations, catalog and chart/resource views work without a Google key, account, or credentials.

The **Chat** view integrates four Google ADK specialists: Songbook, Music Theory, Web Search and Music Math. It supports internal retrieval, automatic Search fallback and deterministic music calculations. These provider features need a server Google key; the offline flow above remains available without one. The destructive-request and unrelated-topic guardrails also work without a key. Local calculation controls and transposition do not need Gemini. Live Gemini replies, production embedding calibration, and grounded Search passed locally on 13 November 2026. Hosted deployment remains pending. See [Agent integration](docs/agent-integration.md) for the Lab 5 mapping, retrieval gate, source handling, and privacy boundaries.

Tested Python version: **3.12.1**. Run commands from the repository root. `requirements.txt` pins Streamlit 1.67.0, Google ADK 2.14.0, Google Gen AI SDK 2.34.0, Chroma 1.5.9, and SQLGlot 30.31.0; transitive packages are resolved by pip.

## Local startup

Create a local virtual environment, install dependencies, and start the app:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/configure_chrome.py  # macOS: open local Streamlit URLs in Chrome
python -m streamlit run app.py
```

Open the URL printed by Streamlit (normally `http://localhost:8501`). Stop the server with `Ctrl+C`. If `.venv` already exists with Python 3.12, reuse it. The equivalent startup command without activation is:

```sh
.venv/bin/python -m streamlit run app.py
```

On macOS, the optional one-time `configure_chrome.py` step installs a tiny `open` shim inside this ignored `.venv`. With the virtual environment activated, Streamlit's normal `python -m streamlit run app.py` command opens local URLs in **Google Chrome**. Other `open` arguments pass through to macOS, and your system default browser is unchanged. If you recreate `.venv`, rerun the setup step. Without activation, use the usual default browser or activate `.venv` first.

The public seed catalog is included at `data/catalog.sqlite`; no key or index build is needed. To rebuild a missing catalog or reproduce the seed explicitly:

```sh
.venv/bin/python scripts/seed_catalog.py
```

The script replaces only the public seed database after validating a complete temporary build. The running app never seeds or writes to SQLite.

## Optional Google key

The server resolves the first nonblank string in this order:

1. `GOOGLE_API_KEY` in Streamlit Secrets.
2. `GOOGLE_API_KEY` in the local process environment.
3. A missing-key status that keeps the shell running.

For local Secrets, create the **file** `.streamlit/secrets.toml` in the existing `.streamlit` directory. Fill the quoted value privately:

```toml
GOOGLE_API_KEY = ""
```

Alternatively, set `GOOGLE_API_KEY` through your terminal's environment or IDE's private environment configuration before startup. `.env` files are ignored but are **not automatically loaded**. Restart Streamlit after changing credential configuration.

After onboarding, the header **Connection** popover displays key presence only. The key remains in server variables and short-lived SDK clients; it is never rendered or put in Streamlit/ADK session state. Missing or unreadable Secrets fall back to the environment. Chat runs on submission. A confirmed local miss triggers one query-only Web Search automatically; ordinary reruns never resubmit. Say “local only” to prevent Web Search for a request. `RIFFIN_MODEL` defaults to `gemini-3.6-flash`; its Search compatibility and locally verified key access are explained in [Agent integration](docs/agent-integration.md#agents-and-model).

For a future Community Cloud deployment, the same blank TOML template belongs in **Advanced settings → Secrets**, with the provided key filled in privately. The user controls all GitHub commits, pushes, and deployment; hosted AI and Search checks remain pending.

## Appearance

Use the top-right **⋮ menu → Light or Dark** (Streamlit 1.67). Both appearances are defined in `.streamlit/config.toml` using Streamlit's [switchable theme configuration](https://docs.streamlit.io/develop/api-reference/configuration/config.toml), with the warm paper / ink and charcoal / cream colors from `docs/UI_STYLE_GUIDE.md`. The native selector remains available.

Poppins is the default for headings, body and controls. Five font faces are bundled under `static/fonts/` and served locally, with the SIL Open Font License and credits in [asset attribution](docs/asset-attribution.md). Chords retain a monospace grid with IBM Plex Mono/system fallbacks. Restart Streamlit once after the font/static-serving configuration changes. Original local SVG art gives each genre a color; the featured card carries the primary profile genre's decorative sticker (Rock uses a flame). Native controls and a responsive grid keep the same flow at desktop and narrow widths. Long chart lines scroll inside a focusable chart region.

**Suggested Prompts** are grouped in the Chat welcome card by Knowledge Base, Songs & chords, Calculations, Google Search, Parallel agents and Boundaries. Selecting one fills the text so you can edit it; it does not call an agent or send until you submit. Song pages place **Open Chords** beside the title, before quality tags and source disclosures. Press it to jump to the sheet; the anchored **Back to Chat** row preserves the conversation. Profile details, song qualities and answer statuses use **Label : Value**; Chat places its colored status tag to the left of the AI usage card.

## Catalog, ranking, and session lifecycle

The seed contains **48 real songs plus six original genre demos, with 108 Guitar/Piano entries**. Each genre has **eight real songs and one clearly labeled original demo**. Recent Pop includes Billie Eilish (2024), Olivia Rodrigo's **drop dead** and **the cure** (2026), and The Weeknd (2024–25). The expansion adds recognizable selections such as Wonderwall, Hotel California, Riptide, Fast Car, Faded, Levels, Autumn Leaves, Blue Bossa, Für Elise and Gymnopédie No. 1. Each song has a source; genre and practice level are curated browsing labels, not live popularity rankings or claims about a full score's difficulty.

The in-app **Chords & Lyrics** view now stores **22 accompaniment-study entries (including 12 original-demo entries) and 86 researched chord-reference entries**. Contemporary songs show source-reported chord facts directly, with source, date and limits. Guitar capo/tuning shapes and Piano concert-pitch equivalents are kept separate where needed. These are not complete or artist-certified transcriptions. Complex pieces remain explicitly partial; analysis services can differ by recording. See the [research ledger](docs/chord_research.md).

Songbook handles both Guitar and Piano chart lookups. Music Theory handles the authored lessons separately. A chord name identifies the same harmony on either instrument, while the playable voicing differs: guitar uses string shapes, tuning, capo and strumming or picking; piano uses hand placement and inversions. Each in-app chart now shows a clearly labeled instrument practice idea, not an asserted transcription of the artist's performance.

**Three Song Picks updates immediately with Favorite Genres**, before the final submit. One genre shows nine choices; multiple genres show their union. With no genre, the picker is disabled. Removing a genre clears only incompatible picks and explains the change; nickname/instrument and compatible picks remain. The final validation rejects out-of-genre IDs as well as duplicates. Draft changes do not replace a saved profile until **Save My Vibe**; Cancel keeps the existing profile.

**Try chords + lyrics demo** opens three public-domain Amazing Grace stanzas with Riffin's own aligned G-major accompaniment, without Gemini. Ode to Joy and Canon in D retain chord-only public-domain studies. Full contemporary lyrics and published arrangements still require rights-cleared material or a licensed provider; they are not scraped into the public repository. Publisher search links are secondary full-score options. See [catalog provenance](docs/catalog-attribution.md) and [artwork licenses](docs/asset-attribution.md). The griffin and random session animal avatars are downloaded artist-created icons under CC BY 3.0. Pastel blob/record art is original code-authored decoration with AI assistance, not generated mascot imagery.

Two additional lyric examples are stored: **Auld Lang Syne** (the verse and chorus in a 1918 songbook) and **Greensleeves** (first verse/refrain, spelling modernized from the historical text). Both use attributed public-domain lyrics and original simplified accompaniment. Every stored lyric entry includes `lyrics_license` and `lyrics_source_url`; seeding and runtime validation reject lyrics without these fields. Instrumental classical references have no invented lyrics. This revision does **not** provide complete contemporary chords-and-lyrics sheets for every song.

`db.py` opens SQLite with **`mode=ro`** and `PRAGMA query_only = ON`. Fixed SQL binds all title, artist, instrument, and chart-ID values as parameters. Reads close their connections. Case and repeated whitespace normalize before exact identity matching. Lookup returns `found`, `ambiguous`, `not_found`, or `error`; an error never counts as a confirmed miss. Try **Amazing Grace** with Any instrument to see Guitar/Piano choices, then choose Piano for a unique hit. A single song with two arrangements also asks which instrument you mean. Lookup alone creates no recent entry; **Open chords** does.

For You excludes the three picks and songs explicitly opened during this session. Local cards match at least one favorite genre, the selected instrument, and an at-or-below-skill arrangement. Each shared picked artist adds 4 points, each matching genre from picks/preferences adds 3, a matching instrument adds 5, and an appropriate level adds 2. Each criterion is counted once. Stable song IDs break ties; displayed reasons quote the actual metadata. The empty local feed points to Browse Songs or profile editing.

With a server Google key, **Beyond the Catalog** also asks the existing Google Search specialist for four candidate songs similar to the selected three, suited to the favorite genres, instrument and skill level. It displays distinct suggestions after excluding catalog songs. It searches once per session profile and only again when the profile changes or **Find More Songs** is pressed. The query includes public song names and playing preferences, never nickname, saves or chat history. Web cards appear only with Google grounding links, shown under **Grounded Web Sources**. They are suggestions outside the stored catalog, so they have no in-app chords or Save action; their displayed level is a learning goal, not a verified arrangement difficulty. If Search is unavailable or returns no usable sourced list, For You explains that state and keeps local picks usable.

The profile (including picks), favorites, recent views, active chart ID, transposed display copies, calculator results, lookup result and chat live in `st.session_state`. Riffin’ does not write these to SQLite, files or its lesson index; native theme preferences and connection state are managed by Streamlit. A normal rerun preserves this session's state. A fresh tab/session, page reload creating a new WebSocket session, or server restart starts setup again; there is no account or persistent recovery.

**Save** creates one favorite per song. Repeating it preserves that entry. **Open chords** refreshes one recent entry per song, with its last-opened arrangement and UTC timestamp. A rerun, lookup, save, or chart render does not refresh that timestamp. Picks shape discovery and remain separate from explicit saves. Editing a profile preserves saved songs, history, and chat. Each new visitor session receives fresh collections.

## Original demos and Music Math

Open **Browse Songs → Original genre demos** for a reusable example in any genre. The six songs are Basement Comet (Rock), Pocket-Sized Sunrise (Pop), Lanterns After Closing (Jazz), Maple Postcard (Indie / Folk), Neon Paper Planes (Electronic) and Courtyard Miniature (Classical). Each has eight new lyric lines, two sections and Guitar/Piano accompaniment. They are generated teaching material, clearly labeled **Original demo**, with CC0 dedication to the extent rights apply. [Full new texts and credits](docs/original-demos.md) are included in the documentation; no third-party lyrics or modern arrangements were copied.

In **Chords & Lyrics → Change key · transpose chords**, choose a target tonic and press **Transpose**. The catalog stays unchanged: the result is a session display copy that survives reruns/theme changes. Roots and slash basses shift together; chord qualities and lyric anchors remain intact. Known capo/D-standard offsets are converted to concert-pitch chord names in standard tuning without a capo. **Original key** restores the source display. Unsupported tunings fail clearly, and a partial source remains partial.

In **Chat → Music calculator**, transposition, rhythm timing and practice scenarios work locally without a key. With AI available, ask Music Math situational questions such as:

- “Transpose C Am F G/B from C major to D major.” → `D Bm G A/C#`.
- “How long are 16 bars of 4/4 at 120 BPM, with two subdivisions per beat?” → 32 seconds, 250 ms per subdivision.
- “For guitar practice I’m at 80 BPM and want 120. Assume 5 BPM gain per week, 20 minutes per session, 5 days a week and full attendance. Estimate weeks and hours.” → scenario: 8 weeks, 40 sessions, 13.3333 hours.

The fourth specialist uses typed Python functions rather than model arithmetic. Exact inputs, formulas and assumptions are displayed. The practice estimate is a simple linear scenario under a supplied learning-rate assumption, not a measured prediction or guarantee of skill. Major/minor changes require reharmonization, rather than transposition. Clear unrelated requests are redirected before a model/search call; the same guard applies in ADK callbacks. The lexical and semantic scope controls are not claimed to perfectly classify every paraphrase.

## Project structure and code walkthrough

```text
README.md                       # Startup, scope and walkthrough
app.py                          # Onboarding, views, explicit session actions
music_agent/
    agent.py                    # Four specialists, AgentTools, exported root_agent
    runner.py, turn.py           # Isolated ADK memory, event/source evidence
    tools.py                    # Typed catalog, retrieval and music calculation tools
    calculations.py             # Deterministic transposition, timing and estimates
    calculator_ui.py            # Local no-key controls and verified result display
    retrieval.py                # Gemini/Chroma lesson index and calibrated gate
    guardrails.py, security.py   # Input masking/injection checks and SQL AST gate
    observability.py             # Callback token counts and paid-tier cost estimate
    activity.py, chat_ui.py      # Live hierarchy, native chat and explicit actions
    session.py, presentation.py  # Session state and escaped visual rendering
    config.py, errors.py         # Server credentials and safe failure categories
    recommendations.py          # Deterministic metadata ranking
    discovery.py                # Grounded, session-cached web song suggestions
schema.sql, db.py                # Public schema and read-only parameterized access
data/seed_catalog.json           # 48 real works + six original demos, source of truth
data/catalog.sqlite             # Trackable public catalog: 108 instrument entries
knowledge/retrieval_checks.json  # Public gate-calibration examples (JSON)
assets/                         # Human-created mascot/avatars, local art and CSS
static/fonts/                   # Locally served Poppins faces and SIL OFL notice
scripts/                        # Seed, index, live integration and judged evaluation
tests/                          # Local tests plus four public golden judge cases
docs/                           # All other Markdown: specs, lessons, credits, reports
.streamlit/config.toml           # Shared typography and both native themes
requirements.txt                # Pinned dependencies
.gitignore                      # Credentials, environments and runtime exclusions
```

Code walkthrough:

1. `app.py:main()` initializes the current session and reads the catalog, then `render_profile_form()` validates and applies setup through `music_agent/session.py:update_profile()`.
2. `music_agent/recommendations.py:rank_songs()` supplies actual metadata reasons to `app.py:render_feed()` and `render_song()`. `music_agent/discovery.py` asks the isolated Search specialist for grounded songs outside the catalog when a key is present.
3. `app.py:handle_open()` validates a chart ID using `db.py:get_chart()`, then calls `music_agent/session.py:open_chart()`. `handle_save()` validates the public song and updates only session favorites.
4. `app.py:render_chart()` uses `music_agent/presentation.py:chart_section_html()` to escape strings and preserve chord/lyric spacing. Attribution comes from the database result.
5. `music_agent/chat_ui.py:render_chat()` submits explicit actions to `music_agent/runner.py:AgentChatSession.send()`. The adapter keeps separate ADK memory per visitor and handles final non-thought events.
6. `music_agent/agent.py:build_agents()` defines the specialists and root AgentTools. Its profile instruction appends only validated instrument/level.
7. `music_agent/tools.py:get_chord_chart()` delegates to the read-only service. `search_theory_notes()` calls `TheoryRetriever.search()`; open `load_lessons()`, `index()`, and `calibrate_gate()` in `retrieval.py` for ingestion and the miss/error boundary.
8. `guardrails.py:before_tool()` enforces Search consent and replaces its arguments. `before_model()` removes Search history; `after_model()` captures grounding. `runner.py:resolve_evidence()` uses tool provenance for display statuses.
9. `guardrails.py:before_agent()` blocks catalog deletion, `on_model_error()` redacts provider errors, and `after_tool()` records the compact trace. Runtime SQL protection remains `db.py:read_catalog()`.
10. `scripts/seed_catalog.py:seed_catalog()` is the only catalog writer. `schema.sql` contains no personalization tables. `music_agent/config.py:resolve_google_api_key()` keeps credentials on the server.

Importing the package or typed tool starts no UI and makes no network request:

```sh
.venv/bin/python -c 'from music_agent import root_agent; print(root_agent.name, [tool.name for tool in root_agent.tools])'
```

The graph imports without credentials or a network request. Standalone ADK Dev UI commands, lesson-index checks, and the provider smoke script are documented in [Agent integration](docs/agent-integration.md#commands). The Streamlit app needs no separate ADK server.

## Git and runtime files

`.gitignore` excludes `.venv/`, `.env` variants, `secrets.toml`, logs, caches, `.adk/`, build/test output, runtime/index directories, databases, and SQLite sidecars. It explicitly permits **`data/catalog.sqlite`**, the approved public seed catalog. Seed JSON, authored knowledge notes, original assets, and configuration remain eligible for tracking. Keep runtime databases and indexes under `runtime/` so they cannot overwrite the approved seed. Supplied reference screenshot filenames are excluded. Files are eligible for tracking but are not staged or committed by this work.

Ignore rules do not remove files already tracked or clean Git history. Review approved assets and publication history before release. No commits, pushes, or deployment are part of this phase.

## Current knowledge base

`docs/MUSIC_KNOWLEDGE_BASE.md` contains four authored lessons, indexed separately by stable ID and actual title:

1. **Major and minor triads:** root/third/fifth, 0–4–7 versus 0–3–7, C major/minor examples.
2. **I–IV–V progressions:** C–F–G–C and transposition to G–C–D–G.
3. **Keyboard inversions:** root position, first and second inversions, moving the lowest note up an octave.
4. **Practicing clean guitar chord changes:** checking muted strings and practicing slow, steady transitions.

The SQLite songbook is separate from these notes. Lyrics, every song's harmony, broad music history and current artist facts are not part of the four-lesson corpus. Retrieval uses the current submitted question; an agent cannot substitute an earlier chat topic to manufacture a citation. A working index with no relevant passage is a miss; unavailable embeddings, a failed gate or index errors remain failures, not coverage claims.

## Verification · 13 November 2026

The **76-test local suite** passed on Python **3.12.1** before this benchmark-report update. The new assistant-plus-judge cost test passed in the focused 7-test capstone-control run; rerun the full suite before submission:

The most recent saved [browser verification report](docs/interface-v8-verification.md) records Poppins loading, navigation, prompts and responsive Light/Dark checks. It predates the For You web cards and the colored Chat status row. The [Music Math report](docs/interface-v6-verification.md) retains demo, calculator and live routing evidence. Automated tests for the latest behavior are included below; a fresh browser pass is still pending.

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/index_knowledge.py
.venv/bin/python scripts/check_agent_integration.py
.venv/bin/python scripts/evaluate_agent.py --report docs/EVALUATION_BENCHMARK_REPORT.md
```

`scripts/evaluate_agent.py` uses the server-side key from ignored local Secrets or `GOOGLE_API_KEY`. It runs four public cases in `tests/golden_cases.json` through separate Riffin’ sessions and a separate structured Gemini judge. With `--report`, it writes a public Markdown report and a numeric JSON companion used by the **Evaluation Harness** card. It exits nonzero if a case fails or the provider/key is unavailable; no private prompts or key are printed. The 13 November live run passed **4/4** with **16 model calls**, **12,266 input tokens**, **4,958 output/thinking tokens**, and **$0.027792 estimated paid-tier model-generation cost**, including the judge. See the [dated benchmark report](docs/EVALUATION_BENCHMARK_REPORT.md) for the four case results and cost exclusions. A live provider attempt needs network access and may incur API charges.

No-key local startup was checked with an empty test-only Secrets file: Streamlit reported a local URL and its health endpoint returned HTTP **200**. The app flow is also covered by tests that remove both Secrets and environment keys. No credential value appears in this README.

The Chat usage line shows native input and output/thinking tokens. Its estimate uses Google's published [Gemini 3.6 Flash paid-tier rates](https://ai.google.dev/gemini-api/docs/pricing/) for the date of the call: through 2026, $0.75 per million uncached input tokens, $0.075 per million cached input tokens and $3.75 per million output/thinking tokens; rates change in 2027. The estimate excludes Search charges, cache storage, free-tier discounts and taxes, and is not a billing statement. Other models show counts with “rate unavailable.” Usage logs contain only fixed agent/model names and numeric totals. Masking is a conservative rule-based protection for common email, phone, card and key patterns; it is not a guarantee of complete PII detection.

Tests cover real catalog metadata, repeatable seeding, read-only parameterized SQL, source/lyrics boundaries, guitar-versus-piano transpositions, exact/ambiguous/missing lookups, HTML escaping, session activity, isolated ADK memory, production code with scripted model/vector fixtures, relevance errors, automatic fallback, no-grounding failure, local-only requests, partial-result preservation, current-question retrieval, private-data-free live callbacks, safe adapter reloads that preserve ADK memory, and rerun deduplication. Fixture responses are distinct from live provider evidence.

The saved browser checks covered all five views at **1440, 1024 and 390 px** in Light/Dark, with no app exception or horizontal page overflow at that time. They also checked session retention and a fresh second session. These are historical checks, not visual proof of the latest For You or Chat changes. See the [interface evidence](docs/interface-v8-verification.md).

Earlier live checks covered grounded Search, lesson retrieval and Gemini replies. Specialist names changed afterward from Guitar/Piano & Theory to Songbook/Music Theory. The renamed graph passes scripted routing checks; a full live routing replay remains pending. A fresh-session internal-miss → Search provider check also remains pending after a model error; scripted fallback tests pass. See [agent integration](docs/agent-integration.md) for the dated evidence and its limits.

**Scope revisions:** FR-07 now automatically follows a confirmed local miss with one isolated query-only Search, as explicitly requested in the latest handoff. Errors and ambiguity never trigger fallback, local-only overrides it, and unsourced web text is suppressed. FR-04/05 now distinguish researched harmonic references from complete lyric charts. FR-11 adds the new pastel/organic design references, session animal avatars, a header Connection popover, and a draggable/collapsible callback-driven hierarchy view. These supersede earlier opt-in/redirect-only wording.

Hosted deployment and Search, clean-checkout installation, publication/history audit, presentation rehearsal and rights-cleared complete contemporary lyric charts remain pending. No commits, pushes or deployment were performed; you control them.
