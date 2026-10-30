"""The reading of the ingest MCP's parliament records (three profiles, v1).

A document is one record of a parliament corpus as support/mcpsource
landed it: the record's JSON, keys sorted, without its `seq`. The reading
takes the API's fields as they are, each to a column of its own name: no
model, no inference, nothing fetched (ruling 96: "add their fields to our
registers"). Three shapes:

  written_questions   `parliament-written-questions`, the Parliament API's written questions
  api_items           `parliament-bills`, `-bills-historical`, `-sc-submissions`, `-sc-reports`, `-sops`:
                      the API's one document shape, typed by corpus and `documentType`
  wayback_pages       `parliament-wayback`, parliament.nz pages the provider took from the Internet
                      Archive, the page's text whole

Every text a view publishes whole (the question, the reply, an API
document's `text`, a page's text) gets a flag beside it,
`<column>_names_address`, true where shapes.py finds an address's shape
(ruling 102: a product applies hard limit 15 at its surface by the flag),
and a line in `address_flags` by key.

A record is read from the version the pull landed last (`items` come in
that order), never the highest `seq`: after the MCP removes records, a
re-rendered one comes back at a lower place. The older versions are listed
in `files` without being opened (each arrival row names its record). A
field the lane has no column for, or a value of a type its column cannot
hold, is listed in `fields_unread`, never dropped silently: the check
goes red on it.

An archived page that is parliament.nz's refusal ("Unauthorized Request
Blocked": the Internet Archive kept the site's answer to its crawler, not
the page) is a challenged read, so a failed read (hard limit 6): set aside
with BLOCKED, never a row; the document stays in the store. Known by its
shape, measured on the 4,839 pages of the first full build: the refusal's
title, and a short text that opens with the refusal's heading and says
"Unauthorized Activity Detected" (10 pages, all one 42-word text; the
shortest real page has 81 words, and none carries either phrase). A word
alone never makes a page a refusal.

The records' `text` is the provider's own run of the record's fields (the
written questions' `text` re-rendered for 17,619 records on 26 October
with nothing else changed): its words are counted (`text_words`, what the
MCP's `measure` counts); kept whole for the API documents and the
archived pages, where it is the page's own text.

    read(items, get_bytes, loaded_at=None, sink=None)
        items: [(corpus, sha256, seq or None, record id or None, served)] → Result
"""
import datetime as dt
import json
import re
from dataclasses import dataclass, field

from registers.parliament import shapes

READER = "registers.parliament.read"
PROFILE = {"wq": "mcp-parliament-written-question", "api": "mcp-parliament-api-item",
           "wayback": "mcp-parliament-wayback-page"}
OLDER_TEXT = "older text"       # files: an archived page's older version whose text differs from the version read


def profile_version(shape: str) -> int:
    """The profile's newest version: the ledger's, or the lane's proposed line until the integrator appends it
    (the written questions and the archived pages are at 2, with the text reader's budget; the API items at 1)."""
    from registers.parliament import model_read
    return model_read.profile_version(PROFILE[shape])


PROFILE_VERSION = {shape: profile_version(shape) for shape in PROFILE}
SITE = "https://www.parliament.nz"
SOURCE_NOTE = ("a record of the query-nz ingest MCP's {corpus} corpus: captured off-estate by Arthur's provider "
               "(ruling 78); the estate never fetched parliament.nz")
WAYBACK_NOTE = ("a parliament.nz page as the Internet Archive kept it, taken by Arthur's provider and served in the "
                "query-nz ingest MCP's parliament-wayback corpus (ruling 78); the estate fetched nothing")
BLOCKED = "blocked: the archived copy is the site's refusal (hard limit 6)"
REFUSAL_TITLE = "Unauthorized Request Blocked"
REFUSAL_MARK = "Unauthorized Activity Detected"
REFUSAL_MAX_WORDS = 60           # the refusal's text is 42 words; the shortest real page of the 4,839 has 81
_HOST = re.compile(r"^https?://([a-z0-9-]+\.)*parliament\.nz(:\d+)?(/|$)", re.I)

