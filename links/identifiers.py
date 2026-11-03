"""The links a private value makes (ruling 142, Arthur, 4 November 2026: "I'm not going to look at the pairs, just go
ahead with your recommendations"): the rules of links/measurements.md §15 and §16, built.

    judgment-address-title@1      a judgment's street address and a LINZ title's; an owner of the title the row
    judgment-address-judgment@1   one street address printed in two court documents
    judgment-address-insolvency@1 a judgment's street address and an estate's address at adjudication
    judgment-address-office@1     a judgment's street address and a company's registered office
    shared-contact@1              one email or phone printed in two court documents (ruling 2)

What it reads. The lanes' private values through the views each lane declares in `pub_private`
(registers/<lane>/pub_private.sql, made by support.db.private_views at the start of the step):
`pub_private.court_identifiers`, `pub_private.insolvency_addresses`, `pub_private.linz_title_addresses` and
`pub_private.linz_title_address_points` (a title's address by geometry). A view not made
(its lane not loaded) makes no link and says so. The rows are the lane's own (`<schema>.rows`); a court document's page
text is opened for the identifiers' own pages only (known documents, never the store wholesale).

How a value is sorted (§15, the measurement's method). An email by its domain (courts, tribunals and government; law
firms; personal webmail; a company's; other); a phone, a street address and a PO Box by the 400 characters before it on
its page (a registry heading; a law firm's words; toll-free; recurring in five or more cases). An office's value (a
court's, an agency's, a law firm's, toll-free, printed in five or more cases) is no one's and makes no link.

Whose value it is (the tie). A value's `person` where the lane filled it (the text reader's item; empty today); else the
party, witness or other person (or body) of the document whose name is printed nearest the value on its page, within
TIE_WINDOW characters (`how`: "person field" or "nearest name on the page"). Judges and counsel are never tied.

Where it writes. The links (two rows, the rule, the level, whether a name was shared, how the tie was made) into
`<schema>.links` like every rule's, with no value in their evidence; the values themselves, the identifier keys, the
targets and the distances into `<schema>_private.identifier_links` (`links_private` for `links`), never read by a reader
login. Both are regenerable and refilled at every build. A link touching a text reader's row (`court_people`) is turned
near after by the model tier (links.build.model_tier), as every rule's is.

    build(conn, s, log)          the step, called by links.build.build_links; returns its counts
"""
from __future__ import annotations

import collections
import html
import json
import re
import time

from keys import addresses as ka
from keys import names as kn

import links
from links import rules

COURT_IDENTIFIERS = "pub_private.court_identifiers"
INSOLVENCY_ADDRESSES = "pub_private.insolvency_addresses"
LINZ_TITLE_ADDRESSES = "pub_private.linz_title_addresses"
LINZ_TITLE_POINTS = "pub_private.linz_title_address_points"   # by geometry, for the titles the property spine gives none
RECUR_CASES = 5           # a value printed in this many distinct cases or more is an office's
WINDOW_BEFORE, WINDOW_AFTER = 400, 120
TIE_WINDOW = 1000         # a name printed further than this from the value on its page is not its tie
NOT_TIED_ROLES = ("judge", "counsel")
COURT_VIEWS = ("court_judgment_parties", "court_people")

GOV_DOMAIN = re.compile(r"(\.govt\.nz$|\.mil\.nz$|parliament\.nz$|justice|police|crownlaw|courts?\b|tribunal|"
                        r"\.gov(\.[a-z]{2})?$|\.ac\.nz$|\.school\.nz$|\.health\.nz$|\.dhb\.)")
LAW_DOMAIN = re.compile(r"(law|legal|lawyer|barrister|chambers|solicitor|attorney|counsel|advocat)")
WEBMAIL = {"gmail.com", "googlemail.com", "hotmail.com", "hotmail.co.nz", "outlook.com", "outlook.co.nz", "live.com",
           "live.co.nz", "yahoo.com", "yahoo.co.nz", "xtra.co.nz", "icloud.com", "me.com", "mac.com", "msn.com",
           "slingshot.co.nz", "orcon.net.nz", "vodafone.co.nz", "clear.net.nz", "paradise.net.nz", "ihug.co.nz",
           "actrix.co.nz", "inspire.net.nz", "windowslive.com", "protonmail.com", "proton.me", "aol.com", "gmx.com",
           "kinect.co.nz", "farmside.co.nz", "wave.co.nz", "snap.net.nz", "spark.co.nz", "woosh.co.nz", "maxnet.co.nz",
           "netspeed.net.nz", "xnet.co.nz", "callplus.net.nz", "2degrees.nz", "one.nz", "bigpond.com"}
