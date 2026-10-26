"""The reading of the `beehive` records (profile `mcp-beehive-record`, v1).

A document is one record of the ingest MCP's `beehive` corpus as
support/mcpsource landed it: the record's JSON, keys sorted, without its
`seq`. The reading takes the MCP's fields as they are: no model, no
inference, nothing fetched. Each record is read by its hash; where the MCP
has served a record more than once with different bytes, the release is
read from the version it served last (the highest `seq`) and the others
are kept in `files` as older versions.

    read(items, get_bytes)   items: [(sha256, seq or None, record id or None)] → Result

The topics and quotes are the provider's model's work, done on its box
outside the estate (ruling 96): kept in their own rows, marked model-made
by the source, never read into a claim or a link. The body and the text go
to the private table only.
"""
import datetime as dt
import json
from dataclasses import dataclass, field

READER = "registers.beehive.read"
PROFILE = "mcp-beehive-record"
PROFILE_VERSION = 1
SOURCE_NOTE = ("a record of the query-nz ingest MCP's beehive corpus: captured and read off-estate by Arthur's "
               "provider (ruling 78); the estate never fetched beehive.govt.nz")
MADE_BY = "the query-nz provider's model, on its own box outside the estate"
HOST = "https://www.beehive.govt.nz/"
KNOWN = ("id", "url", "final_url", "http_status", "type", "kind", "title", "published_at", "date", "word_count",
         "ministers", "portfolios", "topics", "quotes", "body_text", "text", "sha256", "source_file", "model",
         "extracted_at", "updated_at", "capture", "annotation", "fetched_at", "status", "path")
CAPTURE = ("url", "kind", "fetched_at", "status", "path", "sha256", "final_url", "http_status")
ANNOTATION = ("fields", "generator", "created_at")
MODEL_MADE = ("topics", "quotes")       # the fields the provider's model made, where a record names none


@dataclass
class Result:
    releases: list = field(default_factory=list)
    ministers: list = field(default_factory=list)
    portfolios: list = field(default_factory=list)
    topics: list = field(default_factory=list)
    quotes: list = field(default_factory=list)
    texts: list = field(default_factory=list)          # (key, body_text, text): private
    files: list = field(default_factory=list)          # (sha256, record id, seq, status)
    set_aside: list = field(default_factory=list)      # (item, stage, reason)
    counts: dict = field(default_factory=dict)


def _stamp(sha: str, place: str, loaded_at: str) -> dict:
    return {"document": sha, "page": 1, "place": place, "read_from": "text", "reader": READER, "profile": PROFILE,
            "profile_version": PROFILE_VERSION, "loaded_at": loaded_at}


def _iso_date(v):
    if not isinstance(v, str):
        return None
    try:
        return dt.date.fromisoformat(v[:10]).isoformat() if len(v) >= 10 else None
    except ValueError:
        return None


def _int(v):
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def _str(v):
    return v.strip() if isinstance(v, str) and v.strip() else None


def recognise(rec) -> str:
    """'' when the document is this profile's shape, else why not."""
    if not isinstance(rec, dict):
        return "not a JSON object"
    if not _str(rec.get("id")):
        return "no id"
    url = rec.get("url")
    if not isinstance(url, str) or not url.startswith(HOST):
        return "its url is not a beehive.govt.nz page"
    for f in ("ministers", "portfolios", "topics", "quotes"):
        if rec.get(f) is not None and not isinstance(rec[f], list):
            return f"`{f}` is not a list"
    return ""


def _unread(rec: dict) -> list:
    out = set(rec) - set(KNOWN)
    for block, known in (("capture", CAPTURE), ("annotation", ANNOTATION)):
        if isinstance(rec.get(block), dict):
            out |= {f"{block}.{k}" for k in rec[block] if k not in known}
    return sorted(out)


def provenance(rec: dict) -> dict:
    """The provider's own record of its capture and its model, from the
    `capture` and `annotation` blocks or, on its older records, from the
    same fields at the top level."""
    cap = rec.get("capture") if isinstance(rec.get("capture"), dict) else {}
    ann = rec.get("annotation") if isinstance(rec.get("annotation"), dict) else {}
    pick = lambda k: cap.get(k) if cap.get(k) is not None else rec.get(k)   # noqa: E731
    status = pick("status")
    fields = [f for f in ann.get("fields") or [] if isinstance(f, str)] if isinstance(ann.get("fields"), list) else []
    return {"final_url": _str(pick("final_url")), "http_status": _int(pick("http_status")), "kind": _str(pick("kind")),
            "captured_sha256": _str(cap.get("sha256")) or _str(rec.get("sha256")),
            "captured_at": _str(pick("fetched_at")), "capture_status": None if status is None else str(status),
            "provider_file": _str(rec.get("source_file")), "provider_path": _str(pick("path")),
            "model": _str(rec.get("model")), "extracted_at": _str(rec.get("extracted_at")),
            "updated_at": _str(rec.get("updated_at")), "annotation_fields": fields,
            "annotation_generator": _str(ann.get("generator")), "annotation_created_at": _str(ann.get("created_at"))}


