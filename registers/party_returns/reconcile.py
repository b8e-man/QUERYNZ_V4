"""The tolerance a return's parts are held to against its printed total.

Ruling 66 (Arthur, 21 October 13:00), for every political-donation
document: where the parts do not add to the printed total, a difference
below $100 is reconciled and the row carries an `issue` naming the signed
difference (parts minus printed) and which parts; a difference of $100 or
more is unreconciled and set aside as before. The published total is the
printed one; the difference is never folded into it. Exactly $100 is set
aside.

    difference(parts, printed)   cents, parts minus printed
    within(parts, printed)       the difference is below the tolerance
    issue(parts, printed, what)  None when equal to the cent, else "+12.34: what"
"""
from decimal import ROUND_HALF_UP, Decimal

RECONCILE_TOLERANCE_CENTS = 10000


def cents(x) -> int:
    return int((Decimal(str(x)) * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def difference(parts, printed) -> int:
    return cents(parts) - cents(printed)


def within(parts, printed) -> bool:
    return abs(difference(parts, printed)) < RECONCILE_TOLERANCE_CENTS


def issue(parts, printed, what: str):
    d = difference(parts, printed)
    return None if d == 0 else f"{d / 100:+,.2f}: {what}"


def join(issues) -> str:
    """Several issues on one row, in order, once each; None when there are none."""
    out = list(dict.fromkeys(i for i in issues if i))
    return "; ".join(out) or None
