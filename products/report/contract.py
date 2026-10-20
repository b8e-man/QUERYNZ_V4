"""What a template may rely on, and how it reaches it.

A use-case template under `products/templates/<nn>-<name>/` may not import
`products.report` (the one-way test holds a template folder to its own code),
so the shape hands this module to a template's `rules.py` when it loads it:
the name `contract` is bound in the rules file's namespace before it runs,
and a rule file writes `flag = contract.flag` or calls `contract.items(...)`
with no import line. Nothing else of the shape is reachable that way, and
nothing here reads a database: a rule is a pure function of the built report.

What the contract holds:

  flag(...)                  a rule's verdict: fired cites, clear names its sources, blocked says why
  STATUSES, SEVERITIES       the words a flag may use
  items, section, all_items  reading the built report
  COMMON_RULES               the rules every subject report carries, run by the builder for every
                             template unless its template.toml says `common_rules = false`:
                             group-standing, hubs-met, replaced-return. A template rule that returns
                             a flag with the same `rule` name replaces the common one.
  presentation_problems      the shape's presentation rules (products.report.rules), the check the
                             builder runs on every report; a template's tests may run it on a fixture
  CAUSE, OWNER, address_shaped, BLANK_OK
                             the words those rules read, so a template can keep its own text clear
  report_url(ref, base)      the stable address of a report on a row

Version: VERSION. A template that needs more asks for it here, by a card on
the report lane; it does not copy the shape's code."""
from __future__ import annotations

import urllib.parse

from products.report import rules as _rules

VERSION = "0.2"
STATUSES = ("fired", "clear", "blocked")
SEVERITIES = ("red", "amber", "info")

presentation_problems = _rules.problems
CAUSE, OWNER, BLANK_OK, address_shaped = _rules.CAUSE, _rules.OWNER, _rules.BLANK_OK, _rules.address_shaped


# ── the flag ────────────────────────────────────────────────────────────────

def flag(rule: str, version: str, status: str, severity: str, text: str, citations: tuple = (), sources_held: tuple = (),
         sources_not_held: tuple = (), scope: str = "subject") -> dict:
    """A rule's verdict; the contract is checked at construction. `fired`
    must cite rows; `clear` must name the sources it was checked against,
    because a green is only "none in the sources held"; `blocked` must say
    why the check could not run, and is never shown as clear."""
    if status not in STATUSES:
        raise ValueError(f"{rule}: status {status!r}")
    if severity not in SEVERITIES:
        raise ValueError(f"{rule}: severity {severity!r}")
    if status == "fired" and not citations:
        raise ValueError(f"{rule}: a fired flag must cite the rows it rests on")
    if status == "clear" and not sources_held:
        raise ValueError(f"{rule}: a clear flag must name the sources it was checked against")
    if status == "blocked" and not text:
        raise ValueError(f"{rule}: a blocked flag must say why the check could not run")
    return {"rule": rule, "version": version, "status": status, "severity": severity, "text": text, "scope": scope,
            "citations": tuple(citations), "sources_held": tuple(sources_held), "sources_not_held": tuple(sources_not_held)}


# ── reading the built report ────────────────────────────────────────────────

def items(report: dict, views=None, grades=("confirmed", "near")):
    """The items of every section, in order; narrowed to views and grades."""
    for s in report["sections"]:
        for it in s["items"]:
            if (views is None or it["view"] in views) and it["grade"] in grades:
                yield it


def section(report: dict, name: str) -> dict:
    for s in report["sections"]:
        if s["name"] == name:
            return s
    return {"name": name, "heading": "", "items": [], "blank": None}


def all_items(report: dict) -> dict:
    """{ref: item} for the subject, the header's group rows and every section's items, each once."""
    out = {}
    for it in [report.get("subject")] + list(report.get("members", [])) + [it for s in report["sections"] for it in s["items"]]:
        if it:
            out.setdefault(it["ref"], it)
    return out


# ── the rules every subject report carries ──────────────────────────────────

