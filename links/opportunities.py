"""The linking opportunities the document profiles declare, and what the links lane does with each (Arthur, 3 November
2026: "the links lane is aware of the linking opportunities and has rules").

Every extract item of every current profile carries `links`: what the field could join on (`key`: a name, an NZBN, a
company number, an email, a phone, an address, a citation …), what it could join (`to`) and the links rule that joins
it today, or null. This register says, for each (profile, field, key) a profile declares, what the lane does with it:

  rule           a rule of links.rules or links.build joins it today (`rules` names each, as the build makes them);
  sighting       the deterministic name sightings cover it (links.sightings scans the lane's documents for the name
                 forms of pub.names), and no rule joins the field's own rows;
  measure owed   no rule yet: the links method is to measure the gap (counts and twenty pairs), Arthur rules, and only
                 then a versioned rule is built (ruling 106). `decision` names what Arthur is asked.

An entry's `profile` is a shell pattern over profile slugs ("courts-*"). The test (links/tests/test_opportunities.py)
fails when a profile declares an opportunity no entry covers, an entry covers none, an entry names a rule id the lane
does not hold (or holds only as retired), a declared rule is not among its entry's rules, or a sighting entry's lane is
not one the sightings scan.

    listing(profiles=None)    every declared opportunity with its status, rules and note
    problems(profiles=None)   [str]
    python -m links.opportunities          the listing, by status
    python -m links.opportunities --views  and every published view that names a person or a body, read or excluded

A second register, `EXCLUDED`, holds every published view that names a person or a body and that the rows do not read,
with the reason (`view_problems`, held at the links check).
"""
import fnmatch
import sys
from dataclasses import dataclass

import support.profiles as pr

STATUSES = ("rule", "sighting", "measure owed")


@dataclass(frozen=True)
class Entry:
    profile: str            # a shell pattern over slugs
    field: str
    key: str
    status: str
    rules: tuple = ()       # the rule ids that join it today (status rule)
    note: str = ""          # what was measured, and where
    decision: str = ""      # measure owed: the one decision Arthur is asked

    @property
    def lane(self) -> str:
        return self.profile.split("-", 1)[0]


#: the rules that join a court name row today (pub.court_judgment_parties and pub.court_people, links.rows), measured on
#: pub.links 3 November 2026: links/measurements.md
COURT_NAME_RULES = ("full-name@1", "name-only@1", "organisation-name@1", "organisation-sole-company@3",
                    "organisation-one-live-company@3")
_PRIVATE = ("the details are private (courts_private.identifiers) and the lane reads pub.* only: whether links may read "
            "them, and by which rule, is Arthur's, after the twenty pairs")
