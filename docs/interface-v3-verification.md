# Riffin interface and routing verification · 13 November 2026

The current preview is **http://localhost:8504**. Python **3.12.1**; dependencies remain pinned in `requirements.txt`. This revision follows the latest seven-part user request. Earlier opt-in Search and redirect-only songbook descriptions are historical.

## Implemented behavior

1. Each fresh session chooses a cat, rabbit or fox silhouette once. Normal reruns, profile edits and theme changes retain it. User bubbles align right with a fixed 36 px animal avatar; Riffin stays left. Artist attribution is in `docs/asset-attribution.md` and the Connection popover.
2. A confirmed catalog/knowledge miss automatically makes one query-only Google Search attempt in an isolated ADK session. Partial local results survive the fallback. Ambiguous titles, retrieval failures and provider errors remain distinct. “Local only” prevents Search. Unsupported web prose without returned grounding sources is suppressed. Reruns do not resubmit.
3. Navigation says **Songbook**, actions say **Open chords** / **Find chords**, and the complete lyric demonstration says **Chords & lyrics**. Technical database names remain compatible.
4. **Connection** lives in the sticky header; on phones its Wi-Fi icon retains the accessible Connection label. It reports key presence without claiming provider availability. Credits and the four-lesson overview are inside it.
5. The 20-song, 40-entry catalog now contains **34 researched harmonic references and six public-domain accompaniment studies**. Sources, research dates, scope limits and tuning/capo distinctions are stored. Amazing Grace has three public-domain verses with Riffin's authored accompaniment and aligned monospace chord/lyric lines. Full contemporary lyrics and complete published arrangements were not copied. Those require rights-cleared material and remain pending. See `docs/chord_research.md` and `docs/catalog-attribution.md`.
6. The floating hierarchy highlights actual before-agent/model/tool callbacks for Riffin, Guitar, Piano & Theory and Web Search. It opens once on real activity, then supports native collapse and pointer dragging. It shows no prompts, arguments, keys, model thoughts or personal profile data. The existing compact trace remains available.
7. Original local SVG cover art uses pastel fields, organic shapes and record motifs. Fixed genre colors adorn the viewport edges. Attached reference photographs remain outside the repository. The mascot and animal silhouettes remain credited human-created assets.

## Knowledge base

`docs/MUSIC_KNOWLEDGE_BASE.md` contains four authored lessons: **Major and minor triads**, **I–IV–V progressions**, **Keyboard inversions**, and **Practicing clean guitar chord changes**. The SQLite catalog is a separate store. Current music facts and broad music history are outside the lesson corpus.

Retrieval binds to the current submitted question. A live multi-turn check exposed an agent substituting an earlier triad topic; the typed retrieval tool now prevents that substitution, with a regression test. Failed retrieval is never relabeled a confirmed miss.

## Evidence

- **46 local tests passed**, including no-key AppTest flows, repeatable seeding, read-only parameterized SQL, provenance/lyric boundaries, guitar/Piano transposition, ambiguity, repeated opens/saves, isolated session memory, automatic fallback, no grounding, local-only, partial results, current-question binding, event redaction and safe adapter reloads. Scripted provider/vector fixtures are distinct from live Google checks.
- The real question “give me the chords of Cool About It by boygenius” produced a catalog miss and automatically ran grounded Search. The browser captured actual active Riffin, Guitar and Google Search nodes.
- A real C-major-triad question activated Piano & Theory and returned the actual internal lesson title. A real unsupported synthesizer-history question with “Local only” returned a miss and did not invoke Search.
- A further fresh live `internal_miss` provider probe returned a root model error before a confirmed miss. That separate fresh-session knowledge-miss → Search provider check remains **pending**. A later browser continuation did run grounded Search for the same topic, but conversational history allowed the coordinator to skip a new internal lookup; it is not evidence for a fresh internal-miss chain.
- Both Light and Dark at **1440, 1024 and 390 px** passed profile/chat retention, avatar alignment, source/status legibility, cards, stored references and the lyric demo. A second browser context remained fresh. Catalog bytes were unchanged by user interactions.
- Final geometry checks passed all six theme/width combinations: no horizontal overflow or Streamlit exceptions; collapsed panel width **190 px**; at phone/tablet sizes its bottom was **856 px**, above the composer at **886 px** in a 1000 px viewport. Phone header height was **82.2 px**. Dragging, manual collapse and header Connection popover passed. These measurements describe the tested viewport, not all possible browser sizes.

Local evidence is outside Git at `/private/tmp/riffin-no-key/v3/`: `evidence.json`, `live-evidence.json`, `layout-audit.json`, `layout-audit.log`, `real-internal-fallback.json` and screenshots. The final mobile screenshots are `final-chat-Light-390.png` and `final-chat-Dark-390.png`; live route captures include `catalog-auto-search-google_search_specialist.png`.

## Commands

```sh
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m streamlit run app.py --server.headless=true --server.address=127.0.0.1 --server.port=8504
.venv/bin/python scripts/check_agent_integration.py --check internal_miss
```

The last command records the pending provider check above. Browser checks used the local headless Chrome CDP connection and temporary scripts `v3_browser.py` and `v3_layout_audit.py` under `/private/tmp/riffin-no-key/`. The no-key AppTest explicitly removes both environment and Streamlit Secrets keys. The earlier independent no-key server command is documented in README.

`git diff --check` passed. Ignore checks confirmed `.venv`, `.env`, `.streamlit/secrets.toml` and runtime logs are excluded; `data/catalog.sqlite` remains eligible for tracking. No commits, pushes or deployment were performed.

## Files changed in this revision

- UI: `app.py`, `music_agent/chat_ui.py`, `music_agent/session.py`, `music_agent/presentation.py`, `assets/styles.css`, `assets/interface_controls.html`, `assets/art/*.svg`, `assets/avatars/*.png`.
- Agent integration: `music_agent/activity.py`, `music_agent/agent.py`, `music_agent/runner.py`, `music_agent/guardrails.py`, `music_agent/tools.py`, `music_agent/turn.py`.
- Catalog: `db.py`, `schema.sql`, `scripts/seed_catalog.py`, `data/seed_catalog.json`, `data/catalog.sqlite`, `docs/chord_research.md`, `docs/catalog-attribution.md`.
- Verification/documentation: relevant tests, README, this report, `docs/agent-integration.md`, `docs/CAPSTONE_CHECKLIST.md`, `docs/MUSIC_COMPANION_SPEC.md`, `docs/UI_STYLE_GUIDE.md`, `docs/asset-attribution.md`, `.gitignore`.

Hosted behavior, clean-checkout installation and complete rights-cleared contemporary lyric charts remain pending.
