"""Retention and performance reporting from the YouTube Analytics API or Studio."""

from __future__ import annotations

import csv
import json
import secrets
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import studio
from common import (Log, channel_root, channel_settings, human_size, now, read_json,
                    select_channels, write_json)

SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly",
          "https://www.googleapis.com/auth/youtube.readonly"]
AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"
REPORTS = "https://youtubeanalytics.googleapis.com/v2/reports"
TOKEN_DIR = Path.home() / ".config" / "content-helper"


class OAuthError(SystemExit):
    pass


class ApiClient:
    def __init__(self, settings: dict, log: Log):
        config = settings.get("analytics") or {}
        creds = config.get("credentials")
        if not creds:
            raise OAuthError(
                "analytics.credentials is not set for this channel.\n"
                "Create an OAuth client (Desktop app) in Google Cloud, enable the "
                "YouTube Analytics API, download the JSON and point "
                'channels.<slug>.analytics.credentials at it.')
        self.credentials = Path(creds).expanduser()
        self.token_path = Path(config.get("token") or
                               (TOKEN_DIR / f"token-{settings['slug']}.json")).expanduser()
        self.log = log
        self.token = self._load_token()

    def _load_token(self) -> dict:
        if self.token_path.exists():
            token = read_json(self.token_path)
            if token.get("refresh_token"):
                if token.get("expiry", 0) > time.time() + 60:
                    return token
                return self._refresh(token)
        return self._authorize()

    def _credentials(self) -> dict:
        if not self.credentials.exists():
            raise OAuthError(
                f"missing OAuth client file: {self.credentials}\n"
                "Google Cloud -> APIs & Services -> Credentials -> Create OAuth client ID "
                "-> Desktop app -> download JSON, then save it at that path.")
        data = read_json(self.credentials)
        block = data.get("installed") or data.get("web") or {}
        if not block.get("client_id"):
            raise OAuthError(f"{self.credentials} is not an OAuth client file")
        return block

    def _authorize(self) -> dict:
        block = self._credentials()
        result: dict = {}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                result.update({k: v[0] for k, v in query.items()})
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<h2>content-helper is authorised. Close this tab.</h2>")

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        redirect = f"http://127.0.0.1:{server.server_port}/"
        url = AUTH + "?" + urllib.parse.urlencode({
            "client_id": block["client_id"], "redirect_uri": redirect,
            "response_type": "code", "scope": " ".join(SCOPES),
            "access_type": "offline", "prompt": "consent",
        })
        self.log("opening the browser for Google consent")
        webbrowser.open(url)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        deadline = time.time() + 300
        while "code" not in result and "error" not in result and time.time() < deadline:
            time.sleep(0.5)
        server.shutdown()
        if "code" not in result:
            raise OAuthError("authorisation was not completed")
        token = self._post({"code": result["code"], "client_id": block["client_id"],
                            "client_secret": block["client_secret"],
                            "redirect_uri": redirect, "grant_type": "authorization_code"})
        token["client_id"] = block["client_id"]
        token["client_secret"] = block["client_secret"]
        token["expiry"] = time.time() + float(token.get("expires_in", 3600)) - 30
        write_json(self.token_path, token)
        return token

    def _refresh(self, token: dict) -> dict:
        refreshed = self._post({"client_id": token.get("client_id"),
                                "client_secret": token.get("client_secret"),
                                "refresh_token": token["refresh_token"],
                                "grant_type": "refresh_token"})
        token.update(refreshed)
        token["expiry"] = time.time() + float(refreshed.get("expires_in", 3600)) - 30
        write_json(self.token_path, token)
        return token

    def _post(self, payload: dict) -> dict:
        data = urllib.parse.urlencode(payload).encode()
        request = urllib.request.Request(TOKEN, data=data)
        with urllib.request.urlopen(request, timeout=30) as resp:
            return json.load(resp)

    def report(self, **params) -> dict:
        url = REPORTS + "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {self.token['access_token']}"})
        try:
            with urllib.request.urlopen(request, timeout=60) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:300]
            if exc.code == 401:
                self.token = self._refresh(self.token)
                return self.report(**params)
            raise SystemExit(f"YouTube Analytics API {exc.code}: {body}")

    def collect(self, channel_id: str, videos: list[dict], log: Log) -> dict:
        collected = {}
        for video in videos:
            vid = video["id"]
            start = video.get("upload_date") or "2000-01-01"
            end = time.strftime("%Y-%m-%d")
            filters = f"video=={vid}"
            base = {"ids": f"channel=={channel_id}", "startDate": start, "endDate": end,
                    "dimensions": "video", "filters": filters}
            metrics = {}
            for key in ("views,estimatedMinutesWatched,averageViewDuration,"
                        "averageViewPercentage,likes,comments,shares,subscribersGained",):
                try:
                    payload = self.report(metrics=key, **base)
                except SystemExit as exc:
                    log(f"{vid}: metrics failed ({exc})")
                    continue
                metrics.update(rows_to_dict(payload))
            try:
                metrics.update(rows_to_dict(self.report(
                    metrics="impressions,impressionsClickThroughRate", **base)))
            except SystemExit:
                pass
            retention = []
            try:
                payload = self.report(ids=f"channel=={channel_id}", startDate=start,
                                      endDate=end, metrics="audienceWatchRatio,"
                                      "relativeRetentionPerformance",
                                      dimensions="elapsedVideoTimeRatio",
                                      filters=filters, sort="elapsedVideoTimeRatio")
                retention = retention_rows(payload)
            except SystemExit as exc:
                log(f"{vid}: retention unavailable ({exc})")
            collected[vid] = {"metrics": metrics, "retention": retention,
                              "source": "api"}
            log(f"{vid}: {len(retention)} retention points, "
                f"{metrics.get('views', '?')} views")
        return collected


