"""Each party's life on the register, from the Commission's two publications:
its Gazette notices (events, oldest first) and its register page (who is on
it the day it was captured).

THE REGISTRATION IS THE PARTY (old ruling 349); a name is a label it wore
for a window. A registration opens on the day the Commission registered it
and closes on the day it cancelled it; between, each name and abbreviation
it carried has its own window, opened by the registration or by a change the
Commission states, closed by the next change or the cancellation. A party
cancelled and registered again is two registrations.

Renames come from registration windows. A stated change of name keeps the
registration, so the register page prints the party's registration date
under its new name: the page's date and the date of the notice that
registered the old name are one registration printed twice (the notice is
gazetted on the day or up to `GAZETTAL_LAG_DAYS` after). Every page party
is checked that way (`window`), and a page party the notices reach by no
name is paired by the window alone, unique on both sides or not at all
(old lesson: scarcity is not identity).

A name in a notice finds its registration among those live on the day: by
its current name, then by any name or abbreviation it has carried, then by
a unique prefix. A party the notices first meet when it is cancelled or
renamed was registered before their reach (24 February 2000) and has no
start date until the page gives one. Nothing is guessed: two candidates
is a catch-log line.

    build(events, entries, page_date)   Lifecycle(registrations, set_aside)
    name_key(name)                      the comparison key
"""
import datetime as dt
import hashlib
import re
from dataclasses import dataclass, field

from keys.names import organisation_key
from keys.parties import core

GAZETTAL_LAG_DAYS = 120
REACH = "2000-02-24"            # the first notice the export holds
PREFIX_MIN = 8


def name_key(name: str) -> str:
    """Letters and digits, diacritics folded, "NZ" read as New Zealand, the
    leading article and a trailing "party" off: "The Kiwi Party", "Kiwi
    Party" and "the Kiwi Party" are one key; "New Conservative" and
    "Conservative Party NZ" are two."""
    k = core(organisation_key(name or ""))
    return k[:-5] if k.endswith("party") and len(k) > 8 else k


@dataclass
class Name:
    name: str
    kind: str                     # name | abbreviation | printed
    from_on: str = None
    to_on: str = None
    basis: str = ""               # registered | stated | window | register page | printed
    notice: str = None            # the Gazette notice that says so, when one does
    ordinal: int = None


@dataclass
class Registration:
    first_name: str
    registered_on: str = None
    registered_by: str = None     # the latest day it was registered by (a year's list, or the reach)
    registered_basis: str = ""
    registered_notice: str = None
    registered_ordinal: int = None
    cancelled_on: str = None
    cancelled_notice: str = None
    cancelled_ordinal: int = None
    names: list = field(default_factory=list)
    entry: object = None          # the register page's entry, when it lists the party
    page_basis: str = None        # name | former name | window | page only
    window: str = None            # same day | within the gazettal lag | differs | no notice date
    off_register_by: str = None   # not on the page and no cancellation held
    key: str = None

    def current(self, kind: str = "name"):
        live = [n for n in self.names if n.kind == kind and n.to_on is None and not getattr(n, "_closed", False)]
        return live[-1] if live else None

    def keys(self) -> set:
        return {name_key(n.name) for n in self.names}

    @property
    def name(self) -> str:
        """The name it carries now, or last carried; the page's spelling when listed."""
        if self.entry is not None:
            return self.entry.name
        c = self.current() or next((n for n in reversed(self.names) if n.kind == "name"), None)
        if c is None:
            return self.first_name
        # the latest printing of that name: a cancellation prints "… Party" where the registration's list cut it off
        same = [n for n in self.names if n.kind in ("name", "printed") and name_key(n.name) == name_key(c.name)]
        return same[-1].name


@dataclass
class Lifecycle:
    registrations: list = field(default_factory=list)
    resolved: dict = field(default_factory=dict)      # (notice, ordinal) → Registration
    set_aside: list = field(default_factory=list)     # (item, stage, reason)
    corrections: list = field(default_factory=list)   # (notice, ref, field, old, new)


def _close(n: Name, on: str):
    if n is not None:
        n.to_on = on
        if on is None:
            n._closed = True


