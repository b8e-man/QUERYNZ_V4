"""The GETS listing as the ingest MCP serves it (rulings 96, 138): profile `mcp-gets-tender-notice`, v1.

A document is one record of the MCP's `gets` corpus as support/mcpsource landed it: the record's JSON, keys
sorted, without its `seq`. Each record is one tender notice's page on GETS (`ExternalTenderDetails.htm?id=…`),
which Arthur's provider crawled and read on its own box, outside the estate (ruling 78); the estate never fetched
GETS (its terms bar a spider: position `government-electronic-tenders-listing`). The record's field names are the
provider's courts reader's (`case_name` is the tender's name, `case_slug` its RFx ID, `court` the corpus, always
`gets`), kept here under the tender's words. From 4 November the record carries the page's own fields too
(`page_fields`, with `open_date`, `categories`, `coverage`, `prequalifications` lifted out by the provider): the
block is kept whole, and each of its stable labels has a column. GETS prints the regions as the label of the field
after them ("Regions: Auckland Nelson Exemption Reason"), so the block's keys are open-ended (the shape's `open`):
the regions are read from that label, the label's tail (`Exemption Reason`, `Required Pre-qualifications`) and its
value beside them, and any label the lane has no column for is listed in `page_labels_unread`.

The reading takes the fields as served: no model, no inference, nothing fetched. A record is read from the version
the pull landed last (`items` come in that order, never the highest `seq`); the others are counted as `versions`.
The buyer's contact (a person: name, phone, email), the agency's and the delivery addresses, the fax and the
provider's `text` and the page's block whole go to the private twin (ruling 142: everything kept; the tenders
schema holds no address).

    read(items, get_bytes, loaded_at=None)   items: [(sha256, seq or None, record id or None)] → Result
    load(conn, schema, mcp_schema)            the tables under `schema`, rebuilt in one transaction
    python -m registers.tenders.listing [--job | --schema scratch_tenders_listing]
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
from dataclasses import dataclass, field

READER = "registers.tenders.listing"
PROFILE = "mcp-gets-tender-notice"
PROFILE_VERSION = 1
CORPUS = "gets"
JOB = "qv4-tenders-listing-load"
SCHEMA, PRIVATE = "tenders", "tenders_private"
HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_NOTE = ("a GETS tender notice's page, crawled and read by Arthur's provider off-estate and served by the "
               "query-nz ingest MCP's gets corpus (rulings 78, 138); the estate never fetched GETS")

#: the record's top-level fields → the column each lands in (ruling 96: their fields in our registers)
FIELDS = {
    "id": "key", "case_slug": "rfx_id", "case_name": "tender_name", "buyer_org": "buyer", "tender_type": "tender_type",
    "reference_no": "reference_no", "close_date": "close_date", "open_date": "open_date", "categories": "categories",
    "coverage": "coverage", "prequalifications": "prequalifications", "discovered_via": "listed_as",
    "court": "provider_corpus", "kind": "kind", "url": "url", "content_type": "content_type", "bytes": "page_bytes",
    "sha256": "page_sha256", "path": "provider_path", "file": "provider_file", "http_status": "http_status",
    "fetched_at": "fetched_at", "date": "arrival_date", "updated_at": "updated_at", "http_headers": "http_headers",
    "capture": "capture", "file_uri": "provider_file_uri", "tender_id": "provider_tender_id",
    "tender_name": "provider_tender_name",
}
#: kept in the private twin: the provider's text, the page's block whole
PRIVATE_FIELDS = {"text": "text", "page_fields": "page_fields"}
#: the page's stable labels → the column each lands in; the private ones (a person, an address) in the twin
LABELS = {
    "RFx ID": "page_rfx_id", "Tender Name": "page_tender_name", "Tender Type": "page_tender_type",
    "Open Date": "page_open_date", "Close Date": "page_close_date", "Overview": "overview",
    "Categories": "page_categories", "Tender Coverage": "page_coverage", "Reference #": "page_reference",
    "Required Pre-qualifications": "page_prequalifications", "Department/Business Unit": "department",
    "Justification": "justification", "Indicative Total Value": "indicative_total_value",
    "Project Status": "project_status", "Expected number of contracts offered": "expected_contracts",
    "Indicative RFx Release Date": "indicative_release_date",
}
PRIVATE_LABELS = {"Contact": "contact", "Agency Address": "agency_address",
                  "Alternate Physical Delivery Address": "delivery_address",
                  "Alternate Physical Fax Number": "delivery_fax"}
#: what GETS prints after the regions, run into their label
REGION_TAILS = ("Exemption Reason", "Required Pre-qualifications")
REGIONS = ("Auckland", "Bay of Plenty", "Canterbury", "Chatham Islands", "Gisborne", "Hawke's Bay",
           "Manawatu-Wanganui", "Marlborough", "Nelson", "Northland", "Otago", "Southland", "Taranaki", "Tasman",
           "Waikato", "Wellington", "West Coast", "New Zealand", "International")   # the last two as GETS prints them
NO_REGIONS = ("N/A",)                                                         # printed where a notice names none
_REGION = re.compile("|".join(re.escape(r) for r in sorted(REGIONS, key=len, reverse=True)))
JSON_COLUMNS = ("http_headers", "capture", "regions", "page_labels_unread", "fields_unread", "page_fields")
STAMP = ("document", "page", "place", "read_from", "reader", "profile", "profile_version", "loaded_at")
COLUMNS = {
    "listing": tuple(c for c in FIELDS.values()) + tuple(LABELS.values()) + (
        "regions", "regions_as_printed", "regions_unread", "regions_tail", "regions_tail_value", "page_labels_unread",
        "text_words", "fields_unread", "versions", "seq", "source_note") + STAMP,
    "listing_set_aside": ("item", "stage", "reason"),
}
PRIVATE_COLUMNS = {"listing": ("key",) + tuple(PRIVATE_LABELS.values()) + tuple(PRIVATE_FIELDS.values()) + ("document",)}


@dataclass
class Result:
    rows: list = field(default_factory=list)
    private: list = field(default_factory=list)
    set_aside: list = field(default_factory=list)     # (item, stage, reason)
    counts: dict = field(default_factory=dict)


def _str(v):
    return v.strip() if isinstance(v, str) and v.strip() else None


def _int(v):
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def recognise(rec) -> str:
    """'' when the document is this profile's shape, else why not."""
    if not isinstance(rec, dict):
        return "not a JSON object"
    if not _str(rec.get("id")):
        return "no id"
    if rec.get("kind") != "tender_notice":
        return f"kind {rec.get('kind')!r}, not a tender notice"
    if rec.get("page_fields") is not None and not isinstance(rec["page_fields"], dict):
        return "`page_fields` is not a block"
    return ""