def rows_to_dict(payload: dict) -> dict:
    headers = [h["name"] for h in payload.get("columnHeaders", [])]
    rows = payload.get("rows") or []
    return dict(zip(headers, rows[0])) if rows else {}


def retention_rows(payload: dict) -> list[dict]:
    headers = [h["name"] for h in payload.get("columnHeaders", [])]
    points = []
    for row in payload.get("rows") or []:
        item = dict(zip(headers, row))
        points.append({"position": float(item.get("elapsedVideoTimeRatio", 0)),
                       "watch_ratio": float(item.get("audienceWatchRatio", 0)),
                       "relative": item.get("relativeRetentionPerformance")})
    return sorted(points, key=lambda p: p["position"])


def collect_videos(root: Path, args) -> list[dict]:
    videos = []
    for kind in ("long", "shorts"):
        for meta in (root / kind).glob("*/metadata.json"):
            info = read_json(meta)
            if not info.get("id"):
                continue
            upload = str(info.get("upload_date") or "")
            videos.append({
                "id": info["id"],
                "title": info.get("title") or meta.parent.name,
                "kind": kind,
                "duration": int(info.get("duration") or 0),
                "upload_date": (f"{upload[:4]}-{upload[4:6]}-{upload[6:8]}"
                                if len(upload) == 8 else "2000-01-01"),
                "views": info.get("view_count"),
                "folder": meta.parent,
            })
    videos.sort(key=lambda v: v["upload_date"], reverse=True)
    if args.video:
        videos = [v for v in videos if v["id"] == args.video]
    else:
        videos = videos[:args.last]
    return videos


def extract_points(payloads: list) -> list[dict]:
    points: dict[float, dict] = {}

    def walk(node):
        if isinstance(node, dict):
            if "elapsedVideoTimeRatio" in node and (
                    "audienceWatchRatio" in node or "audienceRetention" in node):
                try:
                    pos = float(node["elapsedVideoTimeRatio"])
                    value = node.get("audienceWatchRatio", node.get("audienceRetention"))
                    points[pos] = {"position": pos, "watch_ratio": float(value),
                                   "relative": node.get("relativeRetentionPerformance")}
                    return
                except (TypeError, ValueError):
                    return
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for payload in payloads:
        walk(payload)
    return [points[key] for key in sorted(points)]


