# Virtual Music Companion · UI style guide

## Latest refinements · 13 November 2026

Latest toolbar/prompt adjustment: keep native profile controls beside the fixed brand bar, using a second header row at tablet/phone widths. Keep the native menu available. Navigation and page content share a compact workspace with a 12 px gap. Merge starter actions and suggested prompts into the welcome card; group them by feature in a quiet two-column layout that stacks on phones, with wrapping rows inside each group. Keep all prompt chips and the Music calculator launcher inside the welcome card; its calculator opens in place. The composer contains only the input. Include feature, miss/fallback, guardrail and multi-specialist demo prompts; show actual activity without promising parallel execution. This adjustment is syntax-checked; visual checks are pending user testing.

Poppins now supplies all UI text, locally bundled with SIL OFL notices; chord lines retain a monospace grid. Label/value tags use **Label : Value**. Native icon navigation starts on **For You** after setup, then **Browse Songs**, **Saved & Recent**, **Chords & Lyrics**, and a separately accented **Chat** behind a faint divider. Keep native keyboard selection while hiding the radio circle. On phones the rail scrolls horizontally; it must not overflow the page.

Use 24 px desktop/16 px phone card insets, grouped quality tags and clear section gaps. Place **Open Chords** near each title, before supporting metadata; on the music stand it jumps to the playable sheet. Source details follow the material, with visible scope labels for partial references and generated demos. Anchor **Back to Chat** and **Browse Songs** in the native bottom row. Anchor **Suggested Prompts** above the chat input; chips fill editable text without sending. Keep the floating hierarchy above the actual composer/footer height at narrow widths.

The floating hierarchy uses a 16 px outer inset, padded disclosure/body/footer and inset node cards. It includes Music Math as a fourth specialist and distinguishes actual ADK activity from `local_*` Python calculation events. Five total nodes must fit/scroll within the viewport in both themes. Original genre demos are visibly marked; transposition is a local session display copy, with source scope and assumptions retained. All project Markdown except the root README is consolidated in this `docs/` folder.

Onboarding benefits are three distinct pink, sage and lavender cards in one row, with compact spacing on phones and dark ink in both themes. The welcome title uses semibold Poppins, the supporting line italic muted violet, and the invitation regular secondary text with Riffin’ emphasized. Genre selection immediately refreshes the three-song picker; before genres are selected it is disabled, and changing genres preserves only compatible draft picks. Native inputs rerun independently; one final button validates and saves the guest profile.

The latest display name is **Riffin’**, with the slogan **Good songs. Your kind of progress.** The welcome screen says **Let’s find your groove** and introduces discovery, sourced chords and AI practice help in casual copy. Profile editing says **Tune your vibe**. Nickname, instrument and level use separate pink, sage and lavender pills with dark ink in both themes. The app-owned brand bar is fixed at the top alongside the native toolbar, outside page flow with reserved content space; use stable test IDs, not generated Streamlit class names. Preserve native menu and Connection controls and check scroll behavior on phones.

Use the new user-supplied references as visual inspiration for pastel fields, organic blobs and restrained genre-colored border accents. Keep those reference images outside the public repository. “Chords & Lyrics” and “Open Chords” replace the ambiguous product label “Chart.” A session-stable licensed animal silhouette represents the visitor. Move connection/credits into the header. The floating agent view must show real callback activity, with native collapse and an optional drag handle; it must not animate invented progress. Preserve the tuned light/dark surfaces, contrast, mobile layout, session state and safe content rendering described below.

## Direction

Build a quiet, editorial music interface with a strong featured song, compact browsing cards, and small genre stickers attached to their borders. The user should see what they can play next, why it fits, and where to open the chart. Give light and dark their own tuned surfaces, art treatments, and focus colors. Both modes use the same layout, controls, and information hierarchy.

### Reference details to carry forward

| Reference | Use in this app |
|---|---|
| `IMG_0136.JPG` · Listing card grid | Use its image-led cards, rounded corners, quiet metadata, and single clear action for the For You grid and catalog. Show title, artist, one useful metadata line, and **Open chart**. |
| `IMG_0137 2.JPG` · Iceland Cabin | Use the tall full-bleed composition for one featured song. Fade art into a controlled opaque text area, anchor the title and reason near the bottom, and use one pill-shaped action. Use carousel dots only if the card actually has multiple panels. |
| `IMG_0138.JPG` · Taskello | Use its substantial rounded frame and folder-tab edge once, on the featured card or its header. Pair a warm image or texture with a solid content panel. |

Use original assets or assets approved for public redistribution. The three screenshots are design references. Keep them outside the public app repository and use seed artwork that can ship with the project.

## Theme tokens

| Token | Light | Dark | Use |
|---|---|---|---|
| Canvas | `#F7F6F1` | `#151413` | Page background |
| Surface | `#FFFDF8` | `#1F1D1B` | Cards, forms, chat, and chart panels |
| Raised surface | `#EFEEE7` | `#2A2724` | Insets, source chips, secondary fills |
| Primary text | `#211F1D` | `#F5F1E8` | Headings, chart text, and body |
| Secondary text | `#57534F` | `#BDB5AB` | Artist, metadata, hints, and citations |
| Decorative divider | `#DDD9D0` | `#413C36` | Surface separation |
| Control outline | `#81776D` | `#8A8176` | Visible control boundaries |
| Link and focus | `#8E321D` | `#FF9A78` | Underlined links and keyboard focus ring |
| Primary action fill | `#211F1D` | `#F5F1E8` | Open chart or other primary action |
| Primary action text | `#FFFDF8` | `#211F1D` | Text on primary actions |

