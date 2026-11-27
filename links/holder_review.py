"""An office's holder on a date: twenty cases of a proposed links rule for Arthur (links rules as we go: measure, twenty
pairs, Arthur rules; ruling B, 27 November 2026: "an office is not a person ... a mention resolves to the holder on its
date").

    python -m links.holder_review build [--n 20]     measure, and write the set office-holder-1 into the review folder

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
    if argv[:1] == ["build"]:
        build(int(argv[argv.index("--n") + 1]) if "--n" in argv else 20)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
