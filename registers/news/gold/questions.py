"""The golden sample's questions for Arthur, for the board's review tab (Arthur, 15 November 2026: "a review tab with a
really good interface that gives me the question I'm answering and the information i need to answer it concisely").

    python -m registers.news.gold.questions [--tranche 1] [--run run2]

Writes /home/user/querynzv4-work/live/review/news-gold-<tranche>.json: one short question per point where the
hand labels and the model's read disagree, plus a share of points where they agree (so the labels are checked too).
Each question carries only what answers it: the sentence or two that hold it, with the words it asks about marked,
the headline, site and date, and the whole article behind a fold. Which side said what (`sides`) rides in the file
for scoring and is never shown. Regenerable; Arthur's answers live in the board's own table, never here.

Text is masked as `sample.show` masks it (no street address reaches the file).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from registers.news.gold import trial as T
from registers.news.gold.sample import HERE, _conn

OUT = Path("/home/user/querynzv4-work/live/review")

#: the order Arthur meets them in: the costliest errors first
ORDER = ["role", "allegation", "type", "kind", "sentiment", "quote"]
KIND_LABEL = {"role": "Job title", "allegation": "Fact or allegation", "type": "Kind of article",
              "kind": "What is it", "sentiment": "Tone", "quote": "Who said it"}
TYPE_LABEL = {"review": "review (rates a product or work)", "market_wrap": "market report (a day's trading)",
              "sponsored": "paid or advertorial", "stub": "cut off or paywalled", "feature": "feature (long-form)"}
#: a disagreement on what a name is matters only when one side calls it one of these (a person, a place); team
#: against organisation, or government against organisation, is not worth Arthur's time
MATTERS = {"person", "place"}
#: the model's quotes the labels lack, at most this many per article (most are the labels' gaps)
MODEL_ONLY_PER_ARTICLE = 1
#: of the points where both sides agree, one in AGREE_EVERY is asked too, so the labels are checked as well
AGREE_EVERY = {"quote": 10}
AGREE_DEFAULT = 4


def _qid(*parts) -> str:
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:12]


def _forms(ents: dict, eid) -> list:
    e = ents.get(eid) or {}
    fs = [f for f in (e.get("forms") or []) + [e.get("name") or ""] if f and len(f) > 1]
    return sorted(set(fs), key=len, reverse=True)


def _name(ents: dict, eid) -> str:
    return (ents.get(eid) or {}).get("name") or "nobody named"


def _paras(text: str) -> list:
    return [" ".join(p.split()) for p in re.split(r"\n\s*\n|\n", text) if p.strip()]


def _window(text: str, needles: list, need_all: bool = False, most: int = 2) -> str:
    """The sentence (or two) that holds the needles: the shortest context that answers the question. Paragraphs first;
    a paragraph longer than 600 characters is cut to its sentences."""
    low = [n.lower() for n in needles if n]
    best = []
    for p in _paras(text):
        units = [p] if len(p) <= 600 else T._sentences(p)
        for u in units:
            hits = sum(1 for n in low if n in u.lower())
            if hits and (not need_all or hits >= len(low)):
                best.append((hits, -len(u), u))
    best.sort(reverse=True)
    return " … ".join(u for _, _, u in best[:most]) if best else ""


def _marks(context: str, groups: dict) -> list:
    """[{"text", "mark"}] runs: each group's words marked where they fall (longest first, no overlap)."""
    spans = []
    for mark, words in groups.items():
        for w in sorted({w for w in words if w}, key=len, reverse=True):
            for m in re.finditer(re.escape(w), context, re.I):
                if not any(a < m.end() and m.start() < b for a, b, _ in spans):
                    spans.append((m.start(), m.end(), mark))
    spans.sort()
    out, at = [], 0
    for a, b, mark in spans:
        if a > at:
            out.append({"text": context[at:a]})
        out.append({"text": context[a:b], "mark": mark})
        at = b
    if at < len(context):
        out.append({"text": context[at:]})
    return out


