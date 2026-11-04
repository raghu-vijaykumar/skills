#!/usr/bin/env python3
"""Local voice-profile bootstrap; no model download or synthesis during enrollment."""
import argparse, hashlib, json, os, shutil, subprocess, tempfile, datetime
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def probe(path):
    p=subprocess.run(["ffprobe","-v","error","-select_streams","a:0","-show_entries","stream=sample_rate,channels:format=duration","-of","json",str(path)],capture_output=True,text=True)
    if p.returncode or not p.stdout.strip():raise ValueError("Cannot decode audio: "+str(path))
    data=json.loads(p.stdout)
    if not data.get("streams"):raise ValueError("No audio stream: "+str(path))
    return float(data.get("format",{}).get("duration",0))

def main():
    ap=argparse.ArgumentParser(description="Bootstrap a consented local voice profile")
    ap.add_argument("--workspace",required=True)
    sub=ap.add_subparsers(dest="action",required=True)
    init=sub.add_parser("enroll")
    init.add_argument("--samples",nargs="+",required=True)
    init.add_argument("--profile",default="my-voice")
    init.add_argument("--language",default="kn-en")
    init.add_argument("--consent",action="store_true",help="I own this voice or have explicit permission to clone it")
    init.add_argument("--consent-note",required=True)
    status=sub.add_parser("status")
    status.add_argument("--profile",default="my-voice")
    a=ap.parse_args()
    root=Path(a.workspace).expanduser().resolve()/".content-studio"/"voice"/"profiles"/a.profile
    manifest=root/"profile.json"
    if a.action=="status":
        if not manifest.exists():raise SystemExit("No enrolled voice profile")
        data=json.loads(manifest.read_text(encoding="utf-8"))
        missing=[s["file"] for s in data["samples"] if not (root/s["file"]).exists()]
        print(json.dumps({"profile":a.profile,"samples":len(data["samples"]),"duration_seconds":data["total_duration_seconds"],"consent":data["consent"],"missing_samples":missing,"synthesis_ready":False},indent=2))
        return
    if not a.consent:raise SystemExit("Explicit --consent is required")
    if not a.consent_note.strip():raise SystemExit("Consent note must not be empty")
    if manifest.exists():raise SystemExit("Profile exists; use another name (no implicit overwrite)")
    samples=[Path(s).expanduser().resolve() for s in a.samples]
    if not all(s.is_file() for s in samples):raise SystemExit("One or more samples do not exist")
    durations=[probe(s) for s in samples]
    if any(d<3 for d in durations):raise SystemExit("Each sample must contain at least 3 seconds of audio")
    if sum(durations)<20:raise SystemExit("Provide at least 20 seconds of total speech samples")
    root.mkdir(parents=True,exist_ok=True)
    records=[]
    try:
        for i,(src,duration) in enumerate(zip(samples,durations)):
            dest=root/f"sample-{i:03d}.wav"
            subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-n","-i",str(src),"-vn","-ac","1","-ar","24000","-c:a","pcm_s16le",str(dest)],check=True)
            records.append({"file":dest.name,"sha256":sha(dest),"duration_seconds":round(duration,2),"source_name":src.name})
        data={"schema_version":1,"name":a.profile,"language":a.language,"samples":records,"total_duration_seconds":round(sum(durations),2),"consent":{"affirmed":True,"note":a.consent_note,"recorded_at":datetime.datetime.now(datetime.timezone.utc).isoformat()},"backend":{"name":None,"configured":False},"synthesis_ready":False}
        manifest.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")
    except Exception:
        for record in records:(root/record["file"]).unlink(missing_ok=True)
        raise
    print("Enrolled locally:",manifest)
    print("Voice synthesis is NOT configured. Review samples and install a compatible licensed backend before generating narration.")

if __name__=="__main__":main()
