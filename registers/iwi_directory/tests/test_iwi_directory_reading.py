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


def _table(heading, rows, hapu=True, heads=None):
    heads = heads or (["Hapū"] if hapu else []) + ["Marae", "Wharenui", "Location"]
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
#: the post-settlement flag with nothing beside it (Hako Tūpuna Trust, Ngāti Porou ki Hauraki Rūnanga Trust)
PLAIN = ("posttreaty_sm", "Post-Treaty settlement governance entity. ", None)
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
         + _org(4, "Invented Negotiations Team", [MANDATE], [("Legal entity", "Not Applicable")])
         + _org(5, "Invented Forests Trust", [CNI], [("Legal entity", "Trust")])
         + _org(6, "Invented Plain Trust", [PLAIN], [("Legal entity", "Trust")]))
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
    keys = [s["key"] for s in out["settlements"]]
    if len(set(keys)) != len(keys) or any(s["key"] != r.settlement_row_key(s["entity_key"], s["settlement_key"])
                                          for s in out["settlements"]):
        broken.append(f"a settlement row's key is its entity's with the settlement's, one row each: {keys}")
    cni_rows = [s for s in out["settlements"]
                if s["settlement_key"] == "tkm/settlement/central-north-island-forests-iwi-collective-settlement"]
    if sorted(s["entity_key"] for s in cni_rows) != ["tkm/org/invented-collective-trust", "tkm/org/invented-forests-trust"]:
        broken.append("a collective named by two bodies is two rows under one settlement key")
    plain = [s for s in out["settlements"] if s["entity_key"] == "tkm/org/invented-plain-trust"]
    if [(s["name"], s["settlement_key"], s["stage"]) for s in plain] != [(None, None, "settled: none named")]:
        broken.append(f"the post-settlement flag's own words name no settlement: {plain}")
    sets = {s["settlement_key"]: s for s in out["settlements"]}
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
    # the shapes the first full walk printed (22 October 2026): a list of hapū alone beside a marae table, no
    # wharenui column, marae and location alone, and "Not yet identified" where a marae is not named
    split = _iwi_page(_table("Hapū", [["Ngāti Tahi"], ["Ngāti Rua"]], heads=["Hapū"])
                      + _table("Marae", [["Pā Toru", "Whare Toru", "Toru Road"]], hapu=False), "")
    try:
        out = r.read_page(split, SHA, URL)
        kinds = sorted(e["kind"] for e in out["entities"])
        if kinds != ["hapū", "hapū", "iwi", "marae"] or not any(x["relation"] == "marae of iwi" for x in out["relations"]):
            broken.append(f"a list of hapū alone is the iwi's hapū, its marae table beside it the iwi's: {kinds}")
    except r.NotTheShape as exc:
        broken.append(f"a list of hapū alone is read: {exc}")
    nowhare = _iwi_page(_table("x", [["Ngāti Tahi", "Not yet identified", ""], ["Ngāti Rua", "Pā Wha", "Wha Road"]],
                               heads=["Hapū", "Marae", "Location"])
                        + _table("y", [["Pā Rima", "Rima Road"]], heads=["Marae", "Location"]), "")
    try:
        out = r.read_page(nowhare, SHA, URL)
        names = sorted(e["name"] for e in out["entities"] if e["kind"] == "marae")
        if names != ["Pā Rima", "Pā Wha"]:
            broken.append(f"a table with no wharenui column is read, and 'Not yet identified' is no marae: {names}")
    except r.NotTheShape as exc:
        broken.append(f"a table with no wharenui column is read: {exc}")
    flags = _iwi_page(_table("x", [["A", "B", "C", "D"]]), _org(1, "Flag Trust", [
        ("maunga_blue_sm", "Ngā Iwi o Taranaki. ", None),
        ("rma_sm_hapu", "Resource Management Act consultation - Groups that represent hapū of this iwi. ", None),
        ("phone_sm", "Phone. ", SECRETS[1])], [("Website", f'<a href="http://{SECRETS[2]}">{SECRETS[2]}</a>')]))
    out = r.read_page(flags, SHA, URL)
    got = [f for e in out["entities"] for f in e["flags"]]
    if not any(f.startswith("member of Ngā Iwi o Taranaki") for f in got):
        broken.append("the maunga picture is the Ngā Iwi o Taranaki flag")
    if not any(f.startswith("RMA group representing hapū") for f in got):
        broken.append("the RMA hapū groups' picture is not the iwi authority's")
    if any("phone" in f.lower() for f in got):
        broken.append("a contact icon is never a flag")
    if SECRETS[2] in repr(out) or SECRETS[1] in repr(out):
        broken.append("a contact value in a kept label (a website that is an email address) leaves the page")
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
    "a settlement row keyed by the settlement alone": ('"key": settlement_row_key(key, s_key)', '"key": s_key'),
    "the flag's own words read as a collective": (
        'return {"name": None, "act": None, "act_year": None, "stage": "settled: none named"',
        'return {"name": alt.rstrip("."), "act": None, "act_year": None, "stage": "collective settlement"'),
    "unknown flags dropped": ('return FLAG_BY_IMAGE.get(parts[0], "other: " + parts[0])', 'return FLAG_BY_IMAGE.get(parts[0], "")'),
    "the flag's qualifier ignored": ('        if f"{parts[0]}_{q}" in FLAG_BY_IMAGE:\n', "        if False:\n"),
    "a contact icon kept": ("            if img and contact_image(img.group(1)):\n", "            if False:\n"),
    "a contact value in a kept label kept": ('if CONTACT_VALUE.search(entry["fields"][col] or ""):', "if False:"),
    "a placeholder kept as a marae": ('row = {c: ("" if PLACEHOLDER.match(v) else v)', "row = {c: (v)"),
    "a one-column table's rows dropped": ("if len(cells) <= 1 and len(cols) > 1 or not any(cells):", "if len(cells) <= 1:"),
    "any page read as the site's": ('    if "<title>TKM |" not in page and "Te Kahui Mangai" not in page:\n', "    if False:\n"),
    "any heads accepted": ("if cols not in HAPU_HEADS:", "if False:"),
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
    assert len(filled["read_pages"]) == len(filled["entries"]) == 43 and not filled["read_set_aside"]
    kinds = {}
    for p in filled["read_pages"]:
        kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1
    assert kinds == {"iwi": 17, "region": 13, "authority": 2, "omo": 1, "nontribal": 1, "site": 9}


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
    # the first full walk's hard cases (fix-registers-iwi-directory-1, 23 October 2026)
    flags = [f for e in filled["entities"] for f in e["flags"]]
    assert not [f for f in flags if f.startswith("other: ")]
    assert any(f.startswith("member of Ngā Iwi o Taranaki") for f in ents["tkm/org/te-kahui-o-taranaki-trust"]["flags"])
    assert any(f.startswith("RMA group representing hapū") for f in flags)
    assert hapu("muaupoko") == 7 and hapu("ngati-mutunga-o-wharekauri") == 0
    assert any(r["relation"] == "marae of iwi" and r["to_key"] == "tkm/iwi/muaupoko" for r in filled["relations"])
    assert not [e for e in filled["entities"] if read.PLACEHOLDER.match(e["name"])]
    assert ents["tkm/org/ngati-mutunga-o-wharekauri-iwi-trust"]["website"] is None