- **Light** uses warm paper, crisp ink, and short soft shadows where an image card needs lift.
- **Dark** uses warm charcoal, cream text, and visible surface edges. Tune image scrims independently in both themes. If the brightest crop makes text hard to read, strengthen the solid content area.
- Use locally bundled **Poppins** for all UI text and **IBM Plex Mono**/system monospace for chord alignment. Include font redistribution notices. Preserve Material icon font rendering and chart monospace.
- Use a 44–56 px desktop page title, 36–44 px on narrow screens, 20–24 px section headings, and 15–16 px body text. Compact metadata should be at least 13 px.
- Use a 4/8 px spacing scale. Start with 16–20 px card padding, 24–32 px between sections, 16 px standard card radius, and 24–28 px featured card radius. Primary touch controls should be about 44 px tall.
- Target at least 4.5:1 for ordinary text and 3:1 for essential component boundaries and focus indicators. The theme token pairs are a starting point. Check the actual rendered UI, especially over art.

## Genre stickers

Put personality on the **outer edges** of the featured card or page header. Anchor one sticker to the primary genre. With multiple genres, optionally add one secondary sticker to a different edge. Keep the middle of the page clear for content.

| Genre | Motif | Suggested color |
|---|---|---|
| Rock | Small cutout flame | Ember `#FF6B45` |
| Pop | Four-point sparkle | Pink `#F58BAA` |
| Jazz | Brass record groove or crescent | Gold `#DBA85C` |
| Indie / Folk | Pressed leaf or tape corner | Sage `#88AC92` |
| Electronic | Pixel bolt | Violet `#B39CFA` |
| Classical | Small treble-clef paper cutout | Cornflower `#9BAFEF` |

- A sticker can overlap its frame by 6–10 px and rotate slightly. Give it a light cut-paper edge in light mode and a slightly brighter edge or backing in dark mode. Keep shapes original and simple.
- Keep stickers decorative, hidden from assistive technology, and outside button, text, and focus areas. No pointer events. Use a smaller sticker on narrow screens and keep it inside the viewport. Use text for genre and source wherever they convey information.
- Use static decoration. Keep song cards, forms, chat, and charts visually calm. A saved song or earned achievement can have a functional status marker.

## Screens and components

| Surface | Build rules |
|---|---|
| Onboarding | On a fresh session, show **Let’s find your groove** in a single-column form with nickname, instrument, skill level, genres, and the three-song picker. Use concise labels, clear validation, and one submit action. Use the casual welcome invitation and a short session-only caption as supporting text. Omit account and credential fields. |
| For You | Lead with one featured song. Below it, display two or three image-led cards per row where space permits and one per row on narrow screens. Each card includes title, artist, one recommendation reason, and an **Open chart** action. Save uses a labeled secondary control. |
| Chart | Prioritize the title, key or capo when present, source, and chart content. Set chord and lyric lines in the same monospaced grid so chord positions stay aligned. Keep long lines scrollable inside the chart. Use a clear distinction between chord labels and lyrics, and preserve readable lyrics in both themes. |
| Companion Chat | Use Streamlit’s accessible chat controls and the text labels **Catalog**, **Internal notes**, and **Web results**. Offer **Search the web** when the internal notes or catalog have no relevant match. Keep the compact agent trace in a disclosure and show factual status for loading, no result, and error. |
| Library and profile | Show recently opened and saved songs from the current session in compact rows. Use an actual title, artist, and action. Show a quiet empty state when history or favorites are empty. |

Decorative art can be abstract gradients, original music imagery, or approved artwork. Keep a local fallback for every image-led card. Favor clean hierarchy, useful metadata, and single actions. Use decorative treatments where they support the music identity.

## Streamlit implementation

1. Define both themes in `.streamlit/config.toml` using `[theme.light]` and `[theme.dark]` on the Streamlit version pinned in `requirements.txt`. Expose Streamlit’s theme selector and document where it is.
2. Use native Streamlit widgets for form submission, chat, and buttons. Keep custom styles scoped to the featured card, chart, or other app-owned components. Custom components should use supported Streamlit theme variables for their current colors. Avoid selectors tied to generated Streamlit class names.
3. Drive stickers from a fixed mapping of allowed genre keys to local assets. Keep nickname, model text, and catalog content in escaped or native rendering. Use local fallbacks for missing images and fonts.
4. Test the same onboarding → For You → chart → chat flow in both themes at desktop and narrow widths. Check keyboard focus, text contrast on art, chart scrolling, loading and empty states, and any sticker overlap. Switching themes should preserve the user’s current app state.

## Implementation references

- [Streamlit theme configuration](https://docs.streamlit.io/develop/concepts/configuration/theming)
- [Streamlit custom component theming](https://docs.streamlit.io/develop/concepts/custom-components/components-v2/theming)
- [Streamlit Community Cloud secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
