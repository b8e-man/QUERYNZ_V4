"""The fetch gate: the one place a fetch's permission and pacing are decided
(plan 1.10; from the old `ingestion/fetchgate.py`, with its robots refusal
replaced as hard limit 5 says).

Capture is judged on legality and politeness (hard limit 4), and a robots
file is no longer a permission decision (hard limit 5, ruling 10). The gate
reads robots.txt for ONE thing, a stated crawl delay, and honours it; the
file is archived verbatim with its hash, as a record. What refuses:

  1. a source out by name (hard limit 8): fyi.org.nz and every NZME masthead;
     a held host is not even sent a request for its robots.txt
  2. no one-page legal position on file for the host's class of source
     (hard limit 9): `docs/legal/positions/<class>.md` names its hosts
  3. a publisher's direct request to stop (hard limit 7): `STOP_REQUESTS`
  4. a challenge or a block met on the read (hard limit 6): a 403, 429 or
     5xx, or a challenge page, is a failed read. It is logged and the lane
     moves on; nothing is solved, logged in to, or got around

Politeness (hard limit 7): one User-Agent for the whole estate; a floor
between requests to one host that is the SLOWEST of the default, the stated
floor, the crawl delay and the polite floor; a pacer that blocks and is keyed
by host, so an exit rotation never buys speed; low concurrency; nothing
fetched twice (the document store's sameness hash). An unreadable robots
file is not a refusal; it means the host may be in trouble, so the polite
floor applies.

Every decision is recorded, with its reason, in `<live>/checks/fetch-gate/`.
Pure where it can be: `decide()` takes what was read and returns a decision
with no network, no clock, no file. Stdlib only.
"""
import datetime as dt
import hashlib
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import asdict, dataclass

LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
LEDGER_DIR = os.path.join(LIVE, "checks", "fetch-gate")
ROBOTS_DIR = os.path.join(LIVE, "checks", "robots")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POSITIONS_DIR = os.environ.get("QV4_POSITIONS") or os.path.join(REPO, "docs", "legal", "positions")

#: the one User-Agent. A string that appears twice is a string that differs once.
UA = "QueryNZ/1.0 (research aggregator; contact: admin@followthemoney.nz)"
OUR_TOKEN = "QueryNZ"
DEFAULT_FLOOR_S = 1.5
POLITE_FLOOR_S = 5.0
MAX_FLOOR_S = 120.0          # a crawl delay above this is honoured at this: the host is asking not to be crawled
CHALLENGE_STATUSES = (403, 429, 503, 502, 500, 504)
CHALLENGE_MARKS = ("cf-chl", "challenge-platform", "just a moment", "attention required", "captcha",
                   "radware", "incapsula", "_incapsula_", "are you a human", "access denied")

#: hosts we do not capture from (hard limit 8). Matched with every parent domain.
HELD = {
    "fyi.org.nz": "ruling 321: fyi.org.nz is not captured, indexed or read (hard limit 8)",
    "nzherald.co.nz": "ruling 12: NZME is not captured, indexed or read (hard limit 8)",
    "businessdesk.co.nz": "ruling 12: NZME (BusinessDesk is NZME-owned)",
    "newstalkzb.co.nz": "ruling 12: NZME",
    "gisborneherald.co.nz": "ruling 12: NZME",
    "oneroof.co.nz": "ruling 12: NZME",
    "driven.co.nz": "ruling 12: NZME",
    "nzme.co.nz": "ruling 12: NZME",
}
#: a publisher's direct request to stop: host → when and how it was made (hard limit 7)
STOP_REQUESTS = {}
#: stated floors (seconds between requests), one table, one home
FLOORS = {
    "web.archive.org": 1.0,
    "www.odata.charities.govt.nz": 5.0,   # the Charities Register's feed (charities-capture-1, 20 October)
    "api.business.govt.nz": 5.0,          # the NZBN register's entity detail (societies-1, 20 October)
    "ideas.repec.org": 5.0,
    "greaterauckland.org.nz": 30.0,
    "farmersweekly.co.nz": 5.0,
    "publicdata.co.nz": 5.0,
    # track E, the windowed sources: the floor each legal position states
    # (docs/legal/positions/tenancy-tribunal-decisions.md, real-estate-authority-decisions.md)
    "forms.justice.govt.nz": 5.0,
    "decisions.dotnous.com": 5.0,
}


class Refused(RuntimeError):
    """A permission decision, raised. Never caught and retried."""


