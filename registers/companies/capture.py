"""How this lane's documents arrive (plan 1.10, case two: only the loaded tables survive).

The Companies Office's monthly package (a zip of CSVs from its Box.com
folder) was downloaded by hand by Arthur, loaded into the old estate's
`nzbn_canonical`, and deleted after the load under the old retention rule
(`data-layer/nzbn_canonical/docs/bulk-import.md`). No raw file is held
anywhere on either box. Two packages were loaded: `companies-2026-07`
(14 July 2026) and `companies-2026-08` (16 August 2026). The old loader kept
the latest file's rows and set a role absent from the next file aside with
the import day as its end (never carried here: contract dates, 3).

So the loaded tables were exported once, on 20 October 2026, through the old
read-only login, every statement under a time limit, with server-side
cursors, into four gzip JSON-lines files, and those files are the documents:
every row read from them is "taken from the old estate's tables; original not
held" and cites the export's hash and its line. The hashes are pinned here; a
second export would be new documents and new pins. Nothing is fetched, and the
export is never run at load. The monthly file is Arthur's to download; a
later package is a new export.

  entities      the five company types (`public.entities`, with the July
                state of every entity that changed by August), and the other
                incorporated bodies in the package: incorporated societies
                and the like, charitable trust boards, public sector
                entities, retirement villages (`bulk.*_core_data` and their
                vanished rows). No address: those go to `addresses`
  directors     `public.director_roles` from the two files, with the files
                each role was in. The NZBN API backfill rows are not the file
  shareholders  `public.shareholder_roles`, the same way
  addresses     every registered office the package gives an entity, current
                and vanished. Never a person's address: the monthly file
                carries none, and the old API table that does
                (`bulk.director_addresses`) is not read

Line one of each part is a header (`"t": "export"`) naming the files, the old
loader's own counts per file (items in, for the catch log) and the part.

    export(part)          the part's bytes, through the old read-only login
    copy_all(conn)        land the four parts: ([(part, DocumentRef, name, at)], [(item, why)])
    python -m registers.companies.capture --export DIR    write the four parts once
"""
import datetime as dt
import gzip
import json
import os
import sys

from support.docstore.landing import land, path_for, read_bytes

SOURCE = "companies"
EXPORTED_AT = "2026-10-20T05:57:20+13:00"
EXPORT_NOTE = "taken from the old estate's tables; original not held"
FILES = ("companies-2026-07", "companies-2026-08")
PARTS = ("entities", "directors", "shareholders", "addresses")
#: part → (name, sha256), from the one run of --export (20 October 2026, 05:56 to 05:57 NZDT;
#: 1,920,469 / 1,185,823 / 1,581,956 / 868,688 lines with their headers)
EXPORTS = {
    "entities": ("companies-entities-2026-10-20.jsonl.gz",
                  "736d1f817d126badb8cb8ec20ae6095d985e6fc68b2669b220f0c72c581dad04"),
    "directors": ("companies-directors-2026-10-20.jsonl.gz",
                  "62d0a8e1bb11ce04523c94e7edef471dd2cc82aaaead6263b59df0ae9ee444bb"),
    "shareholders": ("companies-shareholders-2026-10-20.jsonl.gz",
                  "a466343dcf9e305b7bc08daf4fd577a99d2e02430b184a5227a913ea3838af60"),
    "addresses": ("companies-addresses-2026-10-20.jsonl.gz",
                  "e3f3cf09b7bf275bd857fbe531a83522ca4d14c3dbf515486e205f34d23fcdba"),
}

#: The other bodies in the package, by their old table: (register name, number column).
#: `unincorporated_entities_core_data` (sole traders, partnerships, trading
#: trusts) is in the package too and is not taken (card: the package carries sole traders).
OTHER = {
    "other_incorporated_entities_core_data": ("other_incorporated", "incorporation_number"),
    "charitable_trust_boards_core_data": ("charitable_trust_board", "incorporation_number"),
    "public_sector_entities_core_data": ("public_sector", None),
    "retirement_villages_core_data": ("retirement_village", "entity_number"),
}
_OTHER_FIELDS = ("entity_name", "entity_type", "entity_status", "registration_date", "deregistration_date",
                 "incorporated_societies_act", "incsoc2022act_reregistration_date", "charities_register_number")
