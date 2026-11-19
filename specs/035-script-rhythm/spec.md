# Feature Specification: Script rhythm for Content Studio

**Created:** 2026-11-18
**Status:** Implemented
**Branch:** `main`

## User scenarios and testing

### US1: Review a vlog or Reel voice script (P1)

An editor drafts evidence-linked voiceover, then sees cue-specific suggestions when several long sentences or repeated openings flatten the spoken cadence. They can retain a necessary explanation, add a purposeful short pivot, or leave the original dialogue and sound uncovered. The report never rewrites approved text or blocks delivery solely for sentence length.

### US2: Review code-driven narration (P2)

An author checks Remotion narration before synthesis and sees phrase-specific suggestions about repetitive cadence. Short videos and long explainers use the same underlying analysis, while a chapter's question, progress, and payoff remain editorial decisions. The performed take is reviewed at normal speed against picture.

## Functional requirements

- FR1: Inspect sentence or phrase word counts across adjacent cues and report runs of similar long lines and repeated openings with stable cue IDs and available source times.
- FR2: Include a near-capacity cue note when an evidence-linked voiceover line leaves little speaking room, without replacing its existing hard pace validation.
- FR3: Keep rhythm observations advisory, separate from structural errors and existing approval status. Neither a missing short line nor a necessary long explanation fails validation.
- FR4: Preserve source text, timing, evidence IDs, natural-sound gaps, and existing cue approval semantics.
- FR5: Apply the same analysis to vlog voiceover and authored code-driven narration before synthesis. A preview-only route must not invoke speech generation.
- FR6: Update drafting and performance-review guidance for short, vlog, and long-form work. The suggested five-word pivot is optional and must carry a narrative purpose.
- FR7: Script-generation prompts explicitly label needed but unconfirmed specifics as `unknown` (including ticket status), and dependent claims are omitted or flagged for review until resolved.

## Success criteria

- A reviewer can identify the cue and relevant sentence pattern for every rhythm note.
- A long-run fixture and a repeated-opening fixture produce notes; varied, bilingual, intentionally silent, and necessary-explanation fixtures remain deliverable.
- A code-driven author can inspect a rhythm report without generating audio.
- Existing voiceover and narration fixtures retain their validation and synthesis behavior.

## Assumptions

- The user's choice is to apply the review to all voice scripts with format-specific editorial guidance.
- The linked Reel supplies an editorial technique, not reusable media or an exact script template.
- Human script, timing, and performed-audio review remain required.
