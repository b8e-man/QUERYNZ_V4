"""The split rule of profile `hansard-day` (hansard-3, Arthur 31 October 2026):
a sitting day's whole text, as the provider's pdftotext -layout gave it, cut
into sections and speaker turns. Deterministic, no model.

Two layouts, recognised by their page furniture (measured on all 1,862
days, 31 October 2026):

  final   1,827 days, 2003 to 2026: a cover, a table of contents, body
          pages under a running head `20 Nov 2024   Oral Questions   7595`
          (or page number first on even pages), then an index. Paragraphs
          are indented three or four spaces; headings are centred
  draft   35 days of 2026 ("Subject to Revision—Not to be Quoted or
          Distributed", `Page 4   HOUSE OF REPRESENTATIVES  Wednesday, 23
          September 2026`): no contents, no index; paragraphs at the margin,
          headings centred; a first speech carries the time `(14:00)`

The rule:

  1. pages: the text split at form feeds. In the final layout the body is
     the pages that carry the running head (the cover, contents and index
     carry none or another); the head line is dropped. In the draft every
     page is body and its two or three furniture lines are dropped
  2. headings: a centred line (indent 10 or more in the final layout, 8 in
     the draft; an all-capitals line from indent 6), 95 characters or fewer
     (72 for a mixed-case line), starting with a letter, not ending in
     punctuation, not a vote count (`Ayes 63`), not a speaker line. A run of
     heading lines is one section's heading; the text to the next run is
     the section
  3. the section's names: in the final layout the capitals line is the
     proceeding (or the bill, when it names one) and the mixed-case lines the
     subject; a run of mixed-case lines alone takes the proceeding carried
     from the run before (`Question No. 2—Children` under `ORAL QUESTIONS`).
     In the draft the mixed-case line before the capitals is the proceeding
     (`Oral Questions to Ministers`) and the capitals line the subject
     (`FINANCE`); a run beginning in capitals carries the proceeding before
  4. turns: a paragraph that opens with a speaker line, `NAME (role or
     Party—Electorate) [(hh:mm)] [to the Minister …]: speech`. A name in
     capitals (a member's first speech in a debate), a role (SPEAKER,
     CHAIRPERSON (Name), Hon Member) or a mixed-case name already seen in
     capitals that day or found in the roster is a speaker; any other
     mixed-case `Word Word:` is text. The turn runs to the next speaker
     line or heading
  5. the member: the name matched to the old roster (`hansard.members`,
     394 members of Parliaments 47 to 54) within the day's Parliament, by
     surname and given names with honorifics and diacritics folded; a
     surname alone when it is unique in that Parliament; else no member id
     and the label stands. A chair's name in brackets (`CHAIRPERSON (Barbara
     Kuriger)`) is matched the same way, with the role kept

A text with no form feed, or no body page, cannot be split: `split` says
why and the load sets the day aside at stage `read`.

    python -m registers.hansard.split --prove       the 137 days both sources hold against the old counts (live, read-only)
"""
import datetime as dt
import re
import sys
from dataclasses import dataclass, field

from keys import names as N

RULE = "hansard-day split 1"
FINAL, DRAFT = "final", "draft"
FINAL_HEAD = re.compile(r"^\s*(?:\d{1,2} \w{3,4} \d{4}\s{2,}\S.*\s{2,}\d{1,5}|\d{1,5}\s{2,}\S.*\s{2,}\d{1,2} \w{3,4} \d{4})\s*$")
DRAFT_MARK = "Subject to Revision"
DRAFT_HEAD = re.compile(r"HOUSE OF REPRESENTATIVES")
VOTE = re.compile(r"^(Ayes|Noes|Abstentions?)\s+\d+")
HONORIFIC = r"(?:(?i:Rt Hon|Hon|Dr|Sir|Dame|Mr|Mrs|Ms|Miss|Madam|The|An)\s+)*"
WORD = r"[A-ZĀĒĪŌŪ][A-Za-zāēīōūĀĒĪŌŪ'’\-]*"
PARTICLE = r"(?:(?:van|de|der|te|von|du|le|la|VAN|DE|DER|TE|VON|DU|LE|LA) )*"
NAME = HONORIFIC + WORD + r"(?:\s+" + PARTICLE + WORD + r"){0,5}(?:\s+(?:KC|QC|MP))?"
SPEAKER = re.compile(r"^(?P<indent>\s{0,8})(?P<number>\d{1,2}\. )?(?P<name>" + NAME + r")(?P<paren>(?: \([^()\n]{1,90}\))*)"
                     r"(?P<to>\s+to the\s+[^:\n]{1,100})?:(?:\s|$)")
