# Copyright 2026 Doug Trier
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""tb-pad: shared notepad + file drop between the host and the test VM.

WHY: Hyper-V has no clipboard for Linux guests. A tiny web page reachable
from both sides replaces copy/paste without touching the guest (no xrdp,
no X11 session, no sudo).

SECURITY: binds only to the host's address on the Hyper-V Default Switch
(auto-detected from the route to the VM), so only the host and VMs on that
switch can reach it. No authentication by design; refuse any other bind
address unless --allow-any is given. State lives under reports/local/
(gitignored). Standard library only.

Endpoints:
  GET  /            notepad page (textarea, Save, Ctrl+S)
  GET  /text        raw note (text/plain)          curl -s http://HOST:8000/text
  POST /text        replace note with request body  curl --data-binary @f http://HOST:8000/text
  GET  /files/      list dropped files
  GET  /files/NAME  download a dropped file         curl -O http://HOST:8000/files/NAME
  PUT  /files/NAME  upload a file                   curl -T f http://HOST:8000/files/NAME
"""
from __future__ import annotations

import argparse
import html
import ipaddress
import json
import re
import socket
import subprocess
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "reports" / "local" / "pad"
NOTE = STATE / "note.txt"
FILES = STATE / "files"
MAX_BYTES = 64 * 1024 * 1024
NAME_RX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$")

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>tb-pad</title>
<style>body{{font-family:system-ui,sans-serif;margin:1rem;background:#f6f6f6}}
textarea{{width:100%;height:70vh;font:14px/1.4 ui-monospace,Consolas,monospace;padding:.5rem;box-sizing:border-box}}
.bar{{display:flex;gap:1rem;align-items:center;margin:.5rem 0}} code{{background:#eee;padding:0 .3em}}
ul{{margin:.3rem 0}}</style></head><body>
<div class="bar"><strong>tb-pad</strong> <span>{addr}</span>
<a href="/text" target="_blank">raw</a> <a href="/files/">files</a> <a href="/">reload</a></div>
<form method="post" action="/">
<textarea name="t" id="t" spellcheck="false">{text}</textarea>
<div class="bar"><button type="submit">Save</button><span>Ctrl+S saves. Raw note: <code>curl -s http://{addr}/text</code></span></div>
</form>
<script>document.addEventListener('keydown',e=>{{if((e.ctrlKey||e.metaKey)&&e.key==='s'){{e.preventDefault();document.forms[0].submit();}}}});</script>
</body></html>"""


def detect_bind(peer: str) -> str:
    """Host address on the Hyper-V Default Switch.

    Preferred: read the 'vEthernet (Default Switch)' adapter from ipconfig
    (fixed argv, no shell), because the switch subnet can change after a host
    reboot. Fallback: the local address used to route to the VM (--peer).
    """
    if sys.platform == "win32":
        try:
            out = subprocess.run(
                ["ipconfig"], capture_output=True, text=True, check=False, timeout=10
            ).stdout
            section = ""
            for line in out.splitlines():
                if line and not line[0].isspace():
                    section = line
                elif "Default Switch" in section and "IPv4" in line and ":" in line:
                    return line.rsplit(":", 1)[1].strip()
        except (OSError, subprocess.SubprocessError):
            pass
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((peer, 9))
        return s.getsockname()[0]
    finally:
        s.close()