def studio_collect(cfg: dict, settings: dict, videos: list[dict], log: Log) -> dict:
    port = int(cfg["browserDebugPort"])
    browser = settings["browser"]
    if not studio.launch(browser, port, log):
        raise SystemExit("could not open a debuggable browser for Studio analytics")
    collected = {}
    try:
        for video in videos:
            url = (f"https://studio.youtube.com/video/{video['id']}"
                   "/analytics/tab-content/period-default")
            payloads = studio.harvest_json(
                port, url, ("elapsedVideoTimeRatio", "audienceWatchRatio"), log)
            points = extract_points(payloads)
            collected[video["id"]] = {"metrics": {}, "retention": points,
                                      "source": "studio"}
            log(f"{video['id']}: {len(points)} retention points from Studio")
    finally:
        studio.stop(browser, log)
    return collected


def svg_chart(points: list[dict], title: str, path: Path) -> None:
    width, height, pad = 720, 260, 44
    if not points:
        return
    plot_w, plot_h = width - pad * 2, height - pad * 1.6
    coords = []
    for point in points:
        x = pad + point["position"] * plot_w
        y = pad + (1 - min(max(point["watch_ratio"], 0), 1)) * plot_h
        coords.append(f"{x:.1f},{y:.1f}")
    grid = "".join(
        f'<line x1="{pad}" y1="{pad + f * plot_h:.0f}" x2="{pad + plot_w}" '
        f'y2="{pad + f * plot_h:.0f}" stroke="#e5e7eb"/>'
        f'<text x="{pad - 8}" y="{pad + f * plot_h + 4:.0f}" text-anchor="end" '
        f'font-size="11" fill="#6b7280">{int((1 - f) * 100)}%</text>'
        for f in (0, 0.25, 0.5, 0.75, 1))
    ticks = "".join(
        f'<text x="{pad + f * plot_w:.0f}" y="{height - 8}" text-anchor="middle" '
        f'font-size="11" fill="#6b7280">{int(f * 100)}%</text>'
        for f in (0, 0.25, 0.5, 0.75, 1))
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="#ffffff"/>'
        f'<text x="{pad}" y="24" font-size="13" fill="#111827">'
        f'{escape(title)}</text>{grid}{ticks}'
        f'<polyline fill="none" stroke="#2563eb" stroke-width="2" '
        f'points="{" ".join(coords)}"/></svg>', encoding="utf-8")


def escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def at(points: list[dict], position: float) -> float | None:
    if not points:
        return None
    return min(points, key=lambda p: abs(p["position"] - position))["watch_ratio"]


def biggest_drop(points: list[dict]) -> tuple[float, float] | None:
    if len(points) < 2:
        return None
    best = (0.0, 0.0)
    for prev, cur in zip(points, points[1:]):
        drop = prev["watch_ratio"] - cur["watch_ratio"]
        if drop > best[1]:
            best = (cur["position"], drop)
    return best


def insights(video: dict, retention: list[dict], metrics: dict, median_pct: float) -> list[str]:
    notes = []
    if retention:
        hook = at(retention, 0.02)
        early = at(retention, 0.10)
        half = at(retention, 0.5)
        if hook is not None and early is not None and hook - early > 0.15:
            notes.append(
                f"Hook loses {round((hook - early) * 100)} points by 10% of the runtime "
                f"- the opening promise is not landing; tighten the first 15-30s.")
        drop = biggest_drop(retention)
        if drop and drop[1] > 0.06:
            seconds = drop[0] * video["duration"] if video["duration"] else None
            where = f" (~{int(seconds // 60)}:{int(seconds % 60):02d})" if seconds else ""
            notes.append(
                f"Largest single drop of {round(drop[1] * 100)} points at {round(drop[0] * 100)}%"
                f"{where}: check what happens there for a cut, tangent or repeated beat.")
        if half is not None and half < 0.35:
            notes.append(
                f"Only {round(half * 100)}% remain at the halfway mark - the middle needs "
                f"a new hook, a payoff, or should be shorter.")
        if half is not None and half > 0.55:
            notes.append(
                f"{round(half * 100)}% still watching at halfway - this structure works; "
                f"reuse its pacing and length.")
    pct = metrics.get("averageViewPercentage")
    if isinstance(pct, (int, float)) and median_pct:
        delta = pct - median_pct
        if delta <= -5:
            notes.append(f"Average view percentage {round(pct, 1)}% is {round(-delta, 1)} points "
                         f"below the channel median ({round(median_pct, 1)}%).")
        elif delta >= 5:
            notes.append(f"Average view percentage {round(pct, 1)}% beats the channel median "
                         f"by {round(delta, 1)} points.")
    ctr = metrics.get("impressionsClickThroughRate")
    if isinstance(ctr, (int, float)) and ctr < 3:
        notes.append(f"Click-through rate {round(ctr, 2)}% is low - the thumbnail/title pair "
                     f"is the first thing to change, not the video.")
    if video["kind"] == "long" and video["duration"] > 900 and pct and pct < 35:
        notes.append("Long-form over 15 minutes with weak average percentage: cut the runtime "
                     "or split the topic.")
    return notes


