"""Riffin's session-only onboarding, recommendations, catalog, and chart flow."""

# 1. Imports — catalog services have no dependency on Gemini or credentials.
import asyncio
import sqlite3

import streamlit as st

from db import find_chord_chart, get_chart, list_songs
from music_agent import DISPLAY_NAME
from music_agent.config import resolve_google_api_key
from music_agent.discovery import discovery_signature, search_new_songs
from music_agent.chat_ui import queue_search, render_chat
from music_agent.activity import render_activity_panel
from music_agent.presentation import ASSETS, VIEW_LABELS, artwork_html, brand_html, chart_section_html, genre_frame_html, greeting_mascot_html, profile_pills_html, metadata_tags_html
from music_agent.recommendations import LEVELS, rank_songs
from music_agent.session import (
    GENRES, GENRE_DEMOS, INSTRUMENTS, SKILL_LEVELS, initialize_session,
    open_chart, save_song, song_options_for_genres, update_profile,
)


# 2. App actions — only explicit handlers update activity in this session.
def handle_open(chart_id: str) -> None:
    """Validate the chart ID before changing the active chart or recent views."""
    result = get_chart(chart_id)
    if result["status"] == "found":
        open_chart(st.session_state, result["chart"])
        st.session_state["view"] = "Songbook"
        st.session_state["action_error"] = None
    else:
        st.session_state["action_error"] = "This chart could not be opened. Try the catalog again."


def handle_save(song_id: str) -> None:
    """Revalidate the song, then deduplicate the session save."""
    try:
        saved = save_song(st.session_state, song_id, {song["id"] for song in list_songs()})
    except (sqlite3.Error, ValueError, OSError):
        saved = False
    st.session_state["action_error"] = None if saved else "This song could not be saved."


def reopen_and_focus(chart_id: str) -> None:
    """An explicit open refreshes this session once and brings the sheet into view."""
    handle_open(chart_id)
    st.session_state["chord_focus_request"] = st.session_state.get("chord_focus_request", 0) + 1
    st.session_state["focus_chord_sheet"] = True


def edit_profile() -> None:
    """Open preferences without resetting favorites, history, or chat."""
    st.session_state["editing_profile"] = True


def cancel_edit() -> None:
    """Keep the existing profile when the visitor cancels changes."""
    st.session_state["editing_profile"] = False


def sync_genre_picks(songs: list[dict]) -> None:
    """Keep compatible draft picks before the dependent picker is rendered."""
    allowed = {song["id"] for song in song_options_for_genres(songs, st.session_state.get("profile_genres", []))}
    before = st.session_state.get("profile_picks", [])
    st.session_state["profile_picks"] = [song_id for song_id in before if song_id in allowed]
    st.session_state["genre_picks_removed"] = len(before) - len(st.session_state["profile_picks"])


# 3. Session and onboarding — reruns reuse memory; a new session starts setup.
@st.dialog("Meet Riffin’", width="medium", position="center", dismissible=False)
def show_first_visit_greeting() -> None:
    """Welcome this visitor once; the backdrop keeps onboarding in context."""
    with st.container(key="riffin-greeting"):
        st.html(greeting_mascot_html())
        st.html(
            '<div class="riffin-greeting-message">'
            '<p class="riffin-greeting-tagline">Your Virtual Music Sidekick</p>'
            '<p class="riffin-greeting-copy">From “I love this song” to “wait, I can play this.”</p>'
            '</div>'
        )
        with st.container(key="riffin-greeting-action"):
            if st.button("Start Playing", type="primary", key="greeting-continue", use_container_width=True):
                st.session_state["greeting_seen"] = True
                st.rerun()
        st.html('<p class="riffin-greeting-credit">Made by Wywy, Powered by Agentic AI.</p>')


