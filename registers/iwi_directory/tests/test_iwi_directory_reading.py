"""The reading's rules on pages shaped like Te Kāhui Māngai's (every name,
phone and address invented), a mutant check of those rules, the capture's
walk and politeness on a fake transport, and the filled sample (real pages,
sample.list) against the row contract, the ledger, the site's own counts and
the contact rule. No model is called and nothing is fetched."""
import datetime as dt
import os
import re
import types

import pytest

from support import db, rowcontract, sample
from registers.iwi_directory import capture, check, load, read
from registers.iwi_directory import sample as S

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHA = "e" * 64
SAMPLE_SCHEMA = "scratch_test_iwi_directory"
URL = "https://www.tkm.govt.nz/iwi/ngati-invented/"
SECRETS = ("Hemi Inventedname", "021 555 0199", "hemi@invented.example", "12 Pretend Street", "PO Box 999 Nowhere",
           "Aroha Madeup", "07 555 0123")


def _org(n, name, flags, fields, h2=None):
    head = f"<h2>{h2}</h2>" if h2 else ""
    fl = "".join(f'<p><img src="/images/{img}.png" alt="{alt}" width="22" height="16" /> {alt.rstrip(".")}'
                 + (f" [ {br} ]" if br else "") + ".</p>" for img, alt, br in flags)
    fd = "".join(f"<p><b>{k}:</b> {v}</p>" for k, v in fields)
    return (f'{head}<div class="tab"><p><strong>{n}</strong> Iwi Representative Organisation</p><br />'
            f'<h3>{name}</h3><p style=\'float: right;\'>Last updated: 01/02/2025</p><br />'
            f'<div style=\'clear: right;\' class="tab">{fl}{fd}<hr /></div></div>')


def _iwi_page(tables_html, orgs_html, name="Ngāti Invented"):
    return ("<html><head><title>TKM | Iwi | x | Te Kahui Mangai</title></head><body>"
            "<div id=\"header\"><h1><a class='tkm_logo' href='/'></a></h1></div>"
            f"<div id=\"introBox\"><span id='contentStart'><a href='/region/tainui/'>Tainui</a></span><h1>{name}</h1></div>"
            '<div id="iwiMain"><p><img src="/images/mfa.png" alt="Recognised iwi in the Māori Fisheries Act 2004. " /></p></div>'
            '<div id="tabs" class="tabs"></div>'
            '<div id="iwiRohe"><dl class="authority_tree"><dt>Regional Council</dt><dd>Waikato Regional Council</dd></dl>'
            '<dl class="authority_tree"><dt>Territorial Authority</dt><dd>Waitomo District Council</dd></dl></div>'
            f'<div id="iwiHapu"><noscript><h2>Hapū and Marae</h2></noscript>{tables_html}</div>'
            f'<div id="iwiOrganisations"><noscript><h2>Representative Organisations</h2></noscript>'
            f'<h2>Iwi Representative Organisations</h2>{orgs_html}</div>'
            '<div id="clearFooterHome"></div><div id="footer"></div></body></html>').encode()


def _table(heading, rows, hapu=True):
    heads = (["Hapū"] if hapu else []) + ["Marae", "Wharenui", "Location"]
    th = "".join(f"<th><h4>{h}</h4></th>" for h in heads)
    trs = "".join(f'<tr class="{"odd" if i % 2 else "even"}">' + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
                  for i, r in enumerate(rows))
    return f'<h4>{heading}</h4><table class="haputable"><tr class="head">{th}</tr>{trs}</table>'


PSGE = ("posttreaty_sm", "Post-Treaty settlement governance entity. ", "Ngāti Invented Claims Settlement Act 2019")
DEED = ("posttreaty_sm", "Post-Treaty settlement governance entity. ", "Deed of Settlement signed with the Crown on 02 March 2020")
CNI = ("tree-green", "Post settlement governance entity in the Central North Island Forests Iwi Collective Settlement. ", None)
MANDATE = ("treaty_sm", "Mandate recognised by the Crown for Treaty of Waitangi settlement negotiations. ",
           "Agreement in Principle signed with the Crown on 28 June 2019")
