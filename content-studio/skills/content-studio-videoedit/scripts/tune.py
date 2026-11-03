#!/usr/bin/env python3
"""Score audio-enhancement candidates per clip and record the chosen profile.

The tuner never guesses at "better": every candidate is rendered through the
same denoise/limit chain preprocess uses, measured against the untouched source
window, and only wins when it clears the fidelity gates and beats the current
default by more than the measurement margin. Results are written as artifacts
(audio, metrics, profile) so a person can listen before anything is applied.
"""

from __future__ import annotations

import csv
import json
import math
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

import numpy as np

import draftlayout
import ordering
import preprocess
from preprocess import SAMPLE_RATE, ProcessingError, command, pcm16, probe, streams

TUNE_VERSION = 3
WINDOW_FRACTIONS = (0.3, 0.7)
ANALYSIS_HOP_SECONDS = 0.02
BAND_LOW_HZ = 300.0
BAND_HIGH_HZ = 3400.0
MIN_TUNE_SECONDS = 5.0
DEFAULT_MARGIN = 1.5
BASELINE = "default"
# A candidate must stay within this many dB of the source speech level.
LEVEL_DRIFT_DB = 6.0
# Fidelity gates: a candidate that trips any of these cannot be chosen.
FIDELITY_ISSUES = ("clipping", "speech-band loss", "content loss")
# A denoise pass must remove at least this much noise or raise SNR this much to
# be worth applying; otherwise metric jitter decides between near-identical
# chains.
MIN_NOISE_CUT_DB = 1.0
MIN_SNR_GAIN_DB = 1.0

CSV_FIELDS = ("clip", "chosen", "score", "runner_up", "runner_up_score",
              "noise_reduction_db", "snr_gain_db", "speech_band_ratio",
              "peak_dbfs", "issues", "reason")


class TuneError(RuntimeError):
    pass


def candidate_grid(deepfilter_executable: str | None) -> list[dict]:
    """Return the ordered candidate set; the first entry is the current default.

    Every grid includes a no-denoise candidate: some clips carry music or
    ambience rather than speech, and the speech denoiser must lose to leaving
    that content alone instead of being forced on every clip.
    """
    if deepfilter_executable:
        return [
            {"name": "default", "engine": "deepfilter", "post_filter": False,
             "beta": 0.0, "highpass": 0, "attenuation": None},
            {"name": "pf", "engine": "deepfilter", "post_filter": True,
             "beta": 0.02, "highpass": 0, "attenuation": None},
            {"name": "pf-safe", "engine": "deepfilter", "post_filter": True,
             "beta": 0.02, "highpass": 0, "attenuation": 10},
            {"name": "pf-strong", "engine": "deepfilter", "post_filter": True,
             "beta": 0.05, "highpass": 0, "attenuation": None},
            {"name": "none", "engine": "none", "post_filter": False,
             "beta": 0.0, "highpass": 80, "attenuation": None},
        ]
    return [
        {"name": "default", "engine": "ffmpeg", "nr": 12, "highpass": 80},
        {"name": "nr-light", "engine": "ffmpeg", "nr": 6, "highpass": 80},
        {"name": "nr-heavy", "engine": "ffmpeg", "nr": 18, "highpass": 80},
        {"name": "none", "engine": "none", "nr": 0, "highpass": 80},
    ]


def find_deepfilter() -> str | None:
    executable = shutil.which("deep-filter")
    if executable:
        return executable
    return shutil.which("deepFilter")


def windows_for(duration: float, sample_seconds: float) -> list[tuple[float, float]]:
    """Pick evenly spread windows so one quiet intro cannot decide the profile."""
    if duration <= sample_seconds:
        return [(0.0, duration)]
    span = sample_seconds / len(WINDOW_FRACTIONS)
    windows = []
    for fraction in WINDOW_FRACTIONS:
        start = min(max(0.0, duration * fraction - span / 2), duration - span)
        windows.append((round(start, 3), round(start + span, 3)))
    return windows


