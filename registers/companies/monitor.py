"""Company monitoring (plan 5.5, ruling 19): one entity at a time, against
the NZBN register's own interface, when a product looks it up or a watch
falls due.

A product never writes into the estate. It asks through two published
functions this lane owns (publish.sql), which write one queue row each and
take the asker from the database login, never from an argument:

    pub.request_company_check(nzbn, name, product)   → companies.requests
    pub.watch_company(nzbn, product, every_days)      → companies.watch

The nightly job (`qv4-companies-monitor`, proposed in spec.md) takes the
waiting requests, oldest first, then the watches that are due, and for each
makes one call to `GET {BASE}/entities/{nzbn}` through the fetch gate with
our own key (read at the moment of use through support's credential folder,
sent only in its header, never logged or printed). Polite: one call at a
time, at least the gate's floor apart (5 s for this host), at most
DAILY_LIMIT calls in a New Zealand day (the interface states no limit; this
is ours), off-peak, never in the interface's Wednesday 21:00 to 23:00
maintenance window, and nothing fetched twice in a day: an entity already
answered today answers the request from that answer. A 403, 429, 5xx or a
challenge is a failed read: logged, and the night stops (hard limit 6).

Every answer is landed verbatim by hash and recorded in `companies.calls`
(the ledger: never wiped). Its reading goes to the lookup tables (the
entity as the interface answered it, its roles with the interface's own
start and end dates, its holdings, its registered office) and each
difference from the state held before it, the previous answer or else the
monthly file's rows, to `companies.changes`, dated and citing the answer.
Any address a role carries, and every address of a sole trader,
partnership or trust, goes to `companies_private.lookup_addresses` and
nowhere else (hard limit 15). Those three kinds, which the companies lane's
monthly reading does not take, are stored as lookups of their own kind.

An exported copy of a product never calls the interface: the queue
functions and this module stay in the estate, and an export has no key.

    fetch_entity(nzbn, conn, ...)       one gated call: (Fetched, DocumentRef or None)
    read_answer(data, sha, asked_at)    Reading: the entity, roles, holdings, offices, private, set aside
    held_state(conn, nzbn, T)           the state before: the last answer, else the monthly rows
    diff(before, after, ...)            the change rows
    run(conn, ...)                      one night: requests, then due watches
    rebuild(conn, ...)                  the lookup tables and changes again from the ledger's answers
    python -m registers.companies.monitor --night [--anytime] [--budget-s N]
    python -m registers.companies.monitor --fetch NZBN [NZBN ...]   a handful, to prove the path (sample db)
    python -m registers.companies.monitor --rebuild
"""
import datetime as dt
import hashlib
import json
import os
import re
import sys
import threading
import time
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

from keys.addresses import address_key
from keys.names import organisation_key, person_key
from keys.numbers import nzbn as nzbn_ok
from support import db, profiles
from support.docstore.landing import land, read_bytes

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
SOURCE = "companies"
API_NOTE = "the NZBN register's entity detail, as it answered"
PROFILE = "nzbn-entity-detail-any-kind"
READER = "registers.companies.monitor 1"
JOB = "qv4-companies-monitor"
NZ = ZoneInfo("Pacific/Auckland")

BASE = os.environ.get("QV4_NZBN_API_BASE") or "https://api.business.govt.nz/gateway/nzbn/v5"
KEY_FILE = "nzbn.env"
KEY_NAME = "NZBN_API_KEY"
KEY_HEADER = "Ocp-Apim-Subscription-Key"
#: the interface states no rate limit (portal.api.business.govt.nz/api/nzbn, read 21 October 2026); ours
DAILY_LIMIT = 300
#: the lane's own floor between calls, the same as the gate's FLOORS for the host; the slower one holds
FLOOR_S = 5.0
DEFAULT_BUDGET_S = 1500
#: a request still waiting this long after it was raised fails the check
ANSWER_WITHIN = dt.timedelta(hours=48)
#: the path proved on eight entities, 21 October 2026 (nzbn, sha256 of the answer, landed at): five companies
#: of the sample, then a sole trader, a partnership and a trading trust (the monthly reading takes none of the three)
PROOF = (
    ("9429046854308", "4a04d8011c52d8573f5ebd349ccc2074121780a22c2dc62e2a9d1a3edbffa309", "2026-10-21T11:05:16+13:00"),
    ("9429052976568", "7e5de3c19209597e02ee159fb809e90499f1d3dc17b79bfb8f2d89a15cd1025d", "2026-10-21T11:05:22+13:00"),
    ("9429041764886", "f1268f88b9ba4565680586d5e4e3830c432e65c1488990a1cca2c3a364d5b616", "2026-10-21T11:05:28+13:00"),
    ("9429033434155", "0efd3e5558b3ed719bdbacee0cfc2425a24b1567aee72d97457fc4161fe5fa98", "2026-10-21T11:05:34+13:00"),
    ("9429049224986", "24047621e0d36469b5bfe6972e199b092c9a265a04343e5744b46c2b2b86fea0", "2026-10-21T11:05:39+13:00"),
    ("9429053867209", "f04ab846e973b6ae488d34e2940b6ca1fd38ba8508b572a577f5e5ce2a5e6642", "2026-10-21T11:05:46+13:00"),
    ("9429053867230", "b5e3ec66cfb3af2a71c2f33222f3d5f75a3fe7f986f7dca330d4256d2ceb8db2", "2026-10-21T11:05:51+13:00"),
    ("9429053867223", "48692f12198b5a9e9e2011ba01c4ba8a548a8c9fabcd87a2fdec7fc21e4da663", "2026-10-21T11:05:57+13:00"),
)
_ONE_AT_A_TIME = threading.Lock()
_LAST = {"at": 0.0}


