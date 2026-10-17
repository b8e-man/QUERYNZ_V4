"""The gold set — the denominator this service owes every figure it prints.

Arthur, 2026-09-23, on reaching 99%: build it. The efficient way is not to
hand-key three hundred pages cold. It is to run both readers, and let the
review queue produce the gold set as a by-product of the clicks a person is
making anyway: where the readers agree and nothing fires, that is a candidate;
where they do not, it is already an item, and its resolution is a confirmed
row. Same clicks, two products.

TWO TIERS, NEVER MIXED. This is the whole discipline of the module.

  agreed     two independent readers returned the same value and no invariant
             implicated the row. Strong evidence. NOT ground truth: readers
             can fail identically, and a figure computed against this tier is
             a figure about AGREEMENT, not about correctness.
  confirmed  a person looked at the cropped scan and said what it says. This
             is the only tier that may be called ground truth.

FOUND, 2026-09-23. The `agreed` tier produced ZERO across six whole party
returns, and seven fixes made on inference did not move it. The cause was not
in this module at all: `arbitrate.merge` keyed disputed fields on `(part, n)`,
and an unnumbered row's `n` is None — so ONE dispute anywhere in a part
blanked every field of every unnumbered row in it. The rows arriving here
looked perfectly agreed and had nothing left to pin. It was found by printing
what happened to each row instead of reasoning about it, which is what should
have happened at the second attempt rather than the eighth.

`score()` reports against each tier separately and refuses to
produce a blended number. The reason is the whole history of this work: on
2026-09-22 a coverage figure and a denominator figure were quoted as one
thing three times running, and each time the number was true of something
narrower than its label.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import pathlib

from .arbitrate import Arbitration
from .invariants import Report
from .rows import Document, NAMED_DONOR_PARTS, Row, donor_key, malformed

AGREED, CONFIRMED = "agreed", "confirmed"

#: A third state, and not a tier: a person looked and said the readers'
#: agreement is WRONG. It pins nothing — it removes a candidate from the set
#: so the same wrong value is not offered again. `score` never scores against
#: it, because "this is not the value" is not a value.
REJECTED = "rejected"

#: A FOURTH state, and the one the surface was missing. Arthur, 2026-09-23,
#: having gone through the tab: *"make sure you adjust the affected rejections
#: to abstentions."*
#:
#: A person looked and could not answer THE QUESTION AS PUT. That is not the
#: reader being wrong, and recording it as REJECTED said it was. All seven of
#: his rejections turned out to be this — "blended cells", "too many dates on
#: the page for me to find this one. it could be there", "this is an
#: extraction issue, I cant identify which one is or is not correct" — and it
#: was already distorting the only figures this surface produces: implicated
#: read 13 of 19 with them counted as errors, and 13 of 13 without.
#:
#: The two verdicts want opposite work. A REJECTED cell is a reader defect to
#: fix. An ABSTAINED cell is a PRESENTATION defect: "too many dates on the
#: page" means the date was offered without the row it belongs to, which no
#: amount of reader accuracy would cure. So an abstention withdraws the cell
#: from the queue — re-asking the same unanswerable question is the waste this
#: closes — and `score` never counts it either way, because a person who could
#: not tell has said nothing about whether the reader was right.
ABSTAINED = "abstained"

#: Every state a PERSON can put a cell in. A machine only ever writes AGREED.
HUMAN_VERDICTS = (CONFIRMED, REJECTED, ABSTAINED)

#: Findings that name no rows normally put their whole PART in doubt, because
#: a rule like `sum_matches_stated_total` says some row in it is wrong without
#: saying which. This one is different: it reports rows read WITHOUT the
#: form's row number, and gold only ever pins rows that HAVE one. Letting it
#: disqualify the part yielded zero candidates from every document — measured
#: 2026-09-23, and the reason this exemption is written down rather than
#: quietly assumed.
NOT_DISQUALIFYING = frozenset({"rows_carry_printed_numbers"})

#: Fields a gold row can pin. `donor` is compared on its key, not its text:
#: two readers will spell an address differently and neither is wrong.
FIELDS = ("donor", "date", "amount")


def address(n: int | None, donor: str | None, occurrence: int = 0) -> str:
    """How a gold row names the row it pins, ACROSS re-reads.

    The form's printed number is the best address there is, and it is used
    wherever it exists. But it only exists where the reader recovered it from
    the margin, and on the first six documents read whole EVERY agreed row had
    no number — each was a banded aggregate in a part that prints none. Keyed
    on the number alone the gold set stayed empty, which is how this was
    found (2026-09-23).

    So the fallback is the donor plus which of that donor's rows this is.
    Weaker on purpose: a reader that misreads the donor addresses a different
    row, and the pin then reads as MISSING rather than wrong. That is the
    right way for it to fail — it under-claims — and it is why `score` counts
    missing separately rather than folding it into accuracy's numerator.
    """
    if n is not None:
        return f"n={n}"
    return f"d={donor_key(donor or '')}#{occurrence}"


#: WHY a cell is a candidate. This is not the tier — the tier is the verdict
#: (agreed / confirmed / rejected) — it is what the machine knew when it
#: offered the cell, and it decides what a person's answer BUYS.
#:
#: Arthur, 2026-09-23, on the first 65 confirmations: the agreed tier is a
#: calibration instrument and a useless repair instrument, because
#: `candidates` excludes any row a finding names, and "this part does not
#: reconcile" names the whole part. Measured at the time: of 592 candidates,
#: 359 sat in a part that already reconciled, 168 in a part with no stated
#: total, and **none at all** in a part that failed — so every verdict
#: confirmed something we were already right about. CONTESTED is the second
#: class, drawn from exactly the cells AGREED refuses.
AGREED_KIND = "agreed"          # both readers returned this; no rule objected
DISPUTED = "disputed"           # the readers returned DIFFERENT values here
IMPLICATED = "implicated"       # a rule named this row or its part
KINDS = (AGREED_KIND, DISPUTED, IMPLICATED)

#: A contested cell is only answerable if the person is shown what the
#: readers actually said. One option per reader, as `(reader, value)`.
Option = tuple[str, object]


@dataclasses.dataclass(frozen=True)
class GoldRow:
    stem: str
    part: str | None
    n: int | None
    field: str
    value: object
    tier: str
    by: str = ""
    source: str | None = None
    page: int | None = None
    #: How this row is found again. See `address`.
    addr: str = ""
    #: Why it was offered (AGREED_KIND / DISPUTED / IMPLICATED).
    kind: str = AGREED_KIND
    gen: str = ""
    #: What the person SAID about this cell. Arthur 2026-09-23: "for the gold
    #: tier review I need a comment box instead of a corrected value box." A
    #: typed value was only ever usable on an `amount`, and on an implicated
    #: row the useful answer is usually a sentence — what the scan shows, or
    #: why the cell cannot be judged from it.
    note: str = ""
    #: For DISPUTED: what each reader said. For IMPLICATED: empty.
    options: tuple = ()
    #: For IMPLICATED: the rule that objected, and what it said.
    why: str = ""
    #: The PERSON'S verdict this line replaces, when it replaces one. The
    #: ledger is append-only, so a changed mind is a new line and this is how
    #: a reader of the file alone can tell a first answer from a second.
    supersedes: str = ""

    @property
    def id(self) -> str:
        raw = "␟".join(str(x) for x in
                           (self.stem, self.part,
                            self.addr or address(self.n, None), self.field))
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


def candidates(doc: Document, report: Report, arb: Arbitration) -> list[GoldRow]:
    """Rows both readers agreed on that no invariant implicated.

    A row named by ANY finding is excluded, even a flag: the point of a gold
    set is that it is not in doubt, and a row under suspicion is exactly the
    row a later measurement must not be scored against.
    """
    # THREE SETS, NOT ONE. A single (part, n) set cannot hold both "row 7 of
    # part A is in doubt" and "all of part A is in doubt", because an
    # unnumbered row's n is also None — so one dispute on a row with no
    # printed number silently condemned its entire part, and the gold set came
    # back empty from every document read whole (2026-09-23). Two meanings of
    # None is one too many.
    suspect_rows: set[tuple] = set()          # (part, n), n an int
    suspect_parts: set = set()                # the whole part
    suspect_donors: set[tuple] = set()        # (part, donor_key)
    for f in report.findings:
        if f.rule in NOT_DISQUALIFYING:
            continue
        for n in (f.rows or ()):
            suspect_rows.add((f.part, n))
        for k in (f.donors or ()):
            suspect_donors.add((f.part, k))
        if not f.rows and not f.donors:
            suspect_parts.add(f.part)
    for d in arb.disputes:
        if d.n is not None:
            suspect_rows.add((d.part, d.n))
        else:
            suspect_donors.add((d.part, donor_key(d.donor)))

    # ONE SEQUENCE, ONE SET OF ADDRESSES. The occurrence index that makes an
    # unnumbered row addressable must be counted over the SAME list the
    # address is later resolved against. Counting it over `arb.agreed` and
    # resolving it against `doc.rows` gave every agreed row the address of a
    # different row — usually one with no amount — so the field loop dropped
    # it and the gold set came back empty from documents whose rows were
    # perfectly fine (2026-09-23, found after four fixes that each changed
    # nothing, by printing the exclusion for every row instead of reasoning
    # about it).
    #
    # `arb.agreed` is a subset of the merged rows in the same order, so one
    # forward scan pairs them.
    addrs: list[str] = []
    seen: dict[tuple, int] = {}
    for r in doc.rows:
        key = (r.part, donor_key(r.donor))
        i = seen.get(key, 0)
        seen[key] = i + 1
        addrs.append(address(r.n, r.donor, i))

    dbg = os.environ.get("DOCREAD_GOLD_DEBUG")
    out: list[GoldRow] = []
    for r, addr in zip(doc.rows, addrs):
        if not r.agreed:
            continue
        if malformed(r):
            continue          # C423: a row that did not parse is a finding
        if dbg:
            print(f"[gold] agreed row part={r.part!r} n={r.n} "
                  f"key={donor_key(r.donor)[:24]!r} amt={r.amount!r} "
                  f"date={r.date!r} part_susp={r.part in suspect_parts} "
                  f"row_susp={(r.part, r.n) in suspect_rows} "
                  f"donor_susp={(r.part, donor_key(r.donor)) in suspect_donors} "
                  f"named={r.part in NAMED_DONOR_PARTS}", flush=True)
        if r.part in suspect_parts:
            continue
        if r.n is not None and (r.part, r.n) in suspect_rows:
            continue
        if (r.part, donor_key(r.donor)) in suspect_donors:
            continue
        for field in FIELDS:
            v = getattr(r, field)
            if v is None:
                continue
            if field == "donor" and r.part not in NAMED_DONOR_PARTS:
                continue
            out.append(GoldRow(doc.stem, r.part, r.n, field, v, AGREED,
                               source=doc.source, page=r.page, addr=addr))
    return out


#: How many implicated rows one finding may offer. A part-level rule such as
#: `sum_matches_stated_total` says "some row in this part is wrong" without
#: saying which, so it implicates every row in it — 60 rows on a National
#: return. Offering all of them is the same as offering none: the person
#: cannot see where to look. The biggest money goes first, because that is
#: where being wrong costs most and where a reader's error is most visible.
PER_FINDING = 12

#: The generation of the code that MADE a contested candidate. Bumped whenever
#: a fix changes which cells are worth asking about, so that questions produced
#: by a reader we have since corrected stop being served.
#:
#: "c422" is the first: before it, `arbitrate._align` paired rows by position
#: inside a replace block, so a "dispute" could be two DIFFERENT rows' amounts
#: and the page shown could be another row's page. Arthur ruled on two such
#: cells and both were wrong. Those questions are not re-asked — they are
#: withdrawn, because they were never questions.
#:
#: A CONFIRMED or REJECTED row is exempt: a person's word is not a generation
#: of the code, and it outlives every fix.
CONTESTED_GEN = "c422"


def contested(doc: Document, report: Report, arb: Arbitration,
              *, per_finding: int = PER_FINDING) -> list[GoldRow]:
    """The cells `candidates` refuses — where a person's answer RESOLVES.

    Arthur, 2026-09-23, on the agreed tier: *"this is the change that makes
    your time worth more than the calibration."* `candidates` offers only what
    both readers agreed on with no rule objecting, which is by construction
    the cells we were already right about. This offers the other two kinds:

      DISPUTED    the readers returned different values for the same cell.
                  Both readings travel with it, so the answer is a CHOICE, not
                  a transcription — and choosing is cheap where transcribing
                  is not.
      IMPLICATED  a rule named this row, this donor, or this part. The rule's
                  own sentence travels with it, so the person is told what is
                  wrong before being asked to look.

    A cell is offered ONCE, disputed before implicated: a disputed cell is
    already the sharper question, and asking it twice wastes the answer.
    Nothing here is gold until a person says so — every row comes back at the
    AGREED tier, exactly like a `candidates` row, because the tier is the
    verdict and these have had none.
    """
    addrs: list[str] = []
    seen: dict[tuple, int] = {}
    for r in doc.rows:
        key = (r.part, donor_key(r.donor))
        i = seen.get(key, 0)
        seen[key] = i + 1
        addrs.append(address(r.n, r.donor, i))
    by_addr = {(r.part, a): r for r, a in zip(doc.rows, addrs)}

    out: list[GoldRow] = []
    taken: set[tuple] = set()

    def offer(row: Row, addr: str, field: str, value, kind: str,
              options=(), why: str = "") -> None:
        if value is None or (field, doc.stem, row.part, addr) in taken:
            return
        if malformed(row):
            # C423, and the reason this class exists at all: 43 of the first
            # 55 implicated cells asked Arthur about a row whose donor was a
            # column header, the Yes/No column, or nothing. `rows_parse_cleanly`
            # reports those; a person is never asked to confirm one.
            return
        if field == "donor" and row.part not in NAMED_DONOR_PARTS:
            return
        taken.add((field, doc.stem, row.part, addr))
        out.append(GoldRow(doc.stem, row.part, row.n, field, value, AGREED,
                           source=doc.source, page=row.page, addr=addr,
                           kind=kind, options=tuple(options), why=why,
                           gen=CONTESTED_GEN))

    # ---- 1. the disputes the POLICY has not already settled ---------------
    # `arbitrate.TRUSTED_FOR` names, per field, the reader that wins: donor
    # goes to the transcriber, date to either, and AMOUNT TO NEITHER. So a
    # donor disagreement is not an open question — `merge` has already taken
    # the transcriber's word for it, and asking about it spends a person's
    # attention on a decision the estate made on purpose. Measured on Green
    # 2023 the day this was written: 132 disputed cells, of which only the
    # amounts were real questions; the donor ones were the geometric reader
    # returning an address fragment against a full transcription, which is
    # exactly the failure the policy exists to absorb.
    from .arbitrate import TRUSTED_FOR
    for d in arb.disputes:
        if TRUSTED_FOR.get(d.field) is not None:
            continue
        # a dispute is addressed the way the merged row is, so the verdict
        # lands on the cell the product actually serves
        addr = address(d.n, d.donor, 0)
        row = by_addr.get((d.part, addr))
        if row is None:
            row = next((r for r, a in zip(doc.rows, addrs)
                        if r.part == d.part and (r.n == d.n if d.n is not None
                                                 else donor_key(r.donor or "") == donor_key(d.donor or ""))), None)
            if row is None:
                continue
            addr = addrs[doc.rows.index(row)]
        first = d.values[0][1] if d.values else None
        offer(row, addr, d.field, first, DISPUTED, options=d.values,
              why=f"the readers disagree: {d.summary()}")

    # ---- 2. the implicated rows, worst finding first ----------------------
    order = list(report.fails) + list(report.flags)
    for f in order:
        if f.rule in NOT_DISQUALIFYING:
            continue
        # EXACTLY the inverse of `candidates`' exclusion, and written to mirror
        # it line for line. A finding that names rows or donors implicates
        # those and nothing else; only a finding that names NEITHER puts its
        # whole part in doubt. Falling back to the part whenever the named row
        # was not read (row 3 missing from a document that has 1, 2 and 4)
        # made the two classes offer the same cells — caught by the partition
        # test, which exists because that confusion is the thing this second
        # class was built to end.
        if f.rows or f.donors:
            named = [(r, a) for r, a in zip(doc.rows, addrs)
                     if (f.rows and r.n in f.rows)
                     or (f.donors and donor_key(r.donor or "") in f.donors)]
        elif f.part is not None:
            named = [(r, a) for r, a in zip(doc.rows, addrs) if r.part == f.part]
        else:
            named = []
        if not named:
            continue
        named.sort(key=lambda ra: -(ra[0].amount or 0))
        why = f"{f.rule}: {f.detail}"
        for row, addr in named[:per_finding]:
            for field in FIELDS:
                offer(row, addr, field, getattr(row, field), IMPLICATED, why=why)
    return out


# --- the ledger ------------------------------------------------------------

def _rows(path: pathlib.Path):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except ValueError:
            continue


#: How far a part's READ sum may exceed the total the party itself stated
#: before the reading is not a reading. 5% is comfortably above rounding, and
#: nothing hinges on the number: measured over the whole implicated queue,
#: 2% and 5% withdraw the IDENTICAL 1,691 cells, because real over-reads run
#: 2x to 34x and marginal ones essentially do not occur.
OVER_READ_MARGIN = 0.05


def over_read(reconcile: dict | None, part: str | None,
              margin: float = OVER_READ_MARGIN) -> bool:
    """Did the reader produce MORE money in this part than the party declared?

    Arthur, 2026-09-24, rejecting five amounts on `National-Annual-Return-2025`:
    *"i cant find the number on this page"*, *"I dont see how this number fits
    in the logic of this table and neither do I see a similar number that
    could be the source of a miss read"*, then *"third example"*, *"4th
    example"*, *"5th example"*. He was right about all five: $930,000.00,
    $911,902.31, $910,025.64, $511,109.75 and $235,001.69 appear NOWHERE in
    that document, on any page.

    THE ASYMMETRY IS THE WHOLE RULE. Under-reading a part is normal and
    honest — rows wrap, scans are bad, we miss some. OVER-reading it is
    impossible: Part A itemises donations up to the total the party printed at
    the head of the same part, so a read sum above the stated total is money
    the reader made up. National 2025 read $9,186,930.51 against a stated
    $2,727,334.14, from a document whose PRODUCTION register reads 148 rows
    summing to $2,727,334.14 exactly. The document was never the problem.

    So no answer to a cell in such a part can be right, and asking for one
    spends the scarcest thing in the estate on our own defect. The cells are
    withdrawn and become a READER worklist instead of a review queue — the
    same move as the malformed-donor withdrawal (C423/C424) and the evidence
    expiry (C430(a)), one level up: from the cell to the part it sits in.

    A verdict a person has already given is exempt, as always. Their word is
    not a generation of our code.
    """
    r = ((reconcile or {}).get(part or "") or {})
    stated = r.get("stated")
    if not stated or stated <= 0:
        return False          # no stated total: nothing to be over
    return (r.get("read") or 0) > stated * (1 + margin)


def evidence_id(row: GoldRow) -> str:
    """A fingerprint of WHAT THE PERSON WAS SHOWN when they answered.

    C430(a), out of Arthur's own comments. Every one of his seven gold
    abstentions is a sentence about the EVIDENCE and not about the reader:
    "blended cells", "too many dates on the page for me to find this one. it
    could be there", "this is an extraction issue, I cant identify which one
    is or is not correct". All three of his converted identity ones say the
    same thing in one phrase — *"we need some corroborating information"*.

    Those are not answers, they are a WORKLIST: each names a presentation the
    surface could not put an answerable question on. And a worklist is only
    worth keeping if something notices when the work is done. Nothing did —
    an abstention withdrew the cell for good, so a cell Arthur could not judge
    because the reader blended two rows stayed withdrawn after the reader was
    fixed, and the question he was waiting to be asked was never asked again.

    So the fingerprint covers the EVIDENCE and nothing else: the value shown,
    the rule's own sentence, what each reader said, and the page it came from.
    Not the tier, not the note, not who answered — those are the ANSWER, and
    an answer changing is not evidence changing.
    """
    raw = "\u241f".join(str(x) for x in (
        row.value, row.why, tuple(tuple(o) for o in (row.options or ())), row.page))
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


#: The verdicts that are about a READING, and therefore expire when the
#: reading changes. CONFIRMED is deliberately not among them: it says what
#: THE PAGE says, which no re-read can make untrue, and it is the only tier
#: `score` will let a correctness claim be made against. REJECTED and
#: ABSTAINED both say something about a particular reading being unusable —
#: "both readers got this wrong", "I could not answer this as put" — and
#: neither is a statement about a reading nobody has produced yet.
ABOUT_A_READING = (REJECTED, ABSTAINED)


def latest(path: pathlib.Path) -> dict[str, GoldRow]:
    """The LAST line per cell, whatever its tier.

    `load` deliberately lets a person's word beat a later machine agreement,
    which is right for serving and wrong for asking "has the evidence moved
    since they answered". This is the raw tail, and it is only ever used to
    answer that question.
    """
    out: dict[str, GoldRow] = {}
    for d in _rows(path):
        try:
            g = GoldRow(**d)
        except TypeError:
            continue
        out[g.id] = g
    return out


def load(path: pathlib.Path) -> dict[str, GoldRow]:
    """The gold set, CONFIRMED beating agreed for the same cell."""
    out: dict[str, GoldRow] = {}
    for d in _rows(path):
        try:
            g = GoldRow(**d)
        except TypeError:
            continue
        prior = out.get(g.id)
        # A person's word beats a machine agreement, and a rejection beats
        # both: it is the most recent thing a person said about this cell.
        if prior is None or g.tier in HUMAN_VERDICTS \
                or prior.tier == g.tier:
            out[g.id] = g
    return out


def stage(rows, path: pathlib.Path) -> int:
    """Append candidates not already pinned. Returns how many were new."""
    rows = [GoldRow(**r) if isinstance(r, dict) else r for r in rows]
    known = load(path)
    fresh = [g for g in rows
             if g.id not in known or known[g.id].tier != g.tier]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        for g in fresh:
            fh.write(json.dumps(dataclasses.asdict(g), default=str) + "\n")
    return len(fresh)


def confirm(stem: str, part, n: int | None, field: str, value, path: pathlib.Path,
            *, by: str = "", source: str | None = None,
            page: int | None = None, addr: str = "",
            tier: str = CONFIRMED) -> GoldRow:
    """A person looked at the scan and said what it says. Ground truth."""
    if tier not in HUMAN_VERDICTS:
        raise ValueError(f"a person's verdict is one of {HUMAN_VERDICTS}, "
                         f"not {tier!r}")
    g = GoldRow(stem, part, n, field, value, tier, by, source, page,
                addr or address(n, None))
    stage([g], path)
    return g


def assess(row_id: str, verdict: str, path: pathlib.Path, *, value=None,
           by: str = "", note: str = "") -> GoldRow:
    """Promote or reject one candidate BY ITS ID, keeping its address.

    The product's tab hands back an id, not a coordinate — it must not have to
    reconstruct how a row is addressed, and a rejection that landed on a
    different address would silently leave the candidate standing.
    """
    known = load(path)
    g = known.get(row_id)
    if g is None:
        raise KeyError(f"no gold row {row_id!r}")
    if verdict not in HUMAN_VERDICTS:
        raise ValueError(f"not a verdict: {verdict!r}")
    out = dataclasses.replace(
        g, tier=verdict, by=by, note=(note or "")[:1000],
        supersedes=(g.tier if g.tier in HUMAN_VERDICTS else ""),
        value=g.value if (verdict != CONFIRMED or value is None) else value)
    stage([out], path)
    return out


def from_resolutions(queue_path: pathlib.Path, gold_path: pathlib.Path) -> int:
    """Turn the queue's human verdicts into confirmed gold.

    `corrected` pins the value the person typed. `accepted` pins what the row
    already said — which is only meaningful for a dispute, where accepting
    means choosing one reader over another, so an accepted INVARIANT item
    pins nothing.
    """
    from . import queue as q
    items = {i.id: i for i in q.load_items(queue_path)}
    got = 0
    for item_id, r in q.resolutions(queue_path).items():
        it = items.get(item_id)
        if it is None or it.n is None or not it.field:
            continue
        if r.verdict == q.CORRECTED and r.value not in (None, ""):
            value = r.value
        elif r.verdict == q.ACCEPTED and it.kind == "dispute" and it.values:
            value = dict(it.values).get("geometry+glm-ocr")
            if value is None:
                continue
        else:
            continue
        got += stage([GoldRow(it.stem, it.part, it.n, it.field, value,
                              CONFIRMED, r.by, it.source, it.page,
                              address(it.n, it.donor, 0))], gold_path)
    return got


# --- measuring against it ---------------------------------------------------

def score(doc: Document, gold: dict[str, GoldRow], *, tier: str) -> dict:
    """Measure one reader against ONE tier of the gold set.

    `tier` is required and not defaulted, so a caller must say which claim
    they are making. A number against `agreed` is a claim about agreement; a
    number against `confirmed` is a claim about correctness.
    """
    if tier not in (AGREED, CONFIRMED):
        raise ValueError(f"score against which tier? not {tier!r}")
    pins = [g for g in gold.values()
            if g.tier == tier and g.stem == doc.stem]
    # A rejected or abstained cell is not scored under any tier.
    #
    # C424, 2026-09-23: nor is a DONOR cell that holds an address. The guard
    # that refuses those at staging time was too narrow until today — it
    # required the cell to start with a bare house number — so 192 of them
    # were staged anyway, 171 at AGREED and 15 CONFIRMED by a person who was
    # being asked "is this what the form says" about text that IS on the form,
    # just not in that column. The verdicts stand in the ledger: a person's
    # word outlives our fixes (ruling 340), and it is not withdrawn here. What
    # is withdrawn is its use as GROUND TRUTH, because a gold cell saying a
    # donor is named "161 Barnard Street Wellington" would mark a correct
    # reader wrong for ever after. The count is returned, never hidden.
    unfit = [g for g in pins if g.field == "donor"
             and isinstance(g.value, str)
             and malformed(Row(part=g.part, n=g.n, donor=g.value,
                               amount=None, date=None))]
    if unfit:
        pins = [g for g in pins if g not in unfit]
    by_addr: dict[tuple, "Row"] = {}
    seen: dict[tuple, int] = {}
    for r in doc.rows:
        i = seen.get((r.part, donor_key(r.donor)), 0)
        seen[(r.part, donor_key(r.donor))] = i + 1
        by_addr[(r.part, address(r.n, r.donor, i))] = r
    correct = wrong = missing = 0
    misses = []
    for g in pins:
        row = by_addr.get((g.part, g.addr or address(g.n, None, 0)))
        got = getattr(row, g.field, None) if row else None
        if got is None:
            missing += 1
            misses.append({"addr": g.addr, "field": g.field,
                           "want": g.value, "got": None})
        elif _same(g.field, got, g.value):
            correct += 1
        else:
            wrong += 1
            misses.append({"addr": g.addr, "field": g.field,
                           "want": g.value, "got": got})
    n = correct + wrong + missing
    return {"tier": tier, "pins": n, "correct": correct, "wrong": wrong,
            "withdrawn_malformed": len(unfit),
            "missing": missing,
            "accuracy": round(correct / n, 4) if n else None,
            "basis": (f"{correct} of {n} {tier} gold cell(s) for {doc.stem}"
                      if n else f"no {tier} gold for {doc.stem}"),
            "misses": misses[:20]}


def _same(field: str, a, b) -> bool:
    if field == "amount":
        try:
            return abs(float(a) - float(b)) <= 0.005
        except (TypeError, ValueError):
            return False
    if field == "donor":
        return donor_key(str(a)) == donor_key(str(b))
    return str(a) == str(b)
