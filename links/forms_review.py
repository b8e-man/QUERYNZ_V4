"""The name forms Arthur judges: a list of the forms most likely not to be names, for the board's review tab
(Arthur, 27 November 2026: "I need a review of these junk names in the reviewer to assess. this should be a scrollable
list where I identify names that need a closer look as most will be instantly identifiable as junk so I need to be
able to rapidly discard these and identify ones that need more consideration. lets do this then establish the rules
based on what is discarded. each name-form should only be listed for judging once").

    python -m links.forms_review build [--n 1500]    the next set, name-forms-<k>, into the review folder
    python -m links.forms_review absorb              every set's junk and wrong-kind answers into links/forms_judged.json,
                                                     which the form build reads (links.sightings.JUDGED)

WHICH FORMS. A form of links.name_forms the name pass has found at least MIN_HITS times (links.sightings, every lane)
that holds a small word ("of the", "in their") or is found HITS_PER_ROW times as often as the registers file it (a
real name is filed in many rows: "john key" 15,270 rows, 72,993 sightings; a phrase in few: "covid 19", one row,
91,240), the most found first. A form listed in any earlier set of this kind, answered or not, is never listed
again. Each carries what it is filed as (kind, rows), how often and in which lanes it is found, and up to three rows
that file it (register, view, the name as filed), so it is judged on what made it.

THE CHOICES. junk (not a name: discard), wrong kind (a name, filed as the other kind: "Callaghan Innovation" as a
person), keep (a name, rightly filed), closer look. The rules come after, from what is discarded.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

REVIEW = Path("/home/user/querynzv4-work/live/review")
PREFIX = "name-forms-"
MIN_HITS, HITS_PER_ROW, N = 20, 30, 1500
SMALL = ["of", "the", "in", "their", "her", "his", "our", "its", "one", "and", "to", "for", "on", "at", "by", "with", "from",
         "this", "that", "is", "was", "be", "are", "we", "they", "you", "it", "as", "or", "an", "a", "all", "new", "under",
         "over", "after", "before", "who", "what", "which", "not", "no", "into", "about"]
CHOICES = [{"key": "junk", "label": "Junk"}, {"key": "kind", "label": "Wrong kind"},
           {"key": "keep", "label": "Keep"}, {"key": "look", "label": "Closer look"}]


def qid(form: str) -> str:
    return hashlib.sha256(form.encode()).hexdigest()[:16]


def listed(folder: Path = None) -> set:
    """Every form any earlier set of this kind listed, answered or not (Arthur: "only listed for judging once")."""
    out = set()
    for p in (folder or REVIEW).glob(f"{PREFIX}*.json"):
        try:
            out |= {q["form"] for q in json.loads(p.read_text())["questions"]}
        except (ValueError, KeyError):
            continue
    return out


def next_name(folder: Path = None) -> str:
    ks = [int(p.stem[len(PREFIX):]) for p in (folder or REVIEW).glob(f"{PREFIX}*.json") if p.stem[len(PREFIX):].isdigit()]
    return f"{PREFIX}{max(ks, default=0) + 1}"


def build(n: int = N, log=print) -> Path:
    from support import db
    from links import sightings as S
    t0 = time.monotonic()
    before = listed()
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = 0")
        rows = conn.execute("""
            WITH lanes AS (SELECT form, lane, count(*) AS n FROM links.sightings GROUP BY 1, 2),
                 hits AS (SELECT form, sum(n) AS n, jsonb_object_agg(lane, n) AS lanes FROM lanes GROUP BY 1)
            SELECT h.form, f.kind, f.rows, h.n, h.lanes
            FROM hits h JOIN links.name_forms f USING (form)
            WHERE h.n >= %s AND (string_to_array(h.form, ' ') && %s OR h.n::float / f.rows >= %s)
            ORDER BY h.n DESC""", (MIN_HITS, SMALL, HITS_PER_ROW)).fetchall()
        pick = [r for r in rows if r[0] not in before][:n]
        want = {r[0] for r in pick}
        log(f"forms: {len(rows):,} suspect, {len(before):,} listed before, {len(pick):,} this set ({time.monotonic() - t0:.0f} s)")
        examples: dict = {f: [] for f in want}
        with conn.cursor(name="filed") as cur:          # the rows that make each form, as build_forms makes them
            cur.itersize = 50000
            cur.execute("SELECT kind, name_filed, given, middle, family, register, view FROM links.rows "
                        "WHERE NOT (view = ANY(%s)) AND NOT suppressed", (sorted(S.MODEL_VIEWS),))
            for kind, filed, given, middle, family, register, view in cur:
                for f in S.forms_of(kind, filed, given, middle, family):
                    if f in want and len(examples[f]) < 3 and (register, view, filed) not in examples[f]:
                        examples[f].append((register, view, filed))
        conn.commit()
    qs = [{"id": qid(form), "kind": "form", "label": "Name form", "form": form, "filed_as": kind, "rows": rows_n,
           "hits": int(hits), "lanes": lanes or {}, "filed": [{"register": a, "view": b, "name": c} for a, b, c in examples[form]],
           "choices": CHOICES} for form, kind, rows_n, hits, lanes in pick]
    name = next_name()
    p = REVIEW / f"{name}.json"
    REVIEW.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"set": name, "title": f"Name forms, list {name[len(PREFIX):]}", "mode": "list",
                             "about": "Forms the name pass finds that may not be names, the most found first. J junk, "
                                      "W wrong kind, K keep, L closer look; each judged once.",
                             "made_by": "links.forms_review", "questions": qs}, ensure_ascii=False, indent=1))
    log(f"{p}: {len(qs)} forms, {time.monotonic() - t0:.0f} s")
    return p


#: Arthur's rulings on whole classes of the closer-look forms (27 November 2026: "G. junk"): the fragments of a minister's
#: diary lines and portfolios
CLASS_RULINGS = {f: {"choice": "junk", "by": "Arthur, 27 November 2026, class G (portfolio fragments): junk"}
                 for f in ("social development", "economic development", "covid 19", "crown entities", "of health")}


def absorb(folder: Path = None, out: Path = None) -> dict:
    """Each answered junk or wrong-kind form into the judged file, newest answer of a form winning; class rulings over
    them. Keep, closer look and unanswered forms are not carried: they rule nothing."""
    from links import sightings as S
    folder, out = folder or REVIEW, out or S.JUDGED
    got = {}
    for p in sorted(folder.glob(f"{PREFIX}*.json"), key=lambda q: int(q.stem[len(PREFIX):]) if q.stem[len(PREFIX):].isdigit() else 0):
        try:
            forms = {q["id"]: q["form"] for q in json.loads(p.read_text())["questions"]}
            answers = json.loads((folder / "answers" / p.name).read_text())
        except (OSError, ValueError, KeyError):
            continue
        for qid_, a in answers.items():
            if qid_ in forms and a.get("choice") in ("junk", "kind"):
                got[forms[qid_]] = {"choice": a["choice"], "by": f"Arthur, review set {p.stem}", **({"note": a["note"]} if a.get("note") else {})}
    got.update(CLASS_RULINGS)
    out.write_text(json.dumps(dict(sorted(got.items())), ensure_ascii=False, indent=1) + "\n")
    return {"forms": len(got), "junk": sum(1 for v in got.values() if v["choice"] == "junk"),
            "kind": sum(1 for v in got.values() if v["choice"] == "kind")}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["build"]:
        build(int(argv[argv.index("--n") + 1]) if "--n" in argv else N)
        return 0
    if argv[:1] == ["absorb"]:
        from products.board import review
        review.export(sorted(p.stem for p in REVIEW.glob(f"{PREFIX}*.json")))
        print(json.dumps(absorb()))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
