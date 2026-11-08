"""Canonical Content Studio draft layout and legacy migration.

A draft keeps source footage, internal working files, review media, and final
deliverables in predictable places:

    drafts/<draft>/
      original/                    raw camera files
      .content-studio/             internal working files
        processed-clips/<clip>/    per-clip analysis and exports
        analysis/duplicates/       quarantined duplicates
        rough-cut/                 rough cut, timelines, review media
        audio/                     internal audio manifests
        tmp/                       temporary join/normalization work
        _timeline.csv              capture order
      <draft>-rough-cut.mp4        rough-cut video
      <draft>-preprocessed.mp4     full preprocessed video
      <draft>-final.mp4            final full video
      <draft>-audio-only.mp3       extracted mastered audio
      title.txt / description.txt  publication copy
      lifecycle-checklist.json     lifecycle evidence
      draft.json                   draft record and receipts

Older drafts kept camera files, video/, and rough-cut/ at the draft root. The
migration below moves those files into the canonical layout without deleting
source footage.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mkv"}
ORIGINAL = "original"
INTERNAL = ".content-studio"
PROCESSED = "processed-clips"
ROUGH_CUT = "rough-cut"
AUDIO = "audio"
VIDEO = "video"
TIMELINE = "_timeline.csv"

# Files that belong to deliverables, never to the camera-source folder.


def original_dir(draft: Path) -> Path:
    return draft / ORIGINAL


def internal_dir(draft: Path) -> Path:
    return draft / INTERNAL


def processed_dir(draft: Path) -> Path:
    return draft / INTERNAL / PROCESSED


def duplicates_dir(draft: Path) -> Path:
    return draft / INTERNAL / "analysis" / "duplicates"


def timeline_path(draft: Path) -> Path:
    current = internal_dir(draft) / TIMELINE
    legacy = draft / TIMELINE
    if current.exists() or not legacy.exists():
        return current
    return legacy


def rough_cut_dir(draft: Path) -> Path:
    """Internal folder for the rough-cut video, timelines, and review media."""
    return draft / INTERNAL / ROUGH_CUT


def scratch_dir(draft: Path) -> Path:
    return draft / INTERNAL / "tmp"


def rough_cut_path(draft: Path) -> Path:
    return draft / f"{draft.name}-rough-cut.mp4"


def preprocessed_path(draft: Path) -> Path:
    return draft / f"{draft.name}-preprocessed.mp4"


def audio_dir(draft: Path) -> Path:
    """Internal folder for audio manifests; the extracted audio lives at the root."""
    return draft / INTERNAL / AUDIO


def final_path(draft: Path) -> Path:
    return draft / f"{draft.name}-final.mp4"


def audio_only_path(draft: Path) -> Path:
    return draft / f"{draft.name}-audio-only.mp3"


def master_path(draft: Path) -> Path:
    """Return the reviewed master, falling back to legacy layouts."""
    current = final_path(draft)
    legacy_video = draft / "video" / "with-audio.mp4"
    legacy_root = draft / "video.mp4"
    legacy_final = draft / "final-video.mp4"
    if current.exists():
        return current
    for candidate in (legacy_final, legacy_video, legacy_root):
        if candidate.exists():
            return candidate
    return current


def silent_path(draft: Path) -> Path:
    return draft / INTERNAL / "silent.mp4"


def music_path(draft: Path) -> Path:
    return draft / f"{draft.name}-final-with-music.mp4"


def deliverable_names(draft: Path) -> set[str]:
    return {
        rough_cut_path(draft).name,
        preprocessed_path(draft).name,
        final_path(draft).name,
        audio_only_path(draft).name,
        music_path(draft).name,
        "video.mp4", "video.mov", "video.mkv", "video.webm",
        "video-with-music.mp4", "final-video.mp4",
        "final-video-with-music.mp4", "rough-cut.mp4",
        "video-before-intro.mp4",
    }


def transcript_path(draft: Path) -> Path:
    return draft / "transcript.json"


def captions_path(draft: Path) -> Path:
    return draft / "captions.srt"


def title_path(draft: Path) -> Path:
    return draft / "title.txt"


def description_path(draft: Path) -> Path:
    return draft / "description.txt"


def checklist_path(draft: Path) -> Path:
    return draft / "lifecycle-checklist.json"


def record_path(draft: Path) -> Path:
    return draft / "draft.json"


def camera_root(draft: Path) -> Path:
    """Camera files live in original/ once the layout exists."""
    root = original_dir(draft)
    return root if root.is_dir() else draft


def ensure_layout(draft: Path) -> None:
    for folder in (original_dir(draft), internal_dir(draft), processed_dir(draft),
                   rough_cut_dir(draft), audio_dir(draft), scratch_dir(draft)):
        folder.mkdir(parents=True, exist_ok=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _same_bytes(first: Path, second: Path) -> bool:
    return (first.stat().st_size == second.stat().st_size
            and _sha256(first) == _sha256(second))


def _free_name(folder: Path, name: str) -> Path:
    target = folder / name
    if not target.exists():
        return target
    stem, suffix = target.stem, target.suffix
    index = 1
    while True:
        candidate = folder / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def move_file(source: Path, target: Path, log) -> Path:
    """Move a file without silently deleting a different file at the target."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.move(str(source), str(target))
        return target
    if _same_bytes(source, target):
        source.unlink()
        log(f"layout: removed duplicate {source.name}; already at {target}")
        return target
    alternate = _free_name(target.parent, target.name)
    shutil.move(str(source), str(alternate))
    log(f"layout: {source.name} -> {alternate.name}; {target.name} already existed")
    return alternate


