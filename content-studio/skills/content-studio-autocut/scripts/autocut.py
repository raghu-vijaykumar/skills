#!/usr/bin/env python3
"""Deterministic, reviewable rough-cut builder. Optional external semantic annotations."""
import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import math
import tempfile
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

def analyze_scenes(sources, folder):
    candidates = []
    for name, duration in sources.items():
        p = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(folder/name),
            "-vf", "fps=2,select='gt(scene,0.35)',showinfo", "-an", "-f", "null", "-"],
            text=True, capture_output=True)
        boundaries = [0.0]
        for match in re.finditer(r"pts_time:([0-9.]+)", p.stderr):
            t = float(match.group(1))
            if 1 < t < duration-1 and t-boundaries[-1] >= 2:
                boundaries.append(t)
        boundaries.append(duration)
        for a,b in zip(boundaries,boundaries[1:]):
            if b-a >= 1:
                candidates.append(dict(source=name,start=a,end=min(a+12,b),
                    score=0.45,reason="scene change candidate (not semantically ranked)",text=""))
    return candidates

def analyze_speech(sources, folder, model):
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("Install optional dependency: pip install faster-whisper") from exc
    engine = WhisperModel(model, device="cpu", compute_type="int8")
    segments = []
    for name in sources:
        chunks,_ = engine.transcribe(str(folder/name),vad_filter=True)
        for chunk in chunks:
            if chunk.end-chunk.start >= 0.5:
                segments.append(dict(source=name,start=chunk.start,end=chunk.end,
                    score=0.8,reason="speech transcription",text=chunk.text.strip()))
    return segments

def has_audio(path):
    streams = json.loads(run(["ffprobe","-v","error","-show_streams","-of","json",str(path)]))["streams"]
    return any(s.get("codec_type")=="audio" for s in streams)

def build(args):
    folder=args.folder.resolve(); out=args.output.resolve()
    if not folder.is_dir(): raise ValueError("Input folder does not exist")
    if folder==out or folder in out.parents and out==folder: raise ValueError("Output must differ from input")
    if out.exists() and any(out.iterdir()) and not args.force: raise ValueError("Output folder not empty; use --force")
    sources={p.name:duration(p) for p in sorted(folder.iterdir()) if p.is_file() and p.suffix.lower() in EXTS}
    if not sources: raise ValueError("No supported videos")
    clips=read_segments(args.transcripts,sources,False)+read_segments(args.annotations,sources,True)
    if args.auto_vision:
        with tempfile.TemporaryDirectory() as tmp:
            vision_file=Path(tmp)/"vision.json"
            run([sys.executable,str(Path(__file__).with_name("vision.py")),"--folder",str(folder),
                 "--output",str(vision_file),"--model",args.vision_model,
                 "--endpoint",args.ollama_endpoint])
            clips += read_segments(vision_file,sources,True)
    if args.auto_transcribe: clips += analyze_speech(sources,folder,args.whisper_model)
    if args.detect_scenes: clips += analyze_scenes(sources,folder)
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
               "semantic_analysis":"local Ollama vision" if args.auto_vision else ("external annotations" if args.annotations else "not performed"),
               "transcription_enabled":args.auto_transcribe,"scene_detection_enabled":args.detect_scenes,
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
        audio=has_audio(folder/c["source"])
        command=["ffmpeg","-y","-hide_banner","-loglevel","error","-ss",str(c["start"]),
             "-i",str(folder/c["source"])]
        if not audio: command+=["-f","lavfi","-i","anullsrc=r=48000:cl=stereo"]
        command+=["-t",str(c["end"]-c["start"]),"-map","0:v:0",
             "-map","0:a:0" if audio else "1:a:0",
             "-vf","scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
             "-r","30","-c:v","libx264","-preset","veryfast","-crf","20",
             "-c:a","aac","-ar","48000","-ac","2","-b:a","192k","-shortest",str(path)]
        run(command)
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
    p.add_argument("--auto-transcribe",action="store_true")
    p.add_argument("--whisper-model",default="small")
    p.add_argument("--detect-scenes",action="store_true")
    p.add_argument("--auto-vision",action="store_true")
    p.add_argument("--vision-model",default="llava")
    p.add_argument("--ollama-endpoint",default="http://127.0.0.1:11434")
    args=p.parse_args()
    for binary in ("ffmpeg","ffprobe"):
        if not shutil.which(binary): p.error(binary+" missing from PATH")
    try: build(args)
    except Exception as e: p.exit(1,str(e)+"\n")

if __name__=="__main__": main()