def select_clips(files: list[Path], limit: int) -> list[Path]:
    """Spread the sample across durations so short and long clips are represented."""
    if limit <= 0 or limit >= len(files):
        return sorted(files, key=lambda path: path.name.casefold())
    measured = []
    for path in files:
        try:
            duration = float(probe(path)["format"]["duration"])
        except (ProcessingError, OSError, ValueError, KeyError):
            continue
        if duration >= MIN_TUNE_SECONDS:
            measured.append((duration, path))
    pool = measured or [(0.0, path) for path in files]
    pool.sort(key=lambda item: (item[0], item[1].name.casefold()))
    if len(pool) <= limit:
        return [path for _, path in pool]
    step = (len(pool) - 1) / (limit - 1)
    picked = [pool[round(index * step)] for index in range(limit)]
    return [path for _, path in picked]


def extract_window(source: Path, audio: dict, start: float, end: float, target: Path) -> None:
    command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
             "-ss", f"{start:.3f}", "-t", f"{max(0.05, end - start):.3f}",
             "-i", str(source), "-map", f"0:{audio['index']}", "-vn", "-ac", "2",
             "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(target)])


def render_candidate(raw: Path, candidate: dict, target: Path, work: Path,
                     deepfilter_executable: str | None,
                     source_loudness: float | None) -> dict:
    """Apply one candidate through the same chain preprocess uses.

    The candidate is measured before and after level matching so program
    removal can be told apart from noise reduction, and so every candidate is
    ranked at the source's own loudness.
    """
    denoised = raw
    engine = candidate["engine"]
    if engine == "deepfilter":
        if not deepfilter_executable:
            raise TuneError("DeepFilterNet executable disappeared mid-run")
        out_dir = work / f"{candidate['name']}-df"
        shutil.rmtree(out_dir, ignore_errors=True)
        denoised = preprocess.deepfilter(
            raw, out_dir, candidate.get("attenuation"),
            bool(candidate.get("post_filter")), candidate.get("beta", 0.02))
    elif engine == "ffmpeg":
        denoised = work / f"{candidate['name']}-denoised.wav"
        command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                 "-i", str(raw), "-af", f"afftdn=nr={candidate['nr']}:tn=1",
                 "-c:a", "pcm_s16le", str(denoised)])
    staged = denoised
    if candidate["highpass"]:
        staged = work / f"{candidate['name']}-highpass.wav"
        command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                 "-i", str(denoised), "-af", f"highpass=f={candidate['highpass']}",
                 "-c:a", "pcm_s16le", str(staged)])
    loudness = preprocess.measure_loudness(staged)
    lost_db = (source_loudness - loudness
               if source_loudness is not None and loudness is not None else 0.0)
    match_db = preprocess.level_match_db(loudness, source_loudness)
    command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(staged), "-af",
             f"volume={match_db:.2f}dB,"
             f"alimiter=limit={preprocess.LIMIT:.6f}:attack=5:release=50:level=0",
             "-ac", "2", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(target)])
    return {"content_loss_db": round(max(0.0, lost_db), 2),
            "level_match_db": round(match_db, 2)}


