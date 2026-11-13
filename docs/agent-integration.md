# Riffin agent integration

This phase follows the supplied Lab 5 notebook's **specialist Agent → AgentTool → dynamic coordinator → Runner** pattern. The course notebook stays outside the public repository. Colab installers, process-killing commands and tunnels are not part of Riffin’. ADK session creation is awaited for the pinned SDK.

## Latest extension · Music Math and scope

The root now delegates through **four AgentTools**: Songbook, Music Theory, Google Search and **Music Math**. Music Math owns `transpose_chords`, `transpose_song`, `calculate_rhythm` and `estimate_practice`. Typed tools call deterministic bounded Python, retain exact inputs/formulas/assumptions in invocation evidence, and never execute arbitrary expressions or SQL. Calculated outputs replace unsupported model arithmetic in the display result. A scenario estimate is not a measured skill prediction; missing weekly-gain assumptions must be requested rather than invented.

`transpose_song` reads one validated instrument entry, shifts chord roots/slash basses, preserves chord quality and lyric anchors, and returns a concert-pitch display copy. Known capo and D-standard offsets are accounted for; unsupported tunings fail clearly. Major/minor changes require reharmonization and are rejected. A partial source remains partial. Local Songbook and Chat calculator controls use the same functions without Gemini and label those events as local tool execution.

The session runner rejects clear unrelated prompts before credentials or provider calls. The same scope gate is installed in ADK before-agent/tool callbacks, alongside the existing destructive-write guard, with a semantic music-only instruction on the coordinator. Artist names/catalog titles and music follow-ups remain usable. The lexical boundary is tested on representative cases; it is not a claim of perfect classification of every paraphrase. Unrelated refusals cannot trigger Web Search.

The hierarchy includes Music Math and shows either actual ADK callbacks or explicitly named `local_*` calculation events. It has no fabricated progress. All Markdown is under `docs/` except the root README; `NOTES_PATH` now points to `docs/MUSIC_KNOWLEDGE_BASE.md`, while public JSON calibration checks remain under `knowledge/`.

## Agents and model

`music_agent.agent.root_agent` (also exported from `music_agent`) exposes four AgentTools:

| Specialist | Registered tool | Responsibility |
|---|---|---|
| `songbook` | `get_chord_chart(title, artist, instrument)` | Stored Guitar and Piano charts, arrangement ambiguity, and general instrument playing ideas through the read-only SQLite service. |
| `music_theory` | `search_theory_notes(query)` | Authored internal music learning and practice passages, with actual note titles. |
| `google_search_specialist` | ADK `google_search` | Automatic miss fallback and explicitly requested public music lookups with actual grounding metadata. |
| `music_math` | `transpose_chords`, `transpose_song`, `calculate_rhythm`, `estimate_practice` | Deterministic transposition, tempo/beat timing and assumption-based practice scenarios. |

`RIFFIN_MODEL` defaults to **`gemini-3.6-flash`**, whose [documented capabilities include function calling and Google Search grounding](https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash). This replaces the notebook's mixed model strings with a documented Search-compatible model. Any server environment override must also support Google Search. Local key access succeeded on 13 November 2026 for Gemini, embeddings and Google Search. Quota availability can change.

Root descriptions and instructions govern runtime selection; Python does not preselect Songbook versus Music Theory. Root instructions receive only validated instrument and skill level. Every visitor owns a separate `InMemorySessionService` and opaque random user/session IDs. The Streamlit session retains that adapter across reruns. Agents have no save, open, delete, arbitrary SQL, or file-write tool.

## Lesson index and relevance gate

`load_lessons()` splits `docs/MUSIC_KNOWLEDGE_BASE.md` by level-two heading. Each of its four lessons retains its stated source ID, actual title, topic, instruments, and body. It rejects missing/duplicate metadata rather than silently indexing an incomplete corpus.