#: registered office columns, by table: (care of, line 1..4, postcode, country)
_RO = ("registered_office_address_care_of", "registered_office_address_1", "registered_office_address_2",
       "registered_office_address_3", "registered_office_address_4", "registered_office_address_postcode",
       "registered_office_address_country")
_RO_LINE = ("registered_office_address_care_of", "registered_office_address_line_1",
            "registered_office_address_line_2", "registered_office_address_line_3",
            "registered_office_address_line_4", "registered_office_address_postcode")
ADDRESS_COLUMNS = {
    "companies_registered_office_address": _RO,
    "other_incorporated_entities_core_data": _RO_LINE + ("registered_office_address_country",),
    "charitable_trust_boards_core_data": _RO_LINE + ("registered_office_address_country_code",),
    "retirement_villages_core_data": (None,) + _RO[1:6] + (None,),
}
ADDRESS_FIELDS = ("care_of", "line_1", "line_2", "line_3", "line_4", "postcode", "country")


def _j(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str)


def _cols(conn, schema: str, table: str) -> list:
    return [r[0] for r in conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = %s "
        "ORDER BY ordinal_position", (schema, table)).fetchall()]


def _stream(conn, name: str, sql: str, params=()):
    """Rows through a server-side cursor, as dicts."""
    with conn.transaction():
        cur = conn.cursor(name=name)
        cur.itersize = 5000
        cur.execute(sql, params)
        cols = None
        for row in cur:
            cols = cols or [d[0] for d in cur.description]
            yield dict(zip(cols, row))


def _header(conn, part: str) -> dict:
    runs = {r[0]: {"run": str(r[1]), "started": r[2].isoformat(), "entities": r[3], "directors": r[4],
                   "shareholders": r[5]}
            for r in conn.execute("SELECT source_label, id, started_at, entities_upserted, directors_upserted, "
                                  "shareholders_upserted FROM public.import_runs WHERE run_type = 'bulk' "
                                  "AND status = 'completed' ORDER BY started_at").fetchall()}
    aux = {}
    for f, n, label in conn.execute("SELECT file, max(rows), source_label FROM bulk.import_log "
                                    "WHERE source_label LIKE 'companies-%%' GROUP BY 1, 3").fetchall():
        aux.setdefault(label, {})[f] = n
    return {"t": "export", "part": part, "files": [l for l in runs if l in FILES], "runs": runs, "aux_rows": aux,
            "note": EXPORT_NOTE}


def _run_ids(conn) -> dict:
    return {l: str(i) for l, i in conn.execute(
        "SELECT source_label, id FROM public.import_runs WHERE run_type = 'bulk'").fetchall()}


def _seen_in(conn, table: str, key: str, run: str) -> set:
    return {r[0] for r in conn.execute(f"SELECT {key}::text FROM public.{table} WHERE import_run_id = %s", (run,))}