def analyze_window(path: Path) -> dict:
    """Describe noise floor, speech level, and speech-band content of one window."""
    rate, samples = pcm16(path)
    mono = samples.mean(axis=1)
    hop = max(1, int(ANALYSIS_HOP_SECONDS * rate))
    frames = len(mono) // hop
    if frames < 4:
        raise TuneError("window is too short to measure")
    blocks = mono[:frames * hop].reshape(frames, hop)
    levels = 20 * np.log10(np.maximum(np.sqrt(np.mean(blocks ** 2, axis=1)), 1e-6))
    noise = float(np.percentile(levels, 10))
    speech = float(np.percentile(levels, 90))
    quiet = levels[levels <= noise + 6.0]
    spectrum = np.abs(np.fft.rfft(mono * np.hanning(len(mono)))) ** 2
    freqs = np.fft.rfftfreq(len(mono), 1.0 / rate)
    band = float(spectrum[(freqs >= BAND_LOW_HZ) & (freqs <= BAND_HIGH_HZ)].sum()
                 / max(spectrum.sum(), 1e-12))
    return {
        "duration_seconds": round(len(mono) / rate, 3),
        "noise_floor_dbfs": round(noise, 2),
        "speech_level_dbfs": round(speech, 2),
        "snr_db": round(speech - noise, 2),
        "noise_modulation_db": round(float(quiet.std()) if quiet.size >= 3 else 0.0, 2),
        "peak_dbfs": round(20 * math.log10(max(float(np.max(np.abs(mono))), 1e-9)), 2),
        "clip_ratio": round(float(np.mean(np.abs(mono) >= 0.999)), 8),
        "speech_band_ratio": round(band, 4),
    }


def aggregate(measurements: list[dict]) -> dict:
    keys = [key for key, value in measurements[0].items() if isinstance(value, (int, float))]
    totals = {key: float(np.mean([measurement[key] for measurement in measurements]))
              for key in keys}
    return {key: round(value, 4) for key, value in totals.items()}


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def score_candidate(metrics: dict, source: dict) -> tuple[float, list[str]]:
    """Score a candidate against the source window and list fidelity issues.

    Weights favour noise reduction and speech-band SNR because those are what
    the enhancement is for, while the small terms keep a candidate from winning
    through over-suppression, level jumps, or a hollowed speech band.
    """
    noise_reduction = source["noise_floor_dbfs"] - metrics["noise_floor_dbfs"]
    snr_gain = metrics["snr_db"] - source["snr_db"]
    band_ratio = (metrics["speech_band_ratio"] / source["speech_band_ratio"]
                  if source["speech_band_ratio"] else 1.0)
    level_drift = abs(metrics["speech_level_dbfs"] - source["speech_level_dbfs"])
    score = 100.0 * (
        0.40 * clamp01(noise_reduction / 18.0)
        + 0.30 * clamp01(snr_gain / 12.0)
        + 0.15 * clamp01(min(band_ratio, 1.0))
        + 0.10 * clamp01(1.0 - metrics["noise_modulation_db"] / 12.0)
        + 0.05 * clamp01(1.0 - level_drift / LEVEL_DRIFT_DB)
    )
    issues = []
    if metrics["peak_dbfs"] > -0.5 or metrics["clip_ratio"] > 0:
        issues.append("clipping")
    if band_ratio < 0.75:
        issues.append("speech-band loss")
    if metrics.get("content_loss_db", 0.0) > preprocess.CONTENT_LOSS_DB:
        issues.append("content loss")
    if noise_reduction > 25.0:
        issues.append("over-suppressed")
    if level_drift > LEVEL_DRIFT_DB:
        issues.append("level drift")
    return round(score, 2), issues


def measurable_gain(candidate: dict, source: dict) -> bool:
    """Whether a candidate removed noise or raised SNR against the source."""
    metrics = candidate.get("metrics")
    if not metrics or not source:
        return True
    noise_cut = source["noise_floor_dbfs"] - metrics["noise_floor_dbfs"]
    snr_gain = metrics["snr_db"] - source["snr_db"]
    return noise_cut >= MIN_NOISE_CUT_DB or snr_gain >= MIN_SNR_GAIN_DB


