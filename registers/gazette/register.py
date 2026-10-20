"""The liquidated companies against the Companies Office register: each
liquidation row joined to the companies lane's published entities
(`pub.companies`). No model, no guess.

  number   the notice prints the company's number and the register holds
           it: the register's row, and whether its name agrees
  name     no number printed (or one the register does not hold): the one
           entity whose name agrees and that was alive on the appointment
           date (registered on or before it, not removed before it)

A name that agrees with no entity, or with several alive that day, gets no
register row: it is a catch-log line, never the nearest name. The register
holds each entity's latest name, so a company renamed after its
liquidation (a reversed name, a new "(2019)") does not agree by name; where
the notice printed the number, the number decides and the row says the
names differ.

    key(name)                    the name as the two sources are compared
    Index(rows)                  rows: (key, register, number, name, registered_on, removed_on)
    Index.match(company, number, on, year)   (register key or None, how)
    rows_from(conn, schema, shared)    the register's rows, or None where this database has none
"""
import datetime as dt
import re
import unicodedata
from collections import defaultdict

#: how a row was joined; the last three give no register row
NUMBER, NUMBER_NAME_DIFFERS = "number and name", "number; the register's name differs"
NAME, NAME_NUMBER_NOT_HELD = "name, alive on the date", "name; the printed number is not held"
#: a name printed without its legal ending ("GE Custodians"), held with "Limited" (possessions.py)
NAME_LIMITED = "name with Limited added, alive on the date"
SEVERAL, NOT_ALIVE, NOT_HELD = "name; several alive on the date", "name; held, not alive on the date", "not held"
UNMATCHED = (SEVERAL, NOT_ALIVE, NOT_HELD)
COUNT = {NUMBER: "number", NUMBER_NAME_DIFFERS: "number_name_differs", NAME: "name",
         NAME_NUMBER_NOT_HELD: "name_number_not_held", NAME_LIMITED: "name_limited", SEVERAL: "several", NOT_ALIVE: "not_alive", NOT_HELD: "not_held"}

_STATUS = re.compile(r"\s*\((?:\s*[a-z\"“'‘]|\s*(?i:in|formerly|previously|now|receivers?|all|both|trading)\b)[^()]*(?:\([^()]*\)[^()]*)*\)")


def key(name: str) -> str:
    """Upper case without macrons or accents; a bracketed status, former
    name or defined term ("the company") dropped; `&` read as AND, `LTD` as
    LIMITED, `INC` as INCORPORATED; everything but letters and digits removed."""
    s = unicodedata.normalize("NFKD", _STATUS.sub(" ", name or "")).encode("ascii", "ignore").decode()
    s = re.sub(r"\bLTD\b", "LIMITED", s.upper().replace("&", " AND "))
    s = re.sub(r"\bINC\b\.?", "INCORPORATED", s)
    return re.sub(r"[^A-Z0-9]", "", s)


def _number(n) -> str:
    return (n or "").strip().lstrip("0") or None


def _on(d):
    if d is None or isinstance(d, dt.date):
        return d
    return dt.date.fromisoformat(str(d)[:10])


class Index:
    def __init__(self, rows):
        self.by_number, self.by_name = defaultdict(dict), defaultdict(list)
        for k, register, number, name, registered_on, removed_on in rows:
            r = (k, key(name), _on(registered_on), _on(removed_on))
            n = _number(number)
            if n:                                 # each register numbers its own: a notice's "Company No." is never a society's
                self.by_number[register].setdefault(n, r)
            self.by_name[r[1]].append(r)

    def match(self, company: str, number: str = None, on=None, year: int = None, registers=("companies",)) -> tuple:
        """on: the appointment date; without one, the notice's year (alive
        at some time in it). registers: the registers whose numbers the
        printed number can be (a society's notice prints the society's)."""
        on, n, k = _on(on), _number(number), key(company)
        lo, hi = (on, on) if on else (dt.date(year, 1, 1), dt.date(year, 12, 31)) if year else (None, None)
        r = next((self.by_number[g][n] for g in registers if n and n in self.by_number[g]), None)
        if r:
            return r[0], NUMBER if r[1] == k else NUMBER_NAME_DIFFERS
        held = self.by_name.get(k, [])
        alive = [r for r in held if lo is None or ((r[2] is None or r[2] <= hi) and (r[3] is None or r[3] >= lo))]
        if len(alive) == 1:
            return alive[0][0], NAME_NUMBER_NOT_HELD if n else NAME
        return None, SEVERAL if alive else NOT_ALIVE if held else NOT_HELD


def rows_from(conn, schema: str = None, shared: bool = False):
    """The register's entities: in a session's sample the companies lane's
    own table in the shared schema, else `pub.companies`; None where this
    database holds neither (the match is then not made, and says so)."""
    where = [f"{schema}.companies_entities"] if shared and schema else []
    where.append("pub.companies")
    for t in where:
        if conn.execute("SELECT to_regclass(%s) IS NOT NULL", (t,)).fetchone()[0]:
            return conn.execute(f"SELECT key, register, number, name, registered_on, removed_on FROM {t}").fetchall()
    return None