def render_profile_form(songs: list[dict]) -> None:
    """Collect a guest profile and exactly three distinct catalog song IDs."""
    profile = st.session_state["profile"]
    current = profile or {}
    by_id = {song["id"]: song for song in songs}
    with st.container(key="riffin-onboarding-intro"):
        st.header("Tune your vibe" if profile else "Let’s find your groove")
    if not profile:
        with st.container(key="riffin-welcome-features"):
            st.html('''<div class="riffin-feature-grid">
                <article class="welcome-feature discover"><span class="feature-number">01 / DISCOVER</span><h3>Find your next song</h3><p>Discover picks shaped by your taste and playing level.</p></article>
                <article class="welcome-feature chords"><span class="feature-number">02 / PLAY</span><h3>Get into the chords</h3><p>Explore sourced chord references and a chords-with-lyrics demo.</p></article>
                <article class="welcome-feature explore"><span class="feature-number">03 / GROW</span><h3>Keep the music moving</h3><p>Ask about theory, get practice help, or explore music on the web with AI.</p></article>
            </div>''')
    st.html('<p class="riffin-session-note">Just for this visit. Your picks, saves and chats stay with you until the session ends.</p>')
    # Native inputs rerun immediately so genre changes can refresh song options.
    with st.container(border=True, key="profile_form"):
        nickname = st.text_input(
            "Nickname", value=current.get("nickname", ""), max_chars=40, key="profile_nickname",
        )
        # 3a. Equal columns keep related preferences together on wide screens.
        instrument_col, skill_col = st.columns(2, gap="medium")
        with instrument_col:
            instrument = st.selectbox(
                "Instrument", INSTRUMENTS, index=INSTRUMENTS.index(current.get("instrument", "Guitar")),
                key="profile_instrument",
            )
        with skill_col:
            skill = st.selectbox(
                "Skill Level", SKILL_LEVELS, index=SKILL_LEVELS.index(current.get("skill_level", "Beginner")),
                key="profile_skill",
            )
        genres_col, picks_col = st.columns(2, gap="medium")
        with genres_col:
            genres = st.multiselect("Favorite Genres", GENRES, default=current.get("genres", []), key="profile_genres",
                                    on_change=sync_genre_picks, args=(songs,))
            if st.session_state.get("genre_picks_removed"):
                st.caption("Your genres changed, so we cleared picks outside them. The matching picks are still here.")
        eligible = {song["id"] for song in song_options_for_genres(songs, genres)}
        defaults = [song_id for song_id in current.get("picks", []) if song_id in eligible]
        with picks_col:
            picks = st.multiselect(
                "Three Song Picks", [song_id for song_id in by_id if song_id in eligible], default=None if "profile_picks" in st.session_state else defaults,
                format_func=lambda song_id: f"{by_id[song_id]['title']} — {by_id[song_id]['artist']}",
                max_selections=3, key="profile_picks", disabled=not genres,
                help="Songs match any of your selected genres. Removing a genre clears only picks that no longer match.",
            )
            if genres:
                st.caption(f"{len(eligible)} songs across your selected genres. Pick three favorites.")
            else:
                st.html('<p class="riffin-no-genre-hint"><span aria-hidden="true">*</span> Choose a genre to find your first three songs.</p>')
        with st.container(horizontal=True, horizontal_alignment="right", key="riffin-profile-submit-row"):
            submitted = st.button(
                "Save My Vibe" if profile else "Start Exploring", type="primary", key="profile-submit",
            )
    if submitted:
        error = update_profile(st.session_state, nickname, instrument, skill, genres, picks, songs)
        if error:
            st.error(error)
        else:
            if not profile:
                st.session_state["view"] = "For You"
            st.rerun()
    if profile:
        st.button("Cancel", on_click=cancel_edit)


# 4. For You — one featured card, then a responsive native grid of real songs.
def render_song(song: dict, prefix: str, featured: bool = False) -> None:
    """Present public metadata and explicit actions with stable widget keys."""
    profile = st.session_state["profile"]
    card_key = "riffin-feature" if featured else f"song-{prefix}-{song['id']}"
    with st.container(border=True, key=card_key):
        if song.get("origin") == "original-demo":
            st.caption("ORIGINAL DEMO · CC0")
        if featured:
            st.caption("ON YOUR NEXT SETLIST")
            art, details = st.columns([1, 1.15], vertical_alignment="center")
        else:
            art = details = st
        with art.container():
            st.html(artwork_html(song["genre"], featured, profile["genres"][0]))
        with details.container():
            st.subheader(song["title"])
            st.write(song["artist"])
        instrument = profile["instrument"] if profile["instrument"] in song["instruments"] else song["instruments"][0]
        with details.container(horizontal=True):
            st.button(
                "Open Chords", icon=":material/menu_book:", key=f"open-{prefix}-{song['id']}", type="primary",
                on_click=handle_open, args=(f"{song['id']}-{instrument.lower()}",),
            )
            st.button(
                "Saved ✓" if song["id"] in st.session_state["favorites"] else "Save",
                key=f"save-{prefix}-{song['id']}", on_click=handle_save, args=(song["id"],),
            )
        with details.container():
            st.html(metadata_tags_html([("Genre", song["genre"]), ("Level", song["difficulty"]), ("Year", str(song["release_year"] or "Traditional"))]))
            st.caption("Chords + lyrics" if song["id"] in {"amazing-grace", "auld-lang-syne", "greensleeves"} or song.get("origin") == "original-demo" else
                       "Practice chords" if song["chart_kind"] == "inline" else "Chord reference")
            if "reason" in song:
                st.write(" · ".join(song["reason"].split(" · ")[:2]))