TIME = re.compile(r"^\d\d:\d\d$")
ROLES = {"speaker": "Speaker", "mr speaker": "Speaker", "madam speaker": "Speaker", "deputy speaker": "Deputy Speaker",
         "assistant speaker": "Assistant Speaker", "temporary speaker": "Temporary Speaker",
         "chairperson": "Chairperson", "the chairperson": "Chairperson", "temporary chairperson": "Chairperson", "clerk": "Clerk", "the clerk": "Clerk",
         "hon member": "Member (unattributed)", "hon members": "Member (unattributed)",
         "an hon member": "Member (unattributed)", "members": "Member (unattributed)",
         "government members": "Member (unattributed)", "opposition members": "Member (unattributed)",
         "a member": "Member (unattributed)", "hon member of parliament": "Member (unattributed)"}
PARTIES = ("National", "NZ National", "New Zealand National", "Labour", "NZ Labour", "New Zealand Labour", "Green",
           "Greens", "ACT", "ACT NZ", "ACT New Zealand", "NZ First", "New Zealand First", "Te Pāti Māori", "Māori Party",
           "Maori Party", "United Future", "UnitedFuture", "Progressive", "Jim Anderton's Progressive", "Mana", "Alliance",
           "Independent", "Opportunities", "TOP", "Vision NZ")
PARTY_SET = {p.lower() for p in PARTIES}
STRIP = {"rt", "hon", "dr", "sir", "dame", "mr", "mrs", "ms", "miss", "madam", "the", "an", "kc", "qc", "mp"}
QUESTION = re.compile(r"^Question No\. \d")
WRAP_CAPS, WRAP_MIXED = 40, 60              # a heading line this long or longer wraps onto the next
CENTRE_SLACK = 10                            # a mixed-case heading's middle sits this close to the page's centre
#: each Parliament's first day, by its general election (the House never sits between an election and its opening)
PARLIAMENTS = ((dt.date(2002, 7, 27), 47), (dt.date(2005, 9, 17), 48), (dt.date(2008, 11, 8), 49),
               (dt.date(2011, 11, 26), 50), (dt.date(2014, 9, 20), 51), (dt.date(2017, 9, 23), 52),
               (dt.date(2020, 10, 17), 53), (dt.date(2023, 10, 14), 54), (dt.date(2026, 11, 7), 55))
ORDINALS = {"forty-seventh": 47, "forty-eighth": 48, "forty-ninth": 49, "fiftieth": 50, "fifty-first": 51,
            "fifty-second": 52, "fifty-third": 53, "fifty-fourth": 54, "fifty-fifth": 55}


@dataclass
class Turn:
    ordinal: int
    label: str                  # the speaker as printed, honorific and name, without the brackets
    name: str | None            # the person named: the label, or the chair's name in brackets
    role_text: str | None       # the brackets' words: 'Leader of the House', 'Labour—Mana', 'Assistant Speaker'
    party: str | None
    electorate: str | None
    role: str | None            # a role when the label is one (Speaker, Chairperson, Clerk, Member (unattributed))
    caps: bool                  # the name was printed in capitals (a first speech)
    start: int                  # line offsets into the section's lines
    end: int
    member_id: str | None = None
    roster_name: str | None = None
    basis: str | None = None    # how the member was found: full, given, surname; None when not


@dataclass
class Section:
    index: int
    heading: list               # the heading lines as printed
    proceeding: str | None
    subject: str | None
    bill_title: str | None
    lines: list                 # the section's text lines, furniture off
    turns: list = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


@dataclass
class Day:
    layout: str | None
    parliament: int | None
    sections: list = field(default_factory=list)
    pages: int = 0
    body_pages: int = 0
    reason: str = ""            # why the text could not be split, when it could not

    @property
    def turns(self) -> list:
        return [t for s in self.sections for t in s.turns]


# ── the roster ────────────────────────────────────────────────────────────────────────────────────────────────
def fold(s: str) -> str:
    return re.sub(r"[^a-z' -]", "", N.fold_diacritics(s or "").lower().replace("’", "'"))


