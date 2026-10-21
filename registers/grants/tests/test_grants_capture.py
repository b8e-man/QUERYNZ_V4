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

    def last(self, lst, url=None, publisher=None):
        hits = [d for d in self.docs if d["list"] == lst and (url is None or d["url"] == url)
                and (publisher is None or d["publisher"] == publisher)]
        return (hits[-1]["at"], hits[-1]["sha"]) if hits else None

    def add_doc(self, run_id, lst, publisher, url, sha, recognised, new):
        self.docs.append({"list": lst, "url": url, "sha": sha, "recognised": recognised, "publisher": publisher,
                          "at": dt.datetime.now(dt.timezone.utc)})

    def set_aside(self, run_id, item, stage, reason):
        self.asides.append((item, stage, reason))

    def frontier_add(self, host, urls, depth):
        for u in urls:
            self.frontier.setdefault(u, {"depth": depth, "asked": None})

    def frontier_next(self, host, limit, days):
        return [(u, f["depth"]) for u, f in self.frontier.items() if not f["asked"] and f["depth"] >= 0][:limit]

    def frontier_unasked(self, host, depth):
        return [u for u, f in self.frontier.items() if not f["asked"] and f["depth"] == depth]

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
        if not t.frontier.get(f"{CM}/a", {}).get("asked"):
            broken.append(f"a page that blocks ({status}) is marked asked, so the next run does not open on it")

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

    broken += society_properties(mod)

    t, clock = FakeTables(), Clock()
    run = mod.Run(t, land_fn=_land, fetch=lambda u, s: (200, b"", u, ""), clock=clock.now, sleep=clock.sleep,
                  now=lambda: dt.datetime(2026, 10, 22, 14, 0, tzinfo=capture.NZ), log=lambda *a: None)
    if run.run()["requests"]:
        broken.append("off-peak only unless asked")
    return broken


NH = "https://www.newhorizoncommunitytrust.co.nz"


def society_properties(mod) -> list:
    """The walk of a society's grants page, on an invented site under New Horizon's address."""
    broken = []
    start = f"{NH}/approved-grants"
    grants_page = (f'<html><a href="/wp-content/uploads/Grants-Approved-June-2024-May-2025.pdf">2024</a>'
                   f'<a href="/wp-content/uploads/Grants-Approved-April-2013-to-July-2013.pdf">2013</a>'
                   f'<a href="/wp-content/uploads/Annual-Report.pdf">Annual report</a>'
                   f'<a href="https://newhorizoncommunitytrust.co.nz/declined-grants/">Declined grants</a>'
                   f'<a href="/privacy-policy/">Privacy</a><a href="/contact/">Contact</a>'
                   f'<a href="https://cdn.example/grants-2025.pdf">grants 2025</a></html>').encode()
    declined = f'<html><a href="/wp-content/uploads/Grants-Declined-2025.pdf">Declined</a></html>'.encode()
    pages = {start: (200, grants_page, ""),
             f"{NH}/declined-grants": (301, b"", "https://newhorizoncommunitytrust.co.nz/declined-grants/"),
             "https://newhorizoncommunitytrust.co.nz/declined-grants/": (200, declined, ""),
             f"{NH}/privacy-policy": (200, b"<html>privacy</html>", ""),
             f"{NH}/wp-content/uploads/Grants-Approved-June-2024-May-2025.pdf": (200, b"%PDF-1.7 a", ""),
             "https://newhorizoncommunitytrust.co.nz/wp-content/uploads/Grants-Declined-2025.pdf":
                 (200, b"%PDF-1.7 b", "")}
    sites = {"new-horizon-community-trust": start}
    orig = mod.SOCIETY_SITES
    mod.SOCIETY_SITES = sites
    try:
        out, t, asked, clock = _run(mod, pages, ("society-file",))
        files = [d["url"] for d in t.docs if d["list"] == "society-file"]
        if sorted(files) != sorted([f"{NH}/wp-content/uploads/Grants-Approved-June-2024-May-2025.pdf",
                                    "https://newhorizoncommunitytrust.co.nz/wp-content/uploads/Grants-Declined-2025.pdf"]):
            broken.append("every grants file the grants pages link is landed as society-file, the society's own "
                          "www and bare hosts alike")
        if any("2013" in u or "Annual-Report" in u or "contact" in u for u in asked):
            broken.append("a file dated wholly before 2017, a file not about grants and a page not about grants are "
                          "never asked")
        if any("cdn.example" in u for u in asked):
            broken.append("a file on another host is never asked")
        lists = [d["list"] for d in t.docs]
        if "about" not in lists or lists.index("about") > lists.index("society-file"):
            broken.append("the society's privacy or terms page is landed before its first file")
        if any(d["publisher"] != "new-horizon-community-trust" for d in t.docs):
            broken.append("every document a society walk lands names the society as publisher")
        if not clock.waits or min(clock.waits) < 5.0:
            broken.append("a society walk is paced at least 5 s apart")
        for f in t.frontier.values():      # even with the frontier's marks lost, the landed file is not asked again
            f["asked"] = None
        fetch, asked2 = _site(pages)
        mod.Run(t, land_fn=_land, fetch=fetch, clock=clock.now, sleep=clock.sleep, now=lambda: NIGHT,
                lists=("society-file",), log=lambda *a: None).run()
        if any(u.endswith(".pdf") for u in asked2):
            broken.append("a society's file is landed once and never asked again")
    finally:
        mod.SOCIETY_SITES = orig
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
