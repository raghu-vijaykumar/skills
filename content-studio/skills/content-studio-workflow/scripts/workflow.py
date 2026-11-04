#!/usr/bin/env python3
"""Minimal durable DAG runner: resume, retries, stale-input invalidation, human gates."""
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(".tmp");tmp.write_text(json.dumps(obj,indent=2),encoding="utf-8");os.replace(tmp,path)

def main():
    p=argparse.ArgumentParser();p.add_argument("--prompt",required=True);p.add_argument("--resume",action="store_true");p.add_argument("--status",action="store_true");p.add_argument("--reset-step")
    a=p.parse_args(); config=json.loads(Path(a.prompt).read_text(encoding="utf-8"))
    root=Path(config["workspace"]).expanduser().resolve();root.mkdir(parents=True,exist_ok=True)
    state_path=root/".content-studio/workflow/state.json"
    state=json.loads(state_path.read_text()) if state_path.exists() else {"steps":{}}
    steps=config["steps"];names=[s["id"] for s in steps]
    if len(names)!=len(set(names)):raise ValueError("duplicate step id")
    if a.status:
        for n in names:print(n,state["steps"].get(n,{}).get("status","pending"))
        return
    if a.reset_step:
        invalid={a.reset_step}
        for s in steps:
            if any(d in invalid for d in s.get("depends_on",[])):invalid.add(s["id"])
        for n in invalid:state["steps"].pop(n,None)
        save(state_path,state)
    for step in steps:
        name=step["id"];deps=step.get("depends_on",[])
        if any(d not in names for d in deps):raise ValueError("unknown dependency for "+name)
        if any(state["steps"].get(d,{}).get("status")!="done" for d in deps):
            print("WAIT dependencies:",name);save(state_path,state);return
        inputs=[]
        for f in step.get("inputs",[]):
            path=(root/f).resolve()
            if not path.is_relative_to(root):raise ValueError("input escapes workspace")
            if not path.is_file():raise FileNotFoundError(path)
            inputs.append([f,path.stat().st_size,path.stat().st_mtime_ns])
        fingerprint=digest([step,inputs,[state["steps"][d]["fingerprint"] for d in deps]])
        old=state["steps"].get(name,{})
        outputs=[(root/f).resolve() for f in step.get("outputs",[])]
        if any(not x.is_relative_to(root) for x in outputs):raise ValueError("output escapes workspace")
        if old.get("status")=="done" and old.get("fingerprint")==fingerprint and all(x.exists() for x in outputs):
            print("SKIP",name);continue
        if step.get("approval_required"):
            approval=root/".content-studio/workflow/approvals"/(name+".json")
            record=json.loads(approval.read_text()) if approval.exists() else {}
            if record.get("approved") is not True or record.get("fingerprint")!=fingerprint:
                state["steps"][name]={"status":"awaiting_approval","fingerprint":fingerprint}
                save(state_path,state);print("REVIEW",name,"expected fingerprint",fingerprint);return
        cmd=step.get("command")
        if not cmd:
            state["steps"][name]={"status":"done","fingerprint":fingerprint}
            save(state_path,state);continue
        if not isinstance(cmd,list) or not cmd or not all(isinstance(x,str) for x in cmd):raise ValueError("command must be argv array")
        retries=max(0,min(int(step.get("retries",1)),5))
        for attempt in range(retries+1):
            state["steps"][name]={"status":"running","fingerprint":fingerprint,"attempt":attempt+1}
            save(state_path,state)
            result=subprocess.run(cmd,cwd=root,check=False)
            if result.returncode==0 and all(x.exists() for x in outputs):break
            if attempt<retries:time.sleep(min(2**attempt,8))
        else:
            state["steps"][name]={"status":"failed","fingerprint":fingerprint,"returncode":result.returncode}
            save(state_path,state);raise SystemExit("FAILED "+name)
        state["steps"][name]={"status":"done","fingerprint":fingerprint}
        save(state_path,state);print("DONE",name)
    print("Workflow complete; publishing remains a separate human-authorized action.")
if __name__=="__main__":main()