def regions_of(label: str) -> tuple:
    """(regions in the order printed, the label as printed after `Regions:`, what no region name matched, the tail)
    for a page label that opens with `Regions:`."""
    s = label[len("Regions:"):].strip()
    tail = next((t for t in REGION_TAILS if s.endswith(t)), None)
    if tail:
        s = s[:-len(tail)].strip()
    if s in NO_REGIONS:
        return [], s, None, tail
    found = _REGION.findall(s)
    rest = _REGION.sub(" ", s).split()
    return found, s, " ".join(rest) or None, tail


def read_one(sha: str, rec: dict, seq, versions: int, out: Result, loaded_at: str) -> None:
    n = out.counts
    pf = rec.get("page_fields") if isinstance(rec.get("page_fields"), dict) else {}
    row = {col: rec.get(f) for f, col in FIELDS.items()}
    for col in ("key", "rfx_id", "tender_name", "buyer", "tender_type", "reference_no", "close_date", "open_date",
                "categories", "coverage", "prequalifications", "listed_as", "provider_corpus", "kind", "url",
                "content_type", "page_sha256", "provider_path", "provider_file", "fetched_at", "arrival_date",
                "updated_at", "provider_file_uri", "provider_tender_id", "provider_tender_name"):
        row[col] = _str(row[col]) if not isinstance(row[col], (int, float)) else str(row[col])
    for col in ("page_bytes", "http_status"):
        row[col] = _int(row[col])
    for col in ("http_headers", "capture"):
        row[col] = row[col] if isinstance(row[col], dict) else None
    row.update({col: _str(pf.get(label)) for label, col in LABELS.items()})
    regions, printed, unread_regions, tail, tail_value, labels_unread = [], None, None, None, None, []
    for label, value in pf.items():
        if label.startswith("Regions:"):
            if printed is not None:
                _bump(n, "records with more than one regions label")
                labels_unread.append(label)
                continue
            regions, printed, unread_regions, tail = regions_of(label)
            tail_value = _str(value)
        elif label not in LABELS and label not in PRIVATE_LABELS:
            labels_unread.append(label)
    if unread_regions:
        _bump(n, "regions labels with words no region name matched")
    if labels_unread:
        _bump(n, "records with a page label unread")
    known = set(FIELDS) | set(PRIVATE_FIELDS) | {"seq"}
    unread = sorted(set(rec) - known)
    if unread:
        _bump(n, "records with a field unread")
    row.update({"regions": regions, "regions_as_printed": printed, "regions_unread": unread_regions,
                "regions_tail": tail, "regions_tail_value": tail_value, "page_labels_unread": sorted(labels_unread),
                "text_words": len(rec["text"].split()) if isinstance(rec.get("text"), str) else 0,
                "fields_unread": unread, "versions": versions, "seq": seq, "source_note": SOURCE_NOTE,
                "document": sha, "page": 1, "place": "record", "read_from": "text", "reader": READER,
                "profile": PROFILE, "profile_version": PROFILE_VERSION, "loaded_at": loaded_at})
    out.rows.append(row)
    priv = {"key": row["key"], "document": sha, "text": rec.get("text") if isinstance(rec.get("text"), str) else None,
            "page_fields": pf or None}
    priv.update({col: _str(pf.get(label)) for label, col in PRIVATE_LABELS.items()})
    out.private.append(priv)


