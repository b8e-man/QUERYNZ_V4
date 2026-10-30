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

And the MCP's two corpora (hansard-2) against the MCP's own `corpora`
counts and its `measure` (`mcp_failed`):

  5. taken: each corpus's cursor at least `TAKEN_FLOOR` of the MCP's count,
     and every record taken an arrival or a catch line; every document a
     row read, an older version or set aside; no catch line, set-aside line
     or field the lane has no column for
  6. measured: the MCP's `n_docs` for the debates at most the records taken
     plus `TAKEN_FLOOR`'s slack; its `corpus_words` against the words of the
     days' texts held, within 1% (27 October: 94,602,760 both); every day's
     served `word_count` equal to its text's
  7. agreement, on the days both sources hold: of the old sections whose
     subject is not the old page's "(continued on …)" note, the share found
     in the same day's PDF text at least `SUBJECT_FLOOR`, and no day below
     `DAY_FLOOR`. Measured on the whole of both 27 October: 3,691 of 3,885
     (95.0%), the worst day 57.1%. The 194 not found are not layout (six are
     the subject's words broken by it): 41 are in a neighbouring day's PDF,
     and 119 of the other 153 are on eight sittings under urgency that ran
     past midnight, where the old page carried the whole sitting and the
     MCP holds the PDF of its first calendar day only (2024-12-10 continued
     to 13 December; 2025-05-06, 2025-11-18, 2025-12-09 likewise). The
     seven days under 75% are all such sittings. 90% leaves room for
     about as many such sittings again and fails if a PDF of another day,
     or a provider's reading that drops pages, joined the record; 50% for one day is below the worst
     urgency sitting (57%) and above what a PDF of the wrong day gives
     (measured: each day given the next held day's PDF finds 37.6%
     overall, and 85 of 136 days fall below 50%)
  8. counted, never failed: the days only the MCP holds (1,725: 1,724
     before the old estate's first day, 20 November 2024, and 2026-07-30),
     the old days the MCP lacks (0), and the sittings whose page the index
     names (0: the index corpus holds www.parliament.nz pages, never a
     hansard.parliament.nz transcript)

And the split and the text reader (hansard-3, profile `hansard-day`;
`split_failed`):

  9. every day the MCP holds is split (a `day_sections` row set and the
     counts beside the day) or set aside at stage `read` with its reason;
     every `day_turns` row's section exists; the counts beside the day equal
     the rows (the split's turns on the 137 old days are held for the
     comparison and not published: pub.hansard_speeches takes the old
     estate's for those days)
 10. the text reader: names read, days read, days waiting, days set aside
     at read, pieces unusable, all counted; a reading stored in the reader
     store for a day under another version of `hansard-day` than the load
     expects fails (the load replays the expected version only, so the
     document would wait for ever while a reading sits there); a `people`
     row without its day fails
 11. counted, never failed: on the days both sources hold, the split's
     sections and member turns against the sitting row's own counts
     (measured 31 October 2026 on 137 days: the split finds more member
     turns on 129, 53,690 against the old lists' 40,098, because the old
     speaker lists skip an oral question's question line and most speakers
     of a bill debate (2 of 20 on the Citizenship (Western Samoa) third
     reading, 20 November 2024); fewer on the 8 urgency sittings whose later
     calendar days the MCP lacks)

Run bare it answers about the live tables under the session reader (the
day texts are private: the load writes the subject counts beside the days,
and `--owner` recounts them from the texts and holds the two equal).

    python -m registers.hansard.check [--database querynz_v4] [--schema hansard] [--mcp-schema mcpsource] [--owner]
                                      [--mcp-database querynz_v4]   a scratch proof in the sample database reads the live pull's tables
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
TAKEN_FLOOR = 0.99
WORDS_TOLERANCE = 0.01
SUBJECT_FLOOR = 0.90
DAY_FLOOR = 0.50
CORPORA = ("parliament-hansard-index", "parliament-hansard-debates")


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


def mcp_held(conn, schema: str = SCHEMA, mcp_schema: str = "mcpsource", shared: bool = False) -> dict:
    """The lane's and the pull's side of 5 to 8, under the reader (no private table)."""
    from registers.hansard.load import table
    T = lambda t: table(schema, t, shared)  # noqa: E731
    q = lambda sql, *a: conn.execute(sql, a).fetchone()[0]  # noqa: E731
    h = {}
    for c in CORPORA:
        h[c] = {
            "cursor": q(f"SELECT coalesce(max(cursor), 0) FROM {mcp_schema}.cursors WHERE corpus = %s", c),
            "arrivals": q(f"SELECT count(DISTINCT seq) FROM {mcp_schema}.arrivals WHERE corpus = %s", c),
            "documents": q(f"SELECT count(DISTINCT sha256) FROM {mcp_schema}.arrivals WHERE corpus = %s", c),
            "caught": q(f"SELECT count(*) FROM {mcp_schema}.catch WHERE corpus = %s AND resolved_at IS NULL", c),
            "files": q(f"SELECT count(*) FROM {T('files')} WHERE kind = %s", c),
            "older versions": q(f"SELECT count(*) FROM {T('files')} WHERE kind = %s AND status = 'older version'", c),
            "files set aside": q(f"SELECT count(*) FROM {T('files')} WHERE kind = %s AND status = 'set aside'", c)}
    h["parliament-hansard-index"]["rows"] = q(f"SELECT count(*) FROM {T('index_pages')}")
    h["parliament-hansard-debates"]["rows"] = q(f"SELECT count(*) FROM {T('days')}")
    h["fields unread"] = q(f"SELECT (SELECT count(*) FROM {T('days')} WHERE cardinality(fields_unread) > 0) + "
                           f"(SELECT count(*) FROM {T('index_pages')} WHERE cardinality(fields_unread) > 0)")
    h["words"] = q(f"SELECT coalesce(sum(text_words), 0) FROM {T('days')}")
    h["word counts differ"] = q(f"SELECT count(*) FROM {T('days')} WHERE word_count IS DISTINCT FROM text_words")
    h["subjects"], h["in text"] = conn.execute(f"SELECT coalesce(sum(old_subjects), 0), coalesce(sum(subjects_in_text), 0) "
                                               f"FROM {T('days')} WHERE old_sections IS NOT NULL").fetchone()
    h["low days"] = conn.execute(f"SELECT key, subjects_in_text, old_subjects FROM {T('days')} WHERE old_subjects > 0 "
                                 f"AND subjects_in_text < %s * old_subjects ORDER BY key", (DAY_FLOOR,)).fetchall()
    h["worst day"] = conn.execute(f"SELECT key, subjects_in_text, old_subjects FROM {T('days')} WHERE old_subjects > 0 "
                                  f"ORDER BY subjects_in_text::numeric / old_subjects, key LIMIT 1").fetchone()
    h["found"] = dict(conn.execute(f"SELECT found, count(*) FROM {T('day_subjects')} GROUP BY 1").fetchall())
    h["both"] = q(f"SELECT count(*) FROM {T('days')} WHERE old_sections IS NOT NULL")
    h["mcp only"] = q(f"SELECT count(*) FROM {T('days')} WHERE old_sections IS NULL")
    h["mcp only since the old first day"] = q(f"SELECT count(*) FROM {T('days')} WHERE old_sections IS NULL "
                                              f"AND sitting_on >= (SELECT min(sitting_on) FROM {T('sittings')})")
    h["old only"] = q(f"SELECT count(*) FROM {T('sittings')} s WHERE NOT EXISTS "
                      f"(SELECT 1 FROM {T('days')} d WHERE d.key = s.key)")
    h["sittings the index names"] = q(f"SELECT count(*) FROM {T('sittings')} s WHERE EXISTS "
                                      f"(SELECT 1 FROM {T('index_pages')} p WHERE p.url = s.url)")
    return h


def split_held(conn, schema: str = SCHEMA, shared: bool = False, store_root: str = None) -> dict:
    """The lane's side of 9 to 11 (the reader login; the reader store on disk for the version check)."""
    import os
    from support import reader as rd
    from registers.hansard import model_read
    from registers.hansard.load import table
    T = lambda t: table(schema, t, shared)  # noqa: E731
    q = lambda sql, *a: conn.execute(sql, a).fetchone()  # noqa: E731
    h = {}
    h["days"], h["days split"], h["days set aside at read"], h["days read"], h["days waiting"] = q(
        f"SELECT count(*), count(*) FILTER (WHERE split_rule IS NOT NULL), count(*) FILTER (WHERE left(reading, 9) = 'set aside'), "
        f"count(*) FILTER (WHERE reading = 'read'), count(*) FILTER (WHERE reading = 'waiting: text reader') FROM {T('days')}")
    h["days unaccounted"] = q(f"SELECT count(*) FROM {T('days')} WHERE split_rule IS NULL AND left(reading, 9) <> 'set aside'")[0]
    h["sections"], h["turns"] = q(f"SELECT count(*), coalesce(sum(turns), 0) FROM {T('day_sections')}")
    h["turn rows"], h["turns without a section"] = q(
        f"SELECT count(*), count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM {T('day_sections')} s WHERE s.key = t.section)) "
        f"FROM {T('day_turns')} t")
    h["counts off"] = q(f"SELECT count(*) FROM {T('days')} d WHERE d.split_rule IS NOT NULL AND (d.sections, d.turns) IS DISTINCT FROM "
                        f"((SELECT count(*) FROM {T('day_sections')} s WHERE s.sitting_on = d.sitting_on), "
                        f" (SELECT count(*) FROM {T('day_turns')} t WHERE t.sitting_on = d.sitting_on))")[0]
    h["split turns on old days"] = q(f"SELECT count(*) FROM {T('day_turns')} t WHERE EXISTS (SELECT 1 FROM {T('sittings')} o "
                                     f"WHERE o.key = t.sitting_on::text)")[0]      # held for the comparison, not published
    h["names"], h["people without a day"] = q(
        f"SELECT count(*), count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM {T('days')} d WHERE d.key = p.day)) FROM {T('people')} p")
    h["names by kind"] = dict(conn.execute(f"SELECT kind, count(*) FROM {T('people')} GROUP BY 1 ORDER BY 2 DESC").fetchall())
    h["pieces"], h["pieces unusable"], h["pieces truncated"] = q(
        f"SELECT count(*), count(*) FILTER (WHERE unusable IS NOT NULL), count(*) FILTER (WHERE truncated) FROM {T('readings')}")
    h["version expected"] = model_read.profile_version()
    h["other versions"] = []
    root = store_root or rd.STORE
    for sha, day in conn.execute(f"SELECT document, key FROM {T('days')} WHERE reading <> 'read'").fetchall():
        folder = os.path.join(root, sha[:2], sha)
        try:
            names = os.listdir(folder)
        except OSError:
            continue
        for n in names:
            if n.startswith("p1__hansard-day@") and n.split("@")[1].split("__")[0] != str(h["version expected"]):
                h["other versions"].append((day, n.split("__")[1]))
    both = conn.execute(f"SELECT d.key, d.sections, o.old_sections, d.attributed, o.old_speeches FROM {T('days')} d "
                        f"JOIN {T('sittings')} o ON o.key = d.key WHERE d.split_rule IS NOT NULL ORDER BY 1").fetchall()
    h["both"] = {"days": len(both), "sections equal": sum(1 for r in both if r[1] == r[2]),
                 "member turns more": sum(1 for r in both if r[3] > r[4]), "member turns fewer": sum(1 for r in both if r[3] < r[4]),
                 "member turns equal": sum(1 for r in both if r[3] == r[4]),
                 "split member turns": sum(r[3] or 0 for r in both), "old member turns": sum(r[4] or 0 for r in both)}
    return h


def split_failed(h: dict) -> list:
    out = []
    if h["days unaccounted"]:
        out.append(f"{h['days unaccounted']} days neither split nor set aside at read")
    if h["turns without a section"]:
        out.append(f"{h['turns without a section']} day_turns rows whose section is not held")
    if h["counts off"]:
        out.append(f"{h['counts off']} days whose section or turn count differs from the rows")
    if h["people without a day"]:
        out.append(f"{h['people without a day']} people rows without their day")
    for day, v in h["other versions"][:10]:
        out.append(f"day {day}: a reading stored under {v}, the load expects hansard-day@{h['version expected']}")
    if len(h["other versions"]) > 10:
        out.append(f"… and {len(h['other versions']) - 10} more readings under another profile version")
    return out


def owner_recount(conn, schema: str = SCHEMA, shared: bool = False) -> int:
    """The subjects found in their own day's text, counted again from the private texts (the owner login only)."""
    from registers.hansard import read_mcp
    from registers.hansard.load import private_of, table
    n = 0
    texts = conn.execute(f"SELECT t.key, t.text FROM {table(private_of(schema), 'day_texts', shared)} t "
                         f"JOIN {table(schema, 'days', shared)} d ON d.key = t.key WHERE d.old_sections IS NOT NULL")
    for day, text in texts.fetchall():
        own = read_mcp.fold(text)
        for (subject,) in conn.execute(f"SELECT subject FROM {table(schema, 'sections', shared)} "
                                       f"WHERE sitting_on = %s::date", (day,)).fetchall():
            n += read_mcp.where(subject, own, [])[0] == "own day"
    return n


def mcp_outside(client) -> dict:
    """The MCP's own counts: `corpora`'s record count and `measure`'s n_docs and corpus_words, per corpus."""
    listing = {c["name"]: c for c in client.call_retrying("corpora", {})["corpora"]}
    cells = {x["corpus"]: x for x in client.call_retrying("measure", {"keywords": ["minister"],
                                                                      "corpora_filter": list(CORPORA)})["cells"]}
    return {c: {"records": listing[c].get("ingest_cursor", listing[c].get("records")), "n_docs": cells[c]["n_docs"],
                "corpus_words": cells[c]["corpus_words"]} for c in CORPORA}


def mcp_failed(h: dict, o: dict, recount: int = None) -> list:
    """5 to 7 as plain lines; 8 is printed, never failed."""
    out = []
    for c in CORPORA:
        x, y = h[c], o[c]
        if x["cursor"] < TAKEN_FLOOR * y["records"]:
            out.append(f"{c}: taken {x['cursor']} of the MCP's {y['records']} records (floor {TAKEN_FLOOR:.0%})")
        if x["arrivals"] + x["caught"] != x["cursor"]:
            out.append(f"{c}: {x['arrivals']} arrivals and {x['caught']} catch lines for a cursor of {x['cursor']}")
        if x["files"] != x["documents"] or x["rows"] + x["older versions"] + x["files set aside"] != x["documents"]:
            out.append(f"{c}: {x['documents']} documents but {x['rows']} read, {x['older versions']} older versions, "
                       f"{x['files set aside']} set aside")
        if x["caught"] or x["files set aside"]:
            out.append(f"{c}: {x['caught']} catch lines, {x['files set aside']} documents set aside")
        if y["n_docs"] > x["cursor"] and x["cursor"] < TAKEN_FLOOR * y["n_docs"]:
            out.append(f"{c}: the MCP measures {y['n_docs']} documents, the pull holds {x['cursor']}")
    y = o["parliament-hansard-debates"]
    if y["corpus_words"] and abs(h["words"] - y["corpus_words"]) > WORDS_TOLERANCE * y["corpus_words"] \
            and h["parliament-hansard-debates"]["cursor"] >= y["n_docs"]:
        out.append(f"debates: the MCP counts {y['corpus_words']} words, the days' texts hold {h['words']}")
    if h["fields unread"]:
        out.append(f"{h['fields unread']} records with a field the lane has no column for")
    if h["word counts differ"]:
        out.append(f"{h['word counts differ']} days whose served word_count is not their text's")
    if h["subjects"] and h["in text"] < SUBJECT_FLOOR * h["subjects"]:
        out.append(f"old subjects found in the day's PDF text: {h['in text']} of {h['subjects']}, below {SUBJECT_FLOOR:.0%}")
    for day, n, of in h["low days"]:
        out.append(f"day {day}: {n} of {of} old subjects in its PDF text, below {DAY_FLOOR:.0%}")
    if recount is not None and recount != h["in text"]:
        out.append(f"the subjects found, counted again from the texts: {recount}, the days say {h['in text']}")
    return out


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else SCHEMA
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    mcp_schema = argv[argv.index("--mcp-schema") + 1] if "--mcp-schema" in argv else "mcpsource"
    mcp_database = argv[argv.index("--mcp-database") + 1] if "--mcp-database" in argv else database
    owner = "--owner" in argv or database != "querynz_v4"
    from support import db
    from support import mcpsource as M
    from registers.hansard.load import table
    with db.connect(db.OWNER_KEY if owner else db.READ_KEY, database) as conn:
        conn.execute("SET statement_timeout = '60s'")
        # the sample's shared schema names the lane's tables `hansard_…`; a lane or staging schema does not
        shared = conn.execute("SELECT to_regclass(%s) IS NOT NULL", (table(schema, "sittings", True),)).fetchone()[0]
        f = figures(conn, schema, shared)
        if mcp_database != database:      # a scratch proof in the sample database: the pull's tables are the live ones
            with db.connect(db.READ_KEY, mcp_database) as other:
                other.execute("SET statement_timeout = '60s'")
                for t in ("cursors", "arrivals", "catch"):
                    cols = other.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = %s "
                                         "AND table_name = %s ORDER BY ordinal_position", (mcp_schema, t)).fetchall()
                    conn.execute(f"CREATE TEMP TABLE {t} ({', '.join(f'{c} {ty}' for c, ty in cols)})")
                    names = ", ".join(c for c, _ in cols)
                    with conn.cursor().copy(f"COPY {t} ({names}) FROM STDIN") as cp:
                        for row in other.execute(f"SELECT {names} FROM {mcp_schema}.{t} WHERE corpus LIKE 'parliament-hansard%%'"):
                            cp.write_row(row)
            mcp_schema = "pg_temp"
        h = mcp_held(conn, schema, mcp_schema, shared)
        sp = split_held(conn, schema, shared)
        recount = owner_recount(conn, schema, shared) if owner else None
    try:
        o = mcp_outside(M.Client())
        mcp_problems = mcp_failed(h, o, recount)
    except Exception as e:  # noqa: BLE001 — the MCP unreachable is a red line, not a crash
        o, mcp_problems = None, [f"the MCP did not answer: {type(e).__name__}: {str(e)[:200]}"]
    with db.connect(db.READ_KEY, "querynz_v4") as conn:       # the house lane's members, always from the published estate
        conn.execute("SET statement_timeout = '60s'")
        if conn.execute("SELECT to_regclass('pub.members') IS NOT NULL").fetchone()[0]:
            members = [n for (n,) in conn.execute("SELECT name FROM pub.members")]
            f["members"] = members_share(f["speakers"], members)
    problems = failed(f) + mcp_problems + split_failed(sp)
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
    d = h["parliament-hansard-debates"]
    print(f"{SCHEMA}: the MCP: " + ("; ".join(f"{c} taken {h[c]['cursor']} of {o[c]['records']}, n_docs {o[c]['n_docs']}"
                                              for c in CORPORA) if o else "not read")
          + f"; days {d['rows']}, words {h['words']}" + (f" against {o['parliament-hansard-debates']['corpus_words']}" if o else ""))
    w = h["worst day"]
    print(f"{SCHEMA}: old subjects in the same day's PDF text {h['in text']} of {h['subjects']}"
          + (f" ({h['in text'] / h['subjects']:.1%})" if h["subjects"] else "")
          + (f", worst day {w[0]} {w[1]} of {w[2]}" if w else "")
          + f"; by where found: {', '.join(f'{k} {v}' for k, v in sorted(h['found'].items()))}"
          + (f"; recounted from the texts {recount}" if recount is not None else ""))
    print(f"{SCHEMA}: days both hold {h['both']}; only the MCP {h['mcp only']} ({h['mcp only since the old first day']} "
          f"from the old estate's first day on); old days the MCP lacks {h['old only']}; sittings whose page the index "
          f"names {h['sittings the index names']} of {len(f['sittings'])}")
    b = sp["both"]
    print(f"{SCHEMA}: the split (hansard-day): days {sp['days']}, split {sp['days split']}, set aside at read "
          f"{sp['days set aside at read']}; sections {sp['sections']}, turns {sp['turn rows']}; on the {b['days']} days both hold, "
          f"sections equal {b['sections equal']}, member turns more {b['member turns more']}, equal {b['member turns equal']}, "
          f"fewer {b['member turns fewer']} ({b['split member turns']} against the old lists' {b['old member turns']})")
    print(f"{SCHEMA}: the text reader: days read {sp['days read']}, waiting {sp['days waiting']}; pieces {sp['pieces']} "
          f"({sp['pieces unusable']} unusable, {sp['pieces truncated']} cut at the token cap); names {sp['names']} "
          f"({', '.join(f'{k} {v}' for k, v in sp['names by kind'].items()) or 'none'}); readings under another version "
          f"{len(sp['other versions'])}")
    print(f"{SCHEMA}: " + ("0 problems" if not problems else f"{len(problems)} problems"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
