"""How this lane's documents arrive: two ways, one after the other.

1. Once only (plan 1.10, case two: only the loaded tables survive). The old
   estate asked the NZBN register's per-entity interface for every registered
   incorporated society, a seventh a night (`ops/backfill_society_officers.py`,
   C531), and kept what it parsed in `nzbn_canonical.public.society_officers`,
   replacing a society's officers on every ask; the answers themselves were
   never kept. The society rows are the Companies Office's August 2026 monthly
   file (`bulk.other_incorporated_entities_core_data`, with its vanished rows).
   Those tables were exported once, through the old read-only login, every
   statement under a time limit, read-only transactions, server-side cursors,
   into three gzip JSON-lines parts, and the parts are the documents: every
   row read from them is "taken from the old estate's tables; original not
   held" and cites the part's hash and its line. Never run at load.

     societies   every incorporated society the August file names, current and
                 vanished. No registered office: the companies lane carries those
     officers    `public.society_officers`: names, status and the dates the
                 register states. The table holds no address
     asks        `public.society_sweep_log`: when each society was last asked,
                 whether the register answered, and how many officers it gave

   Line one of each part is a header (`"t": "export"`) with the source
   table's own counts, for the catch log.

2. Nightly, from the merge on (`qv4-societies-capture`, proposed in spec.md;
   a build session queues no live job). One request per society to the NZBN
   API's entity detail, `GET {BASE}/entities/{nzbn}`, through the fetch gate
   with our own key (`~/.querynz/nzbn.env`, read at the moment of use, sent
   only in its header, never logged). The answer's bytes are landed verbatim
   by hash, so it is never fetched twice in a day and is re-read without the
   network. The party societies first, then the stalest seventh. A 403, 429,
   5xx or challenge page is a failed read: logged, and the run stops for that
   host. The four questions are answered in `docs/status/societies.md`.

    export(part)                    one part's bytes (run once, done)
    copy_all(conn)                  land the three parts: ([(part, DocumentRef, name, at)], [(item, why)])
    slice_for(day, societies, asked, party)   tonight's NZBNs, party societies first
    fetch_entity(nzbn, ...)         one gated ask: (Fetched, DocumentRef or None)
    python -m registers.societies.capture --export DIR [PART ...]
    python -m registers.societies.capture --fetch NZBN [NZBN ...]   a handful, to prove the path
    python -m registers.societies.capture --night [--budget-s N] [--anytime]   the nightly job
"""
import datetime as dt
import gzip
import json
import os
import re
import sys

from support.docstore.landing import land, path_for, read_bytes

SOURCE = "societies"
EXPORT_NOTE = "taken from the old estate's tables; original not held"
API_NOTE = "the NZBN register's entity detail, as it answered"
PARTS = ("societies", "officers", "asks")
EXPORTED_AT = "2026-10-20T07:23:27+13:00"
#: part → (name, sha256), from the one run of --export (20 October 2026, 07:23:25 to 07:23:27 NZDT;
#: 53,598 / 133,081 / 22,788 lines with their headers)
EXPORTS = {
    "societies": ("societies-societies-2026-10-20.jsonl.gz",
                  "1a9e66b9fa6c4e17f739bfa71f075f8d2a98e7e53a3a93a7f2f37cfa6f3b67af"),
    "officers": ("societies-officers-2026-10-20.jsonl.gz",
                  "64692937c7250987e62be7c22d9ee2886ccba745287a8e1573eb4552b48c4ffe"),
    "asks": ("societies-asks-2026-10-20.jsonl.gz",
                  "0fab67839978da402f17e5cbac7ad38040271737f6787f5c09630ef3fc978c92"),
}
#: the per-entity path proved on five pages, the party societies, 20 October 2026 (sha256, fetched at)
PROOF = (
    ("46067c2c2e5954b01f28eced678a05e0fecf06811d9a02e678d33bcfce87e40e", "2026-10-20T07:28:04+13:00"),
    ("f59a0239d36ae1c2837af2265d631366736176d29a220ae406dd3a112cdf0361", "2026-10-20T07:28:08+13:00"),
    ("8fd4a0722b1862b97e28928d5bef5d0f64f97f1c6f4d62ae025a96df435dd54d", "2026-10-20T07:28:13+13:00"),
    ("bb5fa3a63fa59a3d411acbd0d6873aa10c4f854ae2bdc0e2fa238535421ed7a6", "2026-10-20T07:28:18+13:00"),
    ("0ec3ad217377ecdb8142449699c63968d223d93231cefc3ae7319e476dc5ac32", "2026-10-20T07:28:23+13:00"),
)
SOCIETY_TYPE = "Incorporated Society"
_SOC_FIELDS = ("nzbn", "incorporation_number", "entity_name", "entity_type", "entity_status", "registration_date",
               "deregistration_date", "incorporated_societies_act", "incsoc2022act_reregistration_date",
               "charities_register_number")