RMA = ("rma_sm", "Resource Management Act consultation. ", None)
CONTACT = [("Chair", SECRETS[0]), ("Ph", SECRETS[1]), ("Email", f'<a href="mailto:{SECRETS[2]}">{SECRETS[2]}</a>'),
           ("Postal Address", f"{SECRETS[4]}<br />Nowhere 3999"), ("Physical Address", SECRETS[3]),
           ("RMA Contact", SECRETS[5]), ("Mobile", SECRETS[6])]


def _sample_page():
    t = _table("Uta Rohe", [["Ngāti Tahi", "Pā Tahi", "Whare Tahi", "1 Marae Road, Kāwhia"],
                            ["", "Pā Rua", "*No wharenui*", "Rua Road, Kāwhia"],
                            ["Ngāti Rua", "Pā Tahi", "Whare Tahi", "1 Marae Road, Kāwhia"]])
    o = (_org(1, "Te Rūnanga Invented Trust", [PSGE, RMA],
              [("Legal entity", "Charitable Trust (CC12345)"), ("Governance structure", "Seven trustees.")] + CONTACT
              + [("Website", '<a href="https://invented.example.nz/">our website</a>')])
         + _org(2, "Invented Hapū Group", [("rma_sm", "Resource Management Act consultation - Groups that represent hapū.", None)],
                [("Legal entity", "Incorporated Society"), ("Hapū Represented", "Ngāti Tahi")] + CONTACT,
                h2="Groups that represent hapū of this iwi for the purposes of the RMA")
         + _org(3, "Invented Collective Trust", [DEED, CNI], [("Legal entity", "Trust")])
         + _org(4, "Invented Negotiations Team", [MANDATE], [("Legal entity", "Not Applicable")]))
    return _iwi_page(t, o)


