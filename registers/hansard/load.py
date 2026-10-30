"""Loading (plan 1b.7). The merge gate's staging step calls `load` to build
this lane's tables under a staging schema of the real database, and
`publish` to move the rows into the lane's own tables in one transaction
and refresh the published views. `fill` in sample.py uses the same pieces.

Land the export (never run it: capture.py was run once), read it, copy the
rows in. Items in equal items out plus items set aside (read.py says how).
Then the MCP's two corpora as support/mcpsource landed them (read_mcp.py):
`index_pages` from `parliament-hansard-index`, `days` and `day_subjects`
from `parliament-hansard-debates`, each day's text into the private twin.
As each day's text passes, the split rule of profile `hansard-day`
(split.py, no model) cuts it into `day_sections` and `day_turns`, the
member of each turn matched to the old roster within the day's Parliament,
and the counts go beside the day; a text the rule cannot split is set aside
at stage `read`, named. Then the text reader's stored readings
(model_read.py, replayed and never asked for here, ruling 50): the day's
joined reading into `readings` (one row a piece) and `people` (one row a
name); a day without one is "waiting: text reader". Items in (the
documents) equal rows read plus older versions plus items set aside; the
pull's own catch lines come across as set-aside lines at stage `pull`.
`qv4-hansard-load` runs the same after each night's pull.

    python -m registers.hansard.load                    stage and publish (the job)
    python -m registers.hansard.load --database querynz_v4_sample --schema S [--mcp-database querynz_v4]    a scratch proof
"""
import argparse
import datetime as dt
import json
import os
import sys
import tempfile

from support import jobrun
from support import reader as rd
from support.docstore.landing import read_bytes
from registers.hansard import capture, model_read, read, read_mcp, split as S

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "hansard"
PRIVATE = "hansard_private"
JOB = "qv4-hansard-load"
TABLES = ("sittings", "sections", "turns", "members", "old_speeches", "index_pages", "days", "day_subjects",
          "day_sections", "day_turns", "readings", "people", "files", "set_aside")
PRIVATE_TABLES = ("day_texts",)
CITE = ("source_note", "document", "page", "place", "read_from", "reader", "profile", "profile_version")
SPLIT_NOTE = ("the daily PDF's text as the provider read it, cut into sections and speaker turns by the split rule of "
              "profile hansard-day (no model); the member from the old roster")
