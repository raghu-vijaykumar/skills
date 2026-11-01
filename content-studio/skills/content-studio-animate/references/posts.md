# Carousel and post workflow

One content package can own video, carousel, and post editions. The package YAML selects a registered style, declares its source manifest, and describes each card. Source assets stay in the project's runtime cache; commit provenance and metadata.

Use `videogen content-check <id>` before export. Media cards need a registered evidence asset, attribution, sufficient resolution, and an excerpt inside the source duration. `videogen content-render <id> --format all` exports PNG stills, GIFs, or MP4s according to card kind and writes a manifest and captions. Inspect every exported card and clip at its actual output size. The project may register additional evidence checks in `videogen.config.ts`.