def name_tokens(s: str) -> list:
    """Lower-case, diacritics folded, honorifics and post-nominals off; 'McAnulty' stays one token."""
    return [w for w in fold(s).replace("-", " ").split() if w not in STRIP]


class Roster:
    """The old roster for matching: {(parliament, surname): [(member id, display name, given tokens)]}."""

    def __init__(self, members: list):
        self.by_surname = {}
        for m in members:
            surname, _, given = (m.get("display_name") or "").partition(",")
            sur = " ".join(name_tokens(surname))
            giv = name_tokens(given)
            for p in (m.get("parliaments") or [None]):
                self.by_surname.setdefault((p, sur), []).append((m["key"], m.get("display_name"), giv))

    def find(self, printed: str, parliament: int | None):
        """(member id, display name, basis) or None."""
        toks = name_tokens(printed)
        if len(toks) < 2:
            return None
        for n in (1, 2, 3):                    # a surname of one to three words at the end (van de Molen)
            sur, giv = " ".join(toks[-n:]), toks[:-n]
            cands = self.by_surname.get((parliament, sur)) or (self.by_surname.get((None, sur)) if parliament is None else [])
            if not cands or not giv:
                continue
            full = [c for c in cands if c[2] == giv]
            if len(full) == 1:
                return full[0][0], full[0][1], "full"
            first = [c for c in cands if c[2] and c[2][0] == giv[0]]
            if len(first) == 1:
                return first[0][0], first[0][1], "given"
            sub = [c for c in cands if set(giv) <= set(c[2])]
            if len(sub) == 1:
                return sub[0][0], sub[0][1], "given"
            if len({c[0] for c in cands}) == 1:
                return cands[0][0], cands[0][1], "surname"
        return None


def parliament_of(day: str, text: str = "") -> int | None:
    """The cover's 'Fifty-fourth Parliament' where printed; else by the election before the day."""
    m = re.search(r"\b([A-Z][a-z]+(?:-[a-z]+)?) Parliament\b", text[:3000])
    if m and m.group(1).lower() in ORDINALS:
        return ORDINALS[m.group(1).lower()]
    try:
        d = dt.date.fromisoformat(day)
    except ValueError:
        return None
    out = None
    for first, n in PARLIAMENTS:
        if d >= first:
            out = n
    return out


# ── pages and furniture ───────────────────────────────────────────────────────────────────────────────────────
def layout_of(text: str) -> str | None:
    if DRAFT_MARK in text[:4000] and DRAFT_HEAD.search(text[:4000]):
        return DRAFT
    if any(FINAL_HEAD.match(l) for l in text[:60000].split("\n")):
        return FINAL
    return None


def body_lines(text: str, layout: str) -> tuple:
    """(lines of the body with the furniture off, pages, body pages)."""
    pages = text.split("\f")
    out, body = [], 0
    if layout == FINAL:
        flags = [any(FINAL_HEAD.match(l) for l in p.split("\n")[:4]) for p in pages]
        first = flags.index(True) if True in flags else None
        last = len(flags) - 1 - flags[::-1].index(True) if True in flags else None
        for i, p in enumerate(pages):
            if first is None or i < first or i > last:
                continue
            lines = p.split("\n")
            if flags[i]:
                k = next(j for j, l in enumerate(lines[:4]) if FINAL_HEAD.match(l))
                lines = lines[:k] + lines[k + 1:]
            elif i != first and not p.strip():
                continue
            body += 1
            out.extend(lines)
    else:
        for p in pages:
            lines = p.split("\n")
            k = 0
            while k < min(4, len(lines)) and (DRAFT_MARK in lines[k] or DRAFT_HEAD.search(lines[k]) or not lines[k].strip()
                                                or re.fullmatch(r"\s*\d{4}\s*", lines[k])):
                k += 1
            if p.strip():
                body += 1
            out.extend(lines[k:])
    return out, len(pages), body


# ── headings and speakers ─────────────────────────────────────────────────────────────────────────────────────
def is_caps(s: str) -> bool:
    return s.upper() == s and re.search(r"[A-ZĀĒĪŌŪ]{2}", s) is not None