T, I, J = "text", "int", "json"
WQ_FIELDS = {
    "questionNumber": ("question_number", I), "questionYear": ("question_year", I),
    "parliamentNumber": ("parliament_number", I), "writtenQuestionsDocumentId": ("document_id", T),
    "title": ("title", T), "questionText": ("question_text", T), "replyText": ("reply_text", T),
    "memberId": ("member_id", T), "ministerName": ("minister_name", T),
    "ministerialDisplayName": ("ministerial_display_name", T),
    "portfolioId_PortfolioMinister": ("portfolio_minister_id", T), "roleId": ("role_id", T),
    "statusId": ("status_id", I), "documentType": ("document_type", T),
    "questionReleasedDate": ("question_released_at", T), "date": ("dated", T), "lastModified": ("last_modified", T),
    "attachmentId": ("attachment_id", T), "attachmentName": ("attachment_name", T),
    "attachmentSize": ("attachment_size", I),
}
API_FIELDS = {
    "documentType": ("document_type", T), "itemType": ("item_type", T), "itemSubType": ("item_sub_type", T),
    "title": ("title", T), "shortTitle": ("short_title", T), "billTitle": ("bill_title", T),
    "billNumber": ("bill_number", T), "billCurrentStageName": ("bill_current_stage_name", T),
    "billCurrentStageCode": ("bill_current_stage_code", T), "billCurrentStageId": ("bill_current_stage_id", T),
    "billStage": ("bill_stage", T), "billStages": ("bill_stages", J), "selectCommittee": ("select_committee", T),
    "memberName": ("member_name", T), "partyName": ("party_name", T), "author": ("author", T),
    "people": ("people", J), "publicationDate": ("publication_date", T), "lastStageDate": ("last_stage_date", T),
    "lastModified": ("last_modified", T), "iobClosingDate": ("iob_closing_date", T), "date": ("dated", T),
    "reference": ("reference", T), "url": ("url", T), "titleUrl": ("title_url", T),
    "attachmentId": ("attachment_id", T), "attachmentName": ("attachment_name", T), "duration": ("duration", T),
    "orderNumber": ("order_number", I), "parliamentNumber": ("parliament_number", I), "sop": ("sop", I),
    "state": ("state", T), "status": ("status", T), "subject": ("subject", T), "shoulder": ("shoulder", T),
    "thumbnailUrl": ("thumbnail_url", T), "text": ("text", T), "_collected": ("provider_collected_at", T),
}
WAYBACK_FIELDS = {
    "url": ("url", T), "snapshot_url": ("snapshot_url", T), "ts": ("ts", T), "date": ("dated", T),
    "html_title": ("html_title", T), "doc_type": ("doc_type", T), "kind": ("kind", T), "bytes": ("bytes", I),
    "content_encoding": ("content_encoding", T), "sha256": ("captured_sha256", T), "fetched_at": ("captured_at", T),
    "status": ("capture_status", T), "path": ("provider_path", T), "snapshots": ("snapshots", I),
}
# fields every shape shares: the provider's bookkeeping and blocks, kept whole
COMMON = {"_corpus": ("provider_corpus", T), "_fetched_at": ("provider_fetched_at", T),
          "_shard": ("provider_shard", T), "updated_at": ("updated_at", T), "capture": ("capture", J),
          "annotation": ("annotation", J)}
SHAPE = {"wq": WQ_FIELDS, "api": API_FIELDS, "wayback": WAYBACK_FIELDS}
OWN = {"wq": {"id", "text"}, "api": {"id"}, "wayback": {"id", "text"}}     # read by hand, not by the map
TABLE = {"wq": "written_questions", "api": "api_items", "wayback": "wayback_pages"}
FLAGGED = {"wq": ("question_text", "reply_text"), "api": ("text",), "wayback": ("text",)}   # published whole, flagged


def shape_of(corpus: str) -> str:
    if corpus == "parliament-written-questions":
        return "wq"
    if corpus == "parliament-wayback":
        return "wayback"
    return "api"


