"""The reading of the ingest MCP's two Hansard corpora (rulings 96, 97), from
text, no model, nothing fetched. A document is one record as
support/mcpsource landed it (its JSON, keys sorted, without `seq`).

  parliament-hansard-index    profile `mcp-hansard-index-record`: one row of
                              `index_pages` per record, a sitemap entry of a
                              parliament.nz page (url, lastmod, fetched, date);
                              no text
  parliament-hansard-debates  profile `mcp-hansard-debates-record`: one row of
                              `days` per record, a sitting day's daily PDF as
                              the provider read it with pdftotext -layout (the
                              PDF's address and hash, its page and word
                              counts); the text goes to the private twin
                              through `sink`; no section or speech split

Where the MCP has served a record more than once, the version the pull saw
last is read (`items` come in the order the pull landed them, never by the
highest `seq`) and the others are `files` rows marked "older version".

For a day the old transcript's sections also hold, each old section's
subject is looked for in the day's text (`day_sections`): found in the day's
own text; else in the text of one of the three held days either side (a
sitting under urgency runs past midnight, and the old page carried the whole
sitting where the PDF is one calendar day); a "(continued on …)" note is the
old page's heading for that, never in a PDF; else not found. Both sides are
folded first: case, quotes and dashes, a hyphen broken over a line, runs of
whitespace (pdftotext -layout pads and wraps).

    read_index(items, get_bytes)                        → Result
    read_days(items, get_bytes, subjects, sink)         → Result
"""
import datetime as dt
import json
import re
import unicodedata
from dataclasses import dataclass, field

from support import profiles

READER = "registers.hansard.read_mcp 1"
INDEX, DAYS = "parliament-hansard-index", "parliament-hansard-debates"
PROFILES = {INDEX: "mcp-hansard-index-record", DAYS: "mcp-hansard-debates-record"}
NOTE = ("a record of the query-nz ingest MCP's {corpus} corpus: captured and read off-estate by Arthur's provider "
        "(ruling 78); the estate never fetched parliament.nz")
PDF = re.compile(r"^https://hansard\.parliament\.nz/api/resources/daily/related/(\d{4}-\d\d-\d\d)/[^/]+\.pdf$")
KNOWN = {INDEX: ("bytes", "capture", "date", "fetched", "id", "lastmod", "raw_file", "text", "updated_at", "url"),
         DAYS: ("bytes", "capture", "date", "fetched_at", "http_status", "id", "page_count", "raw_file", "sha256",
                "sitting_date", "text", "title", "updated_at", "url", "word_count")}
NEAR = 3                                          # held days either side looked in for a section of a long sitting


@dataclass
class Result:
    index_pages: list = field(default_factory=list)
    days: list = field(default_factory=list)
    day_sections: list = field(default_factory=list)
    files: list = field(default_factory=list)          # (sha256, name, kind, status)
    set_aside: list = field(default_factory=list)      # (item, stage, reason)
    counts: dict = field(default_factory=dict)


def profile_version(corpus: str) -> int:
    from registers.hansard import read
    slug = PROFILES[corpus]
    p = profiles.profile(slug) or profiles.profile(slug, path=read.PROPOSED)
    if p is None:
        raise LookupError(f"no document profile {slug}")
    return int(p["version"])


def fold(s) -> str:
    s = unicodedata.normalize("NFKC", s or "").lower()
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("–", "-"), ("—", "-")):
        s = s.replace(a, b)
    s = re.sub(r"-[ \t]*\n\s*", "-", s)
    return re.sub(r"\s+", " ", s).strip()


def _str(v):
    return v.strip() if isinstance(v, str) and v.strip() else None


def _int(v):
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def _stamp(v):
    """An ISO time as served, or None (a `Z` read as UTC)."""
    if not isinstance(v, str):
        return None
    try:
        t = dt.datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t.isoformat() if t.tzinfo else None


def _day(v):
    try:
        return dt.date.fromisoformat(v).isoformat() if isinstance(v, str) and len(v) == 10 else None
    except ValueError:
        return None


def recognise(corpus: str, rec) -> str:
    """'' when the document is the corpus's shape, else why not."""
    if not isinstance(rec, dict):
        return "not a JSON object"
    if not _str(rec.get("id")) or not isinstance(rec.get("url"), str):
        return "no id or url"
    if corpus == INDEX:
        if not re.match(r"^https://([a-z0-9-]+\.)*parliament\.nz/", rec["url"]):
            return "its url is not a parliament.nz page"
        return ""
    m = PDF.match(rec["url"])
    if not m:
        return "its url is not a Hansard daily PDF"
    if _day(rec.get("sitting_date")) != m.group(1):
        return "its sitting_date is not the day its PDF's address names"
    if not isinstance(rec.get("text"), str):
        return "no text"
    return ""


def unread(corpus: str, rec: dict) -> list:
    return sorted(set(rec) - set(KNOWN[corpus]))