def read_one(sha: str, rec: dict, seq, versions: int, out: Result, loaded_at: str) -> None:
    key = rec["id"].strip()
    n = out.counts
    prov = provenance(rec)
    made_by = (f"{MADE_BY}: {prov['annotation_generator'] or prov['model']}"
               if prov["annotation_generator"] or prov["model"] else MADE_BY)
    outside = sorted(set(prov["annotation_fields"]) - set(MODEL_MADE))
    if outside:                                       # a field their model made that this lane reads as the site's
        n["model-made fields outside topics and quotes"] = n.get("model-made fields outside topics and quotes", 0) + 1
    ministers = []
    for i, m in enumerate(rec.get("ministers") or [], 1):
        name = _str(m.get("name")) if isinstance(m, dict) else _str(m)
        if not name:
            n["ministers without a name"] = n.get("ministers without a name", 0) + 1
            continue
        ministers.append({"key": f"{key}#minister/{i}", "release": key, "ordinal": i, "name": name,
                          "slug": _str(m.get("slug")) if isinstance(m, dict) else None,
                          **_stamp(sha, f"ministers[{i - 1}]", loaded_at)})
    portfolios = [p.strip() for p in (rec.get("portfolios") or []) if _str(p)]
    for i, p in enumerate(portfolios, 1):
        out.portfolios.append({"key": f"{key}#portfolio/{i}", "release": key, "ordinal": i, "portfolio": p,
                               **_stamp(sha, f"portfolios[{i - 1}]", loaded_at)})
    topics = [t.strip() for t in (rec.get("topics") or []) if _str(t)]
    for i, t in enumerate(topics, 1):
        out.topics.append({"key": f"{key}#topic/{i}", "release": key, "ordinal": i, "topic": t, "model_made": True,
                           "made_by": made_by, **_stamp(sha, f"topics[{i - 1}]", loaded_at)})
    quotes = 0
    for i, q in enumerate(rec.get("quotes") or [], 1):
        text = _str(q.get("text")) if isinstance(q, dict) else _str(q)
        if not text:
            continue
        quotes += 1
        out.quotes.append({"key": f"{key}#quote/{i}", "release": key, "ordinal": i, "quote": text,
                           "speaker": _str(q.get("speaker")) if isinstance(q, dict) else None, "model_made": True,
                           "made_by": made_by, **_stamp(sha, f"quotes[{i - 1}]", loaded_at)})
    out.ministers += ministers
    if not _str(rec.get("title")):
        n["untitled"] = n.get("untitled", 0) + 1
    if rec.get("date") is not None and _iso_date(rec.get("date")) is None:
        n["dates not ISO"] = n.get("dates not ISO", 0) + 1
    out.releases.append({
        "key": key, "url": rec["url"], **prov, "type": _str(rec.get("type")), "title": _str(rec.get("title")),
        "published_at": _str(rec.get("published_at")), "published_on": _iso_date(rec.get("date")),
        "word_count": _int(rec.get("word_count")), "ministers": len(ministers), "portfolios": portfolios,
        "topics": len(topics), "quotes": quotes, "fields_unread": _unread(rec),
        "versions": versions, "seq": seq, "origin": "mcp", "source_note": SOURCE_NOTE, **_stamp(sha, "record", loaded_at)})
    out.texts.append((key, rec.get("body_text") if isinstance(rec.get("body_text"), str) else None,
                      rec.get("text") if isinstance(rec.get("text"), str) else None))