def columns(shape: str) -> tuple:
    """The table's columns in order, as tables.sql has them."""
    head = {"wq": ("key",), "api": ("key", "corpus", "record_id"), "wayback": ("key",)}[shape]
    own = {"wq": ("question_released_on", "reply_present", "question_text_names_address", "reply_text_names_address"),
           "api": ("publication_on", "citation_url", "text_names_address"),
           "wayback": ("archived_at", "citation_url", "text", "text_names_address")}[shape]
    return (head + tuple(c for c, _ in SHAPE[shape].values()) + tuple(c for c, _ in COMMON.values()) + own
            + ("text_words", "fields_unread", "versions", "seq", "served", "source_note")
            + ("document", "page", "place", "read_from", "reader", "profile", "profile_version", "loaded_at"))


@dataclass
class Result:
    rows: dict = field(default_factory=lambda: {"written_questions": [], "api_items": [], "wayback_pages": []})
    flags: list = field(default_factory=list)          # (table, key, column, shape): a text naming an address
    files: list = field(default_factory=list)          # (sha256, corpus, record id, seq, status)
    set_aside: list = field(default_factory=list)      # (item, stage, reason)
    older: list = field(default_factory=list)          # (table, key, sha256): older versions whose text differs
    counts: dict = field(default_factory=dict)

    def emit(self, table: str, row: dict) -> None:
        self.rows[table].append(row)

    def emit_flag(self, flag: tuple) -> None:
        self.flags.append(flag)

    def emit_older(self, table: str, row: dict) -> None:
        """An archived page's older version whose text differs from the version read: a document of its own for
        the text reader (the load replays its reading); not a row of the table. Kept here for the proof."""
        self.older.append((table, row["key"], row["document"]))


def _str(v):
    return v.strip() if isinstance(v, str) and v.strip() else None


def _iso_day(v):
    """The day of a stamp the API gives as a bare date or as midnight UTC (how it stores a day); None for any
    other time, which would need a zone to name its day."""
    if not isinstance(v, str) or len(v) < 10:
        return None
    try:
        d = dt.date.fromisoformat(v[:10])
    except ValueError:
        return None
    return d.isoformat() if len(v) == 10 or v[10:].rstrip("Z") in ("T00:00:00", "T00:00:00.000", "T00:00:00+00:00") \
        else None


NUL = "\x00"
NUL_MARK = "\ufffd"


def clean(v):
    """Text as served, but a NUL (which no text column can hold: one archived page carries some) as U+FFFD; the
    document keeps the bytes."""
    return v.replace(NUL, NUL_MARK) if isinstance(v, str) and NUL in v else v


def _value(v, kind: str, name: str, odd: list):
    """The value for a column of `kind`: text as served (a non-text value as its JSON), an integer, or JSON."""
    if v is None:
        return None
    if kind == I:
        if isinstance(v, int) and not isinstance(v, bool):
            return v
        odd.append(f"{name}:{type(v).__name__}")
        return None
    if kind == J:
        return json.dumps(v, ensure_ascii=False, sort_keys=True).replace("\\u0000", "\\ufffd")
    return clean(v) if isinstance(v, str) else json.dumps(v, ensure_ascii=False, sort_keys=True).replace("\\u0000", "\\ufffd")


def citation_url(rec: dict):
    """The page's own address on parliament.nz where the record gives one: its `url`, its capture's `url`, or
    its `titleUrl`, a path made absolute on the site. None where the API gives none (the written questions,
    bills, reports and SOPs): no address is made up."""
    cap = rec.get("capture") if isinstance(rec.get("capture"), dict) else {}
    for u in (rec.get("url"), cap.get("url"), rec.get("titleUrl")):
        if isinstance(u, str) and u.strip():
            u = u.strip()
            if u.startswith("/"):
                return SITE + u
            if _HOST.match(u):
                return u
    return None


def _norm(v) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def refused(rec: dict) -> str:
    """BLOCKED when an archived page is the site's refusal by its shape, '' when it is not. The refusal's title
    over a text that is not the refusal's (measured: none) is set aside too, under its own reason: a block's
    title is never cleared by what follows it."""
    title, text = _norm(rec.get("html_title")), _norm(rec.get("text"))
    short = len(text.split()) <= REFUSAL_MAX_WORDS and text.startswith(REFUSAL_TITLE) and REFUSAL_MARK in text
    if short and title in (REFUSAL_TITLE, ""):
        return BLOCKED
    if title == REFUSAL_TITLE:
        return "the refusal's title over a text that is not the refusal's shape: a failed read (hard limit 6)"
    return ""


