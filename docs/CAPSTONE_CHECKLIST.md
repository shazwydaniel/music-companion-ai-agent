# Virtual Music Companion · Capstone checklist

## Current enterprise-analyst rubric cross-check · 13 November 2026

- [x] **Pillar 1 — Multi-agent/tools.** Riffin’ is the music-domain option: one ADK coordinator delegates through `AgentTool` to Songbook, Music Theory, Web Search and Music Math. Local routing tests and the 13 November live judge run exercise the current graph.
- [ ] **Pillar 2 — Enterprise integration as worded.** The app queries the seeded SQLite catalog and authored lesson files, but MCP discovery primitives are deliberately omitted at the user's request. The non-MCP source integration is verified; strict rubric completion is not claimed.
- [x] **Pillar 3 — Two-tier guardrails.** Tested prompt-injection refusal and common PII masking before ADK; catalog SELECTs pass `is_sql_mutation` AST verification and read-only SQLite URI/query-only connections. The matcher is rule-based and cannot guarantee all PII or injection variants.
- [x] **Pillar 4 — Observability/cost.** `after_model_callback` captures native usage, logs numeric token counts and dated paid-tier Gemini 3.6 Flash USD estimates, and displays the per-turn summary. Search/billing extras are excluded from the estimate.
- [x] **Pillar 5 — Automated LLM judge.** `scripts/evaluate_agent.py` evaluated four public golden cases with separate Gemini judge calls; 4/4 passed in a live local run. The [submission report](EVALUATION_BENCHMARK_REPORT.md) records 16 assistant-plus-judge model calls and $0.027792 estimated paid-tier generation cost. A missing key/provider causes a nonzero pending result.
- [ ] **Pillar 6 — Hosted deployment.** `app.py`, pinned `requirements.txt`, server-side `st.secrets` resolution, and README startup/deployment instructions exist. GitHub publication and Streamlit Cloud deployment are reserved for the user; hosted acceptance remains pending.

Evidence: `.venv/bin/python -m unittest discover -s tests -q` and `.venv/bin/python scripts/evaluate_agent.py --report docs/EVALUATION_BENCHMARK_REPORT.md`; see the benchmark report and README verification section. No MCP, commit, push or hosted deployment was performed in this work.

Use alongside `docs/MUSIC_COMPANION_SPEC.md`, `docs/UI_STYLE_GUIDE.md`, and the starter `MUSIC_KNOWLEDGE_BASE.md`. Work in order, starting with a runnable skeleton and the chart flow. Check an item after you observe its acceptance result. Record the evidence or remaining blocker in the README. MVP items are the release target. The coursework showcase below is based on the supplied labs and can be updated when an official rubric is available.

**UI refinement revision · 13 November 2026:** 66 local tests pass. For You is the initial view after setup; icon navigation distinguishes Browse Songs, Saved & Recent, Chords & Lyrics and the accented Chat action. Poppins is bundled locally under SIL OFL. Label/value tags use colons, quality metadata is grouped, Open Chords leads song actions and jumps to the sheet, Back to Chat is anchored, and prompt chips fill editable text without submitting. Real-browser checks cover five views in both themes at 1440/1024/390 px, keyboard interaction, repeated sheet jumps, a short-phone expanded hierarchy and session retention/isolation. See [current verification](interface-v8-verification.md). Hosted/release and pending provider requirements below remain unchecked.

**Music Math/original-demo revision · 13 November 2026:** 65 local tests pass. Six generated genre demos add twelve reusable lyric/accompaniment entries; the catalog totals 54 songs / 108 instrument entries. The fourth AgentTool specialist performs deterministic transposition, timing and explicit-assumption practice scenarios. Live Gemini checks returned the expected transposition and 8-week/40-session/13.3333-hour practice scenario. Browser checks captured actual Root/Music Math activity, all six original demos, local calculators, transposition/theme retention, padded five-node hierarchy and unrelated refusal. Markdown is consolidated in `docs/` with the lesson path and local links audited. See `interface-v6-verification.md`. Earlier counts below are historical; hosted/release requirements remain pending.

**Genre catalog revision · 13 November 2026:** 50 local tests pass. The public seed now has 48 songs (eight per genre), 96 instrument entries, 86 short researched harmonic references and ten public-domain accompaniment studies. Three works have attributed public-domain lyric editions; complete contemporary lyrics/arrangements remain pending rights-cleared material. Native genre changes refresh the picker before submit, using a union for multiple genres and preserving compatible draft picks. Tests verify all six filters, the union, removal/clearing, validation and cancel behavior. Welcome benefits use three distinct pastel cards in one row, with a serif heading and italic violet supporting line. Current evidence is in `docs/interface-v5-verification.md`; earlier counts below are historical.

