"""The one party-name function (contract: docs/contracts/keys.md).

A filed party label (an EC return's party line, a disclosure's party line,
often read from pixels: "NEO ZEALAND NATIONAL PARTY") resolves to a
REGISTERED party, and the basis is returned with it so a row can be tiered:

  exact     the registered name itself, after the organisation fold
  variant   the frozen lineage map (renames, the Greens' comma family)
  core      the letters-and-digits core is equal
  fuzzy     the core is close to exactly one registered core and the
            party's distinctive word is readable in it (the pixel-read arm)
  None      unresolved: never guessed

A renamed party is the same party (the registration is the party; the name
on the form is a label it wore at a moment). An amendment marker, a month or
a year names the filing, not the party, and is removed first. A fuzzy match
never joins two parties: "New Labour" is not Labour, "NZNP" is not National
(that reach is Arthur's judgment, not a fix). The two old functions
disagreed on 6 of 78 labels; this is the one.

`REGISTERED` is the Register of Political Parties as held on 18 October
2026 (nzbn_canonical parties.register); the parties lane replaces it with
the live register when it exists, and callers may pass their own list.
"""
import difflib
import re

from keys.names import fold_diacritics, organisation_key, squash

REGISTERED = (
    ("ACT New Zealand", "The ACT Party"),
    ("Alliance Party of Aotearoa New Zealand", "Alliance Party"),
    ("Animal Justice Party Aotearoa New Zealand", "Animal Justice Party"),
    ("Aotearoa Legalise Cannabis Party", "The Cannabis Party"),
    ("Conservative Party NZ", ""),
    ("Free Palestine", ""),
    ("New Zealand First Party", "NZ First"),
    ("New Zealand Labour Party", "Labour Party"),
    ("New Zealand Loyal", "NZ Loyal"),
    ("NZ Outdoors & Freedom Party", ""),
    ("Opportunity Party", "Opportunity"),
    ("Te Pāti Māori", ""),
    ("Te Tai Tokerau Party", "TTTP"),
    ("The Green Party of Aotearoa New Zealand", "Green Party"),
    ("The New Zealand National Party", "National Party"),
    ("Vision New Zealand", "Vision NZ"),
    ("Women's Rights Party", ""),
)

#: folded label → registered name: renames and the spellings filers use
VARIANTS = {
    "green party": "The Green Party of Aotearoa New Zealand",
    "green party of aotearoa nz": "The Green Party of Aotearoa New Zealand",
    "green party of aotearoa new zealand": "The Green Party of Aotearoa New Zealand",
    "green party of aotearoa/new zealand": "The Green Party of Aotearoa New Zealand",
    "greens, the green party of aotearoa nz": "The Green Party of Aotearoa New Zealand",
    "greens, the green party of aotearoa": "The Green Party of Aotearoa New Zealand",
    "labour": "New Zealand Labour Party",
    "labour party": "New Zealand Labour Party",
    "national party": "The New Zealand National Party",
    "new zealand national": "The New Zealand National Party",
    "act nz": "ACT New Zealand",
    "new zealand first": "New Zealand First Party",
    "maori party": "Te Pāti Māori",
    "māori party": "Te Pāti Māori",
    "te pati maori": "Te Pāti Māori",
    "conservative": "Conservative Party NZ",
    "opportunities party": "Opportunity Party",
    "top": "Opportunity Party",
    "opportunities party top": "Opportunity Party",
}
FUZZY_MIN = 0.86
FUZZY_MIN_LEN = 8
LENGTH_WINDOW = (0.85, 1.15)
_GENERIC = ("newzealand", "aotearoa", "party", "nz", "of", "the")
AMENDMENT = re.compile(
    r"\bamended\b|\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b"
    r"|\b(?:19|20)\d\d\b", re.I)


def without_amendment(label: str) -> str:
    """`label` with any amendment marker, month and year removed."""
    return squash(AMENDMENT.sub(" ", label or ""))


def core(label: str) -> str:
    """Letters-and-digits core, diacritics decomposed, definite article off:
    'The N.Z. National Party' → 'nznationalparty'."""
    c = re.sub(r"[^a-z0-9]", "", fold_diacritics(label or "").lower())
    return c[3:] if c.startswith("the") else c


def distinctive(party_name: str) -> str:
    t = core(party_name)
    for g in _GENERIC:
        t = t.replace(g, "")
    return t or core(party_name)


def _token_present(token: str, text: str, min_ratio: float = 0.85) -> bool:
    if len(token) < 4:
        return True
    best = 0.0
    for w in (len(token) - 1, len(token), len(token) + 1):
        for i in range(0, max(1, len(text) - w + 1)):
            best = max(best, difflib.SequenceMatcher(None, token, text[i:i + w]).ratio())
            if best >= min_ratio:
                return True
    return best >= min_ratio


def party_name(label: str, registered=REGISTERED):
    """(registered name | None, basis). See the module's head."""
    if not label or not label.strip():
        return None, "unresolved"
    label = without_amendment(label) or label
    names = [r[0] for r in registered]
    f = organisation_key(label)
    by_fold = {organisation_key(n): n for n in names}
    by_fold.update({fold_diacritics(k).lower(): v for k, v in by_fold.items()})
    if f in by_fold:
        return by_fold[f], "exact"
    if f in VARIANTS and VARIANTS[f] in names:
        return VARIANTS[f], "variant"
    fd = fold_diacritics(f)
    if fd in VARIANTS and VARIANTS[fd] in names:
        return VARIANTS[fd], "variant"
    c = core(label)
    if not c:
        return None, "unresolved"
    by_core = {}
    for n, ab in registered:
        by_core[core(n)] = n
        if len(core(ab or "")) >= 3:
            by_core.setdefault(core(ab), n)
    for v_fold, v_name in VARIANTS.items():
        if v_name in names:
            by_core.setdefault(core(v_fold), v_name)
    for cc in (c, "newzealand" + c[2:] if c.startswith("nz") else c):
        if cc in by_core:
            return by_core[cc], "core"
    if len(c) < FUZZY_MIN_LEN:
        return None, "unresolved"
    # the pixel-read arm: close to one registered core of about the same
    # length. The length window is what keeps "New Labour" out of Labour.
    scored = sorted(((difflib.SequenceMatcher(None, c, k).ratio(), k) for k in by_core
                     if len(k) >= FUZZY_MIN_LEN and LENGTH_WINDOW[0] <= len(c) / len(k) <= LENGTH_WINDOW[1]),
                    reverse=True)
    if scored and scored[0][0] >= FUZZY_MIN:
        best = scored[0]
        rivals = [s for s in scored[1:] if s[0] >= FUZZY_MIN and by_core[s[1]] != by_core[best[1]]]
        if not rivals and _token_present(distinctive(by_core[best[1]]), c):
            return by_core[best[1]], f"fuzzy:{best[0]:.2f}"
    return None, "unresolved"
