"""The offices pass: each political or public office an article gives a person, completed (a trial; Arthur, 27 November
2026, on the office-rule set: "All MPs should have a party, and either 'list' for non-local MPs, or a specified
electorate"; "spokesperson must always be accompanied by an organisation on behalf of which they speak"; "'caretaker'
is a modifier like 'interim'"; "ex-Labour minister Michael Wood ... used to be a minister and a member of the labour
party"; "ministers dont have to be associated with a political party ... it is a governmental position"; "local mps can
be independent").

    python -m registers.news.offices trial [--run o1] [--workers 4]   the office-rule-1 set's articles, into live/news-trial/offices-<run>
    python -m registers.news.offices review [--run o1]                that run as the review set news-offices-<run>

A pass of its own after the read, like the subjects pass: it is given the article, the read's people and the roles the
read bound, and names each office as data (office, portfolio, body, electorate, list, qualifier, party). The read's own
roles prompt (tuned over tranches 1 to 6) is not changed. The gate: the office's words and every printed field must be in
the text. Not in the live read: a trial for Arthur's review.
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import re
import sys
import time
from pathlib import Path

OUT = Path("/home/user/querynzv4-work/live/news-trial")
REVIEW = Path("/home/user/querynzv4-work/live/review")
GATE = "registers.news.offices 1"
OFFICES = ("member of parliament", "minister", "associate minister", "prime minister", "deputy prime minister",
           "party leader", "party co-leader", "party deputy leader", "party president", "spokesperson", "whip", "speaker",
           "mayor", "deputy mayor", "councillor", "candidate", "other")
QUALIFIERS = ("current", "former", "acting", "caretaker", "interim", "incoming", "outgoing", "designate")

PROMPT = """You name the political and public offices one New Zealand news article gives each person, as data. You are given the article, its people (with ids) and the roles a first reading found. Use only what the article prints; never add what you know from outside it.

For each office a person holds or held in the article, give:
- "who": the person's id.
- "office": one of member of parliament, minister, associate minister, prime minister, deputy prime minister, party leader, party co-leader, party deputy leader, party president, spokesperson, whip, speaker, mayor, deputy mayor, councillor, candidate, other.
- "words": the words that give the office, copied character for character from the article ("Labour's finance spokesperson", "National MP for Hamilton West", "caretaker Health Minister").
- "portfolio": for a minister or spokesperson, the area as printed ("Health", "climate change", "finance"), else null.
- "body": who the office is of, as printed: for a party leader or co-leader the party ("Green Party"); for a spokesperson the party or organisation they speak for; for a mayor or councillor the council ("Nelson City Council", "Nelson"); for a minister the government only when printed; else null.
- "party": the party the article says the person belongs to, as printed ("Labour", "National", "Te Pāti Māori"), "independent" when it says so, else null. A party's name before an office ("Labour minister", "ex-Labour minister") is the person's party. A minister needs no party.
- "electorate": for a member of parliament, the electorate as printed ("Hamilton West", "Northland"), else null.
- "list": true when the article calls the member a list MP, false when it gives an electorate, null when it says neither. "Local MP" with no electorate named is list null and electorate null.
- "qualifier": current, former, acting, caretaker, interim, incoming, outgoing or designate. "ex-" and "former" are former; "caretaker" is caretaker (it is never part of the office); "relieving" is acting.

