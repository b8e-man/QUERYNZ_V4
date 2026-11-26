"""Twenty cases of a proposed links rule, for Arthur in the review tab (links rules as we go: measure, twenty pairs,
Arthur rules, then a versioned rule; 27 November 2026).

    python -m links.office_review build [--n 20]     the set office-rule-1 into the review folder

THE PROPOSAL. A name in a read article fits several register entities (a possible tie, links.news). Where exactly one
of them is a politician (pub.entities.politician) and the article's own roles give the name a political office
(OFFICE), the name is that politician. Measured 27 November 2026: 2,197 of 30,458 possible people. Not applied: this
set is the twenty cases Arthur judges first, one a name, newest first.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REVIEW = Path("/home/user/querynzv4-work/live/review")
OFFICE = re.compile(r"\b(minister|prime minister|mp|member of parliament|leader|co-leader|deputy leader|spokesperson|whip|"
                    r"speaker|mayor|councillor)\b", re.I)


def build(n: int = 20, log=print) -> Path:
    from support import db
    from support import reader as rd
    store = rd.Store()
    with db.connect(db.READ_KEY, "querynz_v4") as conn:
        poss = conn.execute("""
            SELECT t.url_key, t.entity, n.name, r.reading_key, r.title, r.host, r.published_at, r.url,
                   array_agg(e.entity_id ORDER BY e.politician DESC), array_agg(e.display_name ORDER BY e.politician DESC),
                   array_agg(coalesce(e.politician, false) ORDER BY e.politician DESC),
                   array_agg(array_to_string(e.registers, ', ') ORDER BY e.politician DESC)
            FROM pub.news_ties t JOIN pub.entities e USING (entity_id) JOIN pub.news_entities n USING (url_key, entity)
            JOIN pub.news_read r USING (url_key)
            WHERE t.status = 'possible' AND n.kind = 'person'
            GROUP BY 1, 2, 3, 4, 5, 6, 7, 8 HAVING sum(coalesce(e.politician, false)::int) = 1
            ORDER BY r.published_at DESC NULLS LAST""").fetchall()
        texts = {}
        qs, arts, seen = [], {}, set()
        for url_key, ent, name, key, title, host, published, url, ids, names, pols, regs in poss:
            if name.lower() in seen:
                continue
            got = json.loads(store.get(key).text or "{}")
            roles = [r for r in got.get("roles") or [] if isinstance(r, dict) and r.get("who") == ent and OFFICE.search(r.get("role") or "")]
            if not roles:
                continue
            if url_key not in texts:
                texts[url_key] = (conn.execute("SELECT text FROM pub.news_read_text WHERE url_key = %s", (url_key,)).fetchone() or [""])[0]
            seen.add(name.lower())
            role = roles[0].get("role")
            arts[url_key] = {"title": title, "site": host, "date": published.date().isoformat() if published else "",
                             "body": texts[url_key], "tags": {}}
            others = "; ".join(f"{nm} ({rg})" for nm, rg, p in zip(names[1:], regs[1:], pols[1:]))
            qs.append({"id": f"{len(qs) + 1:02d}", "kind": "office", "label": "Political office", "article": url_key,
                       "ask": [{"text": "The article names "}, {"text": name, "mark": "who"}, {"text": " as "},
                               {"text": role, "mark": "role"},
                               {"text": f".\nThe politician: {names[0]} ({regs[0]}).\nThe other candidates: {others}.\n"
                                        "Is the person in the article the politician?"}],
                       "context": [{"text": name, "mark": "who"}, {"text": " · "}, {"text": role, "mark": "role"}],
                       "choices": [{"key": "yes", "label": "Yes, the politician"},
                                   {"key": "no", "label": "No, someone else"},
                                   {"key": "unsure", "label": "Can't tell from the article"}],
                       "sides": {"rule": "yes"}})
            if len(qs) >= n:
                break
    p = REVIEW / "office-rule-1.json"
    p.write_text(json.dumps({"set": "office-rule-1", "title": "Political office settles a possible name",
                             "about": "A proposed links rule: a name that fits several people, exactly one a politician, "
                                      "given a political office by the article itself, is that politician. Twenty cases, "
                                      "one a name, newest first. Judge from the article.",
                             "made_by": "links.office_review", "articles": arts, "questions": qs}, ensure_ascii=False, indent=1))
    log(f"{p}: {len(qs)} cases")
    return p


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["build"]:
        build(int(argv[argv.index("--n") + 1]) if "--n" in argv else 20)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
