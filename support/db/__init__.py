"""The new database's shape, and the logins (plan step 1.8).

Two databases on the server that feeds the frozen site: `querynz_v4` (the
real one) and `querynz_v4_sample` (filled from each module's sample list;
for building, never for measuring). Both have the same schemas:

  pub               published tables: the only thing a later module reads
  links, links_private
  <lane>, <lane>_private        one pair per register lane
  <product>                     one per product shape, and the board
  docs                          the document store (step 1.10)
  sealed                        the seal: director home addresses as
                                published before 18 November 2026; never read
                                by the session reader
  scratch_<session>             one per session, made and dropped by the fast tier

A person's home address is kept only in a schema whose name ends `_private`,
and in `sealed`. The session reader (`qv4_read`) is granted everything
else, with default privileges so later tables follow; the product reader
(`qv4_product`) is granted `pub` only. Every login is Arthur's (step 0);
this module never creates a role or a database.

Connection strings come from the credential files in the home folder at the
moment of use and are never printed, logged or returned to a caller that
prints (hard limit 1). `url()` reads one key; `connect()` opens psycopg.

    python -m support.db plan            print the SQL that would run
    python -m support.db apply           create schemas and grants, both databases
    python -m support.db scratch NAME    make scratch_NAME in the sample database
    python -m support.db check           every schema present, grants right

The owner login on the live database `querynz_v4` is refused to a session
that carries no mark (card a-lanes-job-path-published-live-from-a-session-
before-the-gate): a session proves a load in its scratch schema in the
sample database, and the live tables are written by the scheduler and the
gate. A session is a process with CLAUDECODE in its environment; the marks
are QV4_PIECE or QV4_RUN_ID (the scheduler's worker, on every job it runs)
and QV4_INTEGRATOR=1 (the integrator's shell: the gate, the installer, the
catalogue commands, its hand runs). The installed units carry no mark and
are not sessions, so they pass. The sample database and the reader logins
are never refused.

Tests: support/db/tests/ (the SQL without a database; the apply against
the sample database, marked slow)."""
import os
import re
import sys

CRED_DIR = os.environ.get("QV4_CRED_DIR") or os.path.expanduser("~/.querynz")
OWNER_KEY, READ_KEY, PRODUCT_KEY, OLD_READ_KEY = "QV4_OWNER_URL", "QV4_READ_URL", "QV4_PRODUCT_URL", "QV4_OLD_READ_URL"
KEY_FILE = {OWNER_KEY: "v4.env", OLD_READ_KEY: "v4.env", READ_KEY: "v4-read.env", PRODUCT_KEY: "v4-read.env"}
ROLES = {"owner": "qv4_owner", "read": "qv4_read", "product": "qv4_product"}
DATABASES = ("querynz_v4", "querynz_v4_sample")
LIVE = "querynz_v4"
SESSION_VAR = "CLAUDECODE"
MARKS = ("QV4_PIECE", "QV4_RUN_ID")      # set by the scheduler's worker
INTEGRATOR_MARK = "QV4_INTEGRATOR"       # =1 in the integrator's shell

LANES = (
    "charities", "companies", "parties", "party_returns", "candidate_returns", "disclosures",
    "party_finance", "house", "mp_interests", "expenses", "gazette", "societies",
    "hansard", "linz", "tenders", "papers_past",
    "tenancy_tribunal", "real_estate_authority",   # track E, the windowed sources (18 October 2026)
    "party_boards",   # the declared tier, built not deployed (ruling 72, 21 October 2026)
    "openlaw",   # step 5.4, held on the interface's terms (openlaw-1, 21 October 2026)
    "courts",   # step 5.4, the senior courts' judgments (courts-1, 21 October 2026)
    "limited_partnerships", "building_practitioners", "sanctions",   # step 5.3 (sanctions-1, 21 October 2026)
    "commerce_commission", "fma", "worksafe",   # step 5.3, the regulator actions (regulators-1, 21 October 2026)
    "overseas_investment",   # step 5.3, the overseas investment decisions (oio-1, 21 October 2026)
    "hdc_decisions",   # step 5.3, held on the Commissioner's copyright terms (hdc-1, 21 October 2026)
    "grants",   # step 6.3, class 4 society and Lottery grants (grants-1, 21 October 2026)
    "iwi_directory",   # step 6.2 template 3, Te Kāhui Māngai (settlements-1, 22 October 2026)
    "settlement_commitments",   # step 6.2 template 3, Te Haeata, behind a login and watched (settlements-1, 22 October 2026)
    "contract_disclosures",   # step 6.3, agency contract disclosures: ACC's health contract file (procurement-1, 22 October 2026)
    "council_procurement",   # step 6.3, council procurement off GETS: barred by terms or a login, watched (procurement-1, 22 October 2026)
    "council_minutes",   # step 6.3, the InfoCouncil councils' meetings, minutes held unread (councils-1, 23 October 2026)
    "councillor_interests",   # step 6.3, councillors' registers of interests, council by council (councils-1, 23 October 2026)
    "local_elections",   # step 6.3, local election candidate returns, council by council, held unread (local-elections-1, 23 October 2026)
    "beehive",   # ruling 96, the Beehive's releases from the ingest MCP and the old estate's pages (mcp-1, 27 October 2026)
    "ministers_diaries",   # step 6.2, the ministers' diaries from the MCP's parliament-diaries corpus (diaries-2, 27 October 2026)
    "parliament",   # ruling 96, the MCP's seven parliament corpora (parliament-1, 27 October 2026)
)
PRODUCTS = ("ftm", "subject_report", "register_scan", "archive_search", "board")
FIXED = ("pub", "links", "links_private", "docs", "sealed", "scheduler",
         "mcpsource")   # support/mcpsource: the ingest MCP's cursors, arrivals and stamps (ruling 96, mcp-1)