REGISTRY_CTX = re.compile(r"\b(registry|registrar|case manager|court ?house|tribunals? unit|ministry of justice|"
                          r"justice\.govt|DX [A-Z]{2}\d+|registry of the|the (district|high|family|youth|environment|"
                          r"employment|m[aā]ori land) court,? (at|in) [A-Z][a-z]+ (is|at)|tenancy tribunal|"
                          r"disputes tribunal|employment relations authority)\b", re.I)
WIDE_COURT_CTX = re.compile(r"\b(court|tribunal)\b", re.I)
GOV_CTX = re.compile(r"\b(ministry|department|police|crown law|crown solicitor|council|inland revenue|worksafe|"
                     r"commission|authority|agency|ombudsman|commissioner|government|crown)\b", re.I)
LAW_CTX = re.compile(r"\b(solicitors?|barristers?|lawyers?|law|legal|counsel|chambers|partners|attorneys?|"
                     r"for the (applicant|respondent|plaintiff|defendant|appellant)s?)\b", re.I)
_SUFFIX = re.compile(r"\b(limited|ltd|incorporated|inc|trust|trustees?|company|co|group|holdings|nz|new zealand)\b")

#: the categories (§15) whose value is an office's, never a person's or a party's
OFFICE = {"courts, tribunals, government", "law firms", "toll-free (an organisation)", "recurring, no heading (an office)",
          "government context", "court or registry", "law firm context"}
#: the address categories each address rule reads (§16: the addresses not a court's, a law firm's or an office's street and
#: town; the office rule, §15, every address not a court's or a law firm's)
ADDRESS_CATS = {"neither (likely a person's)", "a company's registered office (street only)"}
OFFICE_CATS = ADDRESS_CATS | {"a company's registered office (street and town)"}


# --- the sorting (§15), pure --------------------------------------------------------------------------------------------

def phone_key(v: str) -> str:
    d = re.sub(r"\D", "", v or "")
    if d.startswith("64"):
        d = "0" + d[2:]
    if d.startswith("00"):
        d = d[1:]
    return d


def value_key(kind: str, v: str) -> str:
    if kind == "email":
        return (v or "").strip().lower()
    if kind == "phone":
        return phone_key(v)
    return ka.address_key(v) if kind == "address" else re.sub(r"\s+", " ", (v or "").lower()).strip()


def domain_stem(d: str) -> str:
    labels = d.split(".")
    for tail in (("co", "nz"), ("org", "nz"), ("net", "nz"), ("com", "au"), ("co", "uk"), ("ac", "nz"), ("govt", "nz")):
        if len(labels) > 2 and tuple(labels[-2:]) == tail:
            return labels[-3]
    return labels[-2] if len(labels) >= 2 else labels[0]


def org_squash(name: str) -> str:
    """An organisation's name as one run of letters and digits, its suffixes off (an email domain's stem is compared to it)."""
    s = kn.fold_diacritics(name or "").lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]", "", _SUFFIX.sub(" ", s))


def window(text: str, value: str) -> str:
    if not text:
        return ""
    flat = re.sub(r"\s+", " ", text)
    v = re.sub(r"\s+", " ", value or "")
    i = flat.lower().find(v.lower())
    return "" if i < 0 else flat[max(0, i - WINDOW_BEFORE): i + len(v) + WINDOW_AFTER]


