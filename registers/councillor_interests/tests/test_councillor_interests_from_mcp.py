"""The capture answered from the ingest MCP's copy (`--from-mcp`, 9 November 2026): the crawl is the MCP
provider's, so the walk asks neither the web nor the gate, runs at any hour, an address the MCP lacks is a failed
read with no host held for it, a challenge copy is a block, and (ruling 159) a council whose host the lane or the
gate holds is read from the copy, its hold standing for the boxes' own walk. Every page here is invented; nothing
is fetched."""
import datetime as dt
import hashlib
import os
import tomllib
import types

import support.fetchgate as fg
from registers.councillor_interests import capture
from registers.councillor_interests.tests.test_councillor_interests import LANDING, FakeTables

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
REGS = {"Invented District Council": ("www.invented.govt.nz", "https://www.invented.govt.nz/council/", None),
        "Other District Council": ("www.other.govt.nz", "https://www.other.govt.nz/council/", None)}
DOC = "https://www.invented.govt.nz/files/register-of-pecuniary-interests-2026.pdf"


class Files:
    """mcpsource.files as the replay asks it: each address the copy holds answers with itself as its hash."""

    def __init__(self, held, corpus="estate-councillor_interests"):
        self.held, self.corpus = held, corpus

    def execute(self, sql, params):
        url, corpora = params
        ok = self.corpus in corpora and url in self.held
        return types.SimpleNamespace(fetchone=lambda: (url,) if ok else None)


