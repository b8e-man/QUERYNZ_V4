"""The capture: names classified as the publisher names its files; the
catalogue's own list read from the description held; and the quarterly
refresh against a fake host: a block stops the run after one catch-log line
and nothing more is asked, the historic files are never asked, nothing is
asked twice in a quarter, a 404 on the catalogue's upper-case name is
followed by one request for the lower-case name, the rest between requests
is kept, and nothing is asked outside off-peak. No network."""
import datetime as dt
import os

import pytest

import support.fetchgate as fg
from support.docstore import describe
from registers.tenders import capture
from registers.tenders.tests import fixtures

CATALOGUE_SHA = capture.PROBED["sha256"]
BASE = "https://www.mbie.govt.nz/assets/Data-Files/NZGPP-GETS-Open-Data/"
PACKAGE = (b'{"success": true, "result": {"license_id": "CC-BY-NZ-3.0", "resources": ['
           + b", ".join(b'{"name": "%s", "format": "CSV", "url": "%s%s"}' % (n.encode(), BASE.encode(), f.encode())
                        for n, f in (("GETS award notices", "GETS-award-notices.csv"),
                                     ("GETS supplier data", "GETS-supplier-data.csv"),
                                     ("GETS region by tender", "GETS-region-by-tender.csv"),
                                     ("GETS product categories", "GETS-product-categories.csv"),
                                     ("GETS award notices historic", "gets-award-notices-historic.csv")))
           + b"]}}")


class FakeTables:
    def __init__(self, landed=(), blocked=None):
        self.files, self.asides, self.runs, self.landed, self.blocked = [], [], {}, dict(landed), blocked

    def begin(self, mode):
        rid = len(self.runs) + 1
        self.runs[rid] = {"mode": mode}
        return rid

    def finish(self, run_id, counts, stopped=""):
        self.runs[run_id].update(counts=dict(counts), stopped=stopped)

    def add_file(self, run_id, name, url, ref, new, how, held_from, acquired_at):
        self.files.append({"name": name, "url": url, "sha": ref.sha256, "classified": capture.classify(name if how == "old-raw" else url)})

    def set_aside(self, run_id, item, stage, reason):
        self.asides.append((item, stage, reason))

    def acquired_since(self, set_name, since):
        return set_name in self.landed and self.landed[set_name] >= since

    def blocked_since(self, since):
        return self.blocked is not None and self.blocked >= since


class Host:
    """A fake host: url → (status, body); every request recorded with the clock."""

    def __init__(self, answers, clock):
        self.answers, self.asked, self.clock = answers, [], clock

    def __call__(self, url, timeout):
        self.asked.append((url, self.clock.t))
        status, body = self.answers.get(url, (404, b""))
        return fg.Fetched(url, status, body, url, fg.looks_challenged(status, body))


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


def land_fn(data, *, name, name_kind, fetched_at=None, content_type=""):
    return describe(data, name, content_type, "tenders"), True


NIGHT = dt.datetime(2026, 10, 20, 23, 0, tzinfo=capture.NZ)
CSV = fixtures.files()[("regions", "current")][1]


def refresh(mod, answers, landed=(), when=NIGHT, anytime=False, blocked=None):
    clock = Clock()
    host = Host(answers, clock)
    t = FakeTables(landed, blocked)
    out = mod.Refresh(t, land_fn=land_fn, opener=host, clock=clock, sleep=clock.sleep, now=lambda: when,
                      anytime=anytime, log=lambda *_: None).run()
    return out, t, host


def blocked_run_properties(mod) -> list:
    """What the refresh must do, as a list of what broke; the mutant check
    needs each broken copy of the capture to make this say something."""
    out = []
    o, t, host = refresh(mod, {capture.CATALOGUE: (200, PACKAGE), BASE + "GETS-award-notices.csv": (403, b""),
                               BASE + "gets-award-notices.csv": (200, CSV)})
    asked = [u for u, _ in host.asked]
    if asked != [capture.CATALOGUE, BASE + "GETS-award-notices.csv"]:
        out.append(f"a blocked run asked {len(asked)} times")
    if not o["stopped"].startswith("stopped:") or "403" not in o["stopped"]:
        out.append(f"a block did not stop the run: {o['stopped']!r}")
    o, t, host = refresh(mod, {capture.CATALOGUE: (200, PACKAGE), **{BASE + f: (200, CSV) for f in (
        "GETS-award-notices.csv", "GETS-supplier-data.csv", "GETS-region-by-tender.csv", "GETS-product-categories.csv")}})
    if any("historic" in u for u, _ in host.asked):
        out.append("the historic file was asked for")
    gaps = [b - a for (_, a), (_, b) in zip(host.asked, host.asked[1:])]
    if any(g < capture.FLOOR_S for g in gaps):
        out.append(f"requests {min(gaps)} s apart")
    return out


def test_a_refresh_holds_every_property():
    assert blocked_run_properties(capture) == []


