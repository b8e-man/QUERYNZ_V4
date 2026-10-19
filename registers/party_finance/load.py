"""Loading (plan 1b.7, 1.11). The merge gate's staging step calls `load`
to build this lane's tables under a staging schema of the real database,
and `publish` to move the rows into the lane's own tables in one
transaction and refresh the published views. `sample.fill` uses `build`
for the sample, where every module shares one scratch schema, so there
this lane's tables carry its name (`party_finance_files`, …; `table`).

Capture, read, insert. Every document lands by hash; every Commission
listing row is a row or a catch-log line; every link is a held document or
a catch-log line; every expense return a listing links is a row or a
catch-log line. `reconcile` states those sums, and the run record carries
them.
"""
import os

from support import jobrun
from support import reader as rd
from support.docstore.landing import read_bytes
from registers.party_finance import capture, expenses, promoter_returns, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "party_finance"
PRIVATE = "party_finance_private"
JOB = "qv4-party-finance-load"
COLUMNS_OF = {
    "files": ("document", "kind", "old_path", "url", "captured_at"),
    "set_aside": ("item", "stage", "reason"),
    "expense_listing": ("key", "document", "page", "place", "year", "party_label", "party", "party_basis", "note",
                        "expense_limit", "total_expenses", "allocation", "allocation_spent", "audited", "printed",
                        "reader", "profile", "profile_version", "read_from", "loaded_at"),
    "promoter_listing": ("key", "document", "page", "place", "year", "promoter", "note", "election_expenses",
                         "cannabis_referendum_expenses", "end_of_life_referendum_expenses", "printed", "reader",
                         "profile", "profile_version", "read_from", "loaded_at"),
    "listing_links": ("row_key", "ordinal", "link_text", "url", "amended", "document"),
    "allocations": ("key", "document", "page", "place", "year", "round", "round_label", "final", "party_label", "party",
                    "party_basis", "mark", "eligible", "amount", "printed", "reader", "profile", "profile_version",
                    "read_from", "loaded_at"),
    "allocation_totals": ("key", "document", "year", "round", "round_label", "allocated", "available", "rows_sum",
                          "printed"),
    "promoters": ("key", "document", "page", "place", "year", "promoter", "registered_on", "registered_for", "statement",
                  "reader", "profile", "profile_version", "read_from", "loaded_at"),
    "promoter_people": ("key", "promoter_key", "document", "page", "place", "role", "name", "reader", "profile",
                        "profile_version", "read_from", "loaded_at"),
    "financial_statements": ("key", "document", "page", "place", "filed_year", "party_label", "party", "party_basis",
                             "note", "mark", "balance_date", "deadline", "date_filed", "balance_printed",
                             "deadline_printed", "filed_printed", "audit_requirement", "reader", "profile",
                             "profile_version", "read_from", "loaded_at"),
    "expense_returns": ("key", "document", "page", "place", "listing_row", "year", "party_label", "party",
                        "party_basis", "current", "total", "total_check", "part_a", "part_b", "part_c", "expense_limit",
                        "read_from", "reader", "profile", "profile_version", "loaded_at"),
    "promoter_returns": ("key", "document", "page", "place", "listing_row", "year", "promoter", "part", "spending",
                         "figure", "figure_check", "declared", "schedule", "read_from", "reader", "profile",
                         "profile_version", "loaded_at"),
}
TABLES = tuple(COLUMNS_OF)
#: the private twin's tables (hard limit 15): never published, never granted to a reader
PRIVATE_COLUMNS_OF = {"promoter_contacts": ("promoter_key", "label", "value")}


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema[:55]}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


def sql(name: str, schema: str = SCHEMA, shared: bool = False) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    pre = f"{SCHEMA}_" if shared else ""
    return text.replace(f"{PRIVATE}.", f"{private_of(schema)}.{pre}").replace(f"{SCHEMA}.", f"{schema}.{pre}")


def create_tables(conn, schema: str, shared: bool = False) -> None:
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {private_of(schema)}")
    conn.execute(sql("tables.sql", schema, shared))