def refresh_web_discovery() -> None:
    """Permit one new search only after an explicit refresh in this session."""
    st.session_state["web_discovery"] = None


def render_web_discovery(songs: list[dict], on_activity=None) -> None:
    """Show source-backed web ideas distinct from stored catalog charts."""
    profile = st.session_state["profile"]
    st.subheader("Beyond the Catalog")
    st.caption("More songs to explore, shaped by your genres, three picks and playing level.")
    key = resolve_google_api_key(st.secrets)
    if not key.configured:
        st.info("Web discoveries are offline until a server Google key is configured. Your catalog picks still work.")
        return
    signature = discovery_signature(profile)
    cached = st.session_state.get("web_discovery")
    if not isinstance(cached, dict) or cached.get("signature") != signature:
        st.session_state["agent_turn"] = st.session_state.get("agent_turn", 0) + 1
        st.session_state["agent_activity"] = {"_turn": st.session_state["agent_turn"]}
        with st.spinner("Riffin’ is finding new songs on the web…"):
            result = asyncio.run(search_new_songs(profile, songs, key.api_key, on_activity=on_activity))
        cached = {"signature": signature, "result": result}
        st.session_state["web_discovery"] = cached
    result = cached["result"]
    if result["status"] == "ok":
        with st.grid(min_column_width=260, gap="medium"):
            for index, item in enumerate(result["items"]):
                with st.container(border=True, key=f"riffin-web-card-{index}"):
                    st.caption("WEB DISCOVERY · NEW TO RIFFIN’")
                    st.subheader(item["title"])
                    st.write(item["artist"])
                    st.write(item["why"])
                    st.html(metadata_tags_html([
                        ("Instrument", profile["instrument"]),
                        ("Level", f"{profile['skill_level']} goal"),
                    ]))
        st.caption("These are web suggestions, not stored charts. Practice fit depends on the arrangement you choose.")
    elif result["status"] == "unstructured":
        st.warning("Search found sources but could not make reliable song cards this time.")
        if result["answer"]:
            st.write(result["answer"])
    else:
        st.warning(result["answer"] or "Web discovery is temporarily unavailable.")
    if result["sources"]:
        with st.expander("Grounded Web Sources"):
            st.caption("Links returned by Google Search for this set; song arrangements and difficulty still need checking.")
            for source in result["sources"]:
                st.link_button(source["title"], source["url"])
    st.button("Find More Songs", icon=":material/refresh:", key="refresh-web-discovery", on_click=refresh_web_discovery)


def render_feed(songs: list[dict], on_activity=None) -> None:
    """Rank local songs and cache one grounded web discovery per profile."""
    st.header("For You")
    st.caption("A few songs to make your next practice feel closer.")
    profile = st.session_state["profile"]
    ranked = [song for song in rank_songs(songs, profile, set(st.session_state["recent_views"]))
              if song["genre"] in profile["genres"]
              and profile["instrument"] in song["instruments"]
              and LEVELS[song["difficulty"]] <= LEVELS[profile["skill_level"]]]
    if not ranked:
        st.info("You have explored every suggestion for your genres and playing level. Browse Songs or edit your profile for more.")
    else:
        render_song(ranked[0], "featured", featured=True)
    render_web_discovery(songs, on_activity)
    if ranked:
        st.subheader("Keep exploring")
        with st.grid(min_column_width=260, gap="medium"):
            for song in ranked[1:7]:
                render_song(song, "feed")
        st.button("Browse all songs", icon=":material/library_music:", on_click=lambda: st.session_state.update(view="Catalog"))


