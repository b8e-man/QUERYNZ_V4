"""THE JOB CATALOGUE AND THE MODEL PROFILES (carried from ops/fleet/jobs.py).

Ruling 329 (Arthur, 2026-09-22): a card serves ONE job type, configured for
that job, and *"These configurations need to be kept with the jobs too."*
The new estate's step 2.4 widens the declaration: every job says what it
needs (a model profile or the processor), its memory per parallel worker,
its deadline and query time limit, whether it can share a card, and
optionally that it prefers the most memory. That half is `support.jobspec`
(the job contract); this module reads the catalogue and the profiles and
checks them.

TWO FILES, BOTH DECLARATIONS. `jobs.toml` is the catalogue: each `qv4-` job
type with its needs, class, priority, command, the programs it requires,
its timetable or its standing count. `profiles.toml` is the model profiles
(step 2.15): a model plus its settings on a card. A job names a profile;
jobs sharing a profile share a card's slots (step 2.7).

CONTEXT IS PER SLOT, AND THAT IS THE WHOLE POINT. llama.cpp's `-c` is the
total across slots; `-np` is the slot count. A server at `-c 131072 -np 8`
gives one request 16,384 tokens. The old `ec_pageread` job asked for 16,000
OUTPUT tokens and 409 of its calls went to that server, leaving ~384 for the
page. A profile declares what ONE REQUEST gets and this module derives the
flags, so the mistake is not available to make.

MEMORY IS MEASURED, NEVER COMPUTED. A profile's `memory_gb` is what rocm-smi
showed against the running server, and `measured_geometry` says at which
geometry; a figure carried across a geometry change is a warning, not
evidence. A job's `memory_gb` per worker is what its run records showed.
`load_seconds` is the measured load time of the profile (rule 9: the swap
cost is measured, not a fixed number) and is null until a swap measures it.

TOML, not YAML: the standard library reads it (`tomllib`), so the worker
needs nothing installed to read its own catalogue.
"""
from __future__ import annotations

import dataclasses
import json
import os
import pathlib
import tomllib

from support.jobspec import JobNeeds, validate
from support.scheduler import night, probe

HERE = pathlib.Path(__file__).resolve().parent
JOBS = HERE / "jobs.toml"
PROFILES = HERE / "profiles.toml"
MODELS_DIR = os.environ.get("QV4_MODELS") or "/home/user/models"

CLASSES = ("waiting", "due", "whenever")        # rule 8
PREFIX = "qv4-"


@dataclasses.dataclass(frozen=True)
class Profile:
    """A model plus its settings on a graphics card (step 2.15)."""
    name: str
    model: str                      # the alias the server advertises and the client demands
    weights: tuple[str, ...]        # the main weights, then any projector; relative to MODELS_DIR or absolute
    slots: int                      # requests at once (-np)
    context: int                    # PER REQUEST, not total
    temperature: float
    max_tokens: int                 # the output budget one request may ask for
    memory_gb: float | None         # measured on a card, never computed
    measured_geometry: str | None   # where memory_gb came from, e.g. "50000x2"
    load_seconds: float | None      # measured load time; null until a swap measures it
    flags: tuple[str, ...]          # extra llama-server flags, verbatim
    embedding: bool
    dpi: int | None                 # page readers: dots per inch the pages are rendered at
    used_for: str
    binary: str | None = None       # the model server program this profile needs, by the probe's name; None = the [server] setting
    # A STANDING server (ruling 121): its own qv4- unit runs it on `port` across `cards` cards; the card manager
    # reads its model back and marks the cards, and never starts or stops it.
    unit: str | None = None
    port: int | None = None
    cards: int = 1
    host_memory_gb: float | None = None     # measured: the server's resident host memory (Radiance pins experts there)
    # A VIEW on a standing server: the same model on the same cards, with its own per-request settings
    # (`request`, sent with every call: the reader's thinking off, review's on with a budget).
    on: str | None = None
    request: str = "{}"             # JSON, so the dataclass stays frozen and hashable
    # The requests the server is worth keeping open at once, MEASURED (31 October: eight streams of beehive pieces
    # read 155 a minute on Flash-Next, sixteen 145): the ceiling on pieces in flight across every row on the profile.
    # None = the server's slots. A view may state its own; else its server's.
    streams: int | None = None

    @property
    def request_fields(self) -> dict:
        return json.loads(self.request or "{}")

    @property
    def standing(self) -> bool:
        return bool(self.unit)

    @property
    def total_context(self) -> int:
        """What `-c` must be: per-request context times the slot count."""
        return self.context * self.slots

    @property
    def geometry(self) -> str:
        return f"{self.context}x{self.slots}"

    @property
    def headroom(self) -> int:
        """Tokens left for the PROMPT once the output budget is reserved."""
        return self.context - self.max_tokens

    @property
    def memory_is_for_this_geometry(self) -> bool | None:
        if self.memory_gb is None or self.measured_geometry is None:
            return None
        return self.measured_geometry == self.geometry

    def weight_paths(self, models_dir: str = None) -> list[str]:
        base = models_dir or MODELS_DIR
        return [w if os.path.isabs(w) else os.path.join(base, w) for w in self.weights]

    def serve_flags(self) -> list[str]:
        """The llama-server geometry this profile needs. Derived, never typed."""
        return ["-c", str(self.total_context), "-np", str(self.slots)]


