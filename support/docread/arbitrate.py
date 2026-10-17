"""Two readers, compared — so an error stops being silent.

Arthur, 2026-09-23: *"Is this a possible solution: using a number of diverse
approaches and using the disagreements to flag gaps?"* It is, and it is the
only one of these layers that finds errors nothing else can see. An invariant
catches a read that contradicts the DOCUMENT. Two independent readers catch a
read that is internally consistent and simply wrong — the rotation case, where
every amount on the page is present, the total reconciles, and four donors sit
beside somebody else's money.

WHAT MAKES IT WORK IS INDEPENDENCE. Two readers that share an engine share
their mistakes, and agreement between them means nothing. The pairing this
service is built for is a GEOMETRIC reader (table structure from ruling lines,
cells by coordinate) against a GENERATIVE one (a transcriber reading the page
as a whole). They fail differently: the first loses a faint rule, the second
invents a plausible column. Neither failure reproduces in the other.

ALIGNMENT IS THE WHOLE PROBLEM. Comparing reader A's row 7 against reader B's
row 7 is what produced four false findings on 2026-09-22: if B dropped a row,
every later comparison is off by one and the report fills with disagreements
that are one alignment error. So rows are aligned by SEQUENCE MATCHING on the
donor names — a dropped row shows up as a gap, which is a finding in itself,
and the rows around it stay correctly paired.

AGREEMENT IS NOT CORRECTNESS. Two readers agreeing is evidence, not proof;
identical failures are rare, not impossible. What this module produces is a
partition — agreed, disputed, seen-by-one — and the honest claim is about the
partition, never about truth.
"""
from __future__ import annotations

import dataclasses
import difflib

from .invariants import Finding
from .rows import Document, Row, donor_key, donor_name

#: Money either side of this is the same money.
CENT = 0.005


@dataclasses.dataclass(frozen=True)
class Dispute:
    """One field of one row that the readers did not agree on."""
    part: str | None
    n: int | None
    donor: str | None
    field: str
    values: tuple[tuple[str, object], ...]   # (reader, value), reader-sorted
    page: int | None = None
    bbox: tuple[float, float, float, float] | None = None
    dpi: int | None = None

    def summary(self) -> str:
        vs = ", ".join(f"{r}={v!r}" for r, v in self.values)
        where = f"row {self.n}" if self.n is not None else f"{self.donor!r}"
        return f"part {self.part} {where}: {self.field} — {vs}"


@dataclasses.dataclass(frozen=True)
class Arbitration:
    stem: str
    source: str | None = None
    readers: tuple[str, ...] = ()
    agreed: tuple[Row, ...] = ()
    disputes: tuple[Dispute, ...] = ()
    findings: tuple[Finding, ...] = ()
    uncompared: tuple[Row, ...] = ()

    @property
    def rows_compared(self) -> int:
        """Rows EVERY reader saw. The only honest denominator for agreement."""
        return len(self.agreed) + len({(d.part, d.n, d.donor)
                                       for d in self.disputes})

    @property
    def agreement(self) -> float:
        """Of the rows every reader saw, the fraction they agreed on in full.

        NEVER quote this without `coverage`. A reader that found one row and
        agreed on it scores 100% here; `coverage` is what says the figure
        rests on one row out of sixty. Both numbers or neither — this is the
        shape of the mistake made on 2026-09-22, when three disagreements
        across 554 documents rested on 26.
        """
        total = self.rows_compared
        return len(self.agreed) / total if total else 0.0

    @property
    def coverage(self) -> float:
        """The fraction of rows that could be compared at all."""
        total = self.rows_compared + len(self.uncompared)
        return self.rows_compared / total if total else 0.0

    def basis(self) -> str:
        """The sentence that must travel with the agreement figure.

        A SINGLE READING SAYS SO INSTEAD OF SCORING ITSELF (C308): with one
        reader `rows_compared` is 0, so `agreement` is 0.0, and "0% agreement"
        reads as a disaster when the truth is that nothing was compared.
        """
        if len(self.readers) < 2:
            who = self.readers[0] if self.readers else "unknown"
            return (f"one reading ({who}): nothing compared, "
                    f"{len(self.uncompared)} row(s) from a single reader")
        return (f"{self.agreement:.0%} agreement across {self.rows_compared} "
                f"row(s) both readers saw; {len(self.uncompared)} row(s) "
                f"only one reader saw and were not compared")


