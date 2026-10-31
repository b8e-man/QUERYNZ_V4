"""The cards' working share from the minute samples (1 November 2026). No database."""
import datetime as dt

from support.scheduler import saturation as S

T0 = dt.datetime(2026, 11, 1, 12, 0, tzinfo=dt.timezone.utc)


def m(n):
    return T0 + dt.timedelta(minutes=n)


def test_working_minutes_count_a_pause_takes_the_row_before_and_a_stretch_with_no_rows_is_idle():
    rows = [(m(0), True), (m(1), None), (m(2), True), (m(3), False), (m(4), True), (m(5), True)]
    r = S.share(rows + [(m(20), True)], m(0), m(21))
    # 0-3 working (the pause at 1 reads as working), 3-4 no work, 4-5 working, 5-20 no rows: 2.5 min, then idle, 20-21 working
    assert abs(r["share"] - (3 + 1 + 2.5 + 1) / 21) < 1e-9, r["share"]
    whys = [(round((b - a).total_seconds() / 60, 1), w) for a, b, w in r["idle"]]
    assert whys == [(1.0, "no work"), (12.5, "no measurement")]


def test_the_target_is_met_only_at_ninety_five_percent():
    rows = [(m(i), i % 20 != 0) for i in range(100)]
    r = S.share(rows, m(0), m(100))
    assert r["share"] == 0.95 and r["share"] >= S.TARGET
