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


def _named_before(text: str, ctx: str, names: list, back: int = 3) -> str:
    """The context, with the nearest paragraph before it that names the speaker when the context itself only says
    "he said": up to BACK paragraphs back. The context alone when none does."""
    low = [n.lower() for n in names if n]
    if not ctx or not low or any(n in ctx.lower() for n in low):
        return ctx
    ps = _paras(text)
    first = ctx.split(" … ")[0][:60]
    at = next((i for i, p in enumerate(ps) if first in p), None)
    if at is None:
        return ctx
    for j in range(at - 1, max(-1, at - 1 - back), -1):
        if any(n in ps[j].lower() for n in low):
            u = ps[j] if len(ps[j]) <= 600 else next((x for x in T._sentences(ps[j]) if any(n in x.lower() for n in low)), ps[j])
            return u + " … " + ctx
    return ctx


def _marks(context: str, groups: dict) -> list:
    """[{"text", "mark"}] runs: each group's words marked where they fall (longest first, no overlap)."""
    spans = []
    for mark, words in groups.items():
        for w in sorted({w for w in words if w}, key=len, reverse=True):
            for m in re.finditer((r"(?<!\w)" if w[:1].isalnum() else "") + re.escape(w) + (r"(?!\w)" if w[-1:].isalnum() else ""), context, re.I):
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
            cats, url = c.execute("SELECT categories, news_url FROM old_incoming_news_private.articles WHERE id = %s",
                                  (aid,)).fetchone()
            art = x.get("article") or {}
            # Arthur, 17 November 2026: "I need to know what you have tagged an article inside the reviewer and also
            # what the article is tagged by the website metadata"
            articles[aid] = {"title": a["title"], "site": a["site"], "date": (a["post_date"] or "")[:10], "body": body,
                             "tags": {"model_type": TYPE_LABEL2.get(art.get("type"), art.get("type")),
                                      "model_themes": art.get("themes") or [],
                                      "model_wire": art.get("wire_credit"),
                                      "site_categories": list(cats or []), "site_sections": _sections(url)}}
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


# ── tranche 2 onward: the model's read alone, asked of Arthur (16 November 2026: his verdicts on tranche 1 matched the
# hand labels no better than the model, so the labels are his answers). Questions redesigned from his notes: a title
# question says what kind of "no" it is; a quote question asks who is speaking, the writer and a document among the
# answers; a claim question asks who stands behind it, in the article's own words. Every question is judged on the
# sentence shown, and says so.

ORDER2 = ["claim", "role", "quote", "type", "sentiment"]
LABEL2 = {"role": "Job title", "claim": "Who claims what", "quote": "Who is speaking",
          "type": "Kind of article", "sentiment": "Tone"}
TYPE_LABEL2 = {"news": "news report", "opinion": "opinion, column or letter", "feature": "feature (long-form)",
               "review": "review (rates a product or work)", "market_or_trade": "market or trade report",
               "media_release": "media release (an organisation's own voice)", "live_updates": "live updates",
               "sponsored": "paid or advertorial", "stub": "cut off or paywalled"}
BEHIND_LABEL = {"writer": "The writer, as a plain fact", "someone_in_article": "Someone in the article: it's their claim",
                "finding": "A court, regulator or official finding", "before_court": "Charged or before a court, not yet decided",
                "denial": "The article says it didn't happen"}
#: of the model's quotes, at most QUOTES_PER_ARTICLE, the riskiest first (unattributed, from a document, reported)
QUOTES_PER_ARTICLE = 2
#: claims the model says the writer vouches for, at most this many per article (the rest are all asked)
WRITER_CLAIMS = 1
#: claims asked per article, at most
CLAIMS_PER_ARTICLE = 4
#: Arthur, 18 November 2026: tone scored well but wants more samples; neutral tones are asked too
TONE_PER_ARTICLE = 3
#: the most questions one article gives, from tranche 5 (Arthur, 18 November 2026: tranche 4 showed "many of the same
#: articles"; 32 articles gave 283 questions, up to 17 each). Taken one kind at a time in ORDER2, so an article's
#: questions differ in kind before any kind repeats
PER_ARTICLE = 3
#: a quoted fragment under this many words is a name, term or turn of phrase, not speech (Arthur's tranche 3 notes)
QUOTE_MIN_WORDS = 4


