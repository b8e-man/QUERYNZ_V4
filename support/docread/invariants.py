"""What must be true of a correctly-read filed return, checked without a model.

These are the cheapest error detectors the estate has and they were missing.
Every one is deterministic, runs in milliseconds, and turns a class of SILENT
failure into a loud one. The failure that prompted this service — twelve rows
read correctly and then discarded, and four amounts sitting beside the wrong
donors — is caught twice over by `row_numbers_complete` alone.

A RULE THAT CANNOT DECIDE MUST SAY SO. Every check returns either findings or
a SKIP with its reason, and a Report carries both. "No findings" is not a
result; "no findings, and here is what could not be checked" is. This is
ruling 325 applied to a gate: a figure states its basis. The audit this
service replaces reported three disagreements across 554 documents when it had
in fact examined 26, because nothing made it declare what it had not checked.

SEVERITY IS A ROUTING DECISION, NOT A JUDGEMENT.
  fail — the read contradicts the document. Do not serve it; re-read it.
  flag — the read may be right and cannot be trusted alone. Serve it, queue it.
"""
from __future__ import annotations

import collections
import dataclasses

from .rows import (Document, NAMED_DONOR_PARTS, Row, donor_key,
                   donor_name, malformed, name_key)

#: Money either side of this is the same money. Returns are filed to the cent.
CENT = 0.005

#: Part A discloses party donations ABOVE a statutory threshold, aggregated per
#: donor. The 2010 amendment raised it from $10,000 to $15,000 with effect from
#: 1 January 2011. **The Electoral Amendment Act 2022 lowered it to $5,000 with
#: effect from 1 January 2023** — the Commission says so on its own page, held
#: in this estate at `var/staging/ec-donations/index/live-mocracy-in-nz-
#: political-parties-in-new-zealand-party-donations-and-loans-by-year.html`:
#: *"The reporting requirements for parties changed on 1 January 2023. In their
#: returns this year, parties must report: the names of donors and contributors
#: who gave more than $5,000 (down from $15,000)"*. Before 2008 the regime
#: differs enough that this service ABSTAINS rather than assert a threshold it
#: has not checked.
#:
#: A STALE THRESHOLD DOES NOT FAIL, IT ACCUSES. Held at $15,000 through 2023-25
#: this table flagged 1,077 correctly-disclosed donors — every donor in the new
#: $5,000–$15,000 band — as "at or below the threshold that requires the
#: disclosure", and each one became a question in the review queue: 42% of
#: everything a person was waiting to be asked, from one number three years out
#: of date. The law is the sort of fact that is WRITTEN DOWN by the source; it
#: does not have to be inferred from the corpus and must not be.
THRESHOLDS = ((2023, 5000.0), (2011, 15000.0), (2008, 10000.0))


def threshold_for(year: int | None) -> float | None:
    if year is None:
        return None
    for first, amount in THRESHOLDS:
        if year >= first:
            return amount
    return None


@dataclasses.dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    detail: str
    part: str | None = None
    rows: tuple[int, ...] = ()
    #: The donors this finding is about, as `donor_key`s. A finding about
    #: particular donors on a form that prints no row numbers can name no
    #: rows, and a consumer that reads "no rows" as "the whole part" then
    #: condemns everything — which is how the gold set stayed empty across six
    #: whole documents on 2026-09-23. Name the donors instead.
    donors: tuple[str, ...] = ()


@dataclasses.dataclass(frozen=True)
class Report:
    """What was found AND what could not be looked at."""
    stem: str
    findings: tuple[Finding, ...] = ()
    checked: tuple[str, ...] = ()
    skipped: tuple[tuple[str, str], ...] = ()

    @property
    def fails(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity == "fail")

    @property
    def flags(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity == "flag")

    @property
    def servable(self) -> bool:
        """A read with no contradiction of the document. NOT 'correct'."""
        return not self.fails

    @property
    def coverage(self) -> float:
        """The fraction of rules that could decide. A low number means the
        report is thin, whatever it says — which is the thing the overnight
        audit could not express about itself."""
        total = len(self.checked) + len(self.skipped)
        return len(self.checked) / total if total else 0.0


# --- the rules -------------------------------------------------------------
# Each takes the document and returns (findings, skips). A rule NEVER raises.