def _spine(docs: list[Document], part: str) -> Document:
    """The reader that found the most rows in this part leads the alignment."""
    return max(docs, key=lambda d: len(d.part(part)))


def _align(spine: list[Row], other: list[Row]) -> list[tuple[Row | None, Row | None]]:
    """Pair rows by donor-name sequence, so a dropped row leaves a GAP.

    Position-based comparison shifts every later row when one is missing and
    reports a page of disagreements for a single cause. Sequence matching
    localises the loss.
    """
    a = [donor_key(r.donor) for r in spine]
    b = [donor_key(r.donor) for r in other]
    # A PART WITH NO DONOR NAMES CANNOT BE ALIGNED BY NAME (C463, 2026-10-10).
    # Part G is three banded AGGREGATES and prints no donor, so every key on
    # both sides is the empty string and `SequenceMatcher` reports one long
    # `equal` block however the amounts actually line up. Two consequences,
    # both measured on ACT 2025 page 3 when two readers still ran:
    #
    #   * where the readers found the same number of rows, the zip below pairs
    #     them BY POSITION — the chimera C422 fixed for named rows and left
    #     standing here, because a replace block never forms;
    #   * where they found different numbers, the remainder falls to
    #     insert/delete, `merge` keeps the unpaired character row as a row of
    #     its own, and one printed line is emitted TWICE — once addressed
    #     `n=10` and once `d=…#0`. That is C463, and `gold_queue`'s
    #     `numberless_twins` has been withdrawing the second copy at read time
    #     since 2026-09-28 while the emission stayed open.
    #
    # So a donorless part pairs on EVIDENCE, through the function this module
    # already uses when names are useless — a pair must earn the pairing. It
    # cannot merge two different lines: `_corroboration` requires a positive
    # agreement on n, amount or date, and a row that corroborates with nothing
    # goes out unpaired, which is the honest outcome.
    #
    # DORMANT TODAY AND PINNED ANYWAY: one reader has run since 2026-09-25, so
    # `arbitrate` is reached only with a second reading. A second OCR model
    # brings this straight back, which is why it is fixed before one arrives.
    if not any(a) and not any(b):
        return _pair_replace(spine, other)
    out: list[tuple[Row | None, Row | None]] = []
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.extend(zip(spine[i1:i2], other[j1:j2]))
        elif tag == "replace":
            # Same span, different names. Pairing by POSITION here was the
            # single worst bug this module has had (C422, 2026-09-23): geometry
            # garbles the donor cell, so a whole part A arrives as one replace
            # block, and where the readers found different row counts every
            # later pair was a CHIMERA — the transcriber's donor carried on
            # geometry's page with geometry's amount. Arthur was served page 5
            # for `Allan D Johnson`, who is printed on page 4, and offered
            # 12,500.00 (the amount of a row he could see) against the printed
            # 11,000.00. A pair must now EARN the pairing.
            out.extend(_pair_replace(spine[i1:i2], other[j1:j2]))
        elif tag == "delete":
            out.extend((r, None) for r in spine[i1:i2])
        elif tag == "insert":
            out.extend((None, r) for r in other[j1:j2])
    return out


#: What can corroborate a pairing when the donor names do not match. Never the
#: donor: inside a `replace` block the donor keys differ by definition, which
#: is the whole reason it is a replace.
_CORROBORATES = ("n", "amount", "date")


def _corroboration(x: Row, y: Row) -> int:
    """How many fields positively agree that these are the SAME filed row."""
    return sum(1 for f in _CORROBORATES
               if getattr(x, f) is not None and getattr(y, f) is not None
               and _same(f, getattr(x, f), getattr(y, f)))