#: Arthur, 16 November 2026, of "fled — Alastair Paton": "fled is a word not a fact. fled must always include either a
#: place of departure or a destination". A claim is asked only when it reads as a whole statement: someone did
#: something, with what the act needs (a place, a thing, a person), not a bare verb, a fragment or a headline.
_CLAIM_VERB = re.compile(r"\b(is|are|was|were|be|been|has|have|had|will|would|could|can|may|might|must|should|did|does|do|"
                         r"\w+ed|\w+s|said|says|told|went|made|took|left|fled|got|gave|won|lost|ran|came|"
                         r"became|began|found|held|kept|met|paid|put|sent|set|sold|spent|stood|struck|cut|hit|led)\b")
_CLAIM_OPENS_ON_VERB = re.compile(r"^(is|are|was|were|has|have|had|will|would|did|does|do|been|being|to|and|but|or|"
                                  r"who|which|that|after|before|when|while|as|earlier|later|also|then|now|still|yet|caught|seen|found|charged|accused|arrested|alleged|sentenced|convicted|given|taken|held|known|told|sold|left|\w+ed|\w+ing|\w+ly)\b", re.I)


def _whole_claim(claim: str) -> bool:
    words = claim.split()
    first = words[0].lower() if words else ""
    irregular = _CLAIM_VERB.fullmatch(first) and not re.fullmatch(r"\w+(ed|s)", first)     # "went on to…": no subject
    return (len(words) >= 6 and not _CLAIM_OPENS_ON_VERB.match(claim) and not irregular
            and bool(_CLAIM_VERB.search(" ".join(words[1:]))) and not _POINTS_BACK.search(claim))


#: Arthur, tranche 3: "to be a useful claim we need to know which payments ... 'those' needs a specified target";
#: "'the tag' need[s] a specified target". A statement that points back to something it does not name is not whole.
_POINTS_BACK = re.compile(r"\b(those|these|such|this)\s+(?!year\b|week\b|month\b|morning\b|afternoon\b|evening\b|season\b|is\b|was\b)[a-z]+", re.I)


#: Arthur, 16 November 2026: "None of the answers I am giving are golden corpus candidates. we are refining your ability
#: to ask so we need to find the bad review questions". Every question carries this answer, on key 0.
BAD = {"key": "bad", "label": "Bad question: unclear, incomplete, or I can't answer it as asked"}


#: Arthur, 17 November 2026: "the tags say what the article is in many cases these should be left out of the sample
#: unless there is a reason you want them in". Where the site's own metadata names the kind of article, the kind is
#: not asked; the model's answer is checked against the site's word instead. Only tags that leave no doubt.
_SITE_TYPE = [
    ("sponsored", r"sponsored|advertorial|partner-content|brand-?insight"),
    ("opinion", r"^(opinion|comment|columnists?|letters|editorial|analysis|perspectives?)$"),
    ("live_updates", r"^live(-updates|-blog)?$"),
    ("review", r"^(reviews?|readingroom|book-reviews?)$"),
]


def site_type(site, cats, url, title, body) -> str | None:
    tags = [str(t).strip().lower() for t in list(cats or []) + _sections(url)]
    for kind, pat in _SITE_TYPE:
        if any(re.search(pat, t) for t in tags):
            return kind
    if site == "police.govt.nz" and "/news/release/" in (url or ""):
        return "media_release"
    if site == "scoop.co.nz" and re.search(r"Find more from .+ on InfoPages\.?\s*$", body or ""):
        return "media_release"              # Scoop's own marker of a release posted by its maker
    if re.match(r"(?i)live\b|.*\blive( updates|:)", title or ""):
        return "live_updates"
    return None


def _sections(url) -> list:
    """The site's own sections, from the article's address: every path step but the last (the slug), less dates,
    numbers and plumbing ("/sport/motorsport/formula-1/<slug>" gives sport, motorsport, formula-1)."""
    steps = re.sub(r"^https?://[^/]+", "", url or "").strip("/").split("/")[:-1]
    return [x for x in steps if x and x.count("-") < 3 and not re.fullmatch(r"[\d.]+|v\d.*|api|stuff|stories|story|article|release|[A-Z]{1,2}\d+", x)]


