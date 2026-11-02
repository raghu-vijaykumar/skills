#!/usr/bin/env python3
"""Review gate for autonomous video edits. Approval is always explicit."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--approve",action="store_true")
    group.add_argument("--request-changes",metavar="FEEDBACK")
    p.add_argument("--reviewer",required=True)
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
    print(json.dumps(state,indent=2))

if __name__=="__main__": main()