One entry per office: a person who is an MP and a minister has two. An office the article only implies is not given. A person with no office in the article has no entry.
Answer with ONE JSON object {"offices": [...]}."""

#: o2 (27 November 2026), from Arthur's judgments of o1 (12 of 18 right): "other" hides the office ("the office is Māori
#: caucus chair"; "role: chair or committee chair"; "whats wrong with former climate ambassador?"), so every office carries
#: its title as printed; a person the article names by surname alone has none ("Jones ... drop it"); an activity is no
#: office ("co-chaired negotiations ... doesnt denote a conclusive office or role"); an organisation with its abbreviation
#: printed is written "name (ABBREVIATION)" ("NZNO should be in parentheses")
PROMPT_O2 = PROMPT.replace(
    '- "words": the words that give the office',
    '- "title": the office as a noun phrase, the words printed, without the person, the party or the body: "Māori caucus chair", "chair", "climate ambassador", "kaiwhakahaere", "Health Minister", "list MP". Always given; for "other" it is the office.\n'
    '- "words": the words that give the office').replace(
    '- "body": who the office is of, as printed:',
    '- "body": who the office is of, as printed (an organisation whose abbreviation the article prints is "name (ABBREVIATION)": "Tōpūtanga Tapuhi Kaitiaki o Aotearoa (NZNO)"):').replace(
    'One entry per office:',
    'Only a position a person holds or held, never a thing they did: "co-chaired negotiations" or "led the delegation" is no office. A person the article names by a surname alone ("Jones") gets no entry.\n'
    'One entry per office:')
PROMPTS = {"o1": PROMPT, "o2": PROMPT_O2}

SN = {"type": ["string", "null"]}
SCHEMA = {"type": "object", "properties": {"offices": {"type": "array", "items": {"type": "object", "properties": {
    "who": {"type": "string"}, "office": {"type": "string", "enum": list(OFFICES)}, "title": SN, "words": {"type": "string"},
    "portfolio": SN, "body": SN, "party": SN, "electorate": SN, "list": {"type": ["boolean", "null"]},
    "qualifier": {"type": "string", "enum": list(QUALIFIERS)}},
    "required": ["who", "office", "title", "words", "portfolio", "body", "party", "electorate", "list", "qualifier"]}}},
    "required": ["offices"]}


def _fold(s: str) -> str:
    import unicodedata
    s = "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def gate(offices: list, text: str, people: set) -> tuple[list, list]:
    """Kept: a known person, the words in the text, each printed field in the text ("independent" excepted)."""
    t = _fold(text)
    kept, dropped = [], []
    for o in offices:
        if not isinstance(o, dict):
            continue
        why = None
        if o.get("who") not in people:
            why = "not a person of the article"
        elif not o.get("words") or _fold(o["words"]) not in t:
            why = "words not in the text"
        else:
            for f in ("portfolio", "body", "party", "electorate"):
                v = o.get(f)
                if v and not (f == "party" and _fold(v) == "independent") and _fold(v) not in t:
                    why = f"{f} not in the text"
                    break
        (dropped if why else kept).append({**o, **({"rule": why} if why else {})})
    return kept, dropped


def user_text(text: str, people: dict, roles: list) -> str:
    ps = "\n".join(f"{k}: {v.get('name')}" for k, v in people.items())
    rs = "\n".join(f"{r.get('who')}: {r.get('role')}" + (f" (of {r.get('of')})" if r.get("of") else "") for r in roles)
    return f"PEOPLE:\n{ps or '(none)'}\n\nROLES FOUND:\n{rs or '(none)'}\n\nARTICLE:\n{text}"


def one(text: str, got: dict, url: str, model: str, lane: str = "news-trial", prompt: str = None) -> dict:
    from registers.news.gold import trial as T
    t0 = time.monotonic()
    ents = got.get("entities") if isinstance(got.get("entities"), dict) else {}
    people = {k: v for k, v in ents.items() if isinstance(v, dict) and v.get("kind") == "person"}
    roles = [r for r in got.get("roles") or [] if isinstance(r, dict) and r.get("who") in people]
    out, raw = T._call(url, model, prompt or PROMPT, user_text(text, people, roles), SCHEMA, "offices", lane)
    kept, dropped = gate((T._parse(raw) or {}).get("offices") or [], text, set(people))
    return {"offices": kept, "dropped": dropped, "people": {k: v.get("name") for k, v in people.items()},
            "gate": GATE, "model": model, "seconds": round(time.monotonic() - t0, 1)}


def _articles() -> list[dict]:
    """The office-rule-1 set's articles: each with its text and its stored reading."""
    from support import db
    from support import reader as rd
    src = REVIEW / "office-rule-1.json"
    d = json.loads((src if src.exists() else REVIEW / "done" / "office-rule-1.json").read_text())
    keys = list(dict.fromkeys(q["article"] for q in d["questions"]))
    out = []
    with db.connect(db.READ_KEY, "querynz_v4") as c:
        for k in keys:
            r = c.execute("SELECT r.reading_key, r.title, t.text FROM pub.news_read r JOIN pub.news_read_text t USING (url_key) "
                          "WHERE r.url_key = %s", (k,)).fetchone()
            if r:
                out.append({"id": re.sub(r"[^a-z0-9]+", "-", k.lower())[:60], "url_key": k, "title": r[1], "text": r[2],
                            "got": json.loads(rd.Store().get(r[0]).text or "{}")})
    return out


def trial(run: str, url: str, model: str, workers: int, prompt: str = "o1") -> Path:
    out = OUT / f"offices-{run}"
    out.mkdir(parents=True, exist_ok=True)

    def go(a):
        p = out / f"{a['id']}.json"
        if p.exists():
            return a["id"], "kept"
        try:
            got = one(a["text"], a["got"], url, model, prompt=PROMPTS[prompt])
        except Exception as e:
            return a["id"], f"failed: {type(e).__name__}: {str(e)[:200]}"
        p.write_text(json.dumps({**got, "id": a["id"], "url_key": a["url_key"], "title": a["title"], "text": a["text"]},
                                ensure_ascii=False, indent=1))
        return a["id"], f"{len(got['offices'])} kept, {len(got['dropped'])} dropped, {got['seconds']} s"
    with cf.ThreadPoolExecutor(workers) as ex:
        for aid, how in ex.map(go, _articles()):
            print(aid, how, flush=True)
    return out