@dataclasses.dataclass(frozen=True)
class JobType:
    """One `qv4-` job type: the contract's declaration plus what the
    scheduler needs to place and run it."""
    needs: JobNeeds
    description: str
    priority: int                   # orders a round; unique across the catalogue
    cls: str                        # waiting | due | whenever (rule 8)
    command: tuple[str, ...]        # argv; a pieces job gets the piece key appended
    requires: tuple[str, ...]       # programs the box must have (step 2.3)
    every_s: int                    # timetable: run this often (0 = on demand)
    at_utc: tuple[str, ...]         # timetable: daily at these HH:MM UTC (store and compare in UTC); () = none
    nice: int                       # the child's niceness (the founding units ran at Nice=10 to spare the carve-out)
    wanted: int                     # standing service: how many copies should run (0 = not standing)
    pieces: bool                    # cut into pieces, each recording progress (rule 7)
    item_seconds: float | None      # measured seconds per item; a guess until the run records say
    enabled: bool
    # THE CHAIN RUNS ITSELF (31 October). `pieces_command`: argv run by the worker in the job's environment when a
    # pieced row is claimed with no pieces listed; it prints one piece key a line, nothing meaning nothing waiting.
    # `then`: the jobs queued (one row each, class whenever, no pieces) when a row of this job finishes, one in
    # flight per named job. `threads`: the requests one piece keeps open itself (the hansard reader's --threads), so
    # a row's in-flight count is pieces x threads against the profile's streams.
    pieces_command: tuple[str, ...] = ()
    then: tuple[str, ...] = ()
    threads: int = 1

    @property
    def name(self) -> str:
        return self.needs.name

    @property
    def profile(self) -> str | None:
        return self.needs.model_profile or None

    @property
    def memory_gb(self) -> float:
        return self.needs.memory_gb

    @property
    def concurrency(self) -> int:
        """The CAP on parallel workers; the number actually run is worked
        out from the box's free memory (step 2.5)."""
        return self.needs.concurrency


@dataclasses.dataclass(frozen=True)
class Queueing:
    slice_seconds: int              # rule 2: a turn
    drain_not_kill: bool            # rule 3
    min_queue_to_evict: int         # rule 5's floor when no load time is measured
    max_wait_seconds: int           # rule 6: a small job never waits for ever
    piece_seconds: int              # rule 7: a piece is a few minutes
    due_horizon_seconds: int        # rule 8: a due job goes ahead of bulk work this close to its time
    memory_reserve_gb: float        # step 2.5: kept for the database and the standing services
    lease_seconds: int              # step 2.8
    policy: str


@dataclasses.dataclass(frozen=True)
class Reservation:
    """A card the planner never touches (step 2.9)."""
    box: str
    card: int
    holder: str
    why: str

    @property
    def key(self) -> str:
        return f"{self.box}:{self.card}"