def category(kind: str, key: str, contexts: list, cases: int, counsel_bodies=(), counsel_people=(), company_stems=(),
             office_town: bool = None) -> str:
    """The §15 category of one value. `contexts`: the windows around its printings; `cases`: the distinct cases printing it;
    `counsel_bodies`/`counsel_people`: counsel's keys in its documents; `company_stems`: squashed company names a domain
    stem may be; `office_town`: for an address, None (no office's street), False (an office's street only), True (street
    and town)."""
    reg = sum(1 for w in contexts if REGISTRY_CTX.search(w))
    wide = sum(1 for w in contexts if WIDE_COURT_CTX.search(w))
    gov = sum(1 for w in contexts if GOV_CTX.search(w))
    law = sum(1 for w in contexts if LAW_CTX.search(w) or any(b and b in org_squash(w) for b in counsel_bodies))
    recurs = cases >= RECUR_CASES
    if kind == "email":
        local, _, dom = key.partition("@")
        local = re.sub(r"[^a-z]", "", local)
        stem = re.sub(r"[^a-z0-9]", "", domain_stem(dom))
        if GOV_DOMAIN.search(dom):
            return "courts, tribunals, government"
        if LAW_DOMAIN.search(dom) or any(len(stem) >= 4 and (stem in b or b in stem) for b in counsel_bodies):
            return "law firms"
        if recurs:
            return "recurring, no heading (an office)"
        if dom in WEBMAIL:
            if any(local and p and local.endswith(p.split(" ")[-1]) for p in counsel_people):
                return "law firms"
            return "personal webmail"
        if len(stem) >= 4 and stem in company_stems:
            return "companies"
        return "other"
    if kind == "phone":
        if reg or (recurs and wide) or (gov and recurs):
            return "courts, tribunals, government"
        if law:
            return "law firms"
        if key.startswith(("0800", "0508")):
            return "toll-free (an organisation)"
        if recurs:
            return "recurring, no heading (an office)"
        return "government context" if gov else "other"
    if reg > 0 or (recurs and (gov > 0 or wide > 0)):
        return "court or registry"
    if law:
        return "law firm context"
    if office_town is True:
        return "a company's registered office (street and town)"
    if office_town is False:
        return "a company's registered office (street only)"
    if recurs:
        return "recurring, no heading (an office)"
    return "neither (likely a person's)"


def name_forms(name: str, kind: str) -> list:
    """The forms a row's name is searched for on a page: as filed, and a person's family name alone (three letters or
    more), lower case."""
    out = []
    n = re.sub(r"\s+", " ", (name or "").strip()).lower()
    if len(n) >= 3:
        out.append(n)
    if kind == "person":
        fam = kn.person_name(name or "").family
        if fam and len(fam) >= 3 and fam.lower() not in out:
            out.append(fam.lower())
    return out


def nearest(text: str, value: str, cands: list):
    """The candidate ({ref, kind, name_filed, ...}) whose name is printed nearest `value` on the page `text`, within
    TIE_WINDOW characters, and the distance; (None, None) when none is, or two of different names are equally near."""
    flat = re.sub(r"\s+", " ", text or "").lower()
    v = re.sub(r"\s+", " ", value or "").lower()
    at = flat.find(v)
    if at < 0:
        return None, None
    best, best_d, tied = None, None, False
    for c in cands:
        for form in name_forms(c["name_filed"], c["kind"]):
            for m in re.finditer(r"(?<![a-z])" + re.escape(form) + r"(?![a-z])", flat):
                d = at - m.end() if m.end() <= at else max(0, m.start() - (at + len(v)))
                if d > TIE_WINDOW:
                    continue
                if best_d is None or d < best_d:
                    best, best_d, tied = c, d, False
                elif d == best_d and c["key"] != best["key"]:
                    tied = True
            if best is c:
                break
    return (None, None) if tied or best is None else (best, best_d)


# --- the step ----------------------------------------------------------------------------------------------------------

PRIVATE_DDL = """
CREATE SCHEMA IF NOT EXISTS {p};
CREATE TABLE IF NOT EXISTS {p}.identifier_links (
    row_a text NOT NULL, row_b text NOT NULL, rule text NOT NULL, grade text NOT NULL,
    kind text NOT NULL,            -- email, phone or address
    identifier text NOT NULL,      -- the courts lane's identifier key on the judgment side
    document text NOT NULL,
    value text NOT NULL,           -- the value as printed (private)
    target text,                   -- the other side: an identifier key, a title, an estate, a company
    target_value text,             -- the other side's value as printed (private)
    level text, tie text, distance integer,
    built_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX IF NOT EXISTS identifier_links_pair ON {p}.identifier_links (row_a, row_b);
"""


def private_of(s: str) -> str:
    return "links_private" if s == links.SCHEMA else f"{s}_private"


def _exists(conn, name: str) -> bool:
    return conn.execute("SELECT to_regclass(%s) IS NOT NULL", (name,)).fetchone()[0]