BASE = os.environ.get("QV4_NZBN_API_BASE") or "https://api.business.govt.nz/gateway/nzbn/v5"
KEY_FILE = os.path.join(os.environ.get("QV4_CRED_DIR") or os.path.expanduser("~/.querynz"), "nzbn.env")
KEY_NAME = "NZBN_API_KEY"
KEY_HEADER = "Ocp-Apim-Subscription-Key"
HERE = os.path.dirname(os.path.abspath(__file__))
#: the draft one-page position (ruling 61: written before product; the
#: integrator moves it to docs/legal/positions/ at the merge)
POSITIONS = os.environ.get("QV4_SOCIETIES_POSITIONS") or os.path.join(HERE, "position")
#: the party societies: the old product's own shape (PARTY_SOCIETY_SQL), kept as one expression here
PARTY_NAME = re.compile(r"party of (aotearoa|new zealand)|(labour|green|m[aā]ori) party|te p[aā]ti m[aā]ori"
                        r"|^(the )?opportunit(y|ies) party", re.I)
PARTY_NOT = re.compile(r"branch|electorate|region|district|clubroom|club |residents|young|women", re.I)
NIGHTS = 7
#: the lane's own floor between asks, above the gate's default, until the gate's FLOORS names the host
LANE_FLOOR_S = 5.0
_LAST = {}


def _j(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str)


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
    one = lambda q, p=(): conn.execute(q, p).fetchone()[0]
    counts = {
        "societies": {"current": one("SELECT count(*) FROM bulk.other_incorporated_entities_core_data "
                                     "WHERE entity_type = %s", (SOCIETY_TYPE,)),
                      "vanished": one("SELECT count(*) FROM bulk.other_incorporated_entities_core_data_history "
                                      "WHERE entity_type = %s", (SOCIETY_TYPE,)),
                      "files": [r[0] for r in conn.execute(
                          "SELECT DISTINCT source_label FROM bulk.other_incorporated_entities_core_data "
                          "WHERE entity_type = %s ORDER BY 1", (SOCIETY_TYPE,))]},
        "officers": {"rows": one("SELECT count(*) FROM public.society_officers"),
                     "societies": one("SELECT count(DISTINCT nzbn) FROM public.society_officers"),
                     "first_read": one("SELECT min(imported_at) FROM public.society_officers"),
                     "last_read": one("SELECT max(imported_at) FROM public.society_officers")},
        "asks": {"rows": one("SELECT count(*) FROM public.society_sweep_log")},
    }[part]
    return {"t": "export", "part": part, "counts": counts, "note": EXPORT_NOTE,
            "at": dt.datetime.now().astimezone().isoformat(timespec="seconds")}


def _societies(conn, out) -> None:
    sel = ", ".join(_SOC_FIELDS)
    for r in _stream(conn, "societies_societies",
                     f"SELECT {sel}, source_label AS file, NULL::text AS vanished_at "
                     f"FROM bulk.other_incorporated_entities_core_data WHERE entity_type = %s UNION ALL "
                     f"SELECT {sel}, last_source_label, vanished_at::text "
                     f"FROM bulk.other_incorporated_entities_core_data_history WHERE entity_type = %s "
                     f"ORDER BY 1, 2, vanished_at NULLS LAST", (SOCIETY_TYPE, SOCIETY_TYPE)):
        out.write(_j({"t": "society", **r}) + "\n")


def _officers(conn, out) -> None:
    for r in _stream(conn, "societies_officers",
                     "SELECT id::text AS old_id, nzbn, entity_name, role_type, role_status, first_name, middle_names, "
                     "last_name, full_name, start_date, end_date, unique_identifier, source, imported_at "
                     "FROM public.society_officers ORDER BY nzbn, id"):
        out.write(_j({"t": "officer", **r}) + "\n")


def _asks(conn, out) -> None:
    for r in _stream(conn, "societies_asks",
                     "SELECT nzbn, asked_at, ok, officers, entity_type, note FROM public.society_sweep_log "
                     "ORDER BY nzbn"):
        out.write(_j({"t": "ask", **r}) + "\n")


def export(part: str, connect=None) -> bytes:
    """One part's gzip bytes. Read-only, every statement under a time limit; run once."""
    import io
    from support import db
    connect = connect or (lambda name: db.connect(db.OLD_READ_KEY, name, connect_timeout=10))
    buf = io.StringIO()
    with connect("nzbn_canonical") as c:
        c.execute("SET statement_timeout = '300s'")
        c.execute("SET default_transaction_read_only = on")
        buf.write(_j(_header(c, part)) + "\n")
        {"societies": _societies, "officers": _officers, "asks": _asks}[part](c, buf)
    return gzip.compress(buf.getvalue().encode("utf-8"), compresslevel=6, mtime=0)


