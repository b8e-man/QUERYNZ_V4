"""The gates after the news reader's model (Arthur, 25 November 2026): rules that trade volume for accuracy, applied to
the first read of the corpus and never to a golden-sample tranche ("let's not apply these rules to tranche 8. I want
to judge liberally, but let's apply these rules to the first read we do").

Each gate looks only at the model's record and the article text: no model call. Every item comes back with a verdict,
{"kept": bool, "rule": the rule that decided it}, so what a gate drops is counted and can be read again; nothing is
deleted from the reading. Measured on Arthur's judged answers of tranches 2 to 7 by
`python -m registers.news.gold.gates_check` (25 November 2026, model right among judged items before → after, share
of all model output kept):

  quotes   47% → 97%, 69% kept   the speaker named within 250 characters of the words, and not from a document
                                 (a document's words are kept apart as a citation, not dropped)
  roles    85% → 96%, 70% kept   a title word, no "of" or possessive, no leading "former", "outgoing" ...
  claims   88% → 95%, 67% kept   the claimant and a verb of saying or finding in the span's own sentence; the
                                 writer's own claims pass
  tones    84% → 85%, 83% kept   evidence of four words or more (a tone's errors are judgements, which no rule sees)

The title words and the attribution verbs were tuned on those same answers, so the first ungated tranche after
(tranche 8) is the clean measure.
"""
from __future__ import annotations

import re

GATES = "registers.news.gates 1"

#: how far either side of a quote's words its speaker must be named (characters)
SPEAKER_WINDOW = 250
#: a tone's evidence under this many words is a name or a label, not words that judge ("acclaimed director" kept;
#: "blockbuster" not)
TONE_MIN_WORDS = 4

ROLE_HEAD = re.compile(
    r"(?i)\b(chief|executive|officer|director|chair|chairman|chairwoman|chairperson|president|minister|spokesperson|"
    r"spokesman|spokeswoman|manager|mayor|councillor|judge|justice|commissioner|secretary|leader|head|founder|"
    r"co-founder|owner|partner|principal|professor|lecturer|economist|analyst|editor|reporter|coach|captain|"
    r"inspector|sergeant|constable|superintendent|detective|commander|governor|deputy|member|mp|trustee|board|"
    r"adviser|advisor|consultant|lawyer|barrister|solicitor|counsel|doctor|surgeon|nurse|researcher|scientist|"
    r"strategist|planner|engineer|ambassador|envoy|registrar|coroner|chancellor|dean|vice|general|ceo|cfo|coo|cto|"
    r"md|gm|candidate|representative|convenor|coordinator|co-ordinator|administrator|treasurer|ranger)\b")
ROLE_OF = re.compile(r"(?i)\bof\b|'s\b|’s\b")
ROLE_DESCRIPTOR = re.compile(r"(?i)^(former|outgoing|incoming|acting|interim|then|ex-|retired|late|new|legend|veteran)\b")
ATTRIB = re.compile(
    r"(?i)\b(said|says|say|told|tells|added|adds|asked|explained|according to|wrote|writes|stated|states|noted|warned|"
    r"warns|argued|argues|claimed|claims|insisted|responded|replied|admitted|announced|confirmed|believes|believe|"
    r"alleged|alleges|accused|accuses|charged|found|ruled|concluded|reported|reports|denied|denies|called|calls|"
    r"described|describes|suggested|suggests|urged|urges|wants|thinks|criticised|praised|blamed|estimated|expects|"
    r"predicted|revealed|show|shows|showed)\b")


def forms(ents: dict, eid) -> list:
    """Every way the text prints an entity, longest first (one-letter forms left out)."""
    e = (ents or {}).get(eid) or {}
    return sorted({f for f in (e.get("forms") or []) + [e.get("name") or ""] if f and len(f) > 1}, key=len, reverse=True)


def sentence_of(text: str, span: str) -> str:
    """The sentence of TEXT that holds SPAN (by its first 60 characters), or "" when the text does not hold it."""
    i = text.find(span[:60])
    if i < 0:
        return ""
    a = max(text.rfind(". ", 0, i), text.rfind("\n", 0, i)) + 1
    ends = [x for x in (text.find(". ", i + len(span)), text.find("\n", i + len(span))) if x >= 0]
    return text[a:(min(ends) if ends else len(text)) + 1]


def quote(q: dict, ents: dict, text: str) -> dict:
    t = (q.get("text") or "").strip()
    if q.get("channel") == "document":
        return {"kept": False, "rule": "a document's words: a citation, not speech", "citation": True}
    spk = q.get("speaker")
    if not spk or spk == "writer":
        return {"kept": False, "rule": "nobody named as speaking" if not spk else "the writer's own words"}
    i = text.find(t[:60]) if t else -1
    if i < 0:
        return {"kept": False, "rule": "the words are not in the text"}
    window = text[max(0, i - SPEAKER_WINDOW): i + len(t) + SPEAKER_WINDOW]
    if not any(f in window for f in forms(ents, spk)):
        return {"kept": False, "rule": f"the speaker is not named within {SPEAKER_WINDOW} characters"}
    return {"kept": True, "rule": "speaker named beside the words"}


def role(r: dict, ents: dict, text: str) -> dict:
    words = (r.get("role") or "").strip()
    if ROLE_OF.search(words):
        return {"kept": False, "rule": "an 'of' or a possessive in the title"}
    if ROLE_DESCRIPTOR.search(words):
        return {"kept": False, "rule": "a descriptor leads the title"}
    if not ROLE_HEAD.search(words):
        return {"kept": False, "rule": "no title word"}
    return {"kept": True, "rule": "a title word"}


def claim(cl: dict, ents: dict, text: str) -> dict:
    says = cl.get("says")
    if says == "writer":
        return {"kept": True, "rule": "the writer's own claim"}
    sent = sentence_of(text, (cl.get("span") or "").strip())
    if not sent:
        return {"kept": False, "rule": "the span is not in the text"}
    if not any(f in sent for f in forms(ents, says)):
        return {"kept": False, "rule": "the claimant is not named in the span's sentence"}
    if not ATTRIB.search(sent):
        return {"kept": False, "rule": "no verb of saying or finding in the span's sentence"}
    return {"kept": True, "rule": "claimant and attribution in one sentence"}


def tone(s: dict, ents: dict, text: str) -> dict:
    if len((s.get("evidence") or "").split()) < TONE_MIN_WORDS:
        return {"kept": False, "rule": f"evidence under {TONE_MIN_WORDS} words"}
    return {"kept": True, "rule": "evidence long enough"}


#: the reading's list → its gate
BY_KIND = {"quotes": quote, "roles": role, "claims": claim, "sentiment": tone}


def apply(got: dict, text: str) -> dict:
    """Every gated item of the reading GOT with its verdict under "gate"; returns {kind: {"kept": n, "dropped": n,
    "citations": n}}. GOT is changed in place; nothing is removed from it."""
    ents = got.get("entities") or {}
    counts = {}
    for kind, gate in BY_KIND.items():
        c = counts.setdefault(kind, {"kept": 0, "dropped": 0, "citations": 0})
        for item in got.get(kind) or []:
            if not isinstance(item, dict):
                continue
            v = gate(item, ents, text)
            item["gate"] = v
            c["kept" if v["kept"] else "dropped"] += 1
            c["citations"] += int(bool(v.get("citation")))
    return counts


def kept(got: dict, kind: str) -> list:
    return [x for x in got.get(kind) or [] if isinstance(x, dict) and (x.get("gate") or {}).get("kept")]
