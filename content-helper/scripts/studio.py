"""Chromium DevTools helpers: browser session, cookies, Studio rows, JSON capture."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from common import Log, run_stream

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
    signedIn: !location.href.includes('accounts.google.com'),
    rows: [...seen.values()]
  });
})()
"""


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
        result = self.call("Runtime.evaluate", expression=expression, returnByValue=True,
                           awaitPromise=True)
        return result.get("result", {}).get("result", {}).get("value")

    def close(self) -> None:
        self.ws.close()


def version(port: int) -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=10) as resp:
        return json.load(resp)


def reachable(port: int) -> bool:
    try:
        version(port)
        return True
    except Exception:
        return False


def new_tab(port: int, url: str) -> dict:
    quoted = urllib.parse.quote(url, safe="")
    request = urllib.request.Request(f"http://127.0.0.1:{port}/json/new?{quoted}", method="PUT")
    with urllib.request.urlopen(request, timeout=20) as resp:
        return json.load(resp)


def launch(browser: str, port: int, log: Log) -> bool:
    if os.name != "nt":
        log("the browser session helper is Windows-only")
        return False
    if reachable(port):
        return True
    log(f"launching {browser} with a debug port")
    helper = Path(__file__).with_name("browser_debug.ps1")
    return run_stream(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                       "-File", str(helper), "-Browser", browser, "-Port", str(port)], log) == 0


def stop(browser: str, log: Log) -> None:
    if os.name != "nt":
        return
    helper = Path(__file__).with_name("browser_debug.ps1")
    subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", str(helper), "-Browser", browser, "-Stop"],
                   capture_output=True, text=True)
    log(f"closed {browser}")


def export_cookies(port: int, out_path: Path) -> int:
    session = Session(version(port)["webSocketDebuggerUrl"])
    response = session.call("Storage.getCookies")
    session.close()
    if "error" in response:
        return 1
    keep = [c for c in response["result"]["cookies"]
            if any(d in (c.get("domain") or "") for d in ("youtube.com", "google.com"))]
    lines = ["# Netscape HTTP Cookie File", ""]
    for cookie in keep:
        value = cookie.get("value", "")
        if "\t" in value or "\n" in value:
            continue
        domain = cookie["domain"]
        expires = int(cookie.get("expires") or 0)
        lines.append("\t".join([domain, "TRUE" if domain.startswith(".") else "FALSE",
                                cookie.get("path", "/"),
                                "TRUE" if cookie.get("secure") else "FALSE",
                                str(expires) if expires > 0 else "0",
                                cookie["name"], value]))
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


def cookies_to_temp(port: int) -> tuple[Path | None, Path | None]:
    import tempfile

    temp = Path(tempfile.mkdtemp(prefix="content-helper-cookies-"))
    path = temp / "cookies.txt"
    return (path, temp) if export_cookies(port, path) == 0 and path.exists() else (None, temp)


def rows(channel_id: str, port: int, log: Log) -> list[dict]:
    collected: dict[str, dict] = {}
    for tab in ("videos/upload", "videos/short"):
        url = f"https://studio.youtube.com/channel/{channel_id}/{tab}"
        target = new_tab(port, url)
        session = Session(target["webSocketDebuggerUrl"])
        session.call("Runtime.enable")
        deadline = time.time() + 60
        while time.time() < deadline and session.eval("document.readyState") != "complete":
            time.sleep(1)
        time.sleep(4)
        payload = session.eval(ROW_SCRIPT)
        session.close()
        if not payload:
            log(f"no Studio rows for {tab}")
            continue
        data = json.loads(payload)
        if not data.get("signedIn"):
            raise SystemExit("not signed in to YouTube Studio in that browser profile")
        for row in data.get("rows", []):
            row["tab"] = "shorts" if tab.endswith("short") else "long"
            collected.setdefault(row["id"], row)
    return list(collected.values())


def harvest_json(port: int, url: str, needles: tuple[str, ...], log: Log,
                 wait: float = 18.0) -> list[dict]:
    """Open a page and return every JSON response body containing one of the needles."""
    target = new_tab(port, url)
    session = Session(target["webSocketDebuggerUrl"])
    session.call("Runtime.enable")
    session.call("Network.enable", maxTotalBufferSize=200_000_000,
                 maxResourceBufferSize=40_000_000)
    pending: list[str] = []
    found: list[dict] = []
    deadline = time.time() + wait
    session.ws.settimeout(2)
    while time.time() < deadline:
        try:
            message = json.loads(session.ws.recv())
        except Exception:
            continue
        method = message.get("method")
        if method == "Network.responseReceived":
            params = message["params"]
            mime = params.get("response", {}).get("mimeType", "")
            if "json" in mime:
                pending.append(params["requestId"])
        elif method == "Network.loadingFinished" and message["params"]["requestId"] in pending:
            request_id = message["params"]["requestId"]
            body = session.call("Network.getResponseBody", requestId=request_id)
            text = body.get("result", {}).get("body", "")
            if text and any(needle in text for needle in needles):
                try:
                    found.append(json.loads(text))
                except json.JSONDecodeError:
                    pass
    session.close()
    log(f"harvested {len(found)} matching JSON payloads from {url.split('/video/')[-1][:24]}")
    return found
