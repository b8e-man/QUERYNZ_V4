"""An office's holder on a date: twenty cases of a proposed links rule for Arthur (links rules as we go: measure, twenty
pairs, Arthur rules; ruling B, 27 November 2026: "an office is not a person ... a mention resolves to the holder on its
date").

    python -m links.holder_review build [--n 20]     measure, and write the set office-holder-1 into the review folder
    python -m links.holder_review evidence           the set's cases given their evidence again, ids kept

THE EVIDENCE (Arthur, 29 November 2026: "regenerate the sample texts where it does not contain the information
required to answer the question"). Each case shows the register row as its register files it (a court party with its
judgment's citation, court and date; a diary attendee with the entry it is in), the proposed holder's diary release for
the month with the portfolios it lists, and the holder's own diary entries in that portfolio nearest the date; the whole
of it opens as the case's article.

THE PROPOSAL. A register row that is an office ("Minister of Health", keys.names.is_office) and is dated (links.rows
started_on) is held by the minister whose own diary release for that month lists the portfolio by its own name ("Health",
never "Associate Health"; pub.minister_diary_releases, October 2017 to August 2026), when exactly one minister does. The
Prime Minister by the same diaries' "Prime Minister" portfolio. Not applied: this set is the twenty cases Arthur judges
first, one a portfolio that file offices.
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

REVIEW = Path("/home/user/querynzv4-work/live/review")
_OF = re.compile(r"^(the\s+)?minister\s+(of|for)\s+(the\s+)?", re.I)


def fold(s: str) -> str:
    import unicodedata
    s = "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s.replace("&", " and ")).split())


def portfolio_of(office: str) -> str | None:
    """"MINISTER OF HEALTH" → "health"; "The Prime Minister" → "prime minister"; an office not a minister's: None."""
    s = re.sub(r"\([^()]*\)", " ", office or "").strip()
    if re.match(r"^(the\s+)?prime minister$", s, re.I):
        return "prime minister"
    if not _OF.match(s):
        return None
    p = fold(_OF.sub("", s))
    p = re.sub(r"\s+of new zealand$", "", p)
    return p or None


def holders(conn) -> dict:
    """{(portfolio, "YYYY-MM"): {minister, ...}} from the diary releases, a portfolio by its own name only."""
    out: dict = {}
    for minister, ports, first, last in conn.execute(
            "SELECT minister, portfolios, first_on, last_on FROM pub.minister_diary_releases "
            "WHERE first_on IS NOT NULL AND portfolios IS NOT NULL").fetchall():
        months = {first.strftime("%Y-%m"), (last or first).strftime("%Y-%m")}
        for p in ports or []:
            f = fold(p)
            if not f or f.startswith(("associate", "withh", "all")) or f in ("minister", "ministerial", "attend"):
                continue
            f = "prime minister" if f in ("prime minister", "pm") else f
            for m in months:
                out.setdefault((f, m), set()).add(minister)
    return out


def _row_lines(conn, view: str, key: str) -> list:
    """The register row as its register files it: [(label, text)]."""
    if view == "court_judgment_parties":
        r = conn.execute("SELECT p.name, p.role, p.citation, j.court_name, p.judgment_date, j.heading FROM pub.court_judgment_parties p "
                         "LEFT JOIN pub.court_judgments j ON j.key = p.judgment WHERE p.key = %s", (key,)).fetchone()
        if r:
            return [("Court party", f"{r[0]}, {r[1] or 'a party'}"),
                    ("Judgment", f"{r[2]}, {r[3] or ''}, {r[4].isoformat() if r[4] else 'undated'}".replace(", ,", ","))]
    if view == "minister_diary_attendees":
        r = conn.execute("SELECT a.attendee, e.minister, e.portfolio, e.entry_on, e.time, e.meeting, "
                         "CASE WHEN e.attendees_names_address THEN NULL ELSE e.attendees END "
                         "FROM pub.minister_diary_attendees a JOIN pub.minister_diary_entries e ON e.key = a.entry WHERE a.key = %s",
                         (key,)).fetchone()
        if r:
            return [("Diary attendee", r[0]),
                    ("In the diary of", f"{r[1]}, {r[3].isoformat() if r[3] else ''} {r[4] or ''} ({r[2] or 'no portfolio'})"),
                    ("Meeting", r[5] or ""), ("Attendees as released", r[6] or "(not shown: the line names an address)")]
    return [("Register row", f"{view} {key}")]


def _holder_lines(conn, holder: str, p: str, on) -> list:
    """The holder's release for the month of `on`, its portfolios, and the holder's entries in portfolio `p` nearest `on`."""
    out = []
    rel = conn.execute("SELECT key, file_name, portfolios, first_on, last_on FROM pub.minister_diary_releases "
                       "WHERE minister = %s AND first_on <= %s AND coalesce(last_on, first_on) >= date_trunc('month', %s::date) "
                       "ORDER BY first_on", (holder, on, on)).fetchall()
    for key, fname, ports, first, last in rel:
        out.append(("Diary release", f"{fname} ({first.isoformat()} to {(last or first).isoformat()})"))
        out.append(("Its portfolios", "; ".join(x for x in ports or [] if x)))
        ent = conn.execute("SELECT entry_on, time, portfolio, meeting FROM pub.minister_diary_entries WHERE release = %s "
                           "AND entry_on IS NOT NULL ORDER BY abs(entry_on - %s::date), entry_on LIMIT 400", (key, on)).fetchall()
        near = [e for e in ent if fold(e[2] or "") in (p, "pm" if p == "prime minister" else p)][:3]
        for e in sorted(near):
            out.append(("Entry", f"{e[0].isoformat()} {e[1] or ''} ({e[2]}): {e[3] or ''}"))
        if not near:
            out.append(("Entry", f"no entry of this release is in the portfolio {p}"))
    if not rel:
        out.append(("Diary release", f"none of {holder} covers {on.isoformat()}"))
    return out


