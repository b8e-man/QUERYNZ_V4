"""THE OPEN GOLD QUEUE — which candidates are still a question, and why not.

Arthur, 2026-09-28: *"i cant tell what you want me to review and I would
prefer these were in the querynz document review tab."*

WHY THIS MODULE EXISTS. The policy that decides whether a staged candidate is
still worth asking a person about lived inside the Follow the Money page that
drew it. That was tolerable while one surface read it. It stopped being
tolerable the moment a second consumer appeared — the bridge that publishes
these questions into the document review tab — because a withdrawal rule held
in one consumer and not the other does not fail loudly: it asks somebody a
question the estate already knows is unanswerable. Of the 4,706 staged
candidates live when this was written, 2,687 are withdrawn by the over-read
rule alone. A consumer that missed it would put a month of unanswerable
evenings in front of a person and look like it was working.

So the predicate lives HERE, next to the ledger it reads, and every surface
that shows a gold question measures through it (ruling 324: a figure states
its basis, and two surfaces quoting different bases for the same queue is the
figure this project keeps paying for).

WHAT IT DOES NOT DO. It does not rank, group, paginate or word anything. A
queue is a set and a set of reasons; how a surface presents it is that
surface's business, and `stakes()` is offered for the one part of ordering
that is a fact about the data rather than a choice about a page — what a cell
is worth, which is the amount on its ROW and not its own value.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field

from . import gold as g


@dataclass(frozen=True)
class Queue:
    """Every row still worth asking about, and an account of the rest.

    `rows` is what to ask. `counts` is what to say about it. The withdrawal
    tallies are separate fields as well as `counts` keys because a caller
    that shows an empty queue MUST be able to tell the three empties apart:
    the run has not reached these documents, every candidate is assessed, or
    every candidate was withdrawn because the reading behind it was not a
    reading.
    """

    rows: list = field(default_factory=list)
    all_rows: list = field(default_factory=list)
    counts: dict = field(default_factory=dict)
    withdrawn_malformed: int = 0
    withdrawn_over_read: int = 0
    reopened: int = 0
    withdrawn_twin: int = 0
    answered_twin: int = 0


def corpus_index(path: pathlib.Path) -> dict[str, dict]:
    """stem -> what the corpus run recorded about that document.

    A half-written line loses itself and not the file, for the same reason
    the review ledger's reader forgives one: this is appended to by a running
    job and a reader that throws on the last line takes the surface down.
    """
    out: dict[str, dict] = {}
    if not pathlib.Path(path).exists():
        return out
    for line in pathlib.Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("stem"):
            out[d["stem"]] = d
    return out


def _malformed(part, n, donor) -> bool:
    """`docread.rows.malformed` on one cell — the reader's own definition of a
    defective donor cell, so the reader and every surface agree on it."""
    from .rows import Row, malformed
    return malformed(Row(part=part, n=n, donor=donor, amount=None, date=None))


def numberless_twins(rows) -> set:
    """Candidates that are a SECOND copy of a row already addressed by number.

    C463, found by Arthur counting: *"there are only 38 entries"* where the
    queue said 49, and *"i only see 80"* where it said 88.

    THE READER EMITS ONE PRINTED ROW TWICE. `gold.address` keys a row by its
    printed number where the reader recovered one from the margin (`n=10`) and
    by a donor key where it did not (`d=brendanlindsay#0`) — and on ACT 2025
    page 3, in ONE run at one generation, both came back for the same three
    donations. 21 of that part's 52 queue rows are exact content duplicates,
    and exactly 21 carry no number.

    The numberless copy is the one withdrawn, always, because the printed
    number is the better address and it is the one a person can find on the
    page. Matched on (part, donor, date, amount) — every field of the line —
    so two genuine donations of the same amount from the same donor on
    DIFFERENT dates are two rows and stay two rows.

    Withdrawn at read time rather than fixed at staging because the ledger is
    append-only and these are already written.

    THE EMISSION IS FIXED (C463 closed 2026-10-10) AND THIS RULE STAYS. Two
    things had to be true for it to retire and only one is: a fresh run no
    longer emits a twin — measured over all 107 party returns in scope, 147
    gold rows, 147 distinct addresses, **0 twins** — but the ledger still holds
    **375** of them from the two-reader era, and the ledger is append-only, so
    the withdrawal is permanent work, not a transitional patch.

    The cause was never the addressing. `_align` paired a DONORLESS part by
    position, because Part G prints no donor and every key on both sides is the
    empty string, so `SequenceMatcher` saw one `equal` block; where the readers
    found different row counts the remainder fell to insert/delete, `merge`
    kept the unpaired character row, and one printed line came out twice. A
    donorless part now pairs on evidence (`arbitrate._align`), and that is
    pinned by `test_c463_donorless_alignment.py` against the day a second OCR
    model returns — the defect needs two readers, and one has run since
    2026-09-25.
    """
    lines: dict[tuple, dict] = {}
    for r in rows:
        lines.setdefault((r.stem, r.part, r.addr), {})[r.field] = r.value
    numbered: set = set()
    for (stem, part, addr), f in lines.items():
        if addr.startswith("n="):
            numbered.add((stem, part, str(f.get("donor")), str(f.get("date")),
                          f.get("amount")))
    twins = set()
    for (stem, part, addr), f in lines.items():
        if addr.startswith("n="):
            continue
        if (stem, part, str(f.get("donor")), str(f.get("date")),
                f.get("amount")) in numbered:
            twins.add((stem, part, addr))
    return twins


def open_queue(gold_path: pathlib.Path, corpus: dict[str, dict], *,
               status: str = g.AGREED, kind: str | None = None,
               stem: str | None = None) -> Queue:
    """The gold ledger, with every withdrawal policy applied, counted.

    The policies, in the order they run and with the reason each exists:

    C430(a) — A VERDICT ABOUT A READING EXPIRES WHEN THE READING MOVES. An
    abstention or a rejection is a sentence about the evidence in front of a
    person; when the evidence changes it is a NEW question, and a surface
    that kept the old withdrawal would wait forever for a question it never
    asked again. CONFIRMED is exempt: it says what THE PAGE says, which no
    re-read can make untrue, and it is the only tier `score` will let a
    correctness claim be made against.

    The trust policy, applied here as well as at staging, because the ledger
    is append-only and rows staged before the policy reached `contested` are
    still in the file. Rewriting them would be an edit to a record that
    exists precisely so it cannot be edited.

    C422 — a question made by a reader we have since CORRECTED is withdrawn,
    not re-asked. A cell a person HAS answered is exempt: a verdict is their
    word, not a generation of ours.

    C424 — an UNANSWERED candidate whose own value the reader is now known to
    have malformed is not a question, because no answer to it can be right.

    OVER-READ — a part that reads more money than the party itself declared.
    Under-reading a part is honest; over-reading it is impossible, so the
    reading is wrong before the cell is and every cell in that part is
    unanswerable for the same reason. This is a reader worklist, never a
    person's.
    """
    rows = list(g.load(gold_path).values())

    latest = g.latest(gold_path)
    reopened = 0
    fresh: list = []
    for r in rows:
        if r.tier in g.ABOUT_A_READING:
            cur = latest.get(r.id)
            if cur is not None and g.evidence_id(cur) != g.evidence_id(r):
                fresh.append(cur)      # a different reading is a NEW question
                reopened += 1
                continue
        fresh.append(r)
    rows = fresh

    from .arbitrate import TRUSTED_FOR
    rows = [r for r in rows
            if not (getattr(r, "kind", None) == g.DISPUTED
                    and r.tier == g.AGREED
                    and TRUSTED_FOR.get(r.field) is not None)]
    rows = [r for r in rows
            if not (getattr(r, "kind", None) in (g.DISPUTED, g.IMPLICATED)
                    and r.tier == g.AGREED
                    and getattr(r, "gen", "") != g.CONTESTED_GEN)]

    withdrawn_malformed = 0
    kept = []
    for r in rows:
        if (r.tier == g.AGREED and r.field == "donor" and isinstance(r.value, str)
                and _malformed(r.part, r.n, r.value)):
            withdrawn_malformed += 1
            continue
        kept.append(r)
    rows = kept

    withdrawn_over_read = 0
    kept = []
    for r in rows:
        if (r.tier == g.AGREED
                and (getattr(r, "kind", None) or g.AGREED_KIND) != g.AGREED_KIND
                and g.over_read((corpus.get(r.stem) or {}).get("reconcile"), r.part)):
            withdrawn_over_read += 1
            continue
        kept.append(r)
    rows = kept

    # C463 — the same printed row, written twice. An UNANSWERED numberless
    # copy is not a question: the numbered one asks it, and answering both
    # would count one donation as two in every figure drawn off this set. A
    # cell a person has already ruled on is exempt, as everywhere here: their
    # word stands, and the count below says how many are affected.
    # Detected over EVERY row, answered or not. Computing it over the
    # unanswered ones alone made a cell stop matching its twin the moment
    # somebody confirmed it — the row's signature lost the field that had been
    # answered — so `answered_twin` read 0 however many verdicts sat on
    # duplicates. Detection is about the ROWS; the verdict only decides whether
    # the row is withdrawn or counted.
    twins = numberless_twins(rows)
    withdrawn_twin = 0
    answered_twin = 0
    kept = []
    for r in rows:
        if (r.stem, r.part, r.addr) in twins:
            if r.tier == g.AGREED:
                withdrawn_twin += 1
                continue
            answered_twin += 1
        kept.append(r)
    rows = kept

    counts = {"agreed": 0, "confirmed": 0, "rejected": 0, "abstained": 0}
    for r in rows:
        counts[r.tier] = counts.get(r.tier, 0) + 1
    counts["documents"] = len({r.stem for r in rows})
    counts["withdrawn_malformed"] = withdrawn_malformed
    counts["reopened"] = reopened
    counts["withdrawn_over_read"] = withdrawn_over_read
    # C463: the second copy of a printed row, and how many verdicts were given
    # on one before the duplication was known — a verdict on a duplicate is not
    # wrong, but it is not a second confirmation either, and an accuracy figure
    # that counts it twice overstates its own denominator.
    counts["withdrawn_twin"] = withdrawn_twin
    counts["answered_twin"] = answered_twin
    # ASSESSED means a person said something about the READING. An abstention
    # says something about the QUESTION, so it is counted and shown but never
    # folded into an accuracy figure.
    counts["assessed"] = counts["confirmed"] + counts["rejected"]
    for k in g.KINDS:
        counts[f"open_{k}"] = sum(
            1 for r in rows
            if r.tier == g.AGREED and (getattr(r, "kind", None) or g.AGREED_KIND) == k)

    want = [r for r in rows if r.tier == status]
    if kind:
        want = [r for r in want if (getattr(r, "kind", None) or g.AGREED_KIND) == kind]
    if stem:
        want = [r for r in want if r.stem == stem]

    return Queue(rows=want, all_rows=rows, counts=counts,
                 withdrawn_malformed=withdrawn_malformed,
                 withdrawn_over_read=withdrawn_over_read, reopened=reopened,
                 withdrawn_twin=withdrawn_twin, answered_twin=answered_twin)


def stakes(rows) -> dict[tuple, float]:
    """What each ROW of the scan is worth, keyed (stem, part, addr).

    THE STAKE OF A CELL IS ITS ROW'S AMOUNT, not its own value. A donor or a
    date cell has no money of its own, but the question "is this the right
    donor" on a $9.4m row is worth more than the same question on a $2,000
    one, and the three fields of one line want answering together — the
    person is already looking at that line of the scan.
    """
    out: dict[tuple, float] = {}
    for r in rows:
        if r.field == "amount" and isinstance(r.value, (int, float)):
            k = (r.stem, r.part, r.addr)
            out[k] = max(out.get(k, 0.0), float(r.value))
    return out


def stake_of(table: dict[tuple, float], row) -> float:
    """A cell's stake, 0.0 where its row carries no amount we could read.

    Zero is a real answer and not a missing one: a rule still named the cell,
    so it ranks last rather than being dropped.
    """
    return table.get((row.stem, row.part, row.addr), 0.0)
