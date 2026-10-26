# Themes and styles

`videogen.config.ts` supplies a theme and an array of content styles. `neutralTheme` is suitable for a new project; `reviseLabsTheme` is an opt-in compatibility preset. Use `defineTheme` and `defineContentStyle` from the package to register new identities without editing toolkit code.

`videogen init <directory>` scaffolds the neutral theme. `videogen init <directory> --theme revise-labs` selects the compatibility preset and copies its self-hosted fonts to `public/fonts/`.

A theme owns brand, palette, font stacks, typography minimums, and screen bands. A style owns the editorial format contract. A project owns its actual art direction, scene components, and assets. Exported content cards receive the selected theme and style name through Remotion props.
