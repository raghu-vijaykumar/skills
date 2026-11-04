#!/usr/bin/env python3
"""Compare Content Studio timeline revisions by source identity and source ranges.

This is a deterministic observation report, not an inference of editing intent.
Kdenlive/MLT project import is not supported by this script.
"""
import argparse
import json
from pathlib import Path

def clips(doc):
    if doc.get("schema") != "content-studio.timeline.v1":
        raise ValueError("Expected content-studio.timeline.v1")
    tracks=[t for t in doc.get("tracks",[]) if t.get("kind")=="video"]
    if len(tracks)!=1:raise ValueError("Expected exactly one video track")
    result=tracks[0].get("clips",[])
    for c in result:
        for field in ("id","source","source_in","source_out","start"):
            if field not in c:raise ValueError("Missing clip field: "+field)
    return result

def compare(before,after,tolerance=0.05):
    old=clips(before);new=clips(after)
    old_by={c["id"]:c for c in old};new_by={c["id"]:c for c in new}
    if len(old_by)!=len(old) or len(new_by)!=len(new):
        raise ValueError("Duplicate clip IDs")
    changes=[]
    for index,c in enumerate(old):
        ident=c["id"]
        if ident not in new_by:
            changes.append({"type":"removed","clip_id":ident,"source":c["source"],
                            "source_in":c["source_in"],"source_out":c["source_out"]})
            continue
        n=new_by[ident]
        if c["source"]!=n["source"]:
            changes.append({"type":"source_replaced","clip_id":ident,"before":c["source"],"after":n["source"]})
        if abs(float(c["source_in"])-float(n["source_in"]))>tolerance or abs(float(c["source_out"])-float(n["source_out"]))>tolerance:
            changes.append({"type":"trimmed","clip_id":ident,"source":n["source"],
                            "before":[c["source_in"],c["source_out"]],"after":[n["source_in"],n["source_out"]]})
        if c.get("audio_gain_db",0)!=n.get("audio_gain_db",0):
            changes.append({"type":"gain_changed","clip_id":ident,"before":c.get("audio_gain_db",0),"after":n.get("audio_gain_db",0)})
    for c in new:
        if c["id"] not in old_by:
            changes.append({"type":"added","clip_id":c["id"],"source":c["source"],
                            "source_in":c["source_in"],"source_out":c["source_out"]})
    common_old=[c["id"] for c in old if c["id"] in new_by]
    common_new=[c["id"] for c in new if c["id"] in old_by]
    if common_old!=common_new:
        changes.append({"type":"reordered","before":common_old,"after":common_new})
    return {"schema":"content-studio.timeline-diff.v1",
            "before_revision":before.get("revision"),"after_revision":after.get("revision"),
            "changes":changes,"requires_human_interpretation":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--before",type=Path,required=True)
    p.add_argument("--after",type=Path,required=True)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    result=compare(json.loads(a.before.read_text(encoding="utf-8")),
                   json.loads(a.after.read_text(encoding="utf-8")))
    encoded=json.dumps(result,indent=2,ensure_ascii=False)+"\n"
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(encoded,encoding="utf-8")
    print(encoded,end="")
if __name__=="__main__":
    try:main()
    except (ValueError,OSError) as exc:raise SystemExit(str(exc))
