"""The capture on a fake transport: the licence gate, the floor, off-peak, nothing fetched twice, a challenge
stops the run, a redirect is not followed; and the copy case from the store by hash. Nothing is fetched."""
import datetime as dt
import json

import support.fetchgate as fg
from registers.contract_disclosures import capture


def _pkg(name, licence, files):
    return json.dumps({"success": True, "result": {
        "name": name, "license_id": licence, "license_title": licence, "organization": {"title": "An agency"},
        "metadata_modified": "2023-08-18", "resources": files}}).encode()


ACC_FILE = {"id": "r1", "name": "Health Contract Data", "url": "https://catalogue.data.govt.nz/dataset/d/resource/r1/download",
            "format": "XLSX", "last_modified": "2023-08-18T06:53:43"}
MSD_FILE = {"id": "r2", "name": "MSD", "url": "https://catalogue.data.govt.nz/dataset/e/resource/r2/download",
            "format": "XLSX", "last_modified": "2021-06-16"}
XLSX = b"PK\x03\x04 a workbook"


class FakeTables:
    def __init__(self, held=(), asked=False, blocked=False):
        self.files, self.aside, self._held, self._asked, self._blocked = [], [], set(held), asked, blocked
        self.finished = None

    def begin(self, mode):
        return 1

    def finish(self, run_id, counts, stopped=""):
        self.finished = (counts, stopped)

    def add_file(self, run_id, **kw):
        self.files.append(kw)

    def set_aside(self, run_id, item, stage, reason):
        self.aside.append((item, stage, reason))

    def held(self, rid, modified):
        return (rid, modified) in self._held

    def asked_since(self, since):
        return self._asked

    def blocked_since(self, since):
        return self._blocked


class Ref:
    def __init__(self, data):
        self.sha256, self.size = "a" * 64, len(data)


def _run(answers, t=None, hour=23):
    t, clock, asked = t or FakeTables(), [0.0], []

    def opener(url, timeout):
        asked.append((url, clock[0]))
        st, body = answers.get(url, (404, b""))
        loc = "https://www.acc.co.nz/x" if st in fg.REDIRECT_STATUSES else ""
        return fg.Fetched(url, st, body, url, fg.looks_challenged(st, body), loc)
    out = capture.Refresh(t, land_fn=lambda data, **k: (Ref(data), True), opener=opener, clock=lambda: clock[0],
                          sleep=lambda s: clock.__setitem__(0, clock[0] + s),
                          now=lambda: dt.datetime(2026, 10, 22, hour, 5, tzinfo=capture.NZ)).run()
    return out, t, asked


ANSWERS = {
    capture.CATALOGUE + "health-contract-data": (200, _pkg("health-contract-data", "CC-BY-NZ-3.0", [ACC_FILE])),
    capture.CATALOGUE + "msd-and-myd-contracted-funding-f20": (200, _pkg("msd", "", [MSD_FILE])),
    ACC_FILE["url"]: (200, XLSX),
    MSD_FILE["url"]: (200, XLSX),
}


def test_an_open_licence_lands_its_file_and_a_package_with_none_lands_only_its_description():
    out, t, asked = _run(ANSWERS)
    urls = [u for u, _ in asked]
    assert urls == [capture.CATALOGUE + "health-contract-data", ACC_FILE["url"],
                    capture.CATALOGUE + "msd-and-myd-contracted-funding-f20"]
    assert MSD_FILE["url"] not in urls
    assert [f["role"] for f in t.files] == ["catalogue", "data", "catalogue"]
    assert out["not_open"] == 1 and any(s == "licence" for _, s, _ in t.aside)
    gaps = [b - a for (_, a), (_, b) in zip(asked, asked[1:])]
    assert all(g >= capture.FLOOR_S for g in gaps), gaps


def test_a_file_held_at_the_catalogue_s_date_is_not_asked_again():
    out, t, asked = _run(ANSWERS, FakeTables(held={("r1", "2023-08-18T06:53:43")}))
    assert ACC_FILE["url"] not in [u for u, _ in asked] and out["unchanged"] == 1


def test_nothing_is_asked_by_day_when_not_due_or_after_a_block():
    for t, hour in ((FakeTables(), 14), (FakeTables(asked=True), 23), (FakeTables(blocked=True), 23)):
        out, _, asked = _run(ANSWERS, t, hour)
        assert asked == [] and out["requests"] == 0, out["stopped"]


def test_a_challenge_stops_the_run_and_is_logged_as_hard_limit_6():
    a = dict(ANSWERS)
    a[ACC_FILE["url"]] = (200, b"<html><script src='/_Incapsula_Resource'></script></html>")
    out, t, asked = _run(a)
    assert out["stopped"].startswith("stopped:") and len(asked) == 2
    assert any("hard limit 6" in r for _, _, r in t.aside)


def test_a_redirect_is_not_followed_and_an_answer_that_is_not_the_file_is_not_landed():
    a = dict(ANSWERS)
    a[ACC_FILE["url"]] = (302, b"")
    out, t, asked = _run(a)
    assert [f["role"] for f in t.files] == ["catalogue", "catalogue"] and "not followed" in t.aside[0][2]
    a[ACC_FILE["url"]] = (200, b"<html>a page</html>")
    out, t, asked = _run(a)
    assert [f["role"] for f in t.files] == ["catalogue", "catalogue"] and t.aside[0][1] == "recognise"


def test_the_licence_gate_reads_the_catalogue_s_ids():
    assert capture.licence_open("CC-BY-NZ-3.0") and capture.licence_open("CC-BY-4.0")
    assert not capture.licence_open("") and not capture.licence_open("CC-BY-NC-4.0") and not capture.licence_open("other")


def test_the_copy_case_lands_only_bytes_that_are_their_pinned_hash():
    from support.docstore import sha256_bytes
    good, bad = b"good bytes", b"other bytes"
    pins = {"u1": (sha256_bytes(good), "health-contract-data", "data", {"id": "r1"}, "CC-BY-NZ-3.0"),
            "u2": (sha256_bytes(good), "health-contract-data", "catalogue", None, "CC-BY-NZ-3.0"),
            "u3": ("f" * 64, "health-contract-data", "data", {"id": "r9"}, "CC-BY-NZ-3.0")}
    store = {sha256_bytes(good): good, "f" * 64: bad}
    t = FakeTables()
    out = capture.copy_pinned(t, lambda data, **k: (Ref(data), True), lambda sha: store[sha], pins, log=lambda *_: None)
    assert out["landed"] == 2 and out["set_aside"] == 1 and [f["url"] for f in t.files] == ["u1", "u2"]