#: the register. Courts (3 November 2026): the rules measured on pub.links, the measurements in links/measurements.md
REGISTER: tuple = (
    Entry("courts-*", "parties", "name", "rule", COURT_NAME_RULES,
          "pub.court_judgment_parties rows: confirmed by full-name@1 and the organisation rules @3, near by name-only@1 "
          "and organisation-name@1"),
    Entry("courts-*", "people", "name", "rule", COURT_NAME_RULES,
          "pub.court_people rows: a text reader's names are their own tier (links.rows.MODEL_VIEWS), near only, never a "
          "name form for the sightings"),
    Entry("courts-*", "judges", "name", "sighting", (), "a judge's name is in the document's text, which the name sightings scan"),
    Entry("courts-*", "for_party", "name", "sighting", (), "counsel's party is named in the text the sightings scan"),
    Entry("courts-case-page", "case_name", "name", "sighting", (), "the case page's title is in the text the sightings scan"),
    # ruling 4 (Arthur, 3 November 2026): yes, a case of its own table (links.cases, pub.court_case_documents), never an entity
    Entry("courts-*", "citation", "citation", "rule", ("case-documents@1",),
          "ruling 4: the documents of one citation, case number or case page are one case (links/measurements.md §17)"),
    Entry("courts-*", "case_numbers", "case_number", "rule", ("case-documents@1",), "ruling 4: as the citation"),
    # ruling 1 (Arthur, 3 November 2026): yes, read from the narrow pub.court_company_numbers (document, kind, value, page)
    Entry("courts-*", "identifiers", "nzbn", "rule", ("judgment-number@1",),
          "ruling 1: the party of the document whose name is the body's, confirmed to the body the NZBN names; one body party "
          "under another name near (links/measurements.md §16)"),
    Entry("courts-*", "identifiers", "company_number", "rule", ("judgment-number@1",),
          "ruling 1: as the NZBN, by the companies register's number"),
    Entry("courts-*", "identifiers", "email", "measure owed", (), "measured: links/measurements.md",
          "whether one email printed in two documents joins their names (near or confirming); " + _PRIVATE),
    Entry("courts-*", "identifiers", "phone", "measure owed", (), "measured: links/measurements.md",
          "whether one phone printed in two documents joins their names; " + _PRIVATE),
    Entry("courts-*", "identifiers", "address", "measure owed", (), "measured: links/measurements.md",
          "whether a street address a judgment prints is matched to a company's registered office (never a home "
          "address shown, hard limit 15); " + _PRIVATE),
    Entry("courts-*", "identifiers", "po_box", "measure owed", (), "measured: links/measurements.md",
          "whether a PO Box a judgment prints is matched to a company's address; " + _PRIVATE),
    # LINZ (3 November 2026): the lane's extract list declares two; no links rule reads a LINZ view yet
    Entry("linz-*", "name", "name", "measure owed", (),
          "pub.linz_title_owners (an owner's name as printed, corporate or individual): no links rule reads it",
          "whether a title's corporate owner is joined to the company of that name, and an individual owner to a person "
          "by name (near at most, as a name alone is)"),
    Entry("linz-*", "full_address", "address", "measure owed", (),
          "linz_private.title_addresses (each title's street address, the property spine): private, and the lane reads "
          "pub.* only",
          "whether a title's street address is matched to a company's registered office (never shown, hard limit 15)"),
)


# --- every published view that names a person or a body (3 November 2026) ------------------------------------------
# Arthur: "the views the links never read, yes"; the coordinator's query found about 45 such views rows.py did not read.
# A published view with a name, NZBN, company number or charity number column (`VIEW_COLUMN`, a text column) is either read
# by the lane (`views_read`: a pub view the rows, the numbers, the bodies or a build step reads, or one the lane publishes)
# or listed here with the reason it is not; anything else is red at the links check (links.check.check_views), so a view
# like these is never missed again.
import re as _re

VIEW_COLUMN = _re.compile(r"(^|_)(names?|surname|nzbn|company_number|charity_number)$")
TEXT_TYPES = ("text", "text[]", "character varying", "jsonb")
EXCLUDED = {
    "company_changes": "a company's own change log (before and after): the company is its pub.companies row, read as a body",
    "company_lookups": "the Companies Office's lookup of a company by its NZBN: the same body as its pub.companies row",
    "company_states": "a company's state in one monthly file: the same body as its pub.companies row",
    "society_states": "a society's state in one monthly file: the same body as its pub.societies row",
    "court_cases": "a case page's title: the name sightings scan it (courts-case-page case_name) and the case grouping "
                   "gathers its documents (ruling 4, links.cases)",
    "court_judgments": "the court's name, not a party: the parties are pub.court_judgment_parties",
    "elections": "an election's name",
    "grants": "each grant's recipient is its pub.grant_recipients row (recipient_key), which the rows read with its number",
    "iwi_directory_relations": "the related entity is its own pub.iwi_directory_entities row (to_key), which the rows read",
    "iwi_directory_settlements": "a Treaty settlement's name, not a party",
    "linz_place_names": "a place's name",
    "minister_diary_entries": "the release's file name; an entry's attendees are pub.minister_diary_attendees, which the rows read",
    "parties": "a registered party: the party lane's own entity (`parties:<key>`), which donor and board rows name as theirs",
    "party_events": "a registered party's change of name: the party lane's own entity",
    "party_labels": "a party's label as a return prints it: the party lane's own entity",
    "party_names": "a registered party's names: the party lane's own entity",
    "sanctions_lists": "a sanctions list's name (its listings, pub.sanctions_listings, are read)",
    # owed, each named in the report of 3 November 2026
    "parliament_api_items": "OWED: the member a bill or paper names (`member_name`, 783 rows) is a fifth member view for "
                            "member-on-the-day@1, whose four views ruling 116 fixed: Arthur's word first",
    "linz_title_owners": "OWED: 5.7 million owners do not fit the links build's 7,200 s with the rest (measured 3 November "
                         "2026, links/measurements.md §18): a later tranche, the build split by register first",
    "gazette_company_notices": "OWED: 1.55 million company notices (removals, mostly) with the linz tranche, the same budget: "
                               "the organisation rules hold every matched row in memory",
}


