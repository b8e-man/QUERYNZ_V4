"""The shape's own rules (plan 5.1: "applies the template's own rules and
flags"). Pure functions over the built report, each returning one flag. A
use-case template brings its own file in this shape; these are the ones
every subject report carries: the group's standing, the hubs met, a
replaced return shown and never summed, insolvency and prohibition rows
reached, and what is not held. Loaded by path by products.report.template."""
from products.report.template import flag

GAZETTE = ("New Zealand Gazette notices: liquidations, receiverships, company notices, prohibitions, bankruptcies")
NOT_HELD_FOR_INSOLVENCY = ("the Insolvency Register (interface awaited since 19 September 2026)", "court judgments (step 5.4)")


def items(report, views=None, grades=("confirmed", "near")):
    for s in report["sections"]:
        for it in s["items"]:
            if (views is None or it["view"] in views) and it["grade"] in grades:
                yield it


def group_standing(report):
    g = report["group"]
    if not g.get("built"):
        return flag("group-standing", "0.1", "blocked", "info", "no links have been published: the subject is this one row, and every other row is a namesake, apart")
    if g.get("contested"):
        return flag("group-standing", "0.1", "fired", "amber", "the subject's group is contested as a whole: the watch flagged a sign that its confirmed links cover two people; "
                    "every other row of the group is listed as near", citations=(report["subject"]["ref"],))
    if report["subject"]["kind"] != "person":
        return flag("group-standing", "0.1", "clear", "info", "an organisation: its official number is the link, and it needs no group",
                    sources_held=("pub.links",))
    if g.get("size", 1) == 1:
        return flag("group-standing", "0.1", "clear", "info", "no confirmed link reaches the subject's row: the subject is this one row; every same name elsewhere is a namesake, apart",
                    sources_held=("pub.groups", "pub.links"))
    return flag("group-standing", "0.1", "clear", "info", f"the subject's group of {g.get('size', 1)} rows is not contested",
                sources_held=("pub.groups", "pub.links"))


def hubs_met(report):
    hubs = report["hubs"]
    if hubs:
        kinds = sorted({h["kind"] for h in hubs})
        return flag("hubs-met", "0.1", "fired", "info", f"{len(hubs)} hub(s) met on the walk ({', '.join(kinds)}): a connection through a hub means little on its own",
                    citations=tuple(h["ref"] for h in hubs))
    return flag("hubs-met", "0.1", "clear", "info", "no hub met: no professional director, nominee, Crown holder or thousand-company address on the walk",
                sources_held=("pub.directors", "pub.shareholders", "pub.company_addresses", "pub.groups"))


def replaced_rows(report):
    rep = [it for it in items(report) if it["row"].get("replaced_by")]
    if rep:
        return flag("replaced-return", "0.1", "fired", "info", f"{len(rep)} row(s) come from a return the Commission has since replaced by an amendment; "
                    "each is shown with its replacement named and is never summed", citations=tuple(it["ref"] for it in rep))
    return flag("replaced-return", "0.1", "clear", "info", "no row shown comes from a replaced return", sources_held=("pub.party_return_donors", "pub.party_return_totals", "pub.candidate_return_donors"))


def insolvency(report):
    conf = [it for it in items(report, ("gazette_liquidations", "gazette_company_notices", "gazette_bankruptcies"), ("confirmed",))]
    nearby = [it for it in items(report, ("gazette_liquidations", "gazette_company_notices", "gazette_bankruptcies"), ("near",))]
    if conf:
        return flag("insolvency", "0.1", "fired", "red", f"{len(conf)} Gazette insolvency notice(s) on the subject or a company a confirmed row sits on",
                    citations=tuple(it["ref"] for it in conf), sources_not_held=NOT_HELD_FOR_INSOLVENCY)
    if nearby:
        return flag("insolvency", "0.1", "fired", "amber", f"{len(nearby)} Gazette insolvency notice(s) reached only through a near link: a namesake or a name match, not the subject until confirmed",
                    citations=tuple(it["ref"] for it in nearby), sources_not_held=NOT_HELD_FOR_INSOLVENCY, scope="near")
    return flag("insolvency", "0.1", "clear", "red", "no Gazette insolvency notice on the subject or on a company it has a row on",
                sources_held=(GAZETTE,), sources_not_held=NOT_HELD_FOR_INSOLVENCY)


def prohibition(report):
    conf = [it for it in items(report, ("gazette_prohibitions",), ("confirmed",))]
    nearby = [it for it in items(report, ("gazette_prohibitions",), ("near",))]
    if conf:
        return flag("prohibition", "0.1", "fired", "red", f"{len(conf)} director prohibition notice(s) confirmed to the subject", citations=tuple(it["ref"] for it in conf))
    if nearby:
        return flag("prohibition", "0.1", "fired", "amber", f"{len(nearby)} director prohibition notice(s) under a name near the subject's; not the subject until confirmed",
                    citations=tuple(it["ref"] for it in nearby), scope="near")
    return flag("prohibition", "0.1", "clear", "red", "no director prohibition confirmed or near the subject in the Gazette notices held",
                sources_held=("New Zealand Gazette prohibition notices (pub.gazette_prohibitions)",))


RULES = (group_standing, hubs_met, replaced_rows, insolvency, prohibition)
