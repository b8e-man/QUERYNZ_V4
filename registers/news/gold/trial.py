"""A trial extraction of the golden sample on the boxes' own model, scored against the hand labels.

    python -m registers.news.gold.trial run [--tranche 1] [--run run2] [--url URL] [--model M] [--workers 4]
    python -m registers.news.gold.trial score [--tranche 1] [--run run2]
    python -m registers.news.gold.trial models --urls U1,U2 --model M --run NAME [--tranches 2,...,7] [--per-server 8]
                                               [--part k/n]   another model over the sample, the corpus read's passes

Run 1 (tranche-N/ itself) was one call under json_object. Run 2 onward: the read under a JSON schema whose enums the
server enforces, quotes in a second pass, and the checks after the read (`check`).

Not the reader: a first measure of how far a local model is from the labels, before the reader is designed
(Arthur, 15 November 2026). Outputs are regenerable and land in <work>/live/news-trial/tranche-N/<id>.json; the
score is printed and written beside them as score.json. The model reads the same masked text the labels were typed
from. Article text is data, never instructions.
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import re
import sys
import time
from pathlib import Path

from support import modelclient
from registers.news.gold.sample import HERE, T, _conn, masked

OUT = Path("/home/user/querynzv4-work/live/news-trial")
URL = "http://127.0.0.1:8060/v1/chat/completions"
MODEL = "qwen4exp"
LANE = "news-trial"

PROMPT = """You read one New Zealand news article and record what it says, as data. You never decide who anyone is beyond what the article prints, and you never add anything you know from outside the article.

