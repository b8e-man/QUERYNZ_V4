"""QUEUING THE TRIAL'S PASSES (plan steps 3.5 and 3.6), once the catalogue
holds the trial's job types. A session queues; the scheduler places.

    python -m support.trials.queue one                 pass one: GLM-OCR alone, every page-set document, 200 dpi, the old cache joined
    python -m support.trials.queue two [READER …]      pass two: the challengers (and the incumbent at 300 dpi) as bulk jobs
    python -m support.trials.queue twenty READER       the twenty-page compression comparison for one reader
    python -m support.trials.queue urgent              one small `waiting`-class page job, injected part-way (3.6)
    python -m support.trials.queue rows                the text-reader rows pass over every document with readings
    python -m support.trials.queue status              the trial's rows in the queue

Pieces are the page set's hashes (one document per piece); `twenty` uses
piece keys of the form sha256 with the pages in the job's args.
"""
from __future__ import annotations

import json
import sys

from support.trials import pageset, readers

JOB_FOR = {name: f"qv4-trial-read-{name.replace('infinity-parser2-pro-q8', 'infinity-q8').replace('infinity-parser2-pro', 'infinity')}"
           for name in readers.READERS}
JOB_FOR.update({"chandra-ocr-2": "qv4-trial-read-chandra", "chandra-ocr-2-q4": "qv4-trial-read-chandra-q4"})


def _conn():
    import support.db as db
    return db.connect(db.OWNER_KEY, "querynz_v4", autocommit=True)


def enqueue(job: str, pieces: list[str], args: dict, by: str = "trial") -> int:
    from support.scheduler import SCHEMA
    from support.scheduler import queue as q
    conn = _conn()
    return q.enqueue(conn, SCHEMA, job, args=args, pieces=pieces, created_by=by)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "status"
    docs = pageset.load()
    hashes = [d["sha256"] for d in docs]
    if cmd == "one":
        qid = enqueue(JOB_FOR["glm-ocr"], hashes, {"pass": "one", "dpi": 200, "old_cache": True, "pages": "selected",
                                                   "pageset": pageset.identity()})
        print(f"queued pass one: {JOB_FOR['glm-ocr']} #{qid}, {len(hashes)} pieces at 200 dpi")
        return 0
    if cmd == "two":
        names = argv[1:] or list(readers.CHALLENGERS) + [readers.INCUMBENT]
        for n in names:
            qid = enqueue(JOB_FOR[n], hashes, {"pass": "two", "pages": "selected", "pageset": pageset.identity()})
            print(f"queued pass two: {JOB_FOR[n]} #{qid}, {len(hashes)} pieces")
        return 0
    if cmd == "twenty":
        n = argv[1]
        pages = pageset.twenty()
        by_doc: dict[str, list[int]] = {}
        for sha, p in pages:
            by_doc.setdefault(sha, []).append(p)
        for sha, ps in by_doc.items():
            pass
        qid = enqueue(JOB_FOR[n], list(by_doc), {"pass": "twenty", "pages": "selected", "twenty": {s: ps for s, ps in by_doc.items()},
                                                 "pageset": pageset.identity()})
        print(f"queued twenty-page comparison: {JOB_FOR[n]} #{qid}, {len(by_doc)} pieces")
        return 0
    if cmd == "urgent":
        sha, page = pageset.twenty()[0]
        qid = enqueue("qv4-trial-urgent-page", [f"{sha}:{page}"], {"pass": "urgent"})
        print(f"queued the urgent page: qv4-trial-urgent-page #{qid} ({sha[:12]} p{page})")
        return 0
    if cmd == "rows":
        qid = enqueue("qv4-trial-rows", hashes, {"pass": "rows"})
        print(f"queued the rows pass: qv4-trial-rows #{qid}, {len(hashes)} pieces")
        return 0
    if cmd == "status":
        from support.scheduler import SCHEMA
        conn = _conn()
        for r in conn.execute(f"SELECT id, job, state, pieces_done, pieces_total, outcome FROM {SCHEMA}.queue "
                              f"WHERE job LIKE 'qv4-trial-%%' OR created_by = 'trial' ORDER BY id"):
            print(*r)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
