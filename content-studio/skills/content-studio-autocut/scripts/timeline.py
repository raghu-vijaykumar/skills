#!/usr/bin/env python3
"""Canonical, versioned, editable timeline and deterministic FFmpeg renderer."""
import argparse
import copy
import hashlib
import html
import json
import shutil
import subprocess
from pathlib import Path

def command(args):
    p=subprocess.run(args,capture_output=True,text=True)
    if p.returncode: raise RuntimeError((p.stderr or p.stdout)[-2000:])
    return p.stdout

def validate(timeline, root):
    if timeline.get("schema")!="content-studio.timeline.v1": raise ValueError("Unsupported timeline schema")
    ids=set()
    for track in timeline.get("tracks",[]):
        if track["kind"] not in ("video","audio","caption"): raise ValueError("Unsupported track kind")
        for clip in track.get("clips",[]):
            if clip["id"] in ids: raise ValueError("Duplicate clip ID")
            ids.add(clip["id"])
            if clip["start"]<0 or clip["duration"]<=0: raise ValueError("Invalid clip timing")
            if track["kind"] in ("video","audio"):
                src=(root/clip["source"]).resolve()
                if not src.is_file() or not src.is_relative_to(root.resolve()): raise ValueError("Missing or unsafe source: "+clip["source"])
                if clip["source_in"]<0 or clip["source_out"]<=clip["source_in"]: raise ValueError("Invalid source range")
                if abs(clip["duration"]-(clip["source_out"]-clip["source_in"]))>0.01: raise ValueError("Duration mismatch")
    video=sorted((c for t in timeline["tracks"] if t["kind"]=="video" for c in t["clips"]),key=lambda x:x["start"])
    cursor=0.
    for clip in video:
        if abs(clip["start"]-cursor)>0.02: raise ValueError("Video track must be contiguous and non-overlapping")
        cursor+=clip["duration"]
    if not video: raise ValueError("No video clips")
    return video

def initial_timeline(segments, folder, style="travel-vlog", width=1920, height=1080, fit="blur"):
    cursor=0.
    clips=[]
    for i,c in enumerate(segments):
        length=round(c["end"]-c["start"],3)
        clip={"id":f"v{i:04d}","source":c["source"],"source_in":c["start"],
              "source_out":c["end"],"start":round(cursor,3),"duration":length,
              "reason":c.get("reason",""),"audio_gain_db":0}
        if c.get("reframe"): clip["reframe"]=c["reframe"]
        clips.append(clip)
        cursor+=length
    return {"schema":"content-studio.timeline.v1","revision":1,"style":style,
            "source_root":str(folder.resolve()),"fps":30,"width":width,"height":height,
            "fit":fit,
            "tracks":[{"id":"picture","kind":"video","clips":clips},
                      {"id":"music","kind":"audio","clips":[]},
                      {"id":"captions","kind":"caption","clips":[]}]}

def write_edit_timeline(timeline, output):
    """Write the ordered contribution of each source to rough-cut.mp4."""
    clips=validate(timeline, Path(timeline["source_root"]))
    entries=[{"order":i,"id":clip["id"],"source":clip["source"],
              "timeline_start":clip["start"],
              "timeline_end":round(clip["start"]+clip["duration"],3),
              "source_in":clip["source_in"],"source_out":clip["source_out"],
              "duration":clip["duration"],"reason":clip.get("reason","")}
             for i,clip in enumerate(clips,1)]
    document={"schema":"content-studio.edit-timeline.v1","master":"rough-cut.mp4",
              "duration_seconds":round(sum(float(e["duration"]) for e in entries),3),
              "clips":entries}
    (output/"edit-timeline.json").write_text(json.dumps(document,indent=2)+"\n",encoding="utf-8")
    rows="".join("<tr><td>"+str(e["order"])+"</td><td>"+f"{e['timeline_start']:.2f}–{e['timeline_end']:.2f}"+
        "</td><td>"+html.escape(e["source"])+"</td><td>"+
        f"{e['source_in']:.2f}–{e['source_out']:.2f}"+"</td><td>"+
        f"{e['duration']:.2f}"+"</td><td>"+html.escape(e["reason"])+"</td></tr>"
        for e in entries)
    page=("<!doctype html><meta charset='utf-8'><title>Edit timeline</title>"
          "<style>body{font:15px/1.5 system-ui,sans-serif;margin:2rem;color:#0f172a}"
          "h1{margin:0 0 .25rem}p{color:#475569;margin:0 0 1.25rem}"
          "table{border-collapse:collapse;width:100%}th,td{padding:.55rem .7rem;"
          "border-bottom:1px solid #e2e8f0;text-align:left;vertical-align:top}"
          "th{background:#f8fafc;font-size:.8rem;letter-spacing:.04em;text-transform:uppercase;color:#475569}"
          "tr:hover td{background:#f8fafc}code{font-family:ui-monospace,monospace}</style>"
          "<h1>Edit timeline</h1><p>"+str(len(entries))+" source contribution(s) · "+
          f"{document['duration_seconds']:.2f}s master · <code>rough-cut.mp4</code></p>"
          "<table><thead><tr><th>#</th><th>Master time (s)</th><th>Source</th>"
          "<th>Source in–out (s)</th><th>Duration (s)</th><th>Reason</th></tr></thead>"
          "<tbody>"+rows+"</tbody></table>")
    (output/"edit-timeline.html").write_text(page,encoding="utf-8")
    return output/"edit-timeline.json"


