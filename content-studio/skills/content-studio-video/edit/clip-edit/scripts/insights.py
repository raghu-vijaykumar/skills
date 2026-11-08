"""Collect a channel dataset, analyse it, and propose next content."""

from __future__ import annotations

import csv
import json
import re
import statistics
import time
from pathlib import Path

import analytics
import studio
from common import Log, channel_path, channel_root, channel_settings, human_size, now, read_json, write_json

STOP = set("""how what why does do the a an of to in on for with and or that this your you it
is are was were can could will would actually really explained explain works work working into
from at as by be been being its it's there here about when where which who whom whose than then
them they these those one two not no yes all any more most some such only own same so too very
just also still even ever never make makes made get gets got use used using new best top vs
many one ones two three four five six seven eight nine ten lots lot much little few several
each every most more less entire whole thing things stuff kind sort type way ways
big small large long short high low good bad great huge tiny simple easy hard complex
true false real actually literally basically pretty quite very really
""".split())

PATTERNS = [("how", r"\bhow\b"), ("why", r"\bwhy\b"), ("what", r"\bwhat\b"),
            ("trick", r"\btrick\b"), ("inside", r"\binside\b"),
            ("explained", r"\bexplained\b"), ("vs", r"\bvs\b")]

ACRONYMS = {"ai": "AI", "llm": "LLMs", "gpu": "GPUs", "cpu": "CPUs", "api": "API",
            "rag": "RAG", "cdn": "CDN", "jwt": "JWT", "oauth": "OAuth", "rsa": "RSA",
            "bfs": "BFS", "dfs": "DFS", "sql": "SQL", "http": "HTTP", "url": "URL",
            "tcp": "TCP", "ip": "IP", "dns": "DNS", "pki": "PKI", "rag": "RAG",
            "npu": "NPU", "ssd": "SSD", "ram": "RAM", "nfts": "NFTs"}


def label(token: str) -> str:
    return ACRONYMS.get(token, token.capitalize())


def tokens(title: str) -> list[str]:
    words = re.findall(r"[a-z][a-z0-9'-]{2,}", title.lower())
    return [w for w in words if w not in STOP]


def pattern(title: str) -> str:
    lower = title.lower()
    for name, regex in PATTERNS:
        if re.search(regex, lower):
            return name
    return "other"


def median(values: list[float]) -> float:
    values = [v for v in values if isinstance(v, (int, float))]
    return statistics.median(values) if values else 0.0


def pearson(pairs: list[tuple[float, float]]) -> float:
    pairs = [(x, y) for x, y in pairs if isinstance(x, (int, float)) and isinstance(y, (int, float))]
    if len(pairs) < 3:
        return 0.0
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    num = sum((x - mx) * (y - my) for x, y in pairs)
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return round(num / den, 2) if den else 0.0


def cache_paths(root: Path, vid: str) -> tuple[Path, Path]:
    return channel_path(root, "analytics") / vid / "metrics.json", channel_path(root, "analytics") / "vtr" / f"{vid}.json"


def cached_metrics(root: Path, vid: str, max_age_hours: float = 12) -> dict:
    path = channel_path(root, "analytics") / vid / "metrics.json"
    if not path.exists():
        return {}
    if (time.time() - path.stat().st_mtime) / 3600 > max_age_hours:
        return {}
    return read_json(path).get("metrics") or {}