def current(corpus: str, items, get_bytes, res: Result) -> list:
    """[(sha, record or None, versions, record id)] one per record id, the version the pull saw last; the rest are files rows."""
    last, order = {}, []
    for pos, (sha, _seq, _rid) in enumerate(items):
        if sha not in last:
            order.append(sha)
        last[sha] = pos
    by = {}
    for sha in order:
        try:
            rec = json.loads(get_bytes(sha))
        except (OSError, ValueError) as e:
            res.set_aside.append((sha, "open", f"{corpus}: {type(e).__name__}"))
            res.files.append((sha, corpus, corpus, "set aside"))
            continue
        why = recognise(corpus, rec)
        if why:
            res.set_aside.append((sha, "recognise", f"{corpus}: {why}"))
            res.files.append((sha, corpus, corpus, "set aside"))
            continue
        by.setdefault(rec["id"].strip(), []).append((last[sha], sha, rec if corpus == INDEX else None))
    out = []
    for rid, vs in by.items():
        vs.sort(key=lambda v: v[0])
        for _, sha, _ in vs[:-1]:
            res.files.append((sha, f"{corpus}/{rid}", corpus, "older version"))
        _, sha, rec = vs[-1]
        res.files.append((sha, f"{corpus}/{rid}", corpus, "read"))
        out.append((sha, rec, len(vs), rid))
    return out


def _cite(corpus: str, sha: str, place: str, loaded_at: str) -> dict:
    return {"source_note": NOTE.format(corpus=corpus), "document": sha, "page": 1, "place": place,
            "read_from": "text", "reader": READER, "profile": PROFILES[corpus],
            "profile_version": profile_version(corpus), "loaded_at": loaded_at}


def read_index(items, get_bytes, loaded_at: str = None) -> Result:
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    res = Result()
    for sha, rec, versions, _ in current(INDEX, items, get_bytes, res):
        res.index_pages.append({
            "url": rec["url"], "lastmod": _stamp(rec.get("lastmod")), "fetched": _stamp(rec.get("fetched")),
            "index_on": _day(rec.get("date")), "record": rec["id"], "raw_file": _str(rec.get("raw_file")),
            "versions": versions, "fields_unread": unread(INDEX, rec), **_cite(INDEX, sha, "record", loaded_at)})
    res.counts = {"index documents": len(res.files), "index pages": len(res.index_pages),
                  "index set aside": len(res.set_aside)}
    return res


def where(subject: str, own: str, near: list) -> tuple:
    """(found, neighbour day) for one old section's subject; `near` [(day, folded text)]."""
    sub = fold(subject)
    if not sub:
        return "no subject", None
    if sub.startswith("(continued on"):
        return "continuation note", None
    if sub in own:
        return "own day", None
    for day, text in near:
        if sub in text:
            return "neighbouring day", day
    return "not found", None


def read_days(items, get_bytes, subjects: dict, sink, loaded_at: str = None) -> Result:
    """subjects: {day: [(section key, subject)]} from the old transcript; sink(key, text) takes each day's text."""
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    res = Result()
    chosen = current(DAYS, items, get_bytes, res)
    held = sorted((PDF.match(rid).group(1), sha, v) for sha, _, v, rid in chosen)     # recognised: id is the url
    days = [d for d, _, _ in held]
    want = set()
    for i, d in enumerate(days):
        if d in subjects:
            want.update(days[max(0, i - NEAR): i + NEAR + 1])
    folded, seen = {}, set()
    for d, sha, versions in held:
        if d in seen:
            res.set_aside.append((sha, "read", f"a second record for the sitting day {d}"))
            res.files[:] = [f if f[0] != sha else (sha, f[1], f[2], "set aside") for f in res.files]
            continue
        seen.add(d)
        rec = json.loads(get_bytes(sha))
        text = rec["text"]
        cap = rec.get("capture") if isinstance(rec.get("capture"), dict) else {}
        pick = lambda k: cap.get(k) if cap.get(k) is not None else rec.get(k)   # noqa: E731
        if d in want:
            folded[d] = fold(text)
        sink(d, text)
        res.days.append({
            "key": d, "sitting_on": d, "title": _str(rec.get("title")), "pdf_url": rec["url"],
            "pdf_sha256": _str(pick("sha256")), "pdf_bytes": _int(pick("bytes")), "http_status": _int(pick("http_status")),
            "captured_at": _stamp(pick("fetched_at")), "raw_file": _str(pick("raw_file")),
            "updated_at": _str(rec.get("updated_at")), "page_count": _int(rec.get("page_count")),
            "word_count": _int(rec.get("word_count")), "text_words": len(text.split()), "chars": len(text),
            "versions": versions, "fields_unread": unread(DAYS, rec), "old_sections": None, "old_subjects": None,
            "subjects_in_text": None, **_cite(DAYS, sha, "record", loaded_at)})
    at = {r["key"]: r for r in res.days}
    for i, d in enumerate(days):
        if d not in subjects or d not in at:
            continue
        row = at[d]
        near = [(x, folded[x]) for x in days[max(0, i - NEAR): i + NEAR + 1] if x != d and x in folded]
        n = {"own day": 0, "neighbouring day": 0, "continuation note": 0, "no subject": 0, "not found": 0}
        for key, subject in subjects[d]:
            found, other = where(subject, folded[d], near)
            n[found] += 1
            res.day_sections.append({"key": key, "sitting_on": d, "found": found, "neighbour": other,
                                     "document": row["document"]})
        row["old_sections"] = len(subjects[d])
        row["old_subjects"] = len(subjects[d]) - n["continuation note"] - n["no subject"]
        row["subjects_in_text"] = n["own day"]
    res.counts = {"day documents": len(res.files), "days": len(res.days), "days set aside": len(res.set_aside),
                  "days both hold": sum(1 for r in res.days if r["old_sections"] is not None),
                  "days only the MCP holds": sum(1 for r in res.days if r["old_sections"] is None),
                  "old days the MCP lacks": len(set(subjects) - set(at))}
    return res