def rules(r) -> list:
    """Each rule of the reading, as a list of the ones broken."""
    broken = []
    page = _sample_page()
    try:
        out = r.read_page(page, SHA, URL)
    except Exception as exc:  # noqa: BLE001 — a crash is a broken rule
        return [f"crashed: {exc}"]
    ents = {e["key"]: e for e in out["entities"]}
    kinds = sorted(e["kind"] for e in out["entities"])
    if kinds.count("hapū") != 2 or kinds.count("marae") != 2 or kinds.count("iwi") != 1:
        broken.append(f"two hapū, two marae, one iwi: {kinds}")
    rels = {(x["from_key"], x["relation"], x["to_key"]) for x in out["relations"]}
    tahi = "tkm/hapu/ngati-invented/ngati-tahi"
    pa_rua = "tkm/marae/pa-rua/rua-road-kawhia"
    if (pa_rua, "marae of hapū", tahi) not in rels:
        broken.append("a blank hapū cell is the row above's hapū")
    if ("tkm/marae/pa-tahi/1-marae-road-kawhia", "marae of hapū", "tkm/hapu/ngati-invented/ngati-rua") not in rels:
        broken.append("a marae shared by two hapū is related to both")
    org = ents.get("tkm/org/te-runanga-invented-trust", {})
    if org.get("kind") != "governance entity":
        broken.append("an organisation flagged post-settlement is a governance entity")
    if ents.get("tkm/org/invented-hapu-group", {}).get("kind") != "organisation":
        broken.append("an organisation not flagged post-settlement is an organisation")
    if org.get("charity_number") != "CC12345" or org.get("legal_entity") != "Charitable Trust (CC12345)":
        broken.append("the legal entity and a printed charity number are kept as printed")
    if org.get("website") != "https://invented.example.nz/":
        broken.append("the website is the link printed")
    if ents.get("tkm/org/invented-hapu-group", {}).get("listed_as") != "Groups that represent hapū of this iwi for the purposes of the RMA":
        broken.append("an organisation is listed under the heading above it")
    if ents.get("tkm/org/invented-hapu-group", {}).get("hapu_represented") != "Ngāti Tahi":
        broken.append("hapū represented is kept")
    flat = repr(out)
    for s in SECRETS:
        if s in flat or s.replace(" ", "") in flat.replace(" ", ""):
            broken.append(f"a contact value leaves the page: {s[:4]}…")
    if "Chair" not in out["unread"] or "Email" not in out["unread"]:
        broken.append("the unread labels are counted by name")
    sets = {s["key"]: s for s in out["settlements"]}
    act = sets.get("tkm/settlement/ngati-invented-claims-settlement-act-2019")
    if not act or act["act_year"] != 2019 or act["stage"] != "settled: Act":
        broken.append("a governance entity's Act is its settlement, with its year")
    deed = sets.get("tkm/settlement/invented-collective-trust/02-march-2020")
    if not deed or deed["stage"] != "settled: deed signed" or deed["act"] is not None:
        broken.append("a deed signed with no Act is a settlement by deed, keyed by its entity and date")
    cni = sets.get("tkm/settlement/central-north-island-forests-iwi-collective-settlement")
    if not cni or cni["stage"] != "collective settlement":
        broken.append("the collective settlement flag names its settlement")
    mand = sets.get("tkm/mandate/invented-negotiations-team")
    if not mand or mand["stage"] != "mandate recognised" or mand["signed_on"] != "28 June 2019":
        broken.append("a mandate is a stage, not a settlement")
    if ents.get("tkm/org/invented-negotiations-team", {}).get("kind") != "organisation":
        broken.append("a mandated negotiator is not a governance entity")
    if not any(x["relation"] == "rohe in local authority" and x["to_name"] == "Waitomo District Council"
               and x["section"] == "Territorial Authority" for x in out["relations"]):
        broken.append("the rohe's local authorities are kept with their kind")
    if ents.get("tkm/iwi/ngati-invented", {}).get("region") != "Tainui":
        broken.append("the iwi's region is kept")
    try:
        r.read_page(page.replace(b"<th><h4>Wharenui</h4></th>", b"<th><h4>Notes</h4></th>"), SHA, URL)
        broken.append("a hapū table with other heads is refused")
    except r.NotTheShape:
        pass
    try:
        r.read_page(b"<html><title>Something else</title></html>", SHA, URL)
        broken.append("a page that is not the site's is refused")
    except r.NotTheShape:
        pass
    odd = _iwi_page(_table("x", [["A", "B", "C", "D"]]), _org(1, "Odd Trust", [("newthing", "A new role. ", None)], []))
    if not any(f.startswith("other: newthing") for e in r.read_page(odd, SHA, URL)["entities"] for f in e["flags"]):
        broken.append("an unknown role flag is kept as 'other', for the check to see")
    nohapu = _iwi_page(_table("x", [["Pā", "Whare", "Somewhere"]], hapu=False), "")
    if not any(x["relation"] == "marae of iwi" for x in r.read_page(nohapu, SHA, URL)["relations"]):
        broken.append("a marae on a page with no hapū column is the iwi's")
    return broken


def test_every_rule_holds():
    assert rules(read) == []


