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


#: the register: one entry per (profile pattern, field, key) a profile declares
REGISTER: tuple = ()


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
    for p in bad:
        print("FAIL " + p)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