def _find(name: str, live: list):
    """(registration, how) or (None, why)."""
    k = name_key(name)
    if not k:
        return None, "no name"
    for how, test in (("current name", lambda r: r.current() and name_key(r.current().name) == k),
                      ("a name it carried", lambda r: k in r.keys()),
                      ("a unique prefix", lambda r: len(k) >= PREFIX_MIN and r.current() and (
                          name_key(r.current().name).startswith(k) or k.startswith(name_key(r.current().name))))):
        hits = [r for r in live if test(r)]
        if len(hits) == 1:
            return hits[0], how
        if len(hits) > 1:
            return None, f"{len(hits)} live registrations answer to {name!r} by {how}"
    return None, "none live"


def _correct(events: list, out: Lifecycle) -> list:
    """Apply each corrigendum to the notice it names; the corrigendum's
    quoted text is '<label>: <old>' → '<label>: <new>'."""
    by_notice = {}
    for e in events:
        by_notice.setdefault(e.notice, []).append(e)
    for c in [e for e in events if e.kind == "corrected"]:
        old = c.name.split(":", 1)[-1].strip()
        new = c.new_name.split(":", 1)[-1].strip()
        done = False
        for e in by_notice.get(c.ref, []):
            for f in ("name", "new_name", "abbreviation"):
                if getattr(e, f) == old:
                    setattr(e, f, new)
                    out.corrections.append((c.notice, c.ref, f, old, new))
                    done = True
        if not done:
            out.set_aside.append((f"{c.notice}", "notices", f"a corrigendum of {c.ref} whose text {old!r} the reader did not find there"))
    return [e for e in events if e.kind != "corrected"]


def build(events: list, entries: list, page_date: str, published: dict = None) -> Lifecycle:
    """events: notices.Event, every notice; entries: register.Entry from the
    page captured on `page_date`; published: notice → the day it was
    published (for an event the notice dates by the year only)."""
    out = Lifecycle()
    published = published or {}
    events = _correct(list(events), out)
    day = lambda e: e.decided_on or published.get(e.notice) or "9999"
    regs = out.registrations

    def live(on):
        return [r for r in regs if r.cancelled_on is None]

    def before_reach(name, e):
        r = Registration(first_name=name, registered_by=REACH, registered_basis="registered before the notices' reach")
        r.names.append(Name(name, "name", None, None, "printed in a later notice", e.notice, e.ordinal))
        regs.append(r)
        return r

    for e in sorted(events, key=lambda e: (day(e), e.notice, e.ordinal)):
        if e.kind not in ("registered", "cancelled", "renamed", "abbreviation"):
            continue
        on = e.decided_on
        r, how = _find(e.name, live(on))
        if e.kind == "registered":
            if r is not None and how == "current name":
                r.names.append(Name(e.name, "printed", None, None, "printed", e.notice, e.ordinal))
                out.resolved[(e.notice, e.ordinal)] = r
                if r.registered_on is None and on:
                    r.registered_on, r.registered_notice, r.registered_ordinal = on, e.notice, e.ordinal
                continue
            r = Registration(first_name=e.name, registered_on=on, registered_by=on or published.get(e.notice),
                             registered_basis="registered" if on else "listed as registered during the year",
                             registered_notice=e.notice, registered_ordinal=e.ordinal)
            r.names.append(Name(e.name, "name", on, None, "registered", e.notice, e.ordinal))
            if e.abbreviation:
                r.names.append(Name(e.abbreviation, "abbreviation", on, None, "registered", e.notice, e.ordinal))
            regs.append(r)
            out.resolved[(e.notice, e.ordinal)] = r
            continue
        if r is None:
            if how != "none live":
                out.set_aside.append((f"{e.notice}/{e.ordinal}", "lifecycle", how))
                continue
            r = before_reach(e.name, e)
        out.resolved[(e.notice, e.ordinal)] = r
        cur = r.current()
        if cur is not None and e.kind != "abbreviation" and name_key(cur.name) == name_key(e.name) and cur.name != e.name:
            r.names.append(Name(e.name, "printed", None, None, "printed", e.notice, e.ordinal))
        if e.kind == "cancelled":
            r.cancelled_on, r.cancelled_notice, r.cancelled_ordinal = on, e.notice, e.ordinal
            _close(r.current(), on)
            _close(r.current("abbreviation"), on)
        elif e.kind == "renamed":
            if cur is not None and name_key(cur.name) != name_key(e.name):
                r.names.append(Name(e.name, "printed", None, None, "printed", e.notice, e.ordinal))
            _close(r.current(), on)
            r.names.append(Name(e.new_name, "name", on, None, "stated", e.notice, e.ordinal))
        elif e.kind == "abbreviation":
            a = r.current("abbreviation")
            if a is None and e.old_abbreviation:
                r.names.append(Name(e.old_abbreviation, "abbreviation", None, on, "stated as the former abbreviation", e.notice, e.ordinal))
            _close(a, on)
            if e.abbreviation:
                r.names.append(Name(e.abbreviation, "abbreviation", on, None, "stated", e.notice, e.ordinal))
    _fold_page(out, entries, page_date)
    _keys(out)
    return out