# 5. Catalog lookup — misses, ambiguity, and read errors have distinct statuses.
def render_lookup_result(result: dict) -> None:
    """Require an explicit Open chart even after a successful title lookup."""
    status = result["status"]
    if status == "not_found":
        st.info("No matching chords in the catalog. Try another title or browse below.")
        query = " ".join((
            st.session_state.get("lookup_title", ""),
            st.session_state.get("lookup_artist", ""), "chord chart",
        )).strip()
        st.button("Search the web", key="catalog-search-web", on_click=queue_search, args=(query,))
    elif status == "error":
        st.error("The catalog lookup failed. Please try again; this is not a catalog miss.")
    else:
        choices = result["choices"] if status == "ambiguous" else [{
            "chart_id": result["chart"]["id"], "song_id": result["chart"]["song_id"],
            **{key: result["chart"][key] for key in ("title", "artist", "instrument")},
        }]
        if status == "ambiguous":
            st.info("More than one chart matches. Choose the song and arrangement you mean.")
        else:
            st.success("Catalog match found")
        for choice in choices:
            with st.container(border=True):
                st.write(f"{choice['title']} — {choice['artist']}")
                st.html(metadata_tags_html([("Instrument", choice["instrument"])]))
                st.button(
                    "Open Chords", icon=":material/menu_book:", key=f"lookup-open-{choice['chart_id']}", type="primary",
                    on_click=handle_open, args=(choice["chart_id"],),
                )


def render_catalog(songs: list[dict]) -> None:
    """Offer direct browsing and exact normalized chart lookup."""
    st.header("Browse Songs")
    st.caption("Search the full collection, explore a genre, or open an original demo.")
    st.button("Try chords + lyrics demo", key="catalog-lyrics-demo", on_click=handle_open,
              args=("amazing-grace-guitar",))
    with st.expander("Original genre demos · reusable chords & lyrics"):
        st.caption("Six original teaching songs, generated for Riffin’. No third-party lyrics copied.")
        with st.container(horizontal=True):
            for genre, song_id in GENRE_DEMOS.items():
                st.button(f"Open {genre} demo", key=f"demo-open-{song_id}", on_click=handle_open,
                          args=(f"{song_id}-{st.session_state['profile']['instrument'].lower()}",))
    with st.form("catalog_lookup"):
        title = st.text_input("Song title", key="lookup_title")
        artist = st.text_input("Artist (optional)", key="lookup_artist")
        instrument = st.selectbox("Instrument", ("Any instrument", *INSTRUMENTS), key="lookup_instrument")
        submitted = st.form_submit_button("Find chords")
    if submitted:
        if not title.strip():
            st.warning("Enter a song title to look up a chart.")
            st.session_state["lookup_result"] = None
        else:
            st.session_state["lookup_result"] = find_chord_chart(
                title, artist, "" if instrument == "Any instrument" else instrument,
            )
            if st.session_state["lookup_result"]["status"] == "not_found":
                queue_search(f"{title} {artist} chords".strip(), automatic=True)
                st.rerun()
    if st.session_state["lookup_result"]:
        render_lookup_result(st.session_state["lookup_result"])
    st.subheader("Browse all songs")
    genre = st.selectbox("Browse genre", ("All genres", *GENRES), key="browse_genre")
    with st.grid(min_column_width=260, gap="medium"):
        for song in songs:
            if genre == "All genres" or song["genre"] == genre:
                render_song(song, "catalog")


