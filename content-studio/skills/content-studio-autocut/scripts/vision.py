#!/usr/bin/env python3
"""Optional local visual understanding: Ollama vision model + FFmpeg quality signals."""
import argparse
import base64
import json
import math
import re
import subprocess
import urllib.request
from pathlib import Path

def cmd(args):
    p=subprocess.run(args,capture_output=True)
    if p.returncode: raise RuntimeError(p.stderr.decode(errors="replace")[-1000:])
    return p.stdout

def inspect_frame(video, second):
    frame=cmd(["ffmpeg","-v","error","-ss",str(second),"-i",str(video),
        "-frames:v","1","-vf","scale=640:-2","-f","image2pipe","-vcodec","mjpeg","-"])
    if not frame: raise ValueError("Frame extraction returned empty image")
    return frame

def vision(frame, model, endpoint, timeout):
    request={"model":model,"stream":False,"messages":[{"role":"user",
        "content":"Describe only visible actions, setting, and objects in this frame. "
                  "Then rate how useful it might be as travel-vlog B-roll from 0 to 1. "
                  "Return strict JSON: {\"description\":\"...\",\"score\":0.5}. "
                  "Do not identify people or invent locations.",
        "images":[base64.b64encode(frame).decode("ascii")]}]}
    req=urllib.request.Request(endpoint.rstrip("/")+"/api/chat",
        data=json.dumps(request).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as response:
        payload=json.load(response)
    text=payload["message"]["content"]
    try: data=json.loads(text)
    except json.JSONDecodeError:
        match=re.search(r"\{.*\}",text,re.S)
        if not match: raise ValueError("Model did not return JSON")
        data=json.loads(match.group())
    return str(data.get("description","visual candidate"))[:300],max(0,min(1,float(data.get("score",0.5))))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--folder",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--model",default="llava")
    ap.add_argument("--endpoint",default="http://127.0.0.1:11434")
    ap.add_argument("--interval",type=float,default=12)
    ap.add_argument("--timeout",type=int,default=120)
    args=ap.parse_args()
    if args.interval<=0: ap.error("--interval must be positive")
    results=[]
    for video in sorted(args.folder.iterdir()):
        if video.suffix.lower() not in {".mp4",".mov",".mkv",".m4v",".webm",".avi"} or not video.is_file(): continue
        info=json.loads(cmd(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(video)]))
        duration=float(info["format"]["duration"])
        for i in range(math.ceil(duration/args.interval)):
            start=i*args.interval;end=min(duration,start+args.interval)
            if end-start<0.5: continue
            try:
                frame=inspect_frame(video,(start+end)/2)
                desc,score=vision(frame,args.model,args.endpoint,args.timeout)
                results.append({"source":video.name,"start":start,"end":end,
                    "score":round(score,3),"reason":desc})
                print(video.name,round(start,1),desc,flush=True)
            except Exception as e:
                print("Visual analysis failed:",video.name,start,str(e),flush=True)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({"segments":results},indent=2),encoding="utf-8")
    if not results: raise SystemExit("No successful visual annotations")

if __name__=="__main__": main()
