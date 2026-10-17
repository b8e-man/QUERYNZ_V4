"""The review queue — where a machine that cannot decide hands over.

99% is not reached by a better reader. It is reached by a reader that is right
most of the time and HONEST about the rest, plus a person clearing the rest
quickly. This module is the handover, and it is the only place in the service
where a human judgement is recorded.

APPEND-ONLY, LIKE EVERY OTHER JUDGEMENT IN THE ESTATE. An item is written
once; a resolution is a second row referring to it. Nothing is ever edited in
place, so the queue's history is the audit trail and a wrong resolution is
corrected by a later row rather than by losing the earlier one.

PRIORITY IS A POLICY, NOT A GUESS, and it is stated here so it can be argued
with. Arthur, 2026-09-23: *"let's focus on more recent years and deprioritise
pre-2010."* So the year is the largest term. After that: a contradiction of
the document outranks a doubt about the read, and more money outranks less.

WHAT IS NOT IN THE QUEUE IS THE POINT. Items come only from a rule that fired
or two readers that differed. A row both readers read the same way and that
breaks no invariant is never seen by a person — which is what makes the
volume clearable, and also exactly where a shared failure would hide. The
service claims a partition, never a proof.

AND WHAT IS NO LONGER ASKED IS SAID OUT LOUD. Two rules retire an item without
anyone resolving it: the 2019 window (ruling 347) and a dispute naming a reader
the estate has retired. Both are written as REASONS (`withheld`), counted in
`summary`, and never as deletions — the row stays, and lifting the rule brings
the question back. On 2026-09-26 those two rules took the queue a person would
be shown from 15,230 items to 2,588: 12,081 were arguments with a reader that
no longer runs, and the rest were pre-window.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import pathlib
import re
import time

from .arbitrate import Arbitration, Dispute
from .invariants import Finding, Report, threshold_for
from .rows import Document

#: Arthur's ruling of 2026-09-23. Older returns are still queued — they sort
#: last, so a reviewer's day is spent where the register is most used.
ERA_WEIGHT = ((2020, 3.0), (2010, 2.0), (0, 0.5))

SEVERITY_WEIGHT = {"fail": 3.0, "flag": 1.0}

#: An amount's contribution is logarithmic: $1m matters more than $100k, but
#: not ten times more, and a cent discrepancy is still worth a glance.
MONEY_WEIGHT = 0.5

#: RULING 347 (2026-09-24). For Follow the Money, nothing before 2019 exists.
#: A queued item is a QUESTION PUT TO A PERSON, so asking one about a 2014
#: return is spending the scarcest thing in the estate on work the ruling says
#: is not work. The items are still WRITTEN — kept, like every pre-2019 row —
#: and simply never asked. The one constant is
#: `query.influence.base.WINDOW_FROM`; this is its copy on the capture side of
#: the boundary, and tests/test_window_is_one_number.py fails if they drift.
WINDOW_FROM = 2019

#: Readers the estate no longer runs. A dispute item asks WHICH OF TWO READERS
#: IS RIGHT; once one of them is retired that question has no answer to give,
#: because the reading it would correct is no longer produced. `geometry` (with
#: its `tatr` structure source) was retired 2026-09-25 under the one-recogniser
#: ruling, and took 12,081 of the queue's 15,230 open items with it.
RETIRED_READERS = frozenset({"geometry", "tatr"})

#: Rules whose PREMISE was two readers. `seen_by_one_reader` fires when a row
#: appears in one reading and not the other; with one recogniser every row is
#: seen by one reader, so the rule can only fire on everything or nothing and
#: says nothing either way. 8,419 items were waiting under it.
RETIRED_RULES = frozenset({"seen_by_one_reader"})

OPEN, ACCEPTED, CORRECTED, UNREADABLE = "open", "accepted", "corrected", "unreadable"


@dataclasses.dataclass(frozen=True)
class Item:
    """One thing a person is being asked to look at."""
    id: str
    stem: str
    kind: str                       # "invariant" | "dispute"
    detail: str
    part: str | None = None
    n: int | None = None
    page: int | None = None
    donor: str | None = None
    field: str | None = None
    values: tuple[tuple[str, object], ...] = ()
    severity: str = "flag"
    year: int | None = None
    amount: float | None = None
    rule: str | None = None
    #: The document this came from, relative to the repo.
    source: str | None = None
    #: Where on the page this row sits, from the geometric reader:
    #: (x0, y0, x1, y1) in pixels at `dpi`. The review page crops to it.
    bbox: tuple[float, float, float, float] | None = None
    dpi: int | None = None

    def to_json(self) -> dict:
        d = dataclasses.asdict(self)
        d["values"] = [list(v) for v in self.values]
        return d


@dataclasses.dataclass(frozen=True)
class Resolution:
    item_id: str
    verdict: str                    # accepted | corrected | unreadable
    value: object = None
    by: str = ""
    at: float = 0.0
    note: str = ""


def item_id(stem: str, kind: str, part, n, field, detail: str) -> str:
    """Stable across runs so re-reading a document does not re-queue it.

    Keyed on WHAT IS BEING ASKED, not on when it was asked or what the reader
    happened to say, so a second read of the same defect lands on the same
    item and a resolution already given still applies.
    """
    raw = "␟".join(str(x) for x in (stem, kind, part, n, field, detail))
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def era_weight(year: int | None) -> float:
    if year is None:
        return 1.0
    for first, w in ERA_WEIGHT:
        if year >= first:
            return w
    return 0.5


def priority(item: Item) -> float:
    """Higher is sooner. The policy, in one expression."""
    money = math.log10(max(abs(item.amount or 0.0), 1.0) + 1.0)
    return (era_weight(item.year)
            * (SEVERITY_WEIGHT.get(item.severity, 1.0) + MONEY_WEIGHT * money))


def from_report(doc: Document, report: Report) -> list[Item]:
    """Queue what the invariants could not let pass."""
    out = []
    for f in report.findings:
        amounts = [r.amount for r in doc.rows
                   if r.n is not None and r.n in (f.rows or ()) and r.amount]
        out.append(Item(
            id=item_id(doc.stem, "invariant", f.part,
                       f.rows[0] if f.rows else None, f.rule, f.detail),
            stem=doc.stem, kind="invariant", detail=f.detail, part=f.part,
            source=doc.source,
            n=f.rows[0] if f.rows else None, severity=f.severity,
            year=doc.year, rule=f.rule,
            amount=max(amounts) if amounts else None))
    return out


def from_arbitration(arb: Arbitration, *, year: int | None = None,
                     ) -> list[Item]:
    """Queue what the readers would not agree on."""
    out = []
    for d in arb.disputes:
        amounts = [v for _, v in d.values
                   if d.field == "amount" and isinstance(v, (int, float))]
        out.append(Item(
            id=item_id(arb.stem, "dispute", d.part, d.n, d.field, d.summary()),
            stem=arb.stem, kind="dispute", detail=d.summary(), part=d.part,
            source=arb.source,
            n=d.n, page=d.page, donor=d.donor, field=d.field,
            values=d.values, severity="flag", year=year, bbox=d.bbox,
            dpi=d.dpi,
            amount=max(amounts) if amounts else None, rule="reader_disagreement"))
    for f in arb.findings:
        out.append(Item(
            id=item_id(arb.stem, "dispute", f.part,
                       f.rows[0] if f.rows else None, f.rule, f.detail),
            stem=arb.stem, kind="dispute", detail=f.detail, part=f.part,
            source=arb.source,
            n=f.rows[0] if f.rows else None, severity=f.severity, year=year,
            rule=f.rule))
    return out


# --- the ledger ------------------------------------------------------------

def append(path: pathlib.Path, rows: list[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, default=str) + "\n")
    return len(rows)


def enqueue(items: list[Item], path: pathlib.Path) -> int:
    """Add items not already present. Returns how many were new."""
    known = {i.id for i in load_items(path)}
    fresh = [i for i in items if i.id not in known]
    append(path, [{"row": "item", **i.to_json()} for i in fresh])
    return len(fresh)


def resolve(item_id_: str, verdict: str, path: pathlib.Path, *,
            value=None, by: str = "", note: str = "") -> Resolution:
    """Record a person's judgement. Never edits the item it refers to."""
    if verdict not in (ACCEPTED, CORRECTED, UNREADABLE):
        raise ValueError(f"not a verdict: {verdict!r}")
    r = Resolution(item_id_, verdict, value, by, time.time(), note)
    append(path, [{"row": "resolution", **dataclasses.asdict(r)}])
    return r


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