**Current revision · 13 November 2026:** 46 local tests pass. Songbook now contains six public-domain accompaniment studies and 34 researched harmonic references, with sources, scope notes and guitar/Piano transposition distinctions. Three Amazing Grace verses demonstrate aligned chords and public-domain lyrics. New user instructions make local misses trigger one automatic query-only Web Search; errors and ambiguity remain distinct, local-only prevents Search, and reruns do not resubmit. Earlier real browser callbacks showed Root → Guitar → Search on the exact boygenius miss, and Root → Piano & Theory on supported/local-only requests, before those specialists were renamed Songbook and Music Theory. The floating hierarchy, session animal avatars, header Connection control, pastel art, and selected-genre border ornaments are implemented. Both themes at 1440/1024/390 px passed state/isolation checks. See `docs/interface-v3-verification.md`, `README.md`, and the chord research ledger. Hosted/publication checks and complete rights-cleared contemporary lyric charts remain pending. Earlier opt-in/redirect-only descriptions are superseded by this explicit user revision.

## 1. Assignment deliverables

- [x] **Working AI web app.** The Streamlit interface handles an actual user question through Google ADK and Gemini.
- [ ] **Streamlit Community Cloud deployment.** A clean browser session opens the deployed URL and receives a reply. Record the URL and test date.
- [ ] **Presentation.** Prepare the short demo sequence below and rehearse it on the deployed URL.
- [ ] **Repository handoff.** Include `app.py`, the importable agent package, the seeded SQLite catalog, `schema.sql`, the internal music notes, seed and index setup, `.streamlit/config.toml`, `requirements.txt`, `.gitignore`, approved assets, and a `README.md` with a code walkthrough.

## 2. Functional requirements · MVP

- [x] **FR-01 · First-launch personalization.** Open a fresh session and submit nickname, instrument, level, and genres. Verify customization and the absence of credential fields.
- [x] **FR-02 · Three song picks.** Save three distinct songs from the selected genres. Verify all six filters, multiple-genre union, compatible-pick preservation and invalid submission. Edit the selection and check that the feed refreshes.
- [x] **FR-03 · For You.** Check that picks are excluded and that reasons match catalog metadata. Test the empty state.
- [x] **FR-04 · Chord lookup.** Test a known title and artist, a duplicate title, and an unknown song. Verify each state is distinct.
- [x] **FR-05 · Songbook rendering.** Open a chart with chord and lyric lines, plus another without lyrics. Verify alignment and attribution.
- [x] **FR-06 · History and favorites.** Open a chart and save a song. Repeat both actions and verify one recent entry and one favorite in the current session.
- [ ] **FR-07 · Google Search.** Trigger an internal-note miss and a catalog miss. Verify each automatically runs one query-only Web Search, with no repeat on rerun; verify local-only overrides it and lookup/retrieval errors do not trigger Search. Verify real grounding links on Cloud and test the unavailable or no-source state.
- [ ] **FR-08 · Internal music knowledge base.** Commit the authored starter notes under `knowledge/` and index each lesson by stable ID. Check a supported answer against its cited passage. Verify a miss or index error gets the correct distinct status.
- [ ] **FR-09 · Dynamic routing.** Observe Songbook, Music Theory, and Search in separate traces. Try one differently phrased prompt per route and one ambiguous question.
- [x] **FR-10 · Guardrails.** Ask the assistant to delete the catalog. Verify the refusal, unchanged catalog, and successful subsequent lookup.
- [x] **FR-11 · Themes and genre UI.** Verify the light and dark themes follow the style guide. Choose Rock and verify its flame border sticker in both themes. Switch themes during a session and verify profile, chart, and chat state remain intact.
- [x] **FR-18 · Session-only personalization.** Rerun the app during a session and verify preferences and history still appear. Open a fresh session and verify onboarding returns with no previous profile, picks, favorites, history, or chat. Confirm personal data never reaches a persistence layer.

## 3. Non-functional requirements