def write_revision(timeline, output):
    history=output/"timeline-history"
    history.mkdir(parents=True,exist_ok=True)
    number=timeline["revision"]
    snapshot=history/f"timeline-v{number:03d}.json"
    if snapshot.exists(): raise FileExistsError("Revision already exists: "+str(snapshot))
    encoded=json.dumps(timeline,indent=2)+"\n"
    snapshot.write_text(encoded,encoding="utf-8")
    (output/"timeline.json").write_text(encoded,encoding="utf-8")
    return snapshot

def revise(timeline, instructions):
    t=copy.deepcopy(timeline)
    picture=next(x for x in t["tracks"] if x["kind"]=="video")
    clips=picture["clips"]
    for op in instructions:
        action=op["action"]
        if action=="remove":
            clips[:]=[c for c in clips if c["id"]!=op["id"]]
        elif action=="trim":
            clip=next(c for c in clips if c["id"]==op["id"])
            a=float(op.get("source_in",clip["source_in"]))
            b=float(op.get("source_out",clip["source_out"]))
            if a<0 or b<=a: raise ValueError("Invalid trim")
            clip.update(source_in=a,source_out=b,duration=round(b-a,3))
        elif action=="move":
            clip=next(c for c in clips if c["id"]==op["id"])
            clips.remove(clip)
            clips.insert(int(op["index"]),clip)
        elif action=="gain":
            clip=next(c for c in clips if c["id"]==op["id"])
            clip["audio_gain_db"]=float(op["db"])
        else: raise ValueError("Unknown edit operation: "+action)
    cursor=0.
    for clip in clips:
        clip["start"]=round(cursor,3)
        cursor+=clip["duration"]
    t["revision"]+=1
    return t

def fit_filter(label, width, height, fit, out, reframe=None):
    if width<=0 or height<=0 or width%2 or height%2:
        raise ValueError("target size must be positive even dimensions")
    fit=str(fit or "blur").lower()
    if fit=="reframe":
        if not reframe: raise ValueError("reframe fit requires reframe metadata")
        source_width=int(reframe["source_width"]); source_height=int(reframe["source_height"])
        crop=reframe["crop"]
        crop_width=max(2,int(round(float(crop["w"])*source_width)))
        crop_height=max(2,int(round(float(crop["h"])*source_height)))
        crop_width-=crop_width%2; crop_height-=crop_height%2
        x=max(0,min(source_width-crop_width,int(round(float(crop["x"])*source_width))))
        y=max(0,min(source_height-crop_height,int(round(float(crop["y"])*source_height))))
        return [f"{label}crop={crop_width}:{crop_height}:{x}:{y},"
                f"scale={width}:{height},format=yuv420p{out}"]
    if fit=="pad":
        return [f"{label}scale={width}:{height}:force_original_aspect_ratio=decrease:"
                f"force_divisible_by=2,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
                f"format=yuv420p{out}"]
    if fit=="crop":
        return [f"{label}scale={width}:{height}:force_original_aspect_ratio=increase:"
                f"force_divisible_by=2,crop={width}:{height},format=yuv420p{out}"]
    if fit=="blur":
        return [
            f"{label}split=2[bg][fg]",
            f"[bg]scale={width}:{height}:force_original_aspect_ratio=increase:"
            f"force_divisible_by=2,crop={width}:{height},gblur=sigma=20[bgblur]",
            f"[fg]scale={width}:{height}:force_original_aspect_ratio=decrease:"
            f"force_divisible_by=2[fgfit]",
            f"[bgblur][fgfit]overlay=(W-w)/2:(H-h)/2,format=yuv420p{out}",
        ]
    raise ValueError("Unknown fit mode: "+fit)

def enhancement_filters(clip):
    """Translate source-time enhancements into clip-relative FFmpeg filters."""
    filters=[]
    source_in=float(clip["source_in"])
    duration=float(clip["duration"])
    for item in clip.get("enhancements") or []:
        start=max(0.0,float(item.get("source_start",0))-source_in)
        end=min(duration,float(item.get("source_end",0))-source_in)
        if end<=start: continue
        if item.get("stage") == "polish":
            filters.extend(value for value in (item.get("filters") or []) if value)
            continue
        for value in item.get("filters") or []:
            if value:
                filters.append(f"{value}:enable='between(t,{start:.3f},{end:.3f})'")
    return filters


