#!/usr/bin/env python3
"""Generate explainable preference candidates from repeated human feedback.

No automatic promotion: candidates require explicit human confirmation via memory.py set.
"""
import argparse
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

def candidates(db,minimum=3):
    evidence=defaultdict(list)
    for row in db.execute("""SELECT id,project,scope,feature,decision,reason,context_json
                             FROM events WHERE actor='human' AND reason!='' ORDER BY id"""):
        ident,project,scope,feature,decision,reason,context=row
        if decision not in ("changed","rejected"):continue
        # Group only by exact, explicit human reason. Never invent a causal label.
        key=(scope,feature,reason.strip().casefold())
        evidence[key].append({"event_id":ident,"project":project,"decision":decision})
    result=[]
    for (scope,feature,reason),events in sorted(evidence.items()):
        projects={e["project"] for e in events if e["project"]}
        if len(events)<minimum or len(projects)<2:continue
        result.append({"scope":scope,"feature":feature,"human_reason":reason,
                       "support_count":len(events),"distinct_projects":len(projects),
                       "evidence":events[-20:],"status":"candidate_requires_confirmation",
                       "suggestion":f"Consider a {scope} preference for {feature}: {reason}"})
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument("--db",type=Path,required=True)
    p.add_argument("--minimum",type=int,default=3);a=p.parse_args()
    if a.minimum<2:raise SystemExit("--minimum must be >= 2")
    if not a.db.is_file():raise SystemExit("Memory database does not exist")
    db=sqlite3.connect(a.db)
    print(json.dumps(candidates(db,a.minimum),indent=2,ensure_ascii=False))
if __name__=="__main__":main()