def _bump(n: dict, k: str, by: int = 1) -> None:
    n[k] = n.get(k, 0) + by


def read(items, get_bytes, loaded_at: str = None) -> Result:
    """Every document in `items` (in the order the pull saw them) read or set aside: one row per record id, from the
    version the pull saw last."""
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    out = Result()
    last, seqs, order = {}, {}, []
    for pos, (sha, seq, _rid) in enumerate(items):
        if sha not in last:
            order.append(sha)
        last[sha], seqs[sha] = pos, seq
    by_record = {}
    for sha in order:
        try:
            rec = json.loads(get_bytes(sha))
        except (OSError, ValueError) as e:
            out.set_aside.append({"item": sha, "stage": "open", "reason": f"{type(e).__name__}: {str(e)[:200]}"})
            continue
        why = recognise(rec)
        if why:
            out.set_aside.append({"item": sha, "stage": "recognise", "reason": why})
            continue
        by_record.setdefault(rec["id"].strip(), []).append((last[sha], sha, rec))
    for versions in by_record.values():
        versions.sort(key=lambda v: v[0])
        _, sha, rec = versions[-1]
        read_one(sha, rec, seqs[sha], len(versions), out, loaded_at)
    out.counts.update({"documents": len(order), "notices": len(out.rows), "set aside": len(out.set_aside),
                       "older versions": sum(len(v) - 1 for v in by_record.values()),
                       "with page fields": sum(1 for r in out.private if r["page_fields"]),
                       "with regions": sum(1 for r in out.rows if r["regions"])})
    return out


