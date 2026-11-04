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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from timeline import initial_timeline, write_revision, render, write_edit_timeline

EXTS={".mp4",".mov",".mkv",".m4v",".webm",".avi"}

def run(cmd):
    p=subprocess.run(cmd,capture_output=True,text=True)
    if p.returncode: raise RuntimeError((p.stderr or p.stdout)[-1800:])
    return p.stdout

def duration(path):
    return float(run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(path)]).strip())

def seconds(value):
    if isinstance(value,(int,float)): return float(value)
    text=str(value).strip().lower()
    if re.fullmatch(r"\d+(\.\d+)?",text): return float(text)
    match=re.fullmatch(r"(?:(\d+(?:\.\d+)?)h)?(?:(\d+(?:\.\d+)?)m)?(?:(\d+(?:\.\d+)?)s)?",text)
    if not match or not any(match.groups()):
        raise ValueError(f"invalid duration: {value}")
    hours,minutes,secs=(float(part) if part else 0 for part in match.groups())
    return hours*3600+minutes*60+secs

def parse_size(value):
    match=re.fullmatch(r"(\d+)x(\d+)",str(value).strip().lower())
    if not match: raise ValueError("size must look like 1920x1080")
    width,height=int(match.group(1)),int(match.group(2))
    if width<=0 or height<=0 or width%2 or height%2:
        raise ValueError("size must be positive even dimensions")
    return width,height

def orientation(width,height):
    if width>height: return "landscape"
    if height>width: return "portrait"
    return "square"

def media_info(path):
    data=json.loads(run(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(path)]))
    video=next((s for s in data.get("streams",[]) if s.get("codec_type")=="video"),None)
    if not video: raise ValueError("No video stream: "+str(path))
    duration=float(data.get("format",{}).get("duration") or 0)
    width=int(video.get("width") or 0); height=int(video.get("height") or 0)
    rotation=0
    for side in video.get("side_data_list",[]):
        if "rotation" in side: rotation=int(side["rotation"])
    if abs(rotation)%180==90: width,height=height,width
    if duration<=0 or width<=0 or height<=0: raise ValueError("Invalid media metadata: "+str(path))
    return duration,width,height


def max_resolution(dimensions):
    best=None
    for width,height in dimensions.values():
        key=(width*height,1 if width>=height else 0)
        if best is None or key>best[0]: best=(key,width,height)
    if best is None: raise ValueError("No source dimensions")
    return best[1],best[2]

def filter_source_map(sources,dimensions,target,include_mismatched=False,allow=None):
    if target in (None,"","any"): return dict(sources),[]
    allowed={str(name).lower() for name in (allow or [])}
    kept={}; skipped=[]
    for name,duration in sources.items():
        width,height=dimensions[name]
        value=orientation(width,height)
        if value==target or include_mismatched or name.lower() in allowed:
            kept[name]=duration
        else:
            skipped.append({"source":name,"width":width,"height":height,
                            "orientation":value,"reason":"does not match target orientation"})
    return kept,skipped

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
            "-vf", "fps=2,select=gt(scene\\,0.35),showinfo", "-an", "-f", "null", "-"],
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

def score_quality(clips, folder):
    """Cheap image-quality heuristic; down-ranks underexposed, overexposed and soft frames."""
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Install numpy for --quality-score") from exc
    for clip in clips:
        mid=(clip["start"]+clip["end"])/2
        p=subprocess.run(["ffmpeg","-v","error","-ss",str(mid),
            "-i",str(folder/clip["source"]),"-frames:v","1",
            "-vf","scale=160:90,format=gray","-f","rawvideo","-"],
            capture_output=True)
        if p.returncode or len(p.stdout)!=160*90: continue
        frame=np.frombuffer(p.stdout,dtype=np.uint8).reshape(90,160).astype(np.float32)
        luminance=float(frame.mean())
        lap=frame[1:-1,2:]+frame[1:-1,:-2]+frame[2:,1:-1]+frame[:-2,1:-1]-4*frame[1:-1,1:-1]
        sharpness=float(np.abs(lap).mean())
        exposure=max(0.2,min(1.0,luminance/55,(245-luminance)/35))
        focus=max(0.2,min(1.0,sharpness/9))
        quality=round(exposure*focus,3)
        clip["quality"]=quality
        clip["score"]=round(clip["score"]*(0.65+0.35*quality),4)
        clip["reason"]+="; exposure/sharpness heuristic"
    return clips