MUTANTS = {
    "every label read": ("        if col is None:\n                    entry[\"unread\"]", "        if False:\n                    entry[\"unread\"]"),
    "a blank hapū cell left blank": ('if above is not None and not cells[0] and cols[0] == "Hapū":', "if False:"),
    "every organisation a governance entity": ('"governance entity" if psge else "organisation"', '"governance entity"'),
    "the Act's year dropped": ('"act_year": int(act.group(2))', '"act_year": None'),
    "a mandate made a settlement": ("    if MANDATE.match(alt):\n", "    if False:\n"),
    "the website's text not its link": ('entry["fields"][col] = href.group(1) if href else text(val)',
                                        'entry["fields"][col] = text(val)'),
    "a deed keyed by its words": ('s_key = "tkm/settlement/" + fold(e["name"]) + "/" + fold(s["signed_on"] or s["as_printed"])',
                                  's_key = "tkm/settlement/" + fold(s["as_printed"])'),
    "unknown flags dropped": ('FLAG_BY_IMAGE.get(img.group(1), "other: " + img.group(1))', 'FLAG_BY_IMAGE.get(img.group(1), "")'),
    "any page read as the site's": ('    if "<title>TKM |" not in page and "Te Kahui Mangai" not in page:\n', "    if False:\n"),
    "any heads accepted": ('if cols[-3:] != ["Marae", "Wharenui", "Location"] or cols[:-3] not in ([], ["Hapū"]):', "if False:"),
}


def _mutant(old, new):
    src = open(read.__file__, encoding="utf-8").read()
    assert src.count(old) == 1, f"the mutant's anchor is not in read.py once: {old}"
    mod = types.ModuleType("read_mutant")
    mod.__file__ = read.__file__
    exec(compile(src.replace(old, new), read.__file__, "exec"), mod.__dict__)
    return mod


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_each_mutant_is_caught(name):
    try:
        broken = rules(_mutant(*MUTANTS[name]))
    except (KeyError, TypeError, AttributeError, ValueError, IndexError):
        broken = ["crashed"]
    assert broken, f"the mutant '{name}' passes every rule"


# ── the capture's walk and politeness, on a fake transport ────────────────────

def test_the_walk_keeps_to_the_site_s_pages():
    assert capture.classify("https://www.tkm.govt.nz/iwi/x") == ("https://www.tkm.govt.nz/iwi/x/", "")
    assert capture.classify("https://www.tkm.govt.nz/rohe/AOI-x.pdf")[1]
    assert capture.classify("https://www.tkm.govt.nz/search/?q=a")[1]
    assert capture.classify("https://www.tkm.govt.nz/contact/")[1]
    assert capture.classify("https://tenehenehenui.iwi.nz/")[0] is None
    links = capture.links_of(b"<a href='/iwi/a/'>a</a><a href=\"mailto:x@y.nz\">m</a><a href='/iwi/a/'>again</a>"
                             b"<a href='https://elsewhere.nz/'>e</a><a href='/images/x.png'>p</a>",
                             "https://www.tkm.govt.nz/region/r/")
    assert links == [("https://www.tkm.govt.nz/iwi/a/", ""),
                     ("https://www.tkm.govt.nz/images/x.png", "a file, not a page")]


class FakeTables:
    def __init__(self):
        self.frontier, self.finished, self.asides, self.passes = {}, False, [], 0

    def open_pass(self):
        return 1 if self.passes and not self.finished else None

    def last_finished(self):
        return None

    def begin(self, seeds):
        self.passes += 1
        for s in seeds:
            self.add(1, s, None, "")
        return 1

    def add(self, pid, url, found_on, why):
        self.frontier.setdefault(url, {"state": "not asked" if why else "todo", "ord": len(self.frontier)})

    def next_todo(self, pid):
        todo = sorted((v["ord"], u) for u, v in self.frontier.items() if v["state"] == "todo")
        return todo[0][1] if todo else None

    def mark(self, pid, url, state, kind=None, sha=None, why=None):
        self.frontier[url].update(state=state, kind=kind, sha=sha)

    def finish(self, pid):
        self.finished = True

    def set_aside(self, pid, item, stage, reason):
        self.asides.append((item, stage, reason))


class Ref:
    def __init__(self, sha):
        self.sha256 = sha


