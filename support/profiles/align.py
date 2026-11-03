"""The lane and its profiles aligned (Arthur, 3 November 2026: "the lane asks for something and the profile provides
something. we need to ensure that these somethings are aligned. also, that there are fields in the database table").

A lane declares what its code produces, per profile: the fields its readers make, each with how (`by`: rules,
pattern or model) and, where the code holds one, its closed vocabulary of kinds; and the columns of its tables. Both
are derived from the lane's code (its load's column lists, its readers' output keys, its kinds), never typed out a
second time. `problems` compares that with each profile's current extract list:

  (a) a field the lane produces that the profile's extract list lacks, or lists under another `by` or other kinds;
  (b) a field the profile lists that the lane does not produce;
  (c) a `lands` column that is not one of the lane's table columns;
  (d) a column of the lane's tables, housekeeping apart, that no field of any of the lane's profiles lands in.

`live_problems` checks that every `lands` column exists in the database (the catalog), so a column the
profile promises and the tables lack is red at the lane's check.

    Lane(name, tables, produces, housekeeping)
    problems(lane, profiles=None)                [str]
    live_problems(conn, lane, where, profiles=None)   [str]
"""
from dataclasses import dataclass, field

import support.profiles as pr

#: the stamp every reading row carries: where it was read and by what, never a field of the document
HOUSEKEEPING = frozenset({"key", "document", "page", "place", "read_from", "reader", "model", "model_reader", "profile",
                          "profile_version", "loaded_at", "at"})


@dataclass(frozen=True)
class Lane:
    name: str
    #: table, in the lane's own naming ("judgments", "courts_private.identifiers") → its columns
    tables: dict
    #: profile slug → {field: (by, kinds or None)}
    produces: dict
    #: the lane's own housekeeping: a bare column name (every table) or "table.column"
    housekeeping: frozenset = field(default_factory=frozenset)

    def columns(self) -> set:
        return {f"{t}.{c}" for t, cols in self.tables.items() for c in cols}

    def is_housekeeping(self, col: str) -> bool:
        bare = col.rsplit(".", 1)[1]
        return bare in HOUSEKEEPING or bare in self.housekeeping or col in self.housekeeping


def problems(lane: Lane, profiles: dict = None) -> list:
    profiles = pr.current() if profiles is None else profiles
    out, landed, cols = [], set(), lane.columns()
    for slug, wants in sorted(lane.produces.items()):
        prof = profiles.get(slug)
        if prof is None:
            out.append(f"{slug}: the {lane.name} lane reads a profile the ledger does not hold")
            continue
        items = pr.latest(prof.get("extract"))
        if not items:
            out.append(f"{slug}: the profile lists nothing it extracts; the {lane.name} lane produces {len(wants)} field(s)")
            continue
        for f, (by, kinds) in sorted(wants.items()):
            it = items.get(f)
            if it is None:
                out.append(f"{slug}: the {lane.name} lane produces {f} ({by}); the profile's extract list lacks it")
                continue
            if it["by"] != by:
                out.append(f"{slug}: {f} is by {by} in the lane's code, by {it['by']} in the profile")
            if kinds is not None and sorted(it.get("kinds") or ()) != sorted(kinds):
                out.append(f"{slug}: {f}'s kinds differ: the lane's code has {sorted(kinds)}, the profile {sorted(it.get('kinds') or ())}")
        for f, it in sorted(items.items()):
            if f not in wants:
                out.append(f"{slug}: the profile lists {f} (iteration {it['iteration']}); no code of the {lane.name} lane produces it")
            for col in it.get("lands") or ():
                landed.add(col)
                if col not in cols:
                    out.append(f"{slug}: {f} lands in {col}, which is not a column of the {lane.name} lane's tables")
    for col in sorted(cols - landed):
        if not lane.is_housekeeping(col):
            out.append(f"{col}: a column of the {lane.name} lane's tables that no profile's field lands in")
    return out


def lands_of(lane: Lane, profiles: dict = None) -> set:
    """Every `lands` column the lane's profiles name."""
    profiles = pr.current() if profiles is None else profiles
    return {col for slug in lane.produces for it in pr.latest((profiles.get(slug) or {}).get("extract")).values()
            for col in it.get("lands") or ()}


def live_problems(conn, lane: Lane, where, profiles: dict = None) -> list:
    """Each `lands` column absent from the database. `where(table)` gives the lane table's (schema, table name) in
    this database (a staging or shared schema renames them). Read from the catalog (pg_attribute), not
    information_schema, which shows a login only the columns it holds a grant on: the read login sees no column of a
    private table, and a check that could not see a column must not report it missing."""
    by_table = {}
    for col in lands_of(lane, profiles):
        t, c = col.rsplit(".", 1)
        by_table.setdefault(t, set()).add(c)
    out = []
    for t, want in sorted(by_table.items()):
        schema, name = where(t)
        have = {r[0] for r in conn.execute(
            "SELECT a.attname FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = %s AND c.relname = %s AND a.attnum > 0 AND NOT a.attisdropped", (schema, name)).fetchall()}
        if not have:
            out.append(f"{schema}.{name} does not exist, and a profile's field lands in it")
            continue
        for c in sorted(want - have):
            out.append(f"{schema}.{name} has no column {c}, which a profile's field lands in")
    return out
