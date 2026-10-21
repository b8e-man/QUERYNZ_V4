"""The capture's politeness and its stops, on a fake transport and fake
tables: nothing is fetched. `run_properties(mod)` lists the rules a capture
module breaks; the mutant check runs it on capture.py broken one way at a
time."""
import datetime as dt
import types

import pytest

from registers.grants import capture
from registers.grants.tests import fixtures

NIGHT = dt.datetime(2026, 10, 22, 23, 0, tzinfo=capture.NZ)
CM = "https://www.communitymatters.govt.nz"
FILE_URL = ("https://catalogue.data.govt.nz/dataset/b6b7f1cc-bfa4-4c7a-81e8-8a03f2983cae/resource/"
            "06d99ad0-47d6-4591-84c7-8872a4f77da9/download/class-4-grants-dataset-csv.csv")
FILE_PAGE_BODY = (f'<html><a href="{FILE_URL}">Download</a></html>').encode()
INTERSTITIAL = (b"<!DOCTYPE html><html><head><noscript><title>Pardon Our Interruption</title></noscript>"
                b"<script>window.reeseSkipExpirationCheck = true;</script></head></html>")


class FakeTables:
    def __init__(self):
        self.docs, self.asides, self.frontier, self.runs = [], [], {}, []

    def begin(self):
        self.runs.append({})
        return len(self.runs)

    def finish(self, run_id, counts, stopped):
        self.runs[-1] = {**counts, "stopped": stopped}

    def last(self, lst, url=None):
        hits = [d for d in self.docs if d["list"] == lst and (url is None or d["url"] == url)]
        return (hits[-1]["at"], hits[-1]["sha"]) if hits else None

    def add_doc(self, run_id, lst, publisher, url, sha, recognised, new):
        self.docs.append({"list": lst, "url": url, "sha": sha, "recognised": recognised,
                          "at": dt.datetime.now(dt.timezone.utc)})

    def set_aside(self, run_id, item, stage, reason):
        self.asides.append((item, stage, reason))

    def frontier_add(self, host, urls, depth):
        for u in urls:
            self.frontier.setdefault(u, {"depth": depth, "asked": None})

    def frontier_next(self, host, limit, days):
        return [(u, f["depth"]) for u, f in self.frontier.items() if not f["asked"]][:limit]

    def frontier_asked(self, host, url, status):
        self.frontier[url]["asked"] = True
        self.frontier[url]["status"] = status


class Clock:
    def __init__(self):
        self.t = 0.0
        self.waits = []

    def now(self):
        return self.t

    def sleep(self, s):
        self.waits.append(s)
        self.t += s


def _site(pages):
    """A fake transport: url → (status, body, location); every ask recorded."""
    asked = []

    def fetch(url, timeout):
        asked.append(url)
        status, body, location = pages.get(url, (404, b"", ""))
        return status, body, url, location
    return fetch, asked


def _land(data, *, name, source, name_kind):
    import hashlib
    return types.SimpleNamespace(sha256=hashlib.sha256(data).hexdigest()), True


def _run(mod, pages, lists, **kw):
    t, clock = FakeTables(), Clock()
    fetch, asked = _site(pages)
    run = mod.Run(t, land_fn=_land, fetch=fetch, clock=clock.now, sleep=clock.sleep, now=lambda: NIGHT,
                  lists=lists, log=lambda *a: None, **kw)
    return run.run(), t, asked, clock


@pytest.fixture(autouse=True)
def _no_gate(monkeypatch):
    """The gate's decision without its files: every host permitted at a 5 s floor."""
    monkeypatch.setattr(capture.fg, "check", lambda url, positions_dir=None: types.SimpleNamespace(
        host=capture.fg.host_of(url), floor=5.0))


def _record(name):
    return fixtures.lottery_page(heading=f"2025/26 round one Lottery {name} record of grants")


