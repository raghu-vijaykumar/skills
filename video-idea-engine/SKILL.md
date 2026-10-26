---
name: video-idea-engine
description: Turn a channel analytics dataset into a researched, packaged video idea and a production brief for a short or long video. Use when asked to come up with a new video idea, find a fresh topic from recent papers/blogs/news, plan a video that reaches more people, or turn channel insights into the next upload.
---

# video-idea-engine

A repeatable path from *measured channel data* to *one researched idea* to *a brief you can
produce*. It works with the [content-helper](../content-helper/SKILL.md) workspace and its
`analytics/insights.json` dataset.

No step may be skipped, and no step may invent numbers. If a source is not fetched in this
session, it does not exist for the purposes of the brief.

## Honest framing

Nothing here guarantees a viral video. Reach is decided by YouTube after upload, using
signals this skill cannot control. What this skill does is maximise the probability of
passing each measurable gate, and refuse ideas that fail them:

| gate | short | long | where it comes from |
| --- | --- | --- | --- |
| demand | search/feed interest exists now | same | research sweep |
| entry | VTR >= 50% | CTR >= 4% | audience choice in the first 2s / thumbnail |
| retention | avg % >= 55 | avg % >= 40 | the mechanism, not the edit |
| follow | viewers want the next one | same | a series promise, not a plea |

Thresholds are working targets from the channel's own dataset, not platform rules. Re-read
the dataset each run: when the channel moves, the targets move.

## Step 0 - load the prior

```powershell
python scripts/content.py insights --channel <slug>
```

Read `content/<slug>/analytics/insights.json` and `dataset.csv`. Extract and write down:

- `numbers`: median views, median average %, median VTR, subscribers per 1k views
- `correlations`: which gate currently tracks views
- `topic_lanes`: lanes sorted by median views, and lanes with high VTR but few uploads
- `duration_bands`: the band with the best combination of views and average %
- `videos[]`: the five best and five worst entries, and for each, VTR, avg %, duration

Then state, in one sentence each: what currently wins, what loses, and which gate is
weakest. If the dataset is older than two weeks, refresh it first.

If a channel has fewer than 15 videos, treat every comparison as a hint, not a fact, and
say so in the brief.

## Step 1 - research sweep

Goal: 8-12 candidate mechanisms, all sourced within this session, with dates.

Sources, in priority order:

1. Primary papers: `arxiv.org` (cs.AI, cs.LG, cs.DC, cs.CR, cs.PL, physics), conference
   proceedings, standards documents (RFCs, W3C), official specifications.
2. Engineering blogs from teams that ship the thing: Netflix, Google, Meta, Cloudflare,
   Figma, Uber, AWS, Stripe, Airbnb, Discord, Shopify, Microsoft Research.
3. Changelogs and release notes of tools the audience uses; security advisories.
4. Hacker News front page and Lobsters for what engineers are arguing about this week.
5. Reputable explainers only to locate the primary source, never as the source itself.

For each candidate record: source URL, publication date, the mechanism in one sentence,
one number that makes it concrete, and why it is timely (new paper, new product, new
incident, new version).

Reject anything you cannot explain with a mechanism, and anything whose only interest is
"a product launched". Reject claims you cannot verify from the primary source.

## Step 2 - score the candidates

Copy [templates/scorecard.md](templates/scorecard.md) and score every candidate 0-2 on:

| criterion | 0 | 1 | 2 |
| --- | --- | --- | --- |
| demand | niche within niche | one community cares | many engineers/students search or argue about it |
| surprise | expected | mildly interesting | contradicts a belief the viewer holds |
| mechanism | a list of facts | a chain, but abstract | a visible cause-and-effect that can be drawn |
| proof | no real values | some values | exact numbers, code, state transitions |
| visual | nothing to show | diagrams needed | a hero shot that shows the mechanism move |
| packaging | no honest title | a decent title | a title and thumbnail that promise the surprise |
| fit | off-lane | adjacent | sits in a lane the channel already converts |
| effort | weeks | a few days | one focused session |

Gate: `demand >= 1`, `mechanism >= 2`, `proof >= 2`, `packaging >= 1`, `fit >= 1`,
total >= 12. If nothing passes, research again; do not lower the bar.

Pick one. Write the reason it beat the runner-up in one paragraph, with the scores.

## Step 3 - the promise and the shape

Write exactly one sentence: *"By the end, the viewer will be able to ____."* If the
sentence needs "and", the idea is two videos.

Then pick a runtime from the dataset:

| intent | runtime | evidence to use |
| --- | --- | --- |
| short | 35-60 s | the best `duration_bands` row for shorts; 24 s only if the mechanism is one beat |
| long | 5-9 min | only if the mechanism needs three or more acts; long lanes are judged on CTR, not VTR |

Write the beat sheet in the brief: 5-8 beats for a short, 12-20 for a long. Each beat gets
one line of narration, the visual that proves it, and the exact value shown. A beat with no
visual is a beat to cut.

## Step 4 - package before producing

Five titles, each in a pattern the channel already converts: `How X actually works`,
`Why X (counterintuitive claim)`, `The trick to X`, `What happens inside X`, `X explained`.
Every title must be true and specific. No "you won't believe", no fake stakes, no
withheld noun.

Three thumbnail concepts described as what the eye sees at 120 px: one object, one
mechanism cue, at most four words. The thumbnail shows the mechanism, not the presenter.

Pick one title and one thumbnail; record the runner-up and why it lost. This is the entry
gate, so it is decided before any production work.

## Step 5 - production

Use the workspace, do not invent a second one:

```powershell
python scripts/content.py draft new --channel <slug> --name "<idea>"
```

Then fill the draft:

- `brief.md` - promise, beats, hero shots, values, runtime, source links
- `research.md` - the sweep and scorecard
- `packaging.md` - titles, thumbnail concepts, chosen pair
- `src/` (code-generated channels) or `original-videos/` (edited) for the raw material
- `video.mp4`, `thumbnail.png`, `title.txt`, `description.txt` when produced
- `intro` applies the channel intro when the channel uses one

Verification is not optional:

```powershell
python scripts/content.py media segment --channel <slug> --draft "<idea>" --start 0:00 --end 0:12 --count 6
```

Inspect the frames for the hook and each hero shot, and read the audio for the first
sentence. Fix anything that does not read at a glance before publishing.

## Step 6 - publish, then close the loop

Publish through the channel's normal path, then:

1. After 48 hours run `insights` again with VTR collection and compare this video against
   the dataset medians.
2. Record in the draft's `measurement.md`: VTR, avg %, views, subs, and which gate failed if
   the video underperformed.
3. If the idea won, write the reusable part into the lane notes so the next brief starts
   from it. If it lost, say which step of this guide produced the wrong assumption.

A video that underperforms is not a failure of effort; it is a measurement. It only becomes
a failure if the next brief ignores it.

## Anti-patterns

- Deciding the topic before reading the dataset, then using the data to justify it.
- A topic whose appeal is the news, with no mechanism underneath.
- A mechanism shown only in narration while the visual shows a rectangle.
- Retention padded with loops instead of fixing the entry.
- "Viral" titles that promise something the video does not deliver.
- Producing before packaging is chosen.
- Reporting a metric you did not fetch.