def choose(scored: list[dict], margin: float, source: dict | None = None) -> dict:
    """Pick the best candidate, but only replace the status quo for a reason.

    The default chain is the status quo and no-denoise is the conservative
    fallback. A candidate has to clear the fidelity gates, beat the anchor by
    more than the measurement margin, and measurably reduce noise before it is
    worth applying.
    """
    valid = [item for item in scored
             if not set(item["issues"]) & set(FIDELITY_ISSUES)]
    if not valid:
        return {"chosen": None, "reason": "every candidate failed the fidelity gates"}
    baseline = next((item for item in scored if item["name"] == BASELINE), None)
    valid_baseline = baseline if baseline in valid else None
    leave_alone = next((item for item in valid if item["name"] == "none"), None)
    best = max(valid, key=lambda item: item["score"])
    if best["name"] == BASELINE:
        return {"chosen": BASELINE, "reason": "the current default scored highest"}
    if valid_baseline and best["score"] - valid_baseline["score"] <= margin:
        return {"chosen": BASELINE,
                "reason": f"{best['name']} leads {BASELINE} by "
                          f"{best['score'] - valid_baseline['score']:.2f} <= margin "
                          f"{margin:g}; kept the current default"}
    kept = BASELINE if valid_baseline else "none"
    if leave_alone and best["name"] != "none" \
            and not measurable_gain(best, source):
        return {"chosen": kept,
                "reason": f"{best['name']} did not measurably reduce noise; kept {kept}"}
    if not valid_baseline and leave_alone and best["name"] != "none" \
            and best["score"] - leave_alone["score"] <= margin:
        return {"chosen": "none",
                "reason": f"{best['name']} leads no-denoise by "
                          f"{best['score'] - leave_alone['score']:.2f} <= margin "
                          f"{margin:g}; kept the source"}
    runner = max((item for item in valid if item["name"] != best["name"]),
                 key=lambda item: item["score"], default=None)
    lead = (f"{best['score'] - runner['score']:.2f} ahead of {runner['name']} "
            f"({runner['score']:.2f})" if runner else "the only eligible candidate")
    reason = f"{best['name']} scored {best['score']:.2f}, {lead}"
    if baseline and not valid_baseline:
        reason += (f"; the current default was disqualified "
                   f"({', '.join(baseline['issues'])})")
    return {"chosen": best["name"], "reason": reason}


def tune_clip(source: Path, output_root: Path, candidates: list[dict], args, log,
              deepfilter_executable: str | None) -> dict:
    folder = output_root / source.name.rsplit(".", 1)[0]
    folder.mkdir(parents=True, exist_ok=True)
    profile_path = folder / "profile.json"
    if profile_path.exists() and not args.force:
        previous = json.loads(profile_path.read_text(encoding="utf-8"))
        if previous.get("source_bytes") == source.stat().st_size \
                and previous.get("tune_version") == TUNE_VERSION:
            log(f"{source.name}: profile current -> {previous.get('chosen')}")
            return previous
    info = probe(source)
    video, audio = streams(info)
    if not audio:
        log(f"{source.name}: no audio track; nothing to tune")
        return {}
    duration = float(info["format"]["duration"])
    windows = windows_for(duration, args.sample)
    candidate_dir = folder / "candidates"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    per_candidate: dict[str, list[dict]] = {candidate["name"]: [] for candidate in candidates}
    source_measurements = []
    with tempfile.TemporaryDirectory(prefix="tune-", dir=folder) as scratch:
        work = Path(scratch)
        for index, (start, end) in enumerate(windows, 1):
            raw = work / f"window-{index}.wav"
            extract_window(source, audio, start, end, raw)
            source_measurements.append(analyze_window(raw))
            source_loudness = preprocess.measure_loudness(raw)
            for candidate in candidates:
                rendered = candidate_dir / f"window-{index}-{candidate['name']}.wav"
                staging = work / f"{candidate['name']}.wav"
                render_info = render_candidate(raw, candidate, staging, work,
                                               deepfilter_executable, source_loudness)
                shutil.move(str(staging), str(rendered))
                per_candidate[candidate["name"]].append(
                    {**analyze_window(rendered), **render_info})
    source_summary = aggregate(source_measurements)
    scored = []
    for candidate in candidates:
        summary = aggregate(per_candidate[candidate["name"]])
        score, issues = score_candidate(summary, source_summary)
        scored.append({"name": candidate["name"], "params": candidate, "score": score,
                       "issues": issues, "metrics": summary})
    decision = choose(scored, args.margin, source_summary)
    valid_scores = sorted((item for item in scored
                           if not set(item["issues"]) & set(FIDELITY_ISSUES)),
                          key=lambda item: item["score"], reverse=True)
    runner = next((item for item in valid_scores if item["name"] != decision["chosen"]), None)
    profile = {
        "clip": source.name,
        "source": str(source),
        "source_bytes": source.stat().st_size,
        "duration_seconds": round(duration, 3),
        "tune_version": TUNE_VERSION,
        "sampled_windows": [list(window) for window in windows],
        "source_metrics": source_summary,
        "candidates": scored,
        "chosen": decision["chosen"],
        "reason": decision["reason"],
        "runner_up": runner["name"] if runner else None,
        "runner_up_score": runner["score"] if runner else None,
    }
    (folder / "metrics.json").write_text(
        json.dumps({"source": source_summary,
                    "candidates": [{"name": item["name"], "metrics": item["metrics"],
                                    "score": item["score"], "issues": item["issues"]}
                                   for item in scored]}, indent=2) + "\n", encoding="utf-8")
    profile_path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    if getattr(args, "discard_audio", False):
        shutil.rmtree(candidate_dir, ignore_errors=True)
    log(f"{source.name}: {profile['chosen']} ({profile['reason']})")
    return profile


