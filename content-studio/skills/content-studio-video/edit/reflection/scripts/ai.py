#!/usr/bin/env python3
"""AI reflection review pass driven by the DSRNet backend.

This entrypoint runs a pretrained single-image reflection removal network over a
video, transfers only the model's low-frequency correction back onto the native
frame, and writes a review package with before/after metrics. It never claims
that a strong, content-rich reflection was reconstructed: the result is always
``review_required`` and is rejected when it changes luma, saturation, clipping,
sharpness, or temporal stability beyond the safety gates.

Torch is imported lazily so the rest of the reflection skill keeps working on
machines without a GPU stack.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if parent.name == "content-studio-video")
sys.path.insert(0, str(ROOT / "shared"))
sys.path.insert(0, str(ROOT / "edit" / "clip-edit" / "scripts"))
sys.path.insert(0, str(ROOT / "edit" / "reflection" / "backends"))

import enhance  # noqa: E402
import reflection  # noqa: E402

SCHEMA_VERSION = 1
TOOL_VERSION = "1"
SAMPLE_WIDTH = 640
MAX_SAMPLES = 8
STRENGTH = 1.0
MAX_WIDTH = 640
CANDIDATE_MINIMUM = 0.0015
CANDIDATE_RELATIVE = 0.05
LUMA_LIMIT = 0.05
SATURATION_LIMIT = 0.05
CLIP_LIMIT = 0.02
SHARPNESS_LOW = 0.85
SHARPNESS_HIGH = 1.20
FLICKER_LIMIT = 1.35
REFLECTION_FLOOR = 0.002
AUDIO_CODEC = "copy"


def detail_preserving_fuse(native: np.ndarray, clean_low: np.ndarray,
                           input_low: np.ndarray, strength: float) -> np.ndarray:
    """Apply the model's low-frequency correction without losing native detail.

    ``clean_low`` and ``input_low`` are the model output and the resized input,
    both upscaled to the native frame size. Their difference isolates the
    low-frequency change; the native frame keeps its own high-frequency detail,
    so no resampling blur or tile seams are introduced.
    """
    if strength <= 0.0:
        return native.copy()
    delta = np.clip(clean_low, 0.0, 1.0) - input_low
    return np.clip(native + float(strength) * delta, 0.0, 1.0)


def sample_metrics(rgb: np.ndarray) -> dict:
    """Measure a frame at the detector's 640 px analysis width."""
    if rgb.shape[1] != SAMPLE_WIDTH:
        image = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
        scale = SAMPLE_WIDTH / image.width
        image = image.resize((SAMPLE_WIDTH, max(2, int(round(image.height * scale)))),
                             Image.BICUBIC)
        rgb = np.asarray(image, dtype=np.float32) / 255.0
    parts = reflection.reflection_masks(rgb)
    metrics = enhance.frame_metrics(rgb)
    return {
        "candidate_fraction": round(reflection.fraction(parts["candidate"]), 5),
        "glare_fraction": round(reflection.fraction(parts["glare"]), 5),
        "veil_fraction": round(reflection.fraction(parts["veil"]), 5),
        "luma_mean": round(metrics["luma_mean"], 5),
        "saturation_mean": round(metrics["saturation_mean"], 5),
        "clip_high": round(metrics["clip_high"], 5),
        "sharpness": round(metrics["sharpness"], 5),
    }


def _mean(samples: list[dict], key: str) -> float:
    return float(np.mean([sample[key] for sample in samples])) if samples else 0.0


