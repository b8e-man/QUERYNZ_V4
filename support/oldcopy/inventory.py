"""Stream I's inventory read into work: the NEW and PARTLY tables and stores, every other entry skipped with its
status (support/oldcopy/__init__.py has the file's shape). Pure: no database."""
import dataclasses
import json
import os
import re

COPIED = ("NEW", "PARTLY")
KNOWN = ("NEW", "PARTLY", "HELD", "DERIVED", "OUT")
_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


@dataclasses.dataclass(frozen=True)
class Table:
    database: str
    schema: str
    table: str
    status: str
    key: tuple = ()                 # the inventory's key columns, or () for the catalogue's
    ranges: tuple = ((None, None),)  # (after, through) per range, each a list of key text or None
    leave_out: tuple = ()           # (column, ILIKE pattern) pairs: rows matching any are not copied (held elsewhere)

    @property
    def piece(self) -> str:
        return f"{self.database}:{self.schema}.{self.table}"


@dataclasses.dataclass(frozen=True)
class Store:
    name: str
    root: str
    status: str
    source: str
    html: bool = False
    exclude: tuple = ()


def parse_piece(piece: str) -> tuple:
    """`database:schema.table` -> (database, schema, table); ValueError on anything else."""
    m = re.fullmatch(r"([a-z][a-z0-9_]*):([A-Za-z_][A-Za-z0-9_$]*)\.([A-Za-z_][A-Za-z0-9_$]*)", piece or "")
    if not m:
        raise ValueError(f"not a piece key database:schema.table: {piece!r}")
    return m.groups()


def _status(e: dict) -> str:
    return str(e.get("status") or e.get("verdict") or e.get("class") or "").strip().upper()


def _entries(inv: dict, part: str) -> list:
    v = inv.get(part) or []
    if isinstance(v, dict):
        return [dict(e, _name=k) for k, e in v.items()]
    return list(v)


def _bound(v):
    if v is None:
        return None
    return [str(x) for x in (v if isinstance(v, list) else [v])]


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def tables(inv: dict, databases=None) -> tuple:
    """([Table], [(name, status, why)]): the tables to copy, and every other entry with why it is not copied."""
    out, skipped = [], []
    for e in _entries(inv, "tables"):
        db_, sch, tab = e.get("database"), e.get("schema") or "public", e.get("table")
        if not tab and e.get("_name"):
            try:
                db_, sch, tab = parse_piece(e["_name"])
            except ValueError:
                pass
        name = f"{db_}:{sch}.{tab}"
        st = _status(e)
        if not (db_ and tab and _NAME.match(str(sch)) and _NAME.match(str(tab))):
            skipped.append((name, st, "not a table entry (database, schema, table)"))
            continue
        if databases is not None and db_ not in databases:
            skipped.append((name, st, f"database {db_} is not an old database this copier reads"))
            continue
        if st not in COPIED:
            skipped.append((name, st, "not copied: " + (st or "no status") if st in KNOWN or not st
                            else f"an unknown status {st!r}, not copied"))
            continue
        key = tuple(e.get("key") or ())
        if any(not _NAME.match(str(k)) for k in key):
            skipped.append((name, st, "the inventory's key is not a list of column names"))
            continue
        leave_out = tuple((str(r.get("column")), str(r.get("like"))) for r in (e.get("leave_out") or []))
        if any(not _NAME.match(c) or not p for c, p in leave_out):
            skipped.append((name, st, "the inventory's leave_out is not a list of {column, like}"))
            continue
        if st == "PARTLY":
            missing = e.get("missing") or e.get("missing_ranges") or []
            if not missing:
                skipped.append((name, st, "PARTLY with no missing key range named: reported, not guessed"))
                continue
            ranges = tuple((_bound(r.get("after")), _bound(r.get("through"))) for r in missing)
        else:
            ranges = ((None, None),)
        out.append(Table(db_, sch, tab, st, key, ranges, leave_out))
    return out, skipped


def stores(inv: dict) -> tuple:
    """([Store], [(name, status, why)])."""
    out, skipped = [], []
    for e in _entries(inv, "stores"):
        name = e.get("name") or e.get("_name") or ""
        st = _status(e)
        root = e.get("root") or e.get("path") or ""
        if not name or not root or not os.path.isabs(root):
            skipped.append((name, st, "not a store entry (name and an absolute root)"))
            continue
        if st not in COPIED:
            skipped.append((name, st, "not copied: " + (st or "no status")))
            continue
        html = bool(e.get("html") or e.get("lost_body") or e.get("html_kept"))
        out.append(Store(name, root.rstrip("/") or "/", st, e.get("source") or f"old-{name}", html,
                         tuple(x.strip("/") for x in e.get("exclude") or ())))
    return out, skipped
