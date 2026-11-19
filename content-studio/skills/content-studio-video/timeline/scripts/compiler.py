"""Compile an approved delivery timeline to one FFmpeg picture/audio export."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from model import AUDIO_METHODS, GRAPHIC_METHODS, PICTURE_METHODS, POINT_TRANSITIONS
from model import asset_path, sha256_file
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from xfade_effects import CUSTOM_JOIN_IDS, xfade_options  # noqa: E402


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format",
         "-of", "json", str(path)], capture_output=True, text=True)
    if result.returncode:
        raise ValueError(f"Cannot probe media {path}: {result.stderr[-400:]}")
    return json.loads(result.stdout)


def media_info(path: Path) -> dict:
    data = probe(path)
    video = next((s for s in data.get("streams", [])
                  if s.get("codec_type") == "video"), None)
    audio = next((s for s in data.get("streams", [])
                  if s.get("codec_type") == "audio"), None)
    return {"duration": float(data.get("format", {}).get("duration") or 0),
            "video": video, "audio": audio}


def _fmt(value: float) -> str:
    return f"{value:.6f}"


def _text(value: str) -> str:
    # Drawtext parses punctuation itself; escape it after timeline validation.
    return (value.replace("\\", "\\\\").replace(":", "\\:")
            .replace("'", "\\'").replace("%", "\\%")
            .replace(",", "\\,").replace("[", "\\[").replace("]", "\\]"))


def _picture_filters(active: list[dict], width: int, height: int, fps: float,
                     pixel_format: str = "yuv420p") -> list[str]:
    filters: list[str] = []
    selected_upscale = any(item["method"] == "upscale-lanczos" for item in active)
    for item in active:
        method = item["method"]
        if method == "crop":
            filters.append(
                "crop=iw*{w}:ih*{h}:iw*{x}:ih*{y}".format(
                    **{key: float(item[key]) for key in ("x", "y", "w", "h")}))
        elif method == "lens-correction":
            filters.append(
                "lenscorrection=cx=0.5:cy=0.5:k1={}:k2={}".format(
                    float(item.get("k1", 0)), float(item.get("k2", 0))))
        elif method == "denoise-light":
            filters.append("hqdn3d=2:1:3:2")
        elif method == "denoise-medium":
            filters.append("hqdn3d=4:3:6:4.5")
        elif method == "deflicker":
            filters.append("deflicker=mode=pm:size=10")
        elif method == "upscale-lanczos":
            filters.append(f"scale=iw*{item['scale']}:ih*{item['scale']}:flags=lanczos")
        elif method == "color-eq":
            filters.append("eq=contrast={}:brightness={}:saturation={}".format(
                float(item.get("contrast", 1)), float(item.get("brightness", 0)),
                float(item.get("saturation", 1))))
        elif method == "sharpen-light":
            filters.append("cas=strength=0.25")
        elif method == "sharpen-medium":
            filters.append("cas=strength=0.45")
        else:
            raise ValueError(f"Missing picture adapter: {method}")
    filters.extend([
        # The output canvas is shared by every segment. Selected ranges use
        # Lanczos; ordinary fit scaling stays bicubic so the cue is meaningful.
        f"scale={width}:{height}:force_original_aspect_ratio=decrease:"
        f"flags={'lanczos' if selected_upscale else 'bicubic'}",
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
        "setsar=1", f"fps={_fmt(fps)}", "settb=AVTB", f"format={pixel_format}",
    ])
    return filters


def _audio_filters(active: list[dict]) -> list[str]:
    filters: list[str] = []
    for item in active:
        method = item["method"]
        if method == "highpass":
            frequency = float(item.get("hz", 80))
            if not 20 <= frequency <= 300:
                raise ValueError("Highpass frequency must be 20-300 Hz")
            filters.append(f"highpass=f={frequency:g}")
        elif method == "audio-denoise":
            filters.append("afftdn=nf=-25")
        elif method == "compress":
            filters.append("acompressor=threshold=0.12:ratio=2:attack=20:release=200")
        elif method == "loudnorm":
            filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")
        else:
            raise ValueError(f"Missing audio adapter: {method}")
    return filters


def _breakpoints(start: float, end: float, operations: list[dict]) -> list[float]:
    points = {0.0, end - start}
    for item in operations:
        if item["method"] not in PICTURE_METHODS:
            continue
        left = max(start, float(item["start"]))
        right = min(end, float(item["end"]))
        if left < right:
            points.add(round(left - start, 6))
            points.add(round(right - start, 6))
    return sorted(points)


def _audio_graph(label: str, operations: list[dict], duration: float,
                 graph: list[str]) -> str:
    selected = [o for o in operations if o["method"] in AUDIO_METHODS]
    if not selected:
        graph.append(f"[{label}]alimiter=limit=0.95,aresample=48000,"
                     "aformat=sample_rates=48000:channel_layouts=stereo[afinal]")
        return "afinal"
    points = {0.0, round(duration, 6)}
    for item in selected:
        points.add(round(float(item["start"]), 6))
        points.add(round(float(item["end"]), 6))
    times = sorted(points)
    count = len(times) - 1
    graph.append(f"[{label}]asplit={count}" +
                 "".join(f"[as{i}]" for i in range(count)))
    for i in range(count):
        left, right = times[i], times[i + 1]
        middle = (left + right) / 2
        active = [o for o in selected if float(o["start"]) <= middle < float(o["end"])]
        rank = {"highpass": 1, "audio-denoise": 2, "compress": 3, "loudnorm": 4}
        active.sort(key=lambda item: rank[item["method"]])
        chain = [f"atrim=start={_fmt(left)}:end={_fmt(right)}",
                 "asetpts=PTS-STARTPTS"] + _audio_filters(active)
        graph.append(f"[as{i}]" + ",".join(chain) + f"[ap{i}]")
    graph.append("".join(f"[ap{i}]" for i in range(count)) +
                 f"concat=n={count}:v=0:a=1,alimiter=limit=0.95,"
                 "aresample=48000,"
                 "aformat=sample_rates=48000:channel_layouts=stereo[afinal]")
    return "afinal"


def _compile_copy_video(resolved: dict) -> tuple[list[str], str]:
    """Mix audio while the supplied picture packets bypass every video filter."""
    clip = resolved["clips"][0]
    source = media_info(clip["path"])
    video = source["video"]
    if not video or not source["audio"] or abs(source["duration"] - resolved["duration"]) > .08:
        raise ValueError("Picture-copy mix needs a full-length video with source audio")
    from fractions import Fraction
    rate = float(Fraction(video.get("avg_frame_rate") or "0/1"))
    if (int(video["width"]) != resolved["width"] or
            int(video["height"]) != resolved["height"] or
            abs(rate - resolved["fps"]) > .05):
        raise ValueError("Picture-copy settings must match source size and frame rate")
    inputs = ["-i", str(clip["path"])]
    length = _fmt(resolved["duration"])
    graph = [f"[0:a:0]aresample=48000,aformat=channel_layouts=stereo,"
             f"atrim=duration={length}[abase]"]
    labels = ["abase"]
    for index, cue in enumerate(resolved["audio"], start=1):
        source_path = asset_path(resolved["root"], cue["source"])
        if not media_info(source_path)["audio"]:
            raise ValueError(f"No audio stream in {cue['id']}")
        if cue.get("loop"):
            inputs.extend(["-stream_loop", "-1", "-t", _fmt(float(cue["duration"]))])
        inputs.extend(["-i", str(source_path)])
        delay = int(round(float(cue["start"]) * 1000))
        chain = [f"[{index}:a:0]aresample=48000,aformat=channel_layouts=stereo",
                 f"volume={float(cue.get('gain', 1)):g}"]
        if cue.get("loop"):
            span = float(cue["duration"])
            chain.append(f"atrim=duration={_fmt(span)}")
            if cue.get("fade_in"):
                chain.append(f"afade=t=in:st=0:d={_fmt(float(cue['fade_in']))}")
            if cue.get("fade_out"):
                chain.append(f"afade=t=out:st={_fmt(span - float(cue['fade_out']))}:"
                             f"d={_fmt(float(cue['fade_out']))}")
        chain.extend([f"adelay={delay}|{delay}", "apad",
                      f"atrim=duration={length}[acue{index}]"])
        graph.append(",".join(chain))
        labels.append(f"acue{index}")
    graph.append("".join(f"[{label}]" for label in labels) +
                 f"amix=inputs={len(labels)}:duration=first:normalize=0,"
                 "alimiter=limit=0.95,aresample=48000,"
                 "aformat=sample_rates=48000:channel_layouts=stereo[afinal]")
    return inputs, ";".join(graph)


def verify_picture_copy(source: Path, output: Path) -> dict:
    """Fail closed if remuxing changed coded packets or HDR metadata."""
    original, delivered = media_info(source)["video"], media_info(output)["video"]
    if not original or not delivered:
        raise ValueError("Picture-copy verification needs two video streams")
    keys = ("codec_name", "profile", "width", "height", "pix_fmt", "color_range",
            "color_space", "color_transfer", "color_primaries")
    differences = [key for key in keys if original.get(key) != delivered.get(key)]
    if differences:
        raise ValueError("Picture-copy metadata changed: " + ", ".join(differences))
    # Compare the actual Dolby Vision configuration fields, not just its presence.
    def dovi_metadata(stream: dict) -> list[dict]:
        return [{key: value for key, value in side.items() if key not in {"side_data_type"}}
                for side in stream.get("side_data_list", [])
                if "dovi" in json.dumps(side).lower() or
                "dolby vision" in json.dumps(side).lower()]
    source_dv = dovi_metadata(original)
    output_dv = dovi_metadata(delivered)
    if source_dv != output_dv:
        raise ValueError("Dolby Vision stream metadata changed")
    command = ["ffprobe", "-v", "error", "-select_streams", "v:0",
               "-show_packets", "-show_entries", "packet=data_hash",
               "-show_data_hash", "sha256", "-of", "csv=p=0"]
    hashes = []
    for path in (source, output):
        result = subprocess.run([*command, str(path)], capture_output=True, text=True)
        if result.returncode or "SHA256:" not in result.stdout:
            raise ValueError("Cannot establish video packet identity")
        hashes.append(result.stdout.strip())
    if hashes[0] != hashes[1]:
        raise ValueError("Remux changed or dropped video packet payloads")
    import hashlib
    return {"video_packet_sha256": hashlib.sha256(hashes[0].encode()).hexdigest(),
            "dolby_vision": bool(source_dv)}


def compile_graph(timeline: dict, resolved: dict) -> tuple[list[str], str]:
    """Return input arguments and one graph; every branch stays unencoded."""
    if resolved["video_policy"] == "copy_source":
        return _compile_copy_video(resolved)
    clips = resolved["clips"]
    width, height, fps = resolved["width"], resolved["height"], resolved["fps"]
    duration = resolved["duration"]
    copy_audio = resolved["audio_policy"] == "copy_source"
    custom_join = any(cue["id"] in CUSTOM_JOIN_IDS
                      for cue in resolved["transitions"].values())
    join_format = "yuv444p" if custom_join else "yuv420p"
    graph: list[str] = []
    inputs: list[str] = []
    info: list[dict] = []
    for clip in clips:
        metadata = media_info(clip["path"])
        video = metadata["video"]
        if not video or metadata["duration"] + 0.08 < clip["source_out"]:
            raise ValueError(f"Source range exceeds media: {clip['id']}")
        if (video.get("color_transfer") in {"smpte2084", "arib-std-b67"}
                or video.get("color_primaries") == "bt2020"
                or any("dovi" in json.dumps(side).lower()
                       or "dolby vision" in json.dumps(side).lower()
                       for side in video.get("side_data_list", []))
                or "10" in str(video.get("pix_fmt", ""))
                or "12" in str(video.get("pix_fmt", ""))):
            raise ValueError(
                "HDR, Dolby Vision, or high-bit-depth source needs an explicit supported route")
        for operation in resolved["operations"]:
            if (operation["method"] == "upscale-lanczos"
                    and float(operation["start"]) < clip["end"]
                    and float(operation["end"]) > clip["start"]):
                scale = int(operation["scale"])
                if (width < int(video["width"]) * scale
                        or height < int(video["height"]) * scale):
                    raise ValueError(
                        f"Upscale {operation['id']} needs at least {scale}x "
                        f"source dimensions in the output canvas")
        info.append(metadata)
        # Seek each picture input to its retained source span before decoding.
        # A long source used by several cuts would otherwise be decoded from
        # frame zero once per clip, making late edits prohibitively expensive.
        if copy_audio:
            inputs.extend(["-i", str(clip["path"])])
        else:
            inputs.extend(["-ss", _fmt(clip["source_in"]),
                           "-t", _fmt(clip["duration"]), "-i", str(clip["path"])])
    if copy_audio:
        # Preserve source packets only for a full length, unshifted source.
        source_info = info[0]
        if (not source_info["audio"]
                or abs(source_info["duration"] - duration) > .08):
            raise ValueError("copy_source needs full length source audio")
    for cue in resolved["audio"]:
        source = asset_path(resolved["root"], cue["source"])
        metadata = media_info(source)
        if not metadata["audio"]:
            raise ValueError(f"No audio stream in {cue['id']}")
        # Keep a short PCM tail inside the output trim; larger overruns could
        # hide missing narration and must still stop before an expensive render.
        if cue["kind"] == "voice" and float(cue["start"]) + metadata["duration"] > duration + .12:
            raise ValueError(f"Voice cue {cue['id']} extends past the picture")
        if cue.get("loop"):
            # Repeat the approved source in the decoder, then trim it before
            # mixing so neither a full music master nor a second encode exists.
            inputs.extend(["-stream_loop", "-1", "-t",
                           _fmt(float(cue["duration"])), "-i", str(source)])
        else:
            inputs.extend(["-i", str(source)])
    matte_inputs: dict[str, int] = {}
    for item in resolved["operations"]:
        if item["method"] not in {"text-behind-subject", "object-blur"}:
            continue
        matte = asset_path(resolved["root"], item.get("matte_source") or item.get("mask_source"))
        metadata = media_info(matte)
        if not metadata["video"]:
            raise ValueError(f"No video stream in mask {item['id']}")
        if matte.suffix.lower() != ".png" and metadata["duration"] + .08 < item["end"] - item["start"]:
            raise ValueError(f"Mask is shorter than cue {item['id']}")
        matte_inputs[item["id"]] = len(clips) + len(resolved["audio"]) + len(matte_inputs)
        if matte.suffix.lower() == ".png":
            inputs.extend(["-loop", "1", "-framerate", _fmt(fps)])
        inputs.extend(["-i", str(matte)])
    for i, clip in enumerate(clips):
        points = _breakpoints(clip["start"], clip["end"], resolved["operations"])
        segment_labels: list[str] = []
        count = len(points) - 1
        if count > 1:
            graph.append(f"[{i}:v:0]split={count}" +
                         "".join(f"[raw{i}s{j}]" for j in range(count)))
        for segment in range(count):
            left, right = points[segment], points[segment + 1]
            if right <= left:
                continue
            middle = clip["start"] + (left + right) / 2
            active = [o for o in resolved["operations"]
                      if o["method"] in PICTURE_METHODS
                      and float(o["start"]) <= middle < float(o["end"])]
            rank = {"lens-correction": 0, "crop": 1,
                    "denoise-light": 2, "denoise-medium": 2, "deflicker": 3,
                    "upscale-lanczos": 4, "color-eq": 5,
                    "sharpen-light": 6, "sharpen-medium": 6}
            active.sort(key=lambda o: rank[o["method"]])
            if (len({o["method"] for o in active}) != len(active)
                    or sum(o["method"].startswith("denoise-") for o in active) > 1
                    or sum(o["method"].startswith("sharpen-") for o in active) > 1):
                raise ValueError("Conflicting overlapping picture effects")
            filters = [
                f"trim=start={_fmt(left if not copy_audio else clip['source_in'] + left)}:"
                f"end={_fmt(right if not copy_audio else clip['source_in'] + right)}",
                "setpts=PTS-STARTPTS",
            ] + _picture_filters(active, width, height, fps, join_format)
            label = f"v{i}s{segment}"
            origin = f"raw{i}s{segment}" if count > 1 else f"{i}:v:0"
            graph.append(f"[{origin}]" + ",".join(filters) + f"[{label}]")
            segment_labels.append(label)
        if len(segment_labels) == 1:
            graph.append(f"[{segment_labels[0]}]null[vc{i}]")
        else:
            graph.append("".join(f"[{label}]" for label in segment_labels)
                         + f"concat=n={len(segment_labels)}:v=1:a=0[vc{i}]")
        if copy_audio:
            continue
        if info[i]["audio"]:
            graph.append(f"[{i}:a:0]atrim=start=0:"
                         f"end={_fmt(clip['duration'])},asetpts=PTS-STARTPTS,"
                         f"aresample=48000,aformat=channel_layouts=stereo,"
                         f"volume={float(clip.get('audio_gain', 1)):g}[ac{i}]")
        else:
            graph.append(f"anullsrc=r=48000:cl=stereo,"
                         f"atrim=duration={_fmt(clip['duration'])}[ac{i}]")
    current_v, current_a = "vc0", "ac0"
    current_length = clips[0]["duration"]
    for i in range(1, len(clips)):
        previous_id = clips[i - 1]["id"]
        cue = resolved["transitions"].get(previous_id)
        target_v, target_a = f"joinedv{i}", f"joineda{i}"
        if cue:
            overlap = cue["duration"]
            offset = current_length - overlap
            from model import JOIN_TRANSITIONS
            options = xfade_options(cue["id"], JOIN_TRANSITIONS[cue["id"]])
            graph.append(f"[{current_v}][vc{i}]xfade={options}:duration={_fmt(overlap)}:"
                         f"offset={_fmt(offset)}[{target_v}]")
            graph.append(f"[{current_a}][ac{i}]acrossfade=d={_fmt(overlap)}:"
                         f"c1=tri:c2=tri[{target_a}]")
            current_length += clips[i]["duration"] - overlap
        else:
            graph.append(f"[{current_v}][vc{i}]concat=n=2:v=1:a=0[{target_v}]")
            graph.append(f"[{current_a}][ac{i}]concat=n=2:v=0:a=1[{target_a}]")
            current_length += clips[i]["duration"]
        current_v, current_a = target_v, target_a
    for index, item in enumerate(o for o in resolved["operations"]
                                 if o["method"] in GRAPHIC_METHODS | POINT_TRANSITIONS):
        method = item["method"]
        target = f"effect{index}"
        start, end = float(item["start"]), float(item["end"])
        if method == "title":
            title = str(item.get("text", "")).strip()
            if not title or len(title) > 160:
                raise ValueError("Title text must contain 1-160 characters")
            graph.append(f"[{current_v}]drawtext=fontfile={_text(item['font_source'])}:text='{_text(title)}':"
                         f"fontcolor=white:fontsize=h/18:x=(w-text_w)/2:"
                         f"y=h*0.08:box=1:boxcolor=black@0.5:"
                         f"enable='between(t,{_fmt(start)},{_fmt(end)})'[{target}]")
        elif method == "motion-graphics-ass":
            sidecar = asset_path(resolved["root"], item["source"])
            font_dir = (f":fontsdir={_text(str(Path(item['font_source']).parent))}"
                        if item.get("font_source") else "")
            graph.append(f"[{current_v}]ass={_text(item['source'])}{font_dir}[{target}]")
        elif method == "text-behind-subject":
            # The white matte restores original foreground pixels after the
            # rising title, so the title passes behind the person and terrain.
            index_in = matte_inputs[item["id"]]
            cue_length = end - start
            font_size = max(1, round(height * float(item.get("font_height", .09))))
            from_y = float(item.get("from_y", .55))
            to_y = float(item.get("to_y", .12))
            rise = float(item.get("rise_seconds", 1))
            y = (f"if(lt(t,{_fmt(start + rise)}),"
                 f"h*{from_y:g}+(h*{to_y:g}-h*{from_y:g})*"
                 f"(t-{_fmt(start)})/{_fmt(rise)},h*{to_y:g})")
            y = y.replace(",", "\\,")
            graph.append(f"[{current_v}]split=2[plain{index}][letterbase{index}]")
            graph.append(f"[letterbase{index}]drawtext=fontfile={_text(item['font_source'])}:"
                         f"text='{_text(item['text'].strip())}':fontcolor=white:"
                         f"fontsize={font_size}:x=(w-text_w)/2:y='{y}':"
                         f"enable='between(t,{_fmt(start)},{_fmt(end)})'"
                         f"[lettered{index}]")
            graph.append(f"color=c=black:s={width}x{height}:r={_fmt(fps)}:"
                         f"d={_fmt(duration)},format=yuv420p[blackmask{index}]")
            graph.append(f"[{index_in}:v:0]trim=duration={_fmt(cue_length)},"
                         f"setpts=PTS-STARTPTS+{_fmt(start)}/TB,"
                         f"scale={width}:{height},fps={_fmt(fps)},"
                         f"format=yuv420p[mattepart{index}]")
            graph.append(f"[blackmask{index}][mattepart{index}]"
                         f"overlay=eof_action=pass:repeatlast=0:format=auto,"
                         f"format=yuv420p[fullmask{index}]")
            graph.append(f"[lettered{index}][plain{index}][fullmask{index}]"
                         f"maskedmerge[{target}]")
        elif method == "object-blur":
            # The lossless gray sidecar supplies alpha only. Blur the picture
            # in this graph so there is still one video encode for delivery.
            index_in = matte_inputs[item["id"]]
            sigma = max(24, round(min(width, height) * .04))
            graph.append(f"[{index_in}:v:0]trim=duration={_fmt(duration)},"
                         f"setpts=PTS-STARTPTS,scale={width}:{height},"
                         f"fps={_fmt(fps)},format=gray[blurmask{index}]")
            graph.append(f"[{current_v}]split=2[plain{index}][blurbase{index}]")
            graph.append(f"[blurbase{index}]gblur=sigma={sigma}:steps=2,"
                         f"format=rgba[blurred{index}]")
            graph.append(f"[blurred{index}][blurmask{index}]"
                         f"alphamerge[bluralpha{index}]")
            graph.append(f"[plain{index}][bluralpha{index}]"
                         f"overlay=shortest=1:format=auto,format=yuv420p[{target}]")
        elif method == "cross-blur":
            # Ease the blur in and out around the source cut; start/end remain
            # editable timeline times and the picture/audio duration is fixed.
            middle = (start + end) / 2
            strength = float(item.get("blur_sigma", 10))
            blur = f"gblur@blur{index}"
            commands = (f"{_fmt(start)}-{_fmt(middle)} [expr] {blur} sigma {strength:g}*TI\\;"
                        f"{_fmt(middle)}-{_fmt(end)} [expr] {blur} sigma {strength:g}*(1-TI)\\;"
                        f"{_fmt(end)} {blur} sigma 0")
            graph.append(f"[{current_v}]sendcmd=c='{commands}',"
                         f"{blur}=sigma=0:enable='between(t,{_fmt(start)},{_fmt(end)})'"
                         f"[{target}]")
        elif method in {"glitch", "glitch-reveal"}:
            # Match the specialist's RGB-offset/noise approximation, scoped to
            # this editable point range so surrounding frames pass through.
            shift, noise, contrast = ((10, 20, 1.0) if method == "glitch"
                                      else (22, 30, 1.15))
            enable = f"enable='between(t,{_fmt(start)},{_fmt(end)})'"
            filters = [f"rgbashift=rh={shift}:bh=-{shift}:{enable}",
                       f"noise=alls={noise}:allf=t+u:{enable}"]
            if contrast != 1.0:
                filters.append(f"eq=contrast={contrast:g}:{enable}")
            graph.append(f"[{current_v}]" + ",".join(filters) + f"[{target}]")
        elif method in {"fade-through-black", "fade-through-white", "burn"}:
            # Burn is the catalog's warm dip, not a fire simulation.
            color = {"fade-through-black": "black",
                     "fade-through-white": "white",
                     "burn": "0xFF5A1F"}[method]
            half = (end - start) / 2
            middle = start + half
            graph.append(f"color=c={color}:s={width}x{height}:r={_fmt(fps)}:"
                         f"d={_fmt(duration)},format=rgba,"
                         f"fade=t=in:st={_fmt(start)}:d={_fmt(half)}:alpha=1,"
                         f"fade=t=out:st={_fmt(middle)}:d={_fmt(half)}:alpha=1"
                         f"[overlay{index}]")
            graph.append(f"[{current_v}][overlay{index}]overlay=0:0:"
                         f"shortest=1[{target}]")
        else:
            raise ValueError(f"Missing point transition adapter: {method}")
        current_v = target
    # Custom joins use full-size chroma for coordinate sampling, then return
    # to the delivery pixel format before the single encoder sees the frame.
    graph.append(f"[{current_v}]"
                 f"{'format=yuv420p' if custom_join else 'null'}[vfinal]")
    audio_labels = [current_a]
    for i, cue in enumerate(resolved["audio"]):
        index = len(clips) + i
        metadata = media_info(asset_path(resolved["root"], cue["source"]))
        delay = int(round(float(cue["start"]) * 1000))
        target = f"cue{i}"
        filters = [f"[{index}:a:0]aresample=48000",
                   "aformat=channel_layouts=stereo",
                   f"volume={float(cue.get('gain', 1)):g}"]
        if cue.get("loop"):
            length = float(cue["duration"])
            filters.append(f"atrim=duration={_fmt(length)}")
            if float(cue.get("fade_in", 0)):
                filters.append(f"afade=t=in:st=0:d={_fmt(float(cue['fade_in']))}")
            if float(cue.get("fade_out", 0)):
                filters.append(f"afade=t=out:st={_fmt(length - float(cue['fade_out']))}:"
                               f"d={_fmt(float(cue['fade_out']))}")
        filters.extend([f"adelay={delay}|{delay}", "apad",
                        f"atrim=duration={_fmt(duration)}[{target}]"])
        graph.append(",".join(filters))
        audio_labels.append(target)
    if len(audio_labels) > 1:
        graph.append("".join(f"[{label}]" for label in audio_labels) +
                     f"amix=inputs={len(audio_labels)}:duration=first:"
                     "normalize=0[amixed]")
        current_a = "amixed"
    if not copy_audio:
        _audio_graph(current_a, resolved["operations"], duration, graph)
    return inputs, ";".join(graph)


def _export(timeline: dict, resolved: dict, output: Path,
            preview_range: tuple[float, float] | None = None) -> dict:
    """One FFmpeg invocation encodes the chosen delivery or bounded preview."""
    output = output.resolve()
    if output.exists():
        raise ValueError("Output already exists")
    if output == resolved["output"] and preview_range is not None:
        raise ValueError("Preview cannot occupy the approved final output path")
    if output in [clip["path"] for clip in resolved["clips"]]:
        raise ValueError("Output cannot overwrite a picture source")
    if output in [asset_path(resolved["root"], cue["source"])
                  for cue in resolved["audio"]]:
        raise ValueError("Output cannot overwrite an audio source")
    if output in [asset_path(resolved["root"], op.get("matte_source") or op.get("mask_source"))
                  for op in resolved["operations"]
                  if op["method"] in {"text-behind-subject", "object-blur"}]:
        raise ValueError("Output cannot overwrite a mask")
    inputs, graph = compile_graph(timeline, resolved)
    expected = resolved["duration"]
    seek_args: list[str] = []
    if preview_range is not None:
        start, length = preview_range
        if not 0 <= start < expected or length <= 0 or start + length > expected + .001:
            raise ValueError("Preview range is outside the resolved timeline")
        expected = length
        seek_args = ["-ss", _fmt(start)]
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="timeline-render-", dir=output.parent) as scratch:
        graph_path = Path(scratch) / "graph.txt"
        graph_path.write_text(graph, encoding="utf-8")
        temporary = Path(scratch) / "delivery.mp4"
        copy_audio = resolved["audio_policy"] == "copy_source"
        copy_video = resolved["video_policy"] == "copy_source"
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                   "-n", *inputs, "-/filter_complex", str(graph_path),
                   "-map", "0:v:0" if copy_video else "[vfinal]",
                   "-map", "0:a:0" if copy_audio else "[afinal]",
                   *seek_args,
                   *([] if copy_video and preview_range is None else ["-t", _fmt(expected)]),
                   *(["-c:v", "copy", "-map_metadata", "0"] if copy_video else
                     ["-r", _fmt(resolved["fps"]), "-c:v", "libx264",
                      "-preset", resolved["video_preset"], "-crf", "18",
                      "-pix_fmt", "yuv420p"]),
                   *(["-c:a", "copy"] if copy_audio else
                     ["-c:a", "aac", "-ar", "48000", "-b:a", "192k"]),
                   "-movflags", "+faststart", str(temporary)]
        result = subprocess.run(command, capture_output=True, text=True,
                                cwd=resolved["root"])
        if result.returncode:
            raise RuntimeError((result.stderr or result.stdout)[-2400:])
        delivered = media_info(temporary)
        if (not delivered["video"] or not delivered["audio"]
                or abs(delivered["duration"] - expected) > .15):
            raise RuntimeError("Rendered duration or streams failed validation")
        if copy_video and preview_range is None:
            verify_picture_copy(resolved["clips"][0]["path"], temporary)
        os.replace(temporary, output)
    return {"output": str(output), "output_sha256": sha256_file(output),
            "duration": delivered["duration"]}


def render(timeline: dict, resolved: dict) -> dict:
    record = _export(timeline, resolved, resolved["output"])
    record.update({
        "operations": [item["id"] for item in resolved["operations"]],
        "audio_cues": [item["id"] for item in resolved["audio"]],
        "video_encoder_invocations": 0 if resolved["video_policy"] == "copy_source" else 1,
        "audio_encoder_invocations": 0 if resolved["audio_policy"] == "copy_source" else 1,
        "review_status": "pending_exact_output_review",
    })
    return record


def preview(timeline: dict, resolved: dict, output: Path,
            start: float, duration: float) -> dict:
    record = _export(timeline, resolved, output, (start, duration))
    record.update({"preview_start": start, "preview_duration": duration,
                   "review_status": "preview_only"})
    return record
