# Operation handoffs

## Preflight

`preflight.py profile --draft D --sample SOURCE` retains its current output and adds `sample.audio_streams`, `sample.display`, `sample.frame_timing`, and `capabilities` where a plan selects methods. Reports preserve unknown values. The existing plan/checklist approval is still required before production work.

## Exact-master review

`final-render` gains a read-only `inspect --record R --evidence-dir E [--destination NAME]` method. It validates the render record and output SHA-256, reports measured technical candidates, and writes only bounded review evidence. Technical findings do not create package approval.

## Captions

`edit/captions` accepts a reviewed SRT/ASS or timestamped cue file plus a selected destination and font. `inspect` validates source cues and builds bounded evidence. `changes` emits a pending `motion-graphics-ass` operation for the approved timeline. A changed cue/sidecar creates a new timeline revision and approval fingerprint. No caption command runs by default.

## Sync

`source/sync analyze --camera C --recorder M --out-dir E` writes a source-hash-bound offset/drift report and bounded audition. `REVIEW` means the result is not usable for automatic alignment. Permanent alignment has its own validated timeline operation after the supplied manual edit.

## Framing

Existing `clipping.py propose-crop` and `reframe` methods add measurements and guides to their current evidence; they do not change subject selection or approval ownership. Crop changes still emit pending timeline operations.

## Timeline loudness

An approved `loudnorm` operation has a measured target. The renderer computes the resolved audio graph's measurement before final encode, records those values, and uses them in the final graph. `verify` reports exact-output LUFS and dBTP against the approved target.

## Smart cut

`clip-edit` gains an explicitly selected cuts-only candidate command. Compatibility and frame/audio verification are mandatory; any unsupported case returns a typed refusal or a comparison report pointing to the accurate route. It does not become the default clip-edit behavior.

## Retiming

`edit/retime` creates pending finite operations and bounded previews. `timeline.py validate` resolves output times and rejects unsupported input, unbounded repeat, or missing audio policy before approval. The final renderer consumes every approved retime operation in one export.