def run_properties(mod) -> list:
    broken = []
    home = (f'<html><a href="/a">a</a><a href="{CM}/b/">b</a><a href="https://elsewhere.example/x">x</a>'
            f'<a href="/__data/assets/file.pdf">f</a><a href="/c#top">c</a><a href="/ask-us/view/1">q</a></html>').encode()
    pages = {f"{CM}/": (200, home, ""), f"{CM}/a": (200, _record("Alpha"), ""),
             f"{CM}/b": (301, b"", f"{CM}/b-moved"), f"{CM}/b-moved": (200, b"<html>nothing</html>", ""),
             f"{CM}/c": (301, b"", "https://elsewhere.example/c")}
    out, t, asked, clock = _run(mod, pages, ("lottery-page",))
    if any("elsewhere.example" in u for u in asked):
        broken.append("another host is never asked, by a link or a redirect")
    if any("__data" in u or "ask-us" in u for u in asked):
        broken.append("files and the ask-us pages are never asked by the walk")
    if f"{CM}/b-moved" not in asked:
        broken.append("a redirect on the same host is followed")
    if out["records_of_grants"] != 1 or [d["recognised"] for d in t.docs].count("lottery-record-of-grants-page") != 1:
        broken.append("the walk lands every page and counts the records of grants")
    if len(asked) != len(set(asked)):
        broken.append("each page is asked once in a run")
    if not clock.waits or min(w for w in clock.waits) < 5.0 or len(clock.waits) < len(asked) - 1:
        broken.append("one request at a time, at least 5 s apart")

    for status, body in ((403, b""), (429, b""), (200, INTERSTITIAL)):
        out, t, asked, _ = _run(mod, {f"{CM}/": (200, home, ""), f"{CM}/a": (status, body, ""),
                                      f"{CM}/b": (200, _record("Beta"), "")}, ("lottery-page",))
        if len(asked) != 2 or f"{CM}/b" in asked or not out["blocked_hosts"]:
            broken.append(f"a {status} {'challenge ' if body else ''}stops the host for the run")
        if any(d["url"] == f"{CM}/a" for d in t.docs):
            broken.append("a challenged page is never landed")

    out, t, asked, _ = _run(mod, {f"{CM}/": (500, b"", ""), f"{CM}/x": (500, b"", "")}, ("lottery-page",))
    if out["set_aside"] != 1 or out["blocked_hosts"]:
        broken.append("a server's own error is a failed read, set aside, and the host is not blocked")

    page = "https://catalogue.data.govt.nz/dataset/class-4-grants-data"
    site = {page: (200, FILE_PAGE_BODY, ""), FILE_URL: (200, fixtures.dia_csv(), "")}
    out, t, asked, _ = _run(mod, site, ("dia-file",))
    if asked != [page, FILE_URL] or [d["list"] for d in t.docs] != ["dia-file-page", "dia-file"]:
        broken.append("the file's page, then the file it links")
    for d in t.docs:
        d["at"] -= dt.timedelta(days=40)
    fetch, asked2 = _site(site)
    clock = Clock()
    mod.Run(t, land_fn=_land, fetch=fetch, clock=clock.now, sleep=clock.sleep, now=lambda: NIGHT,
            lists=("dia-file",), log=lambda *a: None).run()
    if asked2 != [page]:
        broken.append("the file is not asked again while its page is unchanged")
    fetch, asked3 = _site(site)
    mod.Run(t, land_fn=_land, fetch=fetch, clock=clock.now, sleep=clock.sleep, now=lambda: NIGHT,
            lists=("dia-file",), log=lambda *a: None).run()
    if asked3:
        broken.append("the file's page is asked at most every 30 days")

    out, t, asked, _ = _run(mod, {page: (200, INTERSTITIAL, "")}, ("dia-file", "lottery-page"))
    if t.docs or out["blocked_hosts"] != ["catalogue.data.govt.nz"]:
        broken.append("the catalogue's interstitial is a challenge: nothing landed")

    t, clock = FakeTables(), Clock()
    run = mod.Run(t, land_fn=_land, fetch=lambda u, s: (200, b"", u, ""), clock=clock.now, sleep=clock.sleep,
                  now=lambda: dt.datetime(2026, 10, 22, 14, 0, tzinfo=capture.NZ), log=lambda *a: None)
    if run.run()["requests"]:
        broken.append("off-peak only unless asked")
    return broken


def test_the_capture_as_written_holds_every_property():
    assert run_properties(capture) == []


def test_a_challenge_by_status_or_by_page():
    assert capture.challenged(200, INTERSTITIAL) and capture.challenged(403, b"")
    assert not capture.challenged(200, fixtures.lottery_page())


def test_the_walk_keeps_one_address_per_page():
    assert capture.canonical("https://WWW.Example.org/a/b/#x") == "https://www.example.org/a/b"
    assert capture.canonical("https://www.example.org") == "https://www.example.org/"


def test_a_blocked_host_red_only_when_nothing_landed():
    assert capture.outcome({"blocked_hosts": ["h"], "landed": 0, "already_held": 0, "stopped": "x"})[0] is False
    assert capture.outcome({"blocked_hosts": ["h"], "landed": 1, "already_held": 0, "stopped": "x"})[0] is True
