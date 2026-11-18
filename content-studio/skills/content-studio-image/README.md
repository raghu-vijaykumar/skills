# Image themes and character styles

A UI theme defines a post's visual language. Content decides the topic and layout. The ten examples below are deliberately different posts; none is a technical architecture diagram. Character art styles are a separate choice, and a genre or mood can be layered onto any of them.

## UI post themes

Each preview uses the maintained [SVG renderer](scripts/render.py) and links to its own README, editable source and example card. These are illustrative concepts that need content review before use.

![Ten different posts in the ten UI themes](post-theme-gallery.png)

| Style | Style | Style |
| --- | --- | --- |
| [![Minimalism](styles/minimalism/sample.png)](styles/minimalism/README.md)<br>**Minimalism** — Make room for one thing | [![Bento box](styles/bento-box/sample.png)](styles/bento-box/README.md)<br>**Bento box** — A good week has room | [![Glassmorphism](styles/glassmorphism/sample.png)](styles/glassmorphism/README.md)<br>**Glassmorphism** — Change the atmosphere |
| [![Neumorphism](styles/neumorphism/sample.png)](styles/neumorphism/README.md)<br>**Neumorphism** — Begin gently | [![Isometric](styles/isometric/sample.png)](styles/isometric/README.md)<br>**Isometric** — Layers of progress | [![Brutalism](styles/brutalism/sample.png)](styles/brutalism/README.md)<br>**Brutalism** — Say it plainly |
| [![Swiss grid](styles/swiss-grid/sample.png)](styles/swiss-grid/README.md)<br>**Swiss grid** — Clarity creates space | [![Editorial](styles/editorial/sample.png)](styles/editorial/README.md)<br>**Editorial** — A note on curiosity | [![Hand drawn](styles/hand-drawn/sample.png)](styles/hand-drawn/README.md)<br>**Hand drawn** — Try, learn, repeat |
| [![Dark glow](styles/dark-glow/sample.png)](styles/dark-glow/README.md)<br>**Dark glow** — What will you build next? |  |  |

## Character styles

This is a broad maintained catalog of 30 rendering treatments, grouped by medium. It does not attempt to name every art style. All portraits use the same [original character brief](examples/character-brief.txt); each image links to an individual README.

![Character style catalog](character-style-gallery.jpg)

### Animation and comics

| Style | Style | Style |
| --- | --- | --- |
| [![Anime](character-styles/anime/sample.png)](character-styles/anime/README.md)<br>**Anime** | [![Manga ink](character-styles/manga-ink/sample.png)](character-styles/manga-ink/README.md)<br>**Manga ink** | [![Chibi](character-styles/chibi/sample.png)](character-styles/chibi/README.md)<br>**Chibi** |
| [![Comic ink](character-styles/comic-ink/sample.png)](character-styles/comic-ink/README.md)<br>**Comic ink** | [![Graphic novel](character-styles/graphic-novel/sample.png)](character-styles/graphic-novel/README.md)<br>**Graphic novel** | [![Storybook](character-styles/storybook/sample.png)](character-styles/storybook/README.md)<br>**Storybook** |

### Digital illustration

| Style | Style | Style |
| --- | --- | --- |
| [![Flat vector](character-styles/flat-vector/sample.png)](character-styles/flat-vector/README.md)<br>**Flat vector** | [![Pixel art](character-styles/pixel-art/sample.png)](character-styles/pixel-art/README.md)<br>**Pixel art** |  |

### Drawing

| Style | Style | Style |
| --- | --- | --- |
| [![Line art](character-styles/line-art/sample.png)](character-styles/line-art/README.md)<br>**Line art** | [![Pencil sketch](character-styles/pencil-sketch/sample.png)](character-styles/pencil-sketch/README.md)<br>**Pencil sketch** | [![Charcoal](character-styles/charcoal/sample.png)](character-styles/charcoal/README.md)<br>**Charcoal** |

### Painting

| Style | Style | Style |
| --- | --- | --- |
| [![Watercolor](character-styles/watercolor/sample.png)](character-styles/watercolor/README.md)<br>**Watercolor** | [![Gouache](character-styles/gouache/sample.png)](character-styles/gouache/README.md)<br>**Gouache** | [![Oil painting](character-styles/oil-painting/sample.png)](character-styles/oil-painting/README.md)<br>**Oil painting** |
| [![Soft pastel](character-styles/soft-pastel/sample.png)](character-styles/soft-pastel/README.md)<br>**Soft pastel** | [![Ink wash](character-styles/ink-wash/sample.png)](character-styles/ink-wash/README.md)<br>**Ink wash** |  |

### Printmaking

| Style | Style | Style |
| --- | --- | --- |
| [![Risograph](character-styles/risograph/sample.png)](character-styles/risograph/README.md)<br>**Risograph** | [![Woodcut](character-styles/woodcut/sample.png)](character-styles/woodcut/README.md)<br>**Woodcut** | [![Screen print](character-styles/screen-print/sample.png)](character-styles/screen-print/README.md)<br>**Screen print** |
| [![Pop art](character-styles/pop-art/sample.png)](character-styles/pop-art/README.md)<br>**Pop art** |  |  |

### Decorative art

| Style | Style | Style |
| --- | --- | --- |
| [![Art Nouveau](character-styles/art-nouveau/sample.png)](character-styles/art-nouveau/README.md)<br>**Art Nouveau** | [![Art Deco](character-styles/art-deco/sample.png)](character-styles/art-deco/README.md)<br>**Art Deco** |  |

### Mixed media

| Style | Style | Style |
| --- | --- | --- |
| [![Editorial collage](character-styles/editorial-collage/sample.png)](character-styles/editorial-collage/README.md)<br>**Editorial collage** | [![Paper cut](character-styles/paper-cut/sample.png)](character-styles/paper-cut/README.md)<br>**Paper cut** |  |

### Dimensional art

| Style | Style | Style |
| --- | --- | --- |
| [![3D animation](character-styles/3d-animation/sample.png)](character-styles/3d-animation/README.md)<br>**3D animation** | [![Low-poly 3D](character-styles/low-poly-3d/sample.png)](character-styles/low-poly-3d/README.md)<br>**Low-poly 3D** | [![Claymation](character-styles/claymation/sample.png)](character-styles/claymation/README.md)<br>**Claymation** |

### Photography

| Style | Style | Style |
| --- | --- | --- |
| [![Photorealistic](character-styles/photorealistic/sample.png)](character-styles/photorealistic/README.md)<br>**Photorealistic** | [![Cinematic portrait](character-styles/cinematic-portrait/sample.png)](character-styles/cinematic-portrait/README.md)<br>**Cinematic portrait** | [![Fashion editorial](character-styles/fashion-editorial/sample.png)](character-styles/fashion-editorial/README.md)<br>**Fashion editorial** |

Rebuild the README galleries with `python content-studio/skills/content-studio-image/scripts/build_gallery.py`. Create a new character prompt with [character_prompt.py](scripts/character_prompt.py). Use [render.py](scripts/render.py) to render your own reviewed post card with a chosen UI theme.
