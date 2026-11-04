#!/usr/bin/env python3
"""Review gate for autonomous video edits. Approval is always explicit."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--approve",action="store_true")
    group.add_argument("--request-changes",metavar="FEEDBACK")
    p.add_argument("--reviewer",required=True)
    p.add_argument("--memory-db",type=Path,help="Optional local editing memory database")
    p.add_argument("--category",choices=["travel","cooking","daily"],default="travel")
    p.add_argument("--project",default="")
    args=p.parse_args()
    folder=args.output.resolve()
    state_path=folder/"review-state.json"
    if not state_path.is_file() or not (folder/"rough-cut.mp4").is_file():
        p.error("No completed rough cut and review state in output folder")
    state=json.loads(state_path.read_text(encoding="utf-8"))
    record={"reviewer":args.reviewer,"at":datetime.now(timezone.utc).isoformat()}
    if args.approve:
        state.update(status="approved",approved=True)
        record["decision"]="approved"
    else:
        feedback=args.request_changes.strip()
        if not feedback: p.error("Feedback cannot be empty")
        state.update(status="changes_requested",approved=False)
        record.update(decision="changes_requested",feedback=feedback)
    state.setdefault("feedback",[]).append(record)
    state_path.write_text(json.dumps(state,indent=2),encoding="utf-8")
    if args.memory_db:
        try:
            import importlib.util
            module_path=Path(__file__).resolve().parents[2]/"content-studio-memory"/"scripts"/"memory.py"
            spec=importlib.util.spec_from_file_location("content_studio_memory",module_path)
            module=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            db=module.connect(args.memory_db.expanduser().resolve())
            db.execute("INSERT INTO events(project,scope,feature,decision,actor,reason,context_json) VALUES(?,?,?,?,?,?,?)",
                (args.project,args.category,"autocut","approved" if args.approve else "changed",
                 "human","" if args.approve else args.request_changes.strip(),
                 json.dumps({"reviewer":args.reviewer,"review_output":str(folder),"revision":state.get("revision")})))
            db.commit()
        except Exception as exc:
            print("Warning: review saved, but memory recording failed: "+str(exc),file=sys.stderr)
    print(json.dumps(state,indent=2))

if __name__=="__main__": main()
