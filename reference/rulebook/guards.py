"""The merge-decision guards — pure functions, no database, no network.

Doctrine (V2, binding): precision-first — silent merges only where our OWN
normalisation says the forms are identical; everything else is scored and
either auto-applied above a conservative threshold WITH these guards, or
queued for review. Every guard here encodes an incident; the docstrings
carry them.
"""
import re

from claim_graph.normalise import norm_form

from .lexicons import NZ_PLACE_STOPFORMS


def mergeable_form(name: str) -> str:
    """C257: the merge form of a name that is ELIGIBLE to be merged at all.

    `merge_variant` answers what a name normalises TO. This answers whether the
    name should be in the candidate pool in the first place, and it is the
    screen the merge refuter never had: an OCR-debris string has a merge form
    like anything else, so two pieces of broken type that happen to normalise
    alike are a perfectly good "duplicate pair" to a blocker that only compares
    strings. C235 measured 1,024,328 such entities live.

    Empty string = not a candidate, which is the answer every producer already
    knows what to do with (`if not form: continue`). One home, three call
    sites — `waves.identical_wave`, `waves.cross_type_wave` and
    `splink_score._rec` — so the refuter cannot be fed debris by a fourth.

    NOT a merge verdict and not a quarantine: the entity stays exactly as it
    is. C235's heal is what disposes of it; this only keeps it out of a
    comparison that could never be meaningful.
    """
    from .lexicons import is_ocr_debris
    return "" if is_ocr_debris(name) else merge_variant(name)


def merge_variant(name: str) -> str:
    """The merge-normalisation: norm_form + English leading-article strip.
    'the Labour Party' == 'Labour Party'.

    `te ` IS NOT AN ARTICLE FOR THIS PURPOSE (Arthur, 2026-07-31). It was in this
    list, and it is a deal-breaker: te reo `te` is part of the name, not a
    detachable determiner. Te Papa is a full name and Papa is a different thing;
    so are Te Mātā and Mata, Te Ātea and Atea, Te Ika a Māui and Ika a Māui.

    It had been survivable while norm_form preserved macrons, because the two
    sides rarely produced identical strings anyway. The C8 macron fold removed
    that accidental shield and the 2026-07-31 auto wave merged 934 pairs on it —
    every one wrong, all reverted. The same shape as C10: a fix exposing a defect
    that had been hiding behind an unrelated behaviour.

    `containment_distinct` already encodes the correct doctrine for the other
    direction ("Te Anau" is distinct from "Anau"); this function contradicted it.

    THE ENGLISH ARTICLE IS DETACHABLE ONLY WHERE WHAT REMAINS CAN STAND ALONE,
    which measurement says is a question of LENGTH, not of the C11 name list.
    Checked against the 85 live merges this rule had already made: nearly all are
    right — The Court Theatre IS Court Theatre, The Warehouse Group IS Warehouse
    Group, The Science Media Centre IS Science Media Centre — because a
    multi-token residual is still distinctive and people write both forms.

    The risk is entirely in SINGLE-token residuals, where the article is doing
    the identifying work: The Post is not Post, The Press is not Press, The Rock
    is not Rock, The Hague is not Hague. So the guard is a token count, and
    excluding `THE_NAMES` wholesale — the first fix attempted here — would have
    blocked dozens of correct merges to prevent a handful of wrong ones."""
    nf = norm_form(name)
    if nf.startswith("the ") and len(nf[4:].split()) >= 2:
        nf = nf[4:]
    return nf


def name_compatible(a: str, b: str, etype: str) -> bool:
    """False = never auto-merge (route to review). The V2 Will/Bill lesson."""
    ta, tb = merge_variant(a).split(), merge_variant(b).split()
    if etype == "person":
        if len(ta) < 2 or len(tb) < 2:
            return False                     # bare surnames never auto cross-doc
        if ta[-1] != tb[-1]:
            return False                     # different surnames
        # two-token sound-alikes with different first letters (Will/Bill)
        if ta[0][0] != tb[0][0] and not (set(ta) <= set(tb) or set(tb) <= set(ta)):
            return False
    if merge_variant(a) in NZ_PLACE_STOPFORMS or merge_variant(b) in NZ_PLACE_STOPFORMS:
        return False
    return True


_NUM_RE = re.compile(r"\d+")


def number_mismatch(a: str, b: str) -> bool:
    """Arthur's age-grade finding (2026-07-25): names whose NUMBER tokens
    differ are near-certainly different entities — sports age grades
    (Under 18 / Under 20), divisions, year-suffixed phoenix re-registrations
    ((2021) Ltd). String similarity barely notices a one-digit change; the
    digit IS the identity. Hard rule: mismatched numeral multisets never
    auto-merge (humans can still override via the manual tool)."""
    return sorted(_NUM_RE.findall(a)) != sorted(_NUM_RE.findall(b))