def _spread(qs: list, most: int, skipped: dict) -> list:
    """At most `most` questions an article: each round takes the next kind (ORDER2) the article still has, so its
    questions differ in kind before a kind repeats. What is left over is counted, never asked."""
    by = {}
    for q in qs:
        by.setdefault(q["article"], []).append(q)
    out = []
    for aid, mine in by.items():
        pools = {k: [q for q in mine if q["kind"] == k] for k in ORDER2}
        took = []
        while len(took) < most and any(pools.values()):
            for k in ORDER2:
                if pools[k] and len(took) < most:
                    took.append(pools[k].pop(0))
        out += took
        left = len(mine) - len(took)
        if left:
            skipped["over the per-article limit"] = skipped.get("over the per-article limit", 0) + left
    return out


def build2(tranche: int, run: str = "run6") -> dict:
    from registers.news.gold import trial as T2
    meta = {a["id"]: a for a in json.loads((HERE / f"tranche-{tranche}.json").read_text())["articles"]}
    articles, qs, skipped = {}, [], {}

    def ask(kind, aid, key, ask_parts, context, groups, choices, model):
        if not context:
            skipped[kind] = skipped.get(kind, 0) + 1
            return
        marked = _marks(context, groups)
        # Arthur, 17 November 2026: text shown "irrelevant to the question". The text shown is the evidence the model
        # cited; when it does not name who the question is about, the model cited the wrong text. That is a reading
        # fault, counted here, and never asked.
        if kind in ("sentiment", "claim") and groups.get("who") and not any(p.get("mark") == "who" for p in marked):
            skipped[f"{kind} (evidence names nobody asked about)"] = skipped.get(f"{kind} (evidence names nobody asked about)", 0) + 1
            return
        need = {"claim": "role", "quote": "quote"}.get(kind)
        if need and not any(p.get("mark") == need for p in marked):
            skipped[kind] = skipped.get(kind, 0) + 1          # the words asked about are not in the text shown
            return
        qs.append({"id": _qid(kind, aid, key), "kind": kind, "label": LABEL2[kind], "article": aid, "ask": ask_parts,
                   "context": marked, "choices": choices + ([{"key": "unsure", "label": "Can't tell from this text"}] if len(choices) < 9 else [])
                   + [BAD],
                   "sides": {"model": model}})

    with _conn() as c:
        for aid in T2._ids(tranche):
            f = T2.OUT / f"tranche-{tranche}" / run / f"{aid}.json"
            if not f.exists():
                continue
            x = json.loads(f.read_text())["parsed"] or {}
            if not x:
                continue          # an article the model could not read: nothing to ask
            text = T2._text(c, aid)
            body = text.split("\n\n", 1)[1] if "\n\n" in text else text
            a = meta[aid]
            cats, url = c.execute("SELECT categories, news_url FROM old_incoming_news_private.articles WHERE id = %s",
                                  (aid,)).fetchone()
            art = x.get("article") or {}
            # Arthur, 17 November 2026: "I need to know what you have tagged an article inside the reviewer and also
            # what the article is tagged by the website metadata"
            articles[aid] = {"title": a["title"], "site": a["site"], "date": (a["post_date"] or "")[:10], "body": body,
                             "tags": {"model_type": TYPE_LABEL2.get(art.get("type"), art.get("type")),
                                      "model_themes": art.get("themes") or [],
                                      "model_wire": art.get("wire_credit"),
                                      "site_categories": list(cats or []), "site_sections": _sections(url)}}
            xe = x.get("entities") or {}

            for r in x.get("roles") or []:
                if not r.get("of"):
                    continue
                pf, of_f = _forms(xe, r["who"]), _forms(xe, r["of"])
                need = [pf[-1] if pf else "", r["role"], of_f[-1] if of_f else ""]      # the shortest forms: the likeliest printed
                ctx = _window(body, need, need_all=True, most=1)
                ask("role", aid, (r["who"], r["role"], r["of"]),
                    [{"text": "Does this text say "}, {"text": _name(xe, r["who"]), "mark": "who"}, {"text": " holds the title “"},
                     {"text": r["role"], "mark": "role"}, {"text": "”"}]
                    + ([{"text": " in the "}, {"text": r["unit"]}] if r.get("unit") else [])
                    + [{"text": " at "}, {"text": _name(xe, r["of"]), "mark": "org"}, {"text": "?"}],
                    ctx, {"who": pf, "role": [r["role"]], "org": of_f},
                    [{"key": "yes", "label": "Yes"},
                     {"key": "not_title", "label": "No: not a title (a verb, a description, a nickname)"},
                     {"key": "not_org", "label": "No: wrong organisation, or not a proper name"},
                     {"key": "unsaid", "label": "No: this text doesn't say so"}], "yes")

            if x.get("claims") is not None:        # run 5 on: claims in layers, each "who says what"
                writer = asked = 0
                for cl in x["claims"]:
                    if asked >= CLAIMS_PER_ARTICLE:
                        break
                    span, stmt, says = (cl.get("span") or "").strip(), (cl.get("statement") or "").strip().rstrip("."), cl.get("says")
                    if not span or not stmt:
                        continue
                    if says == "writer":
                        writer += 1
                        if writer > WRITER_CLAIMS:
                            continue
                    ctx = _window(body, [span[:80]], most=1)
                    if says != "writer":
                        ctx = _named_before(body, ctx, _forms(xe, says))
                    verb = {"charged": "charging", "decided": "finding"}.get(cl.get("stance"), "saying")
                    # short and laid out in lines (Arthur: the Israel questions were "too long and convoluted"): the
                    # claimant by the shortest name the sentence prints, the statement on its own line
                    flat = " ".join(ctx.split()).lower()
                    printed = [f for f in _forms(xe, says) if f.lower() in flat] if says != "writer" else []
                    # Arthur, tranche 3: "it is Senior Constable Paul Stanko speaking": the full name and title shown,
                    # the printed form marked in the text
                    short = (_name(xe, says) or (min(printed, key=len) if printed else "")) if says != "writer" else ""
                    head = {"charged": "Charges", "decided": "Finds"}.get(cl.get("stance"), "Says")
                    who = ([{"text": "Who: "}, {"text": "the writer, as plain fact", "mark": "who"}] if says == "writer"
                           else [{"text": "Who: "}, {"text": short, "mark": "who"}])
                    n0 = len(qs)
                    ask("claim", aid, ("claim2", stmt[:80]),
                        who + [{"text": f"\n{head}: "}, {"text": stmt, "mark": "role"}, {"text": "\nDoes the text show this?"}],
                        ctx, {"role": [span], "who": _forms(xe, says)[:3] if says != "writer" else []},
                        [{"key": "yes", "label": "Yes"},
                         {"key": "other", "label": "No: it's someone else's claim"} if says != "writer" else
                         {"key": "other", "label": "No: it's someone in the article's claim, not the writer's"},
                         {"key": "writer", "label": "No: the writer states it as plain fact"} if says != "writer" else
                         {"key": "opinion", "label": "No: it's the writer's opinion, a prediction or a plan, not a fact"},
                         {"key": "changed", "label": "No: the statement says more, less or other than the text"},
                         {"key": "unsaid", "label": "No: the text doesn't say this at all"}], "yes")
                    asked += len(qs) > n0
            risk = lambda q: (0 if not q.get("speaker") else 1 if q.get("channel") == "document" else
                              2 if q.get("form") in ("indirect", "mixed") else 3)
            quotes = sorted((q for q in x.get("quotes") or [] if isinstance(q, dict) and (q.get("text") or "").strip()), key=risk)
            short = [q for q in quotes if len(q["text"].split()) < QUOTE_MIN_WORDS]
            if short:
                skipped["quote (a term, not speech)"] = skipped.get("quote (a term, not speech)", 0) + len(short)
            quotes = [q for q in quotes if len(q["text"].split()) >= QUOTE_MIN_WORDS]
            for q in quotes[:QUOTES_PER_ARTICLE]:
                t = q["text"].strip()
                spk = q.get("speaker")
                sname = _name(xe, spk) if spk else None
                ctx = _window(body, [t[:60]], most=1) or _window(body, [t[-60:]], most=1)
                # tranche 4: a person's statement the model called a document was the person speaking ("speaker
                # included in statement"): the speaker is asked, not the channel; a document only when nobody is named
                if spk == "writer":
                    model, spk, sname = "writer", None, None
                else:
                    model = "yes" if spk else ("document" if q.get("channel") == "document" else "nobody")
                ask("quote", aid, ("quote", t[:80]),
                    [{"text": "Who is speaking the marked words?"}],
                    ctx, {"quote": [t[:300]], "who": _forms(xe, spk)[:3] if spk else []},
                    ([{"key": "yes", "label": sname}] if sname else [])
                    + [{"key": "other", "label": "Someone else in the article"},
                       {"key": "writer", "label": "The writer: not a quote"},
                       {"key": "document", "label": "A book, report or document" + (f" ({sname})" if sname else "")},
                       {"key": "nobody", "label": "A quote, but nobody is named"},
                       {"key": "span", "label": "A quote, but the marking takes in the speaker or misses words"}],
                    model)

            typ = (x.get("article") or {}).get("type")
            lead = " ".join(body.split())[:700]
            told = site_type(a["site"], cats, url, a["title"], body)
            articles[aid]["tags"]["site_type"] = told
            if told:                      # the site already says what it is: checked against the model, not asked
                skipped["type (the site says)"] = skipped.get("type (the site says)", 0) + 1
            elif tranche >= 5:            # Arthur, 18 November 2026: "let's get rid of the article types question.
                skipped["type (the model's guess stands)"] = skipped.get("type (the model's guess stands)", 0) + 1
            else:                         # The model can just guess those"
              ask("type", aid, "type", [{"text": "What kind of article is this?"}],
                  f"{a['title']} — {lead} …", {},
                  [{"key": k, "label": v} for k, v in TYPE_LABEL2.items()], typ)

            tones = [s for s in x.get("sentiment") or [] if isinstance(s, dict)]
            tones = sorted(tones, key=lambda s: s.get("value") == "neutral")[:TONE_PER_ARTICLE]
            for s in tones:
                voice = "the writer" if s.get("from") in ("article", "own") else _name(xe, s.get("from"))
                ev_ = s.get("evidence") or ""
                ctx = _window(body, [ev_[:80]], most=1)
                if voice != "the writer":
                    ctx = _named_before(body, ctx, _forms(xe, s.get("from")))
                ask("sentiment", aid, ("tone", s.get("toward"), s.get("from")),
                    [{"text": "In this text, how does " + voice + " treat "}, {"text": _name(xe, s.get("toward")), "mark": "who"},
                     {"text": "?"}],
                    ctx, {"who": _forms(xe, s.get("toward"))[:3] + ([] if voice == "the writer" else _forms(xe, s.get("from"))[:2]),
                          "role": [ev_]},
                    [{"key": k, "label": k} for k in ("negative", "mixed", "neutral", "positive")], s.get("value"))

    if tranche >= 5:
        qs = _spread(qs, PER_ARTICLE, skipped)
    qs.sort(key=lambda q: (ORDER2.index(q["kind"]), q["article"]))
    return {"set": f"news-gold-{tranche}", "title": f"News golden sample, tranche {tranche}",
            "about": ("Every question is about what the boxes' model read, and is judged on the text shown alone. "
                      "If no answer fits, note it and pick the nearest."),
            "made_by": "registers.news.gold.questions", "run": run, "skipped": skipped, "articles": articles, "questions": qs}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
    tranche = int(opt("--tranche", 1))
    out = build(tranche, opt("--run", "run2")) if tranche == 1 else build2(tranche, opt("--run", "run6"))
    if out.get("skipped"):
        print("skipped (no sentence shows it):", out["skipped"])
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / f"{out['set']}.json"
    f.write_text(json.dumps(out, ensure_ascii=False, indent=0) + "\n")
    from collections import Counter
    print(f, len(out["questions"]), dict(Counter(q["kind"] for q in out["questions"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
