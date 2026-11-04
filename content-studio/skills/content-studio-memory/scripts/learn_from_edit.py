#!/usr/bin/env python3
"""One-command Kdenlive observation, comparison and review bundle.

No silent learning: a separate explicit confirmation is required to record events.
"""
import argparse
import html
import json
from pathlib import Path
from kdenlive_import import import_mlt
from compare_kdenlive import compare

def build(proposed_path,kdenlive_path,out):
    out=out.resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError("Output folder must be empty to avoid overwriting review evidence")
    proposed=json.loads(proposed_path.read_text(encoding="utf-8"))
    edited=import_mlt(kdenlive_path)
    report=compare(proposed,edited)
    out.mkdir(parents=True,exist_ok=True)
    (out/"kdenlive-observations.json").write_text(json.dumps(edited,indent=2)+"\n",encoding="utf-8")
    (out/"comparison.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    rows="".join("<tr><td>"+html.escape(str(o.get("type","")))+"</td><td><pre>"+
                 html.escape(json.dumps(o,indent=2,ensure_ascii=False))+"</pre></td></tr>"
                 for o in report["observations"])
    issues="".join("<li>"+html.escape(json.dumps(i,ensure_ascii=False))+"</li>" for i in edited["issues"])
    page=("<!doctype html><meta charset='utf-8'><title>Editing memory review</title>"
          "<style>body{font:16px system-ui;max-width:1000px;margin:2rem auto;padding:0 1rem}"
          "table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #aaa;padding:12px;text-align:left}"
          "pre{white-space:pre-wrap;overflow-wrap:anywhere}</style>"
          "<h1>Kdenlive editing observations</h1>"
          "<p>These are source-range observations, not conclusions about your intent. "
          "Check them against the actual Kdenlive project before confirming.</p>"
          "<h2>Importer warnings</h2><ul>"+(issues or "<li>None reported</li>")+"</ul>"
          "<h2>Proposed differences</h2><table><tr><th>Type</th><th>Evidence</th></tr>"+
          rows+"</table><p>Confirmation requires an explicit human reason and "
          "the separate confirm_diff.py command. No preferences were changed.</p>")
    (out/"review.html").write_text(page,encoding="utf-8")
    return {"review":str(out/"review.html"),"comparison":str(out/"comparison.json"),
            "observations":len(report["observations"]),"warnings":len(edited["issues"])}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--proposed",type=Path,required=True)
    p.add_argument("--kdenlive",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(build(a.proposed.resolve(),a.kdenlive.resolve(),a.output),indent=2))
if __name__=="__main__":
    try:main()
    except (ValueError,OSError) as e:raise SystemExit(str(e))
