"""Ruling 66 (Arthur, 21 October 13:00), for every political-donation
document: where a document's parts do not add to its printed total, a
difference below $100 is reconciled and the row carries an `issue` naming
the signed difference and the parts; a difference of $100 or more is not,
and is set aside as before. The published figure is the printed one; the
difference is never folded in. One threshold for the lane, here.

    cents(x) -> int                    to the cent, half up
    difference(parts, printed) -> int  cents, the parts less the printed total
    within(parts, printed) -> bool     the difference is below the tolerance ($100.00 itself is not)
    issue(parts, printed, what)        None when equal to the cent; else "+0.08: what was added, against what"
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


def joined(*issues):
    """Several issues on one row, `; ` between; None when there are none."""
    return "; ".join(i for i in issues if i) or None
