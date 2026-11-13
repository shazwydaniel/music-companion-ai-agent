# Interface refinement verification · 13 November 2026

This phase implements the seven requested navigation, typography, spacing, chord-action and Chat-composer improvements. It changes presentation and session interactions; the approved song catalog and agent routing policies retain their existing behavior.

## Result

- Profile, song, answer-status and calculation tags use **Label : Value**. The shared renderer escapes labels and values, includes zero values such as capo 0, and omits missing values.
- **Poppins** supplies the UI font. Five unchanged TTF faces are bundled in `static/fonts/` with their SIL OFL notice, registered through native Streamlit theme font faces, and served locally. Chord panels retain monospace alignment; Material icons retain their icon font.
- Successful first setup opens **For You**. Navigation has icons and a tab rail distinct from pastel profile pills. **Chat** has a peach/brown accent, shadow and faint divider. Native radio keyboard/selection semantics remain available; phone labels stay on one line in a horizontally scrolling rail.
- **Browse Songs** replaces Catalog, **Saved & Recent** replaces Library, and **Chords & Lyrics** replaces Songbook in navigation and page headings. Internal view IDs remain stable for session actions. A selected song uses its title as the page heading.
- Cards and the music stand group title, artist, actions and quality tags. Primary **Open Chords** precedes supporting metadata. Chords appear before expandable source details; partial-reference and original-demo scope labels remain visible.
- On a song page, **Open Chords** refreshes one session recent entry and jumps to the sheet after the native rerun settles. Consecutive opens use independent numeric request IDs. **Back to Chat** and **Browse Songs** occupy a native anchored footer.
- Four **Suggested Prompts** appear above the anchored Chat composer: Explain a chord, Find a song, Transpose chords, and Plan practice. Clicking fills editable text without sending. Manual submission remains separate. The floating hierarchy clears the measured bottom area and fits below the header on short phone screens.

## Commands and local environment

Python **3.12.1**, using the pinned requirements and existing local virtual environment:

```sh
.venv/bin/python -m streamlit run app.py --server.headless=true --server.address=127.0.0.1 --server.port=8504
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m compileall -q app.py music_agent db.py tests
git diff --check
```

Preview: **http://localhost:8504**. Earlier user servers were left alone. Restart an older server once to pick up the native font/static-serving configuration. A server restart creates a fresh session; ordinary reruns and theme changes preserve the existing session.

**66 tests pass.** Updated expectations verify For You as the starting view and the revised music-stand heading. The added Chat test patches the submit boundary and verifies that a prompt-chip click makes no submission and creates no chat entry; manual submission creates exactly one user/assistant pair, and a rerun does not resend it. Existing escaping checks also cover the new metadata/profile rendering, zero values and missing values. AppTest removes both environment credentials and Streamlit Secrets for no-key paths. Scripted ADK fixtures remain distinct from live provider evidence.

## Browser evidence

Real headless Chrome tested the actual Streamlit DOM in two independent browser contexts. The main flow submitted the native genre-filtered setup, observed For You as the initial view, filled a suggested prompt, edited it to an unrelated question and manually submitted it, opened the Pop original demo, saved it, switched views/themes, repeatedly opened the sheet and returned to Chat. The unrelated response used the local scope guard; **no provider requests were needed for this UI check**.

The final matrix covers **five views × two themes × three widths = 30 combinations** at **1440, 1024 and 390 px**, with a 1000 px viewport height. Checks recorded no Streamlit exceptions or horizontal page overflow. The profile and selected song remained present. Song qualities/status labels used colons. Native bottom controls stayed in the viewport; the floating panel cleared them at narrow widths. A separate fresh browser context returned to the welcome screen without the first visitor's profile/history.

Repeated explicit chord jumps placed the sheet anchor at **123.734375 px**, below the fixed header. The anchored Back to Chat action preserved the displayed conversation. Additional checks cover native ArrowRight navigation, phone-rail geometry, transposed D-major retention across views/themes, source/footer clearance, long prompt autofill without sending, all five loaded Poppins faces and an expanded five-node hierarchy at **390 × 844 px**.

Local evidence is intentionally outside Git:

- `/private/tmp/riffin-no-key/v8/evidence.json`: the 30 view/theme/width measurements, isolated-session result and catalog digest.
- `/private/tmp/riffin-no-key/v8/details.json`: keyboard, phone rail, transposition, typography, footer and short-screen measurements.
- `/private/tmp/riffin-no-key/v8/`: screenshots for the matrix, welcome, sheet jump, source footer and expanded hierarchy.
- `/private/tmp/riffin-no-key/v8-browser.log`, `v8-finish.log`, `v8-details.log`: browser harness output. The final completion run incorporates the corrected DOM selectors, button-wrapper scoping, asynchronous scroll wait and contrast fixes identified during inspection.
- `/private/tmp/riffin-v8-tests.log`: passing local test output.

The catalog SHA-256 remained **`4f5324517965a24d4b51d412e0fd33c0611018f0b2977d46c0718b5a4b83f0c4`** across browser actions. Ignore probes still exclude `.venv`, `.env`, `.streamlit/secrets.toml`, logs, runtime output and artifacts. The approved seed and font assets remain eligible for tracking. README is the only project Markdown outside `docs/`.

## Files changed in this phase

| Area | Files |
|---|---|
| Main UI and shared rendering | `app.py`, `music_agent/presentation.py`, `music_agent/chat_ui.py`, `music_agent/calculator_ui.py` |
| Layout and local interaction scripts | `assets/styles.css`, `assets/interface_controls.html`, new `assets/focus_chords.html` |
| Typography | `.streamlit/config.toml`, new `static/fonts/Poppins-{Regular,Medium,SemiBold,Bold,MediumItalic}.ttf`, `static/fonts/OFL.txt` |
| Behavior checks | `tests/test_app_flow.py`, `tests/test_chat_ui.py`, `tests/test_catalog.py` |
| Handoff | `README.md`, `docs/UI_STYLE_GUIDE.md`, `docs/asset-attribution.md`, `docs/CAPSTONE_CHECKLIST.md`, `docs/INDEX.md`, this report |

## Limits and pending work

No blocker remains for this local UI phase. Hosted deployment, clean-checkout installation, publication/history audit and the previously pending fresh internal-miss → grounded Search provider check remain pending. Live Google calls were not repeated for these presentation changes; the earlier provider evidence is retained in [the Music Math report](interface-v6-verification.md) and [agent integration](agent-integration.md). Complete contemporary lyric sheets still require rights-cleared material; original demos and attributed public-domain examples remain available.

No files were staged or committed, and no push or deployment was performed.