# ── the tables ───────────────────────────────────────────────────────────────────────────────────────────────────
def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def sql(schema: str) -> str:
    with open(os.path.join(HERE, "listing.sql"), encoding="utf-8") as f:
        text = f.read()
    return re.sub(r"(?<![A-Za-z0-9_])tenders(_private)?\.",
                  lambda m: f"{private_of(schema) if m.group(1) else schema}.", text)


def arrivals(conn, mcp_schema: str = "mcpsource") -> list:
    """Every gets record the pull has taken, by `landed_at` then `seq`: the last a record appears is its current
    version. A schema with no pull record answers nothing."""
    if not conn.execute("SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND table_name = 'arrivals'",
                        (mcp_schema,)).fetchone():
        return []
    return [tuple(r) for r in conn.execute(f"SELECT sha256, seq, record_id FROM {mcp_schema}.arrivals "
                                           "WHERE corpus = %s ORDER BY landed_at, seq", (CORPUS,))]


def _copy(conn, name: str, cols: tuple, rows) -> int:
    n = 0
    with conn.cursor().copy(f"COPY {name} ({', '.join(chr(34) + c + chr(34) for c in cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(tuple(json.dumps(row.get(c), ensure_ascii=False) if c in JSON_COLUMNS and row.get(c) is not None
                               else row.get(c) for c in cols))
            n += 1
    return n


def load(conn, schema: str, items, get_bytes, loaded_at: str = None) -> dict:
    """The listing's tables under `schema` (and its private twin), dropped and made again and filled, in the caller's
    transaction. Items in equal rows plus older versions plus items set aside, or it raises."""
    r = read(items, get_bytes, loaded_at)
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {private_of(schema)}")
    for t in COLUMNS:
        conn.execute(f"DROP TABLE IF EXISTS {schema}.{t} CASCADE")
    conn.execute(f"DROP TABLE IF EXISTS {private_of(schema)}.listing CASCADE")
    conn.execute(sql(schema))
    n = _copy(conn, f"{schema}.listing", COLUMNS["listing"], r.rows)
    _copy(conn, f"{schema}.listing_set_aside", COLUMNS["listing_set_aside"], r.set_aside)
    _copy(conn, f"{private_of(schema)}.listing", PRIVATE_COLUMNS["listing"], r.private)
    if r.counts["documents"] != n + r.counts["older versions"] + len(r.set_aside):
        raise RuntimeError(f"tenders listing: {r.counts['documents']} documents but {n} rows, "
                           f"{r.counts['older versions']} older versions and {len(r.set_aside)} set aside")
    return r.counts


def job(log=print) -> int:
    """qv4-tenders-listing-load: the listing read again from every gets record the pull holds, into `tenders`, in one
    transaction (a reader sees the old tables until it commits)."""
    from support import db, jobrun
    from support.docstore.landing import read_bytes
    started = jobrun.now()
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '600s'")
        with conn.transaction():
            counts = load(conn, SCHEMA, arrivals(conn), read_bytes)
    detail = ", ".join(f"{k} {v}" for k, v in counts.items())
    ok = counts["notices"] > 0 and not counts.get("records with a field unread")
    log(f"tenders listing: {'ok' if ok else 'RED'}: {detail}")
    jobrun.record(JOB, ok, detail, started, counts)
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m registers.tenders.listing")
    ap.add_argument("--job", action="store_true", help="qv4-tenders-listing-load: into tenders on querynz_v4")
    ap.add_argument("--schema", default="scratch_tenders_listing")
    a = ap.parse_args(argv)
    if a.job:
        return job()
    from support import db
    from support.docstore.landing import read_bytes
    if not a.schema.startswith("scratch_"):
        print("tenders listing: a session loads only a scratch schema")
        return 2
    with db.connect(db.READ_KEY, "querynz_v4") as src:
        items = arrivals(src)
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        with conn.transaction():
            counts = load(conn, a.schema, items, read_bytes)
    for k, v in counts.items():
        print(f"tenders listing: {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
