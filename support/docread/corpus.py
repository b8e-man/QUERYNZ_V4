"""Run both readers over many documents, and keep the record.

Resumable by design: a document already in the output is skipped, so a run
that dies at 300 of 2,000 continues rather than starts again. The output is
one JSON row per document — what each reader found, what the invariants said,
what the readers would not agree on, and the coverage of both figures.

ORDER IS A POLICY. Arthur, 2026-09-23: *"let's focus on more recent years and
deprioritise pre-2010."* Party annual returns come before candidate returns
(they carry the donor tables and the stated totals the register turns on),
recent years before old, and pre-2010 last rather than never.

PARALLEL WHERE IT HELPS, SERIAL WHERE IT MUST. The geometric reader is CPU and
scales with cores. The transcriber is one GPU lane at concurrency 1, so its
calls queue at the server no matter how many workers ask — which is exactly
what should happen, and why the worker count is chosen for memory (each worker
holds a Table Transformer subprocess) rather than for throughput.

    python -m docread.corpus --kind party --since 2010 --limit 50 --workers 8
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import dataclasses
import multiprocessing
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import traceback

from .sources import find_document, is_raster

import os
from .sources import STAGING
REPO = pathlib.Path(os.environ.get("QV4_OLD_LIVE") or "/home/user/Git Repos/QueryNZ_V3")   # the old folder, read-only
LIVE = pathlib.Path(os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live")
PAGEREAD = STAGING / "pageread"
OUT = LIVE / "checks/docread-corpus.jsonl"
QUEUE = LIVE / "checks/docread-queue.jsonl"

#: Directories under pageread/ that are not a year of party returns.
CANDIDATE_DIR = re.compile(r"^candidates(\d{4})$")

MAX_PAGES = int(os.environ.get("DOCREAD_MAX_PAGES", "40"))

#: NOT fork. A ProcessPoolExecutor starts a management thread and then forks
#: its workers, and a child forked from a threaded parent inherits that
#: thread's lock state without the thread that would release it. The run
#: deadlocks at startup with every worker asleep and the parent in
#: futex_do_wait — observed 2026-09-23, six workers, nothing read in twelve
#: minutes. `forkserver` forks from a clean single-threaded server process
#: instead, which is why CPython's own default moves to it.
#:
#: Each worker therefore IMPORTS this module rather than inheriting it, so
#: nothing may run at import time and `main()` stays behind the name guard.
START_METHOD = os.environ.get("DOCREAD_START_METHOD", "forkserver")


@dataclasses.dataclass(frozen=True)
class Target:
    stem: str
    pdf: pathlib.Path
    year: int | None
    kind: str          # party | candidate | disclosure

    def rank(self) -> tuple:
        """Lower sorts first. Party before candidate, recent before old,
        pre-2010 last (Arthur, 2026-09-23)."""
        kindrank = {"party": 0, "candidate": 1, "disclosure": 2}[self.kind]
        y = self.year or 0
        era = 0 if y >= 2020 else 1 if y >= 2010 else 2
        return (era, kindrank, -y, self.stem)




def targets(kind: str | None = None, since: int | None = None,
            limit: int = 0, only: str | None = None) -> list[Target]:
    """Every document with a stored read, in priority order."""
    out: list[Target] = []
    for d in sorted(PAGEREAD.iterdir()):
        if not d.is_dir() or d.name.startswith("disclosures-quarantine"):
            continue
        m = CANDIDATE_DIR.match(d.name)
        if m:
            k, year = "candidate", int(m.group(1))
        elif d.name.isdigit():
            k, year = "party", int(d.name)
        else:
            k, year = "disclosure", None
        if kind and k != kind:
            continue
        if since is not None and (year is None or year < since):
            continue
        for j in sorted(d.glob("*.json")):
            if only and only not in j.stem:
                continue
            doc = find_document(j.stem)
            if doc is not None:
                out.append(Target(j.stem, doc, year, k))
    out.sort(key=Target.rank)
    return out[:limit] if limit else out


def page_count(path: pathlib.Path) -> int:
    """How many pages — ONE page for a photographed form.

    C308. This asked `pdfinfo` and returned 0 for anything it could not open,
    so an `.jpg` disclosure raised "no pages" before the recogniser was ever
    called. The answer now comes from the recogniser's own `page_total`, which
    reads the bytes: one question, one implementation, and `is_raster` is here
    only so a caller holding a PATH does not have to read the file to know.
    """
    from support.docread import pagereader as vision_ocr
    try:
        return vision_ocr.page_total(path.read_bytes())
    except OSError:
        return 0


def read_one(t: Target, *, max_pages: int = MAX_PAGES) -> dict:
    """One reader, checked and recorded. Never raises.

    THERE USED TO BE TWO. A geometric reader took its structure from ruled
    lines and its characters from a local OCR engine, and its disagreements
    with the transcriber were the signal. Arthur retired that engine on
    2026-09-25 — its characters were the failure, not its structure — and a
    reader with no character source is not a reader. What survives is the
    RECORD: `arbitrate` and `gold` compare readings, and two readings of one
    document can still be a model re-read, a different profile, or a person.
    """
    # Imported inside the worker: each process loads its own.
    from support.docread import pagereader as vision_ocr
    from . import invariants as inv, parse
    from .arbitrate import Arbitration, arbitrate

    t0 = time.time()
    # Computed defensively and OUTSIDE nothing: `relative_to` raises for a
    # path outside the repo, and a raise here escapes the try below, kills
    # the pool's map and loses every document still queued behind it. At 2,700
    # documents a run that dies on one has read none of the rest.
    try:
        src = str(t.pdf.resolve().relative_to(REPO))
    except (ValueError, OSError):
        src = str(t.pdf)
    row = {"stem": t.stem, "year": t.year, "kind": t.kind, "source": src}
    try:
        data = t.pdf.read_bytes()
        row["raster"] = is_raster(t.pdf)
        n = vision_ocr.page_total(data)
        row["pages_total"] = n
        pages = list(range(1, min(n, max_pages) + 1))
        row["pages_read"] = len(pages)
        if not pages:
            # Raised, not returned: an early return skips the uniform exit and
            # the row comes back without its timing. One way out of this
            # function, and every failure takes it.
            raise ValueError("the document reports no pages")

        texts = vision_ocr.ocr_pages(data, pages)
        vlm = parse.parse_document(t.stem, texts, year=t.year,
                                   reader="glm-ocr")
        row["vlm_rows"] = len(vlm.rows)

        # ONE READER IS NOT AN ARBITRATION — AND IT HAD BEEN RAISING ON EVERY
        # DOCUMENT SINCE 2026-09-25 (C308, 2026-10-09). `arbitrate` refuses a
        # single reading, correctly; what was wrong is that this line called it
        # with one. Arthur retired the geometric reader on 2026-09-25 and the
        # last row in the store is dated 2026-09-24, so no run has been made
        # since and nothing said the runner could no longer read anything —
        # C308's own blocker was "the run was never made", which was true and
        # not the whole of it. A single reading is RECORDED as one: every row
        # uncompared, no agreement figure at all rather than a 0.0 that reads
        # as total disagreement, and `single_reading` on the row so no later
        # measurement averages it in with a compared one.
        readings = [vlm]
        doc = readings[0]
        rep = inv.check(doc)
        row.update(
            merged_rows=len(doc.rows),
            stated_totals=doc.stated_totals,
            parts={p: len(doc.part(p)) for p in doc.parts()},
            fails=[f.rule for f in rep.fails],
            flags=[f.rule for f in rep.flags],
            rule_coverage=round(rep.coverage, 3),
        )
        if len(readings) >= 2:
            arb = arbitrate(readings)
            row.update(
                agreement=round(arb.agreement, 3),
                compare_coverage=round(arb.coverage, 3),
                rows_compared=arb.rows_compared,
                rows_uncompared=len(arb.uncompared),
                disputes=len(arb.disputes),
                basis=arb.basis(),
            )
        else:
            arb = Arbitration(stem=t.stem, source=src,
                              readers=(doc.reader or "unknown",),
                              uncompared=tuple(doc.rows))
            row.update(single_reading=True, rows_compared=0,
                       rows_uncompared=len(arb.uncompared), disputes=0,
                       basis=arb.basis())
        for part, stated in doc.stated_totals.items():
            got = sum(r.amount for r in doc.part(part) if r.amount)
            row.setdefault("reconcile", {})[part] = {
                "stated": stated, "read": round(got, 2),
                "ok": abs(got - stated) < 1.0}
        # THE RETURN'S OWN TOTAL (C418, 2026-10-10), recorded beside the
        # per-part reconciliation and never mixed into it: a part total and a
        # document total are different evidence and the 15 documents that lost
        # their part totals with the geometric reader have only this one.
        #
        # `ok` is taken FROM THE INVARIANT, not recomputed. The per-part
        # `reconcile` above compares with a one-dollar tolerance and the
        # invariant uses a cent; a second comparison here would be a third
        # tolerance for one question, which is how the $60,000 arm drifted
        # (#8a634c).
        if doc.declared_total is not None:
            wanted = set(doc.declared_parts)
            got = sum(r.amount for r in doc.rows
                      if r.part in wanted and r.amount)
            row["declared"] = {
                "total": doc.declared_total,
                "parts": "+".join(doc.declared_parts),
                "read": round(got, 2),
                "ok": not any(f.rule == "declared_total_matches_parts"
                              for f in rep.fails)}
        row["_doc"] = doc
        row["_report"] = rep
        row["_arb"] = arb
    except Exception as e:                               # noqa: BLE001
        row["error"] = f"{type(e).__name__}: {e}"
        row["traceback"] = traceback.format_exc()[-800:]
    row["seconds"] = round(time.time() - t0, 1)
    return row


def done_stems(out: pathlib.Path) -> set[str]:
    if not out.exists():
        return set()
    got = set()
    for line in out.read_text().splitlines():
        try:
            got.add(json.loads(line)["stem"])
        except Exception:                                # noqa: BLE001
            continue
    return got


def _worker(t: Target) -> dict:
    row = read_one(t)
    doc, rep, arb = row.pop("_doc", None), row.pop("_report", None), row.pop("_arb", None)
    if doc is not None:
        from . import queue as q
        from . import gold
        row["_items"] = [i.to_json() for i in
                         (q.from_report(doc, rep) + q.from_arbitration(arb, year=t.year))]
        # TWO classes, always both (Arthur 2026-09-23). `candidates` is the
        # calibration set — cells both readers agreed on with no rule against
        # them. `contested` is the repair set — the cells that one refuses.
        # A run that wrote only the first produced 592 candidates of which
        # NONE sat in a part that failed to reconcile.
        row["_gold"] = [dataclasses.asdict(c) for c in
                        (list(gold.candidates(doc, rep, arb))
                         + list(gold.contested(doc, rep, arb)))]
    return row


def run(ts: list[Target], *, out: pathlib.Path = OUT,
        queue: pathlib.Path = QUEUE, workers: int = 8,
        gold_path: pathlib.Path | None = None, redo: bool = False,
        echo=print) -> dict:
    from . import gold
    from . import queue as q

    out.parent.mkdir(parents=True, exist_ok=True)
    # `redo` lifts the skip for the targets NAMED, and nothing else: the store
    # is append-only and every consumer takes the last row for a stem, so a
    # re-read after the reader is fixed is an append, never an edit. C433 is
    # the first of these and will not be the last.
    already = set() if redo else done_stems(out)
    todo = [t for t in ts if t.stem not in already]
    echo(f"{len(ts)} target(s); {len(already)} already done; {len(todo)} to read")
    stats = {"documents": 0, "errors": 0, "queued": 0, "gold": 0,
             "reconciling": 0, "with_stated": 0, "seconds": 0.0}
    t0 = time.time()
    ctx = multiprocessing.get_context(START_METHOD)
    with out.open("a") as fh, cf.ProcessPoolExecutor(max_workers=workers,
                                                     mp_context=ctx) as ex:
        # as_completed, not map: map yields IN ORDER, so one slow document
        # holds back every result behind it and the run looks stalled when it
        # is merely waiting. Results are written as they finish.
        futures = {ex.submit(_worker, t): t for t in todo}
        for i, fut in enumerate(cf.as_completed(futures), 1):
            t = futures[fut]
            try:
                row = fut.result()
            except Exception as e:                       # noqa: BLE001
                row = {"stem": t.stem, "year": t.year, "kind": t.kind,
                       "error": f"worker died: {type(e).__name__}: {e}"}
            items = row.pop("_items", [])
            golds = row.pop("_gold", [])
            fh.write(json.dumps(row, default=str) + "\n")
            fh.flush()
            stats["documents"] += 1
            stats["seconds"] = round(time.time() - t0, 1)
            if row.get("error"):
                stats["errors"] += 1
            if items:
                stats["queued"] += q.append(queue, [{"row": "item", **it}
                                                    for it in items])
            if golds and gold_path is not None:
                stats["gold"] += gold.stage(golds, gold_path)
            rec = row.get("reconcile") or {}
            if rec:
                stats["with_stated"] += 1
                if all(v["ok"] for v in rec.values()):
                    stats["reconciling"] += 1
            if i % 10 == 0 or i == len(todo):
                rate = stats["seconds"] / max(i, 1)
                left = (len(todo) - i) * rate
                echo(f"  {i}/{len(todo)}  {rate:.1f}s/doc  "
                     f"~{left/60:.0f} min left  queued {stats['queued']}  "
                     f"gold {stats['gold']}  errors {stats['errors']}")
    return stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--kind", choices=("party", "candidate", "disclosure"))
    ap.add_argument("--since", type=int, help="earliest year to read")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", help="substring of the stem")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", type=pathlib.Path, default=OUT)
    ap.add_argument("--queue", type=pathlib.Path, default=QUEUE)
    ap.add_argument("--gold", type=pathlib.Path,
                    default=LIVE / "checks/docread-gold.jsonl")
    ap.add_argument("--list", action="store_true", help="show targets, read none")
    ap.add_argument("--redo", action="store_true",
                    help="read the named targets again even where the store "
                         "already holds a row for them (appends; the last row "
                         "for a stem is the one every reader takes)")
    a = ap.parse_args(argv)
    ts = targets(a.kind, a.since, a.limit, a.only)
    if a.list:
        for t in ts:
            print(f"{t.rank()[0]} {t.kind:<10} {t.year} {t.stem}")
        print(f"{len(ts)} target(s)", file=sys.stderr)
        return 0
    stats = run(ts, out=a.out, queue=a.queue, workers=a.workers,
                gold_path=a.gold, redo=a.redo)
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