- [ ] **NFR-01 · Public-repo safety and permissions.** Audit files and Git history planned for publication. Confirm credentials, runtime user data, and logs are absent, and confirm read-only parameterized catalog queries.
- [x] **NFR-02 · Isolation and privacy.** Open two independent browser sessions. Verify profiles, favorites, history, and chat are scoped correctly. Inspect the trace for sensitive fields.
- [x] **NFR-03 · Resilience.** Simulate unavailable AI. Catalog browsing and For You still work. Chat shows a clear error, and reruns do not resend the request.
- [x] **NFR-04 · Provenance.** Confirm catalog, theory, and web source labels correspond to tool output. Check invalid IDs and missing source metadata.
- [x] **NFR-05 · Usability.** Test both themes at desktop and narrow widths, with keyboard navigation and visible focus. Check text over art, sticker placement, and chart overflow.
- [ ] **NFR-06 · Reproducibility.** From a clean checkout, install the pinned dependencies, start Streamlit, and import the ADK package. Verify the shell and catalog start without a key. Repeat the main flow on the hosted URL after Secrets are configured.
- [x] **NFR-07 · Observability.** Capture a trace with specialist, tool, outcome, and duration for each principal route.
- [x] **NFR-08 · State integrity.** Repeat saves, chart opens, and seed initialization. Verify deduplication and document the session lifecycle.
- [ ] **NFR-09 · Presentation-ready source.** Review every logical section for a meaningful comment heading. Verify typed tools have useful docstrings and the README points to the onboarding, coordinator, retrieval, search fallback, and guardrail code.

## 4. Academic evidence for the presentation

- [ ] **Lab 1 · Agent and sessions.** Point to the configured model, instructions, ADK `Runner`, and a multi-turn conversation.
- [ ] **Lab 2 · Tools and callbacks.** Show a typed tool signature, validated arguments, the read-only query, and the guardrail outcome.
- [ ] **Lab 3 · RAG.** Open an original internal note from the repo, show the answer citing it, and explain ingestion, retrieval, and relevance gating. Show the **Search the web** option when the notes have no relevant answer.
- [ ] **Lab 5 · Dynamic routing.** Explain how the root coordinator reads specialist descriptions and invokes `AgentTool`. Show a route selected at runtime and a Google Search tool call.
- [ ] **Bank Virtual Analyst · Streamlit.** Show the hosted URL, explain how local and hosted configuration differ, and describe why app actions own writes.
- [ ] **Lab 4 · Fixed workflow, if implemented.** Show two stages and the `output_key` handoff.
- [ ] **Lab 4b and Lab 6 · Design discussion.** Explain where typed branching, human approval, or a separate MCP tool server would be appropriate. Identify which ideas are design influences and which are implemented.

## 5. Stretch features

- [ ] **FR-12 · Practice plan.** Confirm a verified exercise flows through both stages.
- [ ] **FR-13 · Guitar tuner.** Test the external tuner link and the guidance it accompanies.
- [ ] **FR-14 · Vocal range.** Test the range-check link and one user-supplied range.
- [ ] **FR-15 · Piano score.** Open an attributed beginner score.
- [ ] **FR-16 · Shopping and classes.** Test one budget-based recommendation and a branch lookup. Confirm public fields and source labels.
- [ ] **FR-17 · Badges.** Verify a badge is awarded once from its defined event.
- [ ] **FR-19 · Confirmed session update.** Verify cancellation and one deduplicated favorite update after confirmation.

## 6. Public release and Streamlit deployment

- [ ] Confirm public assets have redistribution approval and required notices. Keep the supplied design references out of the release files.
- [ ] Confirm `.env`, `.streamlit/secrets.toml`, SQLite sidecars, caches, and logs are ignored. Verify the approved seed catalog and authored knowledge base are tracked.
- [ ] Check `README.md` documents the tested Python version, clean setup, `streamlit run app.py`, known limits, and deployment steps. Confirm no assets depend on absolute local paths.
- [ ] In Community Cloud, choose the public GitHub repository, branch, and `app.py`. In **Advanced settings → Secrets**, paste `GOOGLE_API_KEY = ""` and fill the quoted value with the supplied key before deploying.
- [ ] From the hosted URL, verify an ADK reply and a grounded Google Search result separately. Verify both themes, genre stickers, and seeded chart artwork.

## 7. Rehearsal

- [ ] Onboard a beginner guitarist and select three songs.
- [ ] Open a recommended chart and show Recently Opened.
- [ ] Ask a theory question and open the cited internal note in the repo.
- [ ] Ask a music question outside the notes, observe the automatic Web Search, and show the returned source. Then demonstrate the guardrail.
- [ ] Keep screenshots of the successful hosted flow and tool traces for the presentation. Label any provider outage or unverified scenario accurately.