Answer with ONE JSON object, no words before or after it, with these keys:
- "article": {"type": one of news | opinion | feature | review | market_or_trade | media_release | live_updates | sponsored | stub (news reports an event; opinion argues a view, letters included; a feature is long-form and not about one day's event; a review rates a product or work; market_or_trade reports prices, trading or an industry for its own readers; a media_release is an organisation's own announcement in its own voice; sponsored is paid or advertorial, even when written like news; a stub is cut off or paywalled), "themes": IPTC Media Topic labels broad to specific, "dateline": as printed or null, "wire_credit": the agency or outlet it was first published by, or null}
- "authors": [{"as_printed", "kind": person | staff | agency | organisation, "role_line": the author's own bio or credit line as printed, or null}]
- "entities": {"e1": {"name": the fullest form printed, "kind": person | organisation | place | team | government | brand | product | thing | work | event, "forms": [every way the text prints it, exactly]}, ...}. One entity per real thing; "Mr Smith" and "Smith" are forms of the same person. Pronouns are not forms. A person known only by relation ("his wife", "a spokesperson") is an entity with that as its name. Fictional characters are kind "thing". A thing named after a person (a stadium, a trust, a company) is never a person. "name" is the name alone: never a title, rank or job ("Scott Gemmell", not "Superintendent Scott Gemmell"; the rank goes in roles). An honorific or title before a surname is a role, never a first name: "Justice Palmer" is the person "Palmer" (forms "Justice Palmer", "Palmer") with the role "Justice". A nickname that stands for a team or organisation the article also names properly is a form of that entity, and its name is the proper one. A country's name is the entity it stands for in that sentence (Arthur, tranche 6): in a match report "Fiji" is the team (kind team); "Denmark's ambassador" is Denmark's government (kind government); only a place is kind place. The same printed name can be two entities in one article.
- "roles": [{"who": entity id, "role": the role words exactly as printed, "unit": the department, division, section or programme within the organisation, exactly as printed, or null, "of": the entity id of the organisation the TEXT binds it to, or null, "tense": current | former | acting | interim | incoming | outgoing | designate, "bound_by": apposition | possessive | premodifier | statement | unbound}]. Bind a role to an organisation only when the text itself does ("X chief executive Y", "Y, chief executive of X", "X's chief executive"). If the article does not say whose chief executive someone is, "of" is null and "bound_by" is "unbound". The binding must be printed in the same sentence as the person's name; never carry a role from one sentence to a person named in another, and never give a person the role of someone else in the sentence (an appointed liquidator is not the director whose company failed). "of" is an organisation, team or government, never a place and never a person: "Kāpiti Coast builder" is a descriptor, and "his lawyer" or "her mother" is a relation. Never bind a minister to a party or a detective to the police unless the text prints that binding. A person (the subject) holds a position at an organisation (the object), and the object is always a proper noun printed in full: "University of Fiji School of Nursing", never "School of Nursing", "the board" or "the company"; a generic noun is no binding. A role is a position held: never a verb phrase ("produced by", "led by", "coached by"), never an informal descriptor ("legends", "Graham Lowe's men", "the young and energised side"). A person the article never names ("a Fenz spokesperson", "the board chair") gets no role at all: the words are their name. The role is the position words alone (Arthur, tranche 4): never the organisation's name, its short name or its possessive ("Greens housing spokesperson" is the role "housing spokesperson" of the Green Party; "Opportunity Party leader" is "leader"; "Labour's" or "TOP's" alone is no role at all); never "of X", which says only that someone belongs to X; never a ranking, a record, a result or a past achievement ("ranked No 1", "former champion", "stripped of his title", "the man who helped take Parker to a world title"). A unit inside the organisation goes in "unit", printed in full: "head of the Protected Areas Department" at the National Forest Corporation is the role "head", unit "Protected Areas Department", of the National Forest Corporation; "director of the Philosophy, Politics and Economics programme at the University of Otago" is the role "director", unit "Philosophy, Politics and Economics programme", of the University of Otago. A verb that states a position ("heads the church's social services division") is the role "head" with its unit, and "of" is null when the text never names the organisation. "Relieving" is the tense "acting"; "outgoing" is the tense "outgoing" and is never part of the role ("outgoing chair" is the role "chair"). Tranches 1-6 (Arthur): "incumbent" is no role (it says who holds a seat, not a position); a role is singular ("Christopher Hill, David McGrath and Joanna Dunn, receivers" each hold the role "receiver"); only a verb that is the verb of a position noun gives a role ("heads" is "head", "chairs" is "chair"), never "runs", "leads", "owns" or "manages"; a party's name before "minister" ("former National minister") says which party the minister belongs to, not whose minister: the role is "minister" and "of" is null unless the text names the government.
- "relations": [{"a": id, "says": the words exactly as printed, "b": id}] for relations the text states (owns, subsidiary of, wife of, mother of, lawyer for, donated to, hired). Everything between two people goes here, never in roles.
- "descriptors": [{"who": id, "text": exactly as printed}] for age, town, occupation, nationality.
- "quotes": [{"text": exactly as printed, "form": direct | partial | indirect | mixed, "speaker": id or null, "speaker_as_printed": the words that name the speaker at that quote, "verb": said | told | … , "channel": interview | statement | court | social | earlier_article | release | unknown, "about": [ids]}]. One entry per quoted sentence or run of sentences between attributions. Indirect speech counts: every "X said (that) ...", "X told ... that ...", "according to X, ...", "X believes/argued/warned/explained ..." without quotation marks is an indirect quote; copy the reported words after the verb. If the text does not say who spoke, speaker is null.
- "events": [{"kind": a short plain phrase, "claim": the words of the article that state it, exactly as printed, "who": [{"e": id, "part": their part}], "when": as printed or null, "where": id or null, "modality": happened | alleged | denied | planned | rumoured | possible, "stands_behind": writer | someone_in_article | finding | before_court | denial, "source": the id of who makes the claim, or null}]. "stands_behind" says who vouches for the claim: the writer stating it as plain fact; someone in the article whose claim it is (the article reports that they said it); a court, regulator or official finding; a charge or case before a court, not yet decided; or the article saying it did not happen. A charge, an accusation, a claim by one party against another, "allegedly", "is accused of", "said it was dishonest", "likely offended", or anything a court has not yet decided is alleged, never happened. A denial is its own event with modality denied.
- "numbers": [{"text": exactly as printed, "measures": what it counts, "of": id or null}]
- "sentiment": [{"toward": id, "from": "article" or "own" or the id of a quoted speaker, "value": negative | mixed | neutral | positive, "evidence": the words that carry it, exactly as printed}]. Neutral is the default: record negative or positive only where the words themselves judge (praise, blame, criticism, contempt), never because the facts are bad or good news. The judgement must be aimed at the target itself (Arthur, tranche 4): a place where something bad happens is not judged ("Fiji's HIV epidemic" says nothing against Fiji); how common, large or widespread something is, is a fact, not a judgement; reporting a death or a loss is neutral; criticising a party's policy is a judgement of the party only where the words blame or praise the party. A pronoun ("us", "we", "them") is never a target; "US" is the United States only where the text means the country. A tone's target is a person, an organisation, a team or a government, never a thing (Arthur, tranche 5: "it's a violin not a person"). The writer's tone is the writer's own words: what a quoted person says is that person's tone, never the writer's toward them. A court's or tribunal's finding is a finding, not a tone. Results, listings and the outlet describing itself carry no tone, and an advertisement in the page is not the article. Tranche 6 (Arthur): a person's own feelings ("felt sick to her stomach", "really annoyed") are no tone toward anyone, unless the feeling is aimed at someone ("gutted for Mark" is sympathy: positive toward Mark); bad news for the target ("a major headache for the Reserve Bank", "a major blow") judges nothing about the target; the writer reporting a neutral fact of wrongdoing (a tribunal ordered her to pay) is neutral; a target speaking about itself (its own release, statement or quote) gives no tone toward itself, and "toward" and "from" are never the same entity; criticism the writer reports from others ("signs took aim at the chief executive") is those critics' tone, recorded "from" them where they are an entity, never the writer's. Words of the writer's own that judge ("brash", "all-conquering") are tone; praise and blame together are mixed.
- "traps": [] (leave empty)

Every value marked "exactly as printed" must be copied character for character from the article. A street address shows as [street address]; leave it so."""


#: run 3 (Arthur's verdicts on tranche 1, 16 November 2026): the kinds of article, and who vouches for a claim
TYPES = ("news", "opinion", "feature", "review", "market_or_trade", "media_release", "live_updates", "sponsored", "stub")
BEHIND = ("writer", "someone_in_article", "finding", "before_court", "denial")
_S = {"type": "string"}
_SN = {"type": ["string", "null"]}
_E = lambda *v: {"type": "string", "enum": list(v)}
_OBJ = lambda props, req=None: {"type": "object", "properties": props, "required": req or list(props)}
_ARR = lambda item: {"type": "array", "items": item}
QUOTE = _OBJ({"text": _S, "form": _E("direct", "partial", "indirect", "mixed"), "speaker": _SN, "speaker_as_printed": _SN,
              "verb": _SN, "channel": _E("interview", "statement", "court", "social", "earlier_article", "release",
                                         "document", "unknown"),
              "about": _ARR(_S)})
SCHEMA = _OBJ({
    "article": _OBJ({"type": _E(*TYPES),
                     "themes": _ARR(_S), "dateline": _SN, "wire_credit": _SN}),
    "authors": _ARR(_OBJ({"as_printed": _S, "kind": _E("person", "staff", "agency", "organisation"), "role_line": _SN})),
    "entities": {"type": "object", "additionalProperties": _OBJ({
        "name": _S, "kind": _E("person", "organisation", "place", "team", "government", "brand", "product", "thing",
                               "work", "event"), "forms": _ARR(_S)})},
    "roles": _ARR(_OBJ({"who": _S, "role": _S, "unit": _SN, "of": _SN,
                        "tense": _E("current", "former", "acting", "interim", "incoming", "outgoing", "designate"),
                        "bound_by": _E("apposition", "possessive", "premodifier", "statement", "unbound")})),
    "relations": _ARR(_OBJ({"a": _S, "says": _S, "b": _S})),
    "descriptors": _ARR(_OBJ({"who": _S, "text": _S})),
    "quotes": _ARR(QUOTE),
    "events": _ARR(_OBJ({"kind": _S, "claim": _S, "who": _ARR(_OBJ({"e": _S, "part": _S})), "when": _SN, "where": _SN,
                         "modality": _E("happened", "alleged", "denied", "planned", "rumoured", "possible"),
                         "stands_behind": _E(*BEHIND), "source": _SN})),
    "numbers": _ARR(_OBJ({"text": _S, "measures": _S, "of": _SN})),
    "sentiment": _ARR(_OBJ({"toward": _S, "from": _S, "value": _E("negative", "mixed", "neutral", "positive"),
                            "evidence": _S})),
    "traps": _ARR(_S)})

QUOTE_PROMPT = """You find every quotation in one New Zealand news article: direct (in quotation marks), partial (a few quoted words inside a sentence), indirect (reported speech with no quotation marks: "X said that ...", "X told RNZ ...", "according to X", "X warned/argued/believes/explained ..."), and mixed. A quote needs someone who says it: quotation marks attributed to a speaker, or a verb of saying with its subject. These are never quotes: the writer's own sentences, however opinionated; a turn of phrase in quotation marks with no speaker ("best possible truths", as the PR gurus put it); scare quotes; a name or title in quotation marks; and an article written in an organisation's own voice (a police appeal, a media release) is not a quote of that organisation. Words quoted from a book, report, court decision or post: the speaker is its author or maker, and channel is "document" (or "court", "social"). A group can be the speaker ("Niue health officials"). When the text names the person behind a role ("the coroner, Alexander Ho"), the speaker is that person. You are given the article's entities with their ids; the speaker is one of those ids, or null when the text does not say who spoke. Copy "text" character for character from the article, and only the reported words: never the speaker's name, never "said", "told" or "according to". For indirect speech, the words after "said (that)". An unnamed group is the speaker by the words that name it ("Investigators", "police", "officials"); a statement or release a named person issues is that person speaking, with channel "statement", never "document". When the writer quotes themself (a first-person piece), the speaker is "writer". An advertisement, a promotion or a sponsor's line inside the page is not part of the article: no quotes from it. Answer with ONE JSON object {"quotes": [...]}, each {"text", "form", "speaker", "speaker_as_printed", "verb", "channel", "about": [ids]}."""
QUOTES = _OBJ({"quotes": _ARR(QUOTE)})


def _sentences(text: str) -> list:
    return [x for x in re.split(r"(?<=[.!?\"”])\s+|\n+|(?<=[a-z0-9][.!?])(?=[A-Z])", text) if x.strip()]


#: a party's short name, alone, is no role ("Labour's", "TOP's"); only ever dropped whole, never cut from a role's front
PARTY_WORDS = {"greens", "labour", "national", "act", "nz first", "te pāti māori", "top", "national's"}
#: words that are never a title (Arthur, tranches 1 and 6: "incumbent" says who holds a seat; tranche 6: "runs")
NOT_ROLES = {"incumbent", "the incumbent", "runs", "leads", "owns", "manages", "member", "members"}
#: titles whose plural the reader may print for several people at once (tranche 2: "receivers")
SINGULAR_ROLES = {"receiver", "liquidator", "director", "trustee", "administrator", "manager", "partner", "spokesperson",
                  "co-founder", "founder", "owner", "councillor", "commissioner", "minister", "judge"}


def check(got: dict, text: str) -> dict:
    """The checks after the read (tranche 1 findings; tranche 4: a role that is only the organisation's name or
    possessive, or "of X", is no role, and an organisation's name or possessive leading a role is cut from it): a role's "of" is never a place or a person, and the role,
    the person and the organisation it is bound to are printed in one sentence. A binding that fails is unbound and
    noted, never silently kept; a person-to-person role becomes a relation."""
    ents = got.get("entities") or {}
    sents = [" ".join(x.split()).lower() for x in _sentences(text)]
    forms = lambda i: [f.lower() for f in ((ents.get(i) or {}).get("forms") or []) + [(ents.get(i) or {}).get("name") or ""] if f]
    notes, rels = [], got.setdefault("relations", [])
    keep = []
    for r in got.get("roles") or []:
        role = (r.get("role") or "").strip()
        orgs = [f for i, e in ents.items() if (e or {}).get("kind") in ("organisation", "team", "government")
                for f in forms(i)]
        low = role.lower()
        bare = re.sub(r"[’']s$", "", low).strip()
        if low.startswith("of ") or bare in orgs or bare in PARTY_WORDS or not bare:
            notes.append(f"role dropped: {'membership (of X)' if low.startswith('of ') else 'the organisation, not a title'}")
            continue
        # tranches 1 and 6 (Arthur): "incumbent" is no title, and a person the text never names holds none ("A Hato
        # Hone St John spokesman" is a description, not a person to ask about)
        who = ((ents.get(r.get("who")) or {}).get("name") or "").strip()
        if bare in NOT_ROLES or not who or re.match(r"(a|an|the|one|two|three|several)\s", who, re.I) or not re.search(r"[A-ZĀĒĪŌŪ]", who):
            notes.append("role dropped: " + ("not a title" if bare in NOT_ROLES else "the person is not named"))
            continue
        if bare.endswith("s") and bare[:-1] in SINGULAR_ROLES:     # tranche 2: "receivers" → "receiver"
            r["role"] = role[:-1]
        if bare.startswith("outgoing "):                           # tranche 4: "outgoing" is a tense, not the title
            r["role"], r["tense"] = role[len("outgoing "):], "outgoing"
        for f in sorted(orgs, key=len, reverse=True):         # "Greens housing spokesperson" → "housing spokesperson"
            m = re.match(rf"(the\s+)?{re.escape(f)}(?:[’']s)?\s+(?=\S)", low)
            if m and len(role) > m.end():
                r["role"] = role[m.end():]
                notes.append("role: the organisation's name cut from the front")
                break
        keep.append(r)
    got["roles"] = keep
    for r in keep:
        o = r.get("of")
        if not o:
            continue
        kind = (ents.get(o) or {}).get("kind")
        if kind == "person":
            rels.append({"a": r.get("who"), "says": r.get("role"), "b": o})
            r["of"], r["bound_by"], r["checked"] = None, "unbound", "moved to relations: of is a person"
        elif kind == "place":
            r["of"], r["bound_by"], r["checked"] = None, "unbound", "unbound: of is a place"
        elif not _proper((ents.get(o) or {}).get("name")):
            r["of"], r["bound_by"], r["checked"] = None, "unbound", "unbound: of is not a proper noun"
        elif re.search(r"\bby$", (r.get("role") or "").strip(), re.I):
            r["of"], r["bound_by"], r["checked"] = None, "unbound", "unbound: a verb phrase, not a title"
        elif not any(any(f in s for f in forms(r.get("who"))) and any(f in s for f in forms(o))
                     and (r.get("role") or "").lower() in s for s in sents):
            r["of"], r["bound_by"], r["checked"] = None, "unbound", "unbound: not printed in one sentence"
        else:
            continue
        notes.append(r["checked"])
    flat = " ".join(text.split())
    for q in got.get("quotes") or []:
        t = q.get("text") or ""
        if t and " ".join(t.split()) not in flat and re.match(r"that\s+", t):
            q["text"] = re.sub(r"^that\s+", "", t)
            notes.append("quote: a leading 'that' the text does not hold, dropped")
    tone_check(got, notes, text)
    got["checks"] = notes
    return got


PRONOUNS = {"us", "we", "our", "ours", "them", "they", "their", "you", "your", "i", "me", "my", "he", "she", "him", "her", "it"}


def tone_check(got: dict, notes: list = None, text: str = "") -> dict:
    """Tranche 4 (Arthur): a tone must be aimed at its target. A target known only by a pronoun ("us") is none. (Tried
    and dropped: keeping a tone only where its sentence names the target cost as many right tones as it fixed.)"""
    notes = notes if notes is not None else []
    ents = got.get("entities") or {}
    keep = []
    for t in got.get("sentiment") or []:
        e = ents.get(t.get("toward")) or {}
        fs = [f.lower() for f in (e.get("forms") or []) + [e.get("name") or ""] if f]
        if fs and all(f.strip() in PRONOUNS for f in fs):
            notes.append("tone dropped: the target is a pronoun")
            continue
        keep.append(t)
    got["sentiment"] = keep
    return got


def _proper(name) -> bool:
    """A proper noun: some word after any leading article starts with a capital ("the National Party" yes,
    "the board" and "School of nursing" no: the first content word must be capitalised and the name not a bare
    generic like "Board")."""
    w = re.sub(r"^(the|a|an)\s+", "", (name or "").strip(), flags=re.I).split()
    if not w or not w[0][:1].isupper():
        return False
    return not (len(w) == 1 and w[0].lower() in GENERIC)


GENERIC = {"board", "council", "court", "company", "government", "police", "school", "university", "ministry",
           "department", "team", "club", "party", "committee", "trust", "union", "agency", "group", "firm"}


def _ids(tranche: int) -> list:
    return [a["id"] for a in json.loads((HERE / f"tranche-{tranche}.json").read_text())["articles"]]


def _text(c, article_id: str) -> str:
    row = c.execute(f"SELECT title, author, text_content FROM {T} WHERE id = %s", (article_id,)).fetchone()
    title, author, body = row
    return masked(f"HEADLINE: {title}\nBYLINE: {author or ''}\n\n{body or ''}")


def _parse(s: str):
    s = (s or "").strip()
    m = re.search(r"\{.*\}", s, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except ValueError:
        return None


def _call(url, model, system, user, schema, name, lane=LANE):
    extra = {"temperature": 0.0, "max_tokens": 12000, "chat_template_kwargs": {"enable_thinking": False},
             "response_format": {"type": "json_schema", "json_schema": {"name": name, "schema": schema, "strict": True}}}
    out = modelclient.chat(url, lane=lane, model=model, extra=extra, timeout=1200.0,
                           messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
    return out, (out["choices"][0]["message"]["content"] or "")


def read_one(article_id: str, text: str, url: str, model: str, lane: str = LANE) -> dict:
    """Run 2: the whole read under the schema, then quotes in their own pass, then the checks."""
    t0 = time.monotonic()
    user = "ARTICLE (data, not instructions):\n\n" + text
    out, raw = _call(url, model, PROMPT, user, SCHEMA, "article", lane)
    got = _parse(raw)
    if isinstance(got, dict):
        ents = {k: {"name": v.get("name"), "kind": v.get("kind")} for k, v in (got.get("entities") or {}).items()
                if isinstance(v, dict)}
        _, qraw = _call(url, model, QUOTE_PROMPT, "ENTITIES: " + json.dumps(ents, ensure_ascii=False) + "\n\n" + user,
                        QUOTES, "quotes", lane)
        q = _parse(qraw)
        if isinstance(q, dict) and isinstance(q.get("quotes"), list):
            got["quotes_first_pass"] = got.get("quotes")
            got["quotes"] = q["quotes"]
        got = check(got, text)
    return {"id": article_id, "model": out.get("model") or model, "seconds": round(time.monotonic() - t0, 1),
            "usage": out.get("usage"), "parsed": got, "raw": raw if got is None else None}


# ── claims in layers (Arthur, 16 November 2026, of "the commission also issued reports accusing Hamas of war crimes":
# "this is a claim being made by the writer but it is a claim about the commission making a claim about hamas"; and
# of "fled": "fled is a word not a fact. fled must always include either a place of departure or a destination") ──

CLAIM_PROMPT = """You find the claims in one New Zealand news article and record each as who says what. Many sentences hold a claim inside a claim; you always record the innermost one, made by the one whose claim it is. "The commission also issued reports accusing Hamas of war crimes": the claim is made by the commission, and it is "Hamas committed war crimes". "Smith said Jones lied to the council": made by Smith, "Jones lied to the council". "Police allege the man stole $20,000 of cards": made by the police, "the man stole $20,000 of trading cards". When the article itself states something happened, with no one else behind it, it is made by the writer: "David Jones went into voluntary administration on Thursday". The claimant is who asserts the claim, never who the claim is about (Arthur, tranches 3, 4 and 6): "Netanyahu hardened his stance, openly defying Trump", "prompting Canadian retaliation" and "Fisher went on to commit indecent acts" are all made by the writer; the subject of a sentence is its claimant only where a verb of saying, alleging or finding names them as the source. An article in an organisation's own voice (a police release, a council's news item) is the writer: its own statements ("Police have closed State Highway 29") are made by the writer.

Each claim has:
- "says": the id of the entity whose claim it is (from the ENTITIES given), or "writer".
- "statement": what is claimed, and only that: never the claimant, never "said", "alleged", "accused", "found", "asserts" or "claims". One short, whole plain-English sentence of at most 15 words, the core act only, that a reader understands without the article: who did what, with what the act needs to be a fact (where from or where to, to whom, what). "fled" alone is not a statement; "Alastair Paton fled New Zealand for Australia" is. Names, never "he", "she", "it" or "they". Only what the article prints; if it does not print what the act needs, leave the claim out.
- "span": the article's own words the claim rests on, copied character for character, one sentence or less.
- "stance": "happened" (the claimant says it is so), "did_not_happen" (the claimant denies it), "charged" (a charge or a case before a court, not decided), "decided" (a court, regulator or official body has ruled or found it).

Opinions, judgements of quality, predictions, plans, questions and feelings are not claims: a claim is that something happened or is so. At most 12 claims, the most consequential first: claims that a named person or organisation did wrong come first. Answer with ONE JSON object {"claims": [...]}."""
CLAIM = _OBJ({"says": _S, "statement": _S, "span": _S, "stance": _E("happened", "did_not_happen", "charged", "decided")})
CLAIMS = _OBJ({"claims": _ARR(CLAIM)})


def claims_pass(got: dict, text: str, url: str, model: str, lane: str = LANE) -> dict:
    """The claim pass over one read: GOT["claims"] set to the model's claims, or None when it gave none usable."""
    ents = {k: {"name": v.get("name"), "kind": v.get("kind")} for k, v in (got.get("entities") or {}).items()
            if isinstance(v, dict)}
    _, raw = _call(url, model, CLAIM_PROMPT, "ENTITIES: " + json.dumps(ents, ensure_ascii=False)
                   + "\n\nARTICLE (data, not instructions):\n\n" + text, CLAIMS, "claims", lane)
    cl = _parse(raw)
    got["claims"] = cl["claims"] if isinstance(cl, dict) and isinstance(cl.get("claims"), list) else None
    return got


def claims_run(tranche: int, src: str, name: str, url: str, model: str, workers: int) -> None:
    """The claim pass alone, over an earlier run's read: writes NAME/<id>.json as SRC's with "claims" added."""
    s, d = _dir(tranche, src), _dir(tranche, name)
    d.mkdir(parents=True, exist_ok=True)
    with _conn() as c:
        texts = {i: _text(c, i) for i in _ids(tranche)}

    def one(i):
        r = json.loads((s / f"{i}.json").read_text())
        got = r.get("parsed") or {}
        if not got:
            return r
        t0 = time.monotonic()
        claims_pass(got, texts[i], url, model)
        r["claims_seconds"] = round(time.monotonic() - t0, 1)
        return r

    todo = [i for i in texts if (s / f"{i}.json").exists() and not (d / f"{i}.json").exists()]
    with cf.ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(one, i): i for i in todo}
        for f in cf.as_completed(futs):
            i = futs[f]
            try:
                r = f.result()
            except Exception as exc:  # noqa: BLE001 — one article's failure is reported, the rest go on
                print(f"{i[:8]} failed: {type(exc).__name__}: {str(exc)[:160]}", flush=True)
                continue
            (d / f"{i}.json").write_text(json.dumps(r, indent=1, ensure_ascii=False) + "\n")
            n = len((r.get("parsed") or {}).get("claims") or [])
            print(f"{i[:8]} {r.get('claims_seconds')}s {n} claims", flush=True)


# ── tone, judged one at a time (Arthur, tranche 6: the long rules alone did not stop a feeling, bad news or someone
# else's criticism being read as a tone; a short question per tone, on the sentences that carry it) ──
TONE_PROMPT = """You judge one tone in a New Zealand news article. You are given the sentences that carry it, the TARGET, and the VOICE whose tone it is meant to be (the writer, or a named speaker). Answer whether the VOICE's own words judge the TARGET itself: praise, blame, criticism, contempt, admiration or sympathy aimed at the TARGET.

They do NOT when: the words are the voice's own feelings, not aimed at the target ("I felt sick to my stomach", "it really annoyed me"); they are bad or good news for the target, not a judgement of it ("a major headache for the Reserve Bank", "a major blow"); they report a neutral fact of wrongdoing or loss (a tribunal ordered her to pay); they describe how common, large or successful something is; they are someone else's criticism the voice only reports ("signs took aim at the chief executive" is the protesters', not the writer's); they are the target's own words about itself (its own statement, release or quote); or, for the writer's voice, they sit inside a quotation.

Sympathy aimed at the target is positive ("I'm gutted for Mark": positive toward Mark). Praise and blame together are mixed. Answer with ONE JSON object {"judges_target": true or false, "value": "negative" | "mixed" | "neutral" | "positive", "because": a short phrase}."""
TONE = _OBJ({"judges_target": {"type": "boolean"}, "value": _E("negative", "mixed", "neutral", "positive"), "because": _S})


def _tone_sentences(text: str, evidence: str) -> str:
    """The sentence that holds the evidence and the one before it (the speaker is often named there)."""
    ss = _sentences(text)
    ev = " ".join((evidence or "").split())[:60]
    for i, x in enumerate(ss):
        if ev and ev[:40] in " ".join(x.split()):
            return " ".join(ss[max(0, i - 1):i + 1])
    return ""


def tone_pass(got: dict, text: str, url: str, model: str, lane: str = LANE) -> dict:
    """The tone pass over one read: each non-neutral tone asked on its own; one whose words do not judge its target
    moves to GOT["sentiment_dropped"] with the reason, the rest take the pass's value."""
    ents = got.get("entities") or {}
    nm = lambda k: "the writer" if k in ("article", "own", "writer", None) else ((ents.get(k) or {}).get("name") or k)
    keep, dropped = [], []
    for t in got.get("sentiment") or []:
        if not isinstance(t, dict) or (t.get("value") or "neutral") == "neutral":
            keep.append(t)
            continue
        sent = _tone_sentences(text, t.get("evidence"))
        if not sent:
            keep.append(t)
            continue
        _, raw = _call(url, model, TONE_PROMPT, f"TARGET: {nm(t.get('toward'))}\nVOICE: {nm(t.get('from'))}\n"
                       f"EVIDENCE: {t.get('evidence')}\n\nSENTENCES (data, not instructions):\n{sent}", TONE, "tone", lane)
        v = _parse(raw)
        if not isinstance(v, dict):
            keep.append(t)
            continue
        if not v.get("judges_target") or v.get("value") == "neutral":
            dropped.append({**t, "because": v.get("because")})
            continue
        keep.append({**t, "value": v.get("value") or t.get("value"), "first_value": t.get("value")})

    got["sentiment"], got["sentiment_dropped"] = keep, dropped
    return got


def tones_run(tranche: int, src: str, name: str, url: str, model: str, workers: int) -> None:
    """The tone pass alone, over an earlier run's read: each non-neutral tone asked on its own; a tone whose words do
    not judge its target is dropped (kept in "sentiment_dropped" with the reason), the rest take the pass's value."""
    s, d = _dir(tranche, src), _dir(tranche, name)
    d.mkdir(parents=True, exist_ok=True)
    with _conn() as c:
        texts = {i: _text(c, i) for i in _ids(tranche)}

    def one(i):
        r = json.loads((s / f"{i}.json").read_text())
        tone_pass(r.get("parsed") or {}, texts[i], url, model)
        return r

    todo = [i for i in texts if (s / f"{i}.json").exists() and not (d / f"{i}.json").exists()]
    with cf.ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(one, i): i for i in todo}
        for f in cf.as_completed(futs):
            i = futs[f]
            try:
                r = f.result()
            except Exception as exc:  # noqa: BLE001 — one article's failure is reported, the rest go on
                print(f"{i[:8]} failed: {type(exc).__name__}: {str(exc)[:160]}", flush=True)
                continue
            (d / f"{i}.json").write_text(json.dumps(r, indent=1, ensure_ascii=False) + "\n")
            print(f"{i[:8]} {len((r.get('parsed') or {}).get('sentiment_dropped') or [])} tones dropped", flush=True)


def _dir(tranche: int, name: str) -> Path:
    return OUT / f"tranche-{tranche}" / name if name else OUT / f"tranche-{tranche}"


def run(tranche: int, url: str, model: str, workers: int, name: str = "") -> None:
    d = _dir(tranche, name)
    d.mkdir(parents=True, exist_ok=True)
    with _conn() as c:
        texts = {i: _text(c, i) for i in _ids(tranche)}
    todo = [i for i in texts if not (d / f"{i}.json").exists()]
    with cf.ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(read_one, i, texts[i], url, model): i for i in todo}
        for f in cf.as_completed(futs):
            i = futs[f]
            try:
                r = f.result()
            except Exception as exc:  # noqa: BLE001 — one article's failure is reported, the rest go on
                print(f"{i[:8]} failed: {type(exc).__name__}: {str(exc)[:160]}", flush=True)
                continue
            (d / f"{i}.json").write_text(json.dumps(r, indent=1, ensure_ascii=False) + "\n")
            print(f"{i[:8]} {r['seconds']}s {'ok' if r['parsed'] else 'UNPARSED'}", flush=True)


def run_models(tranches: list, urls: list, model: str, name: str, per_server: int = 8, part: str = "0/1") -> None:
    """Another model over the sample (Arthur, 25 November 2026: "try qwen 3.6 35b a3b and compare it to Flash Next on
    the sample"; "a separate instance of the model on each card and use 8 concurrency"): every article of TRANCHES
    read in the four passes the corpus read uses (read, quotes, claims, tones), PER_SERVER at once on each of URLS, into
    tranche-N/NAME/<id>.json. PART "k/n" takes every n-th article from the k-th, so each box can run its own half."""
    k, n = (int(x) for x in part.split("/"))
    with _conn() as c:
        todo = [(t, i, _text(c, i)) for t in tranches for i in _ids(t)]
    todo = [x for j, x in enumerate(todo) if j % n == k and not (_dir(x[0], name) / f"{x[1]}.json").exists()]
    for t in tranches:
        try:
            _dir(t, name).mkdir(parents=True, exist_ok=True)
        except FileExistsError:   # node1 sees node2's disk over NFS: the other box made it a moment ago
            pass

    def one(job):
        (t, i, text), url = job
        r = read_one(i, text, url, model)
        got = r.get("parsed")
        if isinstance(got, dict):
            t0 = time.monotonic()
            claims_pass(got, text, url, model)
            tone_pass(got, text, url, model)
            r["claims_tones_seconds"] = round(time.monotonic() - t0, 1)
        return t, i, r

    jobs = [(x, urls[j % len(urls)]) for j, x in enumerate(todo)]
    with cf.ThreadPoolExecutor(per_server * len(urls)) as ex:
        futs = {ex.submit(one, j): j for j in jobs}
        for f in cf.as_completed(futs):
            (t, i, _), _u = futs[f]
            try:
                t, i, r = f.result()
            except Exception as exc:  # noqa: BLE001 — one article's failure is reported, the rest go on
                print(f"{t} {i[:8]} failed: {type(exc).__name__}: {str(exc)[:160]}", flush=True)
                continue
            (_dir(t, name) / f"{i}.json").write_text(json.dumps(r, indent=1, ensure_ascii=False) + "\n")
            print(f"{t} {i[:8]} {r['seconds']}+{r.get('claims_tones_seconds')}s {'ok' if r['parsed'] else 'UNPARSED'}", flush=True)


# ── scoring ──

def _n(s) -> str:
    return re.sub(r"[^\w]+", " ", str(s or "").lower().replace("’", "'")).strip()


def _forms(e: dict) -> set:
    return {_n(f) for f in (e.get("forms") or []) + [e.get("name")] if _n(f)}


def _contains(gf: set, xf: set) -> int:
    """A gold person's full name (two words or more) printed inside a got form: "Waikato police Superintendent
    Scott Gemmell" holds "scott gemmell". Counted after exact overlap, so it never outranks a true match."""
    return sum(1 for g in gf if len(g.split()) >= 2 and any(f" {g} " in f" {x} " and g != x for x in xf))


def _match_entities(gold: dict, got: dict) -> dict:
    """gold id -> got id, by shared forms (most overlap wins)."""
    m = {}
    for gid, ge in gold.items():
        gf = _forms(ge)
        best, score = None, 0
        for xid, xe in (got or {}).items():
            if not isinstance(xe, dict):
                continue
            xf = _forms(xe)
            s = len(gf & xf) * 10 + _contains(gf, xf)
            if s > score:
                best, score = xid, s
        if best:
            m[gid] = best
    return m


def _tokset(s) -> set:
    return set(_n(s).split())


def _quote_match(gq, xq) -> bool:
    a, b = _tokset(gq.get("text")), _tokset(xq.get("text"))
    return bool(a) and len(a & b) / max(len(a), 1) >= 0.6


def score_one(gold: dict, got: dict, text: str) -> dict:
    s = {}
    ge, xe = gold["entities"], (got.get("entities") or {}) if isinstance(got, dict) else {}
    if not isinstance(xe, dict):
        xe = {}
    m = _match_entities(ge, xe)
    inv = {v: k for k, v in m.items()}
    s["entities_gold"], s["entities_got"], s["entities_matched"] = len(ge), len(xe), len(m)
    s["entity_kind_agree"] = sum(1 for g, x in m.items() if (xe[x] or {}).get("kind") == ge[g]["kind"])
    people = [g for g, e in ge.items() if e["kind"] == "person"]
    s["people_gold"], s["people_matched"] = len(people), sum(1 for g in people if g in m)
    # invented spans: forms, quotes, roles the text does not hold
    t = " ".join(text.split())
    spans = [f for e in xe.values() if isinstance(e, dict) for f in (e.get("forms") or [])]
    spans += [q.get("text") for q in (got.get("quotes") or []) if isinstance(q, dict)]
    spans += [r.get("role") for r in (got.get("roles") or []) if isinstance(r, dict)]
    spans = [x for x in spans if isinstance(x, str) and x.strip()]
    s["spans_got"] = len(spans)
    s["spans_not_in_text"] = sum(1 for x in spans if " ".join(x.split()) not in t)
    # roles: binding precision on roles the model bound
    gb = {(r["who"], _n(r["role"])): r for r in gold["roles"]}
    bound = [r for r in (got.get("roles") or []) if isinstance(r, dict) and r.get("of")]
    s["roles_bound_got"] = len(bound)
    right = 0
    for r in bound:
        g = inv.get(r.get("who"))
        cands = [x for (w, _), x in gb.items() if w == g]
        if any(x["of"] and m.get(x["of"]) == r.get("of") for x in cands):
            right += 1
    s["roles_bound_right"] = right
    s["roles_gold"] = len(gold["roles"])
    s["roles_found"] = sum(1 for r in gold["roles"] if any(inv.get(x.get("who")) == r["who"] for x in (got.get("roles") or []) if isinstance(x, dict)))
    # quotes: recall and speaker accuracy
    gq, xq = gold["quotes"], [q for q in (got.get("quotes") or []) if isinstance(q, dict)]
    s["quotes_gold"], s["quotes_got"] = len(gq), len(xq)
    found = spk = 0
    for q in gq:
        hit = next((x for x in xq if _quote_match(q, x)), None)
        if hit:
            found += 1
            if (q["speaker"] is None and not hit.get("speaker")) or (q["speaker"] and m.get(q["speaker"]) == hit.get("speaker")):
                spk += 1
    s["quotes_found"], s["quote_speaker_right"] = found, spk
    # events: alleged must not become happened
    galleged = [e for e in gold["events"] if e["modality"] == "alleged"]
    xev = [e for e in (got.get("events") or []) if isinstance(e, dict)]
    s["events_gold"], s["events_got"] = len(gold["events"]), len(xev)
    s["alleged_gold"] = len(galleged)
    s["alleged_kept"] = sum(1 for e in galleged if any(x.get("modality") in ("alleged", "denied") and
                                                       {m.get(w["e"]) for w in e["who"]} & {w.get("e") for w in (x.get("who") or []) if isinstance(w, dict)}
                                                       for x in xev))
    # article type
    s["type_right"] = int(((got.get("article") or {}).get("type") if isinstance(got.get("article"), dict) else None) == gold["article"]["type"])
    # sentiment agreement where both have (toward, from)
    gs = {(x["toward"], x["from"]): x["value"] for x in gold["sentiment"]}
    agree = tot = 0
    for x in (got.get("sentiment") or []):
        if not isinstance(x, dict):
            continue
        g = inv.get(x.get("toward"))
        f = x.get("from") if x.get("from") in ("article", "own") else inv.get(x.get("from"))
        if (g, f) in gs:
            tot += 1
            agree += int(gs[(g, f)] == x.get("value"))
    s["sentiment_compared"], s["sentiment_agree"] = tot, agree
    return s


def score(tranche: int, name: str = "") -> dict:
    d = _dir(tranche, name)
    per, total = {}, {}
    with _conn() as c:
        for i in _ids(tranche):
            g = HERE / "labels" / f"{i}.json"
            x = d / f"{i}.json"
            if not g.exists() or not x.exists():
                continue
            got = json.loads(x.read_text()).get("parsed")
            if not isinstance(got, dict):
                per[i] = {"unparsed": 1}
                total["unparsed"] = total.get("unparsed", 0) + 1
                continue
            s = score_one(json.loads(g.read_text()), got, _text(c, i))
            per[i] = s
            for k, v in s.items():
                total[k] = total.get(k, 0) + v
    out = {"tranche": tranche, "articles": len(per), "total": total, "per_article": per}
    (d / "score.json").write_text(json.dumps(out, indent=1) + "\n")
    return out


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    opt = lambda k, dflt: argv[argv.index(k) + 1] if k in argv else dflt
    tranche = int(opt("--tranche", 1))
    if argv[:1] == ["run"]:
        run(tranche, opt("--url", URL), opt("--model", MODEL), int(opt("--workers", 4)), opt("--run", ""))
        return 0
    if argv[:1] == ["models"]:
        run_models([int(x) for x in opt("--tranches", "2,3,4,5,6,7").split(",")], opt("--urls", URL).split(","),
                   opt("--model", MODEL), opt("--run", "other"), int(opt("--per-server", 8)), opt("--part", "0/1"))
        return 0
    if argv[:1] == ["tones"]:
        tones_run(tranche, opt("--from", "run6"), opt("--run", "run7"), opt("--url", URL), opt("--model", MODEL),
                  int(opt("--workers", 4)))
        return 0
    if argv[:1] == ["claims"]:
        claims_run(tranche, opt("--from", "run3"), opt("--run", "run6"), opt("--url", URL), opt("--model", MODEL),
                   int(opt("--workers", 4)))
        return 0
    if argv[:1] == ["score"]:
        t = score(tranche, opt("--run", ""))["total"]
        pct = lambda a, b: f"{100 * t.get(a, 0) / t[b]:.0f}%" if t.get(b) else "n/a"
        print(json.dumps(t, indent=1))
        print("people found", pct("people_matched", "people_gold"), "| entities found", pct("entities_matched", "entities_gold"),
              "| spans not in text", pct("spans_not_in_text", "spans_got"), "| roles bound right", pct("roles_bound_right", "roles_bound_got"),
              "| quotes found", pct("quotes_found", "quotes_gold"), "| quote speaker right", pct("quote_speaker_right", "quotes_found"),
              "| alleged kept alleged", pct("alleged_kept", "alleged_gold"), "| sentiment agree", pct("sentiment_agree", "sentiment_compared"))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
