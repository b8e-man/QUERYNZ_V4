"""The lane's one figure against the outside world (contract: the lane): the
agency's own totals. ACC's file prints each territorial authority's claims and
costs, each region's, and a grand total; the reading keeps every level, so
the rows read must add up to the totals the file prints. Exit 1 on any of:

  1. a listed file not read, or read to no row (`reading`)
  2. a data row without its ten years
  3. a territorial authority's printed figure that is not the sum of its
     contract classes, a region's that is not the sum of its authorities, or
     the grand total that is not the sum of the regions (to the cent; claims
     and costs apart; a sum with a suppressed part is skipped and counted,
     never guessed)
  4. fewer comparisons than `MIN_COMPARED` (a check that compares nothing
     passes everything)
  5. a view column that names an address, email, phone or contact
  6. (live) no file held, or no refresh of the catalogue in `STALE_DAYS`

    python -m registers.contract_disclosures.check [--database querynz_v4] [--schema contract_disclosures]
"""
import argparse
import sys

SCHEMA = "contract_disclosures"
STALE_DAYS = 35
MIN_COMPARED = 500
TOLERANCE = 0.02
BARRED = ("address", "email", "phone", "contact", "street")
VIEW_COLUMNS = ("key", "agency", "level", "region", "territorial_authority", "contract_class", "financial_year",
                "year_ended", "active_claims_as_published", "total_costs_as_published", "active_claims",
                "total_costs_nzd", "suppressed", "licence", "attribution", "document", "page", "place", "read_from",
                "reader", "profile", "profile_version")

_SUMS = """
WITH c AS (SELECT * FROM {T}),
pairs AS (
  SELECT p.level AS lvl, p.place, p.financial_year, p.active_claims AS pc, p.total_costs_nzd AS pk, k.active_claims AS kc,
         k.total_costs_nzd AS kk, k.key AS kkey
  FROM c p LEFT JOIN c k ON k.document = p.document AND k.financial_year = p.financial_year AND (
       (p.level = 'territorial authority' AND k.level = 'class' AND k.region IS NOT DISTINCT FROM p.region
        AND k.territorial_authority = p.territorial_authority)
    OR (p.level = 'region' AND k.level = 'territorial authority' AND k.region = p.region)
    OR (p.level = 'total' AND k.level = 'region'))
  WHERE p.level <> 'class'),
g AS (
  SELECT lvl, place, financial_year, count(kkey) AS n,
         -- claims compared only where the parent and every part print a number; costs likewise, apart
         CASE WHEN min(pc) IS NOT NULL AND count(kc) = count(kkey) THEN abs(min(pc) - coalesce(sum(kc), 0)) END AS dc,
         CASE WHEN min(pk) IS NOT NULL AND count(kk) = count(kkey) THEN abs(min(pk) - coalesce(sum(kk), 0)) END AS dk
  FROM pairs GROUP BY 1, 2, 3)
SELECT lvl, count(dc) + count(dk) AS compared, 2 * count(*) - count(dc) - count(dk) AS skipped,
       count(*) FILTER (WHERE n = 0 OR dc > %(tol)s OR dk > %(tol)s) AS wrong,
       min(place || ' ' || financial_year) FILTER (WHERE n = 0 OR dc > %(tol)s OR dk > %(tol)s) AS first_wrong
FROM g GROUP BY lvl ORDER BY lvl
"""


def _t(schema, t, shared=False):
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


def sums(conn, schema: str = SCHEMA, shared: bool = False) -> dict:
    """level → (compared, skipped, wrong, the first wrong place)."""
    rows = conn.execute(_SUMS.format(T=_t(schema, "costs", shared)), {"tol": TOLERANCE}).fetchall()
    return {r[0]: tuple(r[1:]) for r in rows}


def reading(conn, schema: str = SCHEMA, listed: dict = None, shared: bool = False) -> list:
    out = []
    files = {r[0]: r[1] for r in conn.execute(f"SELECT document, cells_read FROM {_t(schema, 'read_files', shared)}")}
    for sha in (listed or {}):
        if sha not in files:
            out.append(f"{sha[:12]}… is listed and was not read")
    for sha, n in files.items():
        if not n:
            out.append(f"{sha[:12]}… was read to no row")
    bad = conn.execute(f"SELECT count(*) FROM (SELECT document, place FROM {_t(schema, 'costs', shared)} "
                       "GROUP BY 1, 2 HAVING count(*) <> 10) x").fetchone()[0]
    if bad:
        out.append(f"{bad} data rows without their ten years")
    s = sums(conn, schema, shared)
    compared = sum(v[0] for v in s.values())
    for lvl, (n, skipped, wrong, first) in sorted(s.items()):
        if wrong:
            out.append(f"{wrong} of {n} {lvl} figures are not the sum of the level below (first: {first})")
    if files and compared < MIN_COMPARED:
        out.append(f"only {compared} printed totals compared; at least {MIN_COMPARED} are expected")
    for c in VIEW_COLUMNS:
        if any(b in c for b in BARRED):
            out.append(f"the view has a column {c!r}")
    return out


def outside(conn, schema: str = SCHEMA) -> list:
    if conn.execute("SELECT to_regclass(%s)", (f"{schema}.capture_runs",)).fetchone()[0] is None:
        return ["the capture has never run"]
    out = reading(conn, schema)
    if not conn.execute(f"SELECT count(*) FROM {schema}.read_files").fetchone()[0]:
        out.append("no file is held and read")
    age = conn.execute(f"SELECT extract(day FROM now() - max(started_at)) FROM {schema}.capture_runs "
                       "WHERE requests > 0").fetchone()[0]
    if age is None or age >= STALE_DAYS:
        out.append(f"no request to the catalogue in {STALE_DAYS} days")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m registers.contract_disclosures.check")
    ap.add_argument("--database", default="querynz_v4")
    ap.add_argument("--schema", default=SCHEMA)
    a = ap.parse_args(argv)
    from support import db
    key = db.READ_KEY if a.database == "querynz_v4" else db.OWNER_KEY
    with db.connect(key, a.database) as conn:
        problems = outside(conn, a.schema) if a.schema == SCHEMA else reading(conn, a.schema)
        s = sums(conn, a.schema) if not problems or a.schema != SCHEMA else {}
    for lvl, (n, skipped, wrong, _) in sorted(s.items()):
        print(f"{SCHEMA}: {lvl}: {n} printed figures compared, {skipped} skipped (suppressed), {wrong} wrong")
    for p in problems:
        print(f"{SCHEMA}: RED: {p}")
    print(f"{SCHEMA}: " + ("reconciles; 0 problems" if not problems else f"{len(problems)} problems"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
