"""THE TEXT READER TURNS EACH PAGE READER'S TEXT INTO ROWS (plan step 3.7):
amounts and tables are scored after the text reader has read each page
reader's output under the text-reader profile from step 2.15, the same for
every page reader, so a reader is judged on what its text yields and not
on its markup.

    python -m support.trials rows SHA256     one document: every stored trial reading of every page, to rows (the scheduler runs it)

For each stored pixels reading of the document (every reader, every pass),
the text reader is asked for the page's rows as one JSON object: the
part letter, the row number if printed, the amount, the date, whether the
line is a printed total, and the donor as printed, kept ONLY in the stored
reading (never in a log or a table: hard limits 11 and 15). The rows are
stored as a second reading keyed to the same document, page and page
reader with the text reader's model and settings, `read_from = "text"`,
so a replay never asks the model again.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import sys

from support import modelclient
from support import reader as rd
from support.trials import pageset, readers, score

READER = "support.trials.rows 1"
LANE = "trial-rows"
SYSTEM = ("You are reading ONE PAGE of a New Zealand Electoral Commission return as transcribed by a page reader. "
          "Return the money rows printed on the page as ONE JSON object and nothing else: "
          '{"rows": [{"part": "A"|"B"|"C"|"D"|"E"|"F"|"G"|null, "n": <row number as printed or null>, '
          '"amount": <number>, "date": "<as printed or null>", "donor": "<name and address as printed, or null>", '
          '"is_total": <true where the line is a printed TOTAL, false for a donation line>}], '
          '"parts_named": ["A", ...], "declared_total": <the grand total printed on a declaration page, or null>}. '
          "Figures as plain numbers with no currency sign and no thousands separators; NIL is 0. "
          "Copy what is printed; do not add, correct or sum anything. Markup (HTML, Markdown, OTSL tags) is not content.")
ASK = "PAGE TEXT:\n"


def parse(answer: str) -> dict:
    m = re.search(r"\{.*\}", answer or "", re.S)
    if not m:
        return {"rows": [], "parts_named": [], "declared_total": None, "unparsed": True}
    try:
        body = json.loads(m.group(0))
    except ValueError:
        return {"rows": [], "parts_named": [], "declared_total": None, "unparsed": True}
    rows = []
    for r in body.get("rows") or []:
        if not isinstance(r, dict):
            continue
        amt = r.get("amount")
        try:
            amt = float(re.sub(r"[^\d.\-]", "", str(amt))) if amt is not None and str(amt).strip() != "" else None
        except ValueError:
            amt = None
        rows.append({"part": (str(r.get("part")).upper()[:1] if r.get("part") else None), "n": r.get("n"), "amount": amt,
                     "date": r.get("date"), "donor": r.get("donor"), "is_total": bool(r.get("is_total"))})
    dt_ = body.get("declared_total")
    try:
        dt_ = float(re.sub(r"[^\d.\-]", "", str(dt_))) if dt_ is not None and str(dt_).strip() != "" else None
    except ValueError:
        dt_ = None
    return {"rows": rows, "parts_named": [str(p).upper()[:1] for p in (body.get("parts_named") or [])],
            "declared_total": dt_, "unparsed": False}


def ask(text: str, url: str, model: str, post=None) -> tuple[dict, str]:
    out = modelclient.chat(url, lane=LANE, model=model,
                           messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": ASK + score.plain(text)[:40000]}],
                           extra={"temperature": 0.0, "max_tokens": 6000, "chat_template_kwargs": {"enable_thinking": False}},
                           timeout=900, post=post)
    return parse((out["choices"][0]["message"]["content"] or "").strip()), out.get("model") or model


def rows_key_settings(page_reader_model: str, page_settings: dict) -> dict:
    return {"of": page_reader_model, "of_settings": rd.settings_hash(page_settings),
            "system_sha": hashlib.sha256(SYSTEM.encode()).hexdigest()[:16], "temperature": 0.0, "max_tokens": 6000}


def run(sha256: str, *, url: str, model: str, store: rd.Store = None, post=None, log=print, run_id: str = "") -> dict:
    store = store or rd.Store()
    tally = {"document": sha256, "readings": 0, "done": 0, "replayed": 0, "failed": 0}
    for r in score.stored_readings(sha256):
        if r.get("read_from") != "pixels" or not str(r.get("reader", "")).startswith("support.trials"):
            continue
        tally["readings"] += 1
        settings = rows_key_settings(r["model"], r["settings"])
        key = rd.reading_key(sha256, r["page"], model, settings, r["profile"], r["profile_version"])
        if store.has(key):
            tally["replayed"] += 1
            continue
        try:
            body, served = ask(r["text"], url, model, post=post)
        except Exception as e:  # noqa: BLE001
            tally["failed"] += 1
            log(f"rows: {sha256[:12]} p{r['page']} of {r['model']}: FAILED {type(e).__name__}")
            continue
        reading = rd.Reading(sha256, r["page"], READER, served, settings, r["profile"], r["profile_version"], "text",
                             json.dumps({"parts_named": body["parts_named"], "declared_total": body["declared_total"],
                                         "unparsed": body["unparsed"]}),
                             rows=body["rows"], checks={"of_reader": r["model"], "of_key": r.get("key") or "", "trial_pass": (r.get("checks") or {}).get("trial_pass")},
                             made_at=dt.datetime.now().astimezone().isoformat(timespec="seconds"))
        store.put(reading)
        tally["done"] += 1
        log(f"rows: {sha256[:12]} p{r['page']} of {r['model']}: {len(body['rows'])} rows, parts {''.join(body['parts_named'])}, "
            f"declared {'yes' if body['declared_total'] is not None else 'no'}")
    return tally


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__)
        return 2
    url, model = os.environ.get("QV4_MODEL_URL"), os.environ.get("QV4_MODEL")
    if not url or not model:
        print("rows: no card: QV4_MODEL_URL and QV4_MODEL come from the worker", file=sys.stderr)
        return 3
    t = run(argv[0], url=url, model=model, run_id=os.environ.get("QV4_RUN_ID", ""))
    print(f"rows: {argv[0][:12]}: {t['done']} done, {t['replayed']} replayed, {t['failed']} failed of {t['readings']} readings")
    return 1 if t["failed"] and not t["done"] else 0


if __name__ == "__main__":
    sys.exit(main())
