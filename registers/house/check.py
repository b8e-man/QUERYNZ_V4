"""The lane's check against the world outside it (contract: the lane).

Three of the Commission's own published figures, and Stats NZ's names:

  nominations   the release for a general election states its candidates:
                the total, list only, electorate only for registered
                parties, independent or unregistered, both, and per party
                its list and electorate candidates. Each is counted again
                from the candidate rows (2026: 530, 61, 22, 65, 382).
  seats         the overall result states each party's electorate, list and
                total seats. Each is counted again from the members the
                successful-candidates page returned (2020: 120; 2023: 122).
  margins       the status page prints each electorate's margin between its
                two leading candidates; each is counted again from the
                result page's votes where that page is held (2020: 70;
                2023: 71, Port Waikato's poll cancelled).
  electorates   every electorate of an election fought on a boundary set
                held joins Stats NZ's name for it (2020 and 2023: 72 of 72).

A figure that differs, a figure the release states and the lane cannot
count, or an electorate unjoined fails the check. Read-only.

    compare(candidates, members, electorates, figures)   the comparisons
    failed(out)                                          why it fails, as lines
    python -m registers.house.check [--schema house | scratch_<session>] [--database querynz_v4]
"""
import re
import sys

_KEYS = ("candidates", "list_only", "electorate_only", "independent_or_unregistered", "both",
         "list_total", "electorate_total")


def _pk(p) -> str:
    return re.sub(r"[^a-z0-9]", "", (p or "").lower().replace("’", "'"))


def nominations(candidates: list, figures: list, election: str) -> list:
    """[(what, party, stated, counted)] for one general election's release."""
    stated = [f for f in figures if f["election"] == election and f["key"].startswith(f"{election}/nominations/")
              and f["what"] != "pdf places equal"]
    if not stated:
        return []
    rows = [c for c in candidates if c["election"] == election]
    registered = {_pk(f["party"]) for f in stated if f["party"]}
    reg = [c for c in rows if _pk(c["party"]) in registered]
    count = {
        "candidates": len(rows),
        "list_only": sum(1 for c in rows if c["list_place"] is not None and c["electorate"] is None),
        "electorate_only": sum(1 for c in reg if c["electorate"] is not None and c["list_place"] is None),
        "independent_or_unregistered": sum(1 for c in rows if c["electorate"] is not None and _pk(c["party"]) not in registered),
        "both": sum(1 for c in rows if c["electorate"] is not None and c["list_place"] is not None),
        "list_total": sum(1 for c in rows if c["list_place"] is not None),
        "electorate_total": sum(1 for c in reg if c["electorate"] is not None),
        "registered_parties": len(registered),
    }
    out = []
    for f in stated:
        if f["party"] is None:
            out.append((f["what"], None, f["value"], count.get(f["what"])))
        else:
            mine = [c for c in rows if _pk(c["party"]) == _pk(f["party"])]
            n = (sum(1 for c in mine if c["list_place"] is not None) if f["what"] == "list candidates"
                 else sum(1 for c in mine if c["electorate"] is not None))
            out.append((f["what"], f["party"], f["value"], n))
    return out


def seats(members: list, figures: list, election: str) -> list:
    """[(what, party, stated, counted)] for one election's overall result."""
    stated = [f for f in figures if f["election"] == election and "/seats/" in f["key"]]
    rows = [m for m in members if m["election"] == election]
    out = []
    for f in stated:
        mine = rows if f["party"] == "Total" else [m for m in rows if _pk(m["party"]) == _pk(f["party"])]
        n = {"electorate seats": sum(1 for m in mine if m["route"] == "electorate"),
             "list seats": sum(1 for m in mine if m["route"] == "list"),
             "total seats": len(mine)}[f["what"]]
        out.append((f["what"], f["party"], f["value"], n))
    parties = {_pk(f["party"]) for f in stated}
    for m in rows:
        if _pk(m["party"]) not in parties:
            out.append(("total seats", m["party"], 0, 1))
    return out


def margins(candidates: list, electorates: list, figures: list) -> dict:
    """{election: (margins stated, margins equal)}: the status page's margin
    against the leading two candidates' votes on the electorate's own
    result page, where that page is held."""
    held = {e["key"] for e in electorates if e["result_held"] and not e["poll_cancelled"]}
    votes = {}
    for c in candidates:
        if c["electorate"] in held and c["votes"] is not None:
            votes.setdefault(c["electorate"], []).append(c["votes"])
    out = {}
    for f in figures:
        if f["what"] != "margin":
            continue
        ekey = f["key"].replace("/status/", "/").rsplit("/margin", 1)[0]
        if ekey not in held:
            continue
        top = sorted(votes.get(ekey, []), reverse=True)[:2]
        stated, equal = out.get(f["election"], (0, 0))
        out[f["election"]] = (stated + 1, equal + (len(top) == 2 and top[0] - top[1] == f["value"]))
    return out


