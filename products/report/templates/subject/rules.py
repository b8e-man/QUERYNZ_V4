"""The shape's own rules (plan 5.1: "applies the template's own rules and
flags"). Pure functions over the built report, each returning one flag. A
use-case template brings its own file in this shape. The rules every subject
report carries (the group's standing, the hubs met, a replaced return shown
and never summed) are the contract's COMMON_RULES and the builder runs them
for every template; this file adds the two the shape's own report shows,
insolvency and prohibition rows reached. Loaded by path by
products.report.template, which binds `contract` here before the file runs:
no import of the shape, the same way a use-case template's rules.py is
written."""
flag, items = contract.flag, contract.items   # noqa: F821  (bound by the loader)

V = "0.3"
GAZETTE = ("New Zealand Gazette notices: liquidations, receiverships, company notices, prohibitions, bankruptcies")
NOT_HELD_FOR_INSOLVENCY = ("the Insolvency Register (interface awaited since 19 September 2026)", "court judgments (step 5.4)")


def insolvency(report):
    conf = [it for it in items(report, ("gazette_liquidations", "gazette_company_notices", "gazette_bankruptcies"), ("confirmed",))]
    nearby = [it for it in items(report, ("gazette_liquidations", "gazette_company_notices", "gazette_bankruptcies"), ("near",))]
    if conf:
        return flag("insolvency", V, "fired", "red", f"{len(conf)} Gazette insolvency notice(s) on the subject or a company a confirmed row sits on",
                    citations=tuple(it["ref"] for it in conf), sources_not_held=NOT_HELD_FOR_INSOLVENCY)
    if nearby:
        return flag("insolvency", V, "fired", "amber", f"{len(nearby)} Gazette insolvency notice(s) reached only through a near link: a namesake or a name match, not the subject until confirmed",
                    citations=tuple(it["ref"] for it in nearby), sources_not_held=NOT_HELD_FOR_INSOLVENCY, scope="near")
    return flag("insolvency", V, "clear", "red", "no Gazette insolvency notice on the subject or on a company it has a row on",
                sources_held=(GAZETTE,), sources_not_held=NOT_HELD_FOR_INSOLVENCY)


def prohibition(report):
    conf = [it for it in items(report, ("gazette_prohibitions",), ("confirmed",))]
    nearby = [it for it in items(report, ("gazette_prohibitions",), ("near",))]
    if conf:
        return flag("prohibition", V, "fired", "red", f"{len(conf)} director prohibition notice(s) confirmed to the subject", citations=tuple(it["ref"] for it in conf))
    if nearby:
        return flag("prohibition", V, "fired", "amber", f"{len(nearby)} director prohibition notice(s) under a name near the subject's, or on a person on the subject; "
                                                        "not the subject until confirmed", citations=tuple(it["ref"] for it in nearby), scope="near")
    w = report.get("walk") or {}
    if report["subject"]["kind"] == "organisation":   # a company start: the clear covers its officers only as far as they were followed
        if "officers" not in (w.get("buckets") or []) or w.get("officers_omitted"):
            return flag("prohibition", V, "blocked", "red", "a company start: its officers were not all followed, so a prohibition on one may stand unread; "
                                                            "start a report from each officer listed")
        return flag("prohibition", V, "clear", "red", f"no director prohibition on the subject's officers' records ({w.get('officers_followed', 0)} followed one step) in the Gazette notices held",
                    sources_held=("New Zealand Gazette prohibition notices (pub.gazette_prohibitions)", "pub.groups: each officer's confirmed rows"))
    return flag("prohibition", V, "clear", "red", "no director prohibition confirmed or near the subject in the Gazette notices held",
                sources_held=("New Zealand Gazette prohibition notices (pub.gazette_prohibitions)",))


RULES = (insolvency, prohibition)
