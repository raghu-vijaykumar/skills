#!/usr/bin/env python3
"""Minimal durable DAG runner: resume, retries, stale-input invalidation, human gates."""
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path
from preflight import approved

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
    steps=config.get("steps")
    if steps is None:
        video=Path(config["video"]).expanduser().resolve()
        if not video.is_file(): raise FileNotFoundError(video)
        script=Path(__file__).resolve().parents[2]/"content-studio-understand/scripts/understand.py"
        voiceover=config.get("voiceover",{})
        interval=float(voiceover.get("frame_interval_seconds",5))
        columns=int(voiceover.get("grid_columns",5))
        rows=int(voiceover.get("grid_rows",4))
        width=int(voiceover.get("frame_width",480))
        command=[sys.executable,str(script),"--video",str(video),"--out",str(root/".content-studio/understanding"),"--interval",str(interval),"--grid-cols",str(columns),"--grid-rows",str(rows),"--frame-width",str(width)]
        context_file=voiceover.get("context_file")
        if context_file:
            context_path=(root/context_file).resolve()
            if not context_path.is_relative_to(root):raise ValueError("context_file escapes workspace")
            if not context_path.is_file():raise FileNotFoundError(context_path)
            command += ["--context",str(context_path)]
        if not voiceover.get("contact_sheets",True):command.append("--no-grid")
        steps=[
            {"id":"extract_voiceover_evidence","plan_step":"S03","command":command,"outputs":[".content-studio/understanding/evidence.json"],"retries":1},
            {"id":"review_voiceover_script","depends_on":["extract_voiceover_evidence"],"approval_required":True},
            {"id":"review_final_video","depends_on":["review_voiceover_script"],"approval_required":True}
        ] if voiceover.get("enabled",False) else [{"id":"review_final_video","approval_required":True}]
    names=[s["id"] for s in steps]
    if len(names)!=len(set(names)):raise ValueError("duplicate step id")
    if a.status:
        for n in names:print(n,state["steps"].get(n,{}).get("status","pending"))
        return
    # No configured production command runs against an unreviewed or changed plan.
    plan, plan_approval, checklist = approved(root)
    planned_ids = {step["id"] for step in plan["steps"]}
    plan_order = {step["id"]: index for index, step in enumerate(plan["steps"])}
    for step in steps:
        if step.get("command") and step.get("plan_step") not in planned_ids:
            raise ValueError(f"workflow step {step['id']} needs a plan_step from the approved checklist")
    if a.reset_step:
        invalid={a.reset_step}
        for s in steps:
            if any(d in invalid for d in s.get("depends_on",[])):invalid.add(s["id"])
        for n in invalid:state["steps"].pop(n,None)
        save(state_path,state)
    for step in steps:
        name=step["id"];deps=step.get("depends_on",[])
        if step.get("command"):
            for index, prior in enumerate(checklist["items"][:plan_order[step["plan_step"]]]):
                valid = (prior.get("status") == "done" and bool(prior.get("evidence"))) or (
                    prior.get("status") == "not_applicable" and not plan["steps"][index].get("required") and bool(prior.get("reason")))
                if not valid:
                    raise ValueError(f"Complete approved plan step {prior['id']} before running {name}")
        if any(d not in names for d in deps):raise ValueError("unknown dependency for "+name)
        if any(state["steps"].get(d,{}).get("status")!="done" for d in deps):
            print("WAIT dependencies:",name);save(state_path,state);return
        inputs=[]
        for f in step.get("inputs",[]):
            path=(root/f).resolve()
            if not path.is_relative_to(root):raise ValueError("input escapes workspace")
            if not path.is_file():raise FileNotFoundError(path)
            inputs.append([f,path.stat().st_size,path.stat().st_mtime_ns])
        fingerprint=digest([step,inputs,config,plan_approval["plan_sha256"],[(str(config["video"]),Path(config["video"]).expanduser().resolve().stat().st_size,Path(config["video"]).expanduser().resolve().stat().st_mtime_ns)] if config.get("video") else [],[state["steps"][d]["fingerprint"] for d in deps]])
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
