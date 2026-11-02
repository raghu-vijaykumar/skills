#!/usr/bin/env python3
"""Convert human editing feedback into validated timeline operations via local Ollama."""
import argparse
import json
import urllib.request
from pathlib import Path
from timeline import revise, validate, write_revision, render, refresh_review

SYSTEM="""You are a video timeline editing assistant. Output ONLY a JSON array of operations.
Allowed actions: remove {id}, trim {id,source_in,source_out}, move {id,index},
gain {id,db}. Use only IDs from the supplied timeline. Source times are absolute
seconds within original media. Do not invent new footage, music, captions or effects.
If the request cannot be represented safely, return [].
Never mark an edit as approved or publish anything."""

def propose(timeline, feedback, endpoint, model):
    clips=next(t["clips"] for t in timeline["tracks"] if t["kind"]=="video")
    payload={"model":model,"stream":False,"format":"json","messages":[
        {"role":"system","content":SYSTEM},
        {"role":"user","content":json.dumps({"feedback":feedback,"clips":clips,
            "required_response":{"operations":[{"action":"trim","id":"v0000","source_in":0,"source_out":2}]}})}]}
    req=urllib.request.Request(endpoint.rstrip("/")+"/api/chat",
        data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=180) as resp:
        data=json.load(resp)
    result=json.loads(data["message"]["content"])
    ops=result["operations"] if isinstance(result,dict) else result
    if not isinstance(ops,list): raise ValueError("Model did not return operations")
    if len(ops)>30: raise ValueError("Too many proposed operations")
    return ops

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--feedback",required=True)
    p.add_argument("--model",default="llama3.1")
    p.add_argument("--endpoint",default="http://127.0.0.1:11434")
    p.add_argument("--apply",action="store_true",help="Explicitly apply and render proposed edits")
    a=p.parse_args()
    out=a.output.resolve()
    timeline=json.loads((out/"timeline.json").read_text())
    ops=propose(timeline,a.feedback,a.endpoint,a.model)
    proposal={"based_on_revision":timeline["revision"],"feedback":a.feedback,"operations":ops}
    path=out/"proposed-edits.json"
    path.write_text(json.dumps(proposal,indent=2),encoding="utf-8")
    if not ops:
        print("No supported safe edits proposed; human clarification needed. "+str(path))
        return
    revised=revise(timeline,ops)
    validate(revised,Path(revised["source_root"]))
    if not a.apply:
        print("Review proposed edits before applying: "+str(path))
        return
    write_revision(revised,out)
    state_path=out/"review-state.json"
    if state_path.exists():
        state=json.loads(state_path.read_text())
        state.update(status="pending_review",approved=False,revision=revised["revision"])
        state_path.write_text(json.dumps(state,indent=2),encoding="utf-8")
    render(revised,out)
    refresh_review(revised,out)
    print("Revised video and review artifacts generated; human approval required.")

if __name__=="__main__": main()