def wipe(conn, schema: str, shared: bool = False) -> None:
    for t in TABLES:
        conn.execute(f"DELETE FROM {table(schema, t, shared)}")
    for t in PRIVATE_COLUMNS_OF:
        conn.execute(f"DELETE FROM {table(private_of(schema), t, shared)}")


def insert(conn, schema: str, t: str, row: dict, shared: bool = False) -> None:
    cols = COLUMNS_OF.get(t) or PRIVATE_COLUMNS_OF[t]
    conn.execute(f"INSERT INTO {table(schema, t, shared)} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})",
                 tuple(row.get(c) for c in cols))


def aside(conn, schema: str, item: str, stage: str, reason: str, shared: bool = False) -> None:
    insert(conn, schema, "set_aside", {"item": item, "stage": stage, "reason": reason}, shared)


def party_rows(conn, schema: str = None, shared: bool = False) -> list:
    """The parties lane's published names with their registration's window (`pub.party_names` joined to
    `pub.parties`), as `keys.parties.party_name(label, rows, on=…)` takes them. In a session's sample the
    published tables are that lane's own in the shared schema (`parties_names`, `parties_registrations`).
    None found is an error, never a fall back to the 18 October snapshot."""
    where = [(f"{schema}.parties_names", f"{schema}.parties_registrations")] if shared and schema else []
    where.append(("pub.party_names", "pub.parties"))
    for names, regs in where:
        if conn.execute("SELECT to_regclass(%s) IS NOT NULL AND to_regclass(%s) IS NOT NULL", (names, regs)).fetchone()[0]:
            cur = conn.execute(f"SELECT n.party, n.name, n.kind, n.from_on, n.to_on, p.registered_on, p.cancelled_on "
                               f"FROM {names} n JOIN {regs} p ON p.key = n.party")
            rows = [dict(zip([d[0] for d in cur.description], r)) for r in cur]
            if rows:
                return rows
    raise LookupError("party_finance: the parties lane's published names are not in this database "
                      f"(looked for {', '.join(n for n, _ in where)}): fill the parties lane first")


