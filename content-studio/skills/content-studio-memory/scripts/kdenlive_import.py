#!/usr/bin/env python3
"""Import simple Kdenlive MLT playlists into a source-referenced observation timeline.

Unsupported nested tractors, timewarp and transitions are reported, not guessed.
"""
import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

def props(node):
    return {x.get("name"):x.text or "" for x in node.findall("property")}

def seconds(tc,fps):
    if tc is None:return None
    if re.fullmatch(r"\d+(?:\.\d+)?",tc):return float(tc)
    if re.fullmatch(r"\d+:\d+:\d+(?:\.\d+)?",tc):
        h,m,s=tc.split(":");return int(h)*3600+int(m)*60+float(s)
    if re.fullmatch(r"\d+:\d+:\d+:\d+",tc):
        h,m,s,f=map(int,tc.split(":"));return h*3600+m*60+s+f/fps
    raise ValueError("Unsupported MLT timecode: "+str(tc))

def import_mlt(path):
    tree=ET.parse(path);root=tree.getroot()
    if root.tag!="mlt":raise ValueError("Not an MLT project")
    profile=root.find("profile")
    fps=30.0
    if profile is not None:
        num=int(profile.get("frame_rate_num","30"));den=int(profile.get("frame_rate_den","1"))
        if num<=0 or den<=0:raise ValueError("Invalid project frame rate")
        fps=num/den
    producers={}
    for tag in ("producer","chain"):
        for node in root.findall(tag):
            ident=node.get("id")
            if ident:producers[ident]=props(node)
    issues=[];tracks=[]
    for playlist in root.findall("playlist"):
        p=props(playlist)
        if p.get("kdenlive:audio_track")=="1":continue
        if p.get("kdenlive:track_name","").lower().startswith("audio"):continue
        entries=[];cursor=0.0
        for node in playlist:
            if node.tag=="blank":
                cursor+=seconds(node.get("length","0"),fps);continue
            if node.tag!="entry":continue
            producer=node.get("producer","");meta=producers.get(producer,{})
            resource=meta.get("kdenlive:originalurl") or meta.get("resource")
            if not resource or resource in ("0","black") or resource.startswith("color:"):
                issues.append({"playlist":playlist.get("id"),"producer":producer,"reason":"unresolved_resource"});continue
            if meta.get("mlt_service") in ("timewarp",):
                issues.append({"playlist":playlist.get("id"),"producer":producer,"reason":"timewarp_unsupported"});continue
            begin=seconds(node.get("in","0"),fps);end=seconds(node.get("out"),fps)
            if end is None:
                issues.append({"playlist":playlist.get("id"),"producer":producer,"reason":"missing_out"});continue
            # MLT out is inclusive. Frame-accurate clip duration is (out-in)+one frame.
            duration=end-begin+1/fps
            if duration<=0:continue
            source=Path(resource)
            if not source.is_absolute():
                base=Path(root.get("root") or path.parent)
                if not base.is_absolute():base=(path.parent/base)
                source=base/source
            entries.append({"id":f"{playlist.get('id','playlist')}:{len(entries)}",
                            "source":str(source.resolve()),"source_in":round(begin,5),
                            "source_out":round(begin+duration,5),"start":round(cursor,5),
                            "duration":round(duration,5),"producer":producer})
            cursor+=duration
        if entries:tracks.append({"playlist":playlist.get("id"),"clips":entries})
    if not tracks:raise ValueError("No supported video playlist entries found")
    # Kdenlive routinely uses tractors even for basic edits. Report actual
    # compositing complexity rather than rejecting every normal project.
    for tractor in root.findall("tractor"):
        active=[t.get("producer") for t in tractor.findall("track") if t.get("hide")!="video"]
        transitions=tractor.findall("transition")
        filters=tractor.findall("filter")
        if transitions or filters or len(active)>2:
            issues.append({"reason":"complex_tractor_unresolved",
                           "tractor":tractor.get("id"),
                           "active_tracks":active,
                           "transitions":len(transitions),
                           "filters":len(filters)})
    for node in root.findall("playlist"):
        for entry in node.findall("entry"):
            if entry.get("producer") in {t.get("id") for t in root.findall("tractor")}:
                issues.append({"reason":"nested_tractor_entry","playlist":node.get("id")})
    return {"schema":"content-studio.kdenlive-observations.v1","fps":fps,
            "tracks":tracks,"issues":issues,"requires_human_review":True}

def main():
    p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path);a=p.parse_args()
    doc=import_mlt(a.input.resolve())
    encoded=json.dumps(doc,indent=2,ensure_ascii=False)+"\n"
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(encoded,encoding="utf-8")
    print(encoded,end="")
if __name__=="__main__":
    try:main()
    except (ValueError,ET.ParseError,OSError) as e:raise SystemExit(str(e))