def test_names_are_classified_as_the_publisher_names_its_files():
    assert capture.classify(BASE + "GETS-award-notices.csv") == ("data", "notices", "current")
    assert capture.classify("gets-supplier-data-historic.csv") == ("data", "suppliers", "historic")
    assert capture.classify(BASE + "gets-region-by-tender.csv") == ("data", "regions", "current")
    assert capture.classify("GETS-product-categories-historic.csv") == ("data", "categories", "historic")
    assert capture.classify("schema-and-documentation.xlsx") == ("dictionary", None, None)
    assert capture.classify(BASE + "GETS-something-else.csv") == (None, None, None)
    assert capture.lower_name(BASE + "GETS-award-notices.csv") == BASE + "gets-award-notices.csv"


def test_a_challenge_page_answered_200_stops_the_run_and_lands_nothing():
    o, t, host = refresh(capture, {capture.CATALOGUE: (200, PACKAGE),
                                   BASE + "GETS-award-notices.csv": (200, fixtures.CHALLENGE)})
    assert o["stopped"].startswith("stopped:") and "challenge" in o["stopped"]
    assert [f["classified"][1] for f in t.files] == [None]          # the catalogue only
    assert len(host.asked) == 2 and t.asides[-1][1] == "fetch"


def test_a_404_on_the_upper_case_name_asks_once_for_the_lower_case_name():
    o, t, host = refresh(capture, {capture.CATALOGUE: (200, PACKAGE), BASE + "gets-award-notices.csv": (200, CSV)})
    asked = [u for u, _ in host.asked]
    assert asked[:3] == [capture.CATALOGUE, BASE + "GETS-award-notices.csv", BASE + "gets-award-notices.csv"]
    assert [f["name"] for f in t.files][1] == "gets-award-notices.csv"
    assert ("data", "notices", "current") in [f["classified"] for f in t.files]


def test_a_set_acquired_this_quarter_is_not_asked_for_again():
    landed = {"notices": NIGHT - dt.timedelta(days=10)}
    o, t, host = refresh(capture, {capture.CATALOGUE: (200, PACKAGE)}, landed=landed)
    assert BASE + "GETS-award-notices.csv" not in [u for u, _ in host.asked]
    assert o["skipped"] == 1


def test_nothing_is_asked_when_nothing_is_due_or_the_host_blocked_us_this_week():
    fresh = {s: NIGHT - dt.timedelta(days=30) for s in capture.SETS.values()}
    o, t, host = refresh(capture, {capture.CATALOGUE: (200, PACKAGE)}, landed=fresh)
    assert host.asked == [] and o["stopped"].startswith("not due")
    o, t, host = refresh(capture, {capture.CATALOGUE: (200, PACKAGE)}, blocked=NIGHT - dt.timedelta(days=2))
    assert host.asked == [] and o["stopped"].startswith("resting")
    o, t, host = refresh(capture, {capture.CATALOGUE: (200, PACKAGE)}, blocked=NIGHT - dt.timedelta(days=8))
    assert host.asked[0][0] == capture.CATALOGUE


def test_nothing_is_asked_outside_off_peak():
    o, t, host = refresh(capture, {}, when=NIGHT.replace(hour=14))
    assert host.asked == [] and o["stopped"].startswith("not off-peak")


def test_a_body_that_is_not_a_csv_is_set_aside_not_landed():
    o, t, host = refresh(capture, {capture.CATALOGUE: (200, PACKAGE), BASE + "GETS-award-notices.csv": (200, b"{}")})
    assert ("data", "notices", "current") not in [f["classified"] for f in t.files]
    assert any(a[1] == "recognise" for a in t.asides)


def test_the_copy_lands_only_the_pinned_bytes(tmp_path):
    (tmp_path / "gets-region-by-tender.csv").write_bytes(CSV)
    (tmp_path / "gets-award-notices.csv").write_bytes(b"other bytes")
    pins = {"gets-region-by-tender.csv": describe(CSV).sha256, "gets-award-notices.csv": "0" * 64,
            "gets-supplier-data.csv": "1" * 64}
    t = FakeTables()
    out = capture.copy_old(t, land_fn, old_dir=str(tmp_path), pins=pins, probed=None, log=lambda *_: None)
    assert [f["classified"] for f in t.files] == [("data", "regions", "current")]
    assert out["set_aside"] == 2 and {a[1] for a in t.asides} == {"copy"}


def _store():
    from support.docstore.landing import path_for
    if not os.path.exists(path_for(CATALOGUE_SHA)):
        pytest.skip("the document store is not on this box")
    from support.docstore.landing import read_bytes
    return read_bytes


def test_the_catalogue_held_lists_the_four_current_files_under_cc_by_3_nz():
    """Real data: the catalogue's description landed on 21 October 2026."""
    body = _store()(CATALOGUE_SHA)
    listed = capture.listed_files(body)
    assert sorted(capture.classify(u)[1:] for _, u in listed) == [
        ("categories", "current"), ("notices", "current"), ("regions", "current"), ("suppliers", "current")]
    assert capture.licence_of(body)["id"] == "CC-BY-NZ-3.0"


def test_every_pinned_old_file_is_held_by_its_hash():
    read_bytes = _store()
    from support.docstore import sha256_bytes
    for name, sha in capture.OLD_RAWS.items():
        assert sha256_bytes(read_bytes(sha)) == sha, name
