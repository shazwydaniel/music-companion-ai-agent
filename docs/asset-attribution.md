# Riffin artwork and mascot

## Artist-created griffin

`griffin.svg` and `griffin.png` are **Griffin symbol** by **Delapouite**, downloaded unchanged from [Game-icons.net](https://game-icons.net/1x1/delapouite/griffin-symbol.html). Licensed under [Creative Commons Attribution 3.0 Unported](https://creativecommons.org/licenses/by/3.0/) ([legal code](https://creativecommons.org/licenses/by/3.0/legalcode)). Copyright remains with the artist. These files are not covered by the repository MIT license.

The icon appears in the artist's source history on **3 March 2019**: [game-icons/icons commit c10320e](https://github.com/game-icons/icons/commit/c10320edc7ae3f28a29d172e0dd3f029411825d7). It is an existing artist-created vector icon, not an AI-generated image. Riffin adds a warm rounded badge and a music-note decoration in CSS/HTML; the downloaded artwork is unchanged. Attribution and license links appear in the app's About disclosure.

## Original decorative assets

The six abstract record/wave SVG illustrations under `art/` and six genre motifs under `stickers/` were drawn in code with AI assistance for Riffin in 2026. These abstract decorations are distinct from the downloaded mascot. They are original project assets, distributed under the repository MIT license. No album covers, reference screenshots or tracking resources are bundled; fonts have their own license below. Fixed genre mappings live in `music_agent/presentation.py`.

## Session animal silhouettes

Downloaded unchanged as black, transparent PNGs from Game-icons.net. These artist-created icons are licensed under [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) and retain their creators' rights, separately from the repository MIT license:

- `avatars/cat.png`: [Cat](https://game-icons.net/1x1/lorc/cat.html), **Lorc**.
- `avatars/fox.png`: [Fox head](https://game-icons.net/1x1/lorc/fox-head.html), **Lorc**.
- `avatars/rabbit.png`: [Rabbit head](https://game-icons.net/1x1/delapouite/rabbit-head.html), **Delapouite**.

Riffin adds the circular pastel backing through CSS. One animal is chosen in Streamlit session state and survives theme changes and ordinary reruns. No animal image generator is used. Credits are accessible through the header's Connection popover.

The current six art SVGs use pastel genre fields, organic blobs, a record motif and music-note shapes. They remain original code-authored decorations with AI assistance, distinct from the licensed artist-created griffin and animal silhouettes. Supplied visual references `IMG_0139.JPG`–`IMG_0142.JPG` remain outside the public repository; no pixels, logos, subscription copy or linked actions are copied from them.

## Poppins typeface

The five unchanged TTF files in [`static/fonts/`](../static/fonts/) are **Poppins** by The Poppins Project Authors, copyright 2020. Downloaded from the [official Google Fonts Poppins directory](https://github.com/google/fonts/tree/main/ofl/poppins): Regular (400), Medium (500), SemiBold (600), Bold (700), and Medium Italic (500). They are served locally by Streamlit for the UI; no Google Fonts stylesheet or font CDN request is needed. The fonts retain their own **SIL Open Font License 1.1**, included verbatim in [`OFL.txt`](../static/fonts/OFL.txt), separately from the repository MIT license.