def recognise(shape: str, rec) -> str:
    """'' when the document is this profile's shape, else why not."""
    if not isinstance(rec, dict):
        return "not a JSON object"
    if not isinstance(rec.get("id"), (str, int)) or str(rec["id"]).strip() == "":
        return "no id"
    if shape == "wq":
        for f in ("questionNumber", "questionYear"):
            if not isinstance(rec.get(f), int) or isinstance(rec.get(f), bool):
                return f"no `{f}`"
    elif shape == "api":
        if not _str(rec.get("documentType")):
            return "no `documentType`"
    elif not isinstance(rec.get("url"), str) or not _HOST.match(rec["url"]):
        return "its url is not a parliament.nz page"
    else:
        return refused(rec)
    return ""


def read_one(corpus: str, sha: str, rec: dict, seq, versions: int, served: bool, loaded_at: str, out,
             older: bool = False) -> None:
    """One record to its row. `older`: an archived page's older version whose text differs from the version
    read: the row goes to `out.emit_older`, a document for the text reader, never a row of the table."""
    shape = shape_of(corpus)
    rid = str(rec["id"]).strip()
    odd = []
    row = {"key": rid if shape != "api" else f"{corpus}/{rid}"}
    if shape == "api":
        row.update(corpus=corpus, record_id=rid)
    for src, (col, kind) in list(SHAPE[shape].items()) + list(COMMON.items()):
        row[col] = _value(rec.get(src), kind, src, odd)
    known = set(SHAPE[shape]) | set(COMMON) | OWN[shape]
    text = rec.get("text") if isinstance(rec.get("text"), str) else None
    if shape == "wq":
        row["question_released_on"] = _iso_day(rec.get("questionReleasedDate"))
        row["reply_present"] = bool(_str(rec.get("replyText")))
    elif shape == "api":
        row["publication_on"] = _iso_day(rec.get("publicationDate"))
        row["citation_url"] = citation_url(rec)
    else:
        ts = rec.get("ts") if isinstance(rec.get("ts"), str) else ""
        row["archived_at"] = (f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}T{ts[8:10]}:{ts[10:12]}:{ts[12:14]}Z"
                              if re.fullmatch(r"\d{14}", ts) else None)
        row["citation_url"] = rec["url"]
        row["text"] = clean(text)
        if text and NUL in text:
            out.counts["texts with a NUL, kept as U+FFFD"] = out.counts.get("texts with a NUL, kept as U+FFFD", 0) + 1
    for col in FLAGGED[shape]:
        found = shapes.shape(row[col])
        row[f"{col}_names_address"] = found is not None
        if found and not older:
            out.emit_flag((TABLE[shape], row["key"], col, found))
            k = f"{TABLE[shape]}.{col} names an address"
            out.counts[k] = out.counts.get(k, 0) + 1
    if rec.get("text") is not None and text is None:
        odd.append(f"text:{type(rec['text']).__name__}")
    row.update({"text_words": len(text.split()) if text else 0,
                "fields_unread": sorted(set(rec) - known - {"seq"}) + odd, "versions": versions, "seq": seq,
                "served": served,
                "source_note": WAYBACK_NOTE if shape == "wayback" else SOURCE_NOTE.format(corpus=corpus),
                "document": sha, "page": 1, "place": "record", "read_from": "text", "reader": READER,
                "profile": PROFILE[shape], "profile_version": PROFILE_VERSION[shape], "loaded_at": loaded_at})
    if older:
        out.emit_older(TABLE[shape], row)
    else:
        out.emit(TABLE[shape], row)