Production embeddings use **`gemini-embedding-001`**, 768 dimensions, normalized vectors, paired `RETRIEVAL_DOCUMENT` / `RETRIEVAL_QUERY` tasks, and a Chroma **cosine** index. See [Gemini embedding tasks](https://ai.google.dev/gemini-api/docs/embeddings) and [Chroma distance configuration](https://docs.trychroma.com/docs/collections/configure). Chroma receives explicit vectors and `embedding_function=None`, so it downloads no default model.

The first theory request builds the public in-memory index. Its cache key includes the corpus/metadata, public calibration examples, model, dimensions, and metric. The cache contains lesson documents, vectors, the gate, and source metadata only. Query vectors are transient; prompts, credentials, user IDs, and conversations are never inserted. A server restart rebuilds the cache; no disk index is needed for startup.

`knowledge/retrieval_checks.json` contains four supported queries with expected lesson IDs and four unsupported queries. Calibration requires the expected top source for every supported example and a score gap exceeding 0.02 between the weakest positive and strongest negative. Their midpoint becomes the threshold. Failure is `error/calibration_error`, never a knowledge miss. Only a working calibrated query with no passage above threshold returns `no_results`.

The production Gemini embedding index built and passed its calibration checks locally on 13 November 2026. This is a small authored-corpus gate, not a broad semantic-accuracy benchmark. Tests use explicitly named fixture vectors against real Chroma; their 0.5 gate does not certify the production embedding space. A successful answer shows **Internal notes** and the actual title, such as **Major and minor triads**.

## Search authorization and provenance

Following the 13 November user revision, an internal `no_results` or catalog `not_found` triggers **one automatic Web Search** for the current question. The Runner uses the same Search specialist in a fresh, empty session; it does not replay the profile or transcript. Errors and ambiguity do not trigger Search. A partial local result keeps its actual sources when Web Search fills the gap. Explicit “local only” / “do not search” requests override the default. A public-fact Search proposal can also execute automatically without being labelled a confirmed notes miss. Ordinary reruns never repeat a request.

An explicit web request can still traverse the root's Search AgentTool. Automatic fallback runs the specialist directly from the adapter after the local result, with the same grounding/error rules. Typed retrieval binds to the current submitted question, so an LLM cannot cite an earlier lesson by substituting a previous query.

The before-tool callback ignores any model-supplied Search request and replaces it with the approved cleaned query. The specialist's before-model callback restricts model contents to that one query. No profile attributes, earlier chat, or parent transcript are sent to Search. Search has a fixed instruction and its native Google Search tool only.

The specialist's after-model callback captures grounding even inside a nested AgentTool. `propagate_grounding_metadata=True` also preserves metadata through ADK's [AgentTool grounding option](https://google.github.io/adk-docs/tools-custom/function-tools/). The app displays bounded HTTP(S) links from returned grounding chunks under **Web results**. Model-written URLs are removed from the web answer. No usable links means `no_sources`; an unsourced answer is suppressed.

## Failures, guardrail, and trace

The local submission check and ADK before-agent callback refuse destructive catalog requests before any model request. Tool callbacks enforce the per-agent registry. Catalog reads still use `mode=ro`, `query_only`, and fixed parameterized SQL. Only explicit native UI actions update favorites/recent views in the current session.

The trace includes **agent, tool, controlled outcome, elapsed_ms** only, bounded to 40 rows. It excludes arguments, prompts, raw tool results, keys, opaque IDs, and model thoughts. Provider-error callbacks consume exceptions before framework error logging and expose safe credentials/quota/timeout/error categories. Google HTTP requests use one attempt, an explicit turn has a 45-second timeout, and duplicate typed-tool calls are cached within that turn. Ordinary reruns resend nothing.

## Commands

From the repository root:

```sh
# Inspect the four lesson IDs/titles without a key.
.venv/bin/python scripts/index_knowledge.py

# With a server key: explicitly build and calibrate a process-local index.
.venv/bin/python scripts/index_knowledge.py --build

# Separate conditional live checks: Gemini chart reply, grounded Search, theory.
.venv/bin/python scripts/check_agent_integration.py

# Actual ADK Runner/AgentTools with controlled model/vector fixtures; no network.
.venv/bin/python -m unittest discover -s tests -v

# Optional local Dev UI, using the environment key and in-memory storage.
.venv/bin/adk web --no_use_local_storage --host 127.0.0.1 .
```

Select `music_agent` in the optional Dev UI. Streamlit calls the package directly and needs no ADK server or tunnel. Standalone ADK uses the environment key; the Streamlit Secrets resolver applies to Streamlit. `--build` tests the CLI process's public index; the app builds its own cache on first theory use. When the key is absent, the provider commands report pending rather than success.

## Integration evidence boundary

Local tests cover actual ADK specialist/tool execution with scripted model choices, real Chroma with fixture vectors, note hits/misses, automatic fallback, local-only overrides and query isolation, source extraction/no-source handling, credential/quota/timeout categories, separate ADK memory, UI citations and actions, guardrails, and reruns. The destructive prompt leaves the catalog byte-for-byte unchanged and a subsequent chart lookup succeeds.

Separate live checks on 13 November 2026 observed Gemini chart routing, internal lesson retrieval with calibrated production embeddings, direct grounded Search, root Search AgentTool grounding, and the Spotify Search proposal. The original-question → affirmative → Search browser check and theme measurements are documented in `interface-verification.md`. Local scripted tests are distinct from this provider evidence. Hosted behavior and broad routing/semantic quality evaluation remain pending. See `README.md` for commands and evidence locations.


## Live hierarchy

`TurnEvidence.announce()` publishes only agent/tool/controlled status to the current session's `activity.py` observer. Before-agent/model/tool callbacks highlight real work; after callbacks update outcomes. The floating native disclosure auto-opens once on actual activity in a new turn and can be collapsed or dragged. There are no simulated timers, model thoughts, arguments or prompts in it. Earlier browser checks observed Root/Guitar/Search and Root/Piano & Theory before those specialists were renamed. The renamed graph passes local scripted routing checks; live provider routing remains to be repeated. See `interface-v3-verification.md`.