# --- the call --------------------------------------------------------------------------------------------------

def api_key() -> str:
    """Our NZBN key, read now from the credential folder. Never print it."""
    path = os.path.join(db.CRED_DIR, KEY_FILE)
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(KEY_NAME + "="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    except OSError as exc:
        raise RuntimeError(f"no NZBN credential file: {type(exc).__name__}") from None
    raise RuntimeError(f"{KEY_NAME} is not set in {KEY_FILE}")


def entity_url(nzbn: str) -> str:
    if nzbn_ok(nzbn) != nzbn:
        raise ValueError(f"not an NZBN: {nzbn!r}")
    return f"{BASE}/entities/{nzbn}"


def now_nz() -> dt.datetime:
    return dt.datetime.now(NZ)


def nz_day(at) -> dt.date:
    if isinstance(at, str):
        at = dt.datetime.fromisoformat(at)
    return at.astimezone(NZ).date()


def off_peak(t: dt.datetime) -> bool:
    """22:00 to 01:00 New Zealand time, before the societies lane's nightly
    asks of the same host begin, and never in the interface's Wednesday
    21:00 to 23:00 maintenance window."""
    nz = t.astimezone(NZ)
    if nz.weekday() == 2 and 21 <= nz.hour < 23:
        return False
    return nz.hour >= 22 or nz.hour < 1


def fetch_entity(nzbn: str, conn, *, key: str = None, fetch=None, pacer=None, positions_dir: str = None,
                 ledger_dir: str = None, sleep=time.sleep, clock=time.monotonic):
    """One gated call, never two at once. Returns (Fetched, DocumentRef or
    None): the bytes are landed only when the register answered 200 with
    JSON. A refusal raises (fetchgate.Refused); a block comes back as
    `blocked`."""
    from support import fetchgate
    url = entity_url(nzbn)
    with _ONE_AT_A_TIME:
        gap = _LAST["at"] + FLOOR_S - clock()
        if gap > 0 and fetch is None:
            sleep(gap)
        got = fetchgate.open_url(url, timeout=30, headers={KEY_HEADER: key or api_key(),
                                                           "Accept": "application/json"},
                                 pacer=pacer, fetch=fetch, positions_dir=positions_dir, ledger_dir=ledger_dir)
        _LAST["at"] = clock()
    if got.blocked or got.status != 200:
        return got, None
    try:
        json.loads(got.body)
    except ValueError:
        got.blocked = "HTTP 200 that is not JSON: a failed read"
        return got, None
    ref, _ = land(got.body, name=url, source=SOURCE, conn=conn, name_kind="url",
                  fetched_at=now_nz().isoformat(timespec="seconds"), content_type="application/json")
    return got, ref


# --- the reading -----------------------------------------------------------------------------------------------

#: entityTypeCode → the kind a lookup is stored as. The five company types the monthly reading takes are
#: `company`; the three the monthly reading does not take are kinds of their own (plan 5.5)
KIND_OF = {"Sole_Trader": "sole_trader", "SoleTrader": "sole_trader", "Partnership": "partnership",
           "Trading_Trust": "trust", "Trust": "trust", "I": "society", "Incorporated Society": "society"}
COMPANY_CODES = {"LTD", "ULTD", "COOP", "ASIC", "NON_ASIC", "BUSINESS_TRUST"}
#: kinds whose registered office is shown (hard limit 15: a company's registered address is shown). Every
#: address of any other kind may be a person's home, and goes to the private table
OFFICE_SHOWN = {"company", "society"}


def kind_of(type_code: str) -> str:
    if (type_code or "") in COMPANY_CODES:
        return "company"
    return KIND_OF.get(type_code or "", "other")


def day_of(stamp) -> str:
    """The interface's stamp (`2018-06-25T08:30:43.000+1200`, New Zealand local) → its day as filed."""
    if not stamp or not isinstance(stamp, str) or not re.match(r"^\d{4}-\d{2}-\d{2}", stamp):
        return None
    try:
        return dt.date.fromisoformat(stamp[:10]).isoformat()
    except ValueError:
        return None


def short(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def strip_number(name):
    """The interface files a body's name with its register number in front ("7559576 - X LIMITED")."""
    return re.sub(r"^\d+\s+-\s+", "", name) if isinstance(name, str) else name


def _join(*parts) -> str:
    return " ".join(p.strip() for p in parts if isinstance(p, str) and p.strip())


def holder_key(name: str, org: bool) -> str:
    return ("o:" + organisation_key(name)) if org else ("p:" + person_key(name))


def office_key(lines) -> str:
    return address_key(" ".join(x for x in lines if x))


@dataclass
class Reading:
    nzbn: str
    entity: dict
    roles: list = field(default_factory=list)          # {place, uid, type, status, first, middle, last, full, body, start, end}
    holdings: list = field(default_factory=list)       # {place, org, name, holder_nzbn, shares, allocation, start, end, current}
    offices: list = field(default_factory=list)        # {place, uid, start, end, care_of, line_1..4, postcode, country}
    private: list = field(default_factory=list)        # (place, kind, address dict)
    set_aside: list = field(default_factory=list)      # (place, reason)
    counts: dict = field(default_factory=dict)


def _addr(a: dict) -> dict:
    return {k: a.get(k) for k in ("careOf", "address1", "address2", "address3", "address4", "postCode",
                                  "countryCode", "addressType", "startDate", "endDate")}


def read_answer(data: bytes, sha: str, asked_at: str) -> Reading:
    """One entity detail as the register answered it. Every role, holding and
    address is a reading, a private line or a catch-log line; e-mail and
    telephone details are left in the document and never read."""
    raw = json.loads(data)
    nzbn = str(raw.get("nzbn") or "")
    if nzbn_ok(nzbn) != nzbn:
        raise ValueError(f"{sha}: an entity detail with no NZBN")
    kind = kind_of(raw.get("entityTypeCode"))
    privacy = raw.get("privacySettings") or {}
    r = Reading(nzbn, {
        "kind": kind, "entity_type": raw.get("entityTypeCode"), "type_description": raw.get("entityTypeDescription"),
        "name": raw.get("entityName") if not privacy.get("namePrivateInformation") else None,
        "status": raw.get("entityStatusDescription"), "status_code": raw.get("entityStatusCode"),
        "registered_on": day_of(raw.get("registrationDate")), "register_updated_on": day_of(raw.get("lastUpdatedDate")),
        "source_register": raw.get("sourceRegister"), "asked_at": asked_at,
        "trading_names": [t.get("name") for t in raw.get("tradingNames") or [] if t.get("name") and not t.get("endDate")],
    })
    for i, role in enumerate(raw.get("roles") or []):
        place = f"roles[{i}]"
        p, e = role.get("rolePerson") or {}, role.get("roleEntity") or {}
        first, middle, last = p.get("firstName"), p.get("middleNames"), p.get("lastName")
        body = strip_number(e.get("currentEntityName") or e.get("entityName")) if e else None
        full = _join(first, middle, last) or body
        if not full:
            r.set_aside.append((place, f"a {role.get('roleType') or 'untyped'} role with no name"))
            continue
        r.roles.append({"place": place, "uid": role.get("uniqueIdentifier"), "type": role.get("roleType"),
                        "status": role.get("roleStatus"), "first": first, "middle": middle, "last": last,
                        "full": full, "body": bool(body and not p), "body_nzbn": e.get("nzbn") if e else None,
                        "start": day_of(role.get("startDate")), "end": day_of(role.get("endDate")),
                        "suppressed": bool(role.get("suppressed") or p.get("suppressed"))})
        for j, a in enumerate(role.get("roleAddress") or []):
            r.private.append((f"{place}.roleAddress[{j}]", "role", _addr(a)))
        if role.get("roleAsicAddress"):
            r.private.append((f"{place}.roleAsicAddress", "role", role["roleAsicAddress"]))
    sh = (raw.get("company-details") or {}).get("shareholding") or {}
    for i, alloc in enumerate(sh.get("shareAllocation") or []):
        for j, h in enumerate(alloc.get("shareholder") or []):
            _holding(r, f"shareAllocation[{i}].shareholder[{j}]", h, alloc.get("allocation"), i, current=True)
    for i, h in enumerate(sh.get("historicShareholder") or []):
        _holding(r, f"historicShareholder[{i}]", h, None, None, current=False)
    for i, a in enumerate((raw.get("addresses") or {}).get("addressList") or []):
        place = f"addresses[{i}]"
        if kind in OFFICE_SHOWN and a.get("addressType") == "REGISTERED":
            r.offices.append({"place": place, "uid": a.get("uniqueIdentifier"), "start": day_of(a.get("startDate")),
                              "end": day_of(a.get("endDate")), "care_of": a.get("careOf"),
                              "line_1": a.get("address1"), "line_2": a.get("address2"), "line_3": a.get("address3"),
                              "line_4": a.get("address4"), "postcode": a.get("postCode"),
                              "country": a.get("countryCode")})
        else:
            r.private.append((place, (a.get("addressType") or "address").lower(), _addr(a)))
    r.counts = {"roles": len(raw.get("roles") or []), "holdings": len(r.holdings), "offices": len(r.offices),
                "private": len(r.private), "set_aside": len(r.set_aside)}
    if len(r.roles) + sum(1 for p, _ in r.set_aside if p.startswith("roles[")) != r.counts["roles"]:
        raise AssertionError(f"companies monitor {sha}: roles do not reconcile")
    return r


def _holding(r: Reading, place: str, h: dict, allocation, index, current: bool) -> None:
    ind = h.get("individualShareholder") or h.get("historicIndividualShareholder") or {}
    org = h.get("otherShareholder") or h.get("historicOtherShareholder") or {}
    name = strip_number(org.get("currentEntityName") or org.get("entityName")) if org else (
        ind.get("fullName") or _join(ind.get("firstName"), ind.get("middleNames"), ind.get("lastName")))
    for k in ("shareholderAddress", "historicShareholderAddress"):
        if h.get(k):
            r.private.append((f"{place}.{k}", "holder", _addr(h[k])))
    if not name:
        r.set_aside.append((place, f"a {h.get('type') or 'untyped'} holding with no name"))
        return
    r.holdings.append({"place": place, "org": bool(org), "type": h.get("type"), "name": name,
                       "holder_nzbn": org.get("nzbn") if org else None,
                       "shares": allocation, "allocation": index, "start": day_of(h.get("appointmentDate")),
                       "end": day_of(h.get("vacationDate")), "current": current})


# --- the state before, and the differences ---------------------------------------------------------------------

@dataclass
class State:
    """An entity as it stood, from one source, in the shape both sources share."""
    source: str                  # 'answer' | 'monthly'
    document: str                # the answer's hash, or the monthly part's
    label: str                   # 'the answer of <day>' | 'the monthly file <file>'
    name: str = None
    status: str = None
    directors: dict = field(default_factory=dict)   # (person key, start) → {name, key, suppressed, ended}
    holdings: dict = field(default_factory=dict)    # (holder key, shares) → {name, key, suppressed}
    office: dict = None                              # {key, start, text}
    #: the categories this source can speak for. An answer lists every role and holding; the monthly file lists
    #: a company's current ones only while it is live (the August file holds no current role of a removed
    #: company), so a category it holds nothing current for is not compared
    compares: tuple = ("directors", "holdings", "office")


def _norm_status(s) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _num(x):
    try:
        return int(float(x)) if x is not None and float(x) == int(float(x)) else (float(x) if x is not None else None)
    except (TypeError, ValueError):
        return None


def state_of_answer(r: Reading, sha: str) -> State:
    s = State("answer", sha, f"the answer of {nz_day(r.entity['asked_at'])}", r.entity["name"], r.entity["status"])
    for x in r.roles:
        if (x["type"] or "").lower() != "director":
            continue
        s.directors[(person_key(x["full"]), x["start"])] = {
            "name": x["full"], "key": x["uid"], "suppressed": x["suppressed"], "ended": x["end"], "place": x["place"]}
    for x in r.holdings:
        if x["current"]:
            s.holdings[(holder_key(x["name"], x["org"]), _num(x["shares"]))] = {
                "name": x["name"], "key": x["place"], "suppressed": False, "place": x["place"]}
    cur = [o for o in r.offices if not o["end"]]
    if cur:
        o = cur[0]
        lines = (o["line_1"], o["line_2"], o["line_3"], o["line_4"], o["postcode"])
        s.office = {"key": office_key(lines), "start": o["start"], "text": ", ".join(x for x in lines if x),
                    "place": o["place"]}
    return s


def held_state(conn, nzbn: str, T=None, before_call: int = None):
    """The state held before an answer: the latest earlier answer's reading,
    else the monthly file's current rows; None when neither holds the entity.
    `before_call`: the ledger id of the call being read, so a rebuild
    compares each answer with the one before it."""
    T = T or Tables()
    t = lambda n: getattr(T, n)
    q = (f"SELECT document, at FROM {t('calls')} WHERE nzbn = %s AND status = 200 AND document IS NOT NULL "
         + ("AND id < %s " if before_call else "") + "ORDER BY id DESC LIMIT 1")
    prev = conn.execute(q, (nzbn, before_call) if before_call else (nzbn,)).fetchone()
    if prev:
        return state_of_answer(read_answer(read_bytes(prev[0]), prev[0], prev[1].isoformat()), prev[0])
    ent = conn.execute(f"SELECT key, name, status, document, last_file FROM {t('entities')} WHERE nzbn = %s "
                       f"ORDER BY in_latest DESC LIMIT 1", (nzbn,)).fetchone()
    if not ent:
        return None
    ekey, name, status, doc, last = ent
    s = State("monthly", doc, f"the monthly file {last}", name, status)
    for key, full, start, sup, d in conn.execute(
            f"SELECT key, full_name, appointed_on, suppressed, document FROM {t('directors')} "
            f"WHERE entity_key = %s AND in_latest", (ekey,)):
        s.directors[(person_key(full), start.isoformat() if start else None)] = {
            "name": full, "key": key, "suppressed": sup, "ended": None, "document": d}
    for key, stype, name_, shares, sup in conn.execute(
            f"SELECT key, shareholder_type, name, shares, suppressed FROM {t('shareholders')} "
            f"WHERE entity_key = %s AND in_latest", (ekey,)):
        s.holdings[(holder_key(name_, stype == "company"), _num(shares))] = {"name": name_, "key": key,
                                                                               "suppressed": sup}
    o = conn.execute(f"SELECT key, started_on, line_1, line_2, line_3, line_4, postcode FROM "
                     f"{t('registered_offices')} WHERE entity_key = %s AND in_latest LIMIT 1", (ekey,)).fetchone()
    if o:
        lines = o[2:]
        s.office = {"key": office_key(lines), "start": o[1].isoformat() if o[1] else None,
                    "text": ", ".join(x for x in lines if x), "held_key": o[0]}
    s.compares = tuple(c for c, held in (("directors", s.directors), ("holdings", s.holdings),
                                         ("office", s.office)) if held)
    return s


def diff(before: State, after: State, r: Reading) -> list:
    """Each difference as a change: (kind, subject, before, after, effective_on,
    date_basis, place, suppressed, held_key). `effective_on` is the
    interface's own date where it states one (`register`), else empty and
    the change is dated by the day it was seen (`seen`)."""
    out = []
    if before is None:
        return out
    if (before.name or "") != (after.name or "") and after.name is not None:
        out.append(("name", None, before.name, after.name, None, "seen", "entityName", False, None))
    if _norm_status(before.status) != _norm_status(after.status):
        out.append(("status", None, before.status, after.status, None, "seen", "entityStatusDescription", False, None))
    for k, b in before.directors.items() if "directors" in before.compares else ():
        if b.get("ended"):
            continue
        a = after.directors.get(k)
        sup = bool(b.get("suppressed"))
        if a is None:
            out.append(("director_not_listed", b["name"], b["name"], None, None, "seen", "roles", sup, b["key"]))
        elif a["ended"] and not b.get("ended"):
            out.append(("director_ended", b["name"], b["name"], None, a["ended"], "register", a["place"], sup,
                        b["key"]))
    for k, a in after.directors.items() if "directors" in before.compares else ():
        if k not in before.directors and not a["ended"]:
            out.append(("director_appointed", a["name"], None, a["name"], k[1], "register" if k[1] else "seen",
                        a["place"], a["suppressed"], None))
    hist = {}
    for x in r.holdings:
        if not x["current"]:
            hist.setdefault(holder_key(x["name"], x["org"]), []).append(x)
    for k, b in before.holdings.items() if "holdings" in before.compares else ():
        if k not in after.holdings:
            ended = sorted((h for h in hist.get(k[0], []) if h["end"]), key=lambda h: h["end"])
            if ended:
                out.append(("holding_ended", b["name"], f"{b['name']} ({k[1]})", None, ended[-1]["end"], "register",
                            ended[-1]["place"], bool(b.get("suppressed")), b["key"]))
            else:
                out.append(("holding_not_listed", b["name"], f"{b['name']} ({k[1]})", None, None, "seen",
                            "company-details.shareholding", bool(b.get("suppressed")), b["key"]))
    for k, a in after.holdings.items() if "holdings" in before.compares else ():
        if k not in before.holdings:
            h = next((x for x in r.holdings if x["place"] == a["place"]), {})
            out.append(("holding_started", a["name"], None, f"{a['name']} ({k[1]})", h.get("start"),
                        "register" if h.get("start") else "seen", a["place"], False, None))
    bo, ao = before.office, after.office
    if ao and "office" in before.compares and (bo is None or (bo["key"] != ao["key"] and bo.get("start") != ao["start"])):
        out.append(("registered_office", None, bo["text"] if bo else None, ao["text"], ao["start"],
                    "register" if ao["start"] else "seen", ao["place"], False, (bo or {}).get("held_key")))
    return out


# --- storing an answer -----------------------------------------------------------------------------------------

#: the monitor's tables: the queue and the ledger are kept (never wiped by a load or a rebuild); the rest are
#: rebuilt from the ledger's answers by `rebuild`
KEPT = ("requests", "watch", "calls")
REBUILT = ("lookups", "lookup_roles", "lookup_holdings", "lookup_offices", "changes", "lookup_set_aside")
PRIVATE_REBUILT = ("lookup_addresses",)


def profile_version() -> int:
    p = profiles.profile(PROFILE) or profiles.profile(PROFILE, path=PROPOSED)
    if p is None:
        raise LookupError(f"no document profile {PROFILE}")
    return int(p["version"])


class Tables:
    """The monitor's table names under `schema` (the lane's, or the shared sample schema's prefixed ones)."""

    def __init__(self, schema: str = "companies", shared: bool = False, override: dict = None):
        from registers.companies.load import private_of, table
        self.schema, self.shared, self.override = schema, shared, override or {}
        self._t = lambda n: table(schema, n, shared)
        self._p = lambda n: table(private_of(schema), n, shared)

    def __getattr__(self, name):
        if name.startswith("_") or name in ("schema", "shared", "override"):
            raise AttributeError(name)
        if name in self.override:
            return self.override[name]
        if name in PRIVATE_REBUILT:
            return self._p(name)
        return self._t(name)


def _cite(sha: str, place: str, loaded_at: str, version: int) -> dict:
    return {"document": sha, "page": 1, "place": place, "read_from": "text", "reader": READER, "profile": PROFILE,
            "profile_version": version, "loaded_at": loaded_at}


def _insert(conn, table: str, row: dict) -> None:
    cols = list(row)
    conn.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})",
                 [json.dumps(v) if isinstance(v, (dict, list)) else v for v in row.values()])


