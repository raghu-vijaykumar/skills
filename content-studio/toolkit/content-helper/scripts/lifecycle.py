"""Turn a public YouTube backup into exact Git metadata and a draft-source handoff."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


def inside(path: Path, parent: Path) -> Path:
    """Guard every copy or recursive removal against escaping the channel root."""
    resolved = path.resolve()
    if not resolved.is_relative_to(parent.resolve()) or resolved == parent.resolve():
        raise ValueError(f"unsafe channel path: {path}")
    return resolved


def write_if_changed(path: Path, value: str) -> bool:
    # Compare exact bytes: universal newline conversion would hide CRLF drift.
    if path.exists() and path.read_bytes() == value.encode("utf-8"):
        return False
    # Preserve the API description's newline bytes on Windows.
    with path.open("w", encoding="utf-8", newline="\n") as output:
        output.write(value)
    return True


def public_archives(root: Path):
    for kind in ("shorts", "long"):
        parent = root / kind
        if not parent.exists():
            continue
        for folder in sorted(parent.iterdir()):
            info_path = folder / "metadata.json"
            if folder.is_dir() and info_path.is_file():
                info = json.loads(info_path.read_text(encoding="utf-8"))
                if info.get("id"):
                    yield kind, folder, info


def draft_for_youtube_id(root: Path, youtube_id: str) -> Path | None:
    drafts = root / "drafts"
    if not drafts.exists():
        return None
    matches = []
    for folder in drafts.iterdir():
        manifest = folder / "draft.json"
        if folder.is_dir() and manifest.is_file():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            if data.get("youtubeId") == youtube_id:
                matches.append(folder)
    if len(matches) > 1:
        raise ValueError(f"multiple drafts claim YouTube ID {youtube_id}")
    return matches[0] if matches else None


def copy_draft_source(root: Path, draft: Path, archive: Path) -> None:
    """Keep the YouTube-downloaded bytes while copying authored source and assets."""
    inside(draft, root / "drafts")
    inside(archive, root)
    reserved = {"video.mp4", "video.webm", "video.mkv", "metadata.json",
                "title.txt", "description.txt", "thumbnail.jpg", "thumbnail.png",
                "thumbnail.webp", "draft.json"}
    for child in draft.iterdir():
        if child.name in reserved:
            continue
        destination = archive / child.name
        if child.is_dir():
            shutil.copytree(child, destination, dirs_exist_ok=True)
        elif child.is_file():
            shutil.copy2(child, destination)


def reconcile(root: Path, log, attach_drafts: bool = True) -> tuple[list[Path], list[tuple[Path, Path]]]:
    """Return changed archive paths and public draft handoffs for Drive/Git completion."""
    root = root.resolve()
    changed: list[Path] = []
    handoffs: list[tuple[Path, Path]] = []
    for kind, archive, info in public_archives(root):
        inside(archive, root / kind)
        title = f"{str(info.get('title') or '').strip()}\n"
        description = f"{str(info.get('description') or '').rstrip()}\n"
        updated = write_if_changed(archive / "title.txt", title)
        updated |= write_if_changed(archive / "description.txt", description)
        if not any((archive / f"thumbnail.{extension}").is_file() for extension in ("jpg", "png", "webp")):
            raise ValueError(f"missing YouTube thumbnail: {archive}")
        draft = draft_for_youtube_id(root, info["id"]) if attach_drafts else None
        if draft and info.get("availability") == "public":
            copy_draft_source(root, draft, archive)
            receipt = json.loads((draft / "draft.json").read_text(encoding="utf-8"))
            provenance = {"sourceId": draft.name, "youtubeId": info["id"],
                          "sourceMatch": "draft-by-youtube-id", "matchEvidence": "youtube-id",
                          "sourceCommit": receipt.get("sourceCommit"),
                          "uploadedRenderSha256": receipt.get("renderSha256")}
            public_receipt = {key: receipt.get(key) for key in
                              ("youtubeId", "sourceCommit", "renderSha256", "thumbnailSha256",
                               "uploadedAt", "publishAt") if receipt.get(key) is not None}
            updated |= write_if_changed(archive / "publish-receipt.json",
                                        json.dumps(public_receipt, indent=2) + "\n")
            updated |= write_if_changed(archive / "source-provenance.json",
                                        json.dumps(provenance, indent=2) + "\n")
            handoffs.append((draft, archive))
            log(f"public source handoff {draft.name} -> {archive.name}")
        if updated:
            changed.append(archive)
    return changed, handoffs


def remove_verified_draft(root: Path, draft: Path) -> None:
    """Only the caller may decide verification passed before this final step."""
    if draft.is_symlink():
        raise ValueError(f"refusing to remove a linked draft: {draft}")
    target = inside(draft, root / "drafts")
    shutil.rmtree(target)