def build(tranche: int = 1, run: str = "run2") -> dict:
    meta = {a["id"]: a for a in json.loads((HERE / f"tranche-{tranche}.json").read_text())["articles"]}
    articles, qs, n_agree = {}, [], {}

    def ask(kind, aid, ask_parts, context, groups, choices, sides, key):
        nonlocal n_agree
        if sides.get("gold") == sides.get("model"):
            n_agree[kind] = n_agree.get(kind, 0) + 1
            if n_agree[kind] % AGREE_EVERY.get(kind, AGREE_DEFAULT):
                return
        if not context:
            return
        qs.append({"id": _qid(kind, aid, key), "kind": kind, "label": KIND_LABEL[kind], "article": aid,
                   "ask": ask_parts, "context": _marks(context, groups), "choices": choices, "sides": sides})

    with _conn() as c:
        for aid in T._ids(tranche):
            g = json.loads((HERE / "labels" / f"{aid}.json").read_text())
            x = json.loads((T.OUT / f"tranche-{tranche}" / run / f"{aid}.json").read_text())["parsed"] or {}
            text = T._text(c, aid)
            body = text.split("\n\n", 1)[1] if "\n\n" in text else text
            a = meta[aid]
            articles[aid] = {"title": a["title"], "site": a["site"], "date": (a["post_date"] or "")[:10], "body": body}
            ge, xe = g["entities"], x.get("entities") or {}
            m = T._match_entities(ge, xe)
            inv = {v: k for k, v in m.items()}

            # job titles: every binding either side made, and every one the labels made the model left loose
            seen = set()
            for side, roles, ents, to_gold in (("gold", g["roles"], ge, lambda i: i), ("model", x.get("roles") or [], xe, inv.get)):
                for r in roles:
                    if not r.get("of"):
                        continue
                    who, of = to_gold(r["who"]), to_gold(r["of"])
                    key = (who or _name(ents, r["who"]), (r["role"] or "").lower(), of or _name(ents, r["of"]))
                    if key in seen:
                        continue
                    seen.add(key)
                    gold_has = any(gr["who"] == who and gr.get("of") == of and gr.get("of") for gr in g["roles"])
                    model_has = any(inv.get(xr.get("who")) == who and inv.get(xr.get("of")) == of and xr.get("of")
                                    for xr in x.get("roles") or [])
                    pf, of_f = _forms(ents, r["who"]), _forms(ents, r["of"])
                    ctx = _window(body, [pf[0] if pf else "", r["role"], of_f[0] if of_f else ""], most=1) or \
                        _window(body, (pf[:1] + [r["role"]]), most=1)
                    ask("role", aid,
                        [{"text": "Does the article say "}, {"text": _name(ents, r["who"]), "mark": "who"},
                         {"text": " holds the title “"}, {"text": r["role"], "mark": "role"}, {"text": "” at "},
                         {"text": _name(ents, r["of"]), "mark": "org"}, {"text": "?"}],
                        ctx, {"who": pf, "role": [r["role"]], "org": of_f},
                        [{"key": "yes", "label": "Yes, it says so"},
                         {"key": "unsaid", "label": "No: the article doesn't say whose"},
                         {"key": "wrong", "label": "No: that's wrong"},
                         {"key": "unsure", "label": "Can't tell"}],
                        {"gold": "yes" if gold_has else "unsaid", "model": "yes" if model_has else "unsaid"}, key)

            # allegations: every event either side called alleged or denied
            for side, evs, ents in (("gold", g["events"], ge), ("model", x.get("events") or [], xe)):
                for ev in evs:
                    if ev.get("modality") not in ("alleged", "denied"):
                        continue
                    whos = [w.get("e") for w in ev.get("who") or [] if isinstance(w, dict)]
                    pf = [f for w in whos for f in _forms(ents, w)[:1]]
                    words = [w for w in re.findall(r"[a-z]{5,}", (ev.get("kind") or "").lower())][:3]
                    ctx = _window(body, pf + words, most=2)
                    other = x.get("events") if side == "gold" else g["events"]
                    ask("allegation", aid,
                        [{"text": "Is this stated as fact, or only alleged? "},
                         {"text": ev.get("kind") or "", "mark": "role"},
                         {"text": " — " + ", ".join(_name(ents, w) for w in whos)}],
                        ctx, {"who": pf, "role": words},
                        [{"key": "happened", "label": "Stated as fact"}, {"key": "alleged", "label": "Alleged"},
                         {"key": "denied", "label": "Denied"}, {"key": "unsure", "label": "Can't tell"}],
                        {side: ev["modality"], ("model" if side == "gold" else "gold"): "?"},
                        (side, ev.get("kind")))

            # kind of article: only where the sides differ
            gt, xt = g["article"]["type"], (x.get("article") or {}).get("type")
            ask("type", aid, [{"text": "What kind of article is this?"}], " ".join(body.split())[:500] + " …", {},
                [{"key": k, "label": TYPE_LABEL.get(k, k.replace("_", " "))} for k in
                 ("news", "opinion", "feature", "review", "market_wrap", "press_release", "live_blog", "sponsored", "stub")],
                {"gold": gt, "model": xt}, "type")

            # what a name is: where the kinds differ
            for gid, xid in m.items():
                gk, xk = ge[gid]["kind"], (xe.get(xid) or {}).get("kind")
                if gk == xk or not ({gk, xk} & MATTERS):
                    continue
                pf = _forms(ge, gid)
                ask("kind", aid, [{"text": "What is "}, {"text": ge[gid]["name"], "mark": "who"},
                                  {"text": " in this article?"}],
                    _window(body, pf[:1], most=1), {"who": pf},
                    [{"key": k, "label": k} for k in ("person", "organisation", "place", "brand", "product", "thing", "work", "event")],
                    {"gold": gk, "model": xk}, gid)

            # tone: where both sides judged the same voice toward the same thing
            gs = {(s["toward"], s["from"]): s for s in g["sentiment"]}
            for s in x.get("sentiment") or []:
                tg = inv.get(s.get("toward"))
                fr = s.get("from") if s.get("from") in ("article", "own") else inv.get(s.get("from"))
                if (tg, fr) not in gs:
                    continue
                gsx = gs[(tg, fr)]
                voice = "the writer" if fr in ("article", "own") else _name(ge, fr)
                ctx = _window(body, [gsx["evidence"], s.get("evidence") or ""], most=2)
                ask("sentiment", aid, [{"text": "How does " + voice + " treat "}, {"text": _name(ge, tg), "mark": "who"},
                                       {"text": "?"}],
                    ctx, {"who": _forms(ge, tg)[:2], "role": [gsx["evidence"], s.get("evidence") or ""]},
                    [{"key": k, "label": k} for k in ("negative", "mixed", "neutral", "positive")],
                    {"gold": gsx["value"], "model": s.get("value")}, (tg, fr))

            # quotes: the model's that the labels lack, the labels' the model missed, a share of the agreed
            xq = [q for q in x.get("quotes") or [] if isinstance(q, dict)]
            model_only = 0
            for side, quotes, ents, others in (("model", xq, xe, g["quotes"]), ("gold", g["quotes"], ge, xq)):
                for q in quotes:
                    hit = any(T._quote_match(q, o) or T._quote_match(o, q) for o in others)
                    if hit and side == "gold":
                        continue        # an agreed quote is asked once, from the model's side
                    if side == "model" and not hit:
                        model_only += 1
                        if model_only > MODEL_ONLY_PER_ARTICLE:
                            continue
                    spk = q.get("speaker")
                    sname = _name(ents, spk) if spk else None
                    qt = re.sub(r"^that\s+", "", q.get("text") or "")
                    ctx = _window(body, [qt[:60]], most=1) or _window(body, [qt[-60:]], most=1)
                    ask("quote", aid,
                        [{"text": "Did "}, {"text": sname, "mark": "who"}, {"text": " say this?"}] if sname else
                        [{"text": "Is this a quote, with nobody named as saying it?"}],
                        ctx, {"quote": [qt[:200]], "who": _forms(ents, spk)[:2] if spk else []},
                        ([{"key": "yes", "label": f"Yes, {sname}"}, {"key": "other", "label": "A quote, but someone else"}]
                         if sname else [{"key": "yes", "label": "Yes, nobody named"},
                                        {"key": "other", "label": "A quote, and it says who"}])
                        + [{"key": "no", "label": "Not a quote"}, {"key": "unsure", "label": "Can't tell"}],
                        {side: "yes", ("gold" if side == "model" else "model"): "yes" if hit else "missing"},
                        (side, qt[:80]))

    qs.sort(key=lambda q: (ORDER.index(q["kind"]), q["article"]))
    return {"set": f"news-gold-{tranche}", "title": f"News golden sample, tranche {tranche}",
            "about": ("Each question is one point the hand labels and the boxes' model read differently, or a check on "
                      "a point they agree on. Answer from the article only: nothing you know from outside it."),
            "made_by": "registers.news.gold.questions", "run": run, "articles": articles, "questions": qs}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
    out = build(int(opt("--tranche", 1)), opt("--run", "run2"))
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / f"{out['set']}.json"
    f.write_text(json.dumps(out, ensure_ascii=False, indent=0) + "\n")
    from collections import Counter
    print(f, len(out["questions"]), dict(Counter(q["kind"] for q in out["questions"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