def _entities(conn, out) -> None:
    runs = _run_ids(conn)
    # the July state of every entity the August file changed
    july = {}
    for r in conn.execute(
            "SELECT h.entity_id::text, h.entity_name, h.entity_status, h.entity_type, h.registered_at, h.removed_at "
            "FROM public.entity_history h WHERE h.import_run_id = %s AND h.entity_id IN "
            "(SELECT entity_id FROM public.entity_history WHERE import_run_id = %s)",
            (runs[FILES[0]], runs[FILES[1]])).fetchall():
        july[r[0]] = {"name": r[1], "status": r[2], "type": r[3], "registered_on": r[4], "removed_on": r[5]}
    in_july = _seen_in(conn, "entity_history", "entity_id", runs[FILES[0]])
    for e in _stream(conn, "companies_entities",
                     "SELECT id::text, nzbn, company_number, entity_name, entity_type, entity_status, registered_at, "
                     "removed_at, source_file FROM public.entities ORDER BY nzbn"):
        files = [f for f in FILES if (f == FILES[0] and e["id"] in in_july) or e["source_file"] == f]
        line = {"t": "entity", "register": "companies", "nzbn": e["nzbn"], "number": e["company_number"],
                "name": e["entity_name"], "type": e["entity_type"], "status": e["entity_status"],
                "registered_on": e["registered_at"], "removed_on": e["removed_at"], "files": files,
                "last_file": e["source_file"], "old_id": e["id"]}
        j = july.get(e["id"])
        if j and any(j[k] != line[k] for k in ("name", "status", "type", "registered_on", "removed_on")):
            line["earlier"] = [{**j, "file": FILES[0]}]
        out.write(_j(line) + "\n")
    for table, (register, num) in OTHER.items():
        cols = set(_cols(conn, "bulk", table))
        keep = [c for c in _OTHER_FIELDS if c in cols]
        sel = ", ".join(["nzbn" if "nzbn" in cols else "NULL AS nzbn", f"{num} AS number" if num else "NULL AS number"] + keep)
        rows = {}
        for r in _stream(conn, f"companies_{register}", f"SELECT {sel}, source_label, NULL::text AS vanished "
                         f"FROM bulk.{table} UNION ALL SELECT {sel}, last_source_label, vanished_at::text "
                         f"FROM bulk.{table}_history ORDER BY 1, 2"):
            k = r["nzbn"] or f"#{r['number']}"
            rows.setdefault(k, []).append(r)
        for k in sorted(rows):
            current = [r for r in rows[k] if r["vanished"] is None]
            gone = [r for r in rows[k] if r["vanished"] is not None]
            head = (current or gone)[-1]
            line = {"t": "entity", "register": register, "nzbn": head["nzbn"], "number": head["number"],
                    "name": head["entity_name"], "type": head.get("entity_type"), "status": head.get("entity_status"),
                    "registered_on": head.get("registration_date"), "removed_on": head.get("deregistration_date"),
                    "files": [], "last_file": head["source_label"], "in_latest": bool(current),
                    "extra": {c: head.get(c) for c in ("incorporated_societies_act", "incsoc2022act_reregistration_date",
                                                       "charities_register_number") if head.get(c)}}
            if len(current) > 1:
                line["also"] = len(current) - 1
            if gone and current:
                line["earlier"] = [{"name": g["entity_name"], "status": g.get("entity_status"),
                                    "registered_on": g.get("registration_date"),
                                    "removed_on": g.get("deregistration_date"), "file": g["source_label"]}
                                   for g in gone]
            out.write(_j(line) + "\n")


def _roles(conn, out, kind: str) -> None:
    runs = _run_ids(conn)
    table, hist = f"{kind}_roles", f"{kind}_role_history"
    in_july = _seen_in(conn, hist, f"{kind}_role_id", runs[FILES[0]])
    if kind == "director":
        sel = ("d.first_name, d.middle_names, d.last_name, d.full_name, d.role_type, d.appointed_at")
    else:
        sel = ("d.shareholder_type, d.full_name, d.shareholder_entity_name, d.shareholder_nzbn, d.shares, "
               "d.allocation_type")
    for d in _stream(conn, f"companies_{kind}s",
                     f"SELECT d.id::text, d.source_nzbn, e.company_number, {sel}, d.suppressed, d.source_file "
                     f"FROM public.{table} d LEFT JOIN public.entities e ON e.id = d.entity_id "
                     f"ORDER BY d.source_nzbn, d.id"):
        files = [f for f in FILES if (f == FILES[0] and d["id"] in in_july) or d["source_file"] == f]
        line = {"t": kind, "nzbn": d.pop("source_nzbn"), "number": d.pop("company_number"), "files": files,
                "last_file": d.pop("source_file"), "old_id": d.pop("id"), **d}
        if kind == "director":
            line["appointed_on"] = line.pop("appointed_at")
        out.write(_j(line) + "\n")