def copy_all(conn, exports: dict = None, log=None) -> tuple:
    """The three parts landed from the store. Returns
    ([(part, DocumentRef, name, exported at)], [(item, why)])."""
    landed = []
    for part, (name, sha) in (exports or EXPORTS).items():
        if not sha or not os.path.exists(path_for(sha)):
            raise LookupError(f"the societies {part} export {sha or '(not pinned)'} is not in the document store")
        ref, new = land(read_bytes(sha), name=name, source=SOURCE, conn=conn, fetched_at=EXPORTED_AT,
                        content_type="application/gzip")
        if log:
            log(f"societies: {'landed' if new else 'held'} {ref.sha256[:12]} {name}")
        landed.append((part, ref, name, EXPORTED_AT))
    return landed, []


def land_proof(conn, log=None) -> list:
    """The five proved answers registered in this database's store (their
    bytes are in the store already). Returns [(sha256, fetched at)]."""
    out = []
    for sha, at in PROOF:
        if not os.path.exists(path_for(sha)):
            raise LookupError(f"the societies proof answer {sha} is not in the document store")
        data = read_bytes(sha)
        nzbn = str(json.loads(data)["nzbn"])
        ref, new = land(data, name=entity_url(nzbn), source=SOURCE, conn=conn, name_kind="url", fetched_at=at,
                        content_type="application/json")
        if log:
            log(f"societies: {'landed' if new else 'held'} {sha[:12]} {nzbn}")
        out.append((sha, at))
    return out


# --- the nightly ask -------------------------------------------------------------------------------------------

def is_party_society(name: str, status: str = "registered") -> bool:
    return bool(name) and status == "registered" and bool(PARTY_NAME.search(name)) and not PARTY_NOT.search(name)


