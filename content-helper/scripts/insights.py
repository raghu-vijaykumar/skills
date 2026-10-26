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
from common import Log, channel_root, channel_settings, human_size, now, read_json, write_json

STOP = set("""how what why does do the a an of to in on for with and or that this your you it
is are was were can could will would actually really explained explain works work working into
from at as by be been being its it's there here about when where which who whom whose than then
them they these those one two not no yes all any more most some such only own same so too very
just also still even ever never make makes made get gets got use used using new best top vs
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
    return root / "analytics" / vid / "metrics.json", root / "analytics" / "vtr" / f"{vid}.json"


def cached_metrics(root: Path, vid: str, max_age_hours: float = 12) -> dict:
    path = root / "analytics" / vid / "metrics.json"
    if not path.exists():
        return {}
    if (time.time() - path.stat().st_mtime) / 3600 > max_age_hours:
        return {}
    return read_json(path).get("metrics") or {}


def fetch_api(cfg: dict, settings: dict, root: Path, videos: list[dict], refresh: bool,
              log: Log) -> dict:
    client = analytics.ApiClient(settings, log)
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
        if metrics:
            keep = read_json(root / "analytics" / video["id"] / "metrics.json")
            keep.setdefault("video", {"id": video["id"], "title": video["title"],
                                      "kind": video["kind"], "duration": video["duration"],
                                      "upload_date": video["upload_date"]})
            keep["metrics"] = metrics
            keep.setdefault("source", "api")
            write_json(root / "analytics" / video["id"] / "metrics.json", keep)
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


def fetch_vtr(cfg: dict, settings: dict, root: Path, videos: list[dict], limit: int,
              refresh: bool, log: Log) -> dict:
    shorts = [v for v in videos if v["kind"] == "shorts"][:limit]
    if not shorts:
        return {}
    values: dict[str, float] = {}
    pending = []
    for video in shorts:
        _, path = cache_paths(root, video["id"])
        if path.exists() and not refresh:
            data = read_json(path)
            if isinstance(data.get("vtr"), (int, float)):
                values[video["id"]] = data["vtr"]
                continue
        pending.append(video)
    if not pending:
        return values
    port = int(cfg["browserDebugPort"])
    browser = settings["browser"]
    if not studio.launch(browser, port, log):
        log("browser session unavailable; VTR skipped")
        return values
    if not studio.channel_accessible(port, settings["channel_id"], log):
        studio.stop(browser, log)
        return values
    try:
        for video in pending:
            url = (f"https://studio.youtube.com/video/{video['id']}"
                   "/analytics/tab-content/period-default")
            payloads = studio.harvest_json(port, url, ("metricTotals",), log)
            _, metrics = analytics.extract_points(payloads)
            if not metrics:
                payloads = studio.harvest_json(port, url, ("metricTotals",), log, wait=25)
                _, metrics = analytics.extract_points(payloads)
            vtr = metrics.get("shortsFeedImpressionsVtr")
            if isinstance(vtr, (int, float)):
                values[video["id"]] = vtr
                _, path = cache_paths(root, video["id"])
                write_json(path, {"vtr": vtr, "fetched": now()})
                log(f"{video['id']}: VTR {vtr:.1f}%")
    finally:
        studio.stop(browser, log)
    return values


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
        rows.append({
            "id": video["id"], "kind": video["kind"], "title": video["title"],
            "upload_date": video["upload_date"], "duration": video["duration"],
            "views": m.get("views"), "watch_minutes": m.get("estimatedMinutesWatched"),
            "avg_view_sec": m.get("averageViewDuration"),
            "avg_pct": m.get("averageViewPercentage"),
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
              "avg_view_sec", "avg_pct", "vtr", "subs", "likes", "comments", "shares",
              "at25", "at50", "at75", "biggest_drop_at", "biggest_drop",
              "pattern", "title_len"]
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
                         "views": median(views), "avg_pct": median(pcts),
                         "vtr": median(vtrs),
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
                                          if m["avg_pct"] is not None]),
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


def analyse(rows: list[dict]) -> dict:
    with_vtr = [r for r in rows if r["vtr"] is not None]
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
        "subs_total": sum(r["subs"] or 0 for r in rows),
        "corr_vtr_views": pearson([(r["vtr"], r["views"]) for r in with_vtr]),
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
        ("videos with VTR measured", str(len([r for r in analysis["rows"] if r["vtr"] is not None]))),
        ("videos below 45% VTR", str(low_vtr)),
        ("videos above 100% average %", str(loops)),
        ("subscribers gained", str(analysis["subs_total"] or 0)),
        ("subscribers per 1k views", f"{subs_rate * 10:.2f}"),
        ("r(VTR, views)", f"{analysis['corr_vtr_views']}"),
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
            lines.append(f"| {band['band']} | {band['n']} | {band['views']:.0f} | "
                         f"{band['avg_pct']:.0f}% | {vtr_txt} |")

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
            lines.append(f"| {cluster['token']} | {cluster['n']} | {cluster['views']:.0f} | "
                         f"{cluster['avg_pct']:.0f}% | {vtr_txt} | "
                         f"{cluster['best'][:40]} |")

    lines += ["", "## Channel numbers", "", "| metric | value |", "| --- | --- |"]
    lines += [f"| {name} | {value} |" for name, value in facts(analysis)]

    lines += ["", "## Correlations", "",
              f"- r(VTR, views) = {analysis['corr_vtr_views']}",
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
    out = Path(args.out).expanduser() if args.out else root / "analytics"
    videos = analytics.collect_videos(root, type("A", (), {"video": None, "last": 10**6})())
    if not videos:
        log(f"no local metadata under {root}; run backup first")
        return 1
    log(f"insights {slug}: {len(videos)} videos")
    metrics = fetch_api(cfg, settings, root, videos, args.refresh, log)
    vtr = load_cached_vtr(root, videos)
    if args.vtr_count:
        vtr.update(fetch_vtr(cfg, settings, root, videos, args.vtr_count, args.refresh, log))
    rows = build_rows(videos, metrics, vtr)
    write_dataset(rows, out)
    analysis = analyse(rows)
    write_json(out / "insights.json", {
        "channel": {"slug": slug, "name": settings["name"],
                    "channelId": settings["channel_id"]},
        "generated": now(),
        "numbers": {name: value for name, value in facts(analysis)},
        "correlations": {"vtr_vs_views": analysis["corr_vtr_views"],
                         "avg_pct_vs_views": analysis["corr_pct_views"]},
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
