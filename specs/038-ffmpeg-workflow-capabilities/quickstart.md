# Validation guide

Run these commands from `C:\workspace\skills`. The media fixtures use
synthetic inputs in temporary directories. These are development tests, not
human production approvals.

| Story | Focused command | Expected evidence |
| --- | --- | --- |
| 1. Media and method precheck | `python -m unittest discover -s content-studio/skills/content-studio-workflow/tests -p "test_*.py"` | All audio streams, display rotation, timing/VFR uncertainty, source hash, and available/missing/unknown component states. A missing selected component blocks plan approval. |
| 2. Exact master | `python -m unittest discover -s content-studio/skills/content-studio-video/review/final-render/tests -p "test_*.py"` | Known black/freeze/flash/silence candidates are timecoded `REVIEW`; clean moving control avoids forced defects; changed master hash is refused. |
| 3. Requested captions | `python -m unittest discover -s content-studio/skills/content-studio-video/edit/captions/tests -p "test_*.py"` | Exact ASS cue times, font/sidecar hashes, bounded text preview, pending review, and no output without approved precheck. |
| 4. Separate recorder | `python -m unittest discover -s content-studio/skills/content-studio-video/source/sync/tests -p "test_*.py"` | Delayed/drifting fixture yields offset and audition; silence and repeated-pattern ambiguity refuse a confident alignment. |
| 5. Portrait framing | `python -m unittest discover -s content-studio/skills/content-studio-video/edit/clipping/tests -p "test_*.py"` | Source-linked hero crop loss, adjacent crop jump review, no saliency-as-hero substitution, and reviewed timeline handoff. |
| 6. Final mix | `python -m unittest discover -s content-studio/skills/content-studio-video/timeline/tests -p "test_*.py"` | Resolved voice/music mix is measured before one final audio encode; acceptable mix `SKIP`s, a needed fix is measured, and exact-output miss stays `REVIEW`. |
| 7. Guarded smart cut | `python -m unittest discover -s content-studio/skills/content-studio-video/edit/clip-edit/tests -p test_smart_cut.py` | Long-GOP cut between keyframes retains 230 intended frames, byte-identical interior packets, and correlated audio boundary windows; VFR/HDR/incompatible sources refuse. |
| 8. Timeline retime | `python -m unittest discover -s content-studio/skills/content-studio-video/timeline/tests -p test_retime.py` | Speed, freeze, reverse, and finite loop render expected frame order, count, sound treatment, shifted cues, pending-review rejection, and exact-master review samples. |

Finish with:

```powershell
node content-studio/scripts/check-capability-matrices.mjs
npm run check:docs
node --test content-studio/tests/*.test.mjs content-studio/skills/content-studio-video/animation/videogen/tests/*.test.mjs
```

The capability inventory must cover the canonical leaf methods; documentation
links must resolve; the wider Node gate must pass. After tests, inspect the
scoped staged diff, commit the coherent slice on `main`, push, and verify
`origin/main`. For real media, each issue still needs baseline evidence, a
bounded candidate or `SKIP`, human review, and exact-master feedback before
package approval. A passing synthetic fixture cannot approve a draft.