def _lag(page_on: str, notice_on: str) -> str:
    if not notice_on:
        return "no notice date"
    d = (dt.date.fromisoformat(notice_on) - dt.date.fromisoformat(page_on)).days
    return "same day" if d == 0 else ("within the gazettal lag" if 0 < d <= GAZETTAL_LAG_DAYS else "differs")


def _fold_page(out: Lifecycle, entries: list, page_date: str):
    regs = out.registrations
    live = [r for r in regs if r.cancelled_on is None]
    matched = {}
    pending = []
    for en in entries:
        r, how = _find(en.name, live)
        if r is not None and how in ("current name", "a name it carried") and r not in matched.values():
            matched[en.ordinal] = r
            r.page_basis = "name" if how == "current name" else "former name"
        else:
            pending.append(en)
    # the window alone, unique on both sides
    unmatched = [r for r in live if r not in matched.values()]
    pairs = [(en, r) for en in pending for r in unmatched
             if r.registered_on and _lag(en.registered_on, r.registered_on) in ("same day", "within the gazettal lag")]
    for en, r in pairs:
        if sum(1 for p in pairs if p[0] is en) == 1 and sum(1 for p in pairs if p[1] is r) == 1:
            matched[en.ordinal] = r
            r.page_basis = "window"
            _close(r.current(), None)
            r.names.append(Name(en.name, "name", None, None, "window"))
    for en in entries:
        r = matched.get(en.ordinal)
        if r is None:
            if any(en is p[0] for p in pairs):
                out.set_aside.append((f"page party {en.ordinal}", "page", "two registrations fit the page's date; neither is taken"))
            r = Registration(first_name=en.name, registered_on=en.registered_on, registered_by=en.registered_on,
                             registered_basis="register page")
            r.names.append(Name(en.name, "name", en.registered_on, None, "register page"))
            r.page_basis = "page only"
            regs.append(r)
        r.entry = en
        if r.registered_on is None:
            r.registered_on, r.registered_basis = en.registered_on, "register page"
            r.window = "no notice date"
            first = next((n for n in r.names if n.kind == "name"), None)
            if first is not None and first.from_on is None and first.basis.startswith("printed"):
                first.from_on = en.registered_on
        else:
            r.window = _lag(en.registered_on, r.registered_on) if r.registered_notice else "no notice date"
        cur = r.current()
        if cur is not None and cur.name != en.name and name_key(cur.name) == name_key(en.name):
            r.names.append(Name(en.name, "printed", None, None, "register page"))
        a = r.current("abbreviation")
        if en.abbreviation and (a is None or name_key(a.name) != name_key(en.abbreviation)):
            _close(a, None)
            r.names.append(Name(en.abbreviation, "abbreviation", None, None, "register page"))
        elif not en.abbreviation and a is not None:
            _close(a, None)
    for r in regs:
        if r.cancelled_on is None and r.entry is None:
            r.off_register_by = page_date


def stable_key(r: Registration) -> str:
    start = r.registered_on or "before-" + REACH[:4]
    return f"ec-party/{start}/{hashlib.sha256(name_key(r.first_name).encode()).hexdigest()[:12]}"


def _keys(out: Lifecycle):
    seen = {}
    for r in sorted(out.registrations, key=lambda r: (r.registered_on or "", r.registered_notice or "", r.first_name)):
        k = stable_key(r)
        seen[k] = seen.get(k, 0) + 1
        r.key = k if seen[k] == 1 else f"{k}/{seen[k]}"
