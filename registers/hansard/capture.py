"""How this lane's documents arrive (plan 1.10, case two: only text is held).

The old estate captured Parliament's Hansard transcripts (one page per
sitting day at hansard.parliament.nz/hansard-transcript/<date>, cut into
sections) from 20 November 2024 until the site's challenge of about
5 October 2026, and held them as rows, not files: in the news database
`incoming_news.hansard_sections` (each section's text and the speakers it
read, as labelled on the page and as its roster resolved them) and
`hansard_members` (that roster), and in the canonical database its
derivations `registers.hansard_sittings` (one per sitting day, with its
own counts) and `registers.hansard_speeches` (one per sitting, section and
member). All four were exported once, on 26 October 2026, to one
JSON-lines file (`export_hansard`), the way registers/gazette/capture.py
exported the Gazette's notices, and that file is the document: every row
read from it is "taken from the old estate's tables; original not held",
and cites the export's hash, the sitting day and section, and the page's
own address. The hash is pinned here; a second export would be a new
document and a new pin. Nothing is fetched (ruling 78: the estate does not
capture Hansard), and the export is never run at load.

One line per row, `kind` first in the sort: `member`, `section`,
`sitting`, `speech`, each sorted by its own key, so the bytes are the same
for the same rows.

    export_hansard()         the export's bytes, read through the old read-only login
    copy_all(conn)           land the export: ([(kind, DocumentRef, name, captured at)], [(item, why)])
    python -m registers.hansard.capture --export PATH    write the export once
"""
import datetime as dt
import json
import os
import sys

from support.docstore.landing import land, path_for, read_bytes

SOURCE = "hansard"
EXPORT_NAME = "hansard-2026-10-26.jsonl"
EXPORT_SHA = "c912d9bc23c54c2593cfc512f422d29d1856b65e091239687e2fca497f66ac3b"
EXPORTED_AT = "2026-10-26T18:43:16+13:00"
EXPORT_NOTE = "taken from the old estate's tables; original not held"
KINDS = ("member", "section", "sitting", "speech")

#: All four tables are the OLD databases', reached through the old read-only
#: login; each query names its old schema so it is not mistaken for one into
#: this estate's hansard lane (tests/test_imports_one_way.py).
_MEMBERS_SQL = "SELECT member_id, display_name, sort_name, parliaments FROM public.hansard_members"
_SECTIONS_SQL = """
SELECT id::text, sitting_date::text, section_index, parliament, volume, proceeding, subject, bill_title, bill_id,
       body_text, char_count, speakers, speech_count, url, source, status, progress, body_hash,
       fetched_at
  FROM public.hansard_sections
"""
_SITTINGS_SQL = """
SELECT sitting_date::text, parliament, volume, progress, sections, speeches, speakers, resolved, unresolved,
       unattributed, derived_at
  FROM registers.hansard_sittings
"""
_SPEECHES_SQL = """
SELECT id, sitting_date::text, section_index, member_id, speaker_label, speaker_name, in_roster, speech_count,
       proceeding, subject, bill_id, bill_title, progress, url, derived_at, retired_at
  FROM registers.hansard_speeches
"""


def _iso(v):
    return v.isoformat() if isinstance(v, (dt.datetime, dt.date)) else v


def _line(kind: str, row: dict) -> str:
    return json.dumps({"kind": kind, **{k: _iso(v) for k, v in row.items()}}, ensure_ascii=False, sort_keys=True)


def _rows(conn, sql: str) -> list:
    cur = conn.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur]


def lines_of(members: list, sections: list, sittings: list, speeches: list) -> bytes:
    """The export's bytes from the four tables' rows (dicts): one sorted
    line per row, renamed where a name would mislead (`id` is the old row's
    id, `body_text` the section's text)."""
    out = []
    for m in members:
        out.append((0, m["member_id"], "", _line("member", m)))
    for s in sections:
        s = dict(s)
        s["old_id"], s["text"] = s.pop("id"), s.pop("body_text") or ""
        out.append((1, s["sitting_date"], f"{s['section_index']:06d}", _line("section", s)))
    for s in sittings:
        out.append((2, _iso(s["sitting_date"]), "", _line("sitting", s)))
    for s in speeches:
        s = dict(s)
        s["old_id"] = s.pop("id")
        out.append((3, s["sitting_date"], f"{s['section_index']:06d} {s['member_id'] or ''} {s['old_id']:012d}",
                    _line("speech", s)))
    out.sort()
    return ("\n".join(l for *_, l in out) + "\n").encode("utf-8")


def export_hansard(connect=None) -> bytes:
    """The four tables, read-only, every statement under a time limit; run once."""
    from support import db
    connect = connect or (lambda name: db.connect(db.OLD_READ_KEY, name, connect_timeout=10))
    with connect("incoming_news") as c:
        c.execute("SET statement_timeout = '60s'")
        members, sections = _rows(c, _MEMBERS_SQL), _rows(c, _SECTIONS_SQL)
    with connect("nzbn_canonical") as c:
        c.execute("SET statement_timeout = '60s'")
        sittings, speeches = _rows(c, _SITTINGS_SQL), _rows(c, _SPEECHES_SQL)
    return lines_of(members, sections, sittings, speeches)


def copy_all(conn, export_sha: str = None, log=None) -> tuple:
    """The export landed from the store. Returns
    ([(kind, DocumentRef, name, captured at)], [(item, why)])."""
    sha = export_sha or EXPORT_SHA
    if not sha or not os.path.exists(path_for(sha)):
        raise LookupError(f"the Hansard export {sha or '(not pinned)'} is not in the document store")
    ref, new = land(read_bytes(sha), name=EXPORT_NAME, source=SOURCE, conn=conn, fetched_at=EXPORTED_AT)
    if log:
        log(f"hansard: {'landed' if new else 'held'} {ref.sha256[:12]} {EXPORT_NAME}")
    return [("hansard", ref, EXPORT_NAME, EXPORTED_AT)], []


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if "--export" not in argv:
        print("usage: python -m registers.hansard.capture --export PATH")
        return 2
    path = argv[argv.index("--export") + 1]
    if os.path.exists(path):
        print(f"{path} exists: the export is run once")
        return 1
    data = export_hansard()
    with open(path, "wb") as f:
        f.write(data)
    from support.docstore import sha256_file
    n = {k: data.count(f'"kind": "{k}"'.encode()) for k in KINDS}
    print(f"{path}: {data.count(b'\n')} lines {n}, sha256 {sha256_file(path)}, "
          f"{dt.datetime.now().astimezone().isoformat(timespec='seconds')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