def fetch_api(cfg: dict, settings: dict, root: Path, videos: list[dict], refresh: bool,
              log: Log, reauthorize: bool = False) -> dict:
    client = analytics.ApiClient(settings, log, reauthorize=reauthorize)
    out = {}
    for video in videos:
        cached = {} if refresh else cached_metrics(root, video["id"])
        if cached:
            out[video["id"]] = cached
            continue
        filters = f"video=={video['id']}"
        base = {"ids": f"channel=={settings['channel_id']}", "startDate": video["upload_date"],
                "endDate": time.strftime("%Y-%m-%d"), "dimensions": "video", "filters": filters}
        metrics = {}
        try:
            metrics.update(analytics.rows_to_dict(client.report(
                metrics="views,estimatedMinutesWatched,averageViewDuration,"
                        "averageViewPercentage,likes,comments,shares,subscribersGained",
                **base)))
        except SystemExit as exc:
            log(f"{video['id']}: metrics skipped ({exc})")
        # Reach CTR is read from owned Studio data below; the Analytics API does
        # not expose video thumbnail impressions or their CTR in this report.
        if metrics:
            keep = read_json(channel_path(root, "analytics") / video["id"] / "metrics.json")
            keep.setdefault("video", {"id": video["id"], "title": video["title"],
                                      "kind": video["kind"], "duration": video["duration"],
                                      "upload_date": video["upload_date"]})
            keep["metrics"] = metrics
            keep.setdefault("source", "api")
            write_json(channel_path(root, "analytics") / video["id"] / "metrics.json", keep)
        out[video["id"]] = metrics
        log(f"{video['id']}: {metrics.get('views', 'no data')} views")
    return out


def load_cached_vtr(root: Path, videos: list[dict]) -> dict:
    values = {}
    for video in videos:
        _, path = cache_paths(root, video["id"])
        if path.exists():
            data = read_json(path)
            if isinstance(data.get("vtr"), (int, float)):
                values[video["id"]] = data["vtr"]
    return values


def fetch_studio_reach(cfg: dict, settings: dict, root: Path, videos: list[dict], limit: int,
                       refresh: bool, log: Log) -> tuple[dict, dict]:
    """Collect private Shorts VTR and long-form thumbnail CTR from owned Studio.

    Studio data is best effort and may be unavailable for a new video or an
    account without access. Missing fields stay null in the idea dataset.
    """
    selected = [v for v in videos if v["kind"] == "shorts"][:limit]
    selected += [v for v in videos if v["kind"] == "long"][:limit]
    vtr: dict[str, float] = {}
    reach: dict[str, dict] = {}
    pending = []
    for video in selected:
        _, vtr_path = cache_paths(root, video["id"])
        reach_path = channel_path(root, "analytics") / "reach" / f"{video['id']}.json"
        cached = read_json(vtr_path) if vtr_path.exists() and not refresh else {}
        cached_reach = read_json(reach_path) if reach_path.exists() and not refresh else {}
        if isinstance(cached.get("vtr"), (int, float)):
            vtr[video["id"]] = cached["vtr"]
        if isinstance(cached_reach.get("ctr"), (int, float)):
            reach[video["id"]] = {"impressionsClickThroughRate": cached_reach["ctr"],
                                   "impressions": cached_reach.get("impressions")}
        if video["kind"] == "shorts" and video["id"] in vtr or video["kind"] == "long" and video["id"] in reach:
            continue
        pending.append(video)
    if not pending:
        return vtr, reach
    port = int(cfg["browserDebugPort"])
    browser = settings["browser"]
    if not studio.launch(browser, port, log):
        log("browser session unavailable; private Studio reach skipped")
        return vtr, reach
    if not studio.channel_accessible(port, settings["channel_id"], log):
        studio.stop(browser, log)
        return vtr, reach
    try:
        for video in pending:
            tab = "tab-content" if video["kind"] == "shorts" else "tab-reach"
            url = f"https://studio.youtube.com/video/{video['id']}/analytics/{tab}/period-default"
            payloads = studio.harvest_json(port, url, ("metricTotals",), log)
            _, values = analytics.extract_points(payloads)
            if not values:
                payloads = studio.harvest_json(port, url, ("metricTotals",), log, wait=25)
                _, values = analytics.extract_points(payloads)
            seen_vtr = values.get("shortsFeedImpressionsVtr")
            if isinstance(seen_vtr, (int, float)):
                vtr[video["id"]] = seen_vtr
                _, cache = cache_paths(root, video["id"])
                write_json(cache, {"vtr": seen_vtr, "fetched": now(), "source": "owned Studio"})
            seen_ctr = values.get("impressionsClickThroughRate")
            if isinstance(seen_ctr, (int, float)):
                reach[video["id"]] = {"impressionsClickThroughRate": seen_ctr,
                                      "impressions": values.get("impressions")}
                cache = channel_path(root, "analytics") / "reach" / f"{video['id']}.json"
                write_json(cache, {"ctr": seen_ctr, "impressions": values.get("impressions"),
                                   "fetched": now(), "source": "owned Studio reach"})
            if video["kind"] == "long" and video["id"] not in reach:
                log(f"{video['id']}: thumbnail CTR unavailable in owned Studio response")
    finally:
        studio.stop(browser, log)
    return vtr, reach


