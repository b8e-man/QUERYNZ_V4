"""The pack for Arthur (15 November 2026: "give me some to label and I'll check yours").

    python -m registers.news.gold.pack --check ID [ID ...] --label ID [ID ...]

Writes plain-language pages into /home/user/querynzv4-work/notes/news-gold-pack/: for each --check article, the
text and the session's labels as short lines to tick or strike; for each --label article, the text and an empty
form in the same plain words. Street addresses are masked as in `sample.show`. The session turns Arthur's answers
into labels/ files (labelled_by "arthur"); nothing here writes a label.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from registers.news.gold.sample import HERE, show

OUT = Path("/home/user/querynzv4-work/notes/news-gold-pack")

FORM = """## Your labels

Write as much or as little as you like, in any words. Leave a section empty if the article has none.

**People and organisations** (each once, with the kind: person, company, place, team, government…):

**Roles** (who, what, of which organisation; "of which" only if the article says so):

**Who said what** (speaker, and the words, quoted or reported):

**Allegations and denials** (anything not yet proven):

**Who the article is negative or positive about** (and in whose voice: the writer's or a speaker's):

**Anything that would trip a machine:**
"""


def _body(i: str) -> str:
    return show(i).split("\n---\n", 1)[1]


def _mine(d: dict) -> str:
    e = d["entities"]
    nm = lambda k: e.get(k, {}).get("name", k) if k else "nobody named"
    out = [f"Type: {d['article']['type']}. Themes: {', '.join(d['article'].get('themes') or [])}.", "",
           "**People and organisations**"]
    out += [f"- [ ] {v['name']} ({v['kind']})" for v in e.values()]
    out += ["", "**Roles**"]
    out += [f"- [ ] {nm(r['who'])}: {r['role']}" + (f", of {nm(r['of'])}" if r.get("of") else ", of no organisation the text names")
            + ("" if r["tense"] == "current" else f" ({r['tense']})") for r in d["roles"]]
    out += ["", "**Relations**"] + [f"- [ ] {nm(r['a'])} {r['says']} {nm(r['b'])}" for r in d["relations"]]
    out += ["", "**Who said what**"] + [f"- [ ] {nm(q['speaker'])}: \"{q['text'][:160]}\" ({q['form']})" for q in d["quotes"]]
    out += ["", "**Events**"] + [f"- [ ] {ev['kind']} — {', '.join(nm(w['e']) for w in ev['who'])} — {ev['modality']}" for ev in d["events"]]
    out += ["", "**Sentiment**"] + [f"- [ ] toward {nm(s['toward'])}, in the voice of {'the article' if s['from'] in ('article', 'own') else nm(s['from'])}: {s['value']} (\"{s['evidence'][:100]}\")" for s in d["sentiment"]]
    out += ["", "**Traps I saw**"] + [f"- {t}" for t in d.get("traps") or []]
    out += ["", "Strike or correct any line that is wrong; add anything I missed underneath."]
    return "\n".join(out)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--check" not in argv or "--label" not in argv:
        print(__doc__)
        return 2
    ci, li = argv.index("--check"), argv.index("--label")
    check = argv[ci + 1:li] if ci < li else argv[ci + 1:]
    label = argv[li + 1:ci] if li < ci else argv[li + 1:]
    OUT.mkdir(parents=True, exist_ok=True)
    idx = {a["id"]: a for a in json.loads((HERE / "tranche-1.json").read_text())["articles"]}
    names = []
    for n, i in enumerate(label + check, 1):
        a = idx[i]
        kind = "label" if i in label else "check"
        part = FORM if kind == "label" else "## My labels: check them\n\n" + _mine(json.loads((HERE / "labels" / f"{i}.json").read_text()))
        f = OUT / f"{n:02d}-{kind}-{i[:8]}.md"
        f.write_text(f"# {a['title']}\n\n{a['site']}, {a['post_date'][:10]}. Article {i}.\n\n## The article\n\n{_body(i)}\n\n{part}")
        names.append(f.name)
    (OUT / "README.md").write_text(
        "# News golden sample: your part\n\n"
        f"Pages 01–{len(label):02d}: label these yourself before looking at mine. "
        f"Pages {len(label) + 1:02d}–{len(names):02d}: my labels, to check. "
        "Write in the file or tell me in chat; I turn your words into the label files.\n\n"
        + "\n".join(f"- {x}" for x in names) + "\n")
    print("\n".join(names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