PRIVATE_SUFFIX = "_private"
SCRATCH_PREFIX = "scratch_"
NAME = re.compile(r"^[a-z][a-z0-9_]{0,62}$")


def schemas() -> list:
    out = list(FIXED)
    for lane in LANES:
        out += [lane, lane + PRIVATE_SUFFIX]
    out += list(PRODUCTS)
    return out


def is_private(schema: str) -> bool:
    """True for a schema the session reader never sees."""
    return schema.endswith(PRIVATE_SUFFIX) or schema == "sealed"


def plan_sql(extra_schemas=()) -> str:
    """Idempotent SQL: every schema, owned by the owner; the session reader
    on every non-private schema with default privileges; the product reader
    on pub only."""
    owner, read, product = ROLES["owner"], ROLES["read"], ROLES["product"]
    lines = ["-- generated by support.db; idempotent", f"REVOKE ALL ON SCHEMA public FROM PUBLIC;"]
    for s in list(schemas()) + list(extra_schemas):
        if not NAME.match(s):
            raise ValueError(f"not a schema name: {s!r}")
        lines.append(f"CREATE SCHEMA IF NOT EXISTS {s} AUTHORIZATION {owner};")
        if is_private(s):
            lines.append(f"REVOKE ALL ON SCHEMA {s} FROM {read}, {product};")
            lines.append(f"REVOKE ALL ON ALL TABLES IN SCHEMA {s} FROM {read}, {product};")
            lines.append(f"ALTER DEFAULT PRIVILEGES FOR ROLE {owner} IN SCHEMA {s} REVOKE ALL ON TABLES FROM {read}, {product};")
            continue
        lines.append(f"GRANT USAGE ON SCHEMA {s} TO {read};")
        lines.append(f"GRANT SELECT ON ALL TABLES IN SCHEMA {s} TO {read};")
        lines.append(f"GRANT SELECT ON ALL SEQUENCES IN SCHEMA {s} TO {read};")
        lines.append(f"ALTER DEFAULT PRIVILEGES FOR ROLE {owner} IN SCHEMA {s} GRANT SELECT ON TABLES TO {read};")
        lines.append(f"ALTER DEFAULT PRIVILEGES FOR ROLE {owner} IN SCHEMA {s} GRANT SELECT ON SEQUENCES TO {read};")
        if s == "pub":
            lines.append(f"GRANT USAGE ON SCHEMA {s} TO {product};")
            lines.append(f"GRANT SELECT ON ALL TABLES IN SCHEMA {s} TO {product};")
            lines.append(f"ALTER DEFAULT PRIVILEGES FOR ROLE {owner} IN SCHEMA {s} GRANT SELECT ON TABLES TO {product};")
        else:
            lines.append(f"REVOKE ALL ON SCHEMA {s} FROM {product};")
    return "\n".join(lines) + "\n"


def scratch_sql(session: str) -> str:
    s = SCRATCH_PREFIX + re.sub(r"[^a-z0-9_]", "_", session.lower())
    if not NAME.match(s):
        raise ValueError(f"not a schema name: {s!r}")
    return f"CREATE SCHEMA IF NOT EXISTS {s} AUTHORIZATION {ROLES['owner']};\n"