def write_summary(profiles: list[dict], output_root: Path) -> tuple[Path, Path]:
    rows = []
    for profile in profiles:
        chosen = next((item for item in profile["candidates"]
                       if item["name"] == profile["chosen"]), None)
        metrics = chosen["metrics"] if chosen else {}
        source = profile["source_metrics"]
        rows.append({
            "clip": profile["clip"],
            "chosen": profile["chosen"],
            "score": chosen["score"] if chosen else "",
            "runner_up": profile["runner_up"] or "",
            "runner_up_score": profile["runner_up_score"] if profile["runner_up"] else "",
            "noise_reduction_db": round(source["noise_floor_dbfs"]
                                        - metrics.get("noise_floor_dbfs", source["noise_floor_dbfs"]), 2),
            "snr_gain_db": round(metrics.get("snr_db", source["snr_db"]) - source["snr_db"], 2),
            "speech_band_ratio": metrics.get("speech_band_ratio", ""),
            "peak_dbfs": metrics.get("peak_dbfs", ""),
            "issues": ", ".join(chosen["issues"]) if chosen else "",
            "reason": profile["reason"],
        })
    csv_path = output_root / "tuning.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    html = ["<!doctype html><meta charset='utf-8'><title>Audio tuning</title>",
            "<style>body{font-family:system-ui;margin:2rem}"
            "table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:.3rem .5rem}"
            "td.num{text-align:right}</style>",
            "<h1>Audio tuning</h1>",
            "<p>Each candidate was rendered through the preprocess denoise and limiter "
            "chain and measured against the untouched source window. Listen before "
            "applying a profile.</p>", "<table>",
            "<tr><th>clip</th><th>chosen</th><th>score</th><th>runner-up</th>"
            "<th>noise cut dB</th><th>SNR gain dB</th><th>issues</th><th>why</th>"
            "<th>listen</th></tr>"]
    for profile in profiles:
        folder = output_root / profile["clip"].rsplit(".", 1)[0] / "candidates"
        chosen = profile["chosen"]
        players = []
        names = []
        for name in (BASELINE, chosen):
            if name and name not in names:
                names.append(name)
        for name in names:
            matches = sorted(folder.glob(f"window-1-{name}.wav"))
            if matches:
                relative = f"{folder.parent.name}/candidates/{matches[0].name}"
                players.append(f"<div>{name}: <audio controls preload='none' "
                               f"src='{quote(relative)}'></audio></div>")
        row = next(item for item in rows if item["clip"] == profile["clip"])
        html.append(
            f"<tr><td>{profile['clip']}</td><td>{chosen}</td>"
            f"<td class='num'>{row['score']}</td><td>{row['runner_up']}</td>"
            f"<td class='num'>{row['noise_reduction_db']}</td>"
            f"<td class='num'>{row['snr_gain_db']}</td>"
            f"<td>{row['issues']}</td><td>{profile['reason']}</td>"
            f"<td>{''.join(players)}</td></tr>")
    html.append("</table>")
    html_path = output_root / "tuning.html"
    html_path.write_text("\n".join(html) + "\n", encoding="utf-8")
    return csv_path, html_path