def slice_for(societies: list, asked: dict, nights: int = NIGHTS) -> list:
    """Tonight's NZBNs. `societies`: [(nzbn, name, status)] of the registered
    societies; `asked`: nzbn → when last asked (ISO), absent for never. The
    party societies every night, then the stalest ceil(n / nights): never
    asked first, then oldest ask, then NZBN, so the order is the coverage."""
    party = sorted(n for n, name, status in societies if is_party_society(name, status))
    rest = sorted((n for n, name, status in societies if n not in set(party)),
                  key=lambda n: (n in asked, asked.get(n) or "", n))
    share = -(-len(societies) // nights)
    return party + rest[:max(0, share - len(party))]


def api_key() -> str:
    """Our NZBN key, read now from its credential file. Never print it."""
    try:
        with open(KEY_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(KEY_NAME + "="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    except OSError as exc:
        raise RuntimeError(f"no NZBN credential file: {type(exc).__name__}") from None
    raise RuntimeError(f"{KEY_NAME} is not set in {os.path.basename(KEY_FILE)}")


def entity_url(nzbn: str) -> str:
    if not re.fullmatch(r"94\d{11}", nzbn or ""):
        raise ValueError(f"not an NZBN: {nzbn!r}")
    return f"{BASE}/entities/{nzbn}"


def fetch_entity(nzbn: str, conn=None, *, key: str = None, fetch=None, pacer=None, positions_dir: str = None,
                 ledger_dir: str = None):
    """One gated ask. Returns (Fetched, DocumentRef or None): the bytes are
    landed only when the register answered 200 with JSON; a refusal raises
    (fetchgate.Refused), a block comes back as `blocked`."""
    import time
    from support import fetchgate
    url = entity_url(nzbn)
    if fetch is None:
        gap = _LAST.get("at", 0) + LANE_FLOOR_S - time.monotonic()
        if gap > 0:
            time.sleep(gap)
        _LAST["at"] = time.monotonic()
    got = fetchgate.open_url(url, timeout=30, headers={KEY_HEADER: key or api_key(), "Accept": "application/json"},
                             pacer=pacer, fetch=fetch, positions_dir=positions_dir or POSITIONS,
                             ledger_dir=ledger_dir)
    if got.blocked or got.status != 200:
        return got, None
    try:
        json.loads(got.body)
    except ValueError:
        got.blocked = "HTTP 200 that is not JSON: a failed read"
        return got, None
    at = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    ref, _ = land(got.body, name=url, source=SOURCE, conn=conn, name_kind="url", fetched_at=at,
                  content_type="application/json")
    return got, ref


ASK_LEDGER = os.path.join(os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live", "checks",
                          "societies-asks.jsonl")
DEFAULT_BUDGET_S = 5 * 3600 - 600


def off_peak(t: dt.datetime) -> bool:
    """01:00 to 06:00 New Zealand time, and never in the API's Wednesday
    21:00 to 23:00 maintenance window."""
    nz = t.astimezone(dt.timezone(dt.timedelta(hours=13)))
    if nz.weekday() == 2 and 21 <= nz.hour < 23:
        return False
    return 1 <= nz.hour < 6


def clock(conn, ledger: str = ASK_LEDGER) -> dict:
    """nzbn → when it was last asked: the lane's asks, the proved answers,
    and the nights' ledger, so a failed ask advances the clock too (old
    C531: a society that always fails must not hold the head of the queue)."""
    asked = {}

    def see(n, at):
        if n and at and at > asked.get(n, ""):
            asked[n] = at
    for n, at in conn.execute("SELECT nzbn, max(asked_at) FROM societies.asks GROUP BY 1"):
        see(n, at.isoformat())
    if os.path.exists(ledger):
        with open(ledger, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                see(r["nzbn"], r["at"])
    return asked


def answers(ledger: str = ASK_LEDGER) -> list:
    """[(sha256, asked at)] of every answer landed: the five proved, then
    every landed line of the nights' ledger, oldest first."""
    out = list(PROOF)
    if os.path.exists(ledger):
        with open(ledger, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if r.get("sha256"):
                    out.append((r["sha256"], r["at"]))
    return sorted(set(out), key=lambda x: (x[1], x[0]))


def night(conn, *, budget_s: float = DEFAULT_BUDGET_S, anytime: bool = False, key: str = None, fetch=None,
          pacer=None, now=None, ledger: str = ASK_LEDGER, log=print) -> dict:
    """One night: the party societies, then the stalest seventh, one gated
    ask each, until the slice, the budget or off-peak ends, or a block."""
    import time
    from support import jobrun
    now = now or (lambda: dt.datetime.now().astimezone())
    started, t0 = jobrun.now(), time.monotonic()
    socs = [(n, name, status) for n, name, status in conn.execute(
        "SELECT nzbn, name, status FROM societies.societies WHERE in_latest AND status = 'registered' "
        "AND nzbn IS NOT NULL")]
    tonight = slice_for(socs, clock(conn, ledger))
    counts = {"slice": len(tonight), "asked": 0, "landed": 0, "not_found": 0, "failed": 0}
    stopped = ""
    key = key or api_key()
    os.makedirs(os.path.dirname(ledger), exist_ok=True)
    for n in tonight:
        if not anytime and not off_peak(now()):
            stopped = "off-peak ended"
            break
        if time.monotonic() - t0 >= budget_s:
            stopped = "budget spent"
            break
        got, ref = fetch_entity(n, conn, key=key, fetch=fetch, pacer=pacer)
        conn.commit()
        counts["asked"] += 1
        counts["landed" if ref else "not_found" if got.status == 404 else "failed"] += 1
        with open(ledger, "a", encoding="utf-8") as f:
            f.write(json.dumps({"nzbn": n, "at": now().isoformat(timespec="seconds"), "status": got.status,
                                "sha256": ref.sha256 if ref else None, "blocked": got.blocked or None}) + "\n")
        if got.blocked:
            stopped = f"a failed read at {n}: {got.blocked}"
            break
    ok = not stopped.startswith("a failed read")
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + (f"; stopped: {stopped}" if stopped else "")
    log("societies capture: " + detail)
    jobrun.record("qv4-societies-capture", ok, detail, started, counts)
    return {**counts, "stopped": stopped, "ok": ok}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    from support.docstore import sha256_file
    if "--export" in argv:
        folder = argv[argv.index("--export") + 1]
        parts = [p for p in argv if p in PARTS] or list(PARTS)
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
    if "--night" in argv:
        from support import db
        budget = float(argv[argv.index("--budget-s") + 1]) if "--budget-s" in argv else DEFAULT_BUDGET_S
        with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
            conn.execute("SET statement_timeout = '60s'")
            return 0 if night(conn, budget_s=budget, anytime="--anytime" in argv)["ok"] else 1
    if "--fetch" in argv:
        from support import db
        nzbns = argv[argv.index("--fetch") + 1:]
        key = api_key()
        with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
            for n in nzbns:
                got, ref = fetch_entity(n, conn, key=key)
                conn.commit()
                print(f"{n}: HTTP {got.status}, {len(got.body)} bytes"
                      + (f", landed {ref.sha256}" if ref else f", not landed: {got.blocked or 'no answer'}"),
                      flush=True)
                if got.blocked:
                    print("a failed read: the run stops (hard limit 6)")
                    return 1
        return 0
    print(__doc__.strip().splitlines()[-1].strip())
    return 2


if __name__ == "__main__":
    sys.exit(main())