def build_report(root: Path, settings: dict, videos: list[dict], data: dict,
                 out: Path, log: Log) -> None:
    out.mkdir(parents=True, exist_ok=True)
    pcts = [d["metrics"].get("averageViewPercentage") for d in data.values()]
    pcts = [float(p) for p in pcts if isinstance(p, (int, float))]
    median_pct = sorted(pcts)[len(pcts) // 2] if pcts else 0.0

    lines = [f"# Retention report - {settings['name']}", "",
             f"Generated {now()} from {'YouTube Analytics API' if any(v['source'] == 'api' for v in data.values()) else 'YouTube Studio'}.", "",
             "| video | views | avg view | avg % | @25% | @50% | @75% | biggest drop |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    pointers: list[str] = []

    for video in videos:
        entry = data.get(video["id"])
        if not entry:
            continue
        metrics, retention = entry["metrics"], entry["retention"]
        avg = metrics.get("averageViewDuration")
        avg_txt = f"{int(avg // 60)}:{int(avg % 60):02d}" if isinstance(avg, (int, float)) else "-"
        pct = metrics.get("averageViewPercentage")
        pct_txt = f"{pct:.1f}%" if isinstance(pct, (int, float)) else "-"
        cells = [f"{v:.0%}" if (v := at(retention, p)) is not None else "-"
                 for p in (0.25, 0.5, 0.75)]
        drop = biggest_drop(retention)
        drop_txt = f"{drop[0]:.0%} ({drop[1]:.0%})" if drop else "-"
        title = video["title"][:60].replace("|", "/")
        lines.append(f"| [{title}](https://youtu.be/{video['id']}) | "
                     f"{metrics.get('views', '-')} | {avg_txt} | {pct_txt} | "
                     f"{' | '.join(cells)} | {drop_txt} |")

        folder = out / video["id"]
        folder.mkdir(parents=True, exist_ok=True)
        write_json(folder / "metrics.json",
                   {"video": {k: video[k] for k in ("id", "title", "kind", "duration",
                                                    "upload_date")},
                    "metrics": metrics, "source": entry["source"]})
        if retention:
            with (folder / "retention.csv").open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=["position", "watch_ratio", "relative"])
                writer.writeheader()
                writer.writerows(retention)
            svg_chart(retention, video["title"][:70], folder / "retention.svg")
        for note in insights(video, retention, metrics, median_pct):
            pointers.append(f"- **{video['title'][:50]}** - {note}")

    lines += ["", "## Pointers for the next video", ""]
    lines += pointers or ["- Not enough data yet; publish a few more videos or widen --last."]
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"wrote {out / 'report.md'} ({len(videos)} videos)")
    if not any(d["retention"] for d in data.values()):
        log("no retention curves returned; check that the channel has enough watch data")


def run(cfg: dict, args, log: Log) -> int:
    slug, raw = select_channels(cfg, args.channel)[0]
    settings = channel_settings(cfg, slug, raw)
    root = channel_root(cfg, slug)
    videos = collect_videos(root, args)
    if not videos:
        log(f"no local metadata under {root}; run backup first")
        return 1
    out = Path(args.out).expanduser() if args.out else root / "analytics"
    provider = args.provider or settings["analytics"].get("provider", "api")
    log(f"analytics {slug}: {len(videos)} videos via {provider}")
    if provider == "api":
        channel_id = settings["channel_id"] or yt_channel_id(settings, log)
        client = ApiClient(settings, log)
        data = client.collect(channel_id, videos, log)
    else:
        data = studio_collect(cfg, settings, videos, log)
    build_report(root, settings, videos, data, out, log)
    return 0


def yt_channel_id(settings: dict, log: Log) -> str:
    import ytdlp

    return ytdlp.resolve_channel_id(settings, log)