@dataclass
class Robots:
    """What the host's robots.txt said when we read it: a record and a
    crawl delay, never a permission."""
    host: str
    text: str
    status: int          # 0 when nothing answered
    unreadable: bool     # 5xx, 429, timeout, DNS: the host could not answer
    crawl_delay: float
    read_at: str
    sha256: str


@dataclass
class Decision:
    allowed: bool
    reason: str
    host: str
    url: str
    floor: float
    position: str        # the class of source the position on file covers, or ''
    read_at: str = ""


def host_of(url: str) -> str:
    return (urllib.parse.urlsplit(url).hostname or "").lower()


def _parents(host: str):
    parts = (host or "").lower().split(".")
    yield host.lower()
    for i in range(1, len(parts) - 1):
        yield ".".join(parts[i:])


def held_reason(host: str):
    for h in _parents(host):
        if h in HELD:
            return HELD[h]
    return None


def stop_request(host: str):
    for h in _parents(host):
        if h in STOP_REQUESTS:
            return STOP_REQUESTS[h]
    return None


def stated_floor(host: str):
    for h in _parents(host):
        if h in FLOORS:
            return FLOORS[h]
    return None


def positions(folder: str = None) -> dict:
    """host → class of source, from the `hosts:` line of every position on
    file. A position is `docs/legal/positions/<class>.md` with a `hosts:`
    line naming the hosts it covers, comma-separated."""
    folder = folder or POSITIONS_DIR
    out = {}
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return out
    for n in names:
        if not n.endswith(".md") or n == "README.md":
            continue
        try:
            with open(os.path.join(folder, n), encoding="utf-8") as f:
                text = f.read()
        except OSError:
            continue
        m = re.search(r"^hosts:\s*(.+)$", text, re.M)
        if not m:
            continue
        for h in m.group(1).split(","):
            h = h.strip().lower()
            if h:
                out[h] = n[:-3]
    return out


def position_for(host: str, folder: str = None):
    pos = positions(folder)
    for h in _parents(host):
        if h in pos:
            return pos[h]
    return None


def floor_for(host: str, robots: Robots = None) -> float:
    """The slowest of every floor that applies; never a caller's own number."""
    cands = [DEFAULT_FLOOR_S]
    if (s := stated_floor(host)) is not None:
        cands.append(s)
    if robots is not None:
        if robots.crawl_delay:
            cands.append(min(float(robots.crawl_delay), MAX_FLOOR_S))
        if robots.unreadable:
            cands.append(POLITE_FLOOR_S)
    return max(cands)


def crawl_delay_of(text: str) -> float:
    """The one sanctioned use of the standard robots parser: Crawl-delay is a
    directive read per group, not a path decision."""
    rp = urllib.robotparser.RobotFileParser()
    rp.parse((text or "").splitlines())
    d = rp.crawl_delay(OUR_TOKEN)
    if d is None:
        d = rp.crawl_delay("*")
    try:
        return float(d) if d is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def decide(url: str, robots: Robots = None, position: str = None) -> Decision:
    """Pure. The decision for one URL, with the reason it was made."""
    host = host_of(url)
    floor = floor_for(host, robots)
    read_at = robots.read_at if robots else ""

    def d(allowed, reason):
        return Decision(allowed, reason, host, url, floor, position or "", read_at)

    if not host:
        return d(False, f"not a URL with a host: {url!r}")
    if (why := held_reason(host)) is not None:
        return d(False, f"we do not capture from {host}: {why}")
    if (req := stop_request(host)) is not None:
        return d(False, f"{host} asked us to stop: {req} (hard limit 7)")
    if not position:
        return d(False, f"no one-page legal position on file for {host} (hard limit 9): write docs/legal/positions/<class>.md naming it")
    if robots is not None and robots.unreadable:
        return d(True, f"permitted under the position `{position}`; robots.txt could not be read, so the polite floor applies ({floor:.0f}s)")
    return d(True, f"permitted under the position `{position}`; floor {floor:.1f}s" + (f" (crawl delay {robots.crawl_delay:.0f}s honoured)" if robots and robots.crawl_delay else ""))


