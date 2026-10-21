"""Against the real interface, marked slow (the network): the reading's shape
on one page of the newest three cases, read in memory and kept nowhere
(using the interface is within its licence; a permanent copy is not, API
terms 3.6(a)), and the interface's own figure probed by offset. Every
assertion is a count or a shape; nothing is printed, landed or written."""
import os

import pytest

from support import db, rowcontract
from registers.openlaw import capture as C
from registers.openlaw import read

pytestmark = pytest.mark.slow
POSITION = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "position")


@pytest.fixture(autouse=True)
def _key_and_position(monkeypatch):
    if not os.path.exists(os.path.join(db.CRED_DIR, C.KEY_FILE)):
        pytest.skip("no OpenLaw key in the credential folder")
    import support.fetchgate as fg
    if not fg.position_for(C.HOST):
        monkeypatch.setattr(C, "POSITIONS", POSITION)      # until the integrator moves the page


def test_the_newest_page_read_in_memory_has_the_profiles_shape_and_reads_whole():
    f = C.gated(C.cases_query(0, first=3))
    assert f.status == 200 and not f.blocked
    cases, why = read.recognise(f.body)
    assert cases is not None, why
    assert len(cases) == 3
    prof = read.profile()
    typed = [read.read_case(c, "0" * 64, i, prof) for i, c in enumerate(cases)]
    assert all(rows is not None for rows, _ in typed), [w for _, w in typed]
    dates = [rows["case"]["decided_on"] for rows, _ in typed]
    assert all(dates) and dates == sorted(dates, reverse=True)           # newest first
    assert sum(1 for rows, _ in typed if rows["case"]["citation"]) >= 1
    assert all(rows["case"]["court"] for rows, _ in typed)
    for rows, _ in typed:
        for r in [rows["case"]] + rows["parties"] + rows["citations"] + rows["statutes"]:
            assert rowcontract.validate({**r, "loaded_at": "2026-10-21T00:00:00+13:00"}) == []
    del f, cases, typed


def test_the_interface_holds_about_the_figure_it_states():
    r = C.Run(None, land_fn=None, anytime=True, log=lambda *a: None)
    total = r.probe()
    assert 40000 <= total <= 80000, total          # "47k cases" on its home page, 21 October 2026