WAIT_TEXT = "waiting: text reader"
COLUMNS = {
    "sittings": ("key", "sitting_on", "parliament", "volume", "progress", "url", "sections", "turns", "attributed",
                 "unattributed", "speakers", "old_sections", "old_speeches", "old_unattributed", "old_speakers",
                 "old_derived_at", "captured_at") + CITE,
    "sections": ("key", "sitting_on", "section_index", "parliament", "volume", "proceeding", "subject", "bill_title",
                 "bill_id", "progress", "old_status", "text", "chars", "text_sha1", "turns", "url", "captured_at",
                 "old_id") + CITE,
    "turns": ("key", "section", "sitting_on", "section_index", "ordinal", "label", "member_id", "roster_name", "role",
              "in_roster") + CITE,
    "members": ("key", "display_name", "sort_name", "parliaments") + CITE,
    "old_speeches": ("key", "sitting_on", "section_index", "member_id", "speaker_label", "speaker_name",
                     "speech_count", "retired_at", "document"),
    "index_pages": ("url", "lastmod", "fetched", "index_on", "record", "raw_file", "versions", "fields_unread") + CITE
                   + ("loaded_at",),
    "days": ("key", "sitting_on", "title", "pdf_url", "pdf_sha256", "pdf_bytes", "http_status", "captured_at",
             "raw_file", "updated_at", "page_count", "word_count", "text_words", "chars", "versions", "fields_unread",
             "old_sections", "old_subjects", "subjects_in_text", "layout", "parliament", "sections", "turns",
             "attributed", "unattributed", "speakers", "split_rule", "reading", "pieces", "names", "unusable_pieces")
            + CITE + ("loaded_at",),
    "day_subjects": ("key", "sitting_on", "found", "neighbour", "document"),
    "day_sections": ("key", "sitting_on", "section_index", "layout", "heading", "proceeding", "subject", "bill_title",
                     "chars", "turns", "attributed", "unattributed") + CITE,
    "day_turns": ("key", "section", "sitting_on", "section_index", "ordinal", "label", "name", "role_text", "party",
                  "electorate", "role", "first_speech", "member_id", "roster_name", "match_basis", "in_roster", "chars")
                 + CITE,
    "readings": ("key", "day", "sitting_on", "piece", "section", "part", "parts", "chars", "turns", "names", "summary",
                 "truncated", "unusable", "model", "reader", "made_at", "document", "profile", "profile_version",
                 "loaded_at"),
    "people": ("key", "name", "kind", "role", "role_text", "of", "day", "sitting_on", "section", "piece", "source_note",
               "document", "page", "place", "read_from", "reader", "model", "profile", "profile_version", "loaded_at"),
}


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t`; in a schema every module shares (the sample's), the
    lane's tables carry its name: `schema.hansard_t`."""
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


def sql(name: str, schema: str = SCHEMA, shared: bool = False) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    pre = f"{SCHEMA}_" if shared else ""
    text = text.replace(f"CREATE SCHEMA IF NOT EXISTS {PRIVATE};", f"CREATE SCHEMA IF NOT EXISTS {private_of(schema)};")
    text = text.replace(f"{PRIVATE}.", f"{private_of(schema)}.{pre}")
    text = text.replace(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};", f"CREATE SCHEMA IF NOT EXISTS {schema};")
    text = text.replace(f"{SCHEMA}.", f"{schema}.{pre}")
    if shared:   # index names are schema-wide: the lane's prefix keeps them apart in the shared schema
        text = text.replace("CREATE INDEX IF NOT EXISTS ", f"CREATE INDEX IF NOT EXISTS {SCHEMA}_")
    return text


def create_tables(conn, schema: str, shared: bool = False) -> None:
    """The lane's tables as tables.sql has them now, made again on every
    build: every row is rebuilt from documents."""
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {private_of(schema)}")
    for t in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(schema, t, shared)} CASCADE")
    for t in PRIVATE_TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(private_of(schema), t, shared)} CASCADE")
    conn.execute(sql("tables.sql", schema, shared))


def _copy(conn, name: str, cols: tuple, rows) -> None:
    with conn.cursor().copy(f"COPY {name} ({', '.join(chr(34) + c + chr(34) for c in cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(tuple(row.get(c) for c in cols))


def _lines(path: str):
    with open(path, encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


# ── the split of each day ─────────────────────────────────────────────────────────────────────────────────────
class Splitter:
    """Cuts each day's text as it passes the sink, writing the section and turn rows to two scratch files (a day's
    text is never held after its rows are made; a whole corpus of rows is never held in memory) and keeping each
    day's counts and reasons for the days rows."""

    def __init__(self, roster: S.Roster, version: int, loaded_at: str, budget: int):
        self.roster, self.version, self.loaded_at, self.budget = roster, version, loaded_at, budget
        self.counts, self.aside = {}, []                 # day → counts; (day, reason)
        self._dir = tempfile.mkdtemp(prefix="hansard-split-")
        self.sections_path = os.path.join(self._dir, "sections.jsonl")
        self.turns_path = os.path.join(self._dir, "turns.jsonl")
        self._sections = open(self.sections_path, "w", encoding="utf-8")
        self._turns = open(self.turns_path, "w", encoding="utf-8")

    def cite(self, sha: str, place: str) -> dict:
        return {"source_note": SPLIT_NOTE, "document": sha, "page": 1, "place": place, "read_from": "text",
                "reader": S.RULE, "profile": model_read.PROFILE, "profile_version": self.version}

    def take(self, day: str, text: str, sha: str) -> None:
        d = S.split(text, day, self.roster)
        if d.reason:
            self.aside.append((day, f"the hansard-day split rule cannot cut it: {d.reason}"))
            self.counts[day] = {"layout": d.layout, "parliament": d.parliament}
            return
        over = S.unsplittable(d, self.budget)
        if over:
            self.aside.append((day, f"piece {over[0].number} (section {over[0].section}) is {over[0].chars} characters, "
                                    f"over the reader's budget of {self.budget} after every cut"))
        for sec in d.sections:
            att = sum(1 for t in sec.turns if t.member_id)
            key = f"{day}/{sec.index}"
            self._sections.write(json.dumps({
                "key": key, "sitting_on": day, "section_index": sec.index, "layout": d.layout,
                "heading": " / ".join(sec.heading) or None, "proceeding": sec.proceeding, "subject": sec.subject,
                "bill_title": sec.bill_title, "chars": len(sec.text), "turns": len(sec.turns), "attributed": att,
                "unattributed": len(sec.turns) - att, **self.cite(sha, f"day {day} section {sec.index}")},
                ensure_ascii=False) + "\n")
            for t in sec.turns:
                self._turns.write(json.dumps({
                    "key": f"{key}/{t.ordinal}", "section": key, "sitting_on": day, "section_index": sec.index,
                    "ordinal": t.ordinal, "label": t.label, "name": t.name, "role_text": t.role_text, "party": t.party,
                    "electorate": t.electorate, "role": t.role, "first_speech": t.caps, "member_id": t.member_id,
                    "roster_name": t.roster_name, "match_basis": t.basis, "in_roster": t.member_id is not None,
                    "chars": sum(len(l) + 1 for l in sec.lines[t.start:t.end]),
                    **self.cite(sha, f"day {day} section {sec.index} turn {t.ordinal}")}, ensure_ascii=False) + "\n")
        self.counts[day] = {"layout": d.layout, "parliament": d.parliament, "split_rule": S.RULE,
                            **{k: v for k, v in S.counts(d).items() if k in ("sections", "turns", "attributed",
                                                                            "unattributed", "speakers")}}

    def close(self) -> None:
        self._sections.close()
        self._turns.close()

    def remove(self) -> None:
        for p in (self.sections_path, self.turns_path):
            try:
                os.remove(p)
            except OSError:
                pass
        try:
            os.rmdir(self._dir)
        except OSError:
            pass


def readings_of(days: list, store: rd.Store, version: int, loaded_at: str) -> tuple:
    """([readings rows], [people rows]) from the stored joined readings; each day row's reading state set."""
    readings, people = [], []
    for row in days:
        if row["reading"].startswith("set aside"):
            continue
        got = model_read.stored(row["document"], model_read.PROFILE, version, store)
        if got is None:
            row["reading"] = WAIT_TEXT
            continue
        row.update(reading="read", pieces=len(got["pieces"]), names=sum(len(p["names"]) for p in got["pieces"]),
                   unusable_pieces=sum(1 for p in got["pieces"] if p.get("unusable")))
        for p in got["pieces"]:
            readings.append({"key": f"{row['document']}/piece/{p['piece']}", "day": row["key"], "sitting_on": row["key"],
                             "piece": p["piece"], "section": f"{row['key']}/{p['section']}" if p.get("section") is not None else None,
                             "part": p.get("part"), "parts": p.get("parts"), "chars": p.get("chars"), "turns": p.get("turns"),
                             "names": len(p["names"]), "summary": p.get("summary"), "truncated": bool(p.get("truncated")),
                             "unusable": p.get("unusable"), "model": p.get("model") or got["model"], "reader": got["reader"],
                             "made_at": p.get("made_at") or got["made_at"], "document": row["document"],
                             "profile": model_read.PROFILE, "profile_version": version, "loaded_at": loaded_at})
        people.extend(model_read.people_rows(row["document"], got, row, model_read.PROFILE, version, loaded_at))
    return readings, people


def build(conn, schema: str, export: tuple, aside: list, only=None, shared: bool = False, mcp: dict = None,
          get_bytes=read_bytes, store: rd.Store = None) -> dict:
    """export: (sha256, name); aside: [(item, why)] from capture; only: the
    sitting days to read (the sample's), None for all; mcp: {corpus: (items,
    caught)} for the MCP's two corpora, items [(sha256, seq, record id)] in
    the order the pull landed them; store: the reader store the text reader's
    readings are replayed from. Wipes and fills `schema`; returns the counts.
    A reading that is not balanced raises."""
    create_tables(conn, schema, shared)
    res = read.read(get_bytes(export[0]), export[0], only=only)
    if not read.balanced(res):
        raise AssertionError(f"hansard: items in {res.counts['lines']} do not equal rows out plus set aside: {res.counts}")
    _copy(conn, table(schema, "set_aside", shared), ("item", "stage", "reason"),
          [{"item": i, "stage": "capture", "reason": w} for i, w in aside]
          + [{"item": i, "stage": s, "reason": w} for i, s, w in res.set_aside])
    for t in ("sittings", "sections", "turns", "members", "old_speeches"):
        _copy(conn, table(schema, t, shared), COLUMNS[t], getattr(res, t))
    conn.execute(f"INSERT INTO {table(schema, 'files', shared)} VALUES (%s, %s, 'hansard', 'read')", export)
    mcp = mcp or {}
    idx_items, idx_caught = mcp.get(read_mcp.INDEX, ([], []))
    day_items, day_caught = mcp.get(read_mcp.DAYS, ([], []))
    idx = read_mcp.read_index(idx_items, get_bytes)
    subjects = {}
    for sec in res.sections:
        subjects.setdefault(sec["sitting_on"], []).append((sec["key"], sec.get("subject")))
    version = model_read.profile_version()
    loaded_at = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    splitter = Splitter(S.Roster(res.members), version, loaded_at, model_read.budget_of())
    try:
        with conn.cursor().copy(f"COPY {table(private_of(schema), 'day_texts', shared)} (key, text) FROM STDIN") as cp:
            def sink(k, t, sha):
                cp.write_row((k, t))
                splitter.take(k, t, sha)
            days = read_mcp.read_days(day_items, get_bytes, subjects, sink)
        splitter.close()
        set_aside_days = dict(splitter.aside)
        for row in days.days:
            c = splitter.counts.get(row["key"], {})
            row.update({k: c.get(k) for k in ("layout", "parliament", "sections", "turns", "attributed", "unattributed",
                                               "speakers", "split_rule")})
            row["reading"] = f"set aside: {set_aside_days[row['key']]}" if row["key"] in set_aside_days else WAIT_TEXT
            row.update(pieces=None, names=None, unusable_pieces=None)
        readings, people = readings_of(days.days, store or rd.Store(), version, loaded_at)
        for t, rows in (("index_pages", idx.index_pages), ("days", days.days), ("day_subjects", days.day_subjects),
                        ("readings", readings), ("people", people)):
            _copy(conn, table(schema, t, shared), COLUMNS[t], rows)
        _copy(conn, table(schema, "day_sections", shared), COLUMNS["day_sections"], _lines(splitter.sections_path))
        _copy(conn, table(schema, "day_turns", shared), COLUMNS["day_turns"], _lines(splitter.turns_path))
    finally:
        splitter.close()
        splitter.remove()
    _copy(conn, table(schema, "files", shared), ("sha256", "name", "kind", "status"),
          [dict(zip(("sha256", "name", "kind", "status"), f)) for f in idx.files + days.files])
    _copy(conn, table(schema, "set_aside", shared), ("item", "stage", "reason"),
          [{"item": f"{c} seq {q}", "stage": "pull", "reason": f"{st}: {why}"}
           for c, lines in ((read_mcp.INDEX, idx_caught), (read_mcp.DAYS, day_caught)) for q, st, why in lines]
          + [{"item": i, "stage": s, "reason": w} for i, s, w in idx.set_aside + days.set_aside]
          + [{"item": d, "stage": "read", "reason": w} for d, w in splitter.aside])
    n_sec = sum(c.get("sections") or 0 for c in splitter.counts.values())
    n_turn = sum(c.get("turns") or 0 for c in splitter.counts.values())
    return {**res.counts, "not_held": len(aside), **idx.counts, **days.counts,
            "pull caught": len(idx_caught) + len(day_caught),
            "days split": sum(1 for c in splitter.counts.values() if c.get("split_rule")),
            "days set aside at read": len(splitter.aside), "day sections": n_sec, "day turns": n_turn,
            "day member turns": sum(c.get("attributed") or 0 for c in splitter.counts.values()),
            "days read": sum(1 for r in days.days if r["reading"] == "read"),
            "days waiting": sum(1 for r in days.days if r["reading"] == WAIT_TEXT),
            "readings": len(readings), "names": len(people)}


def mcp_items(conn, mcp_schema: str = capture.MCP_SCHEMA) -> dict:
    """{corpus: (arrivals, catch lines)} for the MCP's two Hansard corpora."""
    return {c: (capture.arrivals(conn, c, mcp_schema), capture.caught(conn, c, mcp_schema)) for c in capture.CORPORA}


def _export(conn) -> tuple:
    landed, aside = capture.copy_all(conn)
    return next((ref.sha256, name) for kind, ref, name, at in landed if kind == "hansard"), aside


def load(conn, schema: str, log=print, mcp_schema: str = capture.MCP_SCHEMA) -> int:
    """The export landed and read, and the MCP's two corpora, under `schema`. Returns the section count."""
    started = jobrun.now()
    export, aside = _export(conn)
    counts = build(conn, schema, export, aside, mcp=mcp_items(conn, mcp_schema))
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    log("hansard: " + detail)
    jobrun.record(JOB, True, detail, started, counts)
    return counts["sections"]


def publish(conn, staging: str) -> None:
    """The lane's own tables wiped and refilled from the staged ones, the
    private twin's day texts with them, and the views refreshed, in one
    transaction (contract: the lane)."""
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES:
            conn.execute(f"INSERT INTO {SCHEMA}.{t} SELECT * FROM {staging}.{t}")
        for t in PRIVATE_TABLES:
            conn.execute(f"INSERT INTO {PRIVATE}.{t} SELECT * FROM {private_of(staging)}.{t}")
        conn.execute(sql("publish.sql"))


def main(argv=None) -> int:
    """The job `qv4-hansard-load`: build under a staging schema, publish. With
    --schema, a session's proof: build there and publish nothing."""
    ap = argparse.ArgumentParser(prog="registers.hansard.load")
    ap.add_argument("--database", default="querynz_v4")
    ap.add_argument("--schema", help="build here and stop (a scratch proof); default: stage and publish")
    ap.add_argument("--mcp-schema", default=capture.MCP_SCHEMA)
    ap.add_argument("--mcp-database", help="read the pull's arrivals from this database under the session reader "
                                           "(a scratch proof of the whole corpus into the sample database)")
    a = ap.parse_args(argv)
    from support import db
    with db.connect(db.OWNER_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '600s'")
        if a.schema:
            export, aside = _export(conn)
            if a.mcp_database and a.mcp_database != a.database:
                with db.connect(db.READ_KEY, a.mcp_database) as other:
                    other.execute("SET statement_timeout = '600s'")
                    items = mcp_items(other, a.mcp_schema)
            else:
                items = mcp_items(conn, a.mcp_schema)
            counts = build(conn, a.schema, export, aside, mcp=items)
            conn.commit()
            print("hansard: " + ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {a.database}.{a.schema}")
            return 0
        load(conn, "staging_hansard_load", mcp_schema=a.mcp_schema)
        conn.commit()
        publish(conn, "staging_hansard_load")
        conn.commit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