# 6. Music stand — clear action/metadata hierarchy, then the actual playable material.
def render_chart(on_activity=None) -> None:
    """Render session-only transposition, attributed chord material and anchored navigation."""
    chart_id = st.session_state["active_chart"]
    if chart_id is None:
        st.header("Chords & Lyrics")
        st.caption("Your music stand. Open a song from For You, Browse Songs, or Saved & Recent.")
        st.button("Try chords + lyrics demo", key="songbook-lyrics-demo", on_click=handle_open,
                  args=("amazing-grace-guitar",), type="primary", icon=":material/menu_book:")
        return
    result = get_chart(chart_id)
    if result["status"] != "found":
        st.error("These chords are unavailable. Choose another song in Browse Songs.")
        return
    chart = result["chart"]
    with st.container(border=True, key="riffin-song-overview"):
        st.caption("CHORDS & LYRICS / YOUR MUSIC STAND")
        st.header(chart["title"])
        st.write(chart["artist"])
        other = "Piano" if chart["instrument"] == "Guitar" else "Guitar"
        with st.container(horizontal=True, key="riffin-song-actions"):
            st.button("Open Chords", icon=":material/menu_book:", type="primary", key="reopen-active-chart",
                      on_click=reopen_and_focus, args=(chart_id,))
            st.button("Save", icon=":material/bookmark:", key="save-active-chart", on_click=handle_save, args=(chart["song_id"],))
            st.button(f"Open {other} chords", icon=":material/swap_horiz:", key="other-instrument", on_click=handle_open,
                      args=(f"{chart['song_id']}-{other.lower()}",))
        if chart["song_id"] in st.session_state["favorites"]:
            st.caption("Saved for this session")
        # This disclosure edits only a display copy, never the approved catalog.
        with st.expander("Change key · transpose chords"):
            from music_agent.calculations import SHARPS, FLATS, transpose_catalog_chart
            tonics = tuple(dict.fromkeys((*SHARPS, *FLATS)))
            previous = st.session_state["transpositions"].get(chart_id, {}).get("outputs", {}).get("target_key", "C").split()[0]
            target = st.selectbox("Target sounding tonic", tonics, index=tonics.index(previous) if previous in tonics else 0, key=f"transpose-target-{chart_id}")
            st.caption("Keeps chord quality and mode. Use the result in standard tuning without a capo.")
            if st.button("Transpose", key=f"transpose-song-{chart_id}"):
                if on_activity:
                    on_activity({"agent": "music_math", "tool": "local_transpose_song", "status": "running"})
                changed = transpose_catalog_chart(chart, target)
                if changed["status"] == "found":
                    st.session_state["transpositions"][chart_id] = changed
                else:
                    st.warning(changed["message"])
                if on_activity:
                    on_activity({"agent": "music_math", "tool": "local_transpose_song", "status": changed["status"]})
            if st.button("Original key", key=f"reset-transpose-{chart_id}"):
                st.session_state["transpositions"].pop(chart_id, None)
        if changed := st.session_state["transpositions"].get(chart_id):
            st.caption(f"Transposed for this visit · Original key : {chart['musical_key']}")
            chart = {**chart, "content": changed["outputs"]["content"], "musical_key": changed["outputs"]["target_key"],
                     "tuning": "E A D G B E (standard)" if chart["instrument"] == "Guitar" else None, "capo": 0 if chart["instrument"] == "Guitar" else None}
        has_lyrics = any("lyrics" in line for section in chart["content"] for line in section["lines"])
        material = "Original demo" if chart.get("origin") == "original-demo" else "Partial chord reference" if chart["chart_kind"] == "reference" else "Chords & lyrics" if has_lyrics else "Practice accompaniment"
        st.html(metadata_tags_html([
            ("Instrument", chart["instrument"]), ("Level", chart["difficulty"]), ("Genre", chart["genre"]),
            ("Key", chart["musical_key"]), ("Capo", chart["capo"]), ("Tuning", chart["tuning"]),
            ("Material", material), ("Lyrics", chart.get("lyrics_license")),
        ]))
        if chart["chart_kind"] == "reference":
            st.caption("A researched chord reference, not the complete arrangement. Check version details below.")
        elif chart.get("origin") == "original-demo":
            st.caption("Original generated teaching song · CC0 dedication · reusable demo lyrics and accompaniment")
        # 3a. Instrument advice is a teaching suggestion, not a recording claim.
        if chart["chart_kind"] != "external":
            from music_agent.playing_notes import playing_note
            note = playing_note(chart["instrument"])
            if note:
                with st.container(border=True, key="riffin-playing-note"):
                    st.markdown(f"**{note['title']}**")
                    st.write(note["suggestion"])
                    st.caption(note["scope"])
    # Chords come before provenance detail so the page leads with something to play.
    st.html('<div id="riffin-chord-sheet" aria-hidden="true"></div>')
    with st.container(key="riffin-chord-content"):
        if chart["chart_kind"] == "external":
            with st.container(border=True, key="riffin-chart-resource"):
                st.subheader("Find a published edition")
                st.link_button("Find sheet music at Musicnotes ↗", chart["resource_url"])
                st.caption("External editions may require purchase; no score or lyrics are stored here.")
        else:
            st.subheader("Chords & lyrics" if has_lyrics else "Chord reference")
            for index, section in enumerate(chart["content"]):
                with st.container(key=f"riffin-sheet-section-{index}"):
                    st.caption(section["name"])
                    st.html(chart_section_html(section))
            st.html(ASSETS / "chart_keys.html", unsafe_allow_javascript=True)
            st.caption("Focus a chord panel and use ← / → to scroll. Home / End jump along the line.")
    with st.container(key="riffin-version-details"):
        with st.expander("About this version & sources"):
            if chart.get("reference_note"):
                st.write(chart["reference_note"])
            st.write(chart["attribution"])
            st.html(metadata_tags_html([("Researched", chart.get("checked_on")), ("Lyrics", chart.get("lyrics_license"))]))
            if chart.get("chord_source_url"):
                st.link_button("Chord / lyric source ↗", chart["chord_source_url"])
            if chart.get("lyrics_source_url"):
                st.link_button("Demo reuse terms ↗" if chart.get("origin") == "original-demo" else "Lyric edition ↗", chart["lyrics_source_url"])
            st.link_button("Demo reuse terms ↗" if chart.get("origin") == "original-demo" else "Song metadata source ↗", chart["source_url"])
        if chart["chart_kind"] == "reference" and chart.get("resource_url"):
            with st.expander("Full-score options"):
                st.link_button("Browse publisher editions ↗", chart["resource_url"])
                st.caption("Complete contemporary lyrics and published arrangements need redistribution permission.")
    with st.bottom:
        with st.container(horizontal=True, vertical_alignment="center", key="riffin-song-footer"):
            st.button("Back to Chat", icon=":material/forum:", type="primary", key="song-back-chat", on_click=lambda: st.session_state.update(view="Chat"))
            st.button("Browse Songs", icon=":material/library_music:", key="song-back-browse", on_click=lambda: st.session_state.update(view="Catalog"))
            st.caption(f"On your stand : {chart['title']}")
    if st.session_state.pop("focus_chord_sheet", False):
        # A numeric request ID makes consecutive explicit opens execute independently.
        script = (ASSETS / "focus_chords.html").read_text().replace(
            "__RIFFIN_FOCUS_REQUEST__", str(int(st.session_state["chord_focus_request"])),
        )
        st.html(script, unsafe_allow_javascript=True)