def evidence(conn, view: str, key: str, name: str, p: str, holder: str, on) -> tuple:
    """(article, context) for one case: the lines that answer it, the office and holder marked."""
    lines = _row_lines(conn, view, key) + _holder_lines(conn, holder, p, on)
    body = "\n".join(f"{a}: {b}" for a, b in lines)
    ctx = []
    for a, b in lines:
        ctx.append({"text": f"{a}: "})
        marks = [(b.find(w), w) for w in (name, holder) if w and b.find(w) >= 0]
        pos = 0
        for i, w in sorted(marks):
            if i < pos:
                continue
            ctx += [{"text": b[pos:i]}, {"text": w, "mark": "who" if w == name else "role"}]
            pos = i + len(w)
        ctx.append({"text": b[pos:] + "\n"})
    return {"title": f"{name} on {on.isoformat()}", "site": "", "date": on.isoformat(), "body": body, "tags": []}, \
        [r for r in ctx if r["text"]]


def refresh_evidence(log=print) -> Path:
    """The set's cases, ids and asks kept, each given its evidence (the register row found by view, name and date)."""
    import datetime as dt
    from support import db
    out = REVIEW / "office-holder-1.json"
    d = json.loads(out.read_text())
    arts = {}
    with db.connect(db.READ_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '120s'")
        for q in d["questions"]:
            ask = q["ask"] if isinstance(q["ask"], list) else json.loads(q["ask"])
            name, holder = ask[1]["text"], ask[3]["text"]
            m = re.search(r"\((\w+), dated (\d{4}-\d\d-\d\d)\)", ask[2]["text"])
            view, on = m.group(1), dt.date.fromisoformat(m.group(2))
            row = conn.execute("SELECT key FROM links.rows WHERE view = %s AND name_filed = %s AND started_on = %s "
                               "ORDER BY key LIMIT 1", (view, name, on)).fetchone()
            p = portfolio_of(name)
            arts[q["id"]], q["context"] = evidence(conn, view, row[0] if row else "", name, p, holder, on)
            q["article"] = q["id"]
    d["articles"] = arts
    out.write_text(json.dumps(d, ensure_ascii=False, indent=1))
    log(f"{out}: {len(d['questions'])} cases given their evidence")
    return out


def build(n: int = 20, log=print) -> Path:
    from keys import names as kn
    from links.rows import MODEL_VIEWS
    from support import db
    with db.connect(db.READ_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '600s'")
        held = holders(conn)
        rows = conn.execute(
            "SELECT ref, view, name_filed, started_on FROM links.rows WHERE NOT (view = ANY(%s)) AND started_on IS NOT NULL "
            "AND name_filed ~* '(minister|prime minister)'", (sorted(MODEL_VIEWS),)).fetchall()
    tally = {"office rows dated": 0, "a minister's portfolio": 0, "in the diaries' months": 0, "one holder": 0, "several": 0}
    cases = []
    for ref, view, name, on in rows:
        if not kn.is_office(name):
            continue
        tally["office rows dated"] += 1
        p = portfolio_of(name)
        if not p:
            continue
        tally["a minister's portfolio"] += 1
        got = held.get((p, on.strftime("%Y-%m")))
        if not got:
            continue
        tally["in the diaries' months"] += 1
        if len(got) == 1:
            tally["one holder"] += 1
            cases.append((view, name, on, p, next(iter(got))))
        else:
            tally["several"] += 1
    log(json.dumps(tally))
    random.seed(27)
    pick, seen = [], set()
    for c in random.sample(cases, len(cases)):                # one a portfolio first, then one a portfolio and month
        if c[3] not in seen and len(pick) < n:
            seen.add(c[3])
            pick.append(c)
    for c in random.sample(cases, len(cases)):
        if len(pick) >= n:
            break
        if (c[3], c[2].strftime("%Y-%m")) not in {(x[3], x[2].strftime("%Y-%m")) for x in pick}:
            pick.append(c)
    qs = [{"id": f"{i + 1:02d}", "kind": "holder", "label": "Office holder", "article": None,
           "ask": [{"text": "The register row "}, {"text": name, "mark": "who"},
                   {"text": f" ({view}, dated {on.isoformat()}).\nThe portfolio read: {p}.\nThe proposed holder: "},
                   {"text": holder, "mark": "role"},
                   {"text": f", the one minister whose own diary for {on.strftime('%B %Y')} lists the portfolio.\n"
                            "Did this minister hold that office on that date?"}],
           "context": [{"text": name, "mark": "who"}, {"text": " · "}, {"text": holder, "mark": "role"}],
           "choices": [{"key": "yes", "label": "Yes, the holder"}, {"key": "no", "label": "No"},
                       {"key": "unsure", "label": "Can't tell"}], "sides": {"rule": "yes"}}
          for i, (view, name, on, p, holder) in enumerate(pick)]
    out = REVIEW / "office-holder-1.json"
    out.write_text(json.dumps({"set": "office-holder-1", "title": "An office's holder on its date",
                               "about": "A proposed links rule: a dated register row that is a minister's office is held by "
                                        "the one minister whose own diary release for that month lists the portfolio. "
                                        f"Measured: {json.dumps(tally)}. Twenty cases across the views.",
                               "made_by": "links.holder_review", "articles": {}, "questions": qs}, ensure_ascii=False, indent=1))
    log(f"{out}: {len(qs)} cases")
    return out


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["evidence"]:
        refresh_evidence()
        return 0
    if argv[:1] == ["build"]:
        build(int(argv[argv.index("--n") + 1]) if "--n" in argv else 20)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
