# Riffin’ knowledge stores

The app uses two complementary read-only sources:

| Store | Contents | Agent tool |
|---|---|---|
| `MUSIC_KNOWLEDGE_BASE.md` | Four authored lessons: triads, I–IV–V, inversions and clean guitar changes. Each lesson is indexed independently and uses the retrieval relevance gate. | `search_theory_notes` through Piano & Theory |
| `../data/catalog.sqlite` | 48 sourced real songs plus six original genre demos; 108 instrument entries. Short harmonic references, public-domain studies and original generated lyrics/accompaniments. | `get_chord_chart` through Guitar; `transpose_song` through Music Math |

Favorite genres filter the onboarding picker and influence recommendations. They do not restrict which catalog song or lesson someone may explicitly ask about. Changing genres cannot write to either knowledge store.

The repeatable public catalog source is `../data/seed_catalog.json`; research and reuse scope are recorded in `chord_research.md`, `catalog-attribution.md` and `original-demos.md` in this folder. Stored lyrics include public-domain editions of Amazing Grace, Auld Lang Syne and Greensleeves, plus six original generated CC0-demo texts. Complete contemporary lyrics and full published arrangements require rights-cleared material; they are not scraped into the knowledge base.

To rebuild the catalog explicitly, run `.venv/bin/python scripts/seed_catalog.py` from the repository root. To index the four lessons, run `.venv/bin/python scripts/index_knowledge.py`. Ordinary UI reruns do neither catalog writes nor personal-data indexing. Confirmed misses can fall back to query-only Web Search; retrieval errors remain distinct.