def row_numbers_complete(doc: Document):
    """Every number the form prints, once. The single highest-value check.

    A dropped row leaves a hole; a row read twice leaves a duplicate; a page
    lost whole leaves a run. All three are invisible to a sum when the lost
    rows are also missing from the total, and invisible to everything when the
    reader simply never emitted them.
    """
    findings, skips = [], []
    if not doc.parts():
        skips.append(("row_numbers_complete", "the read produced no rows"))
        return findings, skips
    for part in doc.parts():
        rows = doc.part(part)
        ns = [r.n for r in rows if r.n is not None]
        if len(ns) != len(rows):
            skips.append((f"row_numbers_complete[{part}]",
                          f"{len(rows) - len(ns)} of {len(rows)} rows carry no "
                          f"printed row number, so completeness cannot be "
                          f"decided"))
            continue
        counts = collections.Counter(ns)
        dupes = sorted(n for n, c in counts.items() if c > 1)
        missing = sorted(set(range(min(ns), max(ns) + 1)) - set(ns))
        if missing:
            findings.append(Finding(
                "row_numbers_complete", "fail",
                f"part {part}: {len(missing)} printed row number(s) absent "
                f"from the read: {_runs(missing)}", part, tuple(missing)))
        if dupes:
            findings.append(Finding(
                "row_numbers_complete", "fail",
                f"part {part}: row number(s) read more than once: "
                f"{_runs(dupes)}", part, tuple(dupes)))
    return findings, skips


def row_numbers_start_at_one(doc: Document):
    """A part's rows begin at 1. A read starting at 13 lost a page."""
    findings, skips = [], []
    if not doc.parts():
        skips.append(("row_numbers_start_at_one", "the read produced no rows"))
        return findings, skips
    for part in doc.parts():
        rows = doc.part(part)
        ns = [r.n for r in rows if r.n is not None]
        if len(ns) != len(rows):
            skips.append((f"row_numbers_start_at_one[{part}]",
                          f"{len(rows) - len(ns)} of {len(rows)} rows carry no "
                          f"printed row number"))
            continue
        if min(ns) != 1:
            findings.append(Finding(
                "row_numbers_start_at_one", "fail",
                f"part {part}: the read begins at row {min(ns)}, so rows "
                f"1–{min(ns) - 1} were never read", part,
                tuple(range(1, min(ns)))))
    return findings, skips


def sum_matches_stated_total(doc: Document):
    """The amounts add to the total the FORM prints, not to one we computed."""
    findings, skips = [], []
    if not doc.parts():
        skips.append(("sum_matches_stated_total", "the read produced no rows"))
        return findings, skips
    for part in doc.parts():
        stated = doc.stated_totals.get(part)
        if stated is None:
            skips.append((f"sum_matches_stated_total[{part}]",
                          "the form's own total for this part was not read"))
            continue
        amounts = [r.amount for r in doc.part(part) if r.amount is not None]
        if not amounts:
            skips.append((f"sum_matches_stated_total[{part}]",
                          "no row in this part carries an amount"))
            continue
        got = round(sum(amounts), 2)
        if abs(got - stated) > CENT:
            findings.append(Finding(
                "sum_matches_stated_total", "fail",
                f"part {part}: rows sum to ${got:,.2f}, the form states "
                f"${stated:,.2f}, short ${stated - got:,.2f}", part))
    return findings, skips


def declared_total_matches_parts(doc: Document):
    """The read parts add to the total the RETURN declares for itself.

    WHY THIS EXISTS (C418, 2026-10-10). `sum_matches_stated_total` needs the
    form's per-part total, and those came from the geometric reader reading the
    ruled table footer. That reader was retired on 2026-09-25 and **15 of the
    107 party returns in scope lost every stated total with it** — Labour 2021,
    Te Pāti Māori 2025 and NZ First's amended return among them — so no
    invariant could say anything about their arithmetic at all. A document with
    nothing to reconcile against is not a clean document; it is an unchecked
    one, and it looked identical to a clean one in the corpus row.

    The summary line on page 1 is the party's own arithmetic over its own
    parts, and 106 of the 107 print it. The parts come FROM the line, so a
    return that declares a different combination is held to the one it
    declared and not to a set this code assumed.

    ROWS WITH NO PART ARE NAMED IN THE FINDING. They cannot be in the sum —
    nothing says which part they belong to — so a shortfall that is really a
    part-header miss reads as a part-header miss instead of as missing money.
    """
    findings, skips = [], []
    if doc.declared_total is None:
        skips.append(("declared_total_matches_parts",
                      "the return prints no summary total for itself"))
        return findings, skips
    if not doc.rows:
        skips.append(("declared_total_matches_parts", "the read produced no rows"))
        return findings, skips
    wanted = set(doc.declared_parts)
    amounts = [r.amount for r in doc.rows
               if r.part in wanted and r.amount is not None]
    got = round(sum(amounts), 2)
    if abs(got - doc.declared_total) > CENT:
        orphans = sum(1 for r in doc.rows if not r.part and r.amount is not None)
        orphan_money = round(sum(r.amount for r in doc.rows
                                 if not r.part and r.amount is not None), 2)
        where = (f"; {orphans} row(s) carry no part at all, worth "
                 f"${orphan_money:,.2f}" if orphans else "")
        direction = ("over by" if got > doc.declared_total else "short by")
        findings.append(Finding(
            "declared_total_matches_parts", "fail",
            f"parts {'+'.join(doc.declared_parts)} read ${got:,.2f}, the "
            f"return declares ${doc.declared_total:,.2f}, {direction} "
            f"${abs(doc.declared_total - got):,.2f}{where}"))
    return findings, skips