def older_text(corpus: str, sha: str, texts: set, opened: dict, get_bytes, loaded_at: str, out) -> bool:
    """Older snapshots of one archived page are versions of one document: the newest served version is read,
    and an older one only where its text differs from the newest's and from every later version's (then it is
    a document of its own for the text reader, given to `out.emit_older`). `texts`: the normalised texts seen
    so far, added to. A written question's older versions are the provider's re-rendered `text` with the
    question and reply unchanged: never opened. True when the older version is read."""
    if texts is None:
        return False
    try:
        rec = opened.pop(sha) if sha in opened else json.loads(get_bytes(sha))
    except (OSError, ValueError):
        return False
    if not isinstance(rec, dict) or recognise("wayback", rec) or _norm(rec.get("text")) in texts:
        return False
    texts.add(_norm(rec.get("text")))
    read_one(corpus, sha, rec, None, 1, False, loaded_at, out, older=True)
    out.counts[OLDER_TEXT] = out.counts.get(OLDER_TEXT, 0) + 1
    return True


def read(items, get_bytes, loaded_at: str = None, out: Result = None) -> Result:
    """Every document in `items` read, listed as an older version, or set aside. `out` may be any object with
    Result's fields and `emit`/`emit_flag` (the load streams rows to the tables)."""
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    out = out if out is not None else Result()
    n = out.counts
    last, info, opened = {}, {}, {}
    for pos, (corpus, sha, seq, rid, served) in enumerate(items):
        last[(corpus, sha)] = pos
        info[(corpus, sha)] = (seq, rid, served)
    by_record = {}
    for corpus, sha in sorted(last, key=last.get):
        seq, rid, served = info[(corpus, sha)]
        if rid is None:                       # the sample names hashes only: the record says which it is
            try:
                rec = json.loads(get_bytes(sha))
            except (OSError, ValueError) as e:
                out.set_aside.append((sha, "open", f"{type(e).__name__}: {str(e)[:200]}"))
                out.files.append((sha, corpus, None, seq, "set aside"))
                continue
            opened[sha] = rec
            rid = str(rec.get("id")).strip() if isinstance(rec, dict) and rec.get("id") is not None else None
            if rid is None:
                out.set_aside.append((sha, "recognise", "no id"))
                out.files.append((sha, corpus, None, seq, "set aside"))
                continue
        by_record.setdefault((corpus, rid), []).append(sha)
    for (corpus, rid), shas in by_record.items():
        sha = shas[-1]                         # the version the pull landed last
        seq, _, served = info[(corpus, sha)]
        try:
            rec = opened.pop(sha) if sha in opened else json.loads(get_bytes(sha))
        except (OSError, ValueError) as e:
            out.files += [(s, corpus, rid, info[(corpus, s)][0], "older version") for s in shas[:-1]]
            out.set_aside.append((sha, "open", f"{type(e).__name__}: {str(e)[:200]}"))
            out.files.append((sha, corpus, rid, seq, "set aside"))
            continue
        texts = {_norm(rec.get("text"))} if shape_of(corpus) == "wayback" else None
        for s in reversed(shas[:-1]):          # the later snapshot first: an earlier one with the same text is a copy
            out.files.append((s, corpus, rid, info[(corpus, s)][0],
                              OLDER_TEXT if older_text(corpus, s, texts, opened, get_bytes, loaded_at, out) else "older version"))
        why = recognise(shape_of(corpus), rec)
        if not why and str(rec["id"]).strip() != rid.strip():       # an id may end in a space (one call for submissions)
            why = "the arrival names another record"
        if why:
            if why == BLOCKED:
                n["blocked"] = n.get("blocked", 0) + 1
            out.set_aside.append((sha, "recognise", why))
            out.files.append((sha, corpus, rid, seq, "set aside"))
            continue
        read_one(corpus, sha, rec, seq, len(shas), bool(served), loaded_at, out)
        out.files.append((sha, corpus, rid, seq, "read"))
        n[corpus] = n.get(corpus, 0) + 1
        if not served:
            n["withdrawn by the source"] = n.get("withdrawn by the source", 0) + 1
    n["documents"] = len(last)
    n["records"] = sum(1 for f in out.files if f[4] == "read")
    n["older versions"] = sum(1 for f in out.files if f[4] in ("older version", OLDER_TEXT))
    n["set aside"] = len(out.set_aside)
    return out
