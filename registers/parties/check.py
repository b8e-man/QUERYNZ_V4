"""The lane's check against the world outside it (contract: the lane).

The Commission publishes its register twice: as the page of parties
registered today, and as the Gazette notices that registered, renamed and
cancelled them. The notices alone are read into a lifecycle, with the page
left out, and every party on the page is looked for among the
registrations the notices say are live on the page's day:

  joined          by its name, or by the registration window alone (unique on both sides)
  before reach    registered before the notices begin (24 February 2000); none is owed
  no notice held  registered since, and the notices hold no registration: a gap in the old capture
  differs         joined, and the notice's day is not the page's day nor up to the gazettal lag after it

and every registration the notices say is live and the page does not list
(a cancellation the old capture missed). The four renames known before
this lane (old card C455, found from the windows) must each come out as one
registration on the page, its window agreeing. A `differs`, a known rename
broken, or a page party with no published row fails the check.

    compare(events, entries, page_date, published)   the figures
    python -m registers.parties.check [--schema parties | scratch_<session>] [--database querynz_v4]

Read-only.
"""
import sys

from registers.parties import lifecycle

#: (the name the notices registered, the name the page prints): old card C455, measured 2026-10-09
KNOWN_RENAMES = (
    ("Maori Party", "Te Pāti Māori"),
    ("Conservative Party of New Zealand", "Conservative Party NZ"),
    ("NZ Outdoors Party", "NZ Outdoors & Freedom Party"),
    ("The Opportunities Party (TOP)", "Opportunity Party"),
)


def compare(events: list, entries: list, page_date: str, published: dict = None) -> dict:
    alone = lifecycle.build(events, [], page_date, published)
    live = [r for r in alone.registrations if r.cancelled_on is None]
    joined, window, before, missing, differs = [], [], [], [], []
    used = set()
    for en in entries:
        r, how = lifecycle._find(en.name, live)
        if r is None or how == "a unique prefix" or id(r) in used:
            fits = [x for x in live if id(x) not in used and x.registered_on
                    and lifecycle._lag(en.registered_on, x.registered_on) in ("same day", "within the gazettal lag")]
            r = fits[0] if len(fits) == 1 else None
            if r is not None:
                window.append((en.name, r.first_name))
        else:
            joined.append(en.name)
        if r is None:
            (before if en.registered_on < lifecycle.REACH else missing).append(en.name)
            continue
        used.add(id(r))
        lag = lifecycle._lag(en.registered_on, r.registered_on) if r.registered_notice else "no notice date"
        if lag == "differs":
            differs.append((en.name, en.registered_on, r.registered_on))
    not_listed = [r.name for r in live if id(r) not in used and r.registered_by and r.registered_by <= page_date]
    full = lifecycle.build(events, entries, page_date, published)
    renames = []
    for old, new in KNOWN_RENAMES:
        hit = [r for r in full.registrations
               if r.entry is not None and lifecycle.name_key(r.entry.name) == lifecycle.name_key(new)
               and lifecycle.name_key(old) in r.keys()]
        ok = len(hit) == 1 and hit[0].window in ("same day", "within the gazettal lag")
        renames.append((old, new, ok, hit[0].window if hit else "not found"))
    return {"page": len(entries), "joined": joined, "window": window, "before_reach": before,
            "no_notice_held": missing, "differs": differs, "not_on_page": not_listed, "renames": renames}


def failed(out: dict, published_rows: int = None) -> list:
    why = [f"{n}: the page says {p}, the notice {q}" for n, p, q in out["differs"]]
    why += [f"known rename {o} → {n} does not come out as one registration ({w})" for o, n, ok, w in out["renames"] if not ok]
    if published_rows is not None and published_rows != out["page"]:
        why.append(f"the page lists {out['page']} parties; {published_rows} published rows are on the register")
    return why


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else "parties"
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    from support.docstore.landing import read_bytes
    from registers.parties import notices, read, register
    from registers.parties.load import table
    shared = schema.startswith("scratch_")          # the sample's shared schema: the lane's tables carry its name
    regs, events_t = table(schema, "registrations", shared), table(schema, "events", shared)
    with db.connect(db.READ_KEY if database == "querynz_v4" else db.OWNER_KEY, database) as conn:
        page_sha, page_date = conn.execute(f"SELECT register_document, register_seen_on FROM {regs} "
                                           f"WHERE register_document IS NOT NULL LIMIT 1").fetchone()
        export_sha = conn.execute(f"SELECT document FROM {events_t} LIMIT 1").fetchone()[0]
        on_register = conn.execute(f"SELECT count(*) FROM {regs} WHERE on_register").fetchone()[0]
    events, published = [], {}
    for n in read.read_export(read_bytes(export_sha)):
        published[n["notice"]] = n["published_on"]
        events += notices.read(n["text"], n["notice"], n["published_on"]).events
    out = compare(events, register.read(read_bytes(page_sha)).entries, str(page_date), published)
    print(f"the register page of {page_date}: {out['page']} parties; joined to the notices by name "
          f"{len(out['joined'])}, by the window alone {len(out['window'])}; registered before the notices' reach "
          f"{len(out['before_reach'])}; registered since with no notice held {len(out['no_notice_held'])}")
    for n in out["no_notice_held"]:
        print(f"  no registration notice held: {n}")
    print(f"live by the notices and not on the page (a cancellation not held): {len(out['not_on_page'])}")
    for n in out["not_on_page"]:
        print(f"  {n}")
    for o, n, ok, w in out["renames"]:
        print(f"  known rename {o} → {n}: {'one registration, ' + w if ok else 'BROKEN (' + w + ')'}")
    why = failed(out, on_register)
    for w in why:
        print("FAILS " + w)
    return 1 if why else 0


if __name__ == "__main__":
    sys.exit(main())
