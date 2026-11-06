# Workflow precheck plan and benchmarks

The draft stores `.content-studio/preflight/system.json`, `plan.json`, `approval.json`, and `checklist.json`. `plan.json` is editable before review. Its `steps` array determines the checklist after approval; each step has an ID, title, route, output, acceptance criterion, and `required` flag. Keep the source and final-render review steps required. Add, reorder or change other steps to match the user's workflow. Do not include passwords or unpublished personal data in the plan.

```powershell
python <workflow-skill>/scripts/preflight.py --folder <draft> profile --sample <video> --planned-minutes 10
python <workflow-skill>/scripts/preflight.py --folder <draft> init --kind edited --goal "..." --input "..." --deliverable "..."
python <workflow-skill>/scripts/preflight.py --folder <draft> review
```

Edit `plan.json` after `init`. If a representative AI preview later measures 2.5 seconds per frame, rerun `profile` with `--ai-seconds-per-frame 2.5`, copy the updated system report into the plan, and present the revised estimate for review. A new `system.json` alone does not update or reapprove the plan.

## Benchmark interpretation

`profile` runs at most two seconds of decode and Lanczos scaling on a representative source, with a 90-second timeout per run. This is a planning probe, not an image-quality result or a sustained encode benchmark. It does not modify the source. The extrapolated decode/Lanczos hours omit writing and encoding; avoid presenting them as delivery time. CPU/GPU thermals, codec, storage speed, frame size and model choice can change sustained throughput. Report the sample and planned used duration alongside every estimate.

AI upscale time is **unknown** until a short model pilot on this machine. Time a representative preview, compute seconds per frame, then rerun `profile` with `--ai-seconds-per-frame`. The existing upscale comparison preview has a three-second minimum and can itself be costly on a slow backend; keep a clear precheck time budget and leave the estimate unknown if a pilot is impractical. Extrapolate over **used** timeline frames, include staging and encode overhead separately, and consider slower sustained throughput. Existing [upscale guidance](../../content-studio-videoedit/references/upscale.md) includes historical 2–12+ hour examples from a specific GPU; these are not machine-specific promises. Prefer source preservation or Lanczos when AI previews do not show a quality-gated improvement. Do not auto-upscale HDR/DV; first decide and review the tone map.

For color, use `enhance analyze` and representative source-linked frames before planning a correction. Compare a bounded candidate with the untouched source; assess temporal consistency and side effects. `SKIP` clean footage. For streaming frame review, use a disposable local preview or a small bounded frame sequence with timestamps, plus saved key frames or a short clip for later verification. A stream alone cannot prove the delivered export.

## Review and execution commands

```powershell
python <skill>/scripts/preflight.py --folder <draft> review
python <skill>/scripts/preflight.py --folder <draft> approve --note "User approved plan and route choices"
python <skill>/scripts/preflight.py --folder <draft> verify --phase start
python <skill>/scripts/preflight.py --folder <draft> set --id S03 --status done --evidence "rough-cut/review.mp4; user reviewed"
python <skill>/scripts/preflight.py --folder <draft> verify --phase complete
```

After a plan edit, `verify` fails until the revised plan is approved. Reapproval resets the step checklist; prior evidence may be reattached only after confirming it still satisfies the revised step.
