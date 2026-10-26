"""The lane's figures against the outside world (contract: the lane). The
outside here is the old estate's own record of what it held: its sitting
rows' counts and its derived speeches. And the members every speech names,
against the house lane's `pub.members`. Exit 1 on any of:

  1. a sitting day whose sections, member turns, role-only turns or
     distinct members, counted again from the sections, differ from the
     sitting row's own figures (`old_sections`, `old_speeches`,
     `old_unattributed`, `old_speakers`), or a day with no sitting row
  2. a (sitting, section, member) whose turns counted from the speaker
     lists differ from the old derived speech row's count, or a row on
     either side with no partner (retired old rows are not counted)
  3. the members the speeches name, matched to `pub.members` by name
     (surname and given names, honorifics off; else surname and first
     given name; else surname and a first given name one begins the other),
     below `MEMBER_FLOOR` of the member ids or `TURN_FLOOR` of the member
     turns. Measured on the whole export 26 October 2026: 118 of 128
     members (92.2%), 38,832 of 40,098 turns (96.8%); the ten not matched
     came in mid-term from a party list, which the house lane does not hold
  4. a section whose text does not hash to its SHA-1, or a catch-log line

    python -m registers.hansard.check [--database querynz_v4] [--schema hansard]
"""
import hashlib
import re
import sys
from collections import Counter, defaultdict

from keys import names as N

SCHEMA = "hansard"
MEMBER_FLOOR = 0.90
TURN_FLOOR = 0.95
HONORIFICS = {"rt", "hon", "dr", "sir", "dame", "right", "honourable", "professor", "prof"}
MATCHED = ("full", "first given", "given prefix")


def name_parts(raw: str) -> tuple:
    """('surname', ('given', …)) from 'Surname, Hon Given' or 'SURNAME, Given Middle': lower, diacritics
    folded, honorifics off."""
    fam, _, giv = (raw or "").partition(",")
    if not giv:
        toks = fam.split()
        fam, giv = (toks[-1], " ".join(toks[:-1])) if toks else ("", "")

    def words(s):
        return re.sub(r"[^a-z' -]", "", N.fold_diacritics(s).lower().replace("’", "'")).split()
    return " ".join(words(fam)), tuple(w for w in words(giv) if w not in HONORIFICS)


def match(name: str, members: list) -> str:
    """How a speaker's name finds one person in the members' names: 'full', 'first given', 'given prefix',
    'ambiguous' (more than one person at the closest level) or 'none'."""
    fam, giv = name_parts(name)
    people = {name_parts(m) for m in members}
    cands = {p for p in people if p[0] == fam}
    if not cands:
        return "none"
    tests = (("full", lambda g: g == giv),
             ("first given", lambda g: bool(giv and g) and g[0] == giv[0]),
             ("given prefix", lambda g: bool(giv and g) and (g[0].startswith(giv[0]) or giv[0].startswith(g[0]))))
    for basis, ok in tests:
        hit = {p for p in cands if ok(p[1])}
        if len(hit) == 1:
            return basis
        if len(hit) > 1:
            return "ambiguous"
    return "none"


def members_share(speakers: dict, members: list) -> dict:
    """speakers: {member_id: (roster name, turns)}; members: pub.members names."""
    by = {mid: match(nm, members) for mid, (nm, _) in speakers.items()}
    turns = Counter()
    for mid, (_, n) in speakers.items():
        turns[by[mid] in MATCHED] += n
    return {"members": len(by), "members_matched": sum(1 for b in by.values() if b in MATCHED),
            "turns": sum(turns.values()), "turns_matched": turns[True], "basis": dict(Counter(by.values())),
            "not_matched": sorted(speakers[m][0] for m, b in by.items() if b not in MATCHED)}


def failed(f: dict) -> list:
    out = []
    for day, ours, old in f["sittings"]:
        if old is None:
            out.append(f"sitting {day}: sections held and no sitting row")
        elif ours != old:
            out.append(f"sitting {day}: sections, member turns, role-only turns, members {ours} against the "
                       f"sitting row's own {old}")
    for k, ours, old in f["speeches"]:
        out.append(f"speech {k}: {ours} turns counted from the speaker lists against the old derived row's {old}")
    for k in f["bad_hash"]:
        out.append(f"section {k}: the text does not hash to its SHA-1")
    for item, stage, why in f["set_aside"]:
        out.append(f"catch log: {item} ({stage}): {why}")
    m = f.get("members")
    if m is None:
        out.append("pub.members is not in this database: the members the speeches name were not matched")
    elif m["members"]:
        if m["members_matched"] / m["members"] < MEMBER_FLOOR:
            out.append(f"members matched to pub.members: {m['members_matched']} of {m['members']}, below "
                       f"{MEMBER_FLOOR:.0%}")
        if m["turns"] and m["turns_matched"] / m["turns"] < TURN_FLOOR:
            out.append(f"member turns matched to pub.members: {m['turns_matched']} of {m['turns']}, below {TURN_FLOOR:.0%}")
    return out


