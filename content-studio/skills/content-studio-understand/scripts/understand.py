#!/usr/bin/env python3
"""Extract sparse evidence frames from an approved video. No invented semantic inference."""
import argparse, json, hashlib, subprocess
from pathlib import Path

def probe(video):
    p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(video)],capture_output=True,text=True,check=True)
    return float(json.loads(p.stdout)["format"]["duration"])

def run(video,out,interval,context):
    video=Path(video).resolve(); out=Path(out).resolve()
    if not video.is_file(): raise FileNotFoundError(video)
    if interval<=0: raise ValueError("interval must be positive")
    duration=probe(video); out.mkdir(parents=True,exist_ok=True)
    frames=out/"frames"; frames.mkdir(exist_ok=True)
    digest=hashlib.sha256()
    with video.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):digest.update(block)
    items=[]
    times=[min(duration/2,0.5)] if duration<interval else [min(t,duration-0.05) for t in range(0,int(duration)+1,interval) if t<duration]
    for i,t in enumerate(times):
        name=f"frame-{i:04d}.jpg"; path=frames/name
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",str(t),"-i",str(video),"-frames:v","1","-vf","scale=960:-2",str(path)],check=True)
        items.append({"id":f"f{i:04d}","at_seconds":round(t,3),"path":str(path.relative_to(out))})
    human={}
    if context:
        human=json.loads(Path(context).read_text(encoding="utf-8"))
        if not isinstance(human,dict):raise ValueError("context must be a JSON object")
    result={"source":str(video),"source_sha256":digest.hexdigest(),"duration_seconds":duration,"interval_seconds":interval,"frames":items,"human_context":human,"observations":[],"status":"awaiting_vision_analysis"}
    (out/"evidence.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    (out/"voiceover-template.json").write_text(json.dumps({"source_sha256":digest.hexdigest(),"approval":"pending","segments":[]},indent=2),encoding="utf-8")
    print(out/"evidence.json")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--video",required=True);p.add_argument("--out",required=True);p.add_argument("--interval",type=float,default=8);p.add_argument("--context")
    a=p.parse_args();run(a.video,a.out,a.interval,a.context)