def retention_summary(points: list[dict]) -> dict:
    if not points:
        return {}
    return {"at25": analytics.at(points, 0.25), "at50": analytics.at(points, 0.5),
            "at75": analytics.at(points, 0.75), "drop": analytics.biggest_drop(points)}


def build_rows(videos: list[dict], metrics: dict, vtr: dict) -> list[dict]:
    rows = []
    for video in videos:
        m = metrics.get(video["id"]) or {}
        folder = video["folder"] / "retention.csv"
        points = []
        if folder.exists():
            with folder.open(encoding="utf-8") as fh:
                for line in csv.DictReader(fh):
                    points.append({"position": float(line["position"]),
                                   "watch_ratio": float(line["watch_ratio"])})
        summary = retention_summary(points)
        drop = summary.get("drop")
        creative_file = video["folder"] / "creative.json"
        creative = read_json(creative_file) if creative_file.exists() else {}
        rows.append({
            "id": video["id"], "kind": video["kind"], "title": video["title"],
            "theme_id": creative.get("themeId"), "style_id": creative.get("styleId"),
            "renderer": creative.get("renderer"), "creative_choices": creative.get("choices", []),
            "upload_date": video["upload_date"], "duration": video["duration"],
            "views": m.get("views"), "watch_minutes": m.get("estimatedMinutesWatched"),
            "avg_view_sec": m.get("averageViewDuration"),
            "avg_pct": m.get("averageViewPercentage"),
            "impressions": m.get("impressions"),
            "ctr": m.get("impressionsClickThroughRate"),
            "vtr": vtr.get(video["id"]),
            "subs": m.get("subscribersGained"), "likes": m.get("likes"),
            "comments": m.get("comments"), "shares": m.get("shares"),
            "at25": summary.get("at25"), "at50": summary.get("at50"),
            "at75": summary.get("at75"),
            "biggest_drop_at": drop[0] if drop else None,
            "biggest_drop": drop[1] if drop else None,
            "pattern": pattern(video["title"]), "title_len": len(video["title"]),
            "tokens": tokens(video["title"]),
        })
    rows.sort(key=lambda r: (r["upload_date"], r["id"]))
    return rows


