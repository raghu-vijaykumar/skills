"""Render a consented, local Indic-Mio emotion comparison through speech-core.

The Speech Studio sidecar speaks newline-delimited JSON, so no UI or Python ML
environment is needed once its LiteRT model bundle has been cached locally.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


PROFILE_ROOT = Path(__file__).resolve().parents[1] / "profiles"
MODEL_NAME = "soniqo/Indic-Mio-LiteRT"
EMOTIONS = {"neutral": "", "happy": "<happy>", "surprise": "<surprise>"}
CONDITIONS = (
    ("kn-neutral", "neutral", "ಇವತ್ತು ಇಲ್ಲಿ ತುಂಬಾ ಚೆನ್ನಾಗಿದೆ!"),
    ("kn-happy", "happy", "ಇವತ್ತು ಇಲ್ಲಿ ತುಂಬಾ ಚೆನ್ನಾಗಿದೆ!"),
    ("mixed-neutral", "neutral", "Wow, ನೋಡಿ! Dubai Fountain ತುಂಬಾ ಸುಂದರವಾಗಿದೆ!"),
    ("mixed-surprise", "surprise", "Wow, ನೋಡಿ! Dubai Fountain ತುಂಬಾ ಸುಂದರವಾಗಿದೆ!"),
)


def local_appdata() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        local = str(Path.home() / "AppData" / "Local")
    return Path(local)


def default_output() -> Path:
    return local_appdata() / "ContentStudio" / "voice-tests" / "indic-mio-rakshitha"


def default_sidecar() -> Path:
    return local_appdata() / "ContentStudio" / "tools" / "speech-core-v0.0.10" / "speech-core-tts-sidecar.exe"


def default_bundle() -> Path:
    return local_appdata() / "speech-core" / "soniqo__Indic-Mio-LiteRT"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checked_profile(profile: Path) -> tuple[Path, str]:
    details = json.loads((profile / "profile.json").read_text(encoding="utf-8"))
    consent = details.get("consent", {})
    if consent.get("affirmed") is not True or not consent.get("note"):
        raise ValueError("profile has no affirmed consent note")
    reference = profile / "reference.wav"
    transcript = (profile / "reference.txt").read_text(encoding="utf-8").strip()
    if not reference.is_file() or not transcript:
        raise ValueError("profile reference audio or transcript is missing")
    return reference, transcript


def checked_bundle(bundle: Path) -> None:
    # Fail before starting the sidecar when the model download is unfinished.
    required = (
        "indicmio-text-prefill.tflite",
        "indicmio-token-step.tflite",
        "indicmio-audio-decoder.tflite",
        "indicmio-ref-encoder.tflite",
        "tokenizer.json",
        "config.json",
    )
    missing = [name for name in required if not (bundle / name).is_file()]
    if missing:
        raise ValueError("Indic-Mio bundle is incomplete: " + ", ".join(missing))


def model_text(text: str, emotion: str) -> str:
    # Match Studio's spaced suffix format so the emotion tag is a separate token.
    tag = EMOTIONS[emotion]
    return text + (" " + tag if tag else "")


class Sidecar:
    def __init__(self, executable: Path, bundle: Path, log_path: Path):
        env = os.environ.copy()
        env["SONIQO_INDIC_MIO_BUNDLE_DIR"] = str(bundle)
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        self.process = subprocess.Popen(
            [str(executable)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1,
            env=env, creationflags=creationflags,
        )
        self.responses: queue.Queue[str | None] = queue.Queue()
        self.log_path = log_path
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def _read_stdout(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            self.responses.put(line)
        self.responses.put(None)

    def _read_stderr(self) -> None:
        assert self.process.stderr is not None
        with self.log_path.open("w", encoding="utf-8") as log:
            for line in self.process.stderr:
                log.write(line)
                log.flush()

    def request(self, request: dict, timeout: int = 1200) -> dict:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(request, ensure_ascii=False) + "\n")
        self.process.stdin.flush()
        try:
            line = self.responses.get(timeout=timeout)
        except queue.Empty as exc:
            raise TimeoutError(f"sidecar timed out on {request['id']}; see {self.log_path}") from exc
        if line is None:
            raise RuntimeError(f"sidecar exited on {request['id']}; see {self.log_path}")
        result = json.loads(line)
        if result.get("id") != request["id"] or not result.get("ok"):
            raise RuntimeError(f"sidecar failed on {request['id']}: {result.get('error', result)}")
        return result["result"]

    def close(self) -> None:
        if self.process.stdin:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()


def run(args: argparse.Namespace) -> Path:
    if not 16 <= args.max_tokens <= 384:
        raise ValueError("--max-tokens must be between 16 and 384")
    if not 0 <= args.seed <= 0xFFFFFFFF:
        raise ValueError("--seed must fit an unsigned 32-bit integer")
    profile = args.profile.resolve()
    reference, reference_text = checked_profile(profile)
    checked_bundle(args.bundle)
    if not args.sidecar.is_file():
        raise ValueError(f"sidecar missing: {args.sidecar}")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    # IDs are stable for reproducible paired comparisons; use a new run folder
    # so prior WAVs and provenance are never overwritten.
    run_dir = output / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir.mkdir(exist_ok=False)
    report = {
        "status": "in_progress", "created_utc": datetime.now(timezone.utc).isoformat(),
        "profile": profile.name, "reference": str(reference),
        "reference_sha256": sha256(reference), "reference_text": reference_text,
        "model": MODEL_NAME, "bundle": str(args.bundle.resolve()),
        "sidecar": str(args.sidecar.resolve()), "seed": args.seed,
        "temperature": 0.3, "max_tokens": args.max_tokens, "conditions": [],
        "human_listening_review": "pending",
    }
    report_path = run_dir / "manifest.json"
    def save() -> None:
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    save()
    sidecar = Sidecar(args.sidecar, args.bundle, run_dir / "sidecar.log")
    try:
        sidecar.request({"id": "ping", "command": "ping"}, timeout=20)
        sidecar.request({"id": "init-indic-mio", "command": "init_model", "engine": "indic-mio"})
        for ident, emotion, text in CONDITIONS:
            # Indic-Mio expects its emotion marker at the end of the utterance.
            marked_text = model_text(text, emotion)
            started = time.monotonic()
            result = sidecar.request({
                "id": ident, "command": "synthesize_indic_mio", "engine": "indic-mio",
                "modelId": MODEL_NAME, "voiceId": profile.name,
                "referenceAudioPath": str(reference), "referenceText": reference_text,
                "text": marked_text, "seed": args.seed, "maxTokens": args.max_tokens,
            })
            source = Path(result["audioPath"])
            target = run_dir / f"{ident}.wav"
            target.write_bytes(source.read_bytes())
            entry = {
                "id": ident, "emotion": emotion, "text": text, "model_text": marked_text,
                "wav": str(target), "wav_sha256": sha256(target),
                "sample_rate": result["sampleRate"], "duration_sec": result["durationSec"],
                "render_sec": round(time.monotonic() - started, 2),
            }
            report["conditions"].append(entry)
            save()
            print(f"{ident}: {entry['duration_sec']:.2f}s audio in {entry['render_sec']:.1f}s", flush=True)
        report["status"] = "rendered_review_pending"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = str(exc)
        raise
    finally:
        save()
        sidecar.close()
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sidecar", type=Path, default=default_sidecar())
    parser.add_argument("--bundle", type=Path, default=default_bundle())
    parser.add_argument("--profile", type=Path, default=PROFILE_ROOT / "rakshitha")
    parser.add_argument("--output", type=Path, default=default_output())
    parser.add_argument("--seed", type=int, default=1000)
    parser.add_argument("--max-tokens", type=int, default=192)
    args = parser.parse_args()
    try:
        print(run(args))
        return 0
    except (OSError, ValueError, RuntimeError, TimeoutError) as exc:
        print(f"Indic-Mio comparison failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