def centre_of(lines: list) -> float:
    """Where the page's centred lines sit: the median middle of the short lines indented ten or more."""
    mids = sorted(len(l) - len(l.lstrip()) + len(l.strip()) / 2 for l in lines
                  if len(l) - len(l.lstrip()) >= 10 and 0 < len(l.strip()) <= 72)
    return mids[len(mids) // 2] if mids else 47.0


def is_heading(line: str, layout: str, centre: float = 47.0) -> bool:
    """A centred heading line. Capitals from indent 1 (a long heading wraps and sits left); a mixed-case line
    centred within CENTRE_SLACK of the page's centre, 72 characters or fewer, starting in upper case."""
    s = line.strip()
    if not s or len(s) > 95 or not s[0].isalpha() or s[-1] in ".,;:" or VOTE.match(s) or SPEAKER.match(line):
        return False
    indent = len(line) - len(line.lstrip())
    if is_caps(s):
        return indent >= 1 and len(s) >= 4
    if QUESTION.match(s):
        return indent >= 1
    return (indent >= (10 if layout == FINAL else 8) and len(s) <= 72 and s[0].isupper()
            and abs(indent + len(s) / 2 - centre) <= CENTRE_SLACK)


def continues_heading(line: str, previous: str) -> bool:
    """The rest of a heading that wrapped: the previous heading line ran long, this one follows at once."""
    s = line.strip()
    if not s or len(s) > 95 or not s[0].isalpha() or s[-1] in ".,;:" or VOTE.match(s) or SPEAKER.match(line):
        return False
    indent = len(line) - len(line.lstrip())
    p = previous.strip()
    return indent >= 4 and (len(p) >= WRAP_CAPS if is_caps(p) else len(p) >= WRAP_MIXED)


def merge_wrapped(heads: list) -> list:
    """Heading lines of a run, the wrapped ones joined to the line they continue."""
    out = []
    for h in heads:
        if out and ((is_caps(out[-1]) and is_caps(h) and len(out[-1]) >= WRAP_CAPS)
                    or (not is_caps(out[-1]) and not is_caps(h) and len(out[-1]) >= WRAP_MIXED)):
            out[-1] = out[-1] + " " + h
        else:
            out.append(h)
    return out


def speaker_line(line: str, seen_caps: set, roster: "Roster | None", parliament: int | None):
    """A Turn without its text span, or None when the line is text."""
    m = SPEAKER.match(line)
    if not m:
        return None
    name = re.sub(r"\s+", " ", m.group("name")).strip()
    parens = [p[2:-1].strip() for p in re.findall(r" \([^()\n]{1,90}\)", m.group("paren") or "")]
    parens = [p for p in parens if not TIME.match(p)]
    toks = name_tokens(name)
    key = " ".join(toks)
    role = ROLES.get(fold(name).strip()) or ROLES.get(key)
    caps = is_caps(re.sub(HONORIFIC, "", name, count=1))
    if role is None and not caps and key not in seen_caps:
        if roster is None or roster.find(name, parliament) is None:
            return None
    role_text = parens[0] if parens else None
    party = electorate = None
    person = name if role is None else None
    if role in ("Chairperson", "Assistant Speaker", "Deputy Speaker", "Temporary Speaker", "Speaker") and parens:
        person = parens[0]
        role_text = None
    elif role_text:
        a, sep, b = role_text.partition("—")
        if sep and a.strip().lower() in PARTY_SET:
            party, electorate = a.strip(), b.strip()
        elif role_text.lower() in PARTY_SET:
            party = role_text
        elif role is None and role_text.lower() in ROLES:
            pass
    return Turn(0, name, person, role_text, party, electorate, role, caps, 0, 0)


def name_sections(runs: list, layout: str) -> list:
    """[(proceeding, subject, bill)] for each heading run, the proceeding carried where a run has none."""
    out, carried = [], None
    for run in runs:
        caps = [h for h in run if is_caps(h)]
        mixed = [h for h in run if not is_caps(h)]
        if layout == FINAL:
            if caps:
                carried = " — ".join(caps)
                proceeding, subject = carried, (" — ".join(mixed) if mixed else carried)
            else:
                proceeding, subject = carried, " — ".join(mixed)
        else:
            lead = []
            for h in run:
                if is_caps(h):
                    break
                lead.append(h)
            rest = run[len(lead):]
            if lead and rest:
                carried = " — ".join(lead)
                proceeding, subject = carried, " — ".join(rest)
            elif lead:
                proceeding, subject = (lead[0], " — ".join(lead[1:]) or lead[0]) if len(lead) > 1 else (carried or lead[0], lead[0])
                if len(lead) > 1:
                    carried = lead[0]
            else:
                proceeding, subject = carried, " — ".join(rest)
        bill = next((h for h in run if re.search(r"\bBILLS?\b|\bBill\b", h) and not re.search(r"INTRODUCTION OF BILLS|^BILLS$", h)), None)
        if bill and re.fullmatch(r"(?i)bills?", bill.strip()):
            bill = None
        out.append((proceeding, subject, bill))
    return out


def split(text: str, day: str, roster: Roster | None = None) -> Day:
    layout = layout_of(text)
    if layout is None:
        return Day(None, None, reason="neither layout's page furniture is in the text" if "\f" in text
                   else "no form feed: the text has no pages")
    out = Day(layout, parliament_of(day, text))
    lines, out.pages, out.body_pages = body_lines(text, layout)
    if not out.body_pages:
        out.reason = "no body page under a running head"
        return out
    # heading runs: [(start line, end line, [headings])]; a blank line inside a run is skipped, a wrapped
    # heading's second line joins it
    runs, i, centre = [], 0, centre_of(lines)
    while i < len(lines):
        if is_heading(lines[i], layout, centre):
            j, heads = i, []
            while j < len(lines):
                if is_heading(lines[j], layout, centre) or (heads and continues_heading(lines[j], heads[-1])):
                    heads.append(lines[j].strip())
                elif not lines[j].strip() and j + 1 < len(lines) and is_heading(lines[j + 1], layout, centre):
                    pass
                else:
                    break
                j += 1
            runs.append((i, j, merge_wrapped(heads)))
            i = j
        else:
            i += 1
    if not runs or (runs[0][0] > 0 and any(l.strip() for l in lines[:runs[0][0]])):
        runs.insert(0, (0, 0, []))
    names = name_sections([r[2] for r in runs], layout)
    seen_caps = set()
    for k, ((start, end, heads), (proceeding, subject, bill)) in enumerate(zip(runs, names)):
        stop = runs[k + 1][0] if k + 1 < len(runs) else len(lines)
        body = lines[end:stop]
        sec = Section(k, heads, proceeding, subject, bill, body)
        opens = []
        for n, line in enumerate(body):
            t = speaker_line(line, seen_caps, roster, out.parliament)
            if t is not None:
                if t.caps and t.role is None:
                    seen_caps.add(" ".join(name_tokens(t.label)))
                opens.append((n, t))
        for o, (n, t) in enumerate(opens, 1):
            t.ordinal, t.start = o, n
            t.end = opens[o][0] if o < len(opens) else len(body)
            if roster is not None and t.name:
                hit = roster.find(t.name, out.parliament)
                if hit:
                    t.member_id, t.roster_name, t.basis = hit
            sec.turns.append(t)
        out.sections.append(sec)
    return out


def counts(day: Day) -> dict:
    turns = day.turns
    attributed = [t for t in turns if t.member_id]
    return {"sections": len(day.sections), "turns": len(turns), "attributed": len(attributed),
            "unattributed": len(turns) - len(attributed), "speakers": len({t.member_id for t in attributed}),
            "role_only": sum(1 for t in turns if t.role and not t.member_id),
            "named_unmatched": sum(1 for t in turns if t.name and not t.member_id)}


# ── pieces for the text reader ────────────────────────────────────────────────────────────────────────────────
@dataclass
class Piece:
    number: int                 # from 1
    section: int                # the section's index
    sections: int               # sections covered: 1, or more when whole sections are packed (packed())
    part: int                   # 1 for a whole section; the part number when the section was cut
    parts: int
    text: str
    turns: int                  # speaker turns inside it
    ids: tuple = ()             # the section indexes a packed piece holds, each marked [SECTION n] in its text

    @property
    def chars(self) -> int:
        return len(self.text)


def paragraph_starts(lines: list, layout: str) -> list:
    """Line offsets where a paragraph begins: an indented line in the final layout, a line after a blank or a
    speaker line in the draft (whose paragraphs sit at the margin)."""
    out = []
    for n, l in enumerate(lines):
        if not l.strip():
            continue
        if layout == FINAL:
            if len(l) - len(l.lstrip()) >= 1 or n == 0:
                out.append(n)
        elif n == 0 or not lines[n - 1].strip() or SPEAKER.match(l):
            out.append(n)
    return out or [0]


def _cut(lines: list, starts: list, budget: int) -> list:
    """Groups of consecutive lines, cut at `starts` so each group is within the budget where it can be; a run
    between two starts over the budget is cut at lines."""
    chunks, cur, size = [], [], 0
    bounds = sorted(set(starts) | {0})
    for i, b in enumerate(bounds):
        e = bounds[i + 1] if i + 1 < len(bounds) else len(lines)
        block = lines[b:e]
        n = sum(len(l) + 1 for l in block)
        if n > budget:                      # one paragraph or turn over the budget: by lines
            if cur:
                chunks.append(cur)
                cur, size = [], 0
            for l in block:
                if size + len(l) + 1 > budget and cur:
                    chunks.append(cur)
                    cur, size = [], 0
                cur.append(l)
                size += len(l) + 1
            continue
        if size + n > budget and cur:
            chunks.append(cur)
            cur, size = [], 0
        cur.extend(block)
        size += n
    if cur:
        chunks.append(cur)
    return chunks


def pieces_of(day: Day, budget: int) -> list:
    """The profile's rule for a document over the reader's budget: one piece per section within it; a section
    over it cut at speaker turns into parts within it; a turn over it cut at paragraphs; a paragraph over it
    cut at lines. Empty sections (a heading alone) make no piece."""
    out = []
    for sec in day.sections:
        text = sec.text
        if not text.strip():
            continue
        if len(text) <= budget:
            out.append(Piece(len(out) + 1, sec.index, 1, 1, 1, text, len(sec.turns)))
            continue
        starts = [t.start for t in sec.turns]
        chunks = _cut(sec.lines, starts, budget)
        if any(sum(len(l) + 1 for l in c) > budget for c in chunks):
            chunks = _cut(sec.lines, sorted(set(starts) | set(paragraph_starts(sec.lines, day.layout))), budget)
        for k, c in enumerate(chunks, 1):
            lo = sum(len(x) for x in chunks[:k - 1])
            turns = sum(1 for t in sec.turns if lo <= t.start < lo + len(c))
            out.append(Piece(len(out) + 1, sec.index, 1, k, len(chunks), "\n".join(c), turns))
    return out


MARK = "[SECTION {}]"


def packed(pieces: list, budget: int) -> list:
    """Consecutive whole sections joined into one piece while the joined text, markers included, stays within the
    budget; a section cut into parts stays its own piece. A packed piece marks each section [SECTION n] so the
    reader can say which section a name is in. Renumbered from 1."""
    out, run = [], []

    def flush():
        if not run:
            return
        if len(run) == 1:
            p = run[0]
            out.append(Piece(len(out) + 1, p.section, 1, p.part, p.parts, p.text, p.turns))
        else:
            text = "\n\n".join(MARK.format(p.section) + "\n" + p.text for p in run)
            out.append(Piece(len(out) + 1, run[0].section, len(run), 1, 1, text, sum(p.turns for p in run),
                             tuple(p.section for p in run)))
        run.clear()
    for p in pieces:
        if p.parts > 1:
            flush()
            out.append(Piece(len(out) + 1, p.section, 1, p.part, p.parts, p.text, p.turns))
            continue
        size = sum(len(MARK.format(q.section)) + 2 + q.chars for q in run + [p])
        if run and size > budget:
            flush()
        run.append(p)
    flush()
    return out


def unsplittable(day: Day, budget: int) -> list:
    """The pieces still over the budget after every cut: a line longer than the budget. Named for the catch log."""
    return [p for p in pieces_of(day, budget) if p.chars > budget]


# ── the proof against the old estate ──────────────────────────────────────────────────────────────────────────
def prove(conn, get_bytes, log=print) -> dict:
    """The 137 days both sources hold: the split's sections and member turns against the sitting row's own
    counts (hansard.sittings), and the turns' members against the old turns' member ids. Read-only; the live
    tables under the reader, the texts from the document store."""
    import json
    roster = Roster([{"key": k, "display_name": n, "parliaments": p}
                     for k, n, p in conn.execute("SELECT key, display_name, parliaments FROM hansard.members")])
    old = {d: r for d, *r in conn.execute("SELECT key, old_sections, old_speeches, old_unattributed, old_speakers, "
                                         "parliament FROM hansard.sittings")}
    docs = dict(conn.execute("SELECT key, document FROM hansard.days WHERE old_sections IS NOT NULL"))
    old_sections = {}
    for d, subj, n in conn.execute("SELECT s.sitting_on::text, s.subject, (SELECT count(*) FROM hansard.turns t WHERE "
                                   "t.section = s.key AND t.member_id IS NOT NULL) FROM hansard.sections s"):
        old_sections.setdefault(d, []).append((fold(subj or ""), n))
    by_section = {}
    old_members = {}
    for d, mid, n in conn.execute("SELECT sitting_on::text, member_id, count(*) FROM hansard.turns "
                                  "WHERE member_id IS NOT NULL GROUP BY 1, 2"):
        old_members.setdefault(d, {})[mid] = n
    rows, agree_s, agree_t, within = [], 0, 0, 0
    tot = {"sections": [0, 0], "turns": [0, 0], "speakers": [0, 0]}
    unmatched = {}
    for d in sorted(docs):
        text = json.loads(get_bytes(docs[d]))["text"]
        day = split(text, d, roster)
        c = counts(day)
        o_sec, o_sp, o_un, o_spk, o_parl = old[d]
        rows.append((d, day.layout, c["sections"], o_sec, c["attributed"], o_sp, c["unattributed"], o_un,
                     c["speakers"], o_spk, c["named_unmatched"]))
        agree_s += c["sections"] == o_sec
        agree_t += c["attributed"] == o_sp
        within += abs(c["attributed"] - o_sp) <= max(2, 0.1 * o_sp)
        tot["sections"][0] += c["sections"]; tot["sections"][1] += o_sec
        tot["turns"][0] += c["attributed"]; tot["turns"][1] += o_sp
        tot["speakers"][0] += c["speakers"]; tot["speakers"][1] += o_spk
        for t in day.turns:
            if t.name and not t.member_id:
                unmatched[t.name] = unmatched.get(t.name, 0) + 1
        olds = {}
        for subj, n in old_sections.get(d, []):
            olds.setdefault(subj, []).append(n)
        for sec in day.sections:
            key = fold(sec.subject or "")
            if key in olds and len(olds[key]) == 1:
                diff = sum(1 for t in sec.turns if t.member_id) - olds[key][0]
                by_section[max(-3, min(3, diff))] = by_section.get(max(-3, min(3, diff)), 0) + 1
        if day.parliament != o_parl:
            log(f"{d}: parliament {day.parliament} against the old row's {o_parl}")
    log(f"{len(rows)} days both hold; sections equal on {agree_s}, member turns equal on {agree_t}, within 10% on {within}")
    log(f"totals (split / old): sections {tot['sections'][0]} / {tot['sections'][1]}, member turns {tot['turns'][0]} / "
        f"{tot['turns'][1]}, distinct members {tot['speakers'][0]} / {tot['speakers'][1]}")
    log("day layout sections(old) member-turns(old) role-only(old) members(old) named-unmatched")
    for r in rows:
        if r[2] != r[3] or r[4] != r[5]:
            log(f"{r[0]} {r[1]} {r[2]}({r[3]}) {r[4]}({r[5]}) {r[6]}({r[7]}) {r[8]}({r[9]}) {r[10]}")
    log("sections matched to an old section by subject: member turns split minus old (capped at ±3): "
        + ", ".join(f"{k:+d}: {v}" for k, v in sorted(by_section.items())))
    top = sorted(unmatched.items(), key=lambda kv: -kv[1])[:25]
    log("named speakers not matched to the roster (label: turns): " + "; ".join(f"{k}: {v}" for k, v in top))
    return {"rows": rows, "sections_equal": agree_s, "turns_equal": agree_t, "within": within, "totals": tot,
            "unmatched": unmatched, "by_section": by_section}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if "--prove" in argv:
        from support import db
        from support.docstore.landing import read_bytes
        with db.connect(db.READ_KEY, "querynz_v4") as conn:
            conn.execute("SET statement_timeout = '120s'")
            prove(conn, read_bytes)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