def test_a_settlement_key_names_one_row(filled):
    """Card a-settlement-key-names-several-rows: each row its own key (the entity's with the settlement's), the
    settlement's kept beside it; Hako Tūpuna Trust's flag is the flag's own words, which name no settlement."""
    rows = filled["settlements"]
    assert len({s["key"] for s in rows}) == len(rows)
    assert all(s["key"] == read.settlement_row_key(s["entity_key"], s["settlement_key"]) for s in rows)
    assert not [s for s in rows if read.PSGE.match(s["name"] or "")]
    hako = [(s["name"], s["settlement_key"], s["stage"]) for s in rows if s["entity_key"] == "tkm/org/hako-tupuna-trust"]
    assert hako == [(None, None, "settled: none named")]
    assert {s["settlement_key"] for s in rows if s["iwi_key"] == "tkm/iwi/ngati-hako"} == {
        None, "tkm/mandate/ngati-hako-treaty-settlement-negotiators"}


def test_two_bodies_whose_names_fold_alike_are_two_rows(filled):
    """Card the-iwi-directory-key-folds-two-bodies-into-one, on the stored pages (23 October 2026): Ngāti Hāua Iwi
    Trust (Upper Whanganui, a mandate) and Ngāti Hauā Iwi Trust (Waikato, the 2014 Act) fold to one name; each is
    its own row, keyed by the page that prints it, with its own iwi and its own settlement."""
    ents = {e["key"]: e for e in filled["entities"]}
    assert "tkm/org/ngati-haua-iwi-trust" not in ents
    whanganui = ents["tkm/org/ngati-haua-iwi-trust/ngati-haua-upper-whanganui"]
    waikato = ents["tkm/org/ngati-haua-iwi-trust/ngati-haua"]
    assert (whanganui["name"], whanganui["pages"]) == ("Ngāti Hāua Iwi Trust", 1)
    assert (waikato["name"], waikato["pages"]) == ("Ngāti Hauā Iwi Trust", 1)
    of_iwi = {(r["from_key"], r["to_key"]) for r in filled["relations"] if r["relation"] == "organisation of iwi"
              and r["from_key"].startswith("tkm/org/ngati-haua-iwi-trust")}
    assert of_iwi == {(whanganui["key"], "tkm/iwi/ngati-haua-upper-whanganui"), (waikato["key"], "tkm/iwi/ngati-haua")}
    sets = {(s["entity_key"], s["stage"], s["act"]) for s in filled["settlements"]
            if s["entity_key"].startswith("tkm/org/ngati-haua-iwi-trust")}
    assert sets == {(whanganui["key"], "mandate recognised", None),
                    (waikato["key"], "settled: Act", "Ngāti Hauā Claims Settlement Act 2014")}
    assert not [e for e in filled["entities"] if e["key"].count("/") > 2 and e["key"].startswith("tkm/org/")
                and not e["key"].startswith("tkm/org/ngati-haua-iwi-trust/")]


