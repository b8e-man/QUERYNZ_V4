"""The board's outside check (spec line 4), against the real published
tables through the session reader, never the sample:

  1. A search for a name a published view holds returns that row, with its
     register's count beside it. The name is taken from the table itself at
     run time (the first donor of the largest party return), so the check
     fails if the search or the catalogue breaks, not if the data moves.
  2. A register the plan names but no lane has published says "not held";
     a register whose views are present never does.
  3. Every column the catalogue shows exists in its view (the lanes own
     their views and may rename a column; the board must notice).
  4. No column the board shows is an address column of a person: the only
     address view is the company's registered office (hard limit 15).
  5. The done-when walk (plan 4.9), as far as the published tables allow
     today: a known donor opens; the company behind it is found by name
     (not by link, until links/ publishes); that company's directors open;
     one director's other roles open. Each pane cites its document.
  6. The search tab (ruling 80): the known name is found with only its
     register checked, and not with that register unchecked.
  7. The graph tab (ruling 80): the known donor row is drawn with at least
     one money edge; every edge's far end is a row that exists; no edge type
     is an address; every relation column the catalogue names exists in its
     view and in the view it is matched to (with 3).

  python -m products.board check [--term NAME]      exit 1 on any failure
"""
from __future__ import annotations

import re
import sys

from products.board import catalogue as cat
from products.board import db, graph, search, panes, server

ADDRESS_WORDS = re.compile(r"residential|home_address|street|suburb|postal", re.I)