def evaluate(samples: list[dict], reflection_energy: float,
             flicker_ratio: float | None) -> dict:
    """Turn before/after metrics into a gated decision and a check list."""
    before = {key: _mean([sample["before"] for sample in samples], key)
              for key in ("candidate_fraction", "glare_fraction", "luma_mean",
                          "saturation_mean", "clip_high", "sharpness")}
    after = {key: _mean([sample["after"] for sample in samples], key)
             for key in before}
    reduction = before["candidate_fraction"] - after["candidate_fraction"]
    relative = reduction / max(before["candidate_fraction"], 1e-6)
    sharpness_ratio = after["sharpness"] / max(before["sharpness"], 1e-6)

    checks = [
        {
            "id": "backend_detected_reflection",
            "value": round(reflection_energy, 5),
            "minimum": REFLECTION_FLOOR,
            "passed": reflection_energy >= REFLECTION_FLOOR,
            "note": "mean absolute predicted reflection layer; below the floor the backend abstains",
        },
        {
            "id": "candidate_reduction",
            "value": round(reduction, 5),
            "relative": round(relative, 4),
            "minimum": CANDIDATE_MINIMUM,
            "passed": reduction >= CANDIDATE_MINIMUM or relative >= CANDIDATE_RELATIVE,
        },
        {
            "id": "luma_change",
            "value": round(abs(after["luma_mean"] - before["luma_mean"]), 5),
            "maximum": LUMA_LIMIT,
            "passed": abs(after["luma_mean"] - before["luma_mean"]) <= LUMA_LIMIT,
        },
        {
            "id": "saturation_change",
            "value": round(abs(after["saturation_mean"] - before["saturation_mean"]), 5),
            "maximum": SATURATION_LIMIT,
            "passed": abs(after["saturation_mean"] - before["saturation_mean"]) <= SATURATION_LIMIT,
        },
        {
            "id": "clipping_increase",
            "value": round(after["clip_high"] - before["clip_high"], 5),
            "maximum": CLIP_LIMIT,
            "passed": after["clip_high"] - before["clip_high"] <= CLIP_LIMIT,
        },
        {
            "id": "sharpness_ratio",
            "value": round(sharpness_ratio, 4),
            "range": [SHARPNESS_LOW, SHARPNESS_HIGH],
            "passed": SHARPNESS_LOW <= sharpness_ratio <= SHARPNESS_HIGH,
        },
    ]
    if flicker_ratio is not None:
        checks.append({
            "id": "temporal_flicker",
            "value": round(flicker_ratio, 4),
            "maximum": FLICKER_LIMIT,
            "passed": flicker_ratio <= FLICKER_LIMIT,
        })

    failures = [check["id"] for check in checks if not check["passed"]]
    if any(item in failures for item in
           ("luma_change", "saturation_change", "clipping_increase",
            "sharpness_ratio", "temporal_flicker")):
        decision = "REJECTED"
        reason = "safety gate failed; the AI correction is not safe to review"
    elif "candidate_reduction" in failures or "backend_detected_reflection" in failures:
        decision = "SKIP"
        reason = "the pretrained backend did not measurably reduce the reflection"
    else:
        decision = "REVIEW"
        reason = "measurable reduction; human inspection of the delivered frames is required"

    return {
        "decision": decision,
        "reason": reason,
        "review": {"required": True, "status": "review_required"},
        "before": {key: round(value, 5) for key, value in before.items()},
        "after": {key: round(value, 5) for key, value in after.items()},
        "checks": checks,
        "failed_checks": failures,
    }


def _read_exact(stream, size: int) -> bytes:
    chunks, remaining = [], size
    while remaining:
        block = stream.read(remaining)
        if not block:
            break
        chunks.append(block)
        remaining -= len(block)
    return b"".join(chunks)


