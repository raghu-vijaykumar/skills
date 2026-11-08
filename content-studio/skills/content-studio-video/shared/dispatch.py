"""Keep operation-specific entrypoints thin while legacy engines are extracted."""

from pathlib import Path
import subprocess
import sys


def video_root(script: str) -> Path:
    path = Path(script).resolve()
    return next(parent for parent in path.parents if parent.name == "content-studio-video")


def run_python(script: str, target: str, fixed: tuple[str, ...] = (),
               forbidden: tuple[str, ...] = ()) -> int:
    args = sys.argv[1:]
    # A method entrypoint cannot be silently changed by a later CLI flag.
    protected = {item for item in fixed if item.startswith("--")} | set(forbidden)
    for argument in args:
        if any(argument == flag or argument.startswith(flag + "=") for flag in protected):
            raise SystemExit(f"method option is fixed or unavailable here: {argument}")
    path = video_root(script) / target
    if not path.is_file():
        raise SystemExit(f"method backend is unavailable: {path}")
    return subprocess.call([sys.executable, str(path), *fixed, *args])