COMMON_VERSION = "0.2"


def group_standing(report: dict) -> dict:
    g = report["group"]
    subject = report["subject"]
    if not g.get("built"):
        return flag("group-standing", COMMON_VERSION, "blocked", "info",
                    "no links have been published: the subject is this one row, and every other row is a namesake, apart")
    if g.get("via"):
        standing = "contested as a whole: the watch flagged a sign that its confirmed links cover two people; every other row of the group is listed as near" \
            if g.get("contested") else f"of {g.get('size', 1)} rows, not contested"
        text = (f"the subject is a filed row ({subject['view']}), which has no group of its own; the group shown is that of the person row a "
                f"confirmed link names ({g['via']}), {standing}")
        if g.get("via_groups", 1) > 1:
            text += f"; confirmed links name person rows in {g['via_groups']} groups, and the first by ref is walked"
        return flag("group-standing", COMMON_VERSION, "fired" if g.get("contested") else "clear", "amber" if g.get("contested") else "info", text,
                    citations=(subject["ref"], g["via"]), sources_held=("pub.groups", "pub.links"))
    if g.get("contested"):
        return flag("group-standing", COMMON_VERSION, "fired", "amber",
                    "the subject's group is contested as a whole: the watch flagged a sign that its confirmed links cover two people; "
                    "every other row of the group is listed as near", citations=(subject["ref"],))
    if subject["kind"] != "person":
        return flag("group-standing", COMMON_VERSION, "clear", "info", "an organisation: its official number is the link, and it needs no group",
                    sources_held=("pub.links",))
    if g.get("size", 1) == 1:
        return flag("group-standing", COMMON_VERSION, "clear", "info",
                    "no confirmed link reaches the subject's row: the subject is this one row; every same name elsewhere is a namesake, apart",
                    sources_held=("pub.groups", "pub.links"))
    return flag("group-standing", COMMON_VERSION, "clear", "info", f"the subject's group of {g.get('size', 1)} rows is not contested",
                sources_held=("pub.groups", "pub.links"))


def hubs_met(report: dict) -> dict:
    hubs = report["hubs"]
    if hubs:
        kinds = sorted({h["kind"] for h in hubs})
        return flag("hubs-met", COMMON_VERSION, "fired", "info",
                    f"{len(hubs)} hub(s) met on the walk ({', '.join(kinds)}): a connection through a hub means little on its own",
                    citations=tuple(h["ref"] for h in hubs))
    return flag("hubs-met", COMMON_VERSION, "clear", "info",
                "no hub met: no professional director, nominee, Crown holder or thousand-company address on the walk",
                sources_held=("pub.directors", "pub.shareholders", "pub.company_addresses", "pub.groups"))


def replaced_rows(report: dict) -> dict:
    rep = [it for it in items(report) if (it.get("row") or {}).get("replaced_by")]
    if rep:
        return flag("replaced-return", COMMON_VERSION, "fired", "info",
                    f"{len(rep)} row(s) come from a return the Commission has since replaced by an amendment; each is shown with its replacement "
                    "named and is never summed", citations=tuple(it["ref"] for it in rep))
    return flag("replaced-return", COMMON_VERSION, "clear", "info", "no row shown comes from a replaced return",
                sources_held=("pub.party_return_donors", "pub.party_return_totals", "pub.candidate_return_donors"))


COMMON_RULES = (group_standing, hubs_met, replaced_rows)


# ── the address of a report ─────────────────────────────────────────────────

def report_url(ref: str, base: str = "", template: str = "") -> str:
    """The stable address of a report on a row: `<base>/report/<register>:<key>`,
    the ref as the board names the row, with `?template=<name>` when not the
    shape's own. `base` is the server's root (the board's `QV4_REPORT_URL`),
    empty for a link on the report's own page."""
    url = f"{base.rstrip('/')}/report/{urllib.parse.quote(ref, safe=':/')}"
    return url + (f"?template={urllib.parse.quote(template)}" if template and template != "subject" else "")