def build(conn, schema: str, held: list, store: rd.Store, capture_lines: list = (), shared: bool = False) -> dict:
    """held: [(kind, sha256, old path, Commission URL or None, captured_at)] for documents already in the
    store. Wipes and refills this lane's tables under `schema`; returns the counts."""
    names = party_rows(conn, schema, shared)
    create_tables(conn, schema, shared)
    wipe(conn, schema, shared)
    at = read.now()
    counts = {"accounted": 0, "documents": 0, "listing_rows": 0, "listing_aside": 0, "links": 0, "links_unheld": 0,
              "returns_linked": 0, "returns_read": 0, "returns_aside": 0, "capture_lines": len(capture_lines),
              "allocation_pages": 0, "allocation_rows": 0, "allocation_aside": 0, "unread": 0,
              "register_pages": 0, "promoters": 0, "promoter_people": 0, "promoter_aside": 0,
              "roster_rows": 0, "roster_aside": 0, "statements_linked": 0,
              "promoter_returns_linked": 0, "promoter_parts": 0, "promoter_parts_read": 0, "promoter_parts_aside": 0}
    for item, why in capture_lines:
        aside(conn, schema, item, "capture", why, shared)
    by_url, files, linked = {}, {}, set()
    for kind, sha, path, url, captured in held:
        if sha in files:
            continue
        files[sha] = kind
        insert(conn, schema, "files", {"document": sha, "kind": kind, "old_path": path, "url": url,
                                       "captured_at": captured}, shared)
        counts["documents"] += 1
        if url:
            by_url[url] = sha
    listing_years = {os.path.basename(p): (k, y) for p, k, y in
                     ((os.path.join(capture.INDEX, n), k, y) for n, k, y in capture.LISTINGS)}
    for kind, sha, path, url, captured in held:
        if kind not in read.PROFILE_OF:
            continue
        _, year = listing_years[os.path.basename(path)]
        rows, links, lines = read.listing_rows(kind, read_bytes(sha), sha, year, by_url, at, names)
        t = "expense_listing" if kind == "expenses-listing" else "promoter_listing"
        for r in rows:
            insert(conn, schema, t, r, shared)
        for x in links:
            insert(conn, schema, "listing_links", x, shared)
        for item, stage, why in lines:
            aside(conn, schema, item, stage, why, shared)
        counts["listing_rows"] += len(rows)
        counts["listing_aside"] += sum(1 for _, s, _ in lines if s == "listing")
        counts["links"] += len(links)
        counts["links_unheld"] += sum(1 for x in links if x["document"] is None)
        if kind != "expenses-listing":
            for r in rows:
                for x in links:
                    if x["row_key"] != r["key"] or x["document"] is None:
                        continue
                    counts["promoter_returns_linked"] += 1
                    linked.add(x["document"])
                    res = promoter_returns.read_return(read_bytes(x["document"]), x["document"], store, r["year"])
                    out, lines = read.promoter_return_rows(res, r, at)
                    for row in out:
                        insert(conn, schema, "promoter_returns", row, shared)
                    for item, stage, why in lines:
                        aside(conn, schema, item, stage, why, shared)
                    counts["promoter_parts"] += len(promoter_returns.COLUMNS.get(r["year"], {}))
                    counts["promoter_parts_read"] += len(out)
                    counts["promoter_parts_aside"] += len(lines)
            continue
        for r in rows:
            mine = [x for x in links if x["row_key"] == r["key"]]
            for x in mine:
                if x["document"] is None:
                    continue
                counts["returns_linked"] += 1
                linked.add(x["document"])
                res = expenses.read_return(read_bytes(x["document"]), x["document"], store)
                row = read.expense_return_row(res, r, x, read.is_current(x, mine), at)
                if row:
                    insert(conn, schema, "expense_returns", row, shared)
                    counts["returns_read"] += 1
                else:
                    for stage, why in res.set_aside:
                        aside(conn, schema, x["document"], stage, f"{r['party_label']} {r['year']}: {why}", shared)
                    counts["returns_aside"] += 1
    for kind, sha, path, url, captured in held:
        if kind != "allocation-page":
            continue
        rows, totals, lines = read.allocation_rows(read_bytes(sha), sha, at, names)
        for r in rows:
            insert(conn, schema, "allocations", r, shared)
        for x in totals:
            insert(conn, schema, "allocation_totals", x, shared)
        for item, stage, why in lines:
            aside(conn, schema, item, stage, why, shared)
        counts["allocation_pages"] += 1
        counts["allocation_rows"] += len(rows)
        counts["allocation_aside"] += 0 if rows else 1
    for kind, sha, path, url, captured in held:
        if kind != "promoter-register":
            continue
        rows, ppl, contacts, lines = read.promoter_rows(read_bytes(sha), sha, at)
        for r in rows:
            insert(conn, schema, "promoters", r, shared)
        for r in ppl:
            insert(conn, schema, "promoter_people", r, shared)
        for r in contacts:
            insert(conn, private_of(schema), "promoter_contacts", r, shared)
        for item, stage, why in lines:
            aside(conn, schema, item, stage, why, shared)
        counts["register_pages"] += 1
        counts["promoters"] += len(rows)
        counts["promoter_people"] += len(ppl)
        counts["promoter_aside"] += sum(1 for _, s, _ in lines if s == "promoter")
    for kind, sha, path, url, captured in held:
        if kind != "financials-listing":
            continue
        rows, out_links, lines = read.statement_rows(read_bytes(sha), sha, by_url, at, names)
        for r in rows:
            insert(conn, schema, "financial_statements", r, shared)
        for x in out_links:
            insert(conn, schema, "listing_links", x, shared)
            if x["document"]:
                linked.add(x["document"])
        for item, stage, why in lines:
            aside(conn, schema, item, stage, why, shared)
        counts["roster_rows"] += len(rows)
        counts["roster_aside"] += sum(1 for _, s, _ in lines if s == "statement")
        counts["links"] += len(out_links)
        counts["links_unheld"] += sum(1 for x in out_links if x["document"] is None)
        counts["statements_linked"] = len({x["document"] for x in out_links if x["document"]})
    for sha, kind in files.items():
        if kind in UNREAD:
            aside(conn, schema, sha, "unread", UNREAD[kind], shared)
            counts["unread"] += 1
    for sha, kind in files.items():
        if kind in ("expense-return", "financial-statements", "promoter-return") and sha not in linked:
            aside(conn, schema, sha, "unread", "held; no row of the Commission's own tables links it", shared)
            counts["unread"] += 1
    counts["accounted"] = sum(1 for k in files.values() if k in READ_KINDS) + counts["unread"] + len(linked)
    return counts


