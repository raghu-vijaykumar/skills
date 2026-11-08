# Research: Existing pipeline and single-render route

## Decision: Keep the workflow precheck as the first approval

The existing `content-studio-workflow` plan includes exact methods and commands and binds approval to plan bytes. Retain it. Add a second approval for the resolved timeline, voice assets, effects, and render settings. A changed plan or timeline invalidates the relevant approval.

## Decision: Use a new delivery timeline contract

The AutoCut timeline is a rough-cut artifact whose renderer encodes clip segments and concatenates them. The transition skill's annotation targets the separate edit-timeline report, not that renderer. A delivery timeline can accept manual exports as a source clip or import an AutoCut edit without changing the current raw-footage default.

## Decision: Compile one final output graph

Represent approved operations as typed spans with explicit ordering and track identity. Resolve cuts and overlaps before approval. Split the graph at all effect boundaries so temporal filters do not leak across an unselected span. Combine picture and sound in a single final export. A bounded preview or temporary AI frame cache is acceptable if it does not become a full-length enhancement master.

## Decision: Fail before encode on unsupported methods

The current specialist methods include output-producing scripts, some without graph adapters. Timeline validation needs a capability registry with clear support status. A new effect is supported only after schema, adapter, review, exact-final verification, and tests exist. A registry entry alone cannot authorize rendering.

## Alternatives considered

- Chain existing specialist MP4 outputs: rejected because it re-encodes or remuxes after each operation and breaks the user's single-render requirement.
- Expand the AutoCut renderer in place: rejected because its rough-cut review lifecycle and segment cache precede final timeline approval and do not cover current audio/voice paths.
- Use post-export cue sheets as the timeline: rejected because they omit source cuts, overlapping transitions, and exact asset/approval binding.