def resolve_draft(args) -> Path:
    if getattr(args, "folder", None):
        draft = Path(args.folder).expanduser().resolve()
        if not draft.is_dir():
            raise TuneError(f"folder not found: {draft}")
        return draft
    from common import channel_root, select_channels
    if not args.draft or Path(args.draft).name != args.draft:
        raise TuneError("pass a draft folder name with --draft, or a path with --folder")
    slug, _ = select_channels(args.cfg, args.channel)[0]
    draft = channel_root(args.cfg, slug) / "drafts" / args.draft
    if not draft.is_dir():
        raise TuneError(f"draft not found: {draft}")
    return draft


def run(cfg: dict, args, log) -> int:
    args.cfg = cfg
    try:
        draft = resolve_draft(args)
        files = ordering.camera_files(draft)
        if args.clip:
            wanted = {name.casefold() for name in args.clip}
            files = [path for path in files
                     if path.name.casefold() in wanted
                     or ordering.original_name(path.name).casefold() in wanted]
        if not files:
            raise TuneError("no camera clips to tune")
        selected = select_clips(files, args.limit) if not args.clip else files
        executable = find_deepfilter()
        candidates = candidate_grid(executable)
        output_root = (Path(args.out).expanduser().resolve() if args.out
                       else draftlayout.internal_dir(draft) / "analysis" / "tuning")
        output_root.mkdir(parents=True, exist_ok=True)
        log(f"tune: {len(selected)} clip(s), {len(candidates)} candidates, "
            f"engine {'deepfilter' if executable else 'ffmpeg'}")
        profiles = []
        failed = 0
        for source in selected:
            try:
                profile = tune_clip(source, output_root, candidates, args,
                                    log, executable)
            except (TuneError, ProcessingError, OSError, ValueError) as exc:
                failed += 1
                log(f"{source.name}: {exc}")
                continue
            if profile:
                profiles.append(profile)
        if profiles:
            merged = {profile["clip"]: profile for profile in profiles}
            for path in sorted(output_root.glob("*/profile.json")):
                try:
                    profile = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                if profile.get("tune_version") == TUNE_VERSION:
                    merged.setdefault(profile["clip"], profile)
            csv_path, html_path = write_summary(list(merged.values()), output_root)
            log(f"tune: profiles -> {csv_path}")
            log(f"tune: listen -> {html_path}")
        log(f"tune: {len(profiles)} profiled, {failed} failed")
        return 1 if failed else 0
    except (TuneError, ProcessingError, OSError, ValueError) as exc:
        log(f"tune: {exc}")
        return 1


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel")
    parser.add_argument("--draft")
    parser.add_argument("--folder")
    parser.add_argument("--clip", action="append")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--sample", type=float, default=40.0)
    parser.add_argument("--margin", type=float, default=DEFAULT_MARGIN)
    parser.add_argument("--out")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--discard-audio", action="store_true")
    args = parser.parse_args(argv)
    return run({"workspace": "", "channels": {}}, args, print)


if __name__ == "__main__":
    sys.exit(main())
