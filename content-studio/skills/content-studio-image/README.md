# Image themes and character styles

Choose a UI theme for diagrams, information cards or other structured content. Choose a character style when generating an illustrated person. These are separate decisions from content layout, topic and platform size.

## UI themes: one diagram, ten treatments

Every sample below renders the exact same [request-flow content](examples/request-flow.json). Only its UI theme changes. Click an image to open its individual README and editable SVG.

![Ten UI themes on the same diagram](themes-comparison.png)

| Theme | Theme | Theme |
| --- | --- | --- |
| [![Minimalism](styles/minimalism/sample.png)](styles/minimalism/README.md)<br>**Minimalism** | [![Bento box](styles/bento-box/sample.png)](styles/bento-box/README.md)<br>**Bento box** | [![Glassmorphism](styles/glassmorphism/sample.png)](styles/glassmorphism/README.md)<br>**Glassmorphism** |
| [![Neumorphism](styles/neumorphism/sample.png)](styles/neumorphism/README.md)<br>**Neumorphism** | [![Isometric](styles/isometric/sample.png)](styles/isometric/README.md)<br>**Isometric** | [![Brutalism](styles/brutalism/sample.png)](styles/brutalism/README.md)<br>**Brutalism** |
| [![Swiss grid](styles/swiss-grid/sample.png)](styles/swiss-grid/README.md)<br>**Swiss grid** | [![Editorial](styles/editorial/sample.png)](styles/editorial/README.md)<br>**Editorial** | [![Hand drawn](styles/hand-drawn/sample.png)](styles/hand-drawn/README.md)<br>**Hand drawn** |
| [![Dark glow](styles/dark-glow/sample.png)](styles/dark-glow/README.md)<br>**Dark glow** |  |  |

## Character image styles: one person, six treatments

Each sample uses the same [character brief](examples/character-brief.txt). Click an image for the individual style README.

| Style | Style | Style |
| --- | --- | --- |
| [![Anime](character-styles/anime/sample.png)](character-styles/anime/README.md)<br>**Anime** | [![Watercolor](character-styles/watercolor/sample.png)](character-styles/watercolor/README.md)<br>**Watercolor** | [![Comic ink](character-styles/comic-ink/sample.png)](character-styles/comic-ink/README.md)<br>**Comic ink** |
| [![3D animation](character-styles/3d-animation/sample.png)](character-styles/3d-animation/README.md)<br>**3D animation** | [![Pixel art](character-styles/pixel-art/sample.png)](character-styles/pixel-art/README.md)<br>**Pixel art** | [![Editorial collage](character-styles/editorial-collage/sample.png)](character-styles/editorial-collage/README.md)<br>**Editorial collage** |

Render the common diagram with `python content-studio/skills/content-studio-image/scripts/render.py render --input content-studio/skills/content-studio-image/examples/request-flow.json --style bento-box --output tmp/image-bento`. Rebuild the gallery with `python content-studio/skills/content-studio-image/scripts/build_gallery.py`.
