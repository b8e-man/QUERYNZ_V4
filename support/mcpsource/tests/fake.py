"""A fake `query-nz-ingest` for the tests: the MCP's handshake and its
`corpora` and `records` answers, as server-sent events with keep-alive
pings, from records made in each corpus's recorded shape (shapes.json, the
field names and types the real server served on 26 October 2026). Values
are made up: no record of the real corpus is in git."""
import email.message
import io
import json

from support import mcpsource as M


def _block(items: dict, seq: int) -> dict:
    out = {}
    for k, types in sorted(items.items()):
        t = next((x for x in types if x != "null"), "null")
        out[k] = {"str": f"{k} {seq}", "int": seq, "list": [], "null": None}.get(t)
    return out


def made_record(corpus: str, seq: int, shape: dict) -> dict:
    """A record of `corpus` at `seq` with every recorded field, each of its
    first recorded type."""
    rec = {}
    for field, types in sorted(shape["fields"].items()):
        t = next((x for x in types if x != "null"), "null")
        if field == "seq":
            rec[field] = seq
        elif field == "id":
            rec[field] = f"{corpus}-{seq:06d}"
        elif field == "url":
            rec[field] = f"https://example.test/{corpus}/{seq}" if t == "str" else None
        elif t == "str":
            rec[field] = f"{field} {seq}"
        elif t == "int":
            rec[field] = seq
        elif t == "list":
            items = shape.get("items", {}).get(field)
            if items is None:
                rec[field] = []
            elif set(items) == {"*"}:
                rec[field] = [f"{field} {seq} a", f"{field} {seq} b"]
            else:
                rec[field] = [_block(items, seq)]
        elif t == "dict":
            rec[field] = _block(shape.get("items", {}).get(field, {}), seq)
        else:
            rec[field] = None
    return rec


class Response:
    def __init__(self, body: str, headers: dict, status: int = 200):
        self._body = body.encode("utf-8")
        self.headers = email.message.Message()
        for k, v in headers.items():
            self.headers[k] = v
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeServer:
    """`opener(req, timeout)` in place of urllib's. `records` holds the
    corpus as served: {corpus: [record, …]} in arrival order."""

    def __init__(self, records: dict, sse: bool = True):
        self.records = records
        self.sse = sse
        self.session = "fake-session-1"
        self.requests = []            # (method, arguments) of every request
        self.fail_next = []           # exceptions raised on the next requests, in order
        self.page_hook = None         # page dict -> page dict, to change the shape served

    def _answer(self, rid, result):
        msg = json.dumps({"jsonrpc": "2.0", "id": rid, "result": result})
        if self.sse:
            return Response(f": ping\n\n: ping\n\nevent: message\ndata: {msg}\n\n",
                            {"Content-Type": "text/event-stream", "Mcp-Session-Id": self.session})
        return Response(msg, {"Content-Type": "application/json", "Mcp-Session-Id": self.session})

    def __call__(self, req, timeout=None):
        if self.fail_next:
            raise self.fail_next.pop(0)
        msg = json.loads(req.data)
        method, params = msg.get("method"), msg.get("params") or {}
        self.requests.append((method, params.get("arguments") if method == "tools/call" else None))
        assert "text/event-stream" in req.get_header("Accept")
        if method == "initialize":
            return self._answer(msg["id"], {"protocolVersion": params["protocolVersion"],
                                            "serverInfo": {"name": "query-nz-ingest", "version": "0.2.0"}})
        assert req.get_header("Mcp-session-id") == self.session, "a request without the session id"
        if "id" not in msg:
            return Response("", {"Content-Type": "application/json"}, 202)
        name, args = params["name"], params.get("arguments") or {}
        if name == "corpora":
            body = {"corpora": [{"name": c, "records": len(r), "ingest_cursor": len(r), "arrivals_last_24h": 0}
                                for c, r in self.records.items()], "note": "Counts and freshness only."}
        elif name == "records":
            rows = self.records[args["corpus"]]
            cur, lim = args.get("cursor", 0), args.get("limit", 50)
            page = rows[cur:cur + lim]
            body = {"corpus": args["corpus"], "total": len(rows), "cursor": cur, "next_cursor": cur + len(page),
                    "records": page}
            if self.page_hook:
                body = self.page_hook(body)
        else:
            return self._answer(msg["id"], {"isError": True, "content": [{"type": "text", "text": f"no tool {name}"}]})
        return self._answer(msg["id"], {"content": [{"type": "text", "text": json.dumps(body)}], "isError": False})


def corpus_of(corpus: str, n: int, shape: dict = None) -> list:
    shape = shape or M.shapes()[corpus]
    return [made_record(corpus, i, shape) for i in range(n)]


def client_for(server) -> M.Client:
    return M.Client(url="http://fake.test/mcp", timeout=5, opener=server)


__all__ = ["FakeServer", "corpus_of", "client_for", "made_record", "io"]