def generate_review_assets(out, selected, folder):
    """Produce real, inspectable assets from the selected source ranges."""
    review=out/"review"
    frames=review/"frames"
    audio=review/"audio"
    frames.mkdir(parents=True,exist_ok=True)
    audio.mkdir(parents=True,exist_ok=True)
    assets=[]
    for i,clip in enumerate(selected):
        source=folder/clip["source"]
        middle=(clip["start"]+clip["end"])/2
        frame=frames/f"shot-{i:04d}.jpg"
        run(["ffmpeg","-y","-v","error","-ss",str(middle),"-i",str(source),
             "-frames:v","1","-vf","scale=640:-2",str(frame)])
        sample=audio/f"shot-{i:04d}.mp3"
        if has_audio(source):
            run(["ffmpeg","-y","-v","error","-ss",str(clip["start"]),"-i",str(source),
                 "-t",str(min(12,clip["end"]-clip["start"])),"-vn","-c:a","libmp3lame",
                 "-b:a","128k",str(sample)])
        assets.append({"frame":frame.relative_to(out).as_posix(),
                       "audio":sample.relative_to(out).as_posix() if sample.exists() else None})
    contact=review/"contact-sheet.html"
    cards=[]
    for i,(clip,asset) in enumerate(zip(selected,assets)):
        audio_tag=("<audio controls preload='none' src='../"+html.escape(asset["audio"],quote=True)+"'></audio>"
                   if asset["audio"] else "<p>No source audio</p>")
        cards.append("<article><img loading='lazy' width='320' src='../"+
            html.escape(asset["frame"],quote=True)+"'><p><b>"+html.escape(clip["source"])+
            "</b> "+str(round(clip["start"],2))+"–"+str(round(clip["end"],2))+
            "s</p><p>"+html.escape(clip["reason"])+"</p>"+audio_tag+"</article>")
    contact.write_text("<!doctype html><meta charset='utf-8'><title>Shot review</title>"+
        "<style>body{font:16px system-ui;background:#171923;color:#f8fafc}"+
        "main{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:18px}"+
        "article{padding:12px;border:1px solid #475569;border-radius:10px}"+
        "img{max-width:100%}</style><h1>Shot and audio review</h1><main>"+
        "".join(cards)+"</main>",encoding="utf-8")
    return assets

