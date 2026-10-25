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
  6. The search tab (rulings 80, 81): with "search all" off, the known name
     is found with only its register ticked, and not with it unticked.
  7. The graph tab (ruling 80): the known donor row is drawn with at least
     one money edge; every edge's far end is a row that exists; no edge type
     is an address; every relation column the catalogue names exists in its
     view and in the view it is matched to (with 3). Ruling 84: on that
     graph, a donor row the links join by name alone and the crowded
     graph of a name search (CROWDED), no two texts sit at one place, no
     rule id shows outside a tooltip, and the links' words are on the page.
     Ruling 86 (2): on each, no two text boxes of the rendered SVG touch
     (graph.touching_text, read from its own x, y, anchor, class and text),
     and no edge carries a number.

  8. The field search (ruling 82): every column a field declares exists in
     its view, a date column is a date and a year column a number; a search
     with only the last name "Hart" finds rows, each with HART as a whole
     word of a name, so never HARTNELL alone.
  9. Name order (ruling 85) and near matches (ruling 83): every Name a view
     declares has an order; the known donor a party return files surname
     first (KNOWN_REVERSED, "MILLS PHILLIP", on a form that fixes no order)
     is among the exact results for first Phillip, last Mills and not under
     "Near matches"; a registered office is found as near by a query with
     its level left off and its street type spelled the other way.
 10. No home address reaches any result (hard limit 15): the address field
     reads only catalogue.ADDRESS_COLUMNS and no person's view declares an
     address; a search for each word of the comparison's residence
     vocabulary, in the box and in the address field, returns no person's
     name with a residence after it (carries_residence) and no address
     outside those columns.

 11. Donations summed (ruling 86 (3)): the known donor, filed under one name
     in returns of two years or more to one party, gets one party edge whose
     total equals the amounts listed under it as added and the register's
     own sum (gift_problems).
 12. The originating document (rulings 86 (4), 88): /doc/ of a known cited
     document answers 200 with its stored content type and its own bytes; a
     wrong sha and a name that is not 64 hex characters answer 404; a party
     return answers 200 with its stored content type; a cited document of
     every source the published rows cite answers 200 with its own bytes;
     the row's citation begins with "source" (doc_problems).
 13. Night mode (ruling 86 (1)): every text colour of the stylesheet reads at
     4.5:1 or more on every background it sets; the key's edges at 3:1 on the
     picture and apart (panes.contrast_problems).
 14. The use cases tab (ruling 87): the copy the board runs from renders the
     plan's seventeen rows in its order. Ruling 89: every template folder
     under products/templates/ and products/scan/templates/ binds to exactly
     one row (the scan shape's own two, SHAPE_OWN, apart), an orphan fails;
     each use case with an interface opens it in a new tab, 15 to 17 say what
     holds them.
 15. The connection counter (ruling 90): on the page, "db n/max", n >= 1.
 16. Key columns read as names (ruling 92 (2)): every pointer column and
     its far column exist; a director's row, in the results pane and its
     own pane, shows its company's name as a link with the key on hover,
     never the bare key (far_problems).

  python -m products.board check [--term NAME]      exit 1 on any failure
"""
from __future__ import annotations

import decimal
import re
import sys
import urllib.parse

from products.board import catalogue as cat
from products.board import db, document, graph, links_view, near, search, panes, server, uses

ADDRESS_WORDS = re.compile(r"residential|home_address|street|suburb|postal", re.I)
#: the comparison's residence vocabulary (checks/comparison.py RESIDENCE_WORDS; tests/test_check_vocabulary.py holds the two equal):
#: a residence word in a person's name field is a home address reaching a result
RESIDENCE_WORDS = ("retirement village", "rest home", "resthome", "lifecare", "care home", "retirement")
#: a donor a party return files surname first ("MILLS PHILLIP"; keys/names.py names the case): exact, not near, since
#: the donor form fixes no order (ruling 85)
KNOWN_REVERSED = ("Phillip", "Mills")
DATE_TYPES = {"date", "timestamp with time zone", "timestamp without time zone"}


def problems(conn, term: str = None) -> list:
    out = []
    held = db.pub_views(conn)
    # 3. columns
    columns = {}
    types = {}
    for r in db.rows(conn, "select table_name, column_name, data_type from information_schema.columns where table_schema = 'pub'"):
        columns.setdefault(r["table_name"], set()).add(r["column_name"])
        types[(r["table_name"], r["column_name"])] = r["data_type"]
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
        page = panes.left_pane(term, search.held_registers(held), search.FIRST)
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
        only = server.render(term, [], conn=conn, boxes=search.Boxes(False, ("party_returns",)))     # "search all" off, the one register on
        without = server.render(term, [], conn=conn, boxes=search.Boxes(False, tuple(others)))
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
        out += picture_problems(conn, centre, g, page)
    out += field_problems(conn, held, columns, types)
    out += gift_problems(conn)
    out += doc_problems(conn)
    out += panes.contrast_problems()
    out += uses_problems(held)
    out += far_problems(conn, held, columns)
    return out


def far_problems(conn, held: set, columns: dict) -> list:
    """16. Ruling 92 (2): every pointer column exists, its far column too;
    a director's company reads as the company's name, linked, key on hover."""
    out = []
    for v in cat.VIEWS:
        if v.name not in held:
            continue
        for c, (fv, fc) in cat.pointers(v).items():
            if c not in columns.get(v.name, set()):
                out.append(f"{v.name}: `{c}` names a {fv} row but pub.{v.name} does not carry it")
            if fv in held and fc not in columns.get(fv, set()):
                out.append(f"{v.name}: `{c}` is matched to pub.{fv}.{fc}, which does not exist")
    d = db.rows(conn, "select d.key, d.last_name, d.entity_key, c.name from pub.directors d join pub.companies c on c.key = d.entity_key "
                      "where not coalesce(d.suppressed, false) and d.last_name ~ '^[A-Za-z]{4,}$' order by d.key limit 1")
    if not d:
        return out + ["no director with a held company to show its company's name"]
    d = d[0]
    want = f'title="{panes.esc(d["entity_key"])}">{panes.esc(d["name"])}</a>'
    pane = server.render("", [f"directors:{d['key']}"], conn=conn)
    if want not in pane:
        out.append(f"the row pane of directors:{d['key']} does not show its company's name linked with the key on hover")
    results = server.render("", [], conn=conn, boxes=search.Boxes(False, ("companies",), (("last", d["last_name"]),)))
    results = results[results.index('id="results"'):]
    cells = re.findall(r"<th>company</th><td>(.*?)</td>", results)
    if not cells or not all(c.startswith('<a class="row"') or c.endswith(f"{panes.NOT_HELD_ROW}</span>") for c in cells):
        out.append(f"the results pane for last name {d['last_name']!r} shows a director's company other than by name or as not held")
    if re.search(r"<td>companies/\d+</td>", results + pane):
        out.append("a company key is shown bare, not as the company's name")
    return out


#: the scan shape's own templates (step 6.1 proves the shape on them); they serve no use case and are not orphans
SHAPE_OWN = {"donors-named-as-companies": "step 6.1, the scan shape's own", "society-officers-liquidations": "step 6.1, the scan shape's own"}
COUNTER = re.compile(r'<span class="db" title="([^"]*)">db (\d+)/(\d+)</span>')


def uses_problems(held: set) -> list:
    """14. The use cases tab renders the plan's rows from the copy the board
    runs from, in the plan's order; every template folder on disk is bound to
    exactly one of its rows (ruling 89), and none is an orphan; a use case
    with templates or a site opens it in a new tab, a held one says what
    holds it and is no link. 15. The nav bar counts the database's
    connections (ruling 90): on the page, at least this one."""
    table = uses.read_text(uses.TABLE)
    if table is None:
        return [f"the plan's use-case table {uses.TABLE} is not in the copy the board runs from"]
    want = [r["number"] for r in uses.parse_table(table)]
    page = server.render_uses()
    got = re.findall(r"<tr><td>(\d+)</td>", page)
    out = []
    if got != want or len(got) != 17:
        out.append(f"the use cases tab shows {len(got)} rows in the order {got}; the plan holds {len(want)}")
    for t in uses.read_templates():
        if t["name"] in SHAPE_OWN and not t["uses"]:
            continue
        if len(t["uses"]) != 1 or t["uses"][0] not in want:
            out.append(f"the template folder {t['folder']} binds to use case(s) {list(t['uses'])}, not to exactly one row of the plan's table: an orphan")
    rows = uses.rows(table, uses.read_text(uses.NOT_HELD), uses.read_templates(), held)
    for r in rows:
        if r["number"] in uses.HELD:
            if r["links"] or uses.HELD[r["number"]] not in page:
                out.append(f"use case {r['number']} is held and must say so without a link")
        elif not r["links"]:
            out.append(f"use case {r['number']} ({r['name']}) has no interface on the tab: {r['held']}")
    for a in re.findall(r"<a [^>]*>", page[page.index('<table class="uc">'):] if '<table class="uc">' in page else ""):
        if 'target="_blank"' not in a or 'rel="noopener"' not in a:
            out.append(f"a link on the use cases tab does not open in a new tab: {a}")
    m = COUNTER.search(page)
    if not m:
        out.append("the nav bar carries no database connection counter (ruling 90), or it says db ?")
    elif int(m.group(2)) < 1 or int(m.group(3)) < int(m.group(2)):
        out.append(f"the connection counter reads db {m.group(2)}/{m.group(3)}; the board's own connection is at least one")
    return out


CROWDED = "smith"
RULE_ID = re.compile(r"\b[a-z]+(?:-[a-z]+)*@\d+\b")


def picture_problems(conn, centre: str, g: dict, page: str) -> list:
    """Ruling 84, on the known donor's graph, on a donor row the links join
    by name alone (so a links edge is drawn) and on a crowded name search: no two labels or numbers
    at the same place or with boxes that meet, no rule id outside a tooltip,
    the links' words on the picture's tooltips and in the list."""
    out = []
    linked = db.rows(conn, "select row_a from pub.links where row_a like 'party_returns:%%' and rule = 'name-only@1' "
                           "order by row_a limit 1")
    cases = [(centre, g, page)]
    if not linked:
        out.append("pub.links joins no party_returns row by name-only@1: the words check has no links edge to read")
    else:
        v = links_view.view_for(conn, *links_view.split_ref(linked[0]["row_a"]))
        c = f"{v.name}:{links_view.split_ref(linked[0]['row_a'])[1]}" if v else ""
        lg = graph.build(conn, "", centre=c) if v else {"edges": []}
        if not any(e.get("rule") for e in lg["edges"]):
            out.append(f"the graph of {c} drew no links edge")
        else:
            cases.append((c, lg, server.render_graph("", c, conn=conn)))
            if cat.rule_words("name-only@1") not in cases[-1][2]:
                out.append(f"the graph of {c} does not say {cat.rule_words('name-only@1')!r}")
    crowd = graph.build(conn, CROWDED)                     # a name search: up to 16 rows and their fans, the picture the ruling saw
    cases.append((f"the search {CROWDED!r}", crowd, graph.pane(crowd, CROWDED)))
    for c, gr, html in cases:
        picture = html[html.index("<svg"):html.index("</svg>")] if "<svg" in html else ""
        at = re.findall(r'<text[^>]* x="([\d.]+)" y="([\d.]+)"', picture)
        if len(at) != len(set(at)):
            out.append(f"the graph of {c} draws {len(at) - len(set(at))} texts at the same place as another")
        met = graph.overlaps(graph.place(gr, graph.layout(gr), graph.lines(gr)))
        if met:
            out.append(f"the graph of {c} places {len(met)} texts touching another, first {met[0]}")
        touching = graph.touching_text(picture)
        if touching:
            out.append(f"the graph of {c} draws {len(touching)} pairs of texts whose boxes touch, first {touching[0]}")
        if re.search(r"<text[^>]*>\d+</text>", picture):
            out.append(f"the graph of {c} draws an edge number (ruling 86 (2))")
        bare = re.sub(r"<title>.*?</title>", "", picture, flags=re.S)
        if RULE_ID.search(bare) or "links rule" in bare:
            out.append(f"the graph of {c} shows a rule id outside a tooltip: {(RULE_ID.search(bare) or ['links rule'])[0]}")
    return out


def known_donor(conn) -> str:
    """A donor filed under one name in returns of two years or more to one
    party: the first row of the name with the most rows, read from the table."""
    d = db.rows(conn, "select min(key) as k from pub.party_return_donors where replaced_by is null and amount is not null "
                      "and donor is not null group by " + search.fold_sql("btrim(donor)") +
                " having count(distinct year) >= 2 and count(distinct party_key) = 1 order by count(*) desc, 1 limit 1")
    return f"party_return_donors:{d[0]['k']}" if d else ""


LISTED = re.compile(r'<li>(\d{4}|year not stated) · \$([\d,.]+) · [^<]*(<span class="warn">)?')


def gift_problems(conn) -> list:
    """Ruling 86 (3): the known donor's graph draws one money edge to its one
    party; its label's total equals the sum of the amounts the list shows as
    added, and equals the register's own sum of the rows filed under that
    name to that party, no amendment-replaced row among them; it names two
    years or more."""
    out = []
    centre = known_donor(conn)
    if not centre:
        return ["no donor filed under one name in two years' returns to one party, to test the summed edge on"]
    g = graph.build(conn, "", centre=centre)
    edges = [e for e in g["edges"] if e.get("addends") and e["b"].startswith("parties:")]
    if len(edges) != 1:
        return [f"the graph of the known donor {centre} drew {len(edges)} summed party edges, one wanted"]
    e = edges[0]
    total = graph.summed(e["addends"])["total"]
    page = graph.pane(g, "")
    head = page.find("<h4>" + panes.esc(graph.node_title(g["nodes"][e["b"]])))
    block = page[head:page.find("</ul></li>", head)] if head >= 0 else ""
    shown = [decimal.Decimal(a.replace(",", "")) for _, a, why in LISTED.findall(block) if not why]
    if not shown or sum(shown) != total:
        out.append(f"the known donor's party edge totals {total}, but the amounts listed under it as added sum to {sum(shown)}")
    if graph.money(total) not in e["label"]:
        out.append(f"the known donor's party edge says {e['label']!r}, not its total {graph.money(total)}")
    r = search.row(conn, "party_return_donors", centre.partition(":")[2])
    reg = db.rows(conn, "select sum(amount) as s, count(distinct year) as y from pub.party_return_donors where replaced_by is null "
                        f"and regexp_replace(btrim({search.fold_sql('donor')}), '\\s+', ' ', 'g') = %s and party_key = %s",
                  (cat.fold_term(r["donor"]), r["party_key"]))[0]
    if reg["s"] != total:
        out.append(f"the known donor's party edge totals {total}; the register's rows filed under the name to that party sum to {reg['s']}")
    if (reg["y"] or 0) < 2 or len(graph.summed(e["addends"])["years"]) < 2:
        out.append("the known donor's summed edge does not span two years")
    return out


def doc_problems(conn) -> list:
    """Rulings 86 (4) and 88: a known cited document answers 200 with its
    stored content type, its bytes hashing to its name; a wrong sha and a
    malformed name answer 404; a party return, whose form prints donors'
    addresses, answers 200 with its stored content type (no source is
    refused); one cited document of every source the published rows cite
    answers 200 with its own bytes; the row's pane begins the citation with
    the "source" link, at the page for a PDF."""
    out = []
    cited = db.rows(conn, "select key, document, page from pub.candidates where document is not null order by key limit 200")
    states = document.statuses(conn, [r["document"] for r in cited])
    known = [{**r, "kind": states[r["document"]]["kind"]} for r in cited if states.get(r["document"], {}).get("state") == document.SERVED]
    if not known:
        why = next(iter(states.values()), {}).get("why", "")
        return [f"no candidates row cites a document the board opens: {why}"]
    k = known[0]
    out += opened_problems(conn, k["document"], k["kind"], "the known cited document")
    wrong = ("0" if k["document"][0] != "0" else "1") + k["document"][1:]
    if document.fetch(conn, wrong)[0] != 404:
        out.append("/doc/ of a wrong sha did not answer 404")
    for bad in ("../" + k["document"][3:], k["document"][:2], k["document"].upper()):
        if document.fetch(conn, bad)[0] != 404:
            out.append(f"/doc/ of a name that is not 64 hex characters ({bad[:6]}…) did not answer 404")
    returns = db.rows(conn, "select document from pub.party_return_totals where document is not null order by key limit 50")
    rstates = document.statuses(conn, [r["document"] for r in returns])
    held = [(s, st["kind"]) for s, st in rstates.items() if st["state"] == document.SERVED]
    if not held:
        out.append("no party return document is held to open")
    else:
        out += opened_problems(conn, held[0][0], held[0][1], "a party return")
    by_source = cited_by_source(conn)
    if not by_source:
        out.append("no published row cites a document the store holds")
    for source, (sha, kind) in sorted(by_source.items()):
        out += opened_problems(conn, sha, kind, f"a cited {source} document")
    html = server.render("", server.parse_path(f"candidates:{k['key']}"), conn=conn)
    link = f'<a class="source" href="{document.href(k["document"], k["kind"], k.get("page"))}">source</a>'
    pane = html[html.rfind('<section class="pane'):]
    if link not in pane or pane.index(link) > pane.find("<th>document</th>"):
        out.append("the known row's pane does not begin its citation with the source link")
    return out


def opened_problems(conn, sha: str, kind: str, what: str) -> list:
    """/doc/<sha> answers 200, its stored content type and bytes hashing to its name."""
    status, ctype, body = document.fetch(conn, sha)
    data = body if isinstance(body, bytes) else b""
    if status != 200 or ctype != document.content_type(kind, landing_names(conn, sha), data[:64]):
        return [f"/doc/ of {what} {sha[:12]}… answered {status} {ctype}"]
    if document.hashlib.sha256(data).hexdigest() != sha:
        return [f"/doc/ of {what} {sha[:12]}… sent bytes that do not hash to its name"]
    return []


def cited_by_source(conn, per_view: int = 20) -> dict:
    """{source: (sha, kind)}: one held, not withdrawn document of each source
    the published views' `document` column cites, read through the store's
    reader (never a query of `docs`). Its keys are the sources ruling 88 opens
    that a row can reach."""
    views = [r["table_name"] for r in db.rows(
        conn, "select table_name from information_schema.columns where table_schema = 'pub' and column_name = 'document' "
              "order by table_name")]
    out = {}
    for v in views:
        shas = [r["document"] for r in db.rows(
            conn, f'select distinct document from pub."{v}" where document is not null limit {int(per_view)}')]
        for sha, st in sorted(document.statuses(conn, shas).items()):
            if st["state"] == document.SERVED and st["source"] not in out:
                out[st["source"]] = (sha, st["kind"])
    return out


def landing_names(conn, sha: str) -> list:
    return document.landing.names_of(sha, conn)


def carries_residence(name: str) -> bool:
    """A person's name with a residence after it ("Jane Doe, Sunrise Rest
    Home"): a residence word in a part of the name that follows a comma, a
    "c/-", a bracket or a dash, behind a part that reads as no organisation.
    An institution named for what it is ("Waimate Rest Home") is not one."""
    low = cat.fold_term(name or "")
    for w in RESIDENCE_WORDS:
        i = low.find(w)
        if i < 0:
            continue
        before = low[:i]
        cut = max(before.rfind(","), before.rfind("c/-"), before.rfind("("), before.rfind(" - "))
        if cut > 0 and re.search(r"[a-z]", before[:cut]) and not near.is_organisation(before[:cut]):
            return True
    return False


def _names(v, r) -> list:
    return [near.name_strings(g, r) for g in cat.fields_of(v).names]


def _hits(res) -> list:
    return [(v, r) for reg, found in res.items() if reg != "held" for v, _, rows in found for r in rows]


def field_problems(conn, held: set, columns: dict, types: dict) -> list:
    """8 to 10: the field search, the near matches, and no home address."""
    out = []
    # 8. every declared column exists, with the type its field reads
    for v in cat.VIEWS:
        if v.name not in held:
            continue
        fs = cat.fields_of(v)
        for c in sorted(cat.field_columns(v)):
            if c not in columns.get(v.name, set()):
                out.append(f"{v.name}: the field search declares `{c}`, which pub.{v.name} does not carry")
        for c in fs.dates:
            if c in columns.get(v.name, set()) and types.get((v.name, c)) not in DATE_TYPES:
                out.append(f"{v.name}: the year field reads `{c}` as a date, but it is {types.get((v.name, c))}")
        for c in fs.year:
            if c in columns.get(v.name, set()) and types.get((v.name, c)) not in ("integer", "smallint", "bigint"):
                out.append(f"{v.name}: the year field reads `{c}` as a year, but it is {types.get((v.name, c))}")
    hart = _hits(search.search(conn, "", limit=search.RESULTS_LIMIT, fields={"last": "Hart"}))
    if not hart:
        out.append("a search with only the last name Hart found nothing")
    for v, r in hart:
        if not any(re.search(r"(?<![a-z])hart(?![a-z])", cat.fold_term(n)) for n in _names(v, r)):
            out.append(f"the last name Hart found {v.name}:{r['key']}, whose names carry no whole word HART")
    # 9. every Name has an order; the donor filed surname first is exact and not near; a registered office is near
    for name, fs in cat.FIELDS_OF.items():
        for g in fs.names:
            if g.order not in cat.ORDERS or (g.order == cat.PARTS) == bool(g.whole):
                out.append(f"{name}: the Name over {', '.join(g.columns())} declares no name order (ruling 85)")
    first, last = KNOWN_REVERSED
    asked = {"first": first, "last": last}
    filed = db.rows(conn, "select key from pub.party_return_donors where "
                          f"{search.fold_sql('donor')} ~ %s order by key",
                    [r"^\W*" + cat.fold_term(last) + r"\s+" + cat.fold_term(first) + r"\M[^,]*$"])
    if not filed:
        out.append(f"no party return donor filed as {last.upper()} {first.upper()} to test the name order on")
    else:
        refs = {f"party_return_donors:{r['key']}" for r in filed}
        exact = {f"{v.name}:{r['key']}" for v, r in _hits(search.search(conn, "", limit=search.RESULTS_LIMIT,
                                                                        registers=("party_returns",), fields=asked))}
        if refs - exact:
            out.append(f"{len(refs - exact)} of {len(refs)} donor rows filed {last.upper()} {first.upper()} are not "
                       f"among the exact results for first {first}, last {last}")
        nb = near.near(conn, "", asked, registers=("party_returns",), held=held)
        if refs & set(nb["names"]["refs"]):
            out.append(f"a donor row filed {last.upper()} {first.upper()} is under Near matches: the donor form fixes no order")
        page = server.render("", [], conn=conn, boxes=search.Boxes(False, ("party_returns",), tuple(asked.items())))
        at = page.find('<details class="near"')
        first_seen = page.find(urllib.parse.urlencode({"p": sorted(refs)[0]}) + "&")
        if first_seen < 0 or (at >= 0 and first_seen > at):
            out.append(f"the donor filed {last.upper()} {first.upper()} is not shown among the exact results")
    office = db.rows(conn, "select key, line_2, line_3 from pub.company_addresses where line_1 ~* '^level [0-9]+$' "
                           "and line_2 ~* '^[0-9]+ [a-z]+ street$' and line_3 ~ '^[A-Za-z]+$' order by key limit 1")
    if not office:
        out.append("no registered office with a level and a street to test the near address on")
    else:
        o = office[0]
        query = re.sub(r"(?i)street$", "St", o["line_2"]) + ", " + o["line_3"]
        nb = near.near(conn, "", {"address": query}, registers=("companies",), held=held)
        ref = f"company_addresses:{o['key']}"
        if ref not in nb["addresses"]["refs"]:
            out.append(f"a registered office was not found as near by its address without the level{' (candidates capped)' if nb['addresses']['more'] else ''}")
        clause, params = search.match_sql(cat.BY_NAME["company_addresses"], [], None, False, {"address": query})
        if db.rows(conn, f"select 1 from pub.company_addresses where key = %s and {clause}", [o["key"]] + params):
            out.append("the near-address test row is also an exact match: the test proves nothing")
    # 10. no home address reaches any result
    for v in cat.VIEWS:
        fs = cat.fields_of(v)
        for c in fs.address:
            if (v.name, c) not in cat.ADDRESS_COLUMNS:
                out.append(f"{v.name}: the address field reads `{c}`, which is not a registered address an organisation publishes")
        if fs.address and v.kind == "person":
            out.append(f"{v.name}: a person's view declares an address column (hard limit 15)")
    address_views = {x for x, _ in cat.ADDRESS_COLUMNS}
    for w in RESIDENCE_WORDS:
        for v, r in _hits(search.search(conn, w, limit=search.RESULTS_LIMIT)):
            for n in _names(v, r):
                if carries_residence(n) and not panes.is_suppressed(v, r):
                    out.append(f"{v.name}:{r['key']}: a person's name in a result carries a residence word (hard limit 15)")
        for v, r in _hits(search.search(conn, "", limit=search.RESULTS_LIMIT, fields={"address": w})):
            if v.name not in address_views:
                out.append(f"the address field found a row of {v.name}, which holds no registered address")
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
