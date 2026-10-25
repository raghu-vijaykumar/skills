#!/usr/bin/env python3
"""Read YouTube Studio rows and export cookies over the DevTools protocol."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request


def http_json(port: int, path: str) -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=15) as resp:
        return json.load(resp)


def open_target(port: int, url: str) -> dict:
    quoted = urllib.parse.quote(url, safe="")
    request = urllib.request.Request(f"http://127.0.0.1:{port}/json/new?{quoted}", method="PUT")
    with urllib.request.urlopen(request, timeout=20) as resp:
        return json.load(resp)


class Session:
    def __init__(self, ws_url: str):
        import websocket

        self.ws = websocket.create_connection(ws_url, timeout=60)
        self.counter = 0

    def call(self, method: str, **params):
        self.counter += 1
        self.ws.send(json.dumps({"id": self.counter, "method": method, "params": params}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == self.counter:
                return message

    def eval(self, expression: str):
        result = self.call("Runtime.evaluate", expression=expression, returnByValue=True)
        return result.get("result", {}).get("result", {}).get("value")

    def close(self) -> None:
        self.ws.close()


ROW_SCRIPT = r"""
(() => {
  const rows = [...document.querySelectorAll('ytcp-video-row, tr, [role="row"]')];
  const seen = new Map();
  for (const row of rows) {
    const link = row.querySelector('a[href*="/video/"]');
    if (!link) continue;
    const match = link.getAttribute('href').match(/\/video\/([A-Za-z0-9_-]{11})/);
    if (!match || seen.has(match[1])) continue;
    const text = (row.innerText || '').replace(/\s+/g, ' ').trim();
    const duration = text.match(/(\d{1,2}:\d{2}(?::\d{2})?)/);
    const visibility = ['Scheduled', 'Private', 'Public', 'Unlisted', 'Draft'].find(v => text.includes(v)) || '';
    const title = text.slice(duration ? duration.index + duration[1].length : 0, 160).trim();
    seen.set(match[1], { id: match[1], duration: duration ? duration[1] : '', visibility, title });
  }
  return JSON.stringify({
    title: document.title,
    signedIn: !location.href.includes('accounts.google.com'),
    rows: [...seen.values()]
  });
})()
"""


def collect_rows(port: int, channel_id: str) -> list[dict]:
    rows: dict[str, dict] = {}
    for tab in ("videos/upload", "videos/short"):
        url = f"https://studio.youtube.com/channel/{channel_id}/{tab}"
        target = open_target(port, url)
        session = Session(target["webSocketDebuggerUrl"])
        session.call("Runtime.enable")
        deadline = time.time() + 60
        while time.time() < deadline:
            if session.eval("document.readyState") == "complete":
                break
            time.sleep(1)
        time.sleep(4)
        payload = session.eval(ROW_SCRIPT)
        session.close()
        if not payload:
            print(f"WARN no DOM for {tab}", file=sys.stderr)
            continue
        data = json.loads(payload)
        if not data.get("signedIn"):
            raise SystemExit("Not signed in to YouTube Studio in that browser profile.")
        for row in data.get("rows", []):
            row["tab"] = "shorts" if tab.endswith("short") else "long"
            rows.setdefault(row["id"], row)
    return list(rows.values())


def export_cookies(port: int, out_path: str) -> int:
    version = http_json(port, "/json/version")
    session = Session(version["webSocketDebuggerUrl"])
    response = session.call("Storage.getCookies")
    session.close()
    if "error" in response:
        print("cookie error: " + json.dumps(response["error"]), file=sys.stderr)
        return 1
    keep = [c for c in response["result"]["cookies"]
            if any(d in (c.get("domain") or "") for d in ("youtube.com", "google.com"))]
    lines = ["# Netscape HTTP Cookie File", "# exported over the DevTools protocol", ""]
    for cookie in keep:
        value = cookie.get("value", "")
        if "\t" in value or "\n" in value:
            continue
        domain = cookie["domain"]
        expires = int(cookie.get("expires") or 0)
        lines.append("\t".join([
            domain,
            "TRUE" if domain.startswith(".") else "FALSE",
            cookie.get("path", "/"),
            "TRUE" if cookie.get("secure") else "FALSE",
            str(expires) if expires > 0 else "0",
            cookie["name"],
            value,
        ]))
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"exported {len(keep)} cookies")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=9223)
    parser.add_argument("--channel", help="channel id (UC...) to read from Studio")
    parser.add_argument("--out", help="write the row list to this JSON file")
    parser.add_argument("--cookies-out", help="write a Netscape cookies.txt here")
    args = parser.parse_args()

    try:
        http_json(args.port, "/json/version")
    except Exception:
        print(f"No browser is listening on port {args.port}.", file=sys.stderr)
        return 2

    rc = 0
    if args.channel:
        rows = collect_rows(args.port, args.channel)
        payload = json.dumps(rows, ensure_ascii=False, indent=1)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(payload)
        counts = {}
        for row in rows:
            counts[row["visibility"] or "unknown"] = counts.get(row["visibility"] or "unknown", 0) + 1
        print(f"rows {len(rows)} " + json.dumps(counts))
        rc |= 0 if rows else 1
    if args.cookies_out:
        rc |= export_cookies(args.port, args.cookies_out)
    return rc


if __name__ == "__main__":
    sys.exit(main())