def _pair_replace(xs: list[Row], ys: list[Row]) -> list[tuple[Row | None, Row | None]]:
    """Pair a replace block on EVIDENCE, never on position.

    A row pairs with the unused candidate that corroborates on the most
    fields, ties going to the nearest position — and a row that corroborates
    with nothing goes out unpaired. Unpaired is the honest outcome: the merge
    then builds no row from two readers that never agreed on anything, and the
    completeness checks see a row each reader saw alone, which is a finding a
    person can act on. The old behaviour manufactured a dispute out of two
    different rows' amounts, which is a question nobody can answer.
    """
    out: list[tuple[Row | None, Row | None]] = []
    used: set[int] = set()
    for i, x in enumerate(xs):
        best, best_score = None, 0
        for j, y in enumerate(ys):
            if j in used:
                continue
            score = _corroboration(x, y)
            if score > best_score or (score == best_score and score > 0
                                      and best is not None
                                      and abs(j - i) < abs(best - i)):
                best, best_score = j, score
        if best is None:
            out.append((x, None))
        else:
            used.add(best)
            out.append((x, ys[best]))
    out.extend((None, y) for j, y in enumerate(ys) if j not in used)
    return out


def _value(row: Row | None, field: str):
    return None if row is None else getattr(row, field)


def _same(field: str, x, y) -> bool:
    if x is None or y is None:
        return x is y
    if field == "amount":
        return abs(float(x) - float(y)) <= CENT
    if field == "donor":
        return donor_key(x) == donor_key(y)
    return x == y


def arbitrate(docs: list[Document], *, fields=("donor", "date", "amount"),
              ) -> Arbitration:
    """Compare every reader's rows. Returns the partition, not a verdict."""
    docs = [d for d in docs if d.rows or d.reader]
    if len(docs) < 2:
        raise ValueError("arbitration needs at least two readers")
    stem = docs[0].stem
    readers = tuple(d.reader or f"reader{i}" for i, d in enumerate(docs))
    agreed: list[Row] = []
    disputes: list[Dispute] = []
    findings: list[Finding] = []
    uncompared: list[Row] = []

    parts = sorted({p for d in docs for p in d.parts()})
    for part in parts:
        spine_doc = _spine(docs, part)
        spine = list(spine_doc.part(part))
        others = [d for d in docs if d is not spine_doc]
        # reader -> its row aligned to each spine row (None where it saw none)
        aligned: dict[str, list[Row | None]] = {}
        for d in others:
            name = d.reader or "?"
            pairs = _align(spine, list(d.part(part)))
            by_spine: dict[int, Row | None] = {}
            extras = [o for s, o in pairs if s is None and o is not None]
            for s, o in pairs:
                if s is not None:
                    by_spine[id(s)] = o
            aligned[name] = [by_spine.get(id(s)) for s in spine]
            for o in extras:
                uncompared.append(o)
                findings.append(Finding(
                    "seen_by_one_reader", "flag",
                    f"part {part}: only {name} read a row for "
                    f"{donor_name(o.donor)!r} (${(o.amount or 0):,.2f})", part,
                    (o.n,) if o.n is not None else ()))

        spine_name = spine_doc.reader or "?"
        for i, srow in enumerate(spine):
            row_disputes: list[Dispute] = []
            missing = [r for r, rows in aligned.items() if rows[i] is None]
            if missing:
                uncompared.append(srow)
            for name in missing:
                findings.append(Finding(
                    "seen_by_one_reader", "flag",
                    f"part {part}: {name} read no row for "
                    f"{donor_name(srow.donor)!r} that {spine_name} read "
                    f"(${(srow.amount or 0):,.2f})", part,
                    (srow.n,) if srow.n is not None else ()))
            present = {n: rows[i] for n, rows in aligned.items()
                       if rows[i] is not None}
            for field in fields:
                base = _value(srow, field)
                vals = {spine_name: base}
                for name, row in present.items():
                    vals[name] = _value(row, field)
                distinct = []
                for v in vals.values():
                    if not any(_same(field, v, d) for d in distinct):
                        distinct.append(v)
                if len(distinct) > 1:
                    row_disputes.append(Dispute(
                        part, srow.n, donor_name(srow.donor), field,
                        tuple(sorted(vals.items())), srow.page, srow.bbox,
                        srow.dpi))
            if missing:
                # Not compared: at least one reader had nothing to say here.
                disputes.extend(row_disputes)
            elif row_disputes:
                disputes.extend(row_disputes)
            else:
                agreed.append(srow)
    return Arbitration(stem, docs[0].source, readers, tuple(agreed),
                       tuple(disputes), tuple(findings), tuple(uncompared))


