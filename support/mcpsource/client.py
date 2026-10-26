"""The client for the ingest MCP `query-nz-ingest` (rulings 94, 96), stdlib only.

The server speaks Streamable HTTP: JSON-RPC posted to one address. The
handshake is `initialize` (with `Accept: application/json,
text/event-stream`), whose answer carries an `Mcp-Session-Id` header that
every later request sends back, then the notification
`notifications/initialized`. An answer comes either as one JSON body or as
server-sent events: `data:` lines holding the JSON-RPC message, with `: ping`
comment lines as keep-alives while the server works.

One call per request, one request at a time, each under a time limit. A
call that fails raises `McpError` with the server's own words kept (the
HTTP status and body, or the tool's error text), never a bare traceback.
`call_retrying` waits and asks again when the server is slow or the
connection drops (the server slows under its own arrivals: 45 s a call on
26 October at 16:10), a fresh handshake after a lost session.

    c = Client()                       # http://127.0.0.1:8646/mcp, the tunnel unit qv4-mcp-tunnel
    c.call("corpora", {})              # the tool's answer, parsed from its JSON text
"""
import http.client
import itertools
import json
import socket
import time
import urllib.error
import urllib.request

URL = "http://127.0.0.1:8646/mcp"
PROTOCOL = "2025-03-26"
CLIENT = {"name": "qv4-mcpsource", "version": "1"}
TIMEOUT_S = 180.0


class McpError(Exception):
    """A call that did not answer: `why` is the server's own text, kept."""

    def __init__(self, why: str, transient: bool = False):
        super().__init__(why)
        self.why = why
        self.transient = transient


def messages_of(body: str, content_type: str) -> list:
    """The JSON-RPC messages in one answer: a JSON body, or the `data:`
    lines of an event stream (an event's data may span several lines;
    comment lines such as `: ping` are keep-alives)."""
    if "text/event-stream" not in (content_type or ""):
        body = body.strip()
        if not body:
            return []
        got = json.loads(body)
        return got if isinstance(got, list) else [got]
    out, data = [], []
    for line in [l[:-1] if l.endswith("\r") else l for l in body.split("\n")] + [""]:   # never splitlines: U+2028
        if line.startswith(":"):
            continue
        if line.startswith("data:"):
            data.append(line[5:].lstrip(" ") if line[5:6] == " " else line[5:])
        elif line == "" and data:
            out.append(json.loads("\n".join(data)))
            data = []
    return out


def tool_answer(result: dict):
    """A `tools/call` result's answer: the structured content when given,
    else the JSON in its first text part (or the text itself)."""
    if result.get("isError"):
        text = " ".join(p.get("text", "") for p in result.get("content", []) if p.get("type") == "text")
        raise McpError(f"tool error: {text[:500]}")
    if result.get("structuredContent") is not None:
        sc = result["structuredContent"]
        return sc.get("result", sc) if isinstance(sc, dict) and set(sc) == {"result"} else sc
    for p in result.get("content", []):
        if p.get("type") == "text":
            try:
                return json.loads(p["text"])
            except ValueError:
                return p["text"]
    raise McpError("tool answer has no content")


class Client:
    def __init__(self, url: str = URL, timeout: float = TIMEOUT_S, opener=None):
        self.url, self.timeout = url, timeout
        self.open = opener or urllib.request.urlopen
        self.session = None
        self.ids = itertools.count(1)
        self.calls = 0

    def _post(self, message: dict):
        """(headers, messages) for one posted message."""
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        req = urllib.request.Request(self.url, data=json.dumps(message).encode("utf-8"), headers=headers, method="POST")
        try:
            with self.open(req, timeout=self.timeout) as r:
                body = r.read().decode("utf-8", errors="replace")
                return r.headers, messages_of(body, r.headers.get("Content-Type", ""))
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", errors="replace")[:500] if e.fp else ""
            if e.code == 404 and self.session:      # the server has forgotten the session: shake hands again
                self.session = None
            raise McpError(f"HTTP {e.code} {e.reason}: {text}", transient=e.code in (404, 408, 429, 500, 502, 503, 504))
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError,
                http.client.HTTPException) as e:          # IncompleteRead: the answer cut off mid-stream
            reason = getattr(e, "reason", e)
            raise McpError(f"{type(e).__name__}: {reason}", transient=True)
        except ValueError as e:
            raise McpError(f"an answer that is not JSON-RPC: {e}", transient=True)

    def _request(self, method: str, params: dict):
        rid = next(self.ids)
        headers, msgs = self._post({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        for m in msgs:
            if m.get("id") == rid:
                if "error" in m:
                    err = m["error"]
                    raise McpError(f"JSON-RPC error {err.get('code')}: {err.get('message')} {err.get('data') or ''}".strip())
                return headers, m.get("result")
        raise McpError(f"no answer to request {rid} ({len(msgs)} message(s))", transient=True)

    def connect(self) -> dict:
        """The handshake: initialize, keep the session id, say initialized."""
        self.session = None
        headers, result = self._request("initialize", {"protocolVersion": PROTOCOL, "capabilities": {},
                                                       "clientInfo": CLIENT})
        self.session = headers.get("Mcp-Session-Id") or headers.get("mcp-session-id")
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return result or {}

    def call(self, tool: str, arguments: dict):
        """One tool call, one request."""
        if self.session is None:
            self.connect()
        self.calls += 1
        _, result = self._request("tools/call", {"name": tool, "arguments": arguments})
        return tool_answer(result or {})

    def call_retrying(self, tool: str, arguments: dict, tries: int = 6, wait_s: float = 30.0, sleep=time.sleep, log=None):
        """`call`, asked again after a wait when the failure is the
        server's slowness or a dropped connection; the wait doubles each
        time (30 s, 60 s, … at most 10 minutes). A failure that is not
        transient, or the last try's, is raised with its text."""
        for attempt in range(1, tries + 1):
            try:
                return self.call(tool, arguments)
            except McpError as e:
                if not e.transient or attempt == tries:
                    raise
                pause = min(wait_s * 2 ** (attempt - 1), 600.0)
                if log:
                    log(f"mcpsource: {tool} try {attempt} failed ({e.why[:200]}); waiting {pause:.0f} s")
                sleep(pause)
