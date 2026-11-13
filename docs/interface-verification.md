# Riffin interface verification · 13 November 2026

## What changed

Chat opens immediately after a valid profile. Its first navigation pill is highlighted, and the empty state introduces the artist-created griffin with three explicit prompt starters. User bubbles align right with the avatar on the right; Riffin replies align left with a warm mascot avatar. Source sections, status text, Search actions and compact route disclosures remain native Streamlit controls.

A compact Riffin/tagline header stays at the top while the main content scrolls. The sticky position belongs to the native wrapper around the app-owned header; styling only its inner container would constrain it to its own height. A fixed genre mapping selects a decorative header/featured-card sticker. The profile's primary genre drives the sticker, with no user-provided asset paths. Light and dark use the documented warm surfaces and focus/link colors. Streamlit's native caption opacity is overridden within this app so the specified secondary text colors are displayed at full opacity.

For You has one horizontal featured card on desktop and compact image-led cards below it; the feature stacks on phones. Card art is abstract genre decoration, not an artist's album cover. Catalog browsing supports a genre filter, exact title/artist/instrument lookup, explicit Open chart and Save controls, and distinct miss/error states. Inline studies retain aligned chords/lyrics and a contained horizontal scroll region. External songs open an explicit publisher-resource panel instead of fabricated chart content.

## Commands and environment

Python **3.12.1**, Streamlit **1.67.0**, the repository's pinned ADK/SDK/Chroma dependencies, and headless Chrome **157.0.8103.52** on macOS.

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_agent_integration.py
.venv/bin/python scripts/check_agent_integration.py --check internal_miss
```

**39 tests pass.** The integration CLI performs real calls only when a server key exists, otherwise reports pending. Fixture-model/vector tests are explicitly separate from real provider evidence.

A separate no-key browser server used:

```sh
env -u GOOGLE_API_KEY .venv/bin/python -m streamlit run app.py --server.headless=true --server.address=127.0.0.1 --server.port=8502 --secrets.files=/private/tmp/riffin-no-key/secrets.toml
```

The test-only Secrets file is empty of credentials. The configured live test server used:

```sh
.venv/bin/python -m streamlit run app.py --server.headless=true --server.address=127.0.0.1 --server.port=8503
```

The user's pre-existing server on 8501 was left running. It had an older imported presentation module cached; restart it once before reviewing the updated interface there. Server restarts start new sessions; ordinary reruns/theme changes preserve current-session data.

## Observed browser behavior

| Check | Evidence |
|---|---|
| Fresh onboarding | Set up profile first; nickname, instrument, skill, genres and exactly three distinct real song picks; no account/key fields. Light/Dark captures at 1280 and 390 px. |
| Main chat and responsive views | Light/Dark at 1280, 768 and 390 px. Right bubble starts farther right than Riffin's bubble; its native message flex direction is row-reverse. No app exceptions or horizontal page overflow. |
| Sticky brand | After main-content scrolling, header top remains **44 px** in both themes and widths. Menu remains accessible. |
| Preserved state | Profile still shown; saved Canon in D remains the active chart; blocked chat reply remains after navigating and switching themes. Profile editing also preserves navigation (regression test). |
| Explicit activity | Repeat Save gives one library favorite; one recent song remains after opens; rerenders do not refresh timestamps. Catalog SHA-256 unchanged after browser flow. |
| Independent sessions | Two browser contexts: the second starts setup, has a different nickname, and has empty saved/recent/chat collections. No first-session content appears. |
| Keyboard | Radio arrow navigation; Enter activates Open chart and Save. The chart region receives visible focus. At 390 px its content width is **642 px**, client width **356 px**, and horizontal scroll reaches **286 px** without page overflow. |
| Chart key handling | A fixed local script owns Left/Right and Home/End only while a chart region is focused; no profile/storage/network access. Catalog/model/user HTML is still escaped and rendered without JavaScript enabled. |
| External song | BIRDS OF A FEATHER opens the publisher-resource panel in both themes/widths. Metadata source and Musicnotes search link are distinct. No invented key/capo, copied lyrics or fake inline chart. |
| No key | Onboarding, discovery, catalog, charts, activity and local destructive guardrail work. Chat shows AI unavailable; reruns never resend. |

## Live provider and Search evidence

The original question **“who is the number 1 artist on spotify”** returned a public-fact Search proposal with an actionable **Search the web** button. It was not labelled a confirmed knowledge-base miss. Typing **“yes please”** invoked the isolated Search specialist with the original question, then displayed grounded links returned by Google. A subsequent C-major-triad question displayed **Major and minor triads** and **Keyboard inversions** under Internal notes. These actual results stayed visible across light/dark changes at 1280/390 px.

Separate CLI calls observed:

- Root → Guitar → parameterized catalog lookup, returning two actual instrument choices.
- Root → Piano & Theory → production Gemini embeddings / calibrated Chroma retrieval, with real lesson sources.
- A music-history query routed to internal notes and returned a confirmed `no_results` with a Search offer.
- Direct Google Search and root → Search AgentTool → `google_search`, each with actual grounding links.
- Original Spotify public-fact question → `search_confirmation`, without a Search call until approval.

The browser's Search source links were actual grounding links (including spotifystats.com), not URLs invented by the model. This verifies the Search handoff and provenance; it is not an independent audit of any site's live popularity statistics. Source counts vary between provider runs.

## Text contrast

Native source controls and factual status labels were inspected in both themes. The corrected caption containers use opacity **1**, rather than Streamlit's default 0.6. Key observed color pairs and WCAG relative-luminance ratios:

| Element | Light | Dark |
|---|---|---|
| Status / source metadata on assistant surface | `#57534F` / `#FFFDF8`: 7.50:1 | `#BDB5AB` / `#1F1D1B`: 8.29:1 |
| Secondary text on user bubble | `#57534F` / `#F4DCCF`: 5.80:1 | `#BDB5AB` / `#432C23`: 6.38:1 |
| Grounded link buttons (observed backgrounds) | `#8E321D` / `#FBFBF9`: 7.72:1 | `#FF9A78` / `#1B1A18`: 8.40:1 |

The guide's focus colors are visible on the chart in each theme. Decorative stickers carry no source/status information and do not intercept input.

## Artifacts and limits

Local artifacts are deliberately outside Git:

- `/private/tmp/riffin-no-key/phase4/evidence.json` and view screenshots: responsive, state and session checks.
- `keyboard-evidence.json`, `keyboard-chart-*.png`, `external-resource-*.png`: keyboard focus/scroll and resource presentation.
- `live-ui-evidence.json`, `live-search-offer-1280.png`, `live-sources-*.png`: real consent → Search and internal-source rendering.
- `/private/tmp/riffin-live-current.jsonl`: separate provider check statuses/counts/redacted traces. A later single internal-miss check verified the updated history-routing instruction.

Files changed in this phase: `app.py`; `assets/styles.css`, `assets/chart_keys.html`, the Rock sticker color, griffin SVG/PNG and asset credits; `music_agent/{agent,chat_ui,presentation,recommendations,runner}.py`; `db.py`, `schema.sql`, seed JSON/SQLite and data credits; seed/provider-check scripts; catalog, agent, chat, onboarding and shell tests; README, checklist and integration/interface documentation. Existing theme configuration, secrets resolution, knowledge corpus and pinned dependencies are retained.

Hosted deployment/Search, publication/history audit, clean-checkout installation and presentation rehearsal remain pending. This local browser audit is not a screen-reader or all-browser accessibility certification. No commits, pushes or deployment were performed.