def render(timeline, output):
    root=Path(timeline["source_root"]).resolve()
    video=validate(timeline,root)
    fit=timeline.get("fit","blur")
    width=timeline["width"]; height=timeline["height"]
    cache=output/"render-cache"
    cache.mkdir(parents=True,exist_ok=True)
    parts=[]
    for clip in video:
        src=root/clip["source"]
        settings={k:clip[k] for k in ("source","source_in","source_out","audio_gain_db")}
        if clip.get("reframe"): settings["reframe"]=clip["reframe"]
        if clip.get("enhancements"): settings["enhancements"]=clip["enhancements"]
        settings.update(fps=timeline["fps"],width=width,height=height,fit=fit,
                        mtime=src.stat().st_mtime_ns,size=src.stat().st_size)
        digest=hashlib.sha256(json.dumps(settings,sort_keys=True).encode()).hexdigest()[:20]
        segment=cache/(digest+".mp4")
        if not segment.exists():
            audio=subprocess.run(["ffprobe","-v","error","-select_streams","a:0",
                "-show_entries","stream=index","-of","csv=p=0",str(src)],capture_output=True,text=True)
            has_audio=bool(audio.stdout.strip())
            args=["ffmpeg","-y","-v","error","-ss",str(clip["source_in"]),"-i",str(src)]
            if not has_audio: args+=["-f","lavfi","-i","anullsrc=r=48000:cl=stereo"]
            graph=fit_filter("[0:v:0]",width,height,fit,"[v]",clip.get("reframe"))
            extra=enhancement_filters(clip)
            if extra:
                graph=["[0:v:0]"+",".join(extra)+"[enh]"]+fit_filter(
                    "[enh]",width,height,fit,"[v]",clip.get("reframe"))
            args+=["-t",str(clip["duration"]),"-filter_complex",";".join(graph),
                   "-map","[v]","-map","0:a:0" if has_audio else "1:a:0",
                   "-r",str(timeline["fps"]),"-c:v","libx264","-preset","veryfast","-crf","20",
                   "-c:a","aac","-ar","48000","-ac","2","-af",f"volume={clip['audio_gain_db']}dB",
                   "-shortest",str(segment)]
            command(args)
        parts.append(segment)
    concat=output/"timeline-concat.txt"
    concat.write_text("".join("file '"+str(p.resolve()).replace("'","'\\''")+"'\n" for p in parts),encoding="utf-8")
    command(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(concat),
             "-c","copy",str(output/"rough-cut.mp4")])
    return output/"rough-cut.mp4"

def refresh_review(timeline, output):
    """Rebuild human-review media for the CURRENT timeline revision."""
    from autocut import generate_review_assets
    root=Path(timeline["source_root"]).resolve()
    clips=validate(timeline,root)
    selected=[{"source":c["source"],"start":c["source_in"],"end":c["source_out"],
               "reason":c.get("reason","timeline edit"),"text":""} for c in clips]
    assets=generate_review_assets(output,selected,root)
    (output/"review-manifest.json").write_text(json.dumps({
        "revision":timeline["revision"],"assets":assets,
        "video":"rough-cut.mp4"},indent=2),encoding="utf-8")
    review=output/"review.html"
    review.write_text("<!doctype html><meta charset='utf-8'><title>Review revision</title>"+
        "<h1>Timeline revision "+str(timeline["revision"])+"</h1>"+
        "<video controls width='800' src='rough-cut.mp4'></video>"+
        "<p><a href='review/contact-sheet.html'>Review frames and audio</a></p>",encoding="utf-8")
    return assets

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--render",action="store_true")
    p.add_argument("--edits",type=Path,help="JSON list of remove/trim/move/gain operations")
    p.add_argument("--rollback",type=int)
    a=p.parse_args()
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"): p.error("FFmpeg/FFprobe required")
    out=a.output.resolve()
    current=out/"timeline.json"
    if not current.is_file(): p.error("Missing timeline.json")
    timeline=json.loads(current.read_text(encoding="utf-8"))
    if a.edits and a.rollback is not None: p.error("Choose edits or rollback")
    if a.rollback is not None:
        previous=out/"timeline-history"/f"timeline-v{a.rollback:03d}.json"
        if not previous.is_file(): p.error("Revision not found")
        old=json.loads(previous.read_text(encoding="utf-8"))
        old["revision"]=timeline["revision"]+1
        validate(old,Path(old["source_root"]))
        write_revision(old,out)
        timeline=old
    elif a.edits:
        edits=json.loads(a.edits.read_text(encoding="utf-8"))
        timeline=revise(timeline,edits)
        validate(timeline,Path(timeline["source_root"]))
        write_revision(timeline,out)
    if a.edits or a.rollback is not None:
        state_path=out/"review-state.json"
        if state_path.exists():
            state=json.loads(state_path.read_text(encoding="utf-8"))
            state.update(status="pending_review",approved=False,revision=timeline["revision"])
            state_path.write_text(json.dumps(state,indent=2),encoding="utf-8")
    if a.render:
        result=render(timeline,out)
        refresh_review(timeline,out)
        print(result)
    else: print(json.dumps({"revision":timeline["revision"],"timeline":str(current)}))

if __name__=="__main__": main()