# Residual tokens that make a name-containment pair a plausible SAME-entity
# variant ("Fonterra" ⊂ "Fonterra Co-operative Group Limited"). Any residual
# token outside this set marks the pair DISTINCT ("New Zealand" ⊂ "New Zealand
# Police"; "New Zealand" ⊂ "Air New Zealand") — the queue-pollution class
# Arthur spotted 2026-07-26.
_GENERIC_RESIDUAL = {
    "the", "of", "and", "&", "limited", "ltd", "ltd.", "incorporated", "inc",
    "inc.", "group", "holdings", "company", "co", "co.", "corporation",
    "co-operative", "cooperative", "trading", "enterprises", "nz",
    "new", "zealand", "aotearoa", "international",
}


def _tokens(name: str) -> list[str]:
    """Containment-comparison tokens, aligned with merge_variant's article
    doctrine (D11, Arthur's ruling 2026-08-09): a leading English article
    detaches ONLY when the residual is 2+ tokens — "the New Zealand
    Breakers" compares as "new zealand breakers", but "The Press" keeps its
    article (a single-token residual is identified BY it; the old
    unconditional strip made containment call The Press/Press variants
    while merge_variant ruled them distinct). Te reo articles (te/ngā) are
    part of the name and NEVER dropped."""
    t = norm_form(name).split()
    return t[1:] if t[:1] == ["the"] and len(t) > 2 else t


def containment_distinct(a: str, b: str) -> bool:
    """True when one name token-contains the other (prefix or suffix) and the
    residual carries a substantive word — a place and the org named after it
    are different entities, however similar the strings look. Non-containment
    pairs are never judged here (return False = no opinion)."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb or ta == tb:
        return False
    s, l = (ta, tb) if len(ta) < len(tb) else (tb, ta)
    if l[:len(s)] != s and l[-len(s):] != s:
        return False
    residual = l[len(s):] if l[:len(s)] == s else l[:-len(s)]
    return any(t not in _GENERIC_RESIDUAL for t in residual)


def containment_variant(a: str, b: str) -> bool:
    """True when the names token-contain each other with only GENERIC residual
    — a legitimate string variant of one entity ("Fonterra" / "Fonterra
    Co-operative Group Limited"). Disjoint names are NOT variants (Aotearoa vs
    New Zealand is curated knowledge, not string knowledge)."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return False
    if ta == tb:
        return True
    s, l = (ta, tb) if len(ta) < len(tb) else (tb, ta)
    if l[:len(s)] != s and l[-len(s):] != s:
        return False
    residual = l[len(s):] if l[:len(s)] == s else l[:-len(s)]
    return all(t in _GENERIC_RESIDUAL for t in residual)


# Role-register person namespaces (F7 rollout, 2026-08-08): persons minted
# FROM a register roster are linkage-gated — no wave may fold them with
# article-persons (or each other across registers). The er queue / a human
# links them with evidence; auto-fusion by name is exactly the F1a trap.
ROLE_REGISTERS = ("nzbn_directors", "charities")


def is_register_person(etype: str, register_source: str | None) -> bool:
    return etype == "person" and register_source in ROLE_REGISTERS


def clean_name(name: str) -> str:
    """The display-name normalisation v3/cast.py applies at mint time.
    Whitespace collapse, then edge strip, then a second strip because removing an
    outer quote can re-expose a space. Trailing punctuation strips too
    (C8, Arthur-approved 2026-08-08: 26,777 'New Zealand-'-class names)."""
    c = re.sub(r"\s+", " ", name or "").strip().strip("'\"").strip()
    return re.sub(r"[\s\-\u2013\u2014:;,.]+$", "", c).strip() or c


_BYLINE_PREFIX = re.compile(
    r"^(?:analysis|opinion|review|comment|live|watch|listen|explainer|"
    r"first person|editorial|breaking)\s*[-\u2013\u2014:|]\s*", re.I)
_CREDIT_SUFFIX = re.compile(r"\s+(?:photo|photos|photograph)\s*$", re.I)


def strip_byline(name: str) -> str:
    """Strip byline/credit artifacts the extractor minted into names
    ('Analysis - Nicola Willis', 'Nicola Willis Photo' — C8b, measured
    10,684 + 252 on 2026-08-05). Returns the cleaned name, or the input
    unchanged when stripping would leave nothing."""
    c = clean_name(name)
    prev = None
    while prev != c:
        prev = c
        c = _BYLINE_PREFIX.sub("", c)
        c = _CREDIT_SUFFIX.sub("", c)
        c = clean_name(c)
    return c if c else clean_name(name)
