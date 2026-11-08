#!/usr/bin/env python3
"""Local-only meme catalogue; stdlib SQLite and no network requests."""
import argparse, hashlib, json, shutil, sqlite3
from pathlib import Path

EXT={".mp4":"video",".mov":"video",".webm":"video",".gif":"gif",".png":"image",".jpg":"image",".jpeg":"image",".webp":"image",".wav":"audio",".mp3":"audio",".m4a":"audio"}
RIGHTS={"owned","licensed","permission","unknown"}

def checksum(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def connect(root):
    root.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(root/"catalogue.sqlite")
    db.row_factory=sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS memes(
      id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL,
      relative_path TEXT NOT NULL, sha256 TEXT UNIQUE NOT NULL,
      tags TEXT NOT NULL, language TEXT NOT NULL, license TEXT NOT NULL,
      source TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    db.commit()
    return db

def add(db,root,args):
    src=Path(args.file).expanduser().resolve()
    if not src.is_file():raise ValueError("File not found")
    kind=EXT.get(src.suffix.lower())
    if not kind:raise ValueError("Unsupported media type")
    if args.license not in RIGHTS:raise ValueError("Invalid rights status")
    digest=checksum(src);existing=db.execute("SELECT id FROM memes WHERE sha256=?",(digest,)).fetchone()
    if existing:
        print("Already imported:",existing["id"]);return
    ident="meme-"+digest[:16]
    relative=Path("media")/kind/(ident+src.suffix.lower())
    dest=root/relative;dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dest)
    try:
        db.execute("INSERT INTO memes(id,name,kind,relative_path,sha256,tags,language,license,source) VALUES(?,?,?,?,?,?,?,?,?)",
                   (ident,args.name,kind,relative.as_posix(),digest,args.tags,args.language,args.license,args.source))
        db.commit()
    except Exception:
        dest.unlink(missing_ok=True);raise
    print("Imported:",ident)

def main():
    p=argparse.ArgumentParser();p.add_argument("--library",required=True,help="Local media directory, outside Git")
    sub=p.add_subparsers(dest="action",required=True)
    sub.add_parser("init");sub.add_parser("list")
    a=sub.add_parser("add");a.add_argument("--file",required=True);a.add_argument("--name",required=True)
    a.add_argument("--tags",default="");a.add_argument("--language",default="und")
    a.add_argument("--license",choices=sorted(RIGHTS),default="unknown");a.add_argument("--source",default="")
    s=sub.add_parser("search");s.add_argument("--query",required=True);s.add_argument("--category",choices=["travel","cooking","daily"])
    args=p.parse_args();root=Path(args.library).expanduser().resolve();db=connect(root)
    if args.action=="add":add(db,root,args);return
    if args.action=="init":print("Catalogue ready:",root/"catalogue.sqlite");return
    rows=db.execute("SELECT * FROM memes ORDER BY created_at DESC,id").fetchall()
    if args.action=="search":
        q=args.query.casefold()
        rows=[r for r in rows if q in (r["name"]+" "+r["tags"]+" "+r["language"]).casefold()]
        if args.category:rows=[r for r in rows if args.category in r["tags"].casefold().split(",")]
    print(json.dumps([{**dict(r),"publish_eligible":r["license"]!="unknown"} for r in rows],indent=2,ensure_ascii=False))
if __name__=="__main__":
    try:main()
    except (ValueError,sqlite3.Error) as e:raise SystemExit(str(e))