def _raw(path: pathlib.Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def profiles(path: pathlib.Path | None = None) -> dict[str, Profile]:
    out: dict[str, Profile] = {}
    for name, b in (_raw(path or PROFILES).get("profiles") or {}).items():
        w = b.get("weights") or []
        out[name] = Profile(
            name=name, model=str(b.get("model") or ""),
            weights=tuple([w] if isinstance(w, str) else w),
            slots=int(b.get("slots", 1)), context=int(b.get("context", 0)),
            temperature=float(b.get("temperature", 0.0)), max_tokens=int(b.get("max_tokens", 0)),
            memory_gb=None if b.get("memory_gb") is None else float(b["memory_gb"]),
            measured_geometry=b.get("measured_geometry"),
            load_seconds=None if b.get("load_seconds") is None else float(b["load_seconds"]),
            flags=tuple(b.get("flags") or ()), embedding=bool(b.get("embedding", False)),
            dpi=None if b.get("dpi") is None else int(b["dpi"]), used_for=(b.get("used_for") or "").strip(),
            binary=str(b["binary"]) if b.get("binary") else None,
            unit=str(b["unit"]) if b.get("unit") else None,
            port=None if b.get("port") is None else int(b["port"]), cards=int(b.get("cards", 1)),
            host_memory_gb=None if b.get("host_memory_gb") is None else float(b["host_memory_gb"]),
            on=str(b["on"]) if b.get("on") else None,
            request=json.dumps(b.get("request") or {}, sort_keys=True),
            streams=None if b.get("streams") is None else int(b["streams"]))
    return out


def server_of(profs: dict[str, Profile], name: str) -> Profile:
    """The profile physically on the card for `name`: a view's standing
    server, otherwise the profile itself."""
    p = profs[name]
    return profs.get(p.on, p) if p.on else p


def streams_of(profs: dict[str, Profile], name: str) -> int:
    """The pieces worth keeping in flight on `name` at once, across every
    row and every view on its server: the profile's measured `streams`, else
    its server's, else the server's slots (the server queues past them)."""
    p = profs[name]
    if p.streams:
        return p.streams
    srv = server_of(profs, name)
    return srv.streams or srv.slots


SERVER_BINARIES = ("copy", "built")


def server_binary_setting(path: pathlib.Path | None = None) -> str:
    """Which model server the cards run (profiles.toml `[server] binary`):
    "copy", the old build's binary taken as it is, or "built", the estate's
    own build from source. A setting, so the switch is one line."""
    v = str((_raw(path or PROFILES).get("server") or {}).get("binary") or "copy")
    if v not in SERVER_BINARIES:
        raise ValueError(f"profiles.toml [server] binary is one of {SERVER_BINARIES}, not {v!r}")
    return v


def load(path: pathlib.Path | None = None) -> dict[str, JobType]:
    out: dict[str, JobType] = {}
    for name, b in (_raw(path or JOBS).get("jobs") or {}).items():
        needs = JobNeeds(
            name=name, needs=str(b.get("needs") or "processor"), memory_gb=float(b.get("memory_gb", 0)),
            deadline_s=int(b.get("deadline_s", 0)), query_timeout_s=int(b.get("query_timeout_s", 0)),
            interval_s=int(b.get("every_s", 0)), model_profile=str(b.get("profile") or ""),
            can_share=bool(b.get("can_share", False)), prefers_memory=bool(b.get("prefers_memory", False)),
            concurrency=int(b.get("concurrency", 1)))
        cmd = b.get("command") or []
        pcmd = b.get("pieces_command") or []
        then = b.get("then") or []
        out[name] = JobType(
            needs=needs, description=(b.get("description") or "").strip(), priority=int(b.get("priority", 99)),
            cls=str(b.get("class") or "whenever"), command=tuple([cmd] if isinstance(cmd, str) else cmd),
            requires=tuple(b.get("requires") or ()), every_s=int(b.get("every_s", 0)), at_utc=_times(b.get("at_utc")),
            nice=int(b.get("nice", 0)),
            wanted=int(b.get("wanted", 0)), pieces=bool(b.get("pieces", False)),
            item_seconds=None if b.get("item_seconds") is None else float(b["item_seconds"]),
            enabled=bool(b.get("enabled", True)),
            pieces_command=tuple([pcmd] if isinstance(pcmd, str) else pcmd),
            then=tuple([then] if isinstance(then, str) else then), threads=int(b.get("threads", 1)))
    return out


def queueing(path: pathlib.Path | None = None) -> Queueing:
    q = _raw(path or JOBS).get("queueing") or {}
    return Queueing(
        slice_seconds=int(q.get("slice_seconds", 3600)), drain_not_kill=bool(q.get("drain_not_kill", True)),
        min_queue_to_evict=int(q.get("min_queue_to_evict", 8)), max_wait_seconds=int(q.get("max_wait_seconds", 1800)),
        piece_seconds=int(q.get("piece_seconds", 300)), due_horizon_seconds=int(q.get("due_horizon_seconds", 7200)),
        memory_reserve_gb=float(q.get("memory_reserve_gb", 24)), lease_seconds=int(q.get("lease_seconds", 90)),
        policy=str(q.get("policy", "priority-ordered-round-robin")))


def reservations(path: pathlib.Path | None = None) -> list[Reservation]:
    return [Reservation(box=str(r["box"]), card=int(r["card"]), holder=str(r.get("holder") or ""),
                        why=str(r.get("why") or "")) for r in (_raw(path or JOBS).get("reservations") or [])]


def night_window(path: pathlib.Path | None = None) -> night.Window | None:
    """The standing server's night window (ruling 129), from jobs.toml's
    `[night_window]` section; None when the catalogue has none, and then the
    standing server is never stopped."""
    b = _raw(path or JOBS).get("night_window")
    if not b:
        return None
    return night.Window(start=str(b.get("start_local") or ""), end=str(b.get("end_local") or ""),
                        timezone=str(b.get("timezone") or "Pacific/Auckland"), standing=str(b.get("standing") or ""),
                        profile=str(b.get("profile") or ""), card=int(b.get("card", -1)))


def problems(path: pathlib.Path | None = None, profiles_path: pathlib.Path | None = None) -> list[str]:
    """Everything wrong with the catalogue. Empty list = green. Each rule is
    a shape that has already cost this estate something."""
    jts = load(path)
    profs = profiles(profiles_path)
    out: list[str] = []
    for jt in jts.values():
        for p in validate(jt.needs):
            out.append(f"{jt.name}: {p}")
        if jt.cls not in CLASSES:
            out.append(f"{jt.name}: class {jt.cls!r} is not one of {CLASSES}")
        if jt.profile and jt.profile not in profs:
            out.append(f"{jt.name}: names profile {jt.profile!r}, which profiles.toml does not hold")
        if not jt.command:
            out.append(f"{jt.name}: has no command")
        for t in jt.at_utc:
            if not _hhmm(t):
                out.append(f"{jt.name}: at_utc {t!r} is not HH:MM")
        if len(set(jt.at_utc)) != len(jt.at_utc):
            out.append(f"{jt.name}: at_utc names a time twice")
        if not 0 <= jt.nice <= 19:
            out.append(f"{jt.name}: nice is 0 to 19")
        if jt.every_s and jt.at_utc:
            out.append(f"{jt.name}: a timetable is every_s or at_utc, not both")
        if jt.wanted and (jt.every_s or jt.at_utc):
            out.append(f"{jt.name}: a standing service has no timetable")
        if jt.wanted and jt.pieces:
            out.append(f"{jt.name}: a standing service is not cut into pieces")
        if jt.pieces_command and not jt.pieces:
            out.append(f"{jt.name}: pieces_command on a job that is not cut into pieces (pieces = true)")
        if jt.threads < 1:
            out.append(f"{jt.name}: threads from 1")
        if jt.threads > 1 and not jt.pieces:
            out.append(f"{jt.name}: threads says what one piece keeps open; the job is not cut into pieces")
        if jt.pieces and jt.profile and jt.profile in profs:
            streams = streams_of(profs, jt.profile)
            if jt.concurrency * jt.threads > streams:
                out.append(f"{jt.name}: concurrency {jt.concurrency} x threads {jt.threads} = "
                           f"{jt.concurrency * jt.threads} pieces in flight on one row is over profile {jt.profile}'s "
                           f"{streams} streams")
        for t in jt.then:
            if t not in jts:
                out.append(f"{jt.name}: then names {t!r}, which is not in the catalogue")
            elif t == jt.name:
                out.append(f"{jt.name}: then names itself")
            elif jts[t].pieces and not jts[t].pieces_command:
                out.append(f"{jt.name}: then names {t!r}, a pieced job with no pieces_command, so a row of it queued with "
                           f"no pieces would be refused")
            elif jts[t].wanted or jts[t].every_s or jts[t].at_utc:
                out.append(f"{jt.name}: then names {t!r}, which has a clock or a wanted count of its own")
    prios = [jt.priority for jt in jts.values()]
    if len(set(prios)) != len(prios):
        dupes = sorted({p for p in prios if prios.count(p) > 1})
        out.append(f"priorities are not unique ({dupes}) — the scheduler cannot order the round deterministically")
    for p in profs.values():
        if not p.name.islower() or not all(ch.isalnum() or ch == "-" for ch in p.name):
            out.append(f"profile {p.name!r}: a profile name is lower-case letters, digits and -")
        if not p.model:
            out.append(f"profile {p.name}: names no model (the client refuses a call that names none)")
        if p.on:
            srv = profs.get(p.on)
            if srv is None or not srv.standing:
                out.append(f"profile {p.name}: is a view on {p.on!r}, which is not a standing server in profiles.toml")
            else:
                if p.model != srv.model:
                    out.append(f"profile {p.name}: a view demands {p.model!r} but its server {srv.name} serves {srv.model!r}")
                if p.context > srv.context:
                    out.append(f"profile {p.name}: a request's context {p.context:,} is over its server's {srv.context:,}")
            if p.weights or p.binary or p.unit:
                out.append(f"profile {p.name}: a view names no weights, server or unit of its own; its server does")
        elif not p.weights:
            out.append(f"profile {p.name}: names no weights file")
        if p.unit:
            if not p.unit.startswith(PREFIX):
                out.append(f"profile {p.name}: its unit {p.unit!r} lacks the {PREFIX} prefix (hard limit 23)")
            if not p.port:
                out.append(f"profile {p.name}: a standing server names the port it answers on")
            if not p.binary:
                out.append(f"profile {p.name}: a standing server names its program (binary), so a box without it never claims")
        if p.max_tokens and p.context and p.headroom < 1024:
            out.append(f"profile {p.name}: max_tokens {p.max_tokens:,} against a per-request context of "
                       f"{p.context:,} leaves {p.headroom:,} tokens for the prompt")
        if p.slots < 1 or p.context < 1:
            out.append(f"profile {p.name}: slots and context from 1")
        if p.streams is not None and p.streams < 1:
            out.append(f"profile {p.name}: streams from 1")
        if p.streams and p.streams > server_of(profs, p.name).slots and (p.on is None or p.on in profs):
            out.append(f"profile {p.name}: streams {p.streams} is over its server's {server_of(profs, p.name).slots} slots: "
                       f"the server would queue the rest")
        if p.binary and p.binary not in probe.PROGRAMS:
            out.append(f"profile {p.name}: binary {p.binary!r} is not a program the probe looks for, so no box would ever load it")
    w = night_window(path)
    if w is not None:
        # ruling 129: the window's hours and its two profiles, checked before a worker reads them
        for label, v in (("start_local", w.start), ("end_local", w.end)):
            if not night.valid_hhmm(v):
                out.append(f"night_window: {label} {v!r} is not HH:MM")
        if night.valid_hhmm(w.start) and night.valid_hhmm(w.end) and w.start == w.end:
            out.append("night_window: start_local and end_local are the same minute, so the window never opens")
        if not night.known_zone(w.timezone):
            out.append(f"night_window: timezone {w.timezone!r} is not a zone this box knows")
        st = profs.get(w.standing)
        if st is None or not st.standing:
            out.append(f"night_window: standing {w.standing!r} is not a standing server in profiles.toml")
        pr = profs.get(w.profile)
        if pr is None or pr.standing or pr.on:
            out.append(f"night_window: profile {w.profile!r} is not a profile the worker loads itself (a server of its own, "
                       f"not a standing server or a view)")
        if w.card < 0:
            out.append("night_window: card names the card index the profile is loaded on")
    return out


def warnings(path: pathlib.Path | None = None, profiles_path: pathlib.Path | None = None) -> list[str]:
    """Things to MEASURE, as distinct from things that are broken. A gate
    that fails on work not yet done gets switched off."""
    out: list[str] = []
    for p in profiles(profiles_path).values():
        if p.on:
            continue                  # a view's memory and load time are its server's
        fit = p.memory_is_for_this_geometry
        if p.memory_gb is None:
            out.append(f"profile {p.name}: no measured memory_gb — load it at {p.geometry} and record one")
        elif fit is False:
            out.append(f"profile {p.name}: memory_gb {p.memory_gb} GB was measured at {p.measured_geometry}, "
                       f"but it declares {p.geometry} — the KV cache is most of the difference, so the figure "
                       f"is not evidence here")
        elif fit is None:
            out.append(f"profile {p.name}: memory_gb {p.memory_gb} GB records no measured_geometry")
        if p.load_seconds is None:
            out.append(f"profile {p.name}: load time not yet measured; rule 5 uses the queue floor until a swap measures it")
    for jt in load(path).values():
        if jt.item_seconds is None and not jt.wanted:
            out.append(f"{jt.name}: no item_seconds yet; measured from its run records")
    return out


def switch_cost(frm: Profile | None, to: Profile | None, same_job: bool = False) -> str:
    """What moving a card between profiles costs: `none` (same job type on
    the same profile), `handover` (the profile is already resident: another
    job type takes it for nothing), `load` (other weights or other settings:
    a server restart, minutes). Rule 5 turns on this and on the measured
    `load_seconds` of `to`."""
    if to is None:
        return "none"
    if frm is None:
        return "load"
    if frm.name == to.name:
        return "none" if same_job else "handover"
    return "load"


def _times(v) -> tuple[str, ...]:
    """`at_utc` is one HH:MM or a list of them (the heartbeat runs twice a day)."""
    if v is None or v == "":
        return ()
    if isinstance(v, str):
        return (v,)
    return tuple(str(x) for x in v)


def _hhmm(s: str) -> bool:
    parts = str(s).split(":")
    return len(parts) == 2 and all(p.isdigit() for p in parts) and 0 <= int(parts[0]) < 24 and 0 <= int(parts[1]) < 60
