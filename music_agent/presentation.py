"""Escaped HTML for original decoration and space-preserving chart content."""

# 1. Only fixed genre keys resolve local artwork; there are no user-supplied URLs.
import base64
from html import escape
from pathlib import Path

from db import validate_content
from music_agent import DISPLAY_NAME

ASSETS = Path(__file__).resolve().parents[1] / "assets"
GENRE_ASSETS = {
    "Rock": "rock", "Pop": "pop", "Jazz": "jazz", "Indie / Folk": "folk",
    "Electronic": "electronic", "Classical": "classical",
}
GENRE_COLORS = {
    "Rock": ("#F4CEB8", "#E87952"), "Pop": ("#F2D6E2", "#DD83AB"),
    "Jazz": ("#F2E3B0", "#CAA24F"), "Indie / Folk": ("#D9E5C8", "#88AC92"),
    "Electronic": ("#DED2F3", "#A38ADD"), "Classical": ("#D8DEFA", "#91A4E0"),
}
VIEW_LABELS = {
    "For You": ":material/auto_awesome: For You",
    "Catalog": ":material/library_music: Browse Songs",
    "Library": ":material/bookmarks: Saved & Recent",
    "Songbook": ":material/music_note: Chords & Lyrics",
    "Chat": ":material/forum: Chat",
}


def _image(path: Path) -> str:
    """Embed approved local SVGs, with an original local fallback if missing."""
    fallback = (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 440">'
        b'<path fill="#88AC92" d="M0 0h800v440H0z"/></svg>'
    )
    content = path.read_bytes() if path.is_file() else fallback
    return "data:image/svg+xml;base64," + base64.b64encode(content).decode("ascii")


# 2. Decorative images are hidden from assistive technology and never clickable.
def artwork_html(genre: str, featured: bool = False, sticker_genre: str | None = None) -> str:
    """Render approved artwork and an optional primary-genre border sticker."""
    key = GENRE_ASSETS.get(genre, "folk")
    sticker = ""
    if featured:
        sticker_key = GENRE_ASSETS.get(sticker_genre or genre, "folk")
        sticker = f'<img class="riffin-sticker" src="{_image(ASSETS / "stickers" / f"{sticker_key}.svg")}" alt="">'
    return (
        f'<div class="riffin-art {"featured" if featured else ""}" aria-hidden="true">'
        f'<img class="riffin-cover" src="{_image(ASSETS / "art" / f"{key}.svg")}" alt="">{sticker}</div>'
    )


def brand_html(genre: str = "Pop") -> str:
    """Present the licensed artist's griffin with a fixed genre border sticker."""
    sticker_key = GENRE_ASSETS.get(genre, "pop")
    return (
        '<div class="riffin-brand">'
        f'<span class="riffin-mascot"><img src="{_image(ASSETS / "griffin.svg")}" '
        'alt="Riffin the griffin"><span aria-hidden="true">♪</span></span>'
        f'<div><h1>{DISPLAY_NAME}</h1><p><span>A bandmate</span> <span>in your browser.</span></p></div>'
        f'<img class="brand-sticker" src="{_image(ASSETS / "stickers" / f"{sticker_key}.svg")}" '
        'alt="" aria-hidden="true"></div>'
    )


def greeting_mascot_html() -> str:
    """Reuse the licensed griffin and music-note badge in the first-visit greeting."""
    return (
        '<div class="riffin-greeting-mascot">'
        f'<span class="riffin-mascot greeting"><img src="{_image(ASSETS / "griffin.svg")}" '
        'alt="Riffin the griffin"><span aria-hidden="true">♪</span></span></div>'
    )


def profile_pills_html(profile: dict) -> str:
    """Escape personal text and give each profile detail a distinct labeled pill."""
    fields = (("nickname", "You"), ("instrument", "Instrument"), ("skill_level", "Level"))
    return '<div class="riffin-profile-pills" aria-label="Your playing preferences">' + ''.join(
        f'<span class="profile-pill {key}"><span class="pill-label">{label} :</span>'
        f'<strong>{escape(profile[key])}</strong></span>' for key, label in fields
    ) + '</div>'


def metadata_tags_html(items: list[tuple[str, str | int | float | None]]) -> str:
    """Render escaped label/value qualities consistently across app views."""
    return '<div class="riffin-meta-tags">' + ''.join(
        f'<span class="meta-tag"><span>{escape(label)} :</span> <strong>{escape(str(value))}</strong></span>'
        for label, value in items if value is not None and str(value) != ""
    ) + '</div>'


def genre_frame_html(genre: str) -> str:
    """Attach only fixed, noninteractive genre accents to the viewport edges."""
    pastel, accent = GENRE_COLORS.get(genre, GENRE_COLORS["Pop"])
    key = GENRE_ASSETS.get(genre, "pop")
    return (f'<div class="riffin-genre-frame genre-{key}" style="--genre-pastel:{pastel};--genre-accent:{accent}" '
            'aria-hidden="true"><span class="border-blob first"></span><span class="border-blob second"></span>'
            '<span class="border-dot one"></span><span class="border-dot two"></span></div>')


def welcome_html() -> str:
    """Use downloaded human-created art, never generated mascot artwork."""
    return (
        '<div class="riffin-welcome">'
        f'<span class="riffin-mascot large"><img src="{_image(ASSETS / "griffin.svg")}" '
        'alt="Riffin, your music griffin"><span aria-hidden="true">♫</span></span>'
        '<div><p class="eyebrow">SMALL STEPS. GOOD RIFFS.</p>'
        '<h3>Let’s find your groove.</h3>'
        '<p>A tricky chord? A song you love? I’m all ears.</p></div></div>'
    )


# 3. All catalog strings are escaped, and chord/lyric spaces remain identical.
def chart_section_html(section: dict) -> str:
    """Render one validated section with a keyboard-scrollable, labelled region."""
    validate_content([section])
    lines = []
    for line in section["lines"]:
        lines.append(f'<span class="chords">{escape(line["chords"])}</span>')
        if "lyrics" in line:
            lines.append(escape(line["lyrics"]))
        lines.append("")
    return (
        '<div class="riffin-chart" tabindex="0" role="region" '
        f'aria-label="{escape(section["name"], quote=True)} chart">'
        '<pre>' + "\n".join(lines) + '</pre></div>'
    )