def merge_tree(source: Path, target: Path, log) -> None:
    """Merge a legacy folder into the new layout without overwriting files."""
    if not source.is_dir():
        return
    target.mkdir(parents=True, exist_ok=True)
    for item in sorted(source.iterdir()):
        destination = target / item.name
        if item.is_dir():
            merge_tree(item, destination, log)
        elif destination.exists():
            move_file(item, destination, log)
        else:
            shutil.move(str(item), str(destination))
    try:
        source.rmdir()
    except OSError:
        pass


def migrate(draft: Path, log=print) -> list[str]:
    """Move a legacy draft into the canonical layout. Idempotent."""
    if not draft.is_dir():
        return []
    ensure_layout(draft)
    moves: list[str] = []
    deliverables = deliverable_names(draft)

    # Raw camera clips at the root move into original/.
    for path in sorted(draft.iterdir()):
        if not path.is_file() or path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        if path.name in deliverables:
            continue
        target = move_file(path, original_dir(draft) / path.name, log)
        moves.append(f"{path.name} -> {target.relative_to(draft)}")

    legacy_original = draft / "original-videos"
    if legacy_original.is_dir():
        backup = legacy_original / "video-before-intro.mp4"
        if backup.is_file():
            target = move_file(backup, internal_dir(draft) / "before-intro.mp4", log)
            moves.append(f"original-videos/video-before-intro.mp4 -> {target.relative_to(draft)}")
        merge_tree(legacy_original, original_dir(draft), log)
        moves.append("original-videos/ -> original/")

    legacy_processed = draft / PROCESSED
    if legacy_processed.is_dir():
        merge_tree(legacy_processed, processed_dir(draft), log)
        moves.append("processed-clips/ -> .content-studio/processed-clips/")

    legacy_timeline = draft / TIMELINE
    if legacy_timeline.is_file():
        target = internal_dir(draft) / TIMELINE
        if not target.exists():
            shutil.move(str(legacy_timeline), str(target))
            moves.append(f"{TIMELINE} -> .content-studio/{TIMELINE}")
        else:
            target.unlink()
            moves.append(f"{TIMELINE}: current copy kept")

    legacy_analysis = draft / "analysis"
    if legacy_analysis.is_dir():
        merge_tree(legacy_analysis, internal_dir(draft) / "analysis", log)
        moves.append("analysis/ -> .content-studio/analysis/")

    legacy_audio = draft / "audio-mastered"
    if legacy_audio.is_dir():
        merge_tree(legacy_audio, audio_dir(draft), log)
        moves.append("audio-mastered/ -> .content-studio/audio/")

    legacy_master = draft / "video.mp4"
    if legacy_master.is_file():
        target = move_file(legacy_master, final_path(draft), log)
        moves.append(f"video.mp4 -> {target.relative_to(draft)}")

    legacy_final = draft / "final-video.mp4"
    if legacy_final.is_file() and legacy_final != final_path(draft):
        target = move_file(legacy_final, final_path(draft), log)
        moves.append(f"final-video.mp4 -> {target.relative_to(draft)}")

    legacy_music = draft / "video-with-music.mp4"
    if legacy_music.is_file():
        target = move_file(legacy_music, music_path(draft), log)
        moves.append(f"video-with-music.mp4 -> {target.relative_to(draft)}")

    legacy_music_final = draft / "final-video-with-music.mp4"
    if legacy_music_final.is_file() and legacy_music_final != music_path(draft):
        target = move_file(legacy_music_final, music_path(draft), log)
        moves.append(f"final-video-with-music.mp4 -> {target.relative_to(draft)}")

    legacy_rough_root = draft / "rough-cut.mp4"
    if legacy_rough_root.is_file() and legacy_rough_root != rough_cut_path(draft):
        target = move_file(legacy_rough_root, rough_cut_path(draft), log)
        moves.append(f"rough-cut.mp4 -> {target.relative_to(draft)}")

    legacy_preprocessed = draft / "preprocess-final.mp4"
    if legacy_preprocessed.is_file():
        target = move_file(legacy_preprocessed, preprocessed_path(draft), log)
        moves.append(f"preprocess-final.mp4 -> {target.relative_to(draft)}")

    legacy_video = draft / VIDEO
    if legacy_video.is_dir():
        renames = {
            "with-audio.mp4": final_path(draft),
            "without-audio.mp4": internal_dir(draft) / "silent.mp4",
            "with-music.mp4": music_path(draft),
            "before-intro.mp4": internal_dir(draft) / "before-intro.mp4",
        }
        for name, target in renames.items():
            source = legacy_video / name
            if source.is_file():
                moved = move_file(source, target, log)
                moves.append(f"video/{name} -> {moved.relative_to(draft)}")
        merge_tree(legacy_video, internal_dir(draft) / "legacy-video", log)

    legacy_rough = draft / ROUGH_CUT
    if legacy_rough.is_dir():
        rough_video = legacy_rough / "rough-cut.mp4"
        if rough_video.is_file():
            target = move_file(rough_video, rough_cut_path(draft), log)
            moves.append(f"rough-cut/rough-cut.mp4 -> {target.relative_to(draft)}")
        preprocess_join = legacy_rough / "preprocess-final.mp4"
        if preprocess_join.is_file():
            target = move_file(preprocess_join, preprocessed_path(draft), log)
            moves.append(f"rough-cut/preprocess-final.mp4 -> {target.relative_to(draft)}")
        merge_tree(legacy_rough, rough_cut_dir(draft), log)
        moves.append("rough-cut/ -> .content-studio/rough-cut/")

    legacy_before_intro = draft / "video-before-intro.mp4"
    if legacy_before_intro.is_file():
        target = move_file(legacy_before_intro, internal_dir(draft) / "before-intro.mp4", log)
        moves.append(f"video-before-intro.mp4 -> {target.relative_to(draft)}")

    return moves
