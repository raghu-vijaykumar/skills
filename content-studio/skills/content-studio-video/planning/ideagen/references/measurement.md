# Analytics interpretation

Owned channel data comes from YouTube Analytics/Studio. Thumbnail CTR is taken from the owned Studio reach view because the real time Analytics API does not offer that metric in the video report. Capture collection time, period, sample count, source, format, views, impressions CTR for long form when available, Shorts VTR when available, average view duration/percentage, and retention points when available. The `insights` dataset must keep missing values null, never zero. Compare videos within a channel and format, and call out topic, age, and sample-size confounders.

Public comparison data comes only from observable YouTube video fields (title, description, date, duration, views, likes, comments) gathered with source URLs and timestamps. A single snapshot's views per day is a coarse age-normalized indicator, not actual velocity. Do not claim public CTR, VTR, or retention.

Each draft and published source folder records `creative.json`: `themeId`, `styleId`, `renderer`, `format`, and a short list of creative choices such as hook type, caption treatment, and pacing. Compare style cohorts with counts and distribution, and report a recommendation as an experiment. A shared preset changes only after the user approves the experiment and rendered evidence.
