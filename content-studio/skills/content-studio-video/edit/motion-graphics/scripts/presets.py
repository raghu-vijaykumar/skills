#!/usr/bin/env python3
"""Select and validate motion-graphics presets; no rendering or unsupported cue invention."""
import argparse,json
from pathlib import Path
DATA=Path(__file__).resolve().parents[1]/"presets"/"presets.json"
def load():return json.loads(DATA.read_text(encoding="utf-8"))
def resolve(category,style=None):
    data=load()
    if category not in data["default_by_category"]:raise ValueError("Unknown category: "+category)
    key=style or data["default_by_category"][category]
    if key not in data["presets"]:raise ValueError("Unknown preset: "+key)
    preset=data["presets"][key]
    if preset["category"]!=category:raise ValueError("Preset category mismatch")
    return {"id":key,**preset}
def validate_cues(preset,cues):
    issues=[]
    for i,c in enumerate(cues):
        if c.get("type") not in preset["types"]:issues.append(f"cue {i}: unsupported type {c.get('type')}")
        if not isinstance(c.get("at"),(int,float)) or c["at"]<0:issues.append(f"cue {i}: invalid timestamp")
        if not c.get("evidence") and c.get("type") not in ("title","chapter","cta"):issues.append(f"cue {i}: evidence required")
    return issues
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--category",choices=["travel","cooking","daily"],required=True)
    p.add_argument("--preset",help="Preset id, defaults to category default")
    p.add_argument("--cues",help="Optional JSON array of proposed cues")
    p.add_argument("--out",help="Write resolved preset JSON to file")
    a=p.parse_args();preset=resolve(a.category,a.preset)
    if a.cues:
        cues=json.loads(Path(a.cues).read_text(encoding="utf-8"))
        if not isinstance(cues,list):p.error("Cues must be a JSON array")
        issues=validate_cues(preset,cues)
        if issues:p.error("; ".join(issues))
    result=json.dumps(preset,indent=2,ensure_ascii=False)
    if a.out:Path(a.out).write_text(result+"\n",encoding="utf-8")
    else:print(result)
if __name__=="__main__":main()