#: Which reader is believed for which field, and why. Stated here rather than
#: buried in the merge, because it is a policy and policies must be arguable.
#:
#:   structure  geometry — which rows exist and what the form numbers them.
#:              Measured on National 2017 p3: 24 of 24 rows, 24 of 24 numbers,
#:              against a transcriber that kept the number column on one page
#:              and dropped it on the next.
#:   donor      the transcriber — measurably better characters. Geometry read
#:              'Lane Capital Group' as 'tans Capital Group'.
#:   amount     NEITHER. Agreement is required; a disagreement is queued, not
#:              resolved by preference. Money is the field the register is
#:              for, and there is no reader good enough to be believed alone.
#:   date       whichever read one, agreement preferred.
TRUSTED_FOR = {"structure": "geometry", "donor": "transcriber",
               "amount": None, "date": "either"}


def merge(structure: Document, characters: Document, *,
          policy: dict | None = None) -> tuple[Document, Arbitration]:
    """One document from two readers, plus the record of where they differed.

    The invariants must run on THIS, not on either reader alone. Run on the
    geometric reader, `donor_aggregate_above_threshold` groups by a garbled
    name and flags one donor as four, each below the threshold — a page of
    findings caused entirely by the reader whose characters we already know
    not to trust. Run on the transcriber alone, `row_numbers_complete` cannot
    decide at all, because the column it needs was dropped.
    """
    policy = policy or TRUSTED_FOR
    arb = arbitrate([structure, characters])
    # By identity: whichever reader led the alignment, its row object is the
    # one recorded as agreed.
    agreed_ids = {id(r) for r in arb.agreed}
    # Keyed by the ROW, and an unnumbered row's number is None — so keying on
    # (part, n) alone puts EVERY unnumbered row of a part in one bucket, and
    # one dispute anywhere in part G blanked the amount of every unnumbered
    # part G row, agreed ones included. That is what made the gold set empty:
    # not a filter rejecting rows, but the merge handing it rows whose every
    # field was None. Same collision as in `gold.candidates`, fixed there
    # first and missed here (2026-09-23).
    def _dkey(part, n, donor):
        return (part, n) if n is not None else (part, donor_key(donor or ""))

    disputed: dict[tuple, set[str]] = {}
    for d in arb.disputes:
        disputed.setdefault(_dkey(d.part, d.n, d.donor), set()).add(d.field)

    out: list[Row] = []
    for part in sorted({p for d in (structure, characters) for p in d.parts()}):
        spine = list(structure.part(part))
        pairs = dict(_align(spine, list(characters.part(part))))
        for srow in spine:
            crow = pairs.get(srow)
            fields = disputed.get(_dkey(part, srow.n, srow.donor), set())
            donor = srow.donor
            if crow is not None and policy.get("donor") == "transcriber":
                donor = crow.donor or srow.donor
            date = srow.date or (crow.date if crow else None)
            amount = srow.amount
            if crow is not None and "amount" in fields:
                amount = None          # not resolved by preference: queued
            elif crow is not None and crow.amount is not None:
                amount = crow.amount if srow.amount is None else srow.amount
            out.append(dataclasses.replace(
                srow, donor=donor, date=date, amount=amount,
                reader=f"{structure.reader}+{characters.reader}",
                agreed=(id(srow) in agreed_ids
                        or (crow is not None and id(crow) in agreed_ids))))
        # Rows only the character reader saw are kept: a row is a row, and
        # losing it would hide it from every completeness check.
        seen = {id(v) for v in pairs.values() if v is not None}
        for crow in characters.part(part):
            if id(crow) not in seen:
                # The flag matters MOST here. `arbitrate` leads its alignment
                # with whichever reader found more rows, so on a part where
                # the transcriber leads, the agreed rows are character rows —
                # and these, matched to no structure row, are exactly the ones
                # that land in this tail. Leaving the flag off here meant no
                # document produced any gold at all (2026-09-23).
                out.append(dataclasses.replace(
                    crow, reader=f"{characters.reader}-only",
                    agreed=id(crow) in agreed_ids))
    merged = Document(stem=structure.stem, rows=tuple(out),
                      stated_totals={**characters.stated_totals,
                                     **structure.stated_totals},
                      year=structure.year or characters.year,
                      pages=max(structure.pages, characters.pages),
                      reader=f"{structure.reader}+{characters.reader}",
                      source=structure.source or characters.source)
    return merged, arb