def _run(held, monkeypatch, bodies=None, t=None, corpus="estate-councillor_interests"):
    monkeypatch.setattr(fg, "open_url", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked the web")))
    monkeypatch.setattr(fg, "refused_by", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked the gate")))
    bodies = bodies or {}
    t, store = t or FakeTables(), {}

    def land_fn(data, *, name, content_type):
        sha = hashlib.sha256(data).hexdigest()
        new = sha not in store
        store[sha] = data
        return types.SimpleNamespace(sha256=sha), new

    page = lambda u: bodies.get(u, b"%PDF-1.4 x" if u.endswith(".pdf") else LANDING)
    r = capture.Run(t, land_fn=land_fn, registers=REGS, now=lambda: dt.datetime(2026, 11, 10, 14, 0, tzinfo=capture.NZ),
                    **capture.from_mcp(Files(held, corpus), read_bytes=page))
    return r.run(), t


def test_the_walk_is_answered_from_the_mcp_by_day_and_asks_neither_web_nor_gate(monkeypatch):
    out, t = _run({REGS["Invented District Council"][1], DOC}, monkeypatch)
    assert out["stopped"] == "" and (out["pages"], out["documents"]) == (1, 1)
    assert out["failed"] == 1 and not t.held                       # the other council's page: not held, no hold


def test_another_corpus_s_copy_does_not_answer(monkeypatch):
    out, t = _run({REGS["Invented District Council"][1], DOC}, monkeypatch, corpus="estate-fma")
    assert (out["pages"], out["documents"]) == (0, 0)


def test_a_copy_that_is_a_challenge_page_is_a_block(monkeypatch):
    url = REGS["Invented District Council"][1]
    out, t = _run({url}, monkeypatch, bodies={url: b"<html><head><title>Just a moment...</title></head></html>"})
    assert out["pages"] == 0 and "www.invented.govt.nz" in t.held


def test_a_held_council_s_copy_is_taken_and_its_hold_stands(monkeypatch):
    """Ruling 159: the provider's copy of a council the boxes were blocked from is taken; the hold is not cleared."""
    t = FakeTables()
    t.hold("www.invented.govt.nz", "HTTP 403: a block")
    out, t = _run({REGS["Invented District Council"][1], DOC}, monkeypatch, t=t)
    assert (out["pages"], out["documents"]) == (1, 1)
    assert [i["url"] for i in t.items if i["sha"]] == [REGS["Invented District Council"][1], DOC]
    assert t.held == {"www.invented.govt.nz": "HTTP 403: a block"} and out["held_hosts"] == 0


def test_the_three_councils_held_since_october_are_read_from_the_copy(monkeypatch):
    """Matamata-Piako, Dunedin and Gisborne as REGISTERS has them, their hosts held as the live record holds them
    (pages invented): Matamata-Piako's landing page and the document it links, and Dunedin's register page, are
    taken; Gisborne has no address in REGISTERS, so nothing is asked of it."""
    names = ("Matamata-Piako District Council", "Dunedin City Council", "Gisborne District Council")
    regs = {n: capture.REGISTERS[n] for n in names}
    mpdc, dunedin = regs[names[0]][1], regs[names[1]][1]
    doc = "https://www.mpdc.govt.nz/filelink/fileman-files/OurCouncil/Invented%20Declaration%20of%20Interest.pdf"
    bodies = {mpdc: f'<a href="{doc}">Declaration of interest</a>'.encode(), dunedin: b"<p>Register of members</p>"}
    t = FakeTables()
    for n in names:
        t.hold(regs[n][0], "survey 22 October 2026: HTTP 403: a block or a challenge")
    monkeypatch.setattr(capture, "REGISTERS", regs)
    monkeypatch.setattr(fg, "open_url", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked the web")))
    monkeypatch.setattr(fg, "refused_by", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked the gate")))
    page = lambda u: bodies.get(u, b"%PDF-1.4 x")
    r = capture.Run(t, land_fn=lambda data, **k: (types.SimpleNamespace(sha256=hashlib.sha256(data).hexdigest()), True),
                    registers=regs, **capture.from_mcp(Files({mpdc, dunedin, doc}), read_bytes=page))
    out = r.run()
    assert {i["url"] for i in t.items if i["sha"]} == {mpdc, doc, dunedin}
    assert (out["pages"], out["documents"], out["failed"]) == (2, 1, 0)
    assert len(t.held) == 3                                       # the holds stand for the boxes


def test_a_challenge_copy_on_a_held_council_still_blocks_its_site(monkeypatch):
    url = REGS["Invented District Council"][1]
    t = FakeTables()
    t.hold("www.invented.govt.nz", "HTTP 403: a block")
    out, t = _run({url, DOC}, monkeypatch, t=t,
                  bodies={url: b"<html><head><title>Just a moment...</title></head></html>"})
    assert (out["pages"], out["documents"]) == (0, 0) and out["held_hosts"] == 1


def test_a_challenge_copy_met_in_the_run_holds_its_site_for_the_rest_of_the_run(monkeypatch):
    """The lane's stored holds are not read, but a challenge met tonight holds the site: the register page one step
    down is a challenge, so the survey's document address on the same site is not taken after it."""
    landing, sub = "https://www.invented.govt.nz/council/", "https://www.invented.govt.nz/register-of-interests"
    regs = {"Invented District Council": ("www.invented.govt.nz", landing, DOC)}
    bodies = {landing: f'<a href="{sub}">Register of interests</a>'.encode(),
              sub: b"<html><head><title>Just a moment...</title></head></html>"}
    monkeypatch.setattr(fg, "open_url", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked the web")))
    t = FakeTables()
    r = capture.Run(t, land_fn=lambda data, **k: (types.SimpleNamespace(sha256=hashlib.sha256(data).hexdigest()), True),
                    registers=regs, **capture.from_mcp(Files({landing, sub, DOC}),
                                                       read_bytes=lambda u: bodies.get(u, b"%PDF-1.4 x")))
    out = r.run()
    assert (out["pages"], out["documents"], out["held_hosts"]) == (1, 0, 1)
    assert DOC not in {i["url"] for i in t.items}


def test_the_boxes_own_walk_still_asks_a_held_host_nothing():
    """The direct mode is unchanged: a host the lane holds is passed over, whatever the MCP holds."""
    t = FakeTables()
    t.hold("www.invented.govt.nz", "HTTP 403: a block")
    asked = []
    r = capture.Run(t, land_fn=lambda data, **k: (types.SimpleNamespace(sha256="x"), True), registers=REGS,
                    opener=lambda url, timeout: asked.append(url) or (_ for _ in ()).throw(OSError("down")),
                    anytime=True, sleep=lambda s: None)
    r.run()
    assert asked == [REGS["Other District Council"][1]]


def test_the_nightly_job_takes_the_mcp_copy_and_the_pull_brings_it():
    with open(os.path.join(REPO, "support", "scheduler", "jobs.toml"), "rb") as f:
        jobs = tomllib.load(f)["jobs"]
    job = jobs[capture.JOB]
    assert job.get("enabled", True) and "--from-mcp" in job["command"]
    pulled = jobs["qv4-mcp-pull"]["command"]
    assert set(capture.MCP_CORPORA) <= {pulled[i + 1] for i, a in enumerate(pulled) if a == "--corpus"}