def _site():
    home = b"<title>TKM | Home | Te Kahui Mangai</title><a href='/map/'>m</a><a href='/rohe/x.pdf'>p</a>"
    mp = (b"<title>TKM | Map | Te Kahui Mangai</title><a href='/region/r/'>r</a>")
    region = (b"<title>TKM | R | Te Kahui Mangai</title><div id=\"introBox\"><h1>R</h1></div>"
              b"<dd class='legend'><a href='/iwi/a/'>A</a></dd><dd class='legend'><a href='/iwi/b/'>B</a></dd>")
    return {"https://www.tkm.govt.nz/": home, "https://www.tkm.govt.nz/map/": mp,
            "https://www.tkm.govt.nz/region/r/": region,
            "https://www.tkm.govt.nz/iwi/a/": _sample_page(), "https://www.tkm.govt.nz/iwi/b/": _sample_page()}


def _run(site, statuses=None, now=None, budget_s=10 ** 9):
    t, clock, asked = FakeTables(), [0.0], []
    statuses = statuses or {}

    def opener(url, timeout):
        asked.append(url)
        st = statuses.get(url, 200 if url in site else 404)
        body = site.get(url, b"") if st == 200 else b""
        import support.fetchgate as fg
        return fg.Fetched(url, st, body, url, fg.looks_challenged(st, body))

    def land(data, *, name, **kw):
        return Ref(str(abs(hash(data)))), True

    run = capture.Run(t, land_fn=land, opener=opener, clock=lambda: clock[0],
                      sleep=lambda s: clock.__setitem__(0, clock[0] + s),
                      now=now or (lambda: dt.datetime(2026, 10, 22, 23, 0, tzinfo=capture.NZ)), seeds=("/",),
                      budget_s=budget_s, log=lambda *_: None)
    return run.run(), t, asked, clock


def test_the_walk_lands_every_page_once_and_finishes():
    out, t, asked, clock = _run(_site())
    assert out["landed"] == 5 and t.finished and len(asked) == len(set(asked)) == 6
    assert t.frontier["https://www.tkm.govt.nz/region/tainui/"]["state"] == "set aside"
    assert t.frontier["https://www.tkm.govt.nz/rohe/x.pdf"]["state"] == "not asked"
    assert t.frontier["https://www.tkm.govt.nz/iwi/a/"]["kind"] == "iwi"
    assert clock[0] >= 4 * capture.FLOOR_S


def test_a_block_stops_the_walk():
    out, t, asked, _ = _run(_site(), {"https://www.tkm.govt.nz/map/": 403})
    assert out["stopped"].startswith("stopped:") and len(asked) == 2 and not t.finished
    assert capture.outcome(out)[0]


def test_a_server_error_is_set_aside_and_the_walk_goes_on():
    out, t, asked, clock = _run(_site(), {"https://www.tkm.govt.nz/iwi/a/": 503})
    assert not out["stopped"] and t.frontier["https://www.tkm.govt.nz/iwi/a/"]["state"] == "set aside"
    assert t.finished and clock[0] >= capture.REST_S


def test_no_request_outside_off_peak():
    out, t, asked, _ = _run(_site(), now=lambda: dt.datetime(2026, 10, 22, 12, 0, tzinfo=capture.NZ))
    assert asked == [] and out["stopped"] == "off-peak is over"


# ── the filled sample: real pages ─────────────────────────────────────────────

def _db_or_skip():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")