def describe(o: dict, people: dict) -> str:
    bits = [o["qualifier"] if o["qualifier"] != "current" else "", o["office"]]
    if o.get("title") and o["title"].lower() != o["office"]:
        bits.append(f"({o['title']})")
    if o.get("portfolio"):
        bits.append(f"· portfolio {o['portfolio']}")
    if o.get("body"):
        bits.append(f"· of {o['body']}")
    if o.get("party"):
        bits.append(f"· party {o['party']}")
    if o.get("electorate"):
        bits.append(f"· electorate {o['electorate']}")
    if o.get("list") is True:
        bits.append("· list")
    return f"{people.get(o['who'], o['who'])}: " + " ".join(b for b in bits if b)


def context_runs(text: str, offices: list) -> list:
    """The article's own sentences that hold each office's words, the words marked, in the article's order: the sample
    the review page shows (Arthur, 27 November 2026: "the sample text rarely contains the relevant context")."""
    body = text.split("\n\n", 1)[1] if "\n\n" in text else text
    spans = [(m.start(), m.end()) for m in re.finditer(r"[^.!?\n]+[.!?]?", body)]
    picked = {}
    for o in offices:
        w = (o.get("words") or "").strip()
        if not w:
            continue
        i = body.lower().find(w.lower())
        if i < 0:
            continue
        for a, b in spans:
            if a <= i < b:
                picked.setdefault((a, b), []).append((i, i + len(w)))
                break
    runs = []
    for (a, b), marks in sorted(picked.items()):
        pos = a
        for i, j in sorted(set(marks)):
            if i < pos:
                continue
            runs += [{"text": body[pos:i]}, {"text": body[i:j], "mark": "role"}]
            pos = j
        runs += [{"text": body[pos:b].rstrip() + "\n"}]
    return [r for r in runs if r["text"]] or [{"text": "(no office in the text)"}]


def review(run: str) -> Path:
    arts, qs = {}, []
    for p in sorted((OUT / f"offices-{run}").glob("*.json")):
        r = json.loads(p.read_text())
        arts[r["id"]] = {"title": r["title"], "site": "", "date": "", "body": r["text"], "tags": []}
        ask = [{"text": "Offices named:\n"}]
        for o in r["offices"]:
            ask += [{"text": "• "}, {"text": describe(o, r["people"]), "mark": "who"}, {"text": "  from: "},
                    {"text": o["words"], "mark": "role"}, {"text": "\n"}]
        if not r["offices"]:
            ask.append({"text": "(none)\n"})
        if r["dropped"]:
            ask.append({"text": "Dropped by the gate: " + "; ".join(f"{o.get('words')} ({o['rule']})" for o in r["dropped"]) + "\n"})
        ask.append({"text": "Are these the offices, complete and right?"})
        qs.append({"id": r["id"][:40], "kind": "offices", "label": "Offices", "article": r["id"], "ask": ask,
                   "context": context_runs(r["text"], r["offices"] + r["dropped"]),
                   "choices": [{"key": "yes", "label": "Yes: right and complete"},
                               {"key": "wrong", "label": "One or more is wrong (note which)"},
                               {"key": "missing", "label": "One or more is missing (note what)"},
                               {"key": "both", "label": "Some wrong and some missing (note)"}],
                   "sides": {"model": "yes"}})
    name = f"news-offices-{run}"
    p = REVIEW / f"{name}.json"
    p.write_text(json.dumps({"set": name, "title": f"News offices, trial {run}",
                             "about": "A pass after the read that completes each political or public office: party, "
                                      "electorate or list, portfolio, who a spokesperson speaks for, and the qualifier "
                                      "(former, caretaker, acting). The twenty office-rule articles.",
                             "made_by": "registers.news.offices", "run": run, "skipped": {},
                             "articles": arts, "questions": qs}, ensure_ascii=False, indent=1))
    return p


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    def opt(k, d):
        return argv[argv.index(k) + 1] if k in argv else d
    from registers.news.gold import trial as T
    run = opt("--run", "o1")
    if argv[:1] == ["trial"]:
        print(trial(run, opt("--url", T.URL), opt("--model", T.MODEL), int(opt("--workers", "4")), opt("--prompt", "o1")))
    elif argv[:1] == ["review"]:
        print(review(run))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
