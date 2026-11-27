"""The feeds tab: a media-monitoring feed made from a register entity, broad at first and narrowed (curation steps 3 to
6; Arthur, 26 November 2026: "What we really want is to be able to select an entity and create a feed with relevant
news about them. We want it to start broad and be able to narrow it down"; docs/research/curation-plan.md).

    GET  /feeds                    the feeds made, and a search for an entity to make one from
    GET  /feeds?find=<words>       the entities the read news ties to, whose name holds the words
    GET  /feeds?f=<feed>           one feed: its stories newest first, each saying why it is there; the controls
    POST /feeds/new                entity → a new feed, broad (every relation, its subjects, every type, source, form)
    POST /feeds/save               a feed's settings, as the controls send them

A FEED is its newest settings in `<live>/board/feeds.jsonl` (append-only: a save is a line, the newest line of a feed
counts, a withdrawn feed is a line saying so; nothing is erased). Its items are found at each view, from the
published views of the links lane (links/news.py): never a list kept beside them.

WHAT LETS A STORY IN (the read articles only, decision 2):
  named      the entity is tied in the article (pub.news_ties, status tied: one register entity of that key and kind)
  central    tied, and in the headline, named in three or more forms, or quoted
  in a role  tied, and quoted or holding a role (or the one a role is of)
  connected  an entity one step from it in the registers is tied in the article (decision 3): a company's or a
             society's directors, officers and shareholders, by the body's NZBN in their rows' keys; a person's
             companies and societies the same way
  subjects   the article carries one of the feed's subjects (decision 13: broad includes the documents on its
             subjects that never name it). A feed's subjects start as those its own articles carry far more often
             than the read news does (LIFT times, in SHARE of its own articles), up to MAX_SUBJECTS; one that
             would outnumber the feed's own articles OUTWEIGH times starts unticked; Arthur turns any
             off and adds his own, typed: a typed subject catches its other forms by stems ("3D printing" catches
             "3D-printed firearms"), and takes more names (decision 9: one subject, several signifiers)
A possible tie (the name fits several entities, decision 1) lets nothing in: those articles are counted and listed
apart. Narrowed by type (news only is joined tonight; the others are listed as not yet joined), by source (the site)
and by form (news, opinion, feature, media release ...; decision 19). Newest first (decision 10).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import secrets
import threading
import urllib.parse

from products.board import panes
from products.board.panes import esc

TAB = "feeds"
PATH = "/feeds"
NEW = "/feeds/new"
SAVE = "/feeds/save"
LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
LEDGER = os.path.join(LIVE, "board", "feeds.jsonl")
RELATIONS = (("named", "named in it"), ("central", "central to it"), ("role", "in a role"), ("connected", "connected to it"))
#: the document types a feed can draw from; only those joined to the entities so far can be on
TYPES = (("news", "news articles", True), ("hansard", "Hansard", False), ("council_minutes", "council minutes", False),
         ("gets", "GETS tenders", False), ("gazette", "the Gazette", False), ("courts", "court decisions", False),
         ("beehive", "Beehive releases", False))
STORIES = 150
#: a suggested subject: in SHARE of the entity's own articles (at least MIN_SHARED), LIFT times as often as in the read
#: news; one whose articles outnumber the entity's own more than OUTWEIGH times starts off (listed, unticked)
LIFT, SHARE, MIN_SHARED, MAX_SUBJECTS, OUTWEIGH = 8.0, 0.05, 3, 15, 3.0
BODY = re.compile(r"^(companies|societies):\1/(\d{13})$")
ROW_BODY = re.compile(r"^(companies|societies):\1/(\d{13})/")
#: a row of these views carries its body's NZBN in its key; what the other entity is, seen from the body and from the person
OF_BODY = {"directors": "director", "shareholders": "shareholder", "company_lookup_roles": "officer",
           "company_lookup_holdings": "shareholder", "society_officers": "officer"}
OF_PERSON = {"directors": "a company they direct", "shareholders": "a company they hold shares in",
             "company_lookup_roles": "a company they hold a role in", "company_lookup_holdings": "a company they hold shares in",
             "society_officers": "a society they are an officer of"}
CONNECT_VIEWS = tuple(OF_BODY)
_LOCK = threading.Lock()

CSS = """
.feeds{max-width:80rem;margin:0 auto;padding:0 1rem 4rem}
.fd-top{display:flex;gap:1rem;align-items:baseline;flex-wrap:wrap;margin:.5rem 0}
.fd-top h1{font-size:22px;margin:0}
.fd-layout{display:grid;grid-template-columns:minmax(0,1fr) 20rem;gap:1.5rem}
.fd-ctl{position:sticky;top:.5rem;align-self:start;max-height:calc(100vh - 5rem);overflow-y:auto;background:#161a20;
  border:1px solid #3a404c;border-radius:8px;padding:.6rem .9rem;font-size:13px}
.fd-ctl h3{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#aab1bc;margin:.9rem 0 .3rem}
.fd-ctl label{display:block;margin:.15rem 0}
.fd-ctl .n{color:#8a8f99;margin-left:.25rem}
.fd-ctl .off{color:#6b707a}
.fd-ctl input[type=text]{width:100%;box-sizing:border-box;margin:.2rem 0}
.fd-ctl button{margin-top:.6rem}
.fd-list{display:grid;gap:.9rem}
.fd-story{display:grid;grid-template-columns:9rem minmax(0,1fr);gap:.8rem;border-bottom:1px solid #2a303a;padding-bottom:.8rem}
.fd-story .pic{aspect-ratio:16/10;background:#24221e;overflow:hidden;border-radius:3px}
.fd-story .pic img{width:100%;height:100%;object-fit:cover;display:block}
.fd-story .pic.none{display:flex;align-items:center;justify-content:center}
.fd-story .pic.none::after{content:attr(data-site);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:#8a8578}
.fd-story h3{font-size:17px;margin:0 0 .25rem;line-height:1.25}
.fd-story h3 a{color:#e8eaed;text-decoration:none}
.fd-story h3 a:hover{text-decoration:underline}
.fd-story p{margin:0 0 .3rem;color:#cfd3da;font-size:14px;line-height:1.4}
.fd-story .by{font-size:11px;color:#8a8f99;text-transform:uppercase;letter-spacing:.06em}
.fd-why{display:flex;flex-wrap:wrap;gap:.3rem;margin-top:.3rem}
.fd-why span{font-size:11px;padding:.05rem .45rem;border-radius:9px;background:#24364f;color:#d6e2f2}
.fd-why span.sub{background:#2f3b2a;color:#d8e6cc}
.fd-why span.con{background:#3b2f2a;color:#ecd9cc}
.fd-poss{margin-top:2rem;color:#aab1bc;font-size:13px}
.fd-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(16rem,1fr));gap:.8rem;margin:.8rem 0}
.fd-card{border:1px solid #3a404c;border-radius:8px;padding:.6rem .8rem}
.fd-card a{color:#8cb8ff}
"""


# ---- the ledger --------------------------------------------------------------------------------------------------

def feeds(path: str = None) -> dict:
    """{feed id: its newest settings}, withdrawn ones included (marked)."""
    out = {}
    try:
        with open(path or LEDGER, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    out[r["feed"]] = r
    except FileNotFoundError:
        pass
    return out


def save(settings: dict, path: str = None) -> dict:
    from support import appendline
    p = path or LEDGER
    os.makedirs(os.path.dirname(p), exist_ok=True)
    rec = {**settings, "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    with _LOCK:
        appendline.append_json(p, rec, ensure_ascii=False)
    return rec


# ---- what a feed holds -------------------------------------------------------------------------------------------

def fold(s: str) -> str:
    from support.subjecttext import fold as f
    return f(s)


def connected(conn, entity_id: str) -> dict:
    """{entity_id: why}: the entities one step from this one in the registers (decision 3)."""
    out = {}
    m = BODY.match(entity_id or "")
    if m:            # a body: the people (and bodies) whose director, officer or shareholder rows carry its NZBN
        reg, nzbn = m.groups()
        for gid, view in conn.execute(
                "SELECT DISTINCT g.group_id::text, r.view FROM pub.names r JOIN pub.groups g ON g.row_key = r.ref "
                "WHERE r.ref LIKE %s AND r.view = ANY(%s)", (f"{reg}:{reg}/{nzbn}/%", list(CONNECT_VIEWS))).fetchall():
            if gid != entity_id:
                out.setdefault(gid, OF_BODY[view])
    else:            # a person or a body grouped otherwise: the bodies its rows are an officer, director or shareholder of
        for ref, view in conn.execute(
                "SELECT g.row_key, r.view FROM pub.groups g JOIN pub.names r ON r.ref = g.row_key "
                "WHERE g.group_id::text = %s AND r.view = ANY(%s)", (entity_id, list(CONNECT_VIEWS))).fetchall():
            mm = ROW_BODY.match(ref)
            if mm:
                out.setdefault(f"{mm.group(1)}:{mm.group(1)}/{mm.group(2)}", OF_PERSON[view])
    return out


def suggest_subjects(conn, entity_id: str) -> list[dict]:
    """The subjects the entity's own articles carry far more often than the read news does (decision 17's first
    half: from the documents that name it; the register's industry code is the second half, not joined yet)."""
    rows = conn.execute("""
        WITH mine AS (SELECT DISTINCT url_key FROM pub.news_ties WHERE entity_id = %s AND status = 'tied'),
             n AS (SELECT count(*)::float AS all_n, (SELECT count(*) FROM mine)::float AS my_n FROM pub.news_articles)
        SELECT s.subject, min(s.said), count(*) AS here, t.total,
               (count(*) / n.my_n) / (t.total / n.all_n) AS lift, n.my_n
        FROM mine JOIN pub.news_subjects s USING (url_key)
        JOIN (SELECT subject, count(*)::float AS total FROM pub.news_subjects GROUP BY 1) t USING (subject), n
        GROUP BY s.subject, t.total, n.my_n, n.all_n
        HAVING count(*) >= %s ORDER BY lift DESC, count(*) DESC LIMIT %s""",
                        (entity_id, MIN_SHARED, MAX_SUBJECTS * 3)).fetchall()
    out = [{"name": said, "signifiers": [said], "on": total <= OUTWEIGH * my_n, "here": int(here), "total": int(total),
            "lift": round(lift, 1)}
           for subj, said, here, total, lift, my_n in rows if lift >= LIFT and here >= SHARE * my_n]
    return out[:MAX_SUBJECTS]


def subject_keys(conn, subjects: list[dict]) -> set:
    """The folded subjects the read news holds that a feed's subjects catch: each signifier as it is, and by its stems
    in any subject that holds them ("3D printing" in "3D-printed firearms")."""
    from support.subjecttext import names_in
    want = [s for x in subjects if x.get("on", True) for s in (x.get("signifiers") or [x["name"]]) if s.strip()]
    # a signifier Arthur added to a suggested subject is typed too: it catches its other forms
    if not want:
        return set()
    held = [r[0] for r in conn.execute("SELECT DISTINCT subject FROM pub.news_subjects").fetchall()]
    out = set()
    typed = {fold(s) for x in subjects if x.get("typed") for s in (x.get("signifiers") or [x["name"]])}
    for w in want:
        fw = fold(w)
        out |= {h for h in held if h == fw or (fw in typed and names_in(w, h))}
    return out


def items(conn, f: dict) -> tuple[list[dict], dict]:
    """(stories newest first, facts): the read articles the feed's settings let in, each with why."""
    rel = set(f.get("relations") or [x for x, _ in RELATIONS])
    eid = f["entity_id"]
    why: dict[str, list] = {}
    if rel & {"named", "central", "role"}:
        for url_key, central, role in conn.execute(
                "SELECT t.url_key, bool_or(n.in_headline OR n.mentions >= 3 OR n.quoted), bool_or(n.in_role OR n.quoted) "
                "FROM pub.news_ties t JOIN pub.news_entities n USING (url_key, entity) "
                "WHERE t.entity_id = %s AND t.status = 'tied' GROUP BY 1", (eid,)).fetchall():
            w = []
            if "named" in rel:
                w.append(("named", "named"))
            if central and "central" in rel:
                w.append(("central", "central"))
            if role and "role" in rel:
                w.append(("role", "in a role"))
            if w:
                why[url_key] = w
    con = {}
    if "connected" in rel:
        con = connected(conn, eid)
        if con:
            names = dict(conn.execute("SELECT entity_id, display_name FROM pub.entities WHERE entity_id = ANY(%s)",
                                      (list(con),)).fetchall())
            for url_key, other in conn.execute(
                    "SELECT DISTINCT url_key, entity_id FROM pub.news_ties WHERE entity_id = ANY(%s) AND status = 'tied'",
                    (list(con),)).fetchall():
                why.setdefault(url_key, []).append(("con", f"{names.get(other, other)} ({con[other]})"))
    keys = set()
    if f.get("subjects_on", True):
        keys = subject_keys(conn, f.get("subjects") or [])
        if keys:
            for url_key, said in conn.execute("SELECT url_key, min(said) FROM pub.news_subjects WHERE subject = ANY(%s) GROUP BY 1",
                                              (sorted(keys),)).fetchall():
                why.setdefault(url_key, []).append(("sub", said))
    facts = {"connected": len(con), "subject_keys": len(keys), "matched": len(why)}
    if not why or "news" in set(f.get("types_out") or []):
        return [], facts
    cur = conn.execute(
        "SELECT r.url_key, r.url, r.host, r.title, r.author, r.published_at, r.opening, r.capture_sha256, a.form "
        "FROM pub.news_read r LEFT JOIN pub.news_articles a USING (url_key) WHERE r.url_key = ANY(%s) "
        "AND NOT (r.host = ANY(%s)) AND NOT (coalesce(a.form, '') = ANY(%s)) "
        "ORDER BY r.published_at DESC NULLS LAST LIMIT %s",
        (list(why), list(f.get("sources_out") or []), list(f.get("forms_out") or []), STORIES))
    cols = [c.name for c in cur.description]
    out = [dict(zip(cols, r)) | {"why": why[r[0]]} for r in cur.fetchall()]
    facts["sources"] = dict(conn.execute(
        "SELECT r.host, count(*) FROM pub.news_read r WHERE r.url_key = ANY(%s) GROUP BY 1 ORDER BY 2 DESC LIMIT 40",
        (list(why),)).fetchall())
    facts["forms"] = dict(conn.execute(
        "SELECT coalesce(form, 'unknown'), count(*) FROM pub.news_articles WHERE url_key = ANY(%s) GROUP BY 1 ORDER BY 2 DESC",
        (list(why),)).fetchall())
    return out, facts


def possible(conn, entity_id: str, limit: int = 20) -> tuple[int, list]:
    n = conn.execute("SELECT count(DISTINCT url_key) FROM pub.news_ties WHERE entity_id = %s AND status = 'possible'",
                     (entity_id,)).fetchone()[0]
    rows = conn.execute(
        "SELECT r.url, r.title, r.host, r.published_at, n.name, t.candidates FROM pub.news_ties t "
        "JOIN pub.news_entities n USING (url_key, entity) JOIN pub.news_read r USING (url_key) "
        "WHERE t.entity_id = %s AND t.status = 'possible' ORDER BY r.published_at DESC NULLS LAST LIMIT %s",
        (entity_id, limit)).fetchall()
    return n, rows


# ---- pages -------------------------------------------------------------------------------------------------------

def _when(t) -> str:
    return t.strftime("%-d %b %Y %H:%M") if t else ""


def story(r: dict) -> str:
    from products.board import paper
    pic = (f'<div class="pic" data-site="{esc(r["host"])}"><img src="{esc(paper.PICTURE + "?" + urllib.parse.urlencode({"k": r["url_key"]}))}" '
           f'alt="" loading="lazy" referrerpolicy="no-referrer"></div>')
    chips = "".join(f'<span class="{esc(k)}">{esc(v)}</span>' for k, v in r["why"])
    by = " · ".join(x for x in (r["host"], r.get("author") or "", r.get("form") or "", _when(r["published_at"])) if x)
    return (f'<article class="fd-story pp-story">{pic}<div><h3><a href="{esc(r["url"])}" target="_blank" rel="noopener noreferrer">'
            f'{esc(r["title"])}</a></h3><p>{esc(paper.blurb(r.get("opening") or "", r["title"], 36))}</p>'
            f'<div class="by">{esc(by)}</div><div class="fd-why">{chips}</div></div></article>')


def controls(f: dict, facts: dict) -> str:
    rel = set(f.get("relations") or [x for x, _ in RELATIONS])
    h = [f'<form method="post" action="{SAVE}" class="fd-ctl"><input type="hidden" name="f" value="{esc(f["feed"])}">',
         f'<h3>name</h3><input type="text" name="name" value="{esc(f.get("name") or "")}">', "<h3>relations</h3>"]
    h += [f'<label><input type="checkbox" name="rel" value="{k}"{" checked" if k in rel else ""}> {esc(v)}</label>' for k, v in RELATIONS]
    if "connected" in rel:
        h.append(f'<p class="n">{facts.get("connected", 0)} entities one step away</p>')
    h.append(f'<h3>subjects</h3><label><input type="checkbox" name="subjects_on" value="1"{" checked" if f.get("subjects_on", True) else ""}>'
             f' documents on these subjects, named or not</label>')
    for i, s in enumerate(f.get("subjects") or []):
        names = " / ".join(s.get("signifiers") or [s["name"]])
        here = (f'<span class="n">{s["here"]} of its own, {s.get("total", "?")} in all</span>' if s.get("here") else "")
        h.append(f'<label><input type="checkbox" name="subj_on" value="{i}"{" checked" if s.get("on", True) else ""}> {esc(names)}'
                 f'{here}</label>'
                 f'<input type="hidden" name="subj_{i}" value="{esc(json.dumps(s, ensure_ascii=False))}">'
                 f'<input type="text" name="sig_{i}" placeholder="another name for it" value="">')
    h.append('<input type="text" name="subj_new" placeholder="add a subject (e.g. 3D printing)" value="">')
    h.append("<h3>types</h3>")
    out_t = set(f.get("types_out") or [])
    for k, label, joined in TYPES:
        if joined:
            h.append(f'<label><input type="checkbox" name="type" value="{k}"{"" if k in out_t else " checked"}> {esc(label)}</label>')
        else:
            h.append(f'<label class="off"><input type="checkbox" disabled> {esc(label)} (not joined yet)</label>')
    out_s = set(f.get("sources_out") or [])
    srcs = dict(facts.get("sources") or {})
    for s in out_s:
        srcs.setdefault(s, 0)
    if srcs:
        h.append("<h3>sources</h3>")
        h += [f'<label><input type="checkbox" name="src" value="{esc(s)}"{"" if s in out_s else " checked"}> {esc(s)}'
              f'<span class="n">{n or ""}</span></label><input type="hidden" name="src_all" value="{esc(s)}">' for s, n in srcs.items()]
    out_f = set(f.get("forms_out") or [])
    forms = dict(facts.get("forms") or {})
    for s in out_f:
        forms.setdefault(s, 0)
    if forms:
        h.append("<h3>forms</h3>")
        h += [f'<label><input type="checkbox" name="form" value="{esc(s)}"{"" if s in out_f else " checked"}> {esc(s.replace("_", " "))}'
              f'<span class="n">{n or ""}</span></label><input type="hidden" name="form_all" value="{esc(s)}">' for s, n in forms.items()]
    h.append('<button type="submit">narrow</button> <label><input type="checkbox" name="withdraw" value="1"> withdraw this feed</label></form>')
    return "".join(h)


def take(form: dict, path: str = None) -> str:
    """A posted form → the feed saved; the address to go to."""
    get = lambda k: (form.get(k) or [""])[0]
    have = feeds(path)
    fid = get("f")
    if fid not in have:
        raise ValueError("no such feed")
    f = dict(have[fid])
    f.pop("at", None)
    f["name"] = get("name").strip()[:120] or f.get("name")
    f["relations"] = [k for k, _ in RELATIONS if k in (form.get("rel") or [])]
    f["subjects_on"] = get("subjects_on") == "1"
    on = set(form.get("subj_on") or [])
    subs = []
    i = 0
    while f"subj_{i}" in form:
        s = json.loads(get(f"subj_{i}"))
        s["on"] = str(i) in on
        sig = get(f"sig_{i}").strip()[:120]
        if sig and fold(sig) not in {fold(x) for x in s.get("signifiers") or []}:
            s["signifiers"] = (s.get("signifiers") or [s["name"]]) + [sig]
        subs.append(s)
        i += 1
    new = get("subj_new").strip()[:120]
    if new and fold(new) not in {fold(x) for s in subs for x in s.get("signifiers") or [s["name"]]}:
        subs.append({"name": new, "signifiers": [new], "on": True, "typed": True})
    f["subjects"] = subs
    f["types_out"] = [k for k, _, joined in TYPES if joined and k not in (form.get("type") or [])]
    f["sources_out"] = sorted(set(form.get("src_all") or []) - set(form.get("src") or []))
    f["forms_out"] = sorted(set(form.get("form_all") or []) - set(form.get("form") or []))
    f["withdrawn"] = get("withdraw") == "1"
    save(f, path)
    return PATH if f["withdrawn"] else f"{PATH}?f={urllib.parse.quote(fid)}"


def create(conn, form: dict, path: str = None) -> str:
    eid = ((form.get("entity_id") or [""])[0]).strip()
    row = conn.execute("SELECT entity_id, display_name, kind FROM pub.entities WHERE entity_id = %s", (eid,)).fetchone()
    if not row:
        raise ValueError("no such entity")
    fid = secrets.token_hex(4)
    save({"feed": fid, "name": row[1], "entity_id": row[0], "entity_name": row[1], "kind": row[2],
          "relations": [k for k, _ in RELATIONS], "subjects_on": True, "subjects": suggest_subjects(conn, row[0]),
          "types_out": [], "sources_out": [], "forms_out": [], "withdrawn": False}, path)
    return f"{PATH}?f={fid}"


def finder(conn, words: str) -> str:
    rows = []
    if words:
        rows = conn.execute(
            "SELECT e.entity_id, e.display_name, e.kind, e.registers, count(DISTINCT t.url_key) AS n "
            "FROM (SELECT entity_id, url_key FROM pub.news_ties WHERE status = 'tied') t JOIN pub.entities e USING (entity_id) "
            "WHERE e.display_name ILIKE %s GROUP BY 1, 2, 3, 4 ORDER BY n DESC LIMIT 30",
            ("%" + words.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%",)).fetchall()
    form = (f'<form method="get" action="{PATH}" class="fd-top"><input type="search" name="find" value="{esc(words)}" '
            f'placeholder="a person, company or body named in the read news" size="40"><button>find</button></form>')
    if not words:
        return form
    if not rows:
        return form + '<p class="why">no entity the read news ties to has that in its name</p>'
    cards = "".join(
        f'<div class="fd-card"><b>{esc(name)}</b> <span class="n">{esc(kind)}</span><br><span class="n">{n} articles · '
        f'{esc(", ".join(regs or []))}</span><form method="post" action="{NEW}"><input type="hidden" name="entity_id" value="{esc(eid)}">'
        f'<button>make a feed</button></form></div>' for eid, name, kind, regs, n in rows)
    return form + f'<div class="fd-cards">{cards}</div>'


def render(conn, qs: dict, path: str = None) -> str:
    one = lambda k: ((qs.get(k) or [""])[0] or "").strip()[:200]
    have = {k: v for k, v in feeds(path).items() if not v.get("withdrawn")}
    fid = one("f")
    from products.board import assets
    script = f'<script src="{esc(assets.url("paper.js"))}" defer></script>'
    if fid and fid in have:
        f = have[fid]
        try:
            rows, facts = items(conn, f)
            n_poss, poss = possible(conn, f["entity_id"])
            from products.board import paper
            with paper._LOCK:                     # the picture route answers only for a story a page showed
                for r in rows:
                    paper._SHOWN[r["url_key"]] = (r["url"], r["capture_sha256"] or "")
            err = ""
        except Exception as e:
            rows, facts, n_poss, poss, err = [], {}, 0, [], f"{type(e).__name__}: {str(e).splitlines()[0][:200]}"
        top = (f'<div class="fd-top"><h1>{esc(f.get("name"))}</h1><span class="n">{esc(f.get("kind") or "")} · '
               f'{len(rows)} stories shown of {facts.get("matched", 0)} matched · newest first</span>'
               f'<a href="{PATH}">all feeds</a></div>')
        body = (f'<p class="why">the feed could not be read: {esc(err)}</p>' if err else
                "".join(story(r) for r in rows) or '<p class="why">nothing the read news holds lets a story in</p>')
        pl = ""
        if n_poss:
            pl = (f'<div class="fd-poss"><h3>possible ({n_poss} articles)</h3><p>The name in these fits this entity and '
                  f'another; they are kept out (decision 1).</p><ul>' +
                  "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener noreferrer">{esc(t)}</a> · {esc(h)} · '
                          f'{esc(_when(p))} · “{esc(nm)}” fits {c}</li>' for u, t, h, p, nm, c in poss) + "</ul></div>")
        inner = f'{top}<div class="fd-layout"><div><div class="fd-list">{body}</div>{pl}</div>{controls(f, facts)}</div>'
    else:
        cards = "".join(f'<div class="fd-card"><a href="{PATH}?f={esc(k)}"><b>{esc(v.get("name"))}</b></a><br>'
                        f'<span class="n">{esc(v.get("kind") or "")} · made {esc((v.get("at") or "")[:10])}</span></div>'
                        for k, v in sorted(have.items(), key=lambda kv: kv[1].get("name") or ""))
        inner = (f'<div class="fd-top"><h1>feeds</h1></div>{finder(conn, one("find"))}'
                 + (f'<div class="fd-cards">{cards}</div>' if cards else '<p class="why">no feed made yet: find an entity above</p>'))
    return panes.page("", [], [f'<style>{CSS}</style><section class="feeds">{inner}</section>{script}'], tab=TAB)