def apply_memory(args):
    """Apply only explicitly supported, user-confirmed AutoCut settings."""
    if not args.memory_db:return {}
    import importlib.util
    module_path=Path(__file__).resolve().parents[2]/"content-studio-memory"/"scripts"/"memory.py"
    spec=importlib.util.spec_from_file_location("content_studio_memory",module_path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    db=module.connect(args.memory_db.expanduser().resolve())
    prefs=module.retrieve(db,args.category,args.project)["preferences"]
    applied={}
    for key,attr,allowed in (
        ("autocut_fit","fit",{"pad","blur","crop"}),
        ("autocut_duration","duration",None),
        ("autocut_style","style",None),
    ):
        item=prefs.get(key)
        if not item or item.get("source")!="explicit":continue
        value=item["value"]
        if not isinstance(value,str) or not value.strip():continue
        if allowed and value not in allowed:continue
        if key=="autocut_duration":
            try:
                if not 1<=seconds(value)<=14400:continue
            except ValueError:continue
        setattr(args,attr,value);applied[key]=value
    return applied

def build(args):
    applied_preferences=apply_memory(args)
    folder=args.folder.resolve(); out=args.output.resolve()
    if not folder.is_dir(): raise ValueError("Input folder does not exist")
    if folder==out: raise ValueError("Output must differ from input")
    if out.exists() and any(out.iterdir()) and not args.force: raise ValueError("Output folder not empty; use --force")
    sources={}; dimensions={}
    for path in sorted(folder.iterdir()):
        if path.is_file() and path.suffix.lower() in EXTS:
            clip_duration,width,height=media_info(path)
            sources[path.name]=clip_duration
            dimensions[path.name]=(width,height)
    if not sources: raise ValueError("No supported videos")
    width,height=parse_size(args.size) if args.size and args.size.lower() not in {"auto","max","source"} else max_resolution(dimensions)
    target_orientation=args.orientation or ("any" if not args.size else orientation(width,height))
    sources,skipped=filter_source_map(sources,dimensions,target_orientation,
                                      args.include_mismatched,args.allow)
    if not sources:
        raise ValueError("No videos match orientation "+str(target_orientation))
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
    if args.quality_score: clips = score_quality(clips,folder)
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
    reframe_records=[]
    if args.fit=="reframe":
        import reframe
        for index,clip in enumerate(selected):
            record=reframe.analyze_segment(folder/clip["source"],clip["start"],clip["end"],
                                           (width,height),args.reframe_mode,args.subjects)
            clip["reframe"]=record
            reframe_records.append(record)
            preview_dir=out/"reframe-preview"/f"shot-{index:04d}"
            preview_dir.mkdir(parents=True,exist_ok=True)
            preview=reframe.write_preview(folder/clip["source"],record,preview_dir)
            if preview: record["preview"]=str(preview.relative_to(out))
    out.mkdir(parents=True,exist_ok=True)
    decisions={"memory_preferences_applied":applied_preferences,"style":args.style,"target_seconds":target,"actual_seconds":round(used,3),
               "orientation":target_orientation,"size":f"{width}x{height}","fit":args.fit,
               "skipped_sources":skipped,
               "reframe_mode":args.reframe_mode if args.fit=="reframe" else None,
               "reframe":reframe_records,
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
    timeline=initial_timeline(selected,folder,args.style,width=width,height=height,fit=args.fit)
    if args.force:
        (out/"timeline-history"/"timeline-v001.json").unlink(missing_ok=True)
    write_revision(timeline,out)
    write_edit_timeline(timeline,out)
    render(timeline,out)
    if args.deliver:
        args.deliver.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(out/"rough-cut.mp4",args.deliver)
        print(f"rough cut delivered -> {args.deliver}")
    from timeline import refresh_review
    assets=refresh_review(timeline,out)
    decisions["review_assets"]=assets
    (out/"edit-decisions.json").write_text(json.dumps(decisions,indent=2),encoding="utf-8")
    (out/"review-state.json").write_text(json.dumps({"status":"pending_review",
        "approved":False,"feedback":[],"revision":1},indent=2),encoding="utf-8")
    print(json.dumps({"output":str(out/"rough-cut.mp4"),"review":str(out/"review/contact-sheet.html"),
        "segments":len(selected),"seconds":used,"orientation":target_orientation,
        "size":f"{width}x{height}","fit":args.fit,"skipped":len(skipped)},indent=2))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--folder",type=Path,required=True)
    p.add_argument("--duration",default="12m")
    p.add_argument("--style",default="travel-vlog")
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--deliver",type=Path,
                   help="copy the rendered rough-cut.mp4 to this path (for example draft/rough-cut.mp4)")
    p.add_argument("--transcripts",type=Path)
    p.add_argument("--annotations",type=Path)
    p.add_argument("--force",action="store_true")
    p.add_argument("--auto-transcribe",action="store_true")
    p.add_argument("--whisper-model",default="small")
    p.add_argument("--detect-scenes",action="store_true")
    p.add_argument("--quality-score",action="store_true")
    p.add_argument("--auto-vision",action="store_true")
    p.add_argument("--vision-model",default="llava")
    p.add_argument("--ollama-endpoint",default="http://127.0.0.1:11434")
    p.add_argument("--orientation",choices=["any","landscape","portrait","square"])
    p.add_argument("--include-mismatched",action="store_true",
                   help="keep clips whose orientation does not match the target")
    p.add_argument("--allow",action="append",
                   help="include a specific mismatched filename; repeatable")
    p.add_argument("--fit",choices=["pad","blur","crop","reframe"],default="blur",
                   help="fit mismatched clips with a blurred copy (default), black padding, crop, or subject reframe; reframe is experimental and only for an explicitly requested portrait deliverable")
    p.add_argument("--reframe-mode",choices=["auto","subjects","saliency","center"],default="auto",
                   help="subject signal for --fit reframe: AI boxes, saliency, or center")
    p.add_argument("--subjects",type=Path,
                   help="JSON subject boxes for --fit reframe (source/start/end/box)")
    p.add_argument("--size",help="target size: auto/max or WxH; default highest source resolution")
    p.add_argument("--memory-db",type=Path,help="Optional local editing memory database")
    p.add_argument("--category",choices=["travel","cooking","daily"],default="travel")
    p.add_argument("--project",default="")
    args=p.parse_args()
    for binary in ("ffmpeg","ffprobe"):
        if not shutil.which(binary): p.error(binary+" missing from PATH")
    try: build(args)
    except Exception as e: p.exit(1,str(e)+"\n")

if __name__=="__main__": main()
