"""The release pipeline, behind the new contract (plan 4.4): read the
template's published views and nothing else, pinned to a frozen release's
listing of the captured documents, write a version folder of the ten kinds
of published file, run the gates, record the build, and stop.

What it has not got, on purpose: no deploy step, no deploy token, no
reading of the live site's feedback, no port 8300 or 8301, no publisher
unit to restart. The frozen product's chain is untouched; the comparison
in checks/ (4.5) reads this folder beside the frozen one.

    build(listing_version, out, ...) -> (ok, stamp, lines)
"""
from __future__ import annotations

import datetime as dt
import os
import sys

from products.published_site import candidate_money as CM
from products.published_site import figures as F
from products.published_site import gates, pin, read, redact, render, version
from products.published_site import site_template as ftm

OUT = os.environ.get("QV4_SITE_OUT") or os.path.join(os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live", "site")
#: the views whose rows carry the money: a row citing a document the listing does not hold is left out
PINNED_VIEWS = ("pub.party_return_totals", "pub.party_return_donors", "pub.party_return_loans", "pub.disclosures",
                "pub.candidate_return_totals", "pub.candidate_return_donors")


def pin_tables(tables: read.Tables, listing: pin.Listing) -> dict:
    """Drop, from the money views, every row whose document is not in the
    listing; return what was left out per view."""
    left = {}
    for view in PINNED_VIEWS:
        rows = tables.get(view)
        keep = [r for r in rows if listing.holds(r.get("document"))]
        left[view] = {"rows": len(rows), "kept": len(keep), "left_out": len(rows) - len(keep)}
        tables._cache[view] = keep
    return left


def build(listing_version: str = None, out: str = None, template_path: str = None, stamp: str = None,
          today: dt.date = None, listings_folder: str = None, log=print, allow_drop: bool = False) -> tuple:
    out = out or OUT
    lines = []

    def say(s):
        lines.append(s)
        log(s)

    t = ftm.load(template_path or ftm.PATH)
    s = t.settings
    lv = listing_version or pin.latest(listings_folder)
    if not lv:
        say("fail  no frozen release listing to build from (the watcher writes them under the live folder)")
        return False, None, lines
    try:
        listing = pin.load(pin.listing_path(lv, listings_folder))
    except (OSError, ValueError) as exc:
        say(f"fail  listing {lv}: {exc}")
        return False, None, lines
    say(f"  listing {listing.version}: {listing.files} captured files in {len(listing.folders)} folders")
    years = F.window_years(s, today)
    stamp = version.free_stamp(out, stamp or version.stamp_now())
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

    previous = version.last_built(out)
    try:
        conn = read.product_connect()
    except Exception as exc:  # noqa: BLE001 — a plain line, then stop
        say(f"fail  the published tables could not be read: {type(exc).__name__}: {exc}")
        return False, None, lines
    with conn:
        try:
            tables = read.Tables(t, conn, s["window_from"])
            for r in t.reads:
                if r.table in read.ROSTER_VIEWS or r.table in PINNED_VIEWS or r.table in ("pub.names",):
                    tables.get(r.table)
            left = pin_tables(tables, listing)
            idx = F.PartyIndex(tables.get("pub.parties"), tables.get("pub.party_names"))
            series = F.party_series(tables, s, idx, years)
            cm = CM.candidate_money(tables, idx, F.elections_in_window(tables, years), years)
            donors = F.donors(tables, s, idx, series, years, cm)
            forms = redact.load_forms(tables, s.get("suppressed_names_view"))
        except Exception as exc:  # noqa: BLE001
            say(f"fail  the published tables could not be read: {type(exc).__name__}: {exc}")
            return False, None, lines
        say(f"  read {len(tables.counts)} published views; {len(series)} parties with figures, {len(donors)} folded donors, "
            f"{cm.joined} of {cm.returns} candidate returns joined to a candidate, window {years[0]}–{years[-1]}")
        for view, x in left.items():
            if x["left_out"]:
                say(f"  {view}: {x['left_out']} of {x['rows']} rows cite a document the listing does not hold and are left out")

        hashes = set()
        for view in PINNED_VIEWS:
            hashes.update(r.get("document") for r in tables.get(view))
        hashes.update(p.get("document") for p in tables.get("pub.parties"))
        for view in ("pub.members", "pub.candidates", "pub.electorates", "pub.elections", "pub.party_financial_statements", "pub.party_statement_figures"):
            hashes.update(m.get("document") for m in tables.get(view))
        for st in tables.get("pub.party_financial_statements"):
            hashes.update(st.get("statements") or [])
        try:
            with read.read_connect() as rconn:
                doc_names = read.document_names(rconn, hashes)
        except Exception as exc:  # noqa: BLE001
            say(f"fail  the document store's names could not be read ({type(exc).__name__}); a build with no document store at hand stops")
            return False, None, lines
        unnamed = sum(1 for h, n in doc_names.items() if not n)
        say(f"  {len(doc_names)} documents cited, {unnamed} with no name in the document store")

        ctx = render.Context(t, tables, listing, years, idx, series, donors, doc_names, generated_at, cm=cm)
        files = {}
        files[render.paths.path("home")] = render.home(ctx)
        files[render.paths.path("parties")] = render.parties(ctx)
        files[render.paths.path("search-index")] = render.search_index(ctx)
        files.update(render.subject_parties(ctx))
        files.update(render.donor_pages(ctx))
        for name, fn in getattr(render, "MORE_KINDS", []):
            files.update(fn(ctx))
        redacted = 0
        if forms:
            for rel in list(files):
                files[rel], n = redact.redact(files[rel], forms)
                redacted += n
            say(f"  {len(forms)} suppressed name(s) in force: {redacted} string(s) suppressed; the rows and the money stay")
        built_kinds = {render.paths.kind_of(k) for k in files} - {""}
        not_held = getattr(render, "NOT_HELD_KINDS", {})
        not_built = {k: not_held.get(k, "not built yet by this pipeline") for k in render.paths.KINDS if k not in built_kinds}
        manifest = {"template": t.name, "template_version": t.version, "listing": {"version": listing.version, "files": listing.files,
                                                                                  "listed_at": listing.listed_at, "folders": listing.folders},
                    "pinned": left, "kinds_not_built": {k: v for k, v in not_built.items() if k not in not_held},
                    "kinds_not_held": {k: v for k, v in not_built.items() if k in not_held}, "window": {"from": years[0], "to": years[-1]},
                    "generated_at": generated_at, "views_read": tables.counts, "documents_cited": len(doc_names), "documents_unnamed": unnamed,
                    "suppressed_forms": len(forms), "strings_suppressed": redacted, "previous": os.path.basename(previous) if previous else None}
        try:
            vdir = version.write(out, stamp, files, manifest)
        except (OSError, ValueError, FileExistsError) as exc:
            say(f"fail  could not write the version: {exc}")
            return False, stamp, lines
        say(f"  version {stamp}: {len(files)} files written to {vdir}")
        gate_ctx = {"conn": conn, "years": years, "suppressed_forms": forms, "previous": previous, "allow_drop": allow_drop,
                    "candidate_returns_unjoined": sum(len(v) for v in cm.unjoined.values())}
        results = gates.run_all(vdir, ctx=gate_ctx)
    ok = True
    for name, g_ok, line in results:
        say(f"  {'PASS' if g_ok else 'FAIL'}  {name:<12} {line}")
        ok = ok and g_ok
    version.record(out, stamp, ok, f"{len(files)} files from listing {listing.version}", [(n, o) for n, o, _ in results])
    say(f"{'pass' if ok else 'fail'}  {stamp} {'built; nothing deployed, nothing flipped' if ok else 'refused by a gate; it stays on disk for reading'}")
    return ok, stamp, lines
