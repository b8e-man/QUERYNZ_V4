"""A fake `query-nz-ingest` for the tests: the MCP's handshake and its
`corpora`, `records`, `changes` and `download` answers, as server-sent
events with keep-alive pings, from records made in each corpus's recorded
shape (shapes.json, the field names and types the real server served on 26
and 30 October 2026). Values are made up: no record of the real corpus is
in git. A record whose shape carries a capture sha256 and a content type
(courts) points at a made file, `file_bytes(corpus, seq)`, whose hash the
record promises; `download` serves it as the real tool does (a meta text
part and an embedded resource with the base64 blob)."""
import base64
import email.message
import hashlib
import io
import json

from support import mcpsource as M


def _block(items: dict, seq: int) -> dict:
    out = {}
    for k, types in sorted(items.items()):
        t = next((x for x in types if x != "null"), "null")
        out[k] = {"str": f"{k} {seq}", "int": seq, "list": [], "null": None}.get(t)
        if t == "str" and k in ("fetched_at", "updated_at", "_fetched_at", "fetched"):
            out[k] = "2026-10-29T04:37:04+00:00"
    return out


def file_bytes(corpus: str, seq: int) -> bytes:
    """The made file a record of a corpus with files points at: a PDF for
    an even seq, a page for an odd one."""
    if seq % 2 == 0:
        return b"%PDF-1.4\n% made " + f"{corpus} {seq}".encode() + b"\n%%EOF\n"
    return f"<html><title>made {corpus} {seq}</title></html>".encode()


def made_record(corpus: str, seq: int, shape: dict) -> dict:
    """A record of `corpus` at `seq` with every recorded field, each of its
    first recorded type; one that points at a file promises the hash and
    size of `file_bytes(corpus, seq)`."""
    rec = _made(corpus, seq, shape)
    cap = rec.get("capture")
    if isinstance(cap, dict) and "sha256" in cap and "content_type" in rec:
        data = file_bytes(corpus, seq)
        sha = hashlib.sha256(data).hexdigest()
        rec["content_type"] = "application/pdf" if seq % 2 == 0 else "text/html; charset=utf-8"
        rec["kind"] = "judgment_pdf" if seq % 2 == 0 else "case_page"
        cap["sha256"] = rec["sha256"] = sha
        cap["bytes"] = rec["bytes"] = len(data)
        cap["url"] = rec["url"]
    return rec


def _made(corpus: str, seq: int, shape: dict) -> dict:
    rec = {}
    for field, types in sorted(shape["fields"].items()):
        t = next((x for x in types if x != "null"), "null")
        if field == "seq":
            rec[field] = seq
        elif field == "id":
            rec[field] = f"{corpus}-{seq:06d}"
        elif field == "updated_at":
            rec[field] = "2026-10-26T00:00:00Z"
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
        self.file_hook = None         # (record, bytes) -> bytes, to serve other bytes than the record promises
        self.downloads = []           # the arguments of every `download` call (the tool is metered)

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
            body = {"corpora": [{"name": c, "records": len(r), "ingest_cursor": len(r), "arrivals_last_24h": 0,
                                 "has_files": any(M.file_pointer(x) for x in r)}
                                for c, r in self.records.items()], "note": "Counts and freshness only."}
        elif name == "download":
            self.downloads.append(args)
            rows = self.records.get(args.get("corpus"), [])
            rec = next((r for r in rows if r.get("id") == args.get("record_id")), None)
            if rec is None or M.file_pointer(rec) is None:
                return self._answer(msg["id"], {"isError": True, "content": [{"type": "text", "text": "no such file"}]})
            data = file_bytes(args["corpus"], rec["seq"])
            if self.file_hook:
                data = self.file_hook(rec, data)
            scheme = "qnz-pdf" if "pdf" in rec["content_type"] else "qnz-html"
            meta = {"corpus": args["corpus"], "seq": rec["seq"], "record_id": rec["id"], "title": rec.get("case_slug"),
                    "kind": rec["kind"], "format": args.get("format", "raw"), "content_type": rec["content_type"],
                    "delivered_bytes": len(data), "delivered_sha256": hashlib.sha256(data).hexdigest(),
                    "captured_sha256": rec["capture"]["sha256"],
                    "sha256_matches_capture": hashlib.sha256(data).hexdigest() == rec["capture"]["sha256"],
                    "resource_uri": f"{scheme}://{args['corpus']}/{rec['seq']}", "capture": rec["capture"],
                    "file": "/opt/data/made/" + rec["path"], "note": "bytes exactly as captured; nothing transformed"}
            return self._answer(msg["id"], {"content": [
                {"type": "text", "text": json.dumps(meta)},
                {"type": "resource", "resource": {"uri": meta["resource_uri"], "mimeType": rec["content_type"].split(";")[0],
                                                  "blob": base64.b64encode(data).decode("ascii")}}], "isError": False})
        elif name == "records":
            rows = self.records[args["corpus"]]
            cur, lim = args.get("cursor", 0), args.get("limit", 50)
            page = rows[cur:cur + lim]
            body = {"corpus": args["corpus"], "total": len(rows), "cursor": cur, "next_cursor": cur + len(page),
                    "records": page}
            if self.page_hook:
                body = self.page_hook(body)
        elif name == "changes":                       # moved after `since`, in (updated_at, seq) order
            rows = sorted((r for r in self.records[args["corpus"]] if r.get("updated_at", "") > args["since"]),
                          key=lambda r: (r["updated_at"], r["seq"]))
            cur, lim = args.get("cursor", 0), args.get("limit", 100)
            page = rows[cur:cur + lim]
            body = {"corpus": args["corpus"], "since": args["since"], "cursor": cur, "next_cursor": cur + len(page),
                    "records": page}
        else:
            return self._answer(msg["id"], {"isError": True, "content": [{"type": "text", "text": f"no tool {name}"}]})
        return self._answer(msg["id"], {"content": [{"type": "text", "text": json.dumps(body)}], "isError": False})


def corpus_of(corpus: str, n: int, shape: dict = None) -> list:
    shape = shape or M.shapes()[corpus]
    return [made_record(corpus, i, shape) for i in range(n)]


def client_for(server) -> M.Client:
    return M.Client(url="http://fake.test/mcp", timeout=5, opener=server)


__all__ = ["FakeServer", "corpus_of", "client_for", "made_record", "file_bytes", "io"]
