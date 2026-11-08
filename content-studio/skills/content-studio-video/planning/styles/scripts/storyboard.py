#!/usr/bin/env python3
"""Create self-contained HTML storyboard for human review; no animation claims."""
import argparse
import html
import json
from pathlib import Path

def build(plan):
    scenes = plan.get("scenes", [])
    cards = []
    for i, scene in enumerate(scenes, 1):
        def esc(value):
            return html.escape(str(value), quote=True)
        techniques = " · ".join(scene.get("techniques", []))
        cards.append(f"""<article><div class="number">SCENE {i:02d} · {esc(scene['duration_seconds'])}s</div>
<h2>{esc(scene['id'])}</h2><div class="stage"><div class="shape"></div><div class="center">{esc(scene.get('visual_intent') or scene['label'])}</div></div>
<p><strong>{esc(scene['label'])}</strong> · {esc(scene['renderer'])}</p>
<p>{esc(techniques)}</p><p class="status">{esc(scene['status'])}</p>
<label><input type="checkbox"> Reviewed</label></article>""")
    return """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Content Studio — style storyboard</title>
<style>body{background:#0c111c;color:#edf3ff;font:16px system-ui;margin:0;padding:32px}header{max-width:1000px;margin:auto auto 32px}main{max-width:1000px;margin:auto;display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px}
article{background:#182234;border:1px solid #344158;border-radius:16px;padding:18px}.number,.status{color:#9dc8ff;font-size:13px;letter-spacing:.08em}.stage{height:190px;background:radial-gradient(circle at 25% 25%,#284e74,#111827 70%);border-radius:12px;display:grid;place-items:center;position:relative;overflow:hidden}.shape{position:absolute;width:110px;height:110px;border:3px solid #58d9cf;transform:rotate(25deg);opacity:.45}.center{z-index:1;max-width:75%;text-align:center;font-weight:700}p{line-height:1.5;color:#d0d9e7}label{display:block;margin-top:16px}</style>
<header><h1>Content Studio · Scene storyboard</h1><p>Static planning visualization only. These are not rendered animation frames. Check each scene after inspecting a real preview.</p></header><main>""" + "".join(cards) + "</main></html>"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("plan")
    p.add_argument("--output", required=True)
    args = p.parse_args()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(build(plan), encoding="utf-8")
    print(f"Wrote storyboard: {dest}")

if __name__ == "__main__":
    main()