def load_items(path: pathlib.Path) -> list[Item]:
    """Every item, ONCE. The id is keyed on what is being asked, so two rows
    with one id are one question written twice — which is what a second run
    over the same corpus against a queue another run was also writing
    produced: 29,528 rows for 15,230 questions. Last row wins, so a re-read
    that sharpens the detail replaces the earlier wording."""
    seen: dict[str, Item] = {}
    for d in _rows(path):
        if d.get("row") != "item":
            continue
        d = {k: v for k, v in d.items() if k != "row"}
        d["values"] = tuple(tuple(v) for v in d.get("values", ()))
        if d.get("bbox"):
            d["bbox"] = tuple(d["bbox"])
        it = Item(**d)
        seen[it.id] = it
    return list(seen.values())


def resolutions(path: pathlib.Path) -> dict[str, Resolution]:
    """The LAST resolution for each item — a later row corrects an earlier."""
    out: dict[str, Resolution] = {}
    for d in _rows(path):
        if d.get("row") != "resolution":
            continue
        d = {k: v for k, v in d.items() if k != "row"}
        out[d["item_id"]] = Resolution(**d)
    return out


_THRESHOLD_SAID = re.compile(r"\$([\d,]+) threshold")


def _stale_threshold(item: Item) -> str | None:
    """An item raised under a threshold the statute has since replaced.

    The detail line QUOTES the number it judged against, which is what makes
    this answerable without re-reading the document: if the year's threshold
    is no longer that number, the question was asked under a repealed rule and
    is not put to anyone. The next corpus run raises the right one — the id is
    keyed on the detail, so a corrected finding is a NEW item and does not
    inherit this one's silence.
    """
    if item.rule != "donor_aggregate_above_threshold":
        return None
    m = _THRESHOLD_SAID.search(item.detail or "")
    now = threshold_for(item.year)
    if not m or now is None:
        return None
    said = float(m.group(1).replace(",", ""))
    if said != now:
        return (f"raised under a superseded threshold (${said:,.0f}; "
                f"{item.year}'s is ${now:,.0f})")
    return None


