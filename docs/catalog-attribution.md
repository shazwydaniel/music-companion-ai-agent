# Real songs, researched chord references, and reusable lyric examples

`data/seed_catalog.json` is the source of truth. The explicit seed command builds `data/catalog.sqlite` atomically. The database contains **48 real works plus six original genre demos / 108 Guitar and Piano entries**, nine works per genre, with no user data. Its Songbook contains **86 source-backed harmonic references, ten public-domain study entries and twelve original-demo entries**. No entry needs to redirect to Musicnotes just to show its stored chord information.

The six original teaching songs were generated for this app at the user's request, using common genre-associated chord vocabulary rather than copied song lyrics or arrangements. They are labeled **Original demo** and are dedicated under CC0 1.0 to the extent rights apply. Their complete new texts and accompaniment are documented in [Original demos](original-demos.md). This does not change the separate rights or attribution of the real catalog songs, or the human-created mascot. Original demos use the CC0 terms URL as a reuse notice, not as a claimed external lyric edition.

## What the references mean

Each reference retains a chord-source URL, research date, scope note and attribution. Some entries describe a short repeating cycle; others list a partial chord vocabulary or analytical harmonic centers. These are **not full, official, note-for-note arrangements**. Chordify entries are labelled as recording analyses, not artist-verified transcriptions. Complex works such as Bohemian Rhapsody and Clair de lune are explicitly partial. Do not infer a full progression, timing or playable piano score from a chord-name list.

The [research ledger](chord_research.md) lists all entries and sources. Sources include named educators (Fender, Pianamo, JustinGuitar, Jazz Guitar Online, Spy Tunes, PianoTV) and Chordify recording analysis. Contemporary references store basic harmonic facts only: no lyrics, melody, tablature, voicing diagrams or full third-party arrangement. Each entry keeps a secondary publisher search link under Full-score options, with no guarantee that a particular edition exists or is free.

Guitar shapes, capo placement and concert pitch are distinguished. Here Comes the Sun uses Fender's D-family guitar shapes with capo 7; its Piano entry gives the corresponding A-family concert-pitch chord names. Nirvana's D-standard shape names are distinguished from sounding pitches. Wake Me Up uses JustinGuitar's capo-2 vocabulary. For Too Sweet, a capo-3 mapping is derived from the tutorial's Em-family shapes and the sourced G-minor tonal center; it is not a claim about the artist's preferred fingering. These references are starting points for learning, not substitutes for an authorized complete edition.

## Public-domain chords and lyrics demo

**Amazing Grace** contains three public-domain Newton stanzas with Riffin's own simplified G-major accompaniment, aligned above the lyric words. The historical text/tune is documented by [Hymnary](https://hymnary.org/text/amazing_grace_how_sweet_the_sound) and the [Library of Congress](https://www.loc.gov/collections/amazing-grace/articles-and-essays/dissemination-of-amazing-grace.html/). This is a real traditional song with an authored teaching accompaniment, not a transcription of a modern recording. The **Try chords + lyrics demo** action opens it directly without Gemini.

**Ode to Joy** (Beethoven, 1824) and **Canon in D** (Pachelbel, P.37) retain chord-only accompaniment studies of public-domain compositions. Their work-catalog sources remain with each song. Riffin's new study formatting/accompaniments are dedicated under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). Underlying public-domain works remain public domain.

**Auld Lang Syne** includes the public-domain verse and chorus as printed in [The Canadian Soldiers' Song Book (1918)](https://en.wikisource.org/wiki/The_Canadian_Soldiers%27_Song_Book/Auld_Lang_Syne), with typography-only apostrophe changes and Riffin's own G-major accompaniment. It is this edition's text, not every Burns stanza or a modern recording.

**Greensleeves** includes the first verse and refrain from [A Handful of Pleasant Delights (1584; 1878 edition)](https://en.wikisource.org/wiki/A_Handful_of_Pleasant_Delights/A_new_Courtly_Sonet,_of_the_Lady_Greensleeues). Riffin modernizes spelling and supplies an original simplified A-minor accompaniment. Neither Ralph Vaughan Williams' arrangement nor a modern performance is copied. New accompaniment/formatting remains CC0; historical underlying text remains public domain.

Every stored lyric entry retains `lyrics_license` and `lyrics_source_url` in the seed and SQLite; validation rejects missing reuse metadata. Reference entries cannot contain lyrics. Sources are evidence for the stated factual scope, not a blanket redistribution license for the source's lesson, notation or arrangement.

## Material still requiring clearance

Full contemporary lyrics and copyrighted published arrangements cannot be scraped into a redistributable public app merely because they can be viewed online. Rights-cleared material or an appropriate licensed provider is still needed for complete Billie Eilish, Olivia Rodrigo, The Weeknd, and other contemporary lyric charts. That part remains pending; it is not silently replaced with fabricated lyrics or labelled complete. Artist/recording/score rights remain with their respective owners. Metadata/schema/software fall under the repository MIT license; that does not license a third-party song or score.

Genre groupings and practice levels are editorial browsing estimates, not popularity charts or guarantees about a full edition's difficulty. Song identity sources and chord research sources are separate. No artist album covers, recordings, reference screenshots, or paid scores are redistributed.