def url(key: str = OWNER_KEY, database: str = None) -> str:
    """A connection string from its credential file, read now. Never print
    the result. `database` swaps the database name at the end of the URL."""
    path = os.path.join(CRED_DIR, KEY_FILE[key])
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(key + "="):
                    val = line.split("=", 1)[1].strip().strip("\"'")
                    if database:
                        val = re.sub(r"/[A-Za-z0-9_]+(\?.*)?$", lambda m: "/" + database + (m.group(1) or ""), val)
                    return val
    except OSError as exc:
        raise RuntimeError(f"no credential file for {key}: {type(exc).__name__}") from None
    raise RuntimeError(f"{key} is not set in {os.path.basename(path)}")


class LiveRefused(RuntimeError):
    """An owner connection to the live database from an unmarked session."""


def _database_of(key: str, database: str = None) -> str:
    if database:
        return database
    m = re.search(r"/([A-Za-z0-9_]+)(\?.*)?$", url(key))
    return m.group(1) if m else ""


def marked(env=None) -> bool:
    """True where the caller may write the live database: not a session,
    or a session the scheduler or the integrator marked."""
    env = os.environ if env is None else env
    if not env.get(SESSION_VAR):
        return True
    return env.get(INTEGRATOR_MARK) == "1" or any(env.get(m) for m in MARKS)


def guard(key: str = OWNER_KEY, database: str = None, env=None) -> None:
    """Raise LiveRefused for the owner login on the live database from an
    unmarked session; anything else passes."""
    if key != OWNER_KEY or marked(env) or _database_of(key, database) != LIVE:
        return
    raise LiveRefused(
        f"support.db: the owner login on the live database {LIVE} is refused to a session without a mark "
        f"(QV4_PIECE from the scheduler's worker, or {INTEGRATOR_MARK}=1 from the integrator), because a session "
        f"proves a load in its scratch schema in {LIVE}_sample only and the live tables are written by the "
        f"scheduler and the merge gate.")


def connect(key: str = OWNER_KEY, database: str = None, **kw):
    guard(key, database)
    import psycopg
    return psycopg.connect(url(key, database), **kw)


def apply(database: str, extra_schemas=(), log=print) -> None:
    with connect(OWNER_KEY, database) as conn:
        conn.execute(plan_sql(extra_schemas))
        conn.commit()
    log(f"support.db: {database}: {len(schemas()) + len(extra_schemas)} schemas and their grants applied")


def check(database: str) -> list:
    """Problems found, as plain lines; empty when the shape is right."""
    out = []
    with connect(OWNER_KEY, database) as conn:
        have = {r[0] for r in conn.execute("select nspname from pg_namespace")}
        for s in schemas():
            if s not in have:
                out.append(f"{database}: schema {s} missing")
        rows = conn.execute(
            "select nspname, has_schema_privilege(%s, nspname, 'USAGE'), has_schema_privilege(%s, nspname, 'USAGE') "
            "from pg_namespace where nspname = any(%s)", (ROLES["read"], ROLES["product"], list(schemas()))).fetchall()
        for s, read_ok, product_ok in rows:
            if is_private(s) and read_ok:
                out.append(f"{database}: the session reader can see {s}")
            if not is_private(s) and not read_ok:
                out.append(f"{database}: the session reader cannot see {s}")
            if s == "pub" and not product_ok:
                out.append(f"{database}: the product reader cannot see pub")
            if s != "pub" and product_ok:
                out.append(f"{database}: the product reader can see {s}")
    return out


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or argv[0] not in ("plan", "apply", "scratch", "check"):
        print(__doc__.split("\n\n")[-2])
        return 2
    cmd = argv[0]
    if cmd == "plan":
        print(plan_sql())
        return 0
    if cmd == "scratch":
        if len(argv) != 2:
            print("usage: python -m support.db scratch NAME")
            return 2
        with connect(OWNER_KEY, "querynz_v4_sample") as conn:
            conn.execute(scratch_sql(argv[1]))
            conn.commit()
        print(f"support.db: scratch schema for {argv[1]} is in querynz_v4_sample")
        return 0
    dbs = argv[1:] or list(DATABASES)
    if cmd == "apply":
        for db in dbs:
            apply(db)
        cmd = "check"
    problems = [p for db in dbs for p in check(db)]
    for p in problems:
        print("PROBLEM " + p)
    print("support.db: " + ("shape right" if not problems else f"{len(problems)} problem(s)"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