def every_row_has_an_amount(doc: Document):
    """A row with no money is a row half read."""
    findings, skips = [], []
    bad = [r for r in doc.rows if r.amount is None]
    if bad:
        findings.append(Finding(
            "every_row_has_an_amount", "fail",
            f"{len(bad)} row(s) were read without an amount",
            rows=tuple(r.n for r in bad if r.n is not None)))
    if not doc.rows:
        skips.append(("every_row_has_an_amount", "the read produced no rows"))
    return findings, skips


def rows_parse_cleanly(doc: Document):
    """A row that did not parse is reported here and never offered as gold.

    C423, 2026-09-23. The gold tab was asking Arthur to confirm cells on rows
    whose donor was a column header or the Yes/No column. That is not a
    question a person can answer, and a `confirmed` verdict on one would make
    the reader's own failure into ground truth. It is also why the part sums
    were short: header bands were being counted as donations.
    """
    findings, skips = [], []
    bad = [(r, why) for r in doc.rows if (why := malformed(r))]
    if bad:
        for why in sorted({w for _, w in bad}):
            these = [r for r, w in bad if w == why]
            findings.append(Finding(
                "rows_parse_cleanly", "fail",
                f"{len(these)} row(s) did not parse: {why}",
                rows=tuple(r.n for r in these if r.n is not None),
                donors=tuple(donor_key(r.donor) for r in these if r.donor)))
    if not doc.rows:
        skips.append(("rows_parse_cleanly", "the read produced no rows"))
    return findings, skips


def donor_aggregate_above_threshold(doc: Document):
    """Part A discloses donors ABOVE the threshold, aggregated.

    Rotation-sensitive, which is why it earns its place: moving amounts between
    donors preserves the sum and so passes the total gate, but it can push a
    donor's aggregate below the threshold that put them on the page at all.
    """
    findings, skips = [], []
    limit = threshold_for(doc.year)
    if limit is None:
        skips.append(("donor_aggregate_above_threshold",
                      f"no statutory threshold asserted for year {doc.year}"))
        return findings, skips
    rows = doc.part("A")
    if not rows:
        skips.append(("donor_aggregate_above_threshold",
                      "no part A rows were read"))
        return findings, skips
    agg: dict[str, list[Row]] = collections.defaultdict(list)
    for r in rows:
        if r.donor and r.amount is not None:
            agg[donor_key(r.donor)].append(r)
    if not agg:
        skips.append(("donor_aggregate_above_threshold",
                      "no part A row carries both a donor and an amount"))
        return findings, skips
    for key, rs in sorted(agg.items()):
        total = round(sum(r.amount for r in rs), 2)
        if total <= limit:
            findings.append(Finding(
                "donor_aggregate_above_threshold", "flag",
                f"part A: {rs[0].donor!r} aggregates to ${total:,.2f}, at or "
                f"below the ${limit:,.0f} threshold that requires the "
                f"disclosure", "A", tuple(r.n for r in rs if r.n is not None),
                (key,)))
    return findings, skips


