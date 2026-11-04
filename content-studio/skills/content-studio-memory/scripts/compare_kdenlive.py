#!/usr/bin/env python3
"""Compare source ranges of a Content Studio proposal with a Kdenlive MLT import.

Reports observations; cannot infer motives or guarantee rendered MLT track visibility.
"""
import argparse
import json
from pathlib import Path

def source_key(path):
    return Path(path.replace("\\","/")).name.casefold()

def flatten(doc):
    if doc.get("schema")=="content-studio.timeline.v1":
        tracks=[t for t in doc["tracks"] if t.get("kind")=="video"]
        return [c for t in tracks for c in t["clips"]]
    if doc.get("schema")=="content-studio.kdenlive-observations.v1":
        return [c for t in doc["tracks"] for c in t["clips"]]
    raise ValueError("Unsupported timeline schema")

def overlap(a,b):
    return max(0.0,min(float(a["source_out"]),float(b["source_out"]))-
               max(float(a["source_in"]),float(b["source_in"])))

def compare(proposed,edited):
    before=flatten(proposed);after=flatten(edited)
    # Filenames alone are ambiguous when two source directories contain same names.
    keys={}
    for c in before:
        k=source_key(c["source"]);keys.setdefault(k,set()).add(c["source"])
    ambiguous={k for k,v in keys.items() if len(v)>1}
    observations=[]
    for c in before:
        key=source_key(c["source"])
        if key in ambiguous:
            observations.append({"type":"ambiguous_source","source":c["source"],"reason":"duplicate_basename"})
            continue
        candidates=[x for x in after if source_key(x["source"])==key]
        original=float(c["source_out"])-float(c["source_in"])
        # Union of intersections avoids counting duplicate source segments twice.
        ranges=[]
        for x in candidates:
            lo=max(float(c["source_in"]),float(x["source_in"]))
            hi=min(float(c["source_out"]),float(x["source_out"]))
            if hi>lo:ranges.append((lo,hi))
        ranges.sort();merged=[]
        for lo,hi in ranges:
            if merged and lo<=merged[-1][1]:merged[-1]=(merged[-1][0],max(hi,merged[-1][1]))
            else:merged.append((lo,hi))
        retained=sum(hi-lo for lo,hi in merged)
        if original>0 and retained<original-0.1:
            observations.append({"type":"source_range_reduced","source":c["source"],
                                 "source_in":c["source_in"],"source_out":c["source_out"],
                                 "retained_seconds":round(retained,3),
                                 "original_seconds":round(original,3),
                                 "retained_ratio":round(retained/original,3)})
    return {"schema":"content-studio.kdenlive-comparison.v1",
            "observations":observations,
            "limitations":["Filename matching can be ambiguous across directories",
                           "Nested tractors and compositing may alter visible output",
                           "A missing source range does not establish why it was removed"],
            "import_issues":edited.get("issues",[]),
            "requires_human_review":True}

def main():
    p=argparse.ArgumentParser();p.add_argument("--proposed",type=Path,required=True)
    p.add_argument("--edited",type=Path,required=True);p.add_argument("--output",type=Path)
    a=p.parse_args()
    doc=compare(json.loads(a.proposed.read_text(encoding="utf-8")),
                json.loads(a.edited.read_text(encoding="utf-8")))
    encoded=json.dumps(doc,indent=2,ensure_ascii=False)+"\n"
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(encoded,encoding="utf-8")
    print(encoded,end="")
if __name__=="__main__":
    try:main()
    except (ValueError,OSError) as e:raise SystemExit(str(e))