#: kinds the lane holds and does not read yet: a catch-log line each, so every held document is accounted for
UNREAD = {
    "allocation-decision": "held; the allocation page carries the decision's figures, and the decision itself is not read",
}
#: kinds read whole by the build: a listing or a page is accounted for by being read
READ_KINDS = ("expenses-listing", "promoter-expenses-listing", "allocation-page", "promoter-register", "financials-listing")


def reconcile(c: dict) -> list:
    """The catch log's sums, as lines that must all be empty: items in equal items out plus items set aside."""
    bad = []
    if c["documents"] != c["accounted"]:
        bad.append(f"documents: {c['documents']} held, {c['accounted']} read, a row's source or a catch-log line")
    if c["returns_linked"] != c["returns_read"] + c["returns_aside"]:
        bad.append(f"returns: {c['returns_linked']} linked, {c['returns_read']} read + {c['returns_aside']} set aside")
    if c["promoter_parts"] != c["promoter_parts_read"] + c["promoter_parts_aside"]:
        bad.append(f"promoter parts: {c['promoter_parts']} on the forms, {c['promoter_parts_read']} read + "
                   f"{c['promoter_parts_aside']} set aside")
    return bad


def held_documents(conn, staging: str = None) -> tuple:
    """Land every candidate file by hash: ([(kind, sha, old path, url, captured_at)], capture catch-log lines)."""
    man = capture.manifest(staging)
    held = []
    for kind, ref, path, new in capture.copy_all(conn, staging):
        m = man.get(ref.sha256) or {}
        held.append((kind, ref.sha256, path, m.get("source"), m.get("fetched_at")))
    lines = [(sha, f"{folder}/MANIFEST.jsonl lists {name} as {sha[:12]}…, whose bytes the old job has since overwritten")
             for folder, sha, name in capture.overwritten(staging)]
    lines += [(f"{folder}/{name}", f"{folder}/{name}: no kind matches this file") for folder, name in capture.unrecognised(staging)]
    return held, lines


def load(conn, schema: str, log=print, store: rd.Store = None, shared: bool = False) -> dict:
    started = jobrun.now()
    held, lines = held_documents(conn)
    c = build(conn, schema, held, store or rd.Store(), lines, shared)
    bad = reconcile(c)
    detail = (f"{c['documents']} documents; {c['listing_rows']} listing rows, {c['listing_aside']} set aside; "
              f"{c['links']} links, {c['links_unheld']} not held; {c['returns_linked']} returns linked: "
              f"{c['returns_read']} read, {c['returns_aside']} set aside; into {schema}"
              + (f"; DOES NOT RECONCILE: {bad}" if bad else ""))
    log("party_finance: " + detail)
    jobrun.record(JOB, not bad, detail, started, c)
    if bad:
        raise RuntimeError("party_finance: the catch log does not reconcile: " + "; ".join(bad))
    return c


def publish(conn, staging: str) -> None:
    """The lane's own tables wiped and refilled from the staged ones, and
    the views refreshed, in one transaction (contract: the lane)."""
    with conn.transaction():
        create_tables(conn, SCHEMA)
        wipe(conn, SCHEMA)
        for t in TABLES:
            cols = ", ".join(COLUMNS_OF[t])
            conn.execute(f"INSERT INTO {SCHEMA}.{t} ({cols}) SELECT {cols} FROM {staging}.{t}")
        for t, cols in PRIVATE_COLUMNS_OF.items():
            cols = ", ".join(cols)
            conn.execute(f"INSERT INTO {PRIVATE}.{t} ({cols}) SELECT {cols} FROM {private_of(staging)}.{t}")
        conn.execute(sql("publish.sql"))
