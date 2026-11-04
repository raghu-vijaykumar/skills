#!/usr/bin/env python3
"""Private SQLite editing decisions and explicit preference retrieval; stdlib only."""
import argparse
import json
import sqlite3
from pathlib import Path

SCOPES = {"global", "travel", "cooking", "daily"}
DECISIONS = {"approved", "rejected", "changed", "observed"}
ACTORS = {"human", "agent"}

def valid_scope(scope):
    if scope not in SCOPES and not (scope.startswith("project:") and len(scope)>8):
        raise ValueError("Scope must be global, travel, cooking, daily, or project:<id>")
    return scope

def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("""CREATE TABLE IF NOT EXISTS events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      project TEXT NOT NULL DEFAULT '',
      scope TEXT NOT NULL,
      feature TEXT NOT NULL,
      decision TEXT NOT NULL,
      actor TEXT NOT NULL,
      reason TEXT NOT NULL DEFAULT '',
      context_json TEXT NOT NULL DEFAULT '{}'
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS preferences (
      scope TEXT NOT NULL,
      key TEXT NOT NULL,
      value_json TEXT NOT NULL,
      source TEXT NOT NULL DEFAULT 'explicit',
      updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (scope, key)
    )""")
    db.commit()
    return db

def retrieve(db, scope, project):
    layers=["global"]
    if scope!="global": layers.append(scope)
    if project: layers.append("project:"+project)
    effective={}
    for layer in layers:
        for row in db.execute("SELECT * FROM preferences WHERE scope=? ORDER BY key",(layer,)):
            effective[row["key"]]={"value":json.loads(row["value_json"]),"scope":layer,"source":row["source"]}
    return {"scope":scope,"project":project or None,"preferences":effective}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db",required=True,help="Private local SQLite path, outside Git")
    sub=p.add_subparsers(dest="action",required=True)
    sub.add_parser("init")
    setp=sub.add_parser("set");setp.add_argument("--key",required=True);setp.add_argument("--value",required=True);setp.add_argument("--scope",default="global")
    forget=sub.add_parser("forget");forget.add_argument("--key",required=True);forget.add_argument("--scope",default="global")
    record=sub.add_parser("record");record.add_argument("--feature",required=True);record.add_argument("--decision",choices=sorted(DECISIONS),required=True)
    record.add_argument("--scope",default="global");record.add_argument("--project",default="")
    record.add_argument("--actor",choices=sorted(ACTORS),default="human");record.add_argument("--reason",default="");record.add_argument("--context",default="{}")
    ret=sub.add_parser("retrieve");ret.add_argument("--scope",default="global");ret.add_argument("--project",default="")
    ev=sub.add_parser("events");ev.add_argument("--scope");ev.add_argument("--project");ev.add_argument("--limit",type=int,default=100)
    purge=sub.add_parser("purge-events");purge.add_argument("--project");purge.add_argument("--all",action="store_true")
    args=p.parse_args()
    db=connect(Path(args.db).expanduser().resolve())
    if args.action=="init":print("Ready:",args.db)
    elif args.action=="set":
        valid_scope(args.scope)
        if not args.key.strip():raise ValueError("Empty preference key")
        try:value=json.loads(args.value)
        except json.JSONDecodeError:value=args.value
        db.execute("INSERT INTO preferences(scope,key,value_json) VALUES(?,?,?) ON CONFLICT(scope,key) DO UPDATE SET value_json=excluded.value_json, source='explicit', updated_at=CURRENT_TIMESTAMP",(args.scope,args.key,json.dumps(value)))
        db.commit();print(json.dumps(retrieve(db,args.scope,"")))
    elif args.action=="forget":
        valid_scope(args.scope)
        cur=db.execute("DELETE FROM preferences WHERE scope=? AND key=?",(args.scope,args.key));db.commit()
        print(json.dumps({"deleted":cur.rowcount}))
    elif args.action=="record":
        valid_scope(args.scope)
        context=json.loads(args.context)
        if not isinstance(context,dict):raise ValueError("Context must be a JSON object")
        db.execute("INSERT INTO events(project,scope,feature,decision,actor,reason,context_json) VALUES(?,?,?,?,?,?,?)",
                   (args.project,args.scope,args.feature,args.decision,args.actor,args.reason,json.dumps(context)))
        db.commit();print(json.dumps({"event_id":db.execute("SELECT last_insert_rowid()").fetchone()[0]}))
    elif args.action=="retrieve":
        valid_scope(args.scope)
        print(json.dumps(retrieve(db,args.scope,args.project),indent=2,ensure_ascii=False))
    elif args.action=="events":
        if args.scope:valid_scope(args.scope)
        if args.limit<1 or args.limit>10000:raise ValueError("Limit must be between 1 and 10000")
        sql="SELECT * FROM events WHERE 1=1";params=[]
        if args.scope:sql+=" AND scope=?";params.append(args.scope)
        if args.project is not None:sql+=" AND project=?";params.append(args.project)
        sql+=" ORDER BY id DESC LIMIT ?";params.append(args.limit)
        rows=[{**dict(r),"context":json.loads(r["context_json"])} for r in db.execute(sql,params)]
        for r in rows:del r["context_json"]
        print(json.dumps(rows,indent=2,ensure_ascii=False))
    elif args.action=="purge-events":
        if not args.all and not args.project:raise ValueError("Supply --project or --all")
        if args.all and args.project:raise ValueError("Choose --project or --all, not both")
        cur=db.execute("DELETE FROM events" if args.all else "DELETE FROM events WHERE project=?",() if args.all else (args.project,))
        db.commit();print(json.dumps({"deleted":cur.rowcount}))
if __name__=="__main__":
    try:main()
    except (ValueError,sqlite3.Error) as e:raise SystemExit(str(e))
