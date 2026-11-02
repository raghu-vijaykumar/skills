#!/usr/bin/env python3
"""Deterministic, reviewable rough-cut builder. Optional external semantic annotations."""
import argparse
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

EXTS={".mp4",".mov",".mkv",".m4v",".webm",".avi"}

def run(cmd):
    p=subprocess.run(cmd,capture_output=True,text=True)
    if p.returncode: raise RuntimeError((p.stderr or p.stdout)[-1800:])
    return p.stdout

def duration(path):
    return float(run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(path)]).strip())

def seconds(value):
    if isinstance(value,(int,float)): return float(value)
    if re.fullmatch(r"\d+(\.\d+)?m",value): return float(value[:-1])*60
    if re.fullmatch(r"\d+(\.\d+)?s",value): return float(value[:-1])
    return float(value)

def read_segments(path, sources, annotations):
    if not path: return []
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data,dict): data=data.get("segments",[])
    result=[]
    for s in data:
        name=Path(s.get("source",s.get("file",""))).name
        if name not in sources: continue
        start=float(s["start"]); end=float(s["end"])
        if not (0<=start<end<=sources[name]): continue
        result.append({"source":name,"start":start,"end":end,"score":float(s.get("score",0.5)),
                       "reason":s.get("reason","annotated relevance" if annotations else "timestamped speech"),
                       "text":s.get("text","")})
    return result

def build(args):
    folder=args.folder.resolve(); out=args.output.resolve()
    if not folder.is_dir(): raise ValueError("Input folder does not exist")
    if folder==out or folder in out.parents and out==folder: raise ValueError("Output must differ from input")
    if out.exists() and any(out.iterdir()) and not args.force: raise ValueError("Output folder not empty; use --force")
    sources={p.name:duration(p) for p in sorted(folder.iterdir()) if p.is_file() and p.suffix.lower() in EXTS}
    if not sources: raise ValueError("No supported videos")
    clips=read_segments(args.transcripts,sources,False)+read_segments(args.annotations,sources,True)
    if not clips:
        for name,d in sources.items():
            for start in range(0,int(d),20):
                end=min(d,start+12)
                if end-start>=2: clips.append({"source":name,"start":float(start),"end":end,"score":0.4,
                    "reason":"unreviewed evenly sampled footage; no semantic analysis","text":""})
    # Prefer annotated relevance, then speech; preserve chronological capture order for narrative coherence.
    target=seconds(args.duration)
    ranked=sorted(clips,key=lambda c:(-c["score"],list(sources).index(c["source"]),c["start"]))
    selected=[]; used=0
    for c in ranked:
        if used>=target: break
        if any(x["source"]==c["source"] and max(x["start"],c["start"])<min(x["end"],c["end"]) for x in selected): continue
        length=min(c["end"]-c["start"],target-used)
        if length<0.5: continue
        selected.append({**c,"end":round(c["start"]+length,3)})
        used+=length
    selected.sort(key=lambda c:(list(sources).index(c["source"]),c["start"]))
    if not selected: raise ValueError("No eligible segments")
    out.mkdir(parents=True,exist_ok=True)
    decisions={"style":args.style,"target_seconds":target,"actual_seconds":round(used,3),
               "semantic_analysis":"external annotations only" if args.annotations else "not performed",
               "segments":selected}
    (out/"edit-decisions.json").write_text(json.dumps(decisions,indent=2),encoding="utf-8")
    otio={"OTIO_SCHEMA":"Timeline.1","name":"AI Rough Cut (review required)","tracks":{"OTIO_SCHEMA":"Stack.1","children":[
        {"OTIO_SCHEMA":"Track.1","kind":"Video","children":[{
            "OTIO_SCHEMA":"Clip.2","name":c["source"],"media_reference":{"OTIO_SCHEMA":"ExternalReference.1",
            "target_url":(folder/c["source"]).as_uri()},"source_range":{"OTIO_SCHEMA":"TimeRange.1",
            "start_time":{"OTIO_SCHEMA":"RationalTime.1","value":c["start"],"rate":1},
            "duration":{"OTIO_SCHEMA":"RationalTime.1","value":c["end"]-c["start"],"rate":1}}}
            for c in selected]}]}}
    (out/"timeline.otio").write_text(json.dumps(otio,indent=2),encoding="utf-8")
    rows="".join("<tr><td>"+html.escape(c["source"])+"</td><td>"+str(round(c["start"],2))+"–"+
       str(round(c["end"],2))+"</td><td>"+html.escape(c["reason"])+"</td><td>"+
       html.escape(c["text"])+"</td></tr>" for c in selected)
    (out/"review.html").write_text("<!doctype html><meta charset='utf-8'><title>Rough cut review</title>"+
       "<h1>Review before publishing</h1><p>Automatic selections are proposals, not approved edits.</p>"+
       "<table border='1'><tr><th>Source</th><th>Range (s)</th><th>Reason</th><th>Speech</th></tr>"+
       rows+"</table>",encoding="utf-8")
    parts=[]
    for i,c in enumerate(selected):
        path=out/f"segment-{i:04d}.mp4";parts.append(path)
        run(["ffmpeg","-y","-hide_banner","-loglevel","error","-ss",str(c["start"]),
             "-i",str(folder/c["source"]),"-t",str(c["end"]-c["start"]),
             "-vf","scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
             "-r","30","-c:v","libx264","-preset","veryfast","-crf","20","-an",str(path)])
    concat=out/"segments.txt"
    concat.write_text("".join("file '"+p.name+"'\n" for p in parts),encoding="utf-8")
    run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat","-safe","0",
         "-i",str(concat),"-c","copy",str(out/"rough-cut.mp4")])
    print(json.dumps({"output":str(out/"rough-cut.mp4"),"segments":len(selected),"seconds":used},indent=2))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--folder",type=Path,required=True)
    p.add_argument("--duration",default="12m")
    p.add_argument("--style",default="travel-vlog")
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--transcripts",type=Path)
    p.add_argument("--annotations",type=Path)
    p.add_argument("--force",action="store_true")
    args=p.parse_args()
    for binary in ("ffmpeg","ffprobe"):
        if not shutil.which(binary): p.error(binary+" missing from PATH")
    try: build(args)
    except Exception as e: p.exit(1,str(e)+"\n")

if __name__=="__main__": main()