def _page_texts(sha: str, pages: set) -> dict:
    from support.docread import pages as P
    from support.docstore.landing import read_bytes
    try:
        data = read_bytes(sha)
    except Exception:
        return {}
    if not data:
        return {}
    if not data.startswith(b"%PDF"):
        t = html.unescape(re.sub(r"<[^>]+>", " ", data.decode("utf-8", "replace")))
        return {p: t for p in pages}
    out = {}
    for p in pages:
        try:
            out[p] = P.page_text(data, p) or ""
        except Exception:
            out[p] = ""
    return out


def build(conn, s: str, log=print) -> dict:
    """Make the five rules' links into `<s>.links` and their values into `<s>_private.identifier_links`. Returns counts."""
    from support import db
    t0 = time.monotonic()
    p = private_of(s)
    views = db.private_views(conn, log=lambda *_: None)
    conn.execute(PRIVATE_DDL.format(p=p))
    conn.execute(f"DELETE FROM {p}.identifier_links")
    conn.execute(f"DELETE FROM {s}.links WHERE rule = ANY(%s)", ([rules.RULE_ADDRESS_TITLE, rules.RULE_ADDRESS_JUDGMENT,
                                                                 rules.RULE_ADDRESS_INSOLVENCY, rules.RULE_ADDRESS_OFFICE,
                                                                 rules.RULE_SHARED_CONTACT],))
    out = {"views": views}
    if not _exists(conn, COURT_IDENTIFIERS):
        out["court identifiers"] = "not made"
        conn.commit()
        return out
    q = lambda sql, *a: conn.execute(sql, a).fetchall()  # noqa: E731
    ids = q(f"SELECT key, person, document, kind, value, coalesce(page, 1) FROM {COURT_IDENTIFIERS} "
            f"WHERE kind IN ('address', 'email', 'phone')")
    docs = sorted({r[2] for r in ids})
    case_of = {d: c for d, c in q("SELECT document, coalesce(case_slug, citation, document) FROM pub.court_documents "
                                  "WHERE document = ANY(%s)", docs)}
    # the rows of each document, with the role the text gives it (court_people) or a party's (court_judgment_parties)
    rows_by_doc = collections.defaultdict(list)
    counsel_bodies, counsel_people = collections.defaultdict(set), collections.defaultdict(set)
    for ref, view, key, kind, name_key, fl_key, name_filed, d, role in q(f"""
            SELECT r.ref, r.view, r.key, r.kind, r.name_key, r.fl_key, r.name_filed, r.document,
                   CASE WHEN r.view = 'court_people' THEN cp.role ELSE 'party' END
            FROM {s}.rows r LEFT JOIN pub.court_people cp ON r.view = 'court_people' AND cp.key = r.key
            WHERE r.register = 'courts' AND r.view = ANY(%s) AND r.document = ANY(%s)""", list(COURT_VIEWS), docs):
        if role == "counsel":
            (counsel_people if kind == "person" else counsel_bodies)[d].add(
                (name_key or "") if kind == "person" else org_squash(name_filed))
        if role in NOT_TIED_ROLES:
            continue
        rows_by_doc[d].append({"ref": ref, "view": view, "key": key, "kind": kind, "name_filed": name_filed,
                               "name": (fl_key or name_key) if kind == "person" else name_key, "name_key": name_key})
    # one row per name per document: a parser's party row before a text reader's (a model's row is near only)
    def pick(rs):
        return sorted(rs, key=lambda r: (r["view"] != "court_judgment_parties", r["ref"].encode()))[0]
    names_in = collections.defaultdict(dict)       # document -> {(kind, name): row}
    for d, rs in rows_by_doc.items():
        by = collections.defaultdict(list)
        for r in rs:
            if r["name"]:
                by[(r["kind"], r["name"])].append(r)
        names_in[d] = {k: pick(v) for k, v in by.items()}
    # the page texts, the identifiers' own pages only
    need = collections.defaultdict(set)
    for _, _, d, _, _, page in ids:
        need[d].add(page)
    texts = {d: _page_texts(d, pg) for d, pg in sorted(need.items())}
    out["documents"] = len(docs)
    out["documents unread"] = sum(1 for d in docs if not texts.get(d))
    log(f"links.identifiers: {len(ids)} identifiers on {len(docs)} documents, texts read ({time.monotonic() - t0:.0f} s)")

    # every value, its printings, its category
    by_value = collections.defaultdict(list)       # (kind, key) -> [(identifier key, person, document, value, page)]
    for key, person, d, kind, v, page in ids:
        k = value_key(kind, v)
        if k:
            by_value[(kind, k)].append((key, person, d, v, page))
    parsed = {}                                     # identifier key -> street parts
    for key, _, _, kind, v, _ in ids:
        if kind == "address":
            sp = ka.street_parts(v)
            if sp:
                parsed[key] = sp
    # the registered offices, read the same way, for the street keys the judgments print
    want = {ka.street_key(sp) for sp in parsed.values()}
    offices = collections.defaultdict(list)        # street key -> [(company ref, parts, address)]
    for ent, l1, l2, l3, l4, pc in conn.execute("SELECT entity_key, line_1, line_2, line_3, line_4, postcode FROM "
                                                "pub.company_addresses WHERE kind = 'registered office'"):
        text = ", ".join(x for x in (l1, l2, l3, l4, pc) if x)
        sp = ka.street_parts(text)
        if sp and ka.street_key(sp) in want:
            offices[ka.street_key(sp)].append((links.ref("companies", ent), sp, text))
    log(f"links.identifiers: offices read ({time.monotonic() - t0:.0f} s)")
    stems = {re.sub(r"[^a-z0-9]", "", domain_stem(k.partition("@")[2])) for (kind, k) in by_value if kind == "email"}
    company_stems = {x for (x,) in q(f"SELECT DISTINCT replace(org_key, ' ', '') FROM {s}.bodies "
                                     f"WHERE replace(org_key, ' ', '') = ANY(%s)", sorted(x for x in stems if len(x) >= 4))}
    cat = {}
    for (kind, k), prints in by_value.items():
        ctx = [window(texts.get(d, {}).get(page, ""), v) for _, _, d, v, page in prints]
        dset = {d for _, _, d, _, _ in prints}
        town = None
        if kind == "address":
            sp = parsed.get(prints[0][0])
            if sp:
                levels = [ka.meet(sp, o) for _, o, _ in offices.get(ka.street_key(sp), ())]
                levels = [lv for lv in levels if lv]
                town = (any(lv in rules.PLACE_LEVELS for lv in levels)) if levels else None
        cat[(kind, k)] = category(kind, k, ctx, len({case_of.get(d, d) for d in dset}),
                                  set().union(*(counsel_bodies[d] for d in dset)),
                                  set().union(*(counsel_people[d] for d in dset)), company_stems, town)
    out["categories"] = dict(collections.Counter(f"{kind}: {c}" for (kind, _), c in cat.items()))

    # the tie: whose value each printing is
    tie_of = {}
    tie_how = collections.Counter()
    by_key = {r["key"]: r for rs in rows_by_doc.values() for r in rs}
    for key, person, d, kind, v, page in ids:
        if person and person in by_key:
            r = by_key[person]
            tie_of[key] = {**r, "how": "person field", "distance": None}
        else:
            r, dist = nearest(texts.get(d, {}).get(page, ""), v, rows_by_doc.get(d, ()))
            if r:
                tie_of[key] = {**r, "how": "nearest name on the page", "distance": dist}
        tie_how[tie_of[key]["how"] if key in tie_of else "untied"] += 1
    out["ties"] = dict(tie_how)
    judged = []                                    # (a, b, judged, private record)

    def rec(kind, ident, d, v, target, target_value, level, tie):
        return (kind, ident, d, v, target, target_value, level, tie["how"] if tie else None, tie["distance"] if tie else None)

    def shared_names(d, keyset):
        return [(r, k) for k, r in names_in[d].items() if k in keyset]

    # ruling 2: shared-contact@1
    for (kind, k), prints in sorted(by_value.items()):
        if kind not in ("email", "phone") or cat[(kind, k)] in OFFICE or len({d for _, _, d, _, _ in prints}) < 2:
            continue
        ties, seen = [], set()
        for key, _, d, v, _ in prints:
            t = tie_of.get(key)
            if t and d not in seen:
                seen.add(d)
                ties.append({**t, "document": d, "ident": key, "value": v})
        for a, b, j in rules.judge_shared_contact(kind, ties):
            ta = next(t for t in ties if t["ref"] == a)
            tb = next(t for t in ties if t["ref"] == b)
            judged.append((a, b, j, rec(kind, ta["ident"], ta["document"], ta["value"], tb["ident"], tb["value"], None, ta)))

    # the addresses each address rule reads
    mine = [(key, d, v, parsed[key]) for key, _, d, kind, v, _ in ids
            if kind == "address" and key in parsed and cat.get(("address", value_key("address", v))) in ADDRESS_CATS]
    office_mine = [(key, d, v, parsed[key]) for key, _, d, kind, v, _ in ids
                   if kind == "address" and key in parsed and cat.get(("address", value_key("address", v))) in OFFICE_CATS]
    out["addresses read"] = {"title, judgment, insolvency": len(mine), "office": len(office_mine)}

    # judgment-address-office@1
    company_names = collections.defaultdict(set)
    refs = sorted({c for v in offices.values() for c, _, _ in v})
    for ent, k in q(f"SELECT entity_ref, org_key FROM {s}.org_names WHERE entity_ref = ANY(%s)", refs):
        company_names[ent].add(k)
    for key, d, v, sp in office_mine:
        cs, texts_at = {}, {}
        for c, o, otext in offices.get(ka.street_key(sp), ()):
            lv = ka.meet(sp, o)
            if lv and (c not in cs or rules.PLACE_LEVELS.count(lv) > rules.PLACE_LEVELS.count(cs[c])):
                cs[c], texts_at[c] = lv, otext
        if not cs:
            continue
        named = [(r["ref"], c) for c in sorted(cs) for (kd, nm), r in names_in[d].items()
                 if kd == "organisation" and nm in company_names[c]]
        tie = tie_of.get(key)
        for a, b, j in rules.judge_address_office({"companies": cs, "named": named, "tie": tie}):
            judged.append((a, b, j, rec("address", key, d, v, b, texts_at.get(b), cs.get(b), tie)))
    log(f"links.identifiers: contacts and offices judged ({time.monotonic() - t0:.0f} s)")

    # judgment-address-judgment@1: every parsed judgment address of another document
    blocks = collections.defaultdict(list)
    for key, _, d, kind, v, _ in ids:        # the other side: any judgment address not a court's, registry's or law firm's
        if key in parsed and cat.get(("address", value_key("address", v))) not in OFFICE:
            blocks[ka.street_key(parsed[key])].append((key, d, v, parsed[key]))
    done = set()
    for key, d, v, sp in mine:
        for k2, d2, v2, sp2 in blocks[ka.street_key(sp)]:
            if d2 == d or (k2, key) in done:
                continue
            done.add((key, k2))
            lv = ka.meet(sp, sp2)
            if not lv:
                continue
            common = {n for n in set(names_in[d]) & set(names_in[d2]) if n[0] == "person"}
            shared = [(names_in[d][n]["ref"], names_in[d2][n]["ref"]) for n in sorted(common)
                      if names_in[d][n]["ref"] != names_in[d2][n]["ref"]]
            ta, tb = tie_of.get(key), tie_of.get(k2)
            for a, b, j in rules.judge_address_judgment({"level": lv, "shared": shared, "tie_a": ta, "tie_b": tb}):
                judged.append((a, b, j, rec("address", key, d, v, k2, v2, lv, ta)))

    # judgment-address-insolvency@1
    if _exists(conn, INSOLVENCY_ADDRESSES):
        estates = collections.defaultdict(list)
        for ref, kind, nk, fl, n in q(f"""
                SELECT r.ref, r.kind, r.name_key, r.fl_key, e.estate_number FROM {s}.rows r
                JOIN (SELECT key, estate_number FROM pub.insolvency_people UNION ALL
                      SELECT key, estate_number FROM pub.insolvency_companies) e ON r.ref = 'insolvency:' || e.key
                WHERE r.register = 'insolvency'"""):
            estates[n].append({"ref": ref, "kind": kind, "name": (fl or nk) if kind == "person" else nk})
        ib = collections.defaultdict(list)
        for n, a in q(f"SELECT estate_number, address FROM {INSOLVENCY_ADDRESSES}"):
            sp = ka.street_parts(a)
            if sp and n in estates:
                ib[ka.street_key(sp)].append((n, sp, a))
        for key, d, v, sp in mine:
            for n, esp, a in ib.get(ka.street_key(sp), ()):
                lv = ka.meet(sp, esp)
                if not lv:
                    continue
                named = [(names_in[d][(e["kind"], e["name"])]["ref"], e["ref"]) for e in estates[n]
                         if (e["kind"], e["name"]) in names_in[d]]
                tie = tie_of.get(key)
                for x, y, j in rules.judge_address_insolvency({"level": lv, "named": named, "tie": tie, "estates": estates[n]}):
                    judged.append((x, y, j, rec("address", key, d, v, str(n), a, lv, tie)))
        out["insolvency addresses"] = sum(len(v) for v in ib.values())
    else:
        out["insolvency addresses"] = "view not made"

    # judgment-address-title@1: the title addresses of the street keys the judgments print, and the titles' owner rows
    linz_views = [v for v in (LINZ_TITLE_ADDRESSES, LINZ_TITLE_POINTS) if _exists(conn, v)]
    if linz_views:
        want_mine = {ka.street_key(sp) for _, _, _, sp in mine}
        tb = collections.defaultdict(list)
        n_read = 0
        with conn.cursor(name="links_identifiers_linz") as cur:
            cur.itersize = 50000
            cur.execute(" UNION ".join(f"SELECT title_no, full_address FROM {v}" for v in linz_views))
            for title, full in cur:
                n_read += 1
                m = re.search(r"\d", full or "")
                if not m:
                    continue
                sp = ka.street_parts(full)
                if sp and ka.street_key(sp) in want_mine:
                    tb[ka.street_key(sp)].append((title, sp, full))
        titles = sorted({t for v in tb.values() for t, _, _ in v})
        owners = collections.defaultdict(list)
        for ref, kind, nk, fl, title in q(f"""
                SELECT r.ref, r.kind, r.name_key, r.fl_key, o.title_no FROM pub.linz_title_owners o
                JOIN {s}.rows r ON r.ref = 'linz:' || o.key WHERE o.title_no = ANY(%s)""", titles):
            owners[title].append({"ref": ref, "kind": kind, "name": (fl or nk) if kind == "person" else nk})
        for key, d, v, sp in mine:
            for title, tsp, full in tb.get(ka.street_key(sp), ()):
                lv = ka.meet(sp, tsp)
                if not lv or not owners[title]:
                    continue
                named = [(names_in[d][(o["kind"], o["name"])]["ref"], o["ref"]) for o in owners[title]
                         if (o["kind"], o["name"]) in names_in[d]]
                tie = tie_of.get(key)
                for x, y, j in rules.judge_address_title({"level": lv, "named": named, "tie": tie, "owners": owners[title]}):
                    judged.append((x, y, j, rec("address", key, d, v, title, full, lv, tie)))
        out["linz title addresses read"] = n_read
        out["linz views"] = linz_views
        out["linz titles at a judgment's street"] = len(titles)
    else:
        out["linz title addresses read"] = "view not made"
    log(f"links.identifiers: addresses judged ({time.monotonic() - t0:.0f} s)")

    # store: the best grade per pair and rule first (ON CONFLICT keeps the first), the private record of every judgment
    judged = [(a, b, j, r) for a, b, j, r in judged if a != b]
    judged.sort(key=lambda x: (x[2]["grade"] != "confirmed", x[2]["rule"], *links.pair(x[0], x[1])))
    from links.build import _insert_judged
    _insert_judged(conn, s, [(a, b, j) for a, b, j, _ in judged])
    with conn.cursor().copy(f"COPY {p}.identifier_links (row_a, row_b, rule, grade, kind, identifier, document, value, target, "
                            f"target_value, level, tie, distance) FROM STDIN") as cp:
        for a, b, j, r in judged:
            cp.write_row((*links.pair(a, b), j["rule"], j["grade"]) + tuple(r))
    for rule in (rules.RULE_ADDRESS_TITLE, rules.RULE_ADDRESS_JUDGMENT, rules.RULE_ADDRESS_INSOLVENCY,
                 rules.RULE_ADDRESS_OFFICE, rules.RULE_SHARED_CONTACT):
        c, n = conn.execute(f"SELECT count(*) FILTER (WHERE grade = 'confirmed'), count(*) FILTER (WHERE grade = 'near') "
                            f"FROM {s}.links WHERE rule = %s", (rule,)).fetchone()
        out[rule] = {"confirmed": int(c), "near": int(n)}
    conn.commit()
    out["seconds"] = round(time.monotonic() - t0, 1)
    log(f"links.identifiers: {json.dumps({k: v for k, v in out.items() if '@' in k})} ({out['seconds']} s)")
    return out


def main(argv=None) -> int:
    import sys
    from support import db
    argv = sys.argv[1:] if argv is None else argv
    s = argv[argv.index("--schema") + 1] if "--schema" in argv else links.SCHEMA
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = 0")
        print(json.dumps(build(conn, s), default=str))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
