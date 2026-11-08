#!/usr/bin/env python3
"""Search, inspect and plan non-destructive placements for Content Studio assets."""
import argparse
import json
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / "assets"
CATALOG = ASSETS / "catalog.json"

def load():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    if data.get("schema") != "content-studio.asset-catalog.v1":
        raise ValueError("Unsupported asset catalog schema")
    ids = [asset["id"] for asset in data["assets"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate asset IDs")
    return data["assets"]

def search(assets, query="", category=None):
    words = query.lower().split()
    return [a for a in assets if (not category or a["category"] == category)
            and all(w in " ".join([a["id"],a["title"],*a.get("tags",[])]).lower() for w in words)]

def resolve_render(asset, fmt):
    value = asset.get("rendered_files", {}).get(fmt)
    if not value:
        raise ValueError(f"{asset['id']} has no registered {fmt} render; render and review it first")
    path = (ASSETS / value).resolve()
    if not path.is_relative_to(ASSETS.resolve()) or not path.is_file():
        raise ValueError("Registered asset is missing or outside the assets directory")
    return path

def placement(asset, at, fmt, timeline):
    if at < 0:
        raise ValueError("Placement time must be nonnegative")
    source = resolve_render(asset, fmt)
    if timeline is not None and at + asset["duration_seconds"] > timeline:
        raise ValueError("Asset would extend beyond video")
    return {"asset_id":asset["id"],"source":str(source),"start":at,
            "duration":asset["duration_seconds"],"track":"overlay",
            "placement":asset.get("placement","bottom-center"),
            "review_status":"pending","rendered":False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("command",choices=["list","show","plan"])
    parser.add_argument("--query",default="")
    parser.add_argument("--category")
    parser.add_argument("--id")
    parser.add_argument("--at",type=float,default=0)
    parser.add_argument("--format",default="webm")
    parser.add_argument("--video-duration",type=float)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    assets=load()
    if args.command=="list":
        result=search(assets,args.query,args.category)
    else:
        found=[a for a in assets if a["id"]==args.id]
        if not found: parser.error("Specify a known --id")
        result=found[0] if args.command=="show" else placement(found[0],args.at,args.format,args.video_duration)
    output=json.dumps(result,indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(output+"\n",encoding="utf-8")
    else: print(output)

if __name__=="__main__":
    main()