def record(decision: Decision, ledger_dir: str = None) -> None:
    ledger_dir = ledger_dir or LEDGER_DIR
    os.makedirs(ledger_dir, exist_ok=True)
    row = asdict(decision)
    row["at"] = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    with open(os.path.join(ledger_dir, dt.datetime.now().strftime("%Y-%m") + ".jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


class Pacer:
    """Per-host spacing that blocks. The slot is claimed before the wait, so
    two concurrent callers queue instead of both going at once. Keyed by
    host and nothing else: an exit rotation never resets it."""

    def __init__(self, now=None, sleep=None):
        self.now = now or time.monotonic
        self.sleep = sleep or time.sleep
        self._last = {}
        self._lock = threading.Lock()

    def reserve(self, host: str, floor: float) -> float:
        with self._lock:
            now = self.now()
            last = self._last.get(host)
            start = now if last is None else max(now, last + floor)
            self._last[host] = start
            return max(0.0, start - now)

    def wait(self, host: str, floor: float) -> float:
        gap = self.reserve(host, floor)
        if gap > 0:
            self.sleep(gap)
        return gap


_PACER = Pacer()
_ROBOTS = {}


def _fetch(url: str, timeout: int):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(1 << 20)
    except urllib.error.HTTPError as e:
        return e.code, b""


def read_robots(host: str, fetch=None, timeout: int = 20, archive_dir: str = None) -> Robots:
    """Read https://<host>/robots.txt with the one UA, archive it verbatim
    with its hash, and return the record. `fetch(url, timeout) -> (status,
    body)` is injectable; a transport error is 'unreadable'."""
    read_at = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    try:
        status, body = (fetch or _fetch)(f"https://{host}/robots.txt", timeout)
    except Exception:  # noqa: BLE001 — the record of a failed read is the record
        return Robots(host, "", 0, True, 0.0, read_at, "")
    if status >= 500 or status == 429:
        return Robots(host, "", status, True, 0.0, read_at, "")
    text = body.decode("utf-8", "replace") if status == 200 else ""
    sha = hashlib.sha256(body).hexdigest() if status == 200 else ""
    if status == 200:
        archive_dir = archive_dir or ROBOTS_DIR
        os.makedirs(archive_dir, exist_ok=True)
        with open(os.path.join(archive_dir, f"{host}.{sha[:12]}.txt"), "wb") as f:
            f.write(body)
    return Robots(host, text, status, False, crawl_delay_of(text), read_at, sha)


def robots_for(host: str, fetch=None, refresh: bool = False) -> Robots:
    if refresh or host not in _ROBOTS:
        _ROBOTS[host] = read_robots(host, fetch=fetch)
    return _ROBOTS[host]


def check(url: str, *, fetch=None, positions_dir: str = None, ledger_dir: str = None) -> Decision:
    """Permission for one URL: decide, record, raise on a refusal. A held
    host is refused before its robots.txt is read: not capturing is not
    knocking."""
    host = host_of(url)
    pos = position_for(host, positions_dir)
    if held_reason(host) is not None or stop_request(host) is not None or not pos:
        dec = decide(url, None, pos)
    else:
        dec = decide(url, robots_for(host, fetch=fetch), pos)
    record(dec, ledger_dir)
    if not dec.allowed:
        raise Refused(f"{url}: {dec.reason}")
    return dec


@dataclass
class Fetched:
    url: str
    status: int
    body: bytes
    final_url: str
    blocked: str = ""        # '' or why this is a failed read (a challenge or a block)


def looks_challenged(status: int, body: bytes) -> str:
    if status in CHALLENGE_STATUSES:
        return f"HTTP {status}: a block or a challenge; a challenged read is a failed read (hard limit 6)"
    head = body[:4096].decode("utf-8", "replace").lower()
    for mark in CHALLENGE_MARKS:
        if mark in head:
            return f"a challenge page ({mark!r}); a challenged read is a failed read (hard limit 6)"
    return ""


def open_url(url: str, *, timeout: int = 30, headers: dict = None, pacer: Pacer = None, max_bytes: int = None,
             fetch=None, positions_dir: str = None, ledger_dir: str = None) -> Fetched:
    """The gated fetch: check, pace, go, with the one UA. A 404 is the host
    answering; a 403, 429, 5xx or a challenge page is a failed read, returned
    as `blocked` and never retried in the same run."""
    dec = check(url, positions_dir=positions_dir, ledger_dir=ledger_dir)
    (pacer or _PACER).wait(dec.host, dec.floor)
    if fetch is not None:
        status, body, final = fetch(url, timeout)
    else:
        req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                status, body, final = r.status, (r.read(max_bytes) if max_bytes else r.read()), r.geturl()
        except urllib.error.HTTPError as e:
            status, body, final = e.code, b"", url
    return Fetched(url, status, body, final, looks_challenged(status, body))


def pace(url_or_host: str, pacer: Pacer = None) -> float:
    """Block until the host's floor has passed, for a lane that does its own
    HTTP but must not set its own speed."""
    host = host_of(url_or_host) or url_or_host.lower()
    return (pacer or _PACER).wait(host, floor_for(host, _ROBOTS.get(host)))