class Pad(BaseHTTPRequestHandler):
    server_version = "tb-pad/1"
    addr = ""

    def log_message(self, fmt, *args):  # one line per request, no noise
        sys.stdout.write("%s %s\n" % (self.address_string(), fmt % args))
        sys.stdout.flush()

    # ---- helpers
    def _send(self, code: int, body: bytes, ctype: str = "text/plain; charset=utf-8", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> bytes | None:
        if "chunked" in (self.headers.get("Transfer-Encoding") or "").lower():
            buf = bytearray()
            while True:
                line = self.rfile.readline().strip()
                size = int(line.split(b";")[0], 16) if line else 0
                if size == 0:
                    while self.rfile.readline() not in (b"\r\n", b"\n", b""):
                        pass
                    return bytes(buf)
                buf += self.rfile.read(size)
                self.rfile.readline()
                if len(buf) > MAX_BYTES:
                    self._send(413, b"too large\n")
                    return None
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_BYTES:
            self._send(413, b"too large\n")
            return None
        return self.rfile.read(n) if n else b""

    def _file_path(self, name: str) -> Path | None:
        if not NAME_RX.match(name):
            self._send(400, b"bad file name\n")
            return None
        return FILES / name

    # ---- GET
    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        if path == "/":
            text = NOTE.read_text(encoding="utf-8") if NOTE.exists() else ""
            body = PAGE.format(addr=self.addr, text=html.escape(text)).encode("utf-8")
            self._send(200, body, "text/html; charset=utf-8")
        elif path == "/text":
            body = NOTE.read_bytes() if NOTE.exists() else b""
            self._send(200, body)
        elif path == "/files/":
            items = sorted(p.name for p in FILES.iterdir() if p.is_file())
            if "application/json" in (self.headers.get("Accept") or ""):
                self._send(200, json.dumps(items).encode(), "application/json")
            else:
                li = (
                    "".join(
                        f'<li><a href="/files/{html.escape(n)}">{html.escape(n)}</a> '
                        f"({(FILES / n).stat().st_size} B)</li>"
                        for n in items
                    )
                    or "<li>(none)</li>"
                )
                body = (
                    f"<!doctype html><html><body style='font-family:system-ui'><a href='/'>note</a>"
                    f"<h3>files</h3><ul>{li}</ul><p>upload from a shell: <code>curl -T FILE http://{self.addr}/files/FILE</code></p></body></html>"
                )
                self._send(200, body.encode("utf-8"), "text/html; charset=utf-8")
        elif path.startswith("/files/"):
            p = self._file_path(path[len("/files/") :])
            if p is None:
                return
            if not p.is_file():
                self._send(404, b"no such file\n")
                return
            self._send(
                200,
                p.read_bytes(),
                "application/octet-stream",
                {"Content-Disposition": f'attachment; filename="{p.name}"'},
            )
        else:
            self._send(404, b"not found\n")

    # ---- POST (form save or raw note)
    def do_POST(self):
        path = urllib.parse.urlsplit(self.path).path
        body = self._read_body()
        if body is None:
            return
        if path == "/":
            form = urllib.parse.parse_qs(body.decode("utf-8", "replace"), keep_blank_values=True)
            text = form.get("t", [""])[0].replace("\r\n", "\n")
            NOTE.write_text(text, encoding="utf-8")
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
        elif path == "/text":
            NOTE.write_bytes(body)
            self._send(200, b"saved %d bytes\n" % len(body))
        else:
            self._send(404, b"not found\n")

    # ---- PUT (file upload)
    def do_PUT(self):
        path = urllib.parse.urlsplit(self.path).path
        if not path.startswith("/files/"):
            self._send(404, b"not found\n")
            return
        p = self._file_path(path[len("/files/") :])
        if p is None:
            return
        body = self._read_body()
        if body is None:
            return
        p.write_bytes(body)
        self._send(201, b"stored %s (%d bytes)\n" % (p.name.encode(), len(body)))


def main(argv=None) -> int:
    global STATE, NOTE, FILES
    ap = argparse.ArgumentParser(description="shared notepad + file drop for the test VM")
    ap.add_argument(
        "--peer", default="172.20.252.59", help="VM address used to detect the switch-side host IP"
    )
    ap.add_argument(
        "--bind", default="auto", help="address to listen on (default: auto from --peer)"
    )
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument(
        "--allow-any", action="store_true", help="permit a non-private or wildcard bind address"
    )
    ap.add_argument(
        "--state",
        default=str(STATE),
        help="folder for note.txt and files/ (default: reports/local/pad, gitignored)",
    )
    ap.add_argument(
        "--open", action="store_true", help="open the page in the host browser after starting"
    )
    args = ap.parse_args(argv)

    STATE = Path(args.state).resolve()
    NOTE = STATE / "note.txt"
    FILES = STATE / "files"

    bind = detect_bind(args.peer) if args.bind == "auto" else args.bind
    ip = ipaddress.ip_address(bind) if bind != "0.0.0.0" else None
    if not args.allow_any and (ip is None or not ip.is_private or ip.is_loopback):
        print(
            f"tb-pad: refusing to bind {bind}; expected the private Hyper-V switch address (use --bind or --allow-any)"
        )
        return 2

    STATE.mkdir(parents=True, exist_ok=True)
    FILES.mkdir(exist_ok=True)
    if not NOTE.exists():
        NOTE.write_text("", encoding="utf-8")
    Pad.addr = f"{bind}:{args.port}"
    srv = ThreadingHTTPServer((bind, args.port), Pad)
    print(
        f"tb-pad on http://{Pad.addr}/  note={NOTE}  files={FILES}  (Ctrl+C or close this window to stop)"
    )
    sys.stdout.flush()
    if args.open:
        webbrowser.open(f"http://{Pad.addr}/")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