def _decoder(source: Path, width: int, height: int) -> subprocess.Popen:
    return subprocess.Popen(
        ["ffmpeg", "-nostdin", "-v", "error", "-i", str(source),
         "-map", "0:v:0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _encoder(output: Path, source: Path, width: int, height: int, fps: str) -> subprocess.Popen:
    return subprocess.Popen(
        ["ffmpeg", "-nostdin", "-y", "-v", "error",
         "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{width}x{height}", "-r", fps, "-i", "-",
         "-i", str(source),
         "-map", "0:v:0", "-map", "1:a?",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-c:a", AUDIO_CODEC, "-shortest",
         "-movflags", "+faststart",
         "-metadata", "comment=AI reflection review pass (DSRNet); review required",
         str(output)],
        stdin=subprocess.PIPE, stderr=subprocess.PIPE)


def _write_contact_sheet(paths: list[Path], target: Path, columns: int = 4,
                         width: int = 320) -> None:
    if not paths:
        return
    thumbs = []
    for item in paths:
        image = Image.open(item).convert("RGB")
        height = max(1, int(round(image.height * width / image.width)))
        thumbs.append(image.resize((width, height), Image.BICUBIC))
    rows = math.ceil(len(thumbs) / columns)
    cell_height = max(image.height for image in thumbs)
    sheet = Image.new("RGB", (columns * width, rows * cell_height), (12, 12, 12))
    for index, image in enumerate(thumbs):
        sheet.paste(image, ((index % columns) * width, (index // columns) * cell_height))
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target, quality=90)


def _compare_clip(source: Path, output: Path, target: Path,
                  seconds: float | None) -> Path | None:
    length = ["-t", f"{seconds:.3f}"] if seconds else []
    try:
        enhance.run([
            "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
            *length, "-i", str(source), *length, "-i", str(output),
            "-filter_complex",
            "[0:v]scale=960:-2,setpts=PTS-STARTPTS[a];"
            "[1:v]scale=960:-2,setpts=PTS-STARTPTS[b];"
            "[a][b]hstack=inputs=2[v]",
            "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "22", "-pix_fmt", "yuv420p", str(target)])
        return target
    except enhance.EnhanceError:
        target.unlink(missing_ok=True)
        return None


def _write_report_markdown(report: dict, target: Path) -> None:
    metrics = report["metrics"]
    before = metrics["before"]
    after = metrics["after"]
    lines = [
        f"# AI reflection review - {report['source']['name']}",
        "",
        f"- Decision: **{report['decision']['decision']}**",
        f"- Reason: {report['decision']['reason']}",
        f"- Backend: {report['backend']['name']} ({report['backend']['license']})",
        f"- Checkpoint SHA-256: `{report['backend']['checkpoint']['sha256']}`",
        f"- Working size: {report['backend']['work_size'][0]}x{report['backend']['work_size'][1]}",
        f"- Strength: {report['processing']['strength']}",
        f"- Runtime: {report['processing']['total_seconds']:.1f}s for "
        f"{report['processing']['frames']} frames "
        f"({report['processing']['seconds_per_frame']:.2f}s/frame)",
        "",
        "| Metric | Before | After |",
        "| --- | --- | --- |",
    ]
    for key in ("candidate_fraction", "glare_fraction", "luma_mean",
                "saturation_mean", "clip_high", "sharpness"):
        lines.append(f"| {key} | {before[key]:.5f} | {after[key]:.5f} |")
    lines.extend(["", "## Gates", "", "| Gate | Value | Passed |", "| --- | --- | --- |"])
    for check in report["decision"]["checks"]:
        lines.append(f"| {check['id']} | {check['value']} | {check['passed']} |")
    if report["artifacts"]:
        lines.extend(["", "## Artifacts", ""])
        lines.extend(f"- `{item}`" for item in report["artifacts"])
    lines.extend([
        "",
        "A review result is provisional. Compare the delivered frames and clip "
        "against the source; a successful encode or a lower candidate fraction is "
        "not proof that a strong reflection was reconstructed.",
    ])
    target.write_text("\n".join(lines), encoding="utf-8")


def run(source: Path, output: Path, work: Path, max_width: int = MAX_WIDTH,
        strength: float = STRENGTH, weights: Path | None = None,
        download: bool = False, limit_seconds: float | None = None,
        device: str | None = None, backend=None) -> dict:
    from dsrnet.geometry import working_size

    source = Path(source)
    output = Path(output)
    work = Path(work)
    if output.resolve() == source.resolve():
        raise reflection.ReflectionError("output must differ from the source")

    metadata = enhance.probe_video(source)
    if (metadata.get("color_transfer") or "").lower() in {"smpte2084", "arib-std-b67"}:
        raise reflection.ReflectionError(
            "HDR/HLG source: record an explicit tone-map decision before AI reflection work")

    width = int(metadata["display_width"])
    height = int(metadata["display_height"])
    fps_value = str(metadata.get("fps") or "0/0")
    numerator, _, denominator = fps_value.partition("/")
    fps = float(numerator) / float(denominator or 1) if float(denominator or 1) else 30.0
    source_hash = enhance.sha256_file(source)

    if backend is None:
        from dsrnet.infer import DSRNetBackend, download_checkpoint

        if weights is None and download:
            weights = download_checkpoint()
        backend = DSRNetBackend(weights=weights, device=device)
    work_width, work_height = working_size(width, height, max_width)

    work.mkdir(parents=True, exist_ok=True)
    keys = work / "keys"
    keys.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)

    decoder = _decoder(source, width, height)
    encoder = _encoder(output, source, width, height, fps_value)
    frame_bytes = width * height * 3
    total = int(round(metadata["duration_seconds"] * fps))
    if limit_seconds:
        total = min(total, int(round(limit_seconds * fps)))
    stride = max(1, total // MAX_SAMPLES)
    samples, artifact_keys = [], []
    reflection_energy = 0.0
    flicker_in, flicker_out = [], []
    previous_in = previous_out = None
    processed = 0

    started = time.perf_counter()
    try:
        for index in range(total):
            buffer = _read_exact(decoder.stdout, frame_bytes)
            if len(buffer) != frame_bytes:
                break
            native = np.frombuffer(buffer, np.uint8).reshape(height, width, 3)
            native = native.astype(np.float32) / 255.0
            layers = backend.reflect(native, max_width=max_width)
            fused = detail_preserving_fuse(native, layers["clean_low"],
                                           layers["input_low"], strength)
            encoder.stdin.write((fused * 255.0 + 0.5).astype(np.uint8).tobytes())

            energy = float(np.abs(layers["reflection"]).mean())
            reflection_energy += energy

            before_small = layers["small"]
            after_small = backend.resize(fused, work_width, work_height)
            if index % stride == 0:
                samples.append({
                    "frame": index,
                    "at_seconds": round(index / fps, 3),
                    "before": sample_metrics(before_small),
                    "after": sample_metrics(after_small),
                    "reflection_energy": round(energy, 5),
                })
                stem = f"frame-{index:04d}"
                Image.fromarray((native * 255).astype(np.uint8)).save(keys / f"{stem}-input.png")
                Image.fromarray((fused * 255).astype(np.uint8)).save(keys / f"{stem}-output.png")
                amplified = np.clip(layers["reflection"] * 4.0 + 0.5, 0, 1)
                Image.fromarray((amplified * 255).astype(np.uint8)).save(
                    keys / f"{stem}-reflection.png")
                side = Image.new("RGB", (width * 2, height))
                side.paste(Image.fromarray((native * 255).astype(np.uint8)), (0, 0))
                side.paste(Image.fromarray((fused * 255).astype(np.uint8)), (width, 0))
                side.resize((1280, int(round(height * 1280 / (width * 2)))),
                            Image.BICUBIC).save(keys / f"{stem}-side.jpg", quality=90)
                artifact_keys.append(keys / f"{stem}-side.jpg")

            if previous_in is not None:
                flicker_in.append(float(np.abs(before_small - previous_in).mean()))
                flicker_out.append(float(np.abs(after_small - previous_out).mean()))
            previous_in, previous_out = before_small, after_small
            processed = index + 1
            if processed % 30 == 0:
                rate = (time.perf_counter() - started) / processed
                print(f"  {processed}/{total} frames  {rate:.2f}s/frame", file=sys.stderr)
    finally:
        encoder.stdin.close()
        decoder.stdout.close()
        if decoder.poll() is None:
            decoder.terminate()
        encoder_error = encoder.stderr.read().decode("utf-8", "replace")
        encoder.stderr.close()
        if encoder.wait() != 0:
            raise reflection.ReflectionError(f"encoder failed: {encoder_error[-2000:]}")
        decoder_error = decoder.stderr.read().decode("utf-8", "replace")
        decoder.stderr.close()
        if decoder.wait() not in (0, -15) and not processed:
            raise reflection.ReflectionError(f"decoder failed: {decoder_error[-2000:]}")

    elapsed = time.perf_counter() - started
    backend.close()

    in_energy = float(np.mean(flicker_in)) if flicker_in else 0.0
    out_energy = float(np.mean(flicker_out)) if flicker_out else 0.0
    flicker_ratio = (out_energy / in_energy) if in_energy > 1e-6 else None
    decision = evaluate(samples, reflection_energy / max(processed, 1), flicker_ratio)

    compare = work / "compare.mp4"
    compare_path = _compare_clip(source, output, compare, limit_seconds)
    sheet = work / "contact-sheet.jpg"
    _write_contact_sheet(artifact_keys, sheet)

    artifacts = [str(output)]
    for item in (compare_path, sheet, *artifact_keys):
        if item and Path(item).is_file():
            artifacts.append(str(item))

    report = {
        "schema_version": SCHEMA_VERSION,
        "tool": {"name": "content-studio-video-reflection", "method": "ai",
                 "version": TOOL_VERSION},
        "generated_at": enhance.now(),
        "source": {
            "path": str(source),
            "name": source.name,
            "sha256": source_hash,
            "width": width,
            "height": height,
            "fps": fps_value,
            "duration_seconds": round(float(metadata["duration_seconds"]), 4),
            "has_audio": bool(metadata.get("has_audio")),
            "color_transfer": metadata.get("color_transfer"),
        },
        "backend": {
            "name": "DSRNet (XReflection)",
            "license": "Apache-2.0",
            "source": "https://github.com/hainuo-wang/XReflection",
            "checkpoint": {
                "url": "https://checkpoints.mingjia.li/dsr-25.8915.ckpt",
                "path": str(backend.weights),
                "sha256": "337e23a63fd93fc154330a6bbe21894ebd030fe9b8fa68ea7a6c8173e90f83aa",
                "bytes": 1657092053,
            },
            "work_size": [work_width, work_height],
            "precision": "float16" if backend.half else "float32",
            "device": backend.device,
            "peak_memory_mb": round(backend.peak_memory_mb, 1),
        },
        "processing": {
            "frames": processed,
            "strength": round(float(strength), 3),
            "max_width": int(max_width),
            "total_seconds": round(elapsed, 2),
            "seconds_per_frame": round(elapsed / max(processed, 1), 3),
            "reflection_energy": round(reflection_energy / max(processed, 1), 5),
            "flicker": {
                "source_step": round(in_energy, 5),
                "output_step": round(out_energy, 5),
                "ratio": None if flicker_ratio is None else round(flicker_ratio, 4),
            },
        },
        "metrics": {
            "before": decision["before"],
            "after": decision["after"],
            "samples": samples,
        },
        "decision": {
            "decision": decision["decision"],
            "reason": decision["reason"],
            "review": decision["review"],
            "checks": decision["checks"],
            "failed_checks": decision["failed_checks"],
        },
        "artifacts": artifacts,
    }
    (work / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    _write_report_markdown(report, work / "report.md")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, type=Path, help="source clip")
    parser.add_argument("--output", required=True, type=Path, help="rendered review clip")
    parser.add_argument("--work", type=Path, help="evidence directory")
    parser.add_argument("--weights", type=Path, help="DSRNet checkpoint path")
    parser.add_argument("--download", action="store_true",
                        help="download the checkpoint on first use")
    parser.add_argument("--max-width", type=int, default=MAX_WIDTH,
                        help="model working width, rounded down to a multiple of 32")
    parser.add_argument("--strength", type=float, default=STRENGTH,
                        help="fraction of the predicted reflection correction to apply")
    parser.add_argument("--seconds", type=float,
                        help="limit processing to the first N seconds")
    parser.add_argument("--device", choices=("cuda", "cpu"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = args.file
    if not source.is_file():
        raise SystemExit(f"source not found: {source}")
    work = args.work or (args.output.parent / ".content-studio" / "reflection"
                         / source.stem)
    try:
        report = run(source, args.output, work, max_width=args.max_width,
                     strength=args.strength, weights=args.weights,
                     download=args.download, limit_seconds=args.seconds,
                     device=args.device)
    except (reflection.ReflectionError, FileNotFoundError) as error:
        print(f"ai reflection: {error}", file=sys.stderr)
        return 2
    summary = report["decision"]
    print(f"{summary['decision']}: {summary['reason']}")
    print(f"report: {work / 'report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