def withheld(item: Item) -> str | None:
    """Why this item is not put to a person, or None if it is in force.

    A REASON, NOT A FILTER. Two rules retire an item without resolving it —
    the 2019 window and a reader that no longer exists — and both are
    decisions that can be wrong, so each one says its name here rather than
    thinning the queue silently. Nothing is deleted: the item stays in the
    ledger, and lifting either rule brings it straight back.
    """
    if item.year is not None and item.year < WINDOW_FROM:
        return f"before {WINDOW_FROM} (ruling 347)"
    readers = {str(r) for r, _ in item.values}
    if item.rule == "reader_disagreement" and readers & RETIRED_READERS:
        gone = ", ".join(sorted(readers & RETIRED_READERS))
        return f"disagreement with a retired reader ({gone})"
    if item.rule in RETIRED_RULES:
        return f"{item.rule} needs two readers, and there is one"
    stale = _stale_threshold(item)
    if stale:
        return stale
    return None


def open_items(path: pathlib.Path, *, everything: bool = False) -> list[Item]:
    """Everything still waiting AND still in force, most urgent first."""
    done = resolutions(path)
    return sorted((i for i in load_items(path)
                   if i.id not in done
                   and (everything or withheld(i) is None)),
                  key=priority, reverse=True)


def summary(path: pathlib.Path) -> dict:
    """What the queue holds, what it ASKS, and what it is holding back.

    `open` counts what a person will actually be shown. `withheld` says how
    much is being kept out of their way and under which rule — a number that
    must be visible, because a queue that quietly drops four fifths of itself
    looks exactly like a queue that was always short.
    """
    items, done = load_items(path), resolutions(path)
    by_verdict: dict[str, int] = {}
    for r in done.values():
        by_verdict[r.verdict] = by_verdict.get(r.verdict, 0) + 1
    held: dict[str, int] = {}
    asked = 0
    for i in items:
        if i.id in done:
            continue
        why = withheld(i)
        if why is None:
            asked += 1
        else:
            held[why] = held.get(why, 0) + 1
    return {"items": len(items), "open": asked,
            "withheld": held, "withheld_total": sum(held.values()),
            "resolved": len(done), "by_verdict": by_verdict,
            "documents": len({i.stem for i in items}),
            "documents_asked": len({i.stem for i in items
                                    if i.id not in done and withheld(i) is None})}
