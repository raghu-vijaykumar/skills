#!/usr/bin/env python3
"""Explicitly confirm a reviewed Kdenlive comparison and log observations.

Confirmation is a user action, not inferred approval of a proposed edit.
"""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

def record(db,report,scope,project,reason):
    if report.get("schema")!="content-studio.kdenlive-comparison.v1":
        raise ValueError("Expected Kdenlive comparison report")
    if report.get("import_issues"):
        raise ValueError("Importer reported unresolved issues; inspect and resolve before confirming")
    observations=report.get("observations",[])
    if not observations:raise ValueError("No observations to confirm")
    encoded=json.dumps(report,sort_keys=True)
    digest=hashlib.sha256(encoded.encode()).hexdigest()
    db.execute("""CREATE TABLE IF NOT EXISTS confirmed_imports(
       fingerprint TEXT NOT NULL, project TEXT NOT NULL,
       PRIMARY KEY(fingerprint,project))""")
    if db.execute("SELECT 1 FROM confirmed_imports WHERE fingerprint=? AND project=?",(digest,project)).fetchone():
        return {"recorded":0,"duplicate":True}
    with db:
        db.execute("INSERT INTO confirmed_imports(fingerprint,project) VALUES(?,?)",(digest,project))
        for observation in observations:
            db.execute("""INSERT INTO events(project,scope,feature,decision,actor,reason,context_json)
                VALUES(?,?,?,?,?,?,?)""",(project,scope,"timeline","observed","human",reason,
                json.dumps({"observation":observation,"comparison_sha256":digest})))
    return {"recorded":len(observations),"duplicate":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db",type=Path,required=True);p.add_argument("--report",type=Path,required=True)
    p.add_argument("--scope",choices=["travel","cooking","daily"],required=True)
    p.add_argument("--project",required=True)
    p.add_argument("--confirm-reviewed",action="store_true",required=True,
                   help="Human has checked all source observations against actual edit")
    p.add_argument("--reason",required=True,help="Human-supplied reason; never guessed by the agent")
    a=p.parse_args()
    if not a.project.strip() or not a.reason.strip():p.error("Project and reason cannot be empty")
    if not a.db.is_file():p.error("Memory database not initialized")
    report=json.loads(a.report.read_text(encoding="utf-8"))
    db=sqlite3.connect(a.db)
    print(json.dumps(record(db,report,a.scope,a.project,a.reason)))
if __name__=="__main__":
    try:main()
    except (ValueError,sqlite3.Error,OSError) as e:raise SystemExit(str(e))