def figures(conn, schema: str = SCHEMA, shared: bool = False) -> dict:
    """The lane's own side of every figure; `members` is filled by the caller from pub.members."""
    from registers.hansard.load import table
    T = lambda t: table(schema, t, shared)  # noqa: E731
    sittings = []
    for day, ours, old in conn.execute(
            f"SELECT coalesce(s.key, d.day), ARRAY[s.sections, s.attributed, s.unattributed, s.speakers], "
            f"       CASE WHEN s.key IS NULL THEN NULL "
            f"            ELSE ARRAY[s.old_sections, s.old_speeches, s.old_unattributed, s.old_speakers] END "
            f"FROM {T('sittings')} s FULL JOIN (SELECT DISTINCT sitting_on::text AS day FROM {T('sections')}) d "
            f"ON d.day = s.key ORDER BY 1"):
        sittings.append((day, list(ours) if old is not None else None, list(old) if old is not None else None))
    ours = defaultdict(int)
    for day, idx, mid, n in conn.execute(f"SELECT sitting_on::text, section_index, member_id, count(*) FROM {T('turns')} "
                                         f"WHERE member_id IS NOT NULL GROUP BY 1, 2, 3"):
        ours[(day, idx, mid)] = n
    old = {(d, i, m): n for d, i, m, n in conn.execute(
        f"SELECT sitting_on::text, section_index, member_id, speech_count FROM {T('old_speeches')} "
        f"WHERE retired_at IS NULL")}
    speeches = [("/".join(map(str, k)), ours.get(k, 0), old.get(k, 0)) for k in sorted(set(ours) | set(old))
                if ours.get(k, 0) != old.get(k, 0)]
    bad = [k for k, text, h in conn.execute(f"SELECT key, text, text_sha1 FROM {T('sections')}")
           if hashlib.sha1(text.encode("utf-8")).hexdigest() != h]
    speakers = {mid: (nm, n) for mid, nm, n in conn.execute(
        f"SELECT member_id, min(roster_name), count(*) FROM {T('turns')} WHERE member_id IS NOT NULL GROUP BY 1")}
    return {"sittings": sittings, "speeches": speeches, "bad_hash": bad,
            "set_aside": conn.execute(f"SELECT item, stage, reason FROM {T('set_aside')}").fetchall(),
            "speakers": speakers, "members": None}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else SCHEMA
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    from registers.hansard.load import table
    with db.connect(db.READ_KEY if database == "querynz_v4" else db.OWNER_KEY, database) as conn:
        conn.execute("SET statement_timeout = '60s'")
        # the sample's shared schema names the lane's tables `hansard_…`; a lane or staging schema does not
        shared = conn.execute("SELECT to_regclass(%s) IS NOT NULL", (table(schema, "sittings", True),)).fetchone()[0]
        f = figures(conn, schema, shared)
    with db.connect(db.READ_KEY, "querynz_v4") as conn:       # the house lane's members, always from the published estate
        conn.execute("SET statement_timeout = '60s'")
        if conn.execute("SELECT to_regclass('pub.members') IS NOT NULL").fetchone()[0]:
            members = [n for (n,) in conn.execute("SELECT name FROM pub.members")]
            f["members"] = members_share(f["speakers"], members)
    problems = failed(f)
    for p in problems[:40]:
        print(f"{SCHEMA}: RED: {p}")
    if len(problems) > 40:
        print(f"{SCHEMA}: … and {len(problems) - 40} more")
    agree = sum(1 for d, o, p in f["sittings"] if o is not None and o == p)
    m = f["members"]
    print(f"{SCHEMA}: {agree} of {len(f['sittings'])} sitting days agree with their own counts; "
          f"{len(f['speeches'])} speech rows differ; "
          + (f"members matched {m['members_matched']} of {m['members']}, turns {m['turns_matched']} of {m['turns']}"
             f" ({', '.join(f'{k} {v}' for k, v in sorted(m['basis'].items()))}); not matched: "
             f"{', '.join(m['not_matched']) or 'none'}" if m else "pub.members not read"))
    print(f"{SCHEMA}: " + ("0 problems" if not problems else f"{len(problems)} problems"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
