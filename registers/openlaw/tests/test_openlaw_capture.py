"""The capture, on a fake interface: held without OpenLaw's authorisation
(nothing asked for); once authorised, polite (one at a time, the floor
between answers, off-peak), newest first, resumable by offset, the sample
stopped at its target, a 403, 429 or 5xx or GraphQL errors stopping the
night, the head pass stopping at a page it already holds, the key never in a
name; and the interface's own figure found by probing offsets. Nothing is
fetched."""
import datetime as dt
import os
from types import SimpleNamespace

import pytest

from registers.openlaw import capture as C
from registers.openlaw.tests import fixture as F

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NIGHT = dt.datetime(2026, 10, 21, 23, 0, tzinfo=dt.timezone(dt.timedelta(hours=13)))
DAY = NIGHT.replace(hour=14)


class Tables:
    def __init__(self):
        self.passes, self.pages, self.asides, self.n = [], [], [], 0

    def open_pass(self):
        o = [p for p in self.passes if not p.get("done")]
        return o[-1] if o else None

    def last_done(self, mode):
        d = [p["done"] for p in self.passes if p.get("done") and p["mode"] == mode]
        return max(d) if d else None

    def held_ids(self):
        return {i for p in self.pages for i in p["ids"]}

    def begin(self, mode, target=None, probed=None):
        self.n += 1
        p = {"pass_id": self.n, "mode": mode, "next_offset": 0, "pages": 0, "cases_landed": 0, "target": target,
             "probed": probed}
        self.passes.append(p)
        return p

    def add_page(self, p, offset, url, sha, ids, new):
        p["pages"] += 1
        p["cases_landed"] += len(ids)
        p["next_offset"] = offset + C.PAGE
        self.pages.append({"pass": p["pass_id"], "offset": offset, "url": url, "ids": ids})

    def finish(self, p):
        p["done"] = NIGHT

    def set_aside(self, pass_id, item, stage, reason):
        self.asides.append((item, stage, reason))


class Interface:
    """`total` cases, ids c00000…, newest first; `fail_at`: request number → status or 'errors'."""

    def __init__(self, total, fail_at=None):
        self.total, self.fail_at, self.queries = total, fail_at or {}, []

    def __call__(self, query):
        self.queries.append(query)
        n = len(self.queries)
        if n in self.fail_at:
            f = self.fail_at[n]
            if f == "errors":
                return SimpleNamespace(status=200, body=b'{"errors": [{"message": "x"}]}', blocked="", final_url=C.URL)
            return SimpleNamespace(status=f, body=b"", blocked=f"HTTP {f}: a block", final_url=C.URL)
        first = int(query.split("first: ")[1].split(",")[0])
        off = int(query.split("offset: ")[1].split(",")[0])
        recs = [F.record(f"c{i:05d}") for i in range(off, min(off + first, self.total))]
        if "{ id }" in query:
            recs = [{"id": r["id"]} for r in recs]
        return SimpleNamespace(status=200, body=F.page(*recs), blocked="", final_url=C.URL)


class Clock:
    def __init__(self):
        self.t, self.slept = 0.0, []

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.slept.append(s)
        self.t += s


def _run(api, tables=None, authorised="2026-11-01, a letter", now=NIGHT, **kw):
    tables = tables or Tables()
    clock = Clock()
    landed = []

    def land(body, *, name, source, name_kind, content_type):
        landed.append(name)
        import hashlib
        return SimpleNamespace(sha256=hashlib.sha256(body).hexdigest()), True
    docs = lambda url: SimpleNamespace(status=200, body=b"%PDF terms", blocked="", final_url=url)
    r = C.Run(tables, land_fn=land, post=api, get=docs, authorised=lambda: authorised, clock=clock, sleep=clock.sleep,
              now_local=lambda: now, log=lambda *a: None, **kw)
    return r, tables, clock, landed


def test_held_without_authorisation_and_nothing_is_asked_for():
    api = Interface(100)
    r, t, _, landed = _run(api, authorised=None)
    with pytest.raises(C.Held):
        r.run()
    assert api.queries == [] and landed == [] and t.passes == []


def test_the_position_on_file_records_no_authorisation_so_the_lane_is_held_today():
    """Pinned: when OpenLaw authorises, the position gains its `authorised:` line and this test is changed with it."""
    assert C.authorisation(os.path.join(LANE, "position")) is None


