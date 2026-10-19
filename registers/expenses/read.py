"""The reading: each release workbook's tables through its own document
profile (profiles before readers), turned into register rows under the
row contract, or catch-log lines saying why not. No model is called: a
workbook is read as cells (`sheet.py`, `biff.py`), its tables found by
their labels (`table.py`), and every row checked by the release's own
arithmetic (`check.py`).

The profiles this lane proposes (`profile-proposed.jsonl`) are read from
there until the integrator appends them to `support/profiles`; the higher
version wins wherever it is held.

A row's place is its cell: the key of a figure is the document's hash, the
sheet's position and the cell reference, which a re-read of the same bytes
gives again. A member's line is keyed by its row in the same way.

    profile(slug)                                  the current version, shared ledger or proposed
    release_rows(data, sha, kind, meta, at)        -> {releases, lines, figures, notes, totals, set_aside}
"""
import datetime as dt
import os
import re

from keys import names, parties
from support import profiles
from registers.expenses import check, sheet, table

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
PROFILE_OF = {"mp-workbook": "parliamentary-expenses-workbook", "executive-workbook": "ministerial-expenses-workbook",
              "catalogue-listing": "data-govt-catalogue-package", "dia-listing": "dia-ministers-expense-listing"}
PUBLISHER = {"mp-workbook": "parliamentary-service", "executive-workbook": "internal-affairs"}
READER = "registers.expenses 1: workbook cells (stdlib)"
_MARKS = re.compile(r"\s*\(\s*[A-Za-z0-9]{1,2}\s*\)")
_MP = re.compile(r"\s+MP$")


def profile(slug: str) -> dict:
    found = [p for p in (profiles.profile(slug), profiles.profile(slug, PROPOSED)) if p]
    if not found:
        raise LookupError(f"no document profile {slug}: profiles come before readers")
    return max(found, key=lambda p: int(p["version"]))


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def person(printed: str) -> str:
    """The name without its footnote markers or a trailing 'MP', given-first, honorifics off (keys.names)."""
    s = _MP.sub("", _MARKS.sub("", printed or "")).strip()
    return names.person_name(s).display if s else None


def _iso(d):
    return d.isoformat() if d else None


