"""THE STANDING SERVER'S NIGHT WINDOW (ruling 129, 30 October 2026): the
clock half, pure.

Flash-Next on Radiance holds both of node2's cards all day (ruling 121) and
the page reader (GLM-OCR, 4.8 GB) fits on neither beside it. So between
22:00 and 05:45 NZDT, when page-reader work is queued and no text-reader or
review piece is running or leased, the card manager may stop `qv4-radiance`,
load the page reader on one card for the queued pieces, and start the unit
again when the page queue is empty, or a text piece is due, or the window
ends, whichever is first. The frozen release runs at 06:15 and never calls
Flash-Next. Outside the window the standing server is never stopped or
planned: ruling 121 holds.

This module says only WHETHER A MOMENT IS INSIDE THE WINDOW and where its
edges fall, from the hours in jobs.toml's `[night_window]` section. The
hours are local time in a named zone (NZDT and NZST both), because the
window is placed against the frozen release's local clock, not UTC; the
manager's clock is UTC, as every time in the scheduler is. The acting half
is `cards.Manager.night_tick`.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import zoneinfo


@dataclasses.dataclass(frozen=True)
class Window:
    start: str          # HH:MM local, the window opens
    end: str            # HH:MM local, the window closes (may be past midnight: 22:00 to 05:45)
    timezone: str       # the zone the hours are read in (Pacific/Auckland)
    standing: str       # the standing profile whose unit may be stopped (flash-next)
    profile: str        # the profile loaded in its place (page-reader)
    card: int           # the card index the profile is loaded on; the standing server's other card stays free

    @property
    def zone(self) -> dt.tzinfo:
        return zoneinfo.ZoneInfo(self.timezone)

    @property
    def crosses_midnight(self) -> bool:
        return _minutes(self.end) <= _minutes(self.start)

    def __str__(self) -> str:
        return f"{self.start} to {self.end} {self.timezone}: {self.standing} stopped for {self.profile} on card {self.card}"


def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def valid_hhmm(s: str) -> bool:
    parts = str(s).split(":")
    return len(parts) == 2 and all(p.isdigit() for p in parts) and 0 <= int(parts[0]) < 24 and 0 <= int(parts[1]) < 60


def known_zone(name: str) -> bool:
    try:
        zoneinfo.ZoneInfo(name)
    except (zoneinfo.ZoneInfoNotFoundError, ValueError, TypeError):
        return False
    return True


def local(now: dt.datetime, w: Window) -> dt.datetime:
    """`now` in the window's zone. A naive moment is taken as UTC, as the
    scheduler's clock is."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    return now.astimezone(w.zone)


def in_window(now: dt.datetime, w: Window) -> bool:
    """Whether `now` falls inside the window: from its start, inclusive, to
    its end, exclusive, on the local clock; a window that crosses midnight
    wraps."""
    t = local(now, w)
    m = t.hour * 60 + t.minute
    s, e = _minutes(w.start), _minutes(w.end)
    if s == e:
        return False                       # an empty window: never open
    if s < e:
        return s <= m < e
    return m >= s or m < e


def closes_at(now: dt.datetime, w: Window) -> dt.datetime:
    """The next moment the window closes, at or after `now`, in UTC. Inside
    the window that is the current window's end; outside it, the end of the
    next window."""
    t = local(now, w)
    e = _minutes(w.end)
    end_today = t.replace(hour=e // 60, minute=e % 60, second=0, microsecond=0)
    if end_today <= t:
        end_today = (end_today + dt.timedelta(days=1)).replace(hour=e // 60, minute=e % 60)
    return end_today.astimezone(dt.timezone.utc)


def opens_at(now: dt.datetime, w: Window) -> dt.datetime:
    """The next moment the window opens, at or after `now`, in UTC."""
    t = local(now, w)
    s = _minutes(w.start)
    start_today = t.replace(hour=s // 60, minute=s % 60, second=0, microsecond=0)
    if start_today < t:
        start_today = (start_today + dt.timedelta(days=1)).replace(hour=s // 60, minute=s % 60)
    return start_today.astimezone(dt.timezone.utc)