def views_read() -> set:
    """Every pub view the lane reads or publishes: named in a rows source, a number source, the bodies, the offices or the
    company names, any build step, or the lane's own publish.sql."""
    import inspect
    import links
    from links import build, rows
    text = "\n".join(sql for _, _, sql in rows.SOURCES) + "\n".join(sql for _, _, sql in rows.NUMBERS)
    text += rows.BODY_SQL + rows.ADDRESS_SQL + rows.COMPANY_SQL + inspect.getsource(build) + links.publish_sql()
    return set(_re.findall(r"\bpub\.(\w+)", text))


def view_problems(catalog: dict, read: set = None, excluded: dict = None) -> list:
    """`catalog`: {view: [(column, type)]} of the published views. A view with a `VIEW_COLUMN` text column that the lane
    neither reads nor excludes with a reason is a problem; so is a view both read and excluded, an exclusion with no
    reason, and an exclusion of a view no longer published or no longer naming anybody."""
    read = views_read() if read is None else read
    excluded = EXCLUDED if excluded is None else excluded
    out = []
    naming = {v for v, cols in catalog.items() if any(VIEW_COLUMN.search(c) and t in TEXT_TYPES for c, t in cols)}
    for v in sorted(naming - read - set(excluded)):
        cols = [c for c, t in catalog[v] if VIEW_COLUMN.search(c) and t in TEXT_TYPES]
        out.append(f"pub.{v} names a person or a body ({', '.join(cols)}) and links/rows.py neither reads it nor lists it "
                   f"in links.opportunities.EXCLUDED with a reason")
    for v, why in sorted(excluded.items()):
        if v in read:
            out.append(f"pub.{v} is read and also excluded")
        if not (why or "").strip():
            out.append(f"pub.{v} is excluded with no reason")
        if catalog and v not in naming:
            out.append(f"pub.{v} is excluded, but no published view of that name carries a name or number column")
    return out


def catalog(conn) -> dict:
    """{view: [(column, type)]} of every view in `pub`, from the catalog (pg_attribute: a view's columns as the owner sees
    them, whatever the login's grants)."""
    out: dict = {}
    for v, c, t in conn.execute("""SELECT cl.relname, a.attname, format_type(a.atttypid, a.atttypmod)
                                   FROM pg_class cl JOIN pg_namespace n ON n.oid = cl.relnamespace
                                   JOIN pg_attribute a ON a.attrelid = cl.oid AND a.attnum > 0 AND NOT a.attisdropped
                                   WHERE n.nspname = 'pub' AND cl.relkind IN ('v', 'm', 'r') ORDER BY 1, a.attnum""").fetchall():
        out.setdefault(v, []).append((c, t))
    return out


def rule_ids() -> set:
    """Every rule id the lane builds today: the string constants of links.rules and links.build that are rule ids,
    the retired versions apart."""
    from links import build, rules
    ids = set()
    for mod in (rules, build):
        ids |= {v for k, v in vars(mod).items() if k.isupper() and isinstance(v, str) and pr.RULE_ID.match(v)}
    return ids - set(getattr(rules, "RETIRED", ()))