def record_call(conn, T: Tables, nzbn: str, at: dt.datetime, status: int, sha, blocked, why: str) -> int:
    return conn.execute(f"INSERT INTO {T.calls} (nzbn, at, day, status, document, blocked, why) "
                        f"VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                        (nzbn, at, nz_day(at), status, sha, blocked or None, why)).fetchone()[0]


def apply_answer(conn, T: Tables, call_id: int, sha: str, at: dt.datetime, version: int = None,
                 loaded_at: str = None) -> int:
    """One landed answer read into the lookup tables and compared with the
    state held before it. Returns the number of changes. The same bytes
    landed again add nothing: they say nothing new."""
    if conn.execute(f"SELECT 1 FROM {T.lookups} WHERE document = %s", (sha,)).fetchone():
        return 0
    version = version or profile_version()
    loaded_at = loaded_at or now_nz().isoformat(timespec="seconds")
    r = read_answer(read_bytes(sha), sha, at.isoformat())
    n = r.nzbn
    ekey = f"companies/{n}"
    akey = f"{ekey}/answer/{sha[:12]}"
    before = held_state(conn, n, T, before_call=call_id)
    after = state_of_answer(r, sha)
    held = conn.execute(f"SELECT 1 FROM {T.entities} WHERE nzbn = %s LIMIT 1", (n,)).fetchone() is not None
    conn.execute(f"UPDATE {T.lookups} SET latest = false WHERE nzbn = %s AND latest", (n,))
    e = r.entity
    _insert(conn, T.lookups, {"key": akey, "entity_key": ekey, "nzbn": n, "kind": e["kind"],
                              "entity_type": e["entity_type"], "type_description": e["type_description"],
                              "name": e["name"], "status": e["status"], "registered_on": e["registered_on"],
                              "register_updated_on": e["register_updated_on"], "trading_names": e["trading_names"],
                              "asked_at": at, "call_id": call_id, "in_monthly": held, "latest": True,
                              "source_note": API_NOTE, **_cite(sha, "whole", loaded_at, version)})
    sup_by_name = {person_key(v["name"]): bool(v.get("suppressed")) for v in (before.directors.values() if before else [])}
    held_by = monthly_director_keys(conn, T, n)
    for x in r.roles:
        k = (person_key(x["full"]), x["start"])
        _insert(conn, T.lookup_roles, {
            "key": f"{ekey}/role/{x['uid'] or short(x['full'] + str(x['start']))}/{sha[:12]}", "answer_key": akey,
            "entity_key": ekey, "nzbn": n, "role_uid": x["uid"], "role_type": x["type"], "role_status": x["status"],
            "first_name": x["first"], "middle_names": x["middle"], "last_name": x["last"], "full_name": x["full"],
            "is_body": x["body"], "body_nzbn": x["body_nzbn"], "started_on": x["start"], "ended_on": x["end"],
            "held_key": held_by.get(k), "suppressed": x["suppressed"] or sup_by_name.get(person_key(x["full"]), False),
            "source_note": API_NOTE, **_cite(sha, x["place"], loaded_at, version)})
    for x in r.holdings:
        _insert(conn, T.lookup_holdings, {
            "key": f"{ekey}/holding/{short(x['place'] + x['name'] + str(x['start']))}/{sha[:12]}", "answer_key": akey,
            "entity_key": ekey, "nzbn": n, "holder_type": x["type"], "name": x["name"], "holder_nzbn": x["holder_nzbn"],
            "shares": x["shares"], "allocation": x["allocation"], "started_on": x["start"], "ended_on": x["end"],
            "current": x["current"], "suppressed": False, "source_note": API_NOTE,
            **_cite(sha, x["place"], loaded_at, version)})
    for x in r.offices:
        _insert(conn, T.lookup_offices, {
            "key": f"{ekey}/registered-office/{x['uid'] or short(str(x))}/{sha[:12]}", "answer_key": akey,
            "entity_key": ekey, "nzbn": n, "started_on": x["start"], "ended_on": x["end"], "care_of": x["care_of"],
            "line_1": x["line_1"], "line_2": x["line_2"], "line_3": x["line_3"], "line_4": x["line_4"],
            "postcode": x["postcode"], "country": x["country"], "source_note": API_NOTE,
            **_cite(sha, x["place"], loaded_at, version)})
    for place, kind, addr in r.private:
        conn.execute(f"INSERT INTO {T.lookup_addresses} (key, owner_key, kind, address, document) "
                     f"VALUES (%s, %s, %s, %s, %s)", (f"{akey}/{place}", akey, kind, json.dumps(addr), sha))
    for place, why in r.set_aside:
        conn.execute(f"INSERT INTO {T.lookup_set_aside} (item, stage, reason) VALUES (%s, 'monitor', %s)",
                     (f"{sha}/{place}", why))
    changes = diff(before, after, r)
    for kind, subject, b, a, eff, basis, place, sup, held_key in changes:
        _insert(conn, T.changes, {
            "key": f"{ekey}/change/{sha[:12]}/{kind}/{short(str((subject, b, a, eff)))}", "entity_key": ekey,
            "nzbn": n, "kind": kind, "subject": subject, "before": b, "after": a, "effective_on": eff,
            "date_basis": basis, "seen_on": nz_day(at), "register_updated_on": e["register_updated_on"],
            "compared_with": before.label, "previous_document": before.document, "held_key": held_key,
            "suppressed": sup, "call_id": call_id, "source_note": API_NOTE, **_cite(sha, place, loaded_at, version)})
    return len(changes)


def monthly_director_keys(conn, T: Tables, nzbn: str) -> dict:
    """(person key, start) → the monthly file's director row key, so a role the interface dates can be
    joined to the row whose end the file never stated."""
    return {(person_key(full), start.isoformat() if start else None): key for key, full, start in conn.execute(
        f"SELECT key, full_name, appointed_on FROM {T.directors} WHERE nzbn = %s", (nzbn,))}


def rebuild(conn, schema: str = "companies", shared: bool = False, log=print) -> dict:
    """The lookup tables and the changes wiped and read again from every
    answer in the ledger, oldest first, in one transaction."""
    T = Tables(schema, shared)
    version, n, c = profile_version(), 0, 0
    with conn.transaction():
        for t in REBUILT + PRIVATE_REBUILT:
            conn.execute(f"DELETE FROM {getattr(T, t)}")
        for cid, sha, at in conn.execute(f"SELECT id, document, at FROM {T.calls} WHERE status = 200 AND "
                                         f"document IS NOT NULL ORDER BY id").fetchall():
            c += apply_answer(conn, T, cid, sha, at, version)
            n += 1
    log(f"companies monitor: rebuilt from {n} answer(s), {c} change(s)")
    return {"answers": n, "changes": c}


# --- the night -------------------------------------------------------------------------------------------------

def _resolve(conn, T: Tables, nzbn, name):
    """A request's NZBN, or (None, why it is set aside)."""
    if nzbn:
        n = nzbn_ok(nzbn)
        return (n, None) if n else (None, f"not an NZBN: {len(re.sub(r'[^0-9]', '', nzbn))} digits or a wrong check digit")
    found = [r[0] for r in conn.execute(
        f"SELECT DISTINCT nzbn FROM {T.entities} WHERE lower(name) = lower(%s) AND nzbn IS NOT NULL AND in_latest "
        f"UNION SELECT DISTINCT nzbn FROM {T.lookups} WHERE lower(name) = lower(%s) AND latest LIMIT 3",
        (name, name))]
    if len(found) == 1:
        return found[0], None
    return None, ("no entity held under that exact name; ask by NZBN" if not found else
                  "more than one entity held under that exact name; ask by NZBN")


def due_watches(conn, T: Tables, now: dt.datetime) -> list:
    """The watched NZBNs whose last answer is older than the shortest interval
    any product asked for: never asked first, then the stalest."""
    rows = conn.execute(
        f"SELECT w.nzbn, min(w.every_days), (SELECT max(c.at) FROM {T.calls} c WHERE c.nzbn = w.nzbn AND "
        f"c.status = 200) FROM {T.watch} w WHERE w.active GROUP BY w.nzbn").fetchall()
    due = [(last, n) for n, days, last in rows if last is None or now - last >= dt.timedelta(days=days)]
    return [n for last, n in sorted(due, key=lambda x: (x[0] is not None, x[0] or now, x[1]))]


def run(conn, schema: str = "companies", shared: bool = False, *, budget_s: float = DEFAULT_BUDGET_S,
        anytime: bool = False, key: str = None, fetch=None, pacer=None, now=None, daily_limit: int = DAILY_LIMIT,
        positions_dir: str = None, ledger_dir: str = None, log=print, record: bool = True) -> dict:
    """One night: the waiting requests, oldest first, then the due watches,
    one gated call each, until both are done, the budget or the day's limit
    is spent, off-peak ends, or a read fails."""
    from support import jobrun
    T = Tables(schema, shared)
    now = now or now_nz
    started, t0 = jobrun.now(), time.monotonic()
    version = profile_version()
    counts = {"requests": 0, "answered": 0, "from_today": 0, "set_aside": 0, "watches": 0, "calls": 0,
              "changes": 0}
    stopped = ""

    def stop_why():
        if not anytime and not off_peak(now()):
            return "off-peak ended"
        if time.monotonic() - t0 >= budget_s:
            return "budget spent"
        day = nz_day(now())
        if conn.execute(f"SELECT count(*) FROM {T.calls} WHERE day = %s", (day,)).fetchone()[0] >= daily_limit:
            return f"the day's limit of {daily_limit} calls reached"
        return ""

    def today(n):
        return conn.execute(f"SELECT id FROM {T.calls} WHERE nzbn = %s AND day = %s AND status = 200 AND "
                            f"document IS NOT NULL ORDER BY id DESC LIMIT 1", (n, nz_day(now()))).fetchone()

    def call(n, why):
        nonlocal key
        key = key or api_key()
        got, ref = fetch_entity(n, conn, key=key, fetch=fetch, pacer=pacer, positions_dir=positions_dir,
                                ledger_dir=ledger_dir)
        at = now()
        cid = record_call(conn, T, n, at, got.status, ref.sha256 if ref else None, got.blocked, why)
        counts["calls"] += 1
        if ref:
            counts["changes"] += apply_answer(conn, T, cid, ref.sha256, at, version)
        conn.commit()
        return got, ref, cid

    waiting = conn.execute(f"SELECT id, nzbn, name FROM {T.requests} WHERE state = 'waiting' "
                           f"ORDER BY asked_at, id").fetchall()
    for rid, nzbn, name in waiting:
        counts["requests"] += 1
        n, why = _resolve(conn, T, nzbn, name)
        if n is None:
            conn.execute(f"UPDATE {T.requests} SET state = 'set_aside', reason = %s, answered_at = %s WHERE id = %s",
                         (why, now(), rid))
            conn.commit()
            counts["set_aside"] += 1
            continue
        had = today(n)
        if had:
            conn.execute(f"UPDATE {T.requests} SET state = 'answered', resolved_nzbn = %s, call_id = %s, "
                         f"answered_at = %s, reason = 'answered from the day''s answer' WHERE id = %s",
                         (n, had[0], now(), rid))
            conn.commit()
            counts["answered"] += 1
            counts["from_today"] += 1
            continue
        if (stopped := stop_why()):
            break
        got, ref, cid = call(n, f"request {rid}")
        if ref:
            conn.execute(f"UPDATE {T.requests} SET state = 'answered', resolved_nzbn = %s, call_id = %s, "
                         f"answered_at = %s, reason = 'a call' WHERE id = %s", (n, cid, now(), rid))
            counts["answered"] += 1
        elif got.blocked:
            conn.execute(f"UPDATE {T.requests} SET attempts = attempts + 1, resolved_nzbn = %s WHERE id = %s",
                         (n, rid))
            stopped = f"a failed read at {n}: {got.blocked}"
        else:
            conn.execute(f"UPDATE {T.requests} SET state = 'set_aside', resolved_nzbn = %s, call_id = %s, "
                         f"answered_at = %s, reason = %s WHERE id = %s",
                         (n, cid, now(), "the register has no entity with this NZBN (HTTP 404)" if got.status == 404
                          else f"the register answered HTTP {got.status}", rid))
            counts["set_aside"] += 1
        conn.commit()
        if stopped:
            break
    if not stopped:
        for n in due_watches(conn, T, now()):
            if today(n):
                continue
            if (stopped := stop_why()):
                break
            got, ref, cid = call(n, "watch")
            counts["watches"] += 1
            if got.blocked:
                stopped = f"a failed read at {n}: {got.blocked}"
                break
    ok = not stopped.startswith("a failed read")
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + (f"; stopped: {stopped}" if stopped else "")
    log("companies monitor: " + detail)
    if record:
        jobrun.record(JOB, ok, detail, started, counts)
    return {**counts, "stopped": stopped, "ok": ok}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if "--night" in argv:
        budget = float(argv[argv.index("--budget-s") + 1]) if "--budget-s" in argv else DEFAULT_BUDGET_S
        with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
            conn.execute("SET statement_timeout = '60s'")
            return 0 if run(conn, budget_s=budget, anytime="--anytime" in argv)["ok"] else 1
    if "--rebuild" in argv:
        with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
            conn.execute("SET statement_timeout = '300s'")
            rebuild(conn)
        return 0
    if "--fetch" in argv:
        nzbns = argv[argv.index("--fetch") + 1:]
        if len(nzbns) > 10:
            print("at most ten: a handful proves the path")
            return 2
        key = api_key()
        with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
            for n in nzbns:
                got, ref = fetch_entity(n, conn, key=key)
                conn.commit()
                print(f"{n}: HTTP {got.status}, {len(got.body)} bytes"
                      + (f", landed {ref.sha256}" if ref else f", not landed: {got.blocked or 'no answer'}"),
                      flush=True)
                if got.blocked:
                    print("a failed read: the run stops (hard limit 6)")
                    return 1
        return 0
    print(__doc__.strip().splitlines()[-1].strip())
    return 2


if __name__ == "__main__":
    sys.exit(main())
