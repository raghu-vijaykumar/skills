# Feature specification: image themes and character styles

## Scope

Build an independently callable Content Studio image skill. This slice covers visual themes for structured images and illustration styles for original characters. Social content presets, GIF conversion, platform publishing and analytics are deferred.

## User stories

### P1: Compare UI themes on identical content

As a creator, I can view one unchanged example diagram rendered through distinct visual themes, including minimalism, Bento box, glassmorphism and neumorphism, so I can choose a look without confusing theme with topic or content layout.

Acceptance:
- The catalog stores UI treatment information, with no diagram or post format masquerading as a style.
- Every theme has a README, PNG sample and editable SVG generated from the same source card.
- A single gallery README shows every theme together.

### P1: Choose a character illustration style

As a creator, I can compare the same original character in anime and other illustration styles and use the selected style to generate a new character image.

Acceptance:
- Every character style has an individual README and visual sample.
- A reusable prompt helper combines an arbitrary subject brief with the selected style while retaining the brief.
- Character styles are cataloged separately from UI themes.

### P2: Render a reviewed structured image directly

As a creator, I can render a card by specifying its JSON input, UI theme and canvas without first creating a social presets plan.

Acceptance:
- The renderer emits SVG, PNG, a review page and SHA-256 records.
- It validates diagram relationships, chart provenance, optional factual sources and asset rights.
- It requires a separate production precheck and human visual review, and does not publish.

## Non-goals

No presets planner, social platform export, carousel packaging or automatic publication in this slice.