def read(items, get_bytes, loaded_at: str = None) -> Result:
    """Every document in `items` read or set aside. A document's record id
    is its own `id`; where `items` names one too, the two must agree."""
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    out = Result()
    newest = {}                                   # sha -> highest seq given (None when none given)
    order = []
    for sha, seq, _rid in items:
        if sha not in newest:
            order.append(sha)
            newest[sha] = seq
        elif seq is not None and (newest[sha] is None or seq > newest[sha]):
            newest[sha] = seq
    named = {}
    for sha, _seq, rid in items:
        if rid is not None:
            named.setdefault(sha, set()).add(rid)
    by_record = {}
    for pos, sha in enumerate(order):
        try:
            rec = json.loads(get_bytes(sha))
        except (OSError, ValueError) as e:
            out.set_aside.append((sha, "open", f"{type(e).__name__}: {str(e)[:200]}"))
            out.files.append((sha, None, newest[sha], "set aside"))
            continue
        why = recognise(rec)
        if not why and named.get(sha) and named[sha] != {rec["id"]}:
            why = "the arrival names another record"
        if why:
            out.set_aside.append((sha, "recognise", why))
            out.files.append((sha, rec.get("id") if isinstance(rec, dict) and isinstance(rec.get("id"), str) else None,
                              newest[sha], "set aside"))
            continue
        rank = (newest[sha] if newest[sha] is not None else -1, pos)
        by_record.setdefault(rec["id"].strip(), []).append((rank, sha, rec))
    for rid, versions in by_record.items():
        versions.sort(key=lambda v: v[0])
        _, sha, rec = versions[-1]
        read_one(sha, rec, newest[sha], len(versions), out, loaded_at)
        out.files.append((sha, rid, newest[sha], "read"))
        out.files += [(s, rid, newest[s], "older version") for _, s, _ in versions[:-1]]
    out.counts.update({"documents": len(order), "from the MCP": len(out.releases), "releases": len(out.releases), "older versions":
                       sum(len(v) - 1 for v in by_record.values()), "ministers": len(out.ministers),
                       "portfolios": len(out.portfolios), "topics": len(out.topics), "quotes": len(out.quotes),
                       "set aside": len(out.set_aside)})
    return out


OLD_PROFILE = "beehive-old-estate-export"
OLD_PROFILE_VERSION = 1
OLD_NOTE = "taken from the old estate's tables (its scraper, before ruling 78); original not held"


def read_old(data: bytes, sha: str, held: set, out: Result, loaded_at: str = None) -> None:
    """The old estate's once-only export (capture.OLD_EXPORT_SHA): one
    release per line whose address the MCP does not hold (`held`), with the
    title, the NZ post day and the text as the old scraper kept them; no
    ministers or portfolios (the old scraper kept none). A line the MCP does
    hold is counted and left: the MCP's record is the reading."""
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    n = out.counts
    for i, line in enumerate(data.decode("utf-8").split("\n"), 1):     # never splitlines: a text holds U+2028
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError as e:
            out.set_aside.append((f"{sha}/line {i}", "old export", f"not JSON: {e}"))
            continue
        url = row.get("url")
        if not isinstance(url, str) or not url.startswith(HOST):
            out.set_aside.append((f"{sha}/line {i}", "old export", "its url is not a beehive.govt.nz page"))
            continue
        n["old estate lines"] = n.get("old estate lines", 0) + 1
        if url in held:
            n["old estate pages the MCP holds"] = n.get("old estate pages the MCP holds", 0) + 1
            continue
        text = row.get("text") or ""
        path = url[len(HOST):].split("/", 1)[0]
        out.releases.append({
            "key": url, "url": url, "type": path or None, "title": _str(row.get("title")),
            "published_at": _str(row.get("posted_nz")), "published_on": _iso_date(row.get("posted_nz")),
            "word_count": len(text.split()), "ministers": 0, "portfolios": [], "topics": 0, "quotes": 0,
            "fields_unread": [], "versions": 1, "seq": None, "origin": "old estate", "source_note": OLD_NOTE,
            "final_url": None, "http_status": None, "kind": None, "captured_sha256": None,
            "captured_at": _str(row.get("fetched")) or _str(row.get("scraped")), "capture_status": None,
            "provider_file": None, "provider_path": None, "model": None, "extracted_at": None, "annotation_fields": [],
            "annotation_generator": None, "annotation_created_at": None, "updated_at": None,
            "document": sha, "page": 1, "place": f"line {i}", "read_from": "text", "reader": READER,
            "profile": OLD_PROFILE, "profile_version": OLD_PROFILE_VERSION, "loaded_at": loaded_at})
        out.texts.append((url, text, None))
        held.add(url)
        n["from the old estate"] = n.get("from the old estate", 0) + 1
    n["releases"], n["set aside"] = len(out.releases), len(out.set_aside)
