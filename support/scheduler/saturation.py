"""The cards' working time (Arthur, 1 November 2026: "I want them to be saturated 95% of the time").

The worker writes one row a minute to `card_samples` (cards.Manager.sample): whether any card on the box had work. This
reads them back. A minute is working when its row says so; a row with no answer (a standing server in one of its
pauses) takes the row before it; a stretch with no row at all (the worker stopped, the database down) is not working,
because nothing shows the cards had work. The target is TARGET of the clock.

    python -m support.scheduler saturation [--hours 24] [--box node2]
"""
from __future__ import annotations

import datetime as dt

TARGET = 0.95
#: a gap between two rows longer than this is time with no measurement, counted not working
GAP_S = 150.0


def share(rows: list, start: dt.datetime, end: dt.datetime) -> dict:
    """rows: [(at, working)] in time order. The working share of [start, end), and the idle stretches."""
    total = (end - start).total_seconds()
    if total <= 0:
        return {"share": None, "idle": []}
    busy, idle = 0.0, []
    prev_at, prev_w = start, None
    for at, w in rows + [(end, None)]:
        at = min(max(at, start), end)
        span = (at - prev_at).total_seconds()
        if span > 0:
            if prev_w and span <= GAP_S:
                busy += span
            elif prev_w and span > GAP_S:
                busy += GAP_S
                idle.append((prev_at + dt.timedelta(seconds=GAP_S), at, "no measurement"))
            else:
                idle.append((prev_at, at, "no work" if prev_w is False else "no measurement"))
        prev_at = at
        if w is not None:
            prev_w = w
    merged = []
    for a, b, why in idle:
        if merged and merged[-1][1] == a and merged[-1][2] == why:
            merged[-1] = (merged[-1][0], b, why)
        else:
            merged.append((a, b, why))
    return {"share": busy / total, "idle": merged}


def report(conn, schema: str, hours: float = 24.0, box: str = None, now: dt.datetime = None) -> dict:
    now = now or conn.execute("SELECT now()").fetchone()[0]
    start = now - dt.timedelta(hours=hours)
    q = f"SELECT at, working FROM {schema}.card_samples WHERE at >= %s" + (" AND box = %s" if box else "") + " ORDER BY at"
    rows = conn.execute(q, (start, box) if box else (start,)).fetchall()
    first = rows[0][0] if rows else now
    out = share(rows, start, now)
    out.update(hours=hours, samples=len(rows), measured_from=first, target=TARGET,
               ok=out["share"] is not None and out["share"] >= TARGET)
    return out


def lines(r: dict) -> list:
    if r["share"] is None:
        return ["cards: no measurement"]
    out = [f"cards working {r['share']:.1%} of the last {r['hours']:g} h (target {r['target']:.0%}; {r['samples']} samples, "
           f"measured from {r['measured_from']:%Y-%m-%d %H:%M})" + ("" if r["ok"] else " — UNDER TARGET")]
    for a, b, why in sorted(r["idle"], key=lambda x: x[0] - x[1])[:10]:
        mins = (b - a).total_seconds() / 60
        if mins >= 1:
            out.append(f"  idle {a:%m-%d %H:%M} to {b:%H:%M}, {mins:.0f} min: {why}")
    return out