def _addresses(conn, out) -> None:
    for table, cols in ADDRESS_COLUMNS.items():
        have = set(_cols(conn, "bulk", table))
        register = "companies" if table.startswith("companies_") else OTHER[table][0]
        num = None if register == "companies" else OTHER[table][1]
        start = "start_date" if "start_date" in have else "NULL::text"
        idc = "nzbn" if "nzbn" in have else "NULL::text"
        sel = ", ".join([f"{idc} AS nzbn", f"{num} AS number" if num else "NULL::text AS number",
                         f"{start} AS start_date"] + [f"{c} AS f{i}" if c else f"NULL::text AS f{i}"
                                                      for i, c in enumerate(cols)])
        for r in _stream(conn, f"companies_ro_{register}",
                         f"SELECT {sel}, source_label AS file, NULL::text AS vanished FROM bulk.{table} UNION ALL "
                         f"SELECT {sel}, last_source_label, vanished_at::text FROM bulk.{table}_history ORDER BY 1, 2, 3"):
            fields = {ADDRESS_FIELDS[i]: r[f"f{i}"] for i in range(len(cols))}
            out.write(_j({"t": "registered_office", "register": register, "nzbn": r["nzbn"], "number": r["number"],
                          "start": r["start_date"], **fields, "last_file": r["file"],
                          "in_latest": r["vanished"] is None}) + "\n")


def export(part: str, connect=None) -> bytes:
    """One part's gzip bytes. Read-only, every statement under a time limit; run once."""
    import io
    from support import db
    connect = connect or (lambda name: db.connect(db.OLD_READ_KEY, name, connect_timeout=10))
    buf = io.StringIO()
    with connect("nzbn_canonical") as c:
        c.execute("SET statement_timeout = '600s'")
        c.execute("SET default_transaction_read_only = on")
        buf.write(_j(_header(c, part)) + "\n")
        {"entities": _entities, "addresses": _addresses,
         "directors": lambda c, o: _roles(c, o, "director"),
         "shareholders": lambda c, o: _roles(c, o, "shareholder")}[part](c, buf)
    return gzip.compress(buf.getvalue().encode("utf-8"), compresslevel=6, mtime=0)


def copy_all(conn, exports: dict = None, log=None) -> tuple:
    """The four parts landed from the store. Returns
    ([(part, DocumentRef, name, exported at)], [(item, why)])."""
    landed = []
    for part, (name, sha) in (exports or EXPORTS).items():
        if not sha or not os.path.exists(path_for(sha)):
            raise LookupError(f"the companies {part} export {sha or '(not pinned)'} is not in the document store")
        ref, new = land(read_bytes(sha), name=name, source=SOURCE, conn=conn, fetched_at=EXPORTED_AT,
                        content_type="application/gzip")
        if log:
            log(f"companies: {'landed' if new else 'held'} {ref.sha256[:12]} {name}")
        landed.append((part, ref, name, EXPORTED_AT))
    return landed, []


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if "--export" not in argv:
        print("usage: python -m registers.companies.capture --export DIR [PART ...]")
        return 2
    folder = argv[argv.index("--export") + 1]
    parts = [p for p in argv if p in PARTS] or list(PARTS)
    from support.docstore import sha256_file
    for part in parts:
        path = os.path.join(folder, EXPORTS[part][0])
        if os.path.exists(path):
            print(f"{path} exists: the export is run once")
            return 1
        data = export(part)
        with open(path, "wb") as f:
            f.write(data)
        lines = gzip.decompress(data).count(b"\n")
        print(f"{path}: {lines} lines, {len(data)} bytes, sha256 {sha256_file(path)}, "
              f"{dt.datetime.now().astimezone().isoformat(timespec='seconds')}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