def compare(candidates: list, members: list, electorates: list, figures: list) -> dict:
    out = {"nominations": {}, "seats": {}, "electorates": {}}
    for e in sorted({f["election"] for f in figures}):
        n = nominations(candidates, figures, e)
        if n:
            out["nominations"][e] = n
        s = seats(members, figures, e)
        if s:
            out["seats"][e] = s
    for e in sorted({x["election"] for x in electorates}):
        rows = [x for x in electorates if x["election"] == e]
        if any(x["join_basis"] in ("exact", "not joined") or x["statsnz_code"] for x in rows):
            out["electorates"][e] = (len(rows), sum(1 for x in rows if x["statsnz_code"]))
    out["margins"] = margins(candidates, electorates, figures)
    pdf = [f for f in figures if f["what"] == "pdf places equal"]
    out["pdf"] = {f["election"]: (f["value"], sum(1 for c in candidates if c["election"] == f["election"]
                                                  and c["list_place"] is not None)) for f in pdf}
    return out


def failed(out: dict) -> list:
    why = []
    for e, rows in out["nominations"].items():
        for what, party, stated, counted in rows:
            if counted != stated:
                why.append(f"{e} nominations, {what}{' of ' + party if party else ''}: the Commission states "
                           f"{stated}, the rows count {counted}")
    for e, rows in out["seats"].items():
        for what, party, stated, counted in rows:
            if counted != stated:
                why.append(f"{e} {what} of {party}: the Commission states {stated}, the members count {counted}")
    for e, (n, joined) in out["electorates"].items():
        if joined != n:
            why.append(f"{e}: {joined} of {n} electorates join Stats NZ's names")
    for e, (stated, equal) in out.get("margins", {}).items():
        if equal != stated:
            why.append(f"{e}: {equal} of {stated} of the status page's margins equal the result pages' votes")
    for e, (equal, listed) in out.get("pdf", {}).items():
        if equal != listed:
            why.append(f"{e}: the PDF agrees with {equal} of {listed} list places")
    return why


def report(out: dict) -> list:
    lines = []
    for e, rows in out["nominations"].items():
        diff = sum(1 for r in rows if r[2] != r[3])
        tot = next((r for r in rows if r[0] == "candidates"), None)
        lines.append(f"{e} nominations: {len(rows) - diff} of {len(rows)} of the Commission's figures equal"
                     + (f" (candidates {tot[3]} against {tot[2]})" if tot else ""))
    for e, rows in out["seats"].items():
        diff = sum(1 for r in rows if r[2] != r[3])
        tot = next((r for r in rows if r[1] == "Total" and r[0] == "total seats"), None)
        lines.append(f"{e} seats: {len(rows) - diff} of {len(rows)} of the overall result's figures equal"
                     + (f" (members {tot[3]} against {tot[2]})" if tot else ""))
    for e, (n, joined) in out["electorates"].items():
        lines.append(f"{e} electorates: {joined} of {n} join Stats NZ's names")
    for e, (stated, equal) in out.get("margins", {}).items():
        lines.append(f"{e} margins: {equal} of {stated} of the status page's margins equal the result pages' votes")
    for e, (equal, listed) in out.get("pdf", {}).items():
        lines.append(f"{e} party lists: the Commission's PDF agrees with {equal} of {listed} places")
    return lines


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else "house"
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    from registers.house.load import table
    shared = schema.startswith("scratch_")

    def rows(conn, t):
        cur = conn.execute(f"SELECT * FROM {table(schema, t, shared)}")
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur]

    with db.connect(db.READ_KEY if database == "querynz_v4" else db.OWNER_KEY, database) as conn:
        got = {t: rows(conn, t) for t in ("candidates", "members", "electorates", "figures")}
    out = compare(got["candidates"], got["members"], got["electorates"], got["figures"])
    for line in report(out):
        print(line)
    why = failed(out)
    for w in why:
        print("FAILS " + w)
    return 1 if why else 0


if __name__ == "__main__":
    sys.exit(main())