# 7. Library — activity is in memory and deduplicated by song ID.
def render_library(songs: list[dict]) -> None:
    """Show actual recent and saved songs, with useful empty states."""
    st.header("Saved & Recent")
    st.caption("Songs you saved and opened during this visit. Pick one to keep playing.")
    by_id = {song["id"]: song for song in songs}
    libraries = (
        ("Recently Opened", st.session_state["recent_views"]),
        ("Saved Songs", st.session_state["favorites"]),
    )
    for label, records in libraries:
        st.subheader(label)
        if not records:
            st.caption(
                "No recently opened songs yet." if label == "Recently Opened"
                else "No saved songs yet. Save a song to keep it here for this session."
            )
        ordered = sorted(
            records,
            key=lambda song_id: records[song_id]["opened_at"] if label == "Recently Opened" else records[song_id],
            reverse=True,
        )
        for song_id in ordered:
            if song_id not in by_id:
                continue
            song = by_id[song_id]
            instrument = st.session_state["profile"]["instrument"]
            if instrument not in song["instruments"]:
                instrument = song["instruments"][0]
            chart_id = (
                records[song_id]["chart_id"] if label == "Recently Opened"
                else f"{song_id}-{instrument.lower()}"
            )
            with st.container(border=True, horizontal=True, vertical_alignment="center", key=f"saved-row-{label}-{song_id}"):
                with st.container(width="stretch"):
                    st.write(f"{song['title']} — {song['artist']}")
                    if label == "Recently Opened":
                        timestamp = records[song_id]["opened_at"][:16].replace("T", " ")
                        st.html(metadata_tags_html([("Last opened", f"{timestamp} UTC")]))
                st.button("Open Chords", icon=":material/menu_book:", type="primary", key=f"library-{label}-{song_id}", on_click=handle_open, args=(chart_id,))