def problems(conn, term: str = None) -> list:
    out = []
    held = db.pub_views(conn)
    # 3. columns
    columns = {}
    for r in db.rows(conn, "select table_name, column_name from information_schema.columns where table_schema = 'pub'"):
        columns.setdefault(r["table_name"], set()).add(r["column_name"])
    for v in cat.VIEWS:
        if v.name not in held:
            out.append(f"{v.name}: in the catalogue but not published (pub.{v.name} missing)")
            continue
        cols = columns.get(v.name, set())
        for rel in v.relations:
            if rel.column not in cols:
                out.append(f"{v.name}: a {rel.kind} relation names `{rel.column}`, which pub.{v.name} does not carry")
            if rel.to_column not in columns.get(rel.view, set()):
                out.append(f"{v.name}: a {rel.kind} relation is matched to pub.{rel.view}.{rel.to_column}, which does not exist")
        for c in sorted(cat.columns_shown(v) | set(v.search) | set(v.numbers) | set(v.names) | {v.key_col}):
            if c not in cols:
                out.append(f"{v.name}: the board shows or searches `{c}`, which pub.{v.name} does not carry")
        for c in cols:
            if ADDRESS_WORDS.search(c) and v.name != "company_addresses":
                out.append(f"{v.name}: carries `{c}`, an address-shaped column outside the registered-office view: rule on it before showing")
    for name in held - {v.name for v in cat.VIEWS} - cat.LINKS_PUBLISHED:
        out.append(f"pub.{name} is published but the board has no entry for it: add it to the catalogue from the lane's pane.md")
    # 2. not held
    for register, _ in cat.NOT_HELD:
        if any(v.register == register for v in cat.VIEWS):
            out.append(f"{register} is listed as not held and also has views in the catalogue")
    for register, _ in cat.REGISTERS:
        if not any(v.name in held for v in cat.views_of(register)):
            out.append(f"{register}: none of its views is published; the first pane will say not held")
    # 1. a search finds a row the table holds
    if term is None:
        donor = db.rows(conn, "select donor from pub.party_return_donors where donor is not null order by amount desc nulls last, key limit 1")
        term = donor[0]["donor"] if donor else None
    if not term:
        out.append("no donor row to search for: pub.party_return_donors is empty")
    else:
        res = search.search(conn, term)
        hits = res.get("party_returns", [])
        found = [(v, n, rows) for v, n, rows in hits if v.name == "party_return_donors"]
        if not found:
            out.append(f"a search for {term!r} found no party_return_donors row, which holds it")
        else:
            v, n, rows = found[0]
            if n < 1 or not any(term.lower() in (r.get("donor") or "").lower() for r in rows):
                out.append(f"a search for {term!r} returned {n} party_return_donors rows, none carrying the name")
        page = panes.left_pane(term, search.held_registers(held), tuple(search.held_registers(held)), True)
        if "not held" not in page:
            out.append("the left pane does not say 'not held' for the registers no lane has published")
    # 5. the done-when walk, by name until links exist
    if term and not out:
        walk = []
        res = search.search(conn, term)
        donors = [rows for v, n, rows in res.get("party_returns", []) if v.name == "party_return_donors"]
        if donors:
            d = donors[0][0]
            walk.append(f"party_return_donors:{d['key']}")
            same = search.same_name(conn, cat.BY_NAME["party_return_donors"], d)
            comp = [rows for v, n, rows in same.get("companies", []) if v.name in ("companies", "directors", "shareholders")]
            if comp:
                c = comp[0][0]
                v = cat.BY_NAME[[v.name for v, n, rows in same.get("companies", []) if rows and rows[0] is c][0]]
                company_key = c["key"] if v.name == "companies" else c.get("entity_key")
                if company_key:
                    walk.append(f"companies:{company_key}")
                    kids = search.children(conn, cat.BY_NAME["companies"], {"key": company_key})
                    directors = [rows for j, n, rows in kids if j.view == "directors"]
                    if directors and directors[0]:
                        walk.append(f"directors:{directors[0][0]['key']}")
        html = server.render(term, server.parse_path("|".join(walk)), conn=conn)
        if html.count('<section class="pane') != len(walk) + 2:     # the left pane and the results, then the walk
            out.append(f"the walk from {term!r} rendered {html.count('<section class=\"pane')} panes, expected {len(walk) + 2}")
        if "<h3>Citation</h3>" not in html and walk:
            out.append("a pane in the walk carries no citation")
        if len(walk) < 3:
            out.append(f"the done-when walk reached {len(walk)} panes past the search (donor, company, director wanted); by name, until links exist")
    # 6. the search tab over the check boxes
    if term:
        others = [r for r in search.held_registers(held) if r != "party_returns"]
        only = server.render(term, [], conn=conn, checked=["party_returns"])
        without = server.render(term, [], conn=conn, checked=others)
        if "<strong>party_return_donors</strong>" not in only or "<mark>" not in only:
            out.append(f"the search tab with only party_returns checked did not show {term!r} in party_return_donors, marked")
        if "<strong>party_return_donors</strong>" in without:
            out.append("the search tab with party_returns unchecked still searched party_return_donors")
    # 7. the graph tab
    if any("address" in k for k, _, _ in cat.EDGE_KINDS) or any("address" in r.kind for v in cat.VIEWS for r in v.relations):
        out.append("an edge type named for an address exists (hard limit 15)")
    donor = db.rows(conn, "select key from pub.party_return_donors where return_key is not null and donor is not null "
                          "order by amount desc nulls last, key limit 1")
    if not donor:
        out.append("no donor row with a return to graph")
    else:
        centre = f"party_return_donors:{donor[0]['key']}"
        g = graph.build(conn, "", centre=centre)
        if centre not in g["nodes"] or g["drawn"]["money"] < 1:
            out.append(f"the graph of {centre} drew no money edge")
        for e in g["edges"]:
            if "address" in e["kind"]:
                out.append(f"the graph drew an address edge: {e}")
        for nid in g["nodes"]:
            view, _, key = nid.partition(":")
            if search.row(conn, view, key) is None:
                out.append(f"the graph drew a node for {nid}, which is not a row of pub.{view}")
        page = server.render_graph("", centre, conn=conn)
        if "<svg" not in page or "<script" in page or "<h3>Key</h3>" not in page:
            out.append("the graph tab did not render its picture and key without script")
    return out


def main(argv=None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    term = argv[argv.index("--term") + 1] if "--term" in argv else None
    with db.read_connect() as conn:
        bad = problems(conn, term)
    for b in bad:
        print("PROBLEM " + b)
    print("products.board check: " + ("green" if not bad else f"{len(bad)} problem(s)"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