def write_dataset(rows: list[dict], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    fields = ["id", "kind", "title", "upload_date", "duration", "views", "watch_minutes",
              "avg_view_sec", "avg_pct", "impressions", "ctr", "vtr", "subs", "likes", "comments", "shares",
              "at25", "at50", "at75", "biggest_drop_at", "biggest_drop",
              "pattern", "title_len", "theme_id", "style_id", "renderer"]
    with (out / "dataset.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    write_json(out / "dataset.json", rows)


def cluster_stats(rows: list[dict]) -> list[dict]:
    by_token: dict[str, list[dict]] = {}
    for row in rows:
        for token in set(row["tokens"]):
            by_token.setdefault(token, []).append(row)
    clusters = []
    for token, members in by_token.items():
        if len(members) < 3:
            continue
        views = [m["views"] for m in members if m["views"]]
        pcts = [m["avg_pct"] for m in members if m["avg_pct"] is not None]
        vtrs = [m["vtr"] for m in members if m["vtr"] is not None]
        clusters.append({"token": token, "n": len(members),
                         "views": median(views), "avg_pct": median(pcts) if pcts else None,
                         "vtr": median(vtrs) if vtrs else None,
                         "best": max(members, key=lambda m: m["views"] or 0)["title"]})
    clusters.sort(key=lambda c: (c["views"] or 0), reverse=True)
    return clusters


def duration_bands(rows: list[dict]) -> list[dict]:
    bands = {"<40s": (0, 40), "40-60s": (40, 60), "60-120s": (60, 120), ">120s": (120, 10**6)}
    result = []
    for name, (low, high) in bands.items():
        members = [r for r in rows if low <= (r["duration"] or 0) < high]
        if not members:
            continue
        result.append({"band": name, "n": len(members),
                       "views": median([m["views"] for m in members if m["views"]]),
                       "avg_pct": median([m["avg_pct"] for m in members
                                          if m["avg_pct"] is not None]) or None,
                       "vtr": median([m["vtr"] for m in members if m["vtr"] is not None])})
    return result


def weekday_stats(rows: list[dict]) -> list[dict]:
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    buckets: dict[int, list[dict]] = {}
    for row in rows:
        try:
            day = time.strptime(row["upload_date"][:10], "%Y-%m-%d").tm_wday
        except ValueError:
            continue
        buckets.setdefault(day, []).append(row)
    return [{"day": names[day], "n": len(members),
             "views": median([m["views"] for m in members if m["views"]])}
            for day, members in sorted(buckets.items())]


def style_cohorts(rows: list[dict]) -> list[dict]:
    """Describe comparable style groups; interpretation remains a human review."""
    groups: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        if row.get("style_id"):
            groups.setdefault((row["kind"], row["style_id"]), []).append(row)
    return [{"kind": kind, "styleId": style, "n": len(items),
             "medianViews": median([r["views"] for r in items if r["views"] is not None]),
             "medianCtr": median([r["ctr"] for r in items if r["ctr"] is not None]) if any(r["ctr"] is not None for r in items) else None,
             "medianVtr": median([r["vtr"] for r in items if r["vtr"] is not None]) if any(r["vtr"] is not None for r in items) else None,
             "medianAveragePercentage": median([r["avg_pct"] for r in items if r["avg_pct"] is not None]) if any(r["avg_pct"] is not None for r in items) else None,
             "largestDrops": [{"videoId": r["id"], "at": r["biggest_drop_at"],
                                "size": r["biggest_drop"]} for r in items
                               if r["biggest_drop_at"] is not None]}
            for (kind, style), items in sorted(groups.items())]


def style_experiments(cohorts: list[dict]) -> list[dict]:
    """Offer comparisons only where both styles have measured samples."""
    proposals = []
    for kind in ("long", "shorts"):
        comparable = [c for c in cohorts if c["kind"] == kind and c["n"] >= 2
                      and c["medianAveragePercentage"] is not None]
        if len(comparable) < 2:
            continue
        ranked = sorted(comparable, key=lambda c: c["medianAveragePercentage"], reverse=True)
        better, baseline = ranked[0], ranked[-1]
        if better["styleId"] == baseline["styleId"]:
            continue
        proposals.append({"format": kind, "tryStyleId": better["styleId"],
                          "compareWithStyleId": baseline["styleId"],
                          "sampleCounts": {better["styleId"]: better["n"],
                                           baseline["styleId"]: baseline["n"]},
                          "medianAveragePercentage": {better["styleId"]: better["medianAveragePercentage"],
                                                       baseline["styleId"]: baseline["medianAveragePercentage"]},
                          "retentionDrops": {better["styleId"]: better["largestDrops"],
                                             baseline["styleId"]: baseline["largestDrops"]},
                          "note": "Review topic and age differences; test in a new draft. Do not edit shared presets automatically."})
    return proposals


def analyse(rows: list[dict]) -> dict:
    with_vtr = [r for r in rows if r["vtr"] is not None]
    with_ctr = [r for r in rows if r["ctr"] is not None]
    with_pct = [r for r in rows if r["avg_pct"] is not None]
    return {
        "rows": rows,
        "n": len(rows),
        "long": len([r for r in rows if r["kind"] == "long"]),
        "shorts": len([r for r in rows if r["kind"] == "shorts"]),
        "views_median": median([r["views"] for r in rows]),
        "views_total": sum(r["views"] or 0 for r in rows),
        "pct_median": median([r["avg_pct"] for r in with_pct]),
        "vtr_median": median([r["vtr"] for r in with_vtr]),
        "ctr_median": median([r["ctr"] for r in with_ctr]),
        "ctr_count": len(with_ctr),
        "style_cohorts": style_cohorts(rows),
        "style_experiments": style_experiments(style_cohorts(rows)),
        "subs_total": sum(r["subs"] or 0 for r in rows),
        "corr_vtr_views": pearson([(r["vtr"], r["views"]) for r in with_vtr]),
        "corr_ctr_views": pearson([(r["ctr"], r["views"]) for r in with_ctr]),
        "corr_pct_views": pearson([(r["avg_pct"], r["views"]) for r in with_pct]),
        "loops": [r for r in with_pct if (r["avg_pct"] or 0) > 100],
        "low_vtr": [r for r in with_vtr if r["vtr"] < 45],
        "clusters": cluster_stats(rows),
        "bands": duration_bands(rows),
        "weekdays": weekday_stats(rows),
        "top": sorted(rows, key=lambda r: r["views"] or 0, reverse=True)[:8],
        "best_pct": sorted([r for r in with_pct], key=lambda r: r["avg_pct"], reverse=True)[:5],
    }


def facts(analysis: dict) -> list[tuple[str, str]]:
    """Measured numbers only: no recommendations, no generated titles."""
    loops = len(analysis["loops"])
    low_vtr = len(analysis["low_vtr"])
    subs_rate = (analysis["subs_total"] / analysis["views_total"] * 100
                 if analysis["views_total"] else 0.0)
    return [
        ("videos", str(analysis["n"])),
        ("long / shorts", f"{analysis['long']} / {analysis['shorts']}"),
        ("views total", f"{analysis['views_total']:,}"),
        ("views median", f"{analysis['views_median']:.0f}"),
        ("average % median", f"{analysis['pct_median']:.1f}"),
        ("VTR median", f"{analysis['vtr_median']:.1f}"),
        ("CTR median", f"{analysis['ctr_median']:.1f}" if analysis["ctr_count"] else "unavailable"),
        ("videos with CTR measured", str(analysis["ctr_count"])),
        ("videos with VTR measured", str(len([r for r in analysis["rows"] if r["vtr"] is not None]))),
        ("videos below 45% VTR", str(low_vtr)),
        ("videos above 100% average %", str(loops)),
        ("subscribers gained", str(analysis["subs_total"] or 0)),
        ("subscribers per 1k views", f"{subs_rate * 10:.2f}"),
        ("r(VTR, views)", f"{analysis['corr_vtr_views']}"),
        ("r(CTR, views)", f"{analysis['corr_ctr_views']}"),
        ("r(average %, views)", f"{analysis['corr_pct_views']}"),
    ]


def render(rows: list[dict], analysis: dict, settings: dict, out: Path, log: Log) -> None:
    lines = [f"# Channel insights - {settings['name']}", "", f"Generated {now()}.", "",
             f"{analysis['n']} videos ({analysis['long']} long, {analysis['shorts']} shorts), "
             f"{analysis['views_total']:,} views total, median {analysis['views_median']:.0f} "
             f"views, median average % {analysis['pct_median']:.1f}, median VTR "
             f"{analysis['vtr_median']:.1f}%.", "",
             "## Top videos", "",
             "| video | kind | views | avg % | VTR |", "| --- | --- | --- | --- | --- |"]
    for row in analysis["top"]:
        pct = f"{row['avg_pct']:.0f}%" if row["avg_pct"] is not None else "-"
        vtr = f"{row['vtr']:.1f}%" if row["vtr"] is not None else "-"
        lines.append(f"| [{row['title'][:55]}](https://youtu.be/{row['id']}) | {row['kind']} | "
                     f"{row['views'] or '-'} | {pct} | {vtr} |")

    if analysis["bands"]:
        lines += ["", "## Duration bands", "", "| band | n | median views | avg % | VTR |",
                  "| --- | --- | --- | --- | --- |"]
        for band in analysis["bands"]:
            vtr_txt = f"{band['vtr']:.0f}%" if band["vtr"] else "-"
            avg_txt = f"{band['avg_pct']:.0f}%" if band["avg_pct"] is not None else "-"
            lines.append(f"| {band['band']} | {band['n']} | {band['views']:.0f} | "
                         f"{avg_txt} | {vtr_txt} |")

    if analysis["weekdays"]:
        lines += ["", "## Upload day", "", "| day | n | median views |", "| --- | --- | --- |"]
        for day in analysis["weekdays"]:
            lines.append(f"| {day['day']} | {day['n']} | {day['views']:.0f} |")

    if analysis["clusters"]:
        lines += ["", "## Topic lanes", "",
                  "| lane | n | median views | avg % | VTR | best |",
                  "| --- | --- | --- | --- | --- | --- |"]
        for cluster in analysis["clusters"][:12]:
            vtr_txt = f"{cluster['vtr']:.0f}%" if cluster["vtr"] else "-"
            avg_txt = f"{cluster['avg_pct']:.0f}%" if cluster["avg_pct"] is not None else "-"
            lines.append(f"| {cluster['token']} | {cluster['n']} | {cluster['views']:.0f} | "
                         f"{avg_txt} | {vtr_txt} | {cluster['best'][:40]} |")

    lines += ["", "## Channel numbers", "", "| metric | value |", "| --- | --- |"]
    lines += [f"| {name} | {value} |" for name, value in facts(analysis)]

    lines += ["", "## Correlations", "",
              f"- r(VTR, views) = {analysis['corr_vtr_views']}",
              f"- r(CTR, views) = {analysis['corr_ctr_views']}",
              f"- r(average %, views) = {analysis['corr_pct_views']}",
              "", f"Machine-readable input for a model: insights.json "
                  f"({human_size((out / 'insights.json').stat().st_size)}), dataset.csv, "
                  f"per-video metrics in analytics/<id>/.", ""]
    (out / "insights.md").write_text("\n".join(lines), encoding="utf-8")
    log(f"wrote {out / 'insights.md'}")


def run(cfg: dict, args, log: Log) -> int:
    slug, raw = select_pair(cfg, args.channel)
    settings = channel_settings(cfg, slug, raw)
    root = channel_root(cfg, slug)
    out = Path(args.out).expanduser() if args.out else channel_path(root, "analytics")
    videos = analytics.collect_videos(root, type("A", (), {"video": None, "last": 10**6})())
    if not videos:
        log(f"no local metadata under {root}; run backup first")
        return 1
    log(f"insights {slug}: {len(videos)} videos")
    metrics = fetch_api(cfg, settings, root, videos, args.refresh, log, args.reauthorize)
    vtr = load_cached_vtr(root, videos)
    if args.vtr_count:
        studio_vtr, studio_reach = fetch_studio_reach(cfg, settings, root, videos,
                                                       args.vtr_count, args.refresh, log)
        vtr.update(studio_vtr)
        for vid, reach in studio_reach.items():
            metrics.setdefault(vid, {}).update(reach)
    rows = build_rows(videos, metrics, vtr)
    write_dataset(rows, out)
    analysis = analyse(rows)
    write_json(out / "insights.json", {
        "channel": {"slug": slug, "name": settings["name"],
                    "channelId": settings["channel_id"]},
        "generated": now(),
        "numbers": {name: value for name, value in facts(analysis)},
        "correlations": {"vtr_vs_views": analysis["corr_vtr_views"],
                         "ctr_vs_views": analysis["corr_ctr_views"],
                         "avg_pct_vs_views": analysis["corr_pct_views"]},
        "style_cohorts": analysis["style_cohorts"],
        "style_experiments": analysis["style_experiments"],
        "duration_bands": analysis["bands"],
        "upload_days": analysis["weekdays"],
        "topic_lanes": analysis["clusters"],
        "videos": rows,
    })
    render(rows, analysis, settings, out, log)
    log(f"{len(rows)} videos in dataset; median views {analysis['views_median']:.0f}; "
        f"VTR median {analysis['vtr_median']:.1f}%")
    return 0


def select_pair(cfg: dict, name: str | None) -> tuple[str, dict]:
    from common import select_channels

    return select_channels(cfg, name)[0]