# 8. Page configuration, secrets, and catalog setup — never seed on a rerun.
def main() -> None:
    """Run the offline-first flow with no shared or persistent user data."""
    st.set_page_config(page_title=DISPLAY_NAME, page_icon=str(ASSETS / "griffin.png"), layout="wide")
    st.html(ASSETS / "styles.css")
    initialize_session(st.session_state)
    # Detach navigation from widget cleanup while the profile form is showing.
    st.session_state["view"] = st.session_state.pop("redirect_view", st.session_state.get("view", "For You"))
    profile = st.session_state["profile"]
    genre = profile["genres"][0] if profile else "Pop"
    st.html(genre_frame_html(genre))
    with st.container(key="riffin-header"):
        with st.container(horizontal=True, vertical_alignment="center", key="riffin-toolbar-row"):
            st.html(brand_html(genre))
            # 8a. Native profile controls share the fixed toolbar band with the brand.
            if profile:
                with st.container(horizontal=True, vertical_alignment="center", width="content", key="riffin-profile-bar"):
                    with st.container(width=32):
                        st.image(str(ASSETS / "avatars" / f"{st.session_state['avatar']}.png"), width=32)
                    st.html(profile_pills_html(profile))
                    st.button("Edit profile", icon=":material/tune:", on_click=edit_profile)
            with st.popover("Connection", icon=":material/wifi:", key="connection-status"):
                google_key = resolve_google_api_key(st.secrets)
                st.write("AI ready · key configured" if google_key.configured else "AI offline · key unavailable")
                st.caption("Key presence only; provider availability is checked when you ask a question.")
                st.caption("Local misses trigger Web Search automatically. Say ‘local only’ to keep a request in the catalog and notes.")
                st.caption("Preferences, saves and conversations last for this session.")
                with st.expander("Knowledge base · four lessons"):
                    st.write("Major/minor triads; I–IV–V progressions; keyboard inversions; clean guitar chord changes.")
                    st.caption("The song catalog is a separate store. Current music facts come from Web Search.")
                st.markdown("Griffin: [Delapouite](https://game-icons.net/1x1/delapouite/griffin-symbol.html). Animal avatars: Lorc and Delapouite, [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).")
                st.caption("Light / Dark: top-right menu.")
    try:
        songs = list_songs()
        if not songs:
            raise ValueError("Empty seed catalog")
    except (sqlite3.Error, ValueError, OSError):
        st.error("The song catalog is temporarily unavailable. Please try again later.")
        return
    if st.session_state["profile"] is None or st.session_state["editing_profile"]:
        render_profile_form(songs)
        if st.session_state["profile"] is None and not st.session_state["greeting_seen"]:
            show_first_visit_greeting()
        return
    observer = render_activity_panel()
    st.html(ASSETS / "interface_controls.html", unsafe_allow_javascript=True)
    # 8b. Navigation and content are adjacent, without overlay placeholders between them.
    with st.container(key="riffin-workspace", gap="small"):
        st.radio("Explore Riffin’", tuple(VIEW_LABELS), format_func=VIEW_LABELS.__getitem__, horizontal=True,
                 key="view", label_visibility="collapsed")
        if st.session_state.get("action_error"):
            st.error(st.session_state["action_error"])
        view = st.session_state["view"]
        with st.container(key="riffin-page-" + view.lower().replace(" ", "-")):
            if view == "For You":
                render_feed(songs, observer)
            elif view == "Catalog":
                render_catalog(songs)
            elif view == "Library":
                render_library(songs)
            elif view == "Songbook":
                render_chart(observer)
            else:
                # 9. Each rendered source and live node comes from this session's results.
                render_chat(handle_open, handle_save, observer)
    # 10. Every newly opened tab starts at the top; ordinary reruns keep their position.
    if st.session_state.get("last_rendered_view") != view:
        st.session_state["last_rendered_view"] = view
        request = st.session_state.get("page_scroll_request", 0) + 1
        st.session_state["page_scroll_request"] = request
        script = (ASSETS / "scroll_top.html").read_text().replace(
            "__RIFFIN_SCROLL_REQUEST__", str(int(request)),
        )
        st.html(script, unsafe_allow_javascript=True)


if __name__ == "__main__":
    main()