def test_authorisation_is_read_from_the_position_covering_the_host(tmp_path):
    (tmp_path / "openlaw-case-law.md").write_text("# x\n\nhosts: openlaw.nz\n\nauthorised: 2026-11-01, OpenLaw's email\n")
    assert C.authorisation(str(tmp_path)) == "2026-11-01, OpenLaw's email"
    (tmp_path / "openlaw-case-law.md").write_text("# x\n\nhosts: example.org\n\nauthorised: 2026-11-01\n")
    assert C.authorisation(str(tmp_path)) is None


def test_the_first_night_lands_the_terms_probes_the_figure_and_takes_the_sample_newest_first(monkeypatch):
    monkeypatch.setattr(C, "SAMPLE", 30)
    api = Interface(95)
    r, t, clock, landed = _run(api)
    out = r.run()
    assert landed[:3] == list(C.DOCS.values())
    p = t.passes[0]
    assert (p["mode"], p["probed"], p["cases_landed"], p.get("done")) == ("sample", 95, 30, NIGHT)
    assert [pg["offset"] for pg in t.pages] == [0, 10, 20]
    assert all("CASE_DATE_DESC" in q for q in api.queries if "{ id }" not in q)
    assert out["stopped"] == "" and out["cases"] == 30


def test_one_request_at_a_time_with_the_floor_between_answers():
    api = Interface(25)
    r, _, clock, _ = _run(api, mode="full")
    r.run()
    assert len(clock.slept) == r.counts["requests"] - 1 and all(s >= C.FLOOR_S for s in clock.slept)
    assert C.FLOOR_S >= 2


def test_a_full_pass_ends_on_a_short_page_and_is_finished():
    api = Interface(25)
    r, t, _, _ = _run(api, mode="full")
    r.run()
    assert [pg["offset"] for pg in t.pages] == [0, 10, 20] and t.passes[0].get("done")
    assert len(t.held_ids()) == 25


@pytest.mark.parametrize("fail", [403, 429, 500, 503, "errors"])
def test_a_block_a_throttle_a_server_error_or_graphql_errors_stops_the_night(fail):
    api = Interface(100, fail_at={20: fail})      # past the probe's requests: on a page
    r, t, _, _ = _run(api, mode="full")
    out = r.run()
    assert out["stopped"].startswith("stopped:") and len(api.queries) == 20
    assert t.asides and not t.passes[0].get("done")


def test_a_stopped_pass_resumes_from_its_offset_next_night():
    api = Interface(100, fail_at={20: 429})
    r, t, _, _ = _run(api, mode="full")
    r.run()
    done_offsets = [pg["offset"] for pg in t.pages]
    api2 = Interface(100)
    r2, _, _, _ = _run(api2, tables=t)
    r2.run()
    later = [pg["offset"] for pg in t.pages][len(done_offsets):]
    assert later[0] == done_offsets[-1] + 10 and t.passes[0].get("done") and len(t.passes) == 1
    assert not any("{ id }" in q for q in api2.queries)        # a resumed pass does not probe again


def test_off_peak_only_unless_by_hand():
    api = Interface(100)
    r, t, _, _ = _run(api, now=DAY, mode="full")
    out = r.run()
    assert api.queries == [] and out["stopped"] == "off-peak is over"
    r, t, _, _ = _run(Interface(5), now=DAY, mode="full", anytime=True)
    assert r.run()["cases"] == 5


def test_the_head_pass_stops_at_a_page_it_already_holds():
    t = Tables()
    _run(Interface(40), tables=t, mode="full")[0].run()
    api = Interface(40)
    r, _, _, _ = _run(api, tables=t, mode="head")
    r.run()
    assert len(api.queries) == 1 and t.passes[-1]["mode"] == "head" and t.passes[-1].get("done")


def test_the_key_is_never_in_a_name_a_query_or_a_url():
    assert "apikey" not in C.page_name(0).lower() and "apikey" not in C.cases_query(0).lower()
    assert C.KEY_HEADER == "x-apikey" and C.URL == "https://api.openlaw.nz/graphql"


@pytest.mark.parametrize("total", [0, 1, 2, 9, 10, 32767, 32768, 32769, 46545, 70000, 200001])
def test_the_figure_is_found_by_probing_offsets(total):
    asked = []

    def ask(off):
        asked.append(off)
        return off < total
    n, requests = C.probe_total(ask)
    assert n == total and requests == len(asked) and requests <= 40


def test_a_non_page_answer_is_named():
    assert C.answer(b'{"errors": [1, 2]}') == (None, "the interface answered with 2 error(s)")
    assert C.answer(F.page(F.clean()))[0][0]["id"] == F.clean()["id"]
