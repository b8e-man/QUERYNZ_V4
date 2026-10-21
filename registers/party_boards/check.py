"""The lane's check against the world outside it (contract: the lane), and
its counts.

The outside figure is the capture's own list. The old job's manifest says
which pages it captured, for which party, from which address and on which
day; every one it lists in the window must be a page row here under the
same hash, address and day, read or a drop-note with its reason, and every
page before the window listed as not landed. A capture missing, or a page
row the manifest does not list, fails the check; so does a page read with
no row behind it, or a row whose page is not marked read.

The counts are what Arthur reads: role rows per party, the distinct roles
and names each party declares, and pages by what became of them, with
every drop-note reason and its count (the pages the profile's markers do
not recognise).

Beside them, for information and never failing: the frozen site's party
boards (its `party_asserted` members, which the old code read from these
pages and from the whole-site crawl) against this lane's names from the
same address. The two read the same bytes differently, and the frozen side
also read pages this capture does not hold.

    counts(roles, pages)                        the figures
    against_manifest(pages, manifest)           [why it fails]
    python -m registers.party_boards.check [--schema party_boards | scratch_<session>] [--database querynz_v4] [--frozen]

Read-only.
"""
import collections
import glob
import json
import os
import sys

from registers.party_boards import capture


def counts(roles: list, pages: list) -> dict:
    by_party = collections.defaultdict(lambda: {"rows": 0, "roles": set(), "names": set(), "pages read": 0})
    for r in roles:
        p = by_party[r["party"]]
        p["rows"] += 1
        p["roles"].add(r["role"].lower())
        p["names"].add(r["name"].lower())
    status = collections.Counter()
    reasons = collections.Counter()
    for pg in pages:
        if pg["capture_kind"] == "manifest":
            continue
        status[pg["status"]] += 1
        if pg["status"] == "drop-note":
            reasons[pg["reason"]] += 1
        if pg["status"] == "read" and pg["rows"]:
            by_party[pg["party"]]["pages read"] += 1
    for pg in pages:
        if pg.get("party") and pg["party"] not in by_party:
            by_party[pg["party"]]
    return {"rows": len(roles), "by_party": {k: {**v, "roles": len(v["roles"]), "names": len(v["names"])}
                                              for k, v in sorted(by_party.items())},
            "status": dict(status), "drop_reasons": dict(reasons.most_common()),
            "unrecognised": status.get("drop-note", 0)}


def against_manifest(pages: list, manifest: list, roles: list = None) -> list:
    why = []
    have = {(p["document"], p["ts"], p["url"]): p for p in pages if p["capture_kind"] != "manifest"}
    want = {(c.sha256, c.ts, c.url): c for c in manifest}
    for k, c in want.items():
        p = have.get(k)
        if p is None:
            why.append(f"the manifest lists {c.sha256[:12]} ({c.party}, {c.ts}) and no page row holds it")
            continue
        if capture.in_window(c) != (p["status"] != "before the window, not landed"):
            why.append(f"{c.sha256[:12]} ({c.ts}): landed or not, against the window")
        if p["party"] != c.party or str(p["captured_on"]) != c.captured_on:
            why.append(f"{c.sha256[:12]}: the page row's party or day is not the manifest's")
    for k in have.keys() - want.keys():
        why.append(f"a page row {k[0][:12]} ({k[1]}) the manifest does not list")
    if roles is not None:
        cited = collections.Counter(r["document"] for r in roles)
        for p in pages:
            if p["capture_kind"] == "manifest" or not p["rows"]:
                continue
            if p["status"] != "read" or cited[p["document"]] != p["rows"]:
                why.append(f"{p['document'][:12]}: {p['rows']} row(s) on its page row, {cited[p['document']]} cited")
        read_docs = {p["document"] for p in pages if p["status"] == "read"}
        for d in cited.keys() - read_docs:
            why.append(f"{d[:12]}: rows cite a page not marked read")
    return why


FROZEN = os.path.join(capture.OLD_LIVE, "var", "pi-snapshot")
FROZEN_VERSIONS = os.path.join(FROZEN, "v")


def frozen_current() -> str:
    """The frozen site's newest published version (its RELEASES.jsonl's last
    `publish`), read as the comparison reads it; None where none is held."""
    last = None
    try:
        with open(os.path.join(FROZEN, "RELEASES.jsonl"), encoding="utf-8") as f:
            for line in f:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if row.get("action") == "publish" and row.get("version"):
                    last = row["version"]
    except OSError:
        return None
    return last if last and os.path.isdir(os.path.join(FROZEN_VERSIONS, last)) else None


def frozen_boards(version_dir: str) -> dict:
    """(party, address) → {name lower} from the frozen site's party pages."""
    out = collections.defaultdict(set)
    for f in glob.glob(os.path.join(version_dir, "data", "subject", "party", "*.json")):
        with open(f, encoding="utf-8") as fh:
            doc = json.load(fh)
        board = (doc.get("board") or {}).get("party_asserted") or {}
        for m in board.get("members") or []:
            out[(doc.get("name") or os.path.basename(f), (m.get("source_url") or "").rstrip("/"))].add(m["name"].lower())
    return out


def _rows(conn, sql: str) -> list:
    cur = conn.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur]


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else "party_boards"
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    from registers.party_boards.load import table
    shared = schema.startswith("scratch_")
    with db.connect(db.READ_KEY if database == "querynz_v4" else db.OWNER_KEY, database) as conn:
        roles = _rows(conn, f"SELECT party, url, document, name, role FROM {table(schema, 'roles', shared)}")
        pages = _rows(conn, f"SELECT document, ts, url, party, captured_on, capture_kind, status, reason, rows "
                            f"FROM {table(schema, 'pages', shared)}")
    c = counts(roles, pages)
    print(f"{c['rows']} declared board role row(s)")
    for party, v in c["by_party"].items():
        print(f"  {party}: {v['rows']} row(s), {v['roles']} distinct role(s), {v['names']} distinct name(s), "
              f"from {v['pages read']} page(s)")
    print("pages: " + ", ".join(f"{k} {n}" for k, n in sorted(c["status"].items())))
    print(f"unrecognised (drop-notes): {c['unrecognised']}")
    for reason, n in c["drop_reasons"].items():
        print(f"  {n:4}  {reason}")
    manifest = capture.manifest()
    if shared:                                      # the sample holds a few pages: the manifest's lines for those
        held = {p["document"] for p in pages}
        manifest = [cp for cp in manifest if cp.sha256 in held]
    why = against_manifest(pages, manifest, roles)
    if "--frozen" in argv:
        cur = frozen_current()
        if cur:
            frozen = frozen_boards(os.path.join(FROZEN_VERSIONS, cur))
            ours = collections.defaultdict(set)
            for r in roles:
                ours[r["url"].rstrip("/")].add(r["name"].lower())
            print(f"against the frozen site {cur} (information; the frozen side also read the whole-site crawl):")
            for (party, url), names in sorted(frozen.items()):
                if url in ours:
                    print(f"  {party} {url}: frozen {len(names)}, here {len(ours[url])}, in both {len(names & ours[url])}")
    for w in why:
        print("FAILS " + w)
    return 1 if why else 0


if __name__ == "__main__":
    sys.exit(main())