def donor_spelling_stable(doc: Document):
    """One donor, one spelling, down their own rows.

    Aggregated donations repeat the donor line. Two spellings of one donor is
    usually OCR, occasionally a second donor, and always worth a human glance.
    """
    findings, skips = [], []
    seen: dict[str, set[str]] = collections.defaultdict(set)
    named = [r for r in doc.rows if r.part in NAMED_DONOR_PARTS]
    for r in named:
        if r.donor:
            seen[donor_key(r.donor)].add(donor_name(r.donor))
    varied = {k: v for k, v in seen.items() if len(v) > 1}
    if not seen:
        skips.append(("donor_spelling_stable",
                      "no row in a donor-naming part carries a name"))
    for key, spellings in sorted(varied.items()):
        findings.append(Finding(
            "donor_spelling_stable", "flag",
            f"one donor read {len(spellings)} ways: "
            + " / ".join(sorted(spellings)[:3]), donors=(key,)))
    return findings, skips


def dates_within_return_year(doc: Document):
    """A donation in a return for 2017 was received in 2017."""
    findings, skips = [], []
    if doc.year is None:
        skips.append(("dates_within_return_year", "the return's year is unknown"))
        return findings, skips
    dated = [r for r in doc.rows if r.date]
    if not dated:
        skips.append(("dates_within_return_year", "no row carries a date"))
        return findings, skips
    off = [r for r in dated if int(r.date[:4]) != doc.year]
    if off:
        findings.append(Finding(
            "dates_within_return_year", "flag",
            f"{len(off)} row(s) dated outside {doc.year}: "
            + ", ".join(sorted({r.date[:4] for r in off})),
            rows=tuple(r.n for r in off if r.n is not None)))
    return findings, skips


def no_repeated_row(doc: Document):
    """The same donor, date and amount twice is a read that double-counted."""
    findings, skips = [], []
    trips = collections.Counter(
        (r.part, name_key(r.donor), r.date, r.amount) for r in doc.rows
        if r.donor and r.date and r.amount is not None)
    dupes = [t for t, c in trips.items() if c > 1]
    if not trips:
        skips.append(("no_repeated_row",
                      "no row carries a donor, a date and an amount"))
    for part, key, d, amt in sorted(dupes, key=lambda t: (t[0] or "", t[1])):
        findings.append(Finding(
            "no_repeated_row", "flag",
            f"part {part}: a donor, date and amount appear more than once "
            f"(${amt:,.2f} on {d})", part))
    return findings, skips


def rows_carry_printed_numbers(doc: Document):
    """Did the reader keep the form's row-number column at all?

    Not a check on the DOCUMENT — a check on the READ. The number column sits
    outside the ruled border and a generative transcriber drops it at will;
    when it does, `row_numbers_complete` cannot decide and the document's
    biggest error detector goes dark. That must be visible as a finding, not
    only as a skip, because a skipped rule is easy to read as a pass.
    """
    findings, skips = [], []
    for part in doc.parts():
        rows = doc.part(part)
        unnumbered = [r for r in rows if r.n is None]
        if not unnumbered:
            continue
        pages = sorted({r.page for r in unnumbered if r.page})
        findings.append(Finding(
            "rows_carry_printed_numbers", "flag",
            f"part {part}: {len(unnumbered)} of {len(rows)} rows were read "
            f"without the form's row number"
            + (f" (page(s) {', '.join(map(str, pages))})" if pages else "")
            + " — completeness cannot be checked for them", part))
    if not doc.rows:
        skips.append(("rows_carry_printed_numbers", "the read produced no rows"))
    return findings, skips


RULES = (
    rows_parse_cleanly,
    rows_carry_printed_numbers,
    row_numbers_complete,
    row_numbers_start_at_one,
    sum_matches_stated_total,
    declared_total_matches_parts,
    every_row_has_an_amount,
    donor_aggregate_above_threshold,
    donor_spelling_stable,
    dates_within_return_year,
    no_repeated_row,
)


def _runs(ns: list[int]) -> str:
    """12, 13, 14, 19 -> '12–14, 19'. A lost page reads as a run."""
    if not ns:
        return ""
    out, start, prev = [], ns[0], ns[0]
    for n in ns[1:] + [None]:
        if n != prev + 1:
            out.append(str(start) if start == prev else f"{start}–{prev}")
            start = n
        prev = n
    return ", ".join(out)


def check(doc: Document, rules=RULES) -> Report:
    """Run every rule. A rule that cannot decide is recorded, not forgotten."""
    findings: list[Finding] = []
    checked: list[str] = []
    skipped: list[tuple[str, str]] = []
    for rule in rules:
        fs, sk = rule(doc)
        findings.extend(fs)
        skipped.extend(sk)
        if not sk:
            checked.append(rule.__name__)
    return Report(doc.stem, tuple(findings), tuple(checked), tuple(skipped))