def declared(profiles: dict = None) -> list:
    """[(profile, field, key, to, rule)] for every `links` entry of every current profile's newest extract items."""
    profiles = pr.current() if profiles is None else profiles
    out = []
    for slug, prof in sorted(profiles.items()):
        for f, it in sorted(pr.latest(prof.get("extract")).items()):
            for ln in it.get("links") or ():
                out.append((slug, f, ln["key"], ln["to"], ln["rule"]))
    return out


def entry_for(slug: str, field: str, key: str, register: tuple = None):
    hits = [e for e in (REGISTER if register is None else register)
            if fnmatch.fnmatchcase(slug, e.profile) and e.field == field and e.key == key]
    return hits[0] if len(hits) == 1 else (None if not hits else hits)


def listing(profiles: dict = None, register: tuple = None) -> list:
    out = []
    for slug, f, key, to, rule in declared(profiles):
        e = entry_for(slug, f, key, register)
        e = e if isinstance(e, Entry) else None
        out.append({"profile": slug, "field": f, "key": key, "to": to, "rule": rule,
                    "status": e.status if e else None, "rules": e.rules if e else (), "note": e.note if e else "",
                    "decision": e.decision if e else ""})
    return out


def problems(profiles: dict = None, register: tuple = None, known: set = None) -> list:
    register = REGISTER if register is None else register
    known = rule_ids() if known is None else known
    from links.sightings import LANES
    out, used = [], set()
    for slug, f, key, to, rule in declared(profiles):
        e = entry_for(slug, f, key, register)
        if e is None:
            out.append(f"{slug}: {f} declares a {key} opportunity ({to}) the links register lacks")
            continue
        if isinstance(e, list):
            out.append(f"{slug}: {f} {key} is covered by {len(e)} register entries; one says what the lane does")
            continue
        used.add(e)
        if rule is not None and rule not in e.rules:
            out.append(f"{slug}: {f} {key} names the rule {rule}, which its register entry does not")
        if e.status == "rule" and rule is None:
            out.append(f"{slug}: {f} {key} is joined by a rule ({', '.join(e.rules)}); the profile names none")
        if e.status != "rule" and rule is not None:
            out.append(f"{slug}: {f} {key} names the rule {rule}; the register says {e.status}")
    for e in register:
        if e.status not in STATUSES:
            out.append(f"{e.profile} {e.field} {e.key}: status {e.status!r} is none of {STATUSES}")
        if (e.status == "rule") != bool(e.rules):
            out.append(f"{e.profile} {e.field} {e.key}: a `rule` entry names its rules, and only a `rule` entry does")
        for r in e.rules:
            if r not in known:
                out.append(f"{e.profile} {e.field} {e.key}: the rule {r} is not one the links lane builds")
        if e.status == "sighting" and e.lane not in {ln.split("-", 1)[0] for ln in LANES}:
            out.append(f"{e.profile} {e.field} {e.key}: a sighting, but the sightings do not scan the {e.lane} lane")
        if e.status == "measure owed" and not e.decision:
            out.append(f"{e.profile} {e.field} {e.key}: measure owed, and no decision named for Arthur")
        if e not in used:
            out.append(f"{e.profile} {e.field} {e.key}: a register entry no profile declares")
    return out


def main(argv=None) -> int:
    rows = listing()
    for status in STATUSES:
        mine = [r for r in rows if r["status"] == status]
        print(f"{status}: {len(mine)}")
        seen = set()
        for r in mine:
            k = (r["field"], r["key"])
            if k not in seen:
                seen.add(k)
                n = len({x["profile"] for x in mine if (x["field"], x["key"]) == k})
                print(f"  {r['field']} by {r['key']} ({n} profiles){': ' + ', '.join(r['rules']) if r['rules'] else ''}")
    bad = problems()
    if "--views" in (argv or sys.argv[1:]):
        from support import db
        with db.connect(db.READ_KEY, "querynz_v4") as conn:
            bad += view_problems(catalog(conn))
    for p in bad:
        print("FAIL " + p)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
