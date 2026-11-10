"""Generate bounded, synthetic timeline-method evidence without production approval."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(SKILL.parent / "shared"))
import compiler  # noqa: E402
import model  # noqa: E402
from preview_gif import write_comparison  # noqa: E402

WORK = ROOT / "tmp/capability-gallery/timeline"
OUT = SKILL / "previews/methods"
WORK.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)


def run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-1000:])


def source(name, video_filter, audio_filter, video_lavfi=None):
    path = WORK / f"{name}.mp4"
    video_lavfi = video_lavfi or "testsrc2=size=160x90:rate=12:duration=2"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", video_lavfi,
         "-f", "lavfi", "-i", audio_filter,
         "-vf", video_filter, "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-shortest", str(path)])
    return path


def base_timeline(video):
    plan = WORK / "preflight/plan.json"
    plan.parent.mkdir(exist_ok=True)
    plan.write_text(json.dumps({"schema_version": 1, "kind": "edited",
                                "stage": "edited-render", "steps": [{"id": "S01"}]}),
                    encoding="utf-8")
    # The fixture record is intentionally synthetic and is never used for a
    # production render or presented as a human editor's approval.
    plan.with_name("approval.json").write_text(json.dumps({
        "plan_sha256": model.sha256_file(plan),
        "review_note": "Synthetic gallery fixture, no human approval"}),
        encoding="utf-8")
    plan.with_name("checklist.json").write_text(json.dumps({
        "plan_sha256": model.sha256_file(plan), "items": [{"id": "S01"}]}),
        encoding="utf-8")
    timeline = model.make_initial(plan, video, WORK / "unused-final.mp4",
                                  fps=12, width=320, height=180)
    timeline["picture"][0]["source_out"] = 2
    timeline["video_preset"] = "veryfast"
    return timeline


def render(timeline, filename):
    resolved = model.validate(timeline, require_review=False)
    target = WORK / filename
    # The gallery reruns into its own temporary directory; the production
    # renderer still refuses to overwrite an existing delivery file.
    if target.is_file():
        target.unlink()
    compiler.preview(timeline, resolved, target, 0, 2)
    return target


def audio_mp3(video, target):
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i",
         str(video), "-vn", "-c:a", "libmp3lame", "-q:a", "5", str(target)])


def main():
    tone = "sine=frequency=440:sample_rate=48000:duration=2"
    normal = source("normal", "format=yuv420p", tone)
    clean_title = source("clean-title", "format=yuv420p", tone,
                         "smptebars=size=160x90:rate=12:duration=2")
    noisy = source("noisy", "noise=alls=25:allf=t", tone)
    flicker = source("flicker", "eq=brightness='0.16*sin(2*PI*n/4)':eval=frame", tone)
    sources = {"normal": normal, "noisy": noisy, "flicker": flicker}
    methods = [
        ("crop", "normal", {"x": .16, "y": .12, "w": .68, "h": .76}),
        ("lens-correction", "normal", {"k1": .3, "k2": .05}),
        ("denoise-light", "noisy", {}),
        ("denoise-medium", "noisy", {}),
        ("deflicker", "flicker", {}),
        ("upscale-lanczos", "normal", {"scale": 2}),
        ("color-eq", "normal", {"contrast": 1.3, "brightness": .08,
                                 "saturation": 1.4}),
        ("sharpen-light", "normal", {}),
        ("sharpen-medium", "normal", {}),
    ]
    baseline = {key: render(base_timeline(path), f"{key}-baseline.mp4")
                for key, path in sources.items()}
    baseline["clean-title"] = render(base_timeline(clean_title),
                                      "clean-title-baseline.mp4")
    for method, source_key, args in methods:
        timeline = base_timeline(sources[source_key])
        timeline["operations"] = [{"id": method, "method": method,
                                    "start": 0, "end": 2,
                                    "review_status": "pending_review", **args}]
        output = render(timeline, f"{method}.mp4")
        write_comparison([baseline[source_key], output],
                         ["BEFORE", f"AFTER: {method}"], OUT / f"{method}.gif",
                         duration=2, fps=8)
        print(method, "picture", flush=True)

    font = WORK / "font.ttf"
    font.write_bytes(Path("C:/Windows/Fonts/arial.ttf").read_bytes())
    ass = WORK / "graphic.ass"
    ass.write_text("""[Script Info]
ScriptType: v4.00+
PlayResX: 320
PlayResY: 180
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,28,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,1,0,2,20,20,20,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,TIMELINE GRAPHIC
""", encoding="utf-8")
    for method, extra in [
        ("title", {"text": "TIMELINE TITLE", "font_source": font.name,
                   "font_sha256": model.sha256_file(font)}),
        ("motion-graphics-ass", {"source": ass.name,
                                 "sha256": model.sha256_file(ass)}),
    ]:
        picture_source = clean_title if method == "title" else normal
        timeline = base_timeline(picture_source)
        timeline["operations"] = [{"id": method, "method": method,
                                    "start": 0, "end": 2,
                                    "review_status": "pending_review", **extra}]
        output = render(timeline, f"{method}.mp4")
        baseline_key = "clean-title" if method == "title" else "normal"
        write_comparison([baseline[baseline_key], output],
                         ["BEFORE", f"AFTER: {method}"], OUT / f"{method}.gif",
                         duration=2, fps=8)
        print(method, "picture", flush=True)

    audio_sources = {
        "highpass": "aevalsrc=0.3*sin(2*PI*60*t)+0.12*sin(2*PI*440*t):s=48000:d=2",
        "audio-denoise": "aevalsrc=0.12*sin(2*PI*440*t)+0.09*(random(0)-0.5):s=48000:d=2",
        "compress": "aevalsrc=(0.08+0.55*gt(mod(t\,1)\,0.5))*sin(2*PI*440*t):s=48000:d=2",
        "loudnorm": "sine=frequency=440:sample_rate=48000:duration=2:beep_factor=0",
    }
    for method, audio_filter in audio_sources.items():
        video = source(f"audio-{method}", "format=yuv420p", audio_filter)
        timeline = base_timeline(video)
        baseline_audio = render(timeline, f"{method}-baseline.mp4")
        timeline["operations"] = [{"id": method, "method": method,
                                    "start": 0, "end": 2,
                                    "review_status": "pending_review"}]
        output = render(timeline, f"{method}.mp4")
        audio_mp3(baseline_audio, OUT / f"{method}-before.mp3")
        audio_mp3(output, OUT / f"{method}-after.mp3")
        print(method, "audio", flush=True)


if __name__ == "__main__":
    main()
