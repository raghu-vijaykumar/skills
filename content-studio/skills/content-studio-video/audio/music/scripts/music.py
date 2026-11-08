#!/usr/bin/env python3
"""Choose, review, and record background music for one draft."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_ROOT = next(parent for parent in Path(__file__).resolve().parents if parent.name == "content-studio")
sys.path.insert(0, str(BUNDLE_ROOT / "skills" / "content-studio-video" / "edit" / "clip-edit" / "scripts"))

from common import DEFAULT_CONFIG, channel_root, load_config, select_channels  # noqa: E402

DEFAULT_CATALOG = BUNDLE_ROOT / "assets" / "music"
LICENSE_LABELS = {
    "youtube-audio-library": "YouTube Audio Library",
    "youtube-audio-library-cc-by": "YouTube Audio Library (CC BY 4.0)",
    "pixabay": "Pixabay Content License",
    "pixabay-cc0": "Pixabay (CC0)",
    "cc-by-4.0": "Creative Commons Attribution 4.0",
    "cc0": "CC0 / public domain",
}


def slugify(value: str) -> str:
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9]+", "-", value.lower().replace("&", "and")))


def category_key(value: str) -> str:
    """Match both genre labels (Dance & Electronic) and slugs (dance-electronic)."""
    normalized = value.lower().replace("r&b", "rnb").replace("r and b", "rnb")
    return slugify(normalized).replace("and", "").replace("-", "")


def format_duration(seconds: float | None) -> str:
    if not seconds:
        return "?:??"
    total = round(float(seconds))
    return f"{total // 60}:{total % 60:02d}"


def source_label(track: dict) -> str:
    if track.get("source"):
        return str(track["source"])
    return "Pixabay Music" if str(track.get("license", "")).startswith("pixabay") \
        else "YouTube Audio Library"


def license_label(track: dict) -> str:
    return LICENSE_LABELS.get(str(track.get("license", "")), str(track.get("license", "unknown")))


def attribution_line(track: dict) -> str:
    if not track.get("attribution_required"):
        return "No attribution required."
    text = str(track.get("attribution_text", "")).strip()
    if text:
        return text
    return f'Music: "{track.get("title", "")}" by {track.get("artist", "")} ({license_label(track)})'


def load_catalog(root: Path) -> tuple[dict, list[dict]]:
    manifest_path = root / "library.json"
    if not manifest_path.is_file():
        raise SystemExit(
            f"music catalog not found: {manifest_path}\n"
            "Run: node content-studio/scripts/music-library.mjs init"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tracks = []
    for raw in manifest.get("tracks", []):
        track = dict(raw)
        file = root / "local" / Path(str(track.get("file", "")))
        track["absolute_path"] = str(file.resolve())
        track["available"] = file.is_file()
        track["duration_seconds"] = float(track.get("duration_seconds") or 0)
        tracks.append(track)
    return manifest, tracks


def filter_tracks(tracks: list[dict], *, category: str | None = None,
                  mood: str | None = None, query: str | None = None,
                  min_duration: float | None = None, max_duration: float | None = None,
                  available_only: bool = True) -> list[dict]:
    selected = []
    for track in tracks:
        if available_only and not track.get("available"):
            continue
        if category and category_key(category) != category_key(str(track.get("category", ""))):
            continue
        if mood and mood.lower() not in str(track.get("mood", "")).lower():
            continue
        if query:
            needle = query.lower()
            haystack = " ".join(str(track.get(key, "")) for key in
                                ("title", "artist", "file", "category", "mood")).lower()
            if needle not in haystack:
                continue
        duration = float(track.get("duration_seconds") or 0)
        if min_duration is not None and duration < min_duration:
            continue
        if max_duration is not None and duration > max_duration:
            continue
        selected.append(track)
    return sorted(selected, key=lambda item: (str(item.get("category", "")),
                                              str(item.get("title", "")).lower()))


def resolve_track(tracks: list[dict], selector: str) -> dict:
    needle = selector.strip().lower()
    if not needle:
        raise SystemExit("--track cannot be empty")
    exact = [track for track in tracks
             if needle in {str(track.get("file", "")).lower(),
                           Path(str(track.get("file", ""))).name.lower(),
                           str(track.get("title", "")).lower()}]
    if len(exact) == 1:
        return exact[0]
    matches = [track for track in tracks
               if needle in str(track.get("title", "")).lower()
               or needle in str(track.get("file", "")).lower()
               or needle in str(track.get("artist", "")).lower()]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise SystemExit(f"no catalog track matches {selector!r}; run list to see titles")
    names = "\n".join(f"  {track.get('title')} — {track.get('artist')} ({track.get('file')})"
                      for track in matches[:12])
    raise SystemExit(f"{selector!r} matches {len(matches)} tracks; use the exact title or file:\n{names}")


def print_tracks(tracks: list[dict]) -> None:
    if not tracks:
        print("no matching tracks")
        return
    print(f"{'CATEGORY':<18} {'TITLE':<32} {'ARTIST':<22} {'TIME':>6}  LICENSE")
    for track in tracks:
        print(f"{str(track.get('category', '')):<18} {str(track.get('title', ''))[:32]:<32} "
              f"{str(track.get('artist', ''))[:22]:<22} {format_duration(track.get('duration_seconds')):>6}  "
              f"{license_label(track)}")


def write_review(draft: Path, tracks: list[dict], catalog: Path, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, track in enumerate(tracks, 1):
        uri = Path(track["absolute_path"]).as_uri()
        rows.append(
            "<tr>"
            f"<td>{index}</td>"
            f"<td><strong>{html.escape(str(track.get('title', '')))}</strong><br>"
            f"<span>{html.escape(str(track.get('artist', '')))}</span></td>"
            f"<td>{html.escape(str(track.get('category', '')))}"
            f"{' · ' + html.escape(str(track.get('mood', ''))) if track.get('mood') else ''}</td>"
            f"<td>{format_duration(track.get('duration_seconds'))}</td>"
            f"<td>{html.escape(license_label(track))}<br>"
            f"<small>{html.escape(attribution_line(track))}</small></td>"
            f"<td><audio controls preload='none' src='{html.escape(uri)}'></audio></td>"
            "</tr>"
        )
    page = (
        "<!doctype html><meta charset='utf-8'><title>Music review</title>"
        "<style>body{font:15px system-ui,sans-serif;max-width:1200px;margin:2rem auto;padding:0 1rem}"
        "table{border-collapse:collapse;width:100%}th,td{padding:.7rem;border-bottom:1px solid #ccc;"
        "vertical-align:top;text-align:left}small{color:#555}audio{width:260px}</style>"
        "<h1>Music review</h1>"
        f"<p>Catalog: <code>{html.escape(str(catalog))}</code></p>"
        "<p>Listen to each candidate. Reply with the exact title you approve; the selection is not "
        "written until the user chooses. Audio stays in the local catalog and is not copied into the draft.</p>"
        "<table><tr><th>#</th><th>Track</th><th>Category</th><th>Time</th>"
        "<th>License</th><th>Preview</th></tr>" + "".join(rows) + "</table>"
    )
    output.write_text(page, encoding="utf-8")
    return output


def write_selection(draft: Path, track: dict, catalog: Path, channel: str,
                    draft_name: str) -> tuple[Path, Path]:
    selection = draft / "music-selection.json"
    credits = draft / "music-credits.txt"
    selected_at = datetime.now().astimezone().isoformat(timespec="seconds")
    payload = {
        "schema_version": 1,
        "channel": channel,
        "draft": draft_name,
        "selected_at": selected_at,
        "catalog": str(catalog),
        "track": track,
        "credits": attribution_line(track),
    }
    selection.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    credits.write_text(
        f"Track: {track.get('title', '')}\n"
        f"Artist: {track.get('artist', '')}\n"
        f"Source: {source_label(track)}\n"
        f"License: {license_label(track)}\n"
        f"Attribution: {attribution_line(track)}\n"
        f"File: {track.get('file', '')}\n"
        f"Selected: {selected_at}\n",
        encoding="utf-8",
    )
    return selection, credits


def probe_media(path: Path) -> tuple[float, bool]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise SystemExit(f"ffprobe failed for {path}: {result.stderr.strip()[-400:]}")
    data = json.loads(result.stdout or "{}")
    duration = float(data.get("format", {}).get("duration") or 0)
    audio = any(stream.get("codec_type") == "audio" for stream in data.get("streams", []))
    if duration <= 0 or not audio:
        raise SystemExit(f"media needs a positive duration and audio: {path}")
    return duration, audio


def mix_music(video: Path, track: Path, output: Path, *, volume: float = 0.18,
              duck: bool | None = None, fade: float = 1.0) -> dict:
    duration, _ = probe_media(video)
    probe_media(track)
    if output.exists():
        raise SystemExit(f"output already exists: {output}")
    if duck is None:
        transcript = (video.parent.parent if video.parent.name == "video" else video.parent) / "transcript.json"
        duck = False
        if transcript.is_file():
            data = json.loads(transcript.read_text(encoding="utf-8"))
            duck = data.get("speech") is not False
    fade = max(0.0, min(float(fade), duration / 2))
    filters = [f"volume={volume:.4f}", f"atrim=0:{duration:.6f}", "asetpts=PTS-STARTPTS"]
    if fade > 0:
        filters += [f"afade=t=in:st=0:d={fade:.3f}",
                    f"afade=t=out:st={max(0.0, duration - fade):.3f}:d={fade:.3f}"]
    music = "[1:a]" + ",".join(filters) + "[music]"
    if duck:
        graph = ("[0:a]asplit=2[voice][key];" + music
                 + ";[music][key]sidechaincompress=threshold=0.05:ratio=4:"
                   "attack=20:release=300[ducked]"
                   ";[voice][ducked]amix=inputs=2:duration=first:dropout_transition=2[a]")
    else:
        graph = music + ";[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[a]"
    output.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(video), "-stream_loop", "-1", "-i", str(track),
         "-filter_complex", graph, "-map", "0:v:0", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
         "-t", f"{duration:.6f}", "-movflags", "+faststart", str(output)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        output.unlink(missing_ok=True)
        raise SystemExit(f"ffmpeg music mix failed: {result.stderr.strip()[-600:]}")
    actual, _ = probe_media(output)
    if abs(actual - duration) > max(0.2, duration * 0.005):
        output.unlink(missing_ok=True)
        raise SystemExit(f"music mix duration changed: {duration:.3f}s -> {actual:.3f}s")
    return {"duration_seconds": round(actual, 3), "volume": volume,
            "duck": bool(duck), "fade_seconds": fade}


def draft_for(args) -> tuple[str, Path]:
    if not getattr(args, "channel", None) or not getattr(args, "draft", None):
        raise SystemExit("--channel and --draft are required")
    cfg = load_config(Path(args.config))
    slug, _ = select_channels(cfg, args.channel)[0]
    draft = channel_root(cfg, slug) / "drafts" / args.draft
    if not draft.is_dir():
        raise SystemExit(f"draft not found: {draft}")
    return slug, draft


def add_filters(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--category", help="Audio Library genre or catalog category")
    parser.add_argument("--mood", help="mood substring such as calm or inspirational")
    parser.add_argument("--query", help="title, artist, file, category, or mood text")
    parser.add_argument("--min-duration", type=float, help="minimum seconds")
    parser.add_argument("--max-duration", type=float, help="maximum seconds")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Choose and record background music from the local catalog.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--catalog", default=os.environ.get("CONTENT_STUDIO_MUSIC",
                                                           str(DEFAULT_CATALOG)))
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--config", default=argparse.SUPPRESS)
    shared.add_argument("--catalog", default=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)

    listing = sub.add_parser("list", parents=[shared],
                             help="list catalog tracks with filters")
    add_filters(listing)
    listing.add_argument("--json", action="store_true")
    listing.add_argument("--include-missing", action="store_true",
                         help="include catalog entries whose audio file is missing")

    review = sub.add_parser("review", parents=[shared],
                            help="build an audio review page for a draft")
    review.add_argument("--channel", required=True)
    review.add_argument("--draft", required=True)
    add_filters(review)
    review.add_argument("--count", type=int, default=5)
    review.add_argument("--out", help="review HTML path")

    select = sub.add_parser("select", parents=[shared],
                            help="record the approved track for a draft")
    select.add_argument("--channel", required=True)
    select.add_argument("--draft", required=True)
    select.add_argument("--track", required=True,
                        help="exact title, file name, or a unique substring")

    mix = sub.add_parser("mix", parents=[shared],
                         help="mix the selected track under the draft master")
    mix.add_argument("--channel", required=True)
    mix.add_argument("--draft", required=True)
    mix.add_argument("--track", help="catalog title/file; default: music-selection.json")
    mix.add_argument("--input", help="video input (default: draft/final-video.mp4)")
    mix.add_argument("--output", help="output (default: draft/video-with-music.mp4)")
    mix.add_argument("--volume", type=float, default=0.18,
                     help="music gain relative to the master (default 0.18)")
    mix.add_argument("--fade", type=float, default=1.0,
                     help="fade in/out seconds (default 1.0)")
    mix.add_argument("--duck", action=argparse.BooleanOptionalAction, default=None,
                     help="duck music under speech; default: auto from transcript.speech")
    mix.add_argument("--force", action="store_true", help="replace an existing output")

    show = sub.add_parser("show", parents=[shared],
                          help="show the recorded selection for a draft")
    show.add_argument("--channel", required=True)
    show.add_argument("--draft", required=True)
    return parser


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    catalog = Path(args.catalog).expanduser().resolve()

    if args.command == "show":
        _, draft = draft_for(args)
        selection = draft / "music-selection.json"
        if not selection.is_file():
            raise SystemExit(f"no music selection yet: {selection}")
        payload = json.loads(selection.read_text(encoding="utf-8"))
        track = payload.get("track", {})
        print(f"{track.get('title')} — {track.get('artist')}")
        print(f"license: {license_label(track)}")
        print(f"attribution: {attribution_line(track)}")
        print(f"file: {track.get('file')}")
        return 0

    _manifest, tracks = load_catalog(catalog)

    if args.command == "list":
        selected = filter_tracks(
            tracks, category=args.category, mood=args.mood, query=args.query,
            min_duration=args.min_duration, max_duration=args.max_duration,
            available_only=not args.include_missing)
        if args.json:
            print(json.dumps({"catalog": str(catalog), "tracks": selected}, indent=2))
        else:
            print_tracks(selected)
        return 0

    if args.command == "review":
        slug, draft = draft_for(args)
        selected = filter_tracks(
            tracks, category=args.category, mood=args.mood, query=args.query,
            min_duration=args.min_duration, max_duration=args.max_duration)[:max(1, args.count)]
        if not selected:
            raise SystemExit("no matching tracks; adjust the filters or add tracks to the catalog")
        output = Path(args.out).expanduser().resolve() if args.out \
            else draft / ".content-studio" / "analysis" / "music-review.html"
        write_review(draft, selected, catalog, output)
        print(f"draft: {slug}/{args.draft}")
        print_tracks(selected)
        print(f"review: {output}")
        print("Listen, then record the approved track with select --track \"<exact title>\".")
        return 0

    if args.command == "select":
        slug, draft = draft_for(args)
        track = resolve_track(tracks, args.track)
        if not track.get("available"):
            raise SystemExit(f"audio file is missing: {track.get('absolute_path')}")
        selection, credits = write_selection(draft, track, catalog, slug, args.draft)
        print(f"selected: {track.get('title')} — {track.get('artist')}")
        print(f"selection: {selection}")
        print(f"credits: {credits}")
        return 0

    if args.command == "mix":
        slug, draft = draft_for(args)
        if args.track:
            track = resolve_track(tracks, args.track)
            selection_note = None
        else:
            selection = draft / "music-selection.json"
            if not selection.is_file():
                raise SystemExit(f"no music selection yet: {selection}")
            payload = json.loads(selection.read_text(encoding="utf-8"))
            track = dict(payload.get("track", {}))
            if not track.get("absolute_path"):
                catalog_root = Path(payload.get("catalog") or catalog)
                track["absolute_path"] = str(
                    (catalog_root / "local" / Path(str(track.get("file", "")))).resolve())
            selection_note = selection.name
        track_path = Path(str(track.get("absolute_path", "")))
        if not track_path.is_file():
            raise SystemExit(f"selected audio file is missing: {track_path}")
        current = draft / "final-video.mp4"
        legacy_video = draft / "video" / "with-audio.mp4"
        legacy = draft / "video.mp4"
        video = Path(args.input).expanduser().resolve() if args.input else (
            current if current.is_file() or not (legacy_video.is_file() or legacy.is_file())
            else (legacy_video if legacy_video.is_file() else legacy))
        output = Path(args.output).expanduser().resolve() if args.output \
            else draft / "final-video-with-music.mp4"
        if not video.is_file():
            raise SystemExit(f"master video not found: {video}")
        if output.resolve() == video.resolve():
            raise SystemExit("music mix output must differ from the input master")
        if output.exists():
            if not args.force:
                raise SystemExit(f"output already exists: {output} (use --force)")
            output.unlink()
        result = mix_music(video, track_path, output, volume=args.volume,
                           duck=args.duck, fade=args.fade)
        record = {
            "mixed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "selection": selection_note,
            "track": track,
            "input": str(video),
            "output": str(output),
            **result,
        }
        (draft / "music-mix.json").write_text(json.dumps(record, indent=2) + "\n",
                                              encoding="utf-8")
        print(f"mixed: {track.get('title')} -> {output}")
        print(f"record: {draft / 'music-mix.json'}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