def test_a_body_is_split_only_where_its_pages_print_different_names():
    """The split on invented pages: a name printed on two pages stays one body; a name that differs by a macron is
    another body, keyed by the first page that prints it, and its relations and settlements go with it."""
    def page(slug, name, flags):
        out = read.read_page(_iwi_page(_table("x", [["A", "B", "C", "D"]]), _org(1, name, flags, [])), slug * 64,
                             f"https://www.tkm.govt.nz/iwi/{slug}/")
        return out
    pages = [page("a", "Ngāti Rua Trust", [PSGE]), page("b", "Ngāti Rūa Trust", [MANDATE]),
             page("c", "Ngāti Rua Trust", [RMA]), page("d", "Ngāti Rūa Trust", [RMA])]
    ents = [e for p in pages for e in p["entities"]]
    rels = [r for p in pages for r in p["relations"]]
    sets = [s for p in pages for s in p["settlements"]]
    assert load.split_by_printed_name(ents, rels, sets) == ["tkm/org/ngati-rua-trust"]
    orgs = [(e["key"], e["name"]) for e in ents if e["key"].startswith("tkm/org/")]
    assert orgs == [("tkm/org/ngati-rua-trust/a", "Ngāti Rua Trust"), ("tkm/org/ngati-rua-trust/b", "Ngāti Rūa Trust"),
                    ("tkm/org/ngati-rua-trust/a", "Ngāti Rua Trust"), ("tkm/org/ngati-rua-trust/b", "Ngāti Rūa Trust")]
    assert {(r["from_key"], r["to_key"]) for r in rels if r["relation"] == "organisation of iwi"} == {
        ("tkm/org/ngati-rua-trust/a", "tkm/iwi/a"), ("tkm/org/ngati-rua-trust/b", "tkm/iwi/b"),
        ("tkm/org/ngati-rua-trust/a", "tkm/iwi/c"), ("tkm/org/ngati-rua-trust/b", "tkm/iwi/d")}
    assert {(s["entity_key"], s["key"], s["stage"]) for s in sets} == {
        ("tkm/org/ngati-rua-trust/a", "tkm/org/ngati-rua-trust/a|tkm/settlement/ngati-invented-claims-settlement-act-2019",
         "settled: Act"),
        ("tkm/org/ngati-rua-trust/b", "tkm/org/ngati-rua-trust/b|tkm/mandate/ngati-rua-trust", "mandate recognised")}
    same = [page("a", "Ngāti Rua Trust", [RMA]), page("b", "NGĀTI RUA  Trust", [RMA])]
    ents = [e for p in same for e in p["entities"]]
    assert load.split_by_printed_name(ents, [], []) == []
    assert {e["key"] for e in ents if e["key"].startswith("tkm/org/")} == {"tkm/org/ngati-rua-trust"}


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
        conn.execute(f"DELETE FROM {T('read_pages')}")
        assert check.outside(conn, SAMPLE_SCHEMA, filled["entries"])[0].startswith(
            "a finished walk is held and none of it is published")
    finally:
        conn.rollback()