def release_rows(data: bytes, sha256: str, kind: str, meta: dict = None, loaded_at: str = None) -> dict:
    """One workbook → its register rows and catch-log lines. `meta` is the old job's manifest row
    (url, name, quarter): the quarter is the publisher's label, used only where the workbook's
    own title states no period, and the basis says so."""
    meta = meta or {}
    at = loaded_at or now()
    prof = profile(PROFILE_OF[kind])
    stamp = {"reader": READER, "profile": prof["slug"], "profile_version": int(prof["version"]), "read_from": "text",
             "loaded_at": at}
    out = {k: [] for k in ("releases", "lines", "figures", "notes", "totals", "set_aside")}
    try:
        books = sheet.sheets(data, meta.get("file") or sha256)
    except Exception as exc:  # noqa: BLE001 — a workbook that will not open is a catch-log line, never a dead load
        out["set_aside"].append((sha256, "workbook", f"the workbook will not open: {type(exc).__name__}: {str(exc)[:160]}"))
        return out
    label = None
    if meta.get("quarter_start") and meta.get("quarter_end"):
        label = (dt.date.fromisoformat(meta["quarter_start"]), dt.date.fromisoformat(meta["quarter_end"]))
    n_tables = 0
    for si, (sname, cells) in enumerate(books, 1):
        tables, skipped = table.read(cells, sname, si)
        for ref, why in skipped:
            out["set_aside"].append((f"{sha256}/sheet{si}/{ref}", "row", f"{sname}!{ref}: {why}"))
        if not tables and any(isinstance(c.value, float) for c in cells):
            out["set_aside"].append((f"{sha256}/sheet{si}", "sheet",
                                     f"sheet {sname!r} carries figures and no release table (no title and header found)"))
        before = []
        for t in tables:
            n_tables += 1
            rkey = f"{sha256}/sheet{si}/r{t.header_row}"
            per, basis = t.period, "title"
            if per is None and label and len(books) == 1 and len(tables) == 1:
                per, basis = label, "publisher's label"
            if per is None:
                out["set_aside"].append((rkey, "release", f"{sname}: the table states no period and none can be taken "
                                                          f"from the publisher's label for this one table"))
                before += t.members()
                continue
            differs_from_label = bool(label and basis == "title" and len(books) == 1 and len(tables) == 1 and per != label)
            out["releases"].append({
                "key": rkey, "document": sha256, "page": si, "place": f"{sname}!R{t.header_row}", "sheet": sname,
                "publisher": PUBLISHER[kind], "title": t.title, "period_start": _iso(per[0]), "period_end": _iso(per[1]),
                "period_basis": basis, "label": meta.get("name"),
                "label_start": _iso(label[0]) if label else None, "label_end": _iso(label[1]) if label else None,
                "label_differs": differs_from_label, "url": meta.get("url"),
                "columns": " | ".join(f"{c.heading} [{c.role}]" for c in t.columns), **stamp})
            heading = {c.col: c for c in t.columns}
            for ln in t.lines:
                lkey = f"{sha256}/sheet{si}/row{ln.row}"
                if ln.kind == "member":
                    chk, csum, total = check.row_check(ln, t)
                    party, pbasis = parties.party_name(ln.party) if ln.party else (None, "unresolved")
                    out["lines"].append({
                        "key": lkey, "release": rkey, "document": sha256, "page": si, "place": f"{sname}!R{ln.row}",
                        "member": ln.name, "name": person(ln.name), "party_printed": ln.party_printed,
                        "party_label": ln.party, "party": party, "party_basis": pbasis,
                        "marks": " ".join(ln.marks) or None, "categories_sum": csum, "total": total, "check": chk,
                        **stamp})
                    if chk not in check.PUBLISHED_CHECKS:
                        cats = ", ".join(f"{heading[c].heading} {ln.figures[c][1]}" for c in sorted(ln.figures)
                                         if heading[c].role == "category")
                        out["set_aside"].append((lkey, "arithmetic",
                                                 f"{sname}!R{ln.row} {ln.name}: categories add to {csum} and the row prints "
                                                 f"{'no total' if total is None else total} ({cats}); not published"))
                    for c, (v, printed, ref) in sorted(ln.figures.items()):
                        out["figures"].append({
                            "key": f"{sha256}/sheet{si}/{ref}", "line": lkey, "release": rkey, "document": sha256,
                            "page": si, "place": f"{sname}!{ref}", "category": heading[c].heading,
                            "role": heading[c].role, "figure": v, "printed": printed, **stamp})
            for tt in check.totals(t, before):
                wide = tt["scope"] in ("table", "sheet")
                for h, printed, rows_sum, equal in tt["columns"]:
                    role = next(c.role for c in t.columns if c.heading == h)
                    out["totals"].append({"release": rkey, "line_place": f"{sname}!R{tt['line'].row}",
                                          "label": tt["line"].name, "scope": tt["scope"], "heading": h, "total_role": role,
                                          "printed": printed, "rows_sum": rows_sum, "equal": equal, "widest": False})
            # the widest total of the table (its grand total) is the outside check's figure
            widest = [x for x in out["totals"] if x["release"] == rkey and x["scope"] in ("table", "sheet")]
            if widest:
                last = widest[-1]["line_place"]
                for x in widest:
                    x["widest"] = x["line_place"] == last
            for ref, text in t.notes:
                out["notes"].append({"key": f"{sha256}/sheet{si}/{ref}", "release": rkey, "document": sha256, "page": si,
                                     "place": f"{sname}!{ref}", "text": text})
            before += t.members()
    if n_tables == 0:
        out["set_aside"].append((sha256, "workbook", "no release table found in any sheet (no title and header by their labels)"))
    return out