def _rows(conn, q):
    cur = conn.execute(q)
    cols = [d.name for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


@pytest.fixture(scope="module")
def filled():
    _db_or_skip()
    items = sample.read_list(os.path.join(LANE, "sample.list"))
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        S.fill(conn, SAMPLE_SCHEMA, items)
        conn.execute(load.sql("publish.sql", SAMPLE_SCHEMA).replace("pub.", f"{SAMPLE_SCHEMA}.v_"))
        conn.commit()
        T = lambda t: load.table(SAMPLE_SCHEMA, t)
        yield {"conn": conn, "items": items, **{t: _rows(conn, f"SELECT * FROM {T(t)}") for t in load.TABLES},
               "entries": S.entries_of(items, conn)}


def test_every_page_is_in_the_ledger_and_none_set_aside(filled):
    assert len(filled["read_pages"]) == len(filled["entries"]) == 36 and not filled["read_set_aside"]
    kinds = {}
    for p in filled["read_pages"]:
        kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1
    assert kinds == {"iwi": 10, "region": 13, "authority": 2, "omo": 1, "nontribal": 1, "site": 9}


def test_every_row_meets_the_row_contract(filled):
    for r in filled["entities"] + filled["relations"] + filled["settlements"]:
        assert rowcontract.validate({**r, "loaded_at": r["loaded_at"].isoformat()}) == [], r["key"]


def test_the_region_maps_link_the_site_s_117_iwi(filled):
    linked = {s for p in filled["read_pages"] if p["kind"] == "region" for s in p["iwi_links"]}
    assert len(linked) == 117


#: the sample's hard cases, as the site printed them on 22 October 2026
def test_the_hard_cases_read_as_the_site_prints_them(filled):
    ents = {e["key"]: e for e in filled["entities"]}
    hapu = lambda iwi: sum(1 for e in filled["entities"] if e["kind"] == "hapū" and e["iwi_key"] == f"tkm/iwi/{iwi}")
    assert hapu("maniapoto") == 50 and hapu("ngai-tahu") == 18 and hapu("moriori") == 0
    assert ents["tkm/org/te-nehenehenui-trust"]["kind"] == "governance entity"
    acts = {(s["entity_key"], s["act"]) for s in filled["settlements"] if s["act"]}
    assert ("tkm/org/te-nehenehenui-trust", "Maniapoto Claims Settlement Act 2022") in acts
    assert ("tkm/org/te-runanga-o-ngai-tahu", "Ngāi Tahu Claims Settlement Act 1998") in acts
    assert sum(1 for s in filled["settlements"] if s["iwi_key"] == "tkm/iwi/ngati-pikiao") == 3
    assert ents["tkm/org/te-runanga-a-iwi-o-ngapuhi"]["kind"] == "organisation"
    assert any(r["relation"] == "marae of iwi" and r["to_key"] == "tkm/iwi/moriori" for r in filled["relations"])
    assert ents["tkm/org/te-kotahitanga-o-te-arawa-waka-fisheries-trust-board"]["pages"] == 2
    assert sum(1 for e in filled["entities"] if e["kind"] == "marae" and e["listed_as"] != "tribal marae") == 175


def test_no_contact_value_on_a_page_reaches_a_row(filled):
    """Every email address and phone-shaped run the real iwi and organisation pages print is absent from every row:
    the allowlist holds on the site's own pages, not only on invented ones."""
    from support.docstore.landing import read_bytes
    found = set()
    for url, sha in filled["entries"]:
        page = read_bytes(sha).decode("utf-8", "replace")
        found |= set(re.findall(check.EMAIL, page))
        found |= {m.group(0) for m in re.finditer(r"\b0\d[\d ]{6,11}\d\b", read.text(page))}
    assert len(found) > 20
    flat = repr(filled["entities"] + filled["relations"] + filled["settlements"])
    assert [v for v in found if v in flat] == []


def test_the_views_and_the_reading_are_clean(filled):
    conn = filled["conn"]
    assert check.reading(conn, SAMPLE_SCHEMA) == []
    assert check.views(conn, f"{SAMPLE_SCHEMA}.v_") == []


def test_the_check_goes_red_on_a_contact_value_or_a_broken_ledger(filled):
    conn = filled["conn"]
    T = lambda t: load.table(SAMPLE_SCHEMA, t)
    try:
        conn.execute(f"UPDATE {T('entities')} SET governance_structure = 'call 021 555 0199' "
                     "WHERE key = 'tkm/org/te-nehenehenui-trust'")
        conn.execute(f"DELETE FROM {T('entities')} WHERE key = 'tkm/iwi/waitaha'")
        problems = check.reading(conn, SAMPLE_SCHEMA)
        assert any("email or a phone" in p for p in problems)
        assert any("not held" in p for p in problems)
    finally:
        conn.rollback()
